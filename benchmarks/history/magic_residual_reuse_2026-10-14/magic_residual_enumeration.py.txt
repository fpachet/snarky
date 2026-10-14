"""Experimental integer residual extraction and bounded native enumeration."""

from __future__ import annotations

import ctypes as ct
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from snarky import Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)

_LOADED_KERNELS = {}
_FLAGS = ("-O3", "-std=c11", "-shared", "-fPIC")


@dataclass
class Residual:
    indices: tuple[int, ...]
    domains: tuple[tuple[int, ...], ...]
    rows: tuple[tuple[int, tuple[tuple[int, int], ...], int], ...]
    invalid: bool = False


class Compiler:
    def __init__(self, model):
        self.model = model
        self.values = []
        for v in model.variables:
            if any(
                not isinstance(x, Number)
                or type(x.value) is not int
                or not 0 <= x.value < 4096
                for x in v.domain
            ):
                raise ValueError("experiment requires integer values in 0..4095")
            self.values.append(tuple(x.value for x in v.domain))
        indices = {v.name: i for i, v in enumerate(model.variables)}
        self.rows = []
        distinct = 0
        for c in model.constraints:
            if isinstance(c, AllDifferentConstraint):
                if set(c.variables) != set(indices):
                    raise ValueError("experiment requires one global ALLDIFF")
                distinct += 1
                continue
            if isinstance(c, SumConstraint):
                terms, op = tuple((1, v) for v in c.variables), 0
            elif isinstance(c, LinearSumConstraint):
                terms = c.terms
                op = {
                    ConstraintOperator.EQUAL: 0,
                    ConstraintOperator.LESS_EQUAL: 1,
                    ConstraintOperator.GREATER_EQUAL: 2,
                }[c.operator]
            else:
                raise ValueError("unsupported constraint in residual study")
            self.rows.append(
                (
                    op,
                    tuple((indices[v], coefficient) for coefficient, v in terms),
                    c.target,
                )
            )
        if distinct != 1 or model.rules or model.objective:
            raise ValueError(
                "experiment supports pure feasibility with one global ALLDIFF"
            )

    def extract(self, masks):
        if len(masks) != len(self.values):
            raise ValueError("mask count does not match model")
        fixed, domains = {}, {}
        for i, mask in enumerate(masks):
            if mask <= 0 or mask >= 1 << len(self.values[i]):
                return Residual((), (), (), True)
            if not mask & (mask - 1):
                fixed[i] = self.values[i][mask.bit_length() - 1]
            else:
                pending, values = mask, []
                while pending:
                    bit = pending & -pending
                    pending ^= bit
                    values.append(self.values[i][bit.bit_length() - 1])
                domains[i] = tuple(values)
        used = set(fixed.values())
        if len(used) != len(fixed):
            return Residual((), (), (), True)
        domains = {
            i: tuple(v for v in values if v not in used)
            for i, values in domains.items()
        }
        if any(not values for values in domains.values()):
            return Residual((), (), (), True)
        order = tuple(sorted(domains, key=lambda i: len(domains[i])))
        if len(order) > 32:
            raise ValueError("residual exceeds 32 variables")
        position = {i: j for j, i in enumerate(order)}
        rows = []
        for op, terms, target in self.rows:
            target -= sum(c * fixed[i] for i, c in terms if i in fixed)
            active = tuple((position[i], c) for i, c in terms if i in domains)
            if not active:
                valid = (
                    target == 0 if op == 0 else target >= 0 if op == 1 else target <= 0
                )
                if not valid:
                    return Residual((), (), (), True)
                continue
            if (
                abs(target) + sum(abs(c) * max(domains[order[i]]) for i, c in active)
                >= 1 << 62
            ):
                raise ValueError("residual arithmetic exceeds conservative int64 bound")
            if any(not -(1 << 31) < c < 1 << 31 for _, c in active):
                raise ValueError("coefficient exceeds int32")
            rows.append((op, active, target))
        if len(rows) > 64:
            raise ValueError("residual exceeds 64 constraints")
        return Residual(order, tuple(domains[i] for i in order), tuple(rows))


class Kernel:
    def __init__(self, library):
        self.library = ct.CDLL(str(Path(library).resolve()))
        self.function = self.library.residual_enum
        ip, lp, up = (
            ct.POINTER(ct.c_int),
            ct.POINTER(ct.c_int64),
            ct.POINTER(ct.c_uint64),
        )
        self.function.argtypes = [
            ct.c_int,
            ip,
            ip,
            ct.c_int,
            ip,
            ip,
            ip,
            ip,
            lp,
            ct.c_int,
            ct.c_int,
            ct.c_uint64,
            ip,
            up,
        ]
        self.function.restype = ct.c_int

    @classmethod
    def build(cls, output, *, cache_dir=None, source=None):
        """Cache by source, compiler and platform; reuse the loaded CDLL in-process.

        The output copy is retained for experiment provenance. The actual loaded
        library has an immutable content-keyed path, avoiding stale dlopen handles
        when an experiment's output filename is reused after a source change.
        """
        source = Path(source or Path(__file__).with_name("residual_enum.c"))
        output = Path(output).resolve()
        started = perf_counter()
        source_bytes = source.read_bytes()
        compiler = Path(shutil.which("cc") or "cc").resolve()
        version = subprocess.check_output([str(compiler), "--version"], text=True)
        identity = dict(
            abi=1,
            source_sha256=hashlib.sha256(source_bytes).hexdigest(),
            compiler=str(compiler),
            compiler_version=version,
            compiler_stat=[compiler.stat().st_size, compiler.stat().st_mtime_ns],
            flags=_FLAGS,
            platform=platform.platform(),
            machine=platform.machine(),
            environment={
                name: os.environ.get(name)
                for name in (
                    "SDKROOT",
                    "MACOSX_DEPLOYMENT_TARGET",
                    "CPATH",
                    "LIBRARY_PATH",
                )
            },
        )
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        root = Path(cache_dir or "generated/neural_attention/residual_kernel_cache")
        bundle = root.resolve() / key
        library, metadata = bundle / "enumerator.so", bundle / "build.json"
        try:
            report = json.loads(metadata.read_text())
            hit = (
                report["binary_sha256"]
                == hashlib.sha256(library.read_bytes()).hexdigest()
            )
        except (OSError, ValueError, KeyError):
            hit = False
        compile_seconds = 0.0
        if not hit:
            bundle.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=bundle) as temporary:
                built = Path(temporary) / "enumerator.so"
                frozen_source = Path(temporary) / "kernel.c"
                frozen_source.write_bytes(source_bytes)
                command = [
                    str(compiler),
                    *_FLAGS,
                    str(frozen_source),
                    "-o",
                    str(built),
                ]
                t = perf_counter()
                process = subprocess.run(
                    command, capture_output=True, text=True, check=True
                )
                compile_seconds = perf_counter() - t
                report = dict(
                    identity=identity,
                    source=str(source.resolve()),
                    command=command,
                    compiler=version,
                    stdout=process.stdout,
                    stderr=process.stderr,
                    binary_sha256=hashlib.sha256(built.read_bytes()).hexdigest(),
                    original_compile_seconds=compile_seconds,
                )
                saved = Path(temporary) / "build.json"
                saved.write_text(json.dumps(report, indent=2) + "\n")
                os.replace(built, library)
                os.replace(saved, metadata)
        loaded_key = (str(library), report["binary_sha256"])
        loaded = loaded_key in _LOADED_KERNELS
        if not loaded:
            _LOADED_KERNELS[loaded_key] = cls(library)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output != library:
            shutil.copyfile(library, output)
        return _LOADED_KERNELS[loaded_key], dict(
            **report,
            seconds=perf_counter() - started,
            compile_seconds=compile_seconds,
            cache_hit=hit,
            loaded_reused=loaded,
            cache_key=key,
            library=str(library),
        )

    def prepare(self, residual):
        offsets, values, starts, variables, coefficients, ops, targets = (
            [0],
            [],
            [0],
            [],
            [],
            [],
            [],
        )
        for domain in residual.domains:
            values.extend(domain)
            offsets.append(len(values))
        for op, terms, target in residual.rows:
            ops.append(op)
            targets.append(target)
            for v, coefficient in terms:
                variables.append(v)
                coefficients.append(coefficient)
            starts.append(len(variables))
        integers = [offsets, values, starts, variables, coefficients, ops]
        arrays = [(ct.c_int * len(v))(*v) for v in integers]
        target_array = (ct.c_int64 * len(targets))(*targets)
        first = (ct.c_int * len(residual.domains))()
        counts = (ct.c_uint64 * 3)()

        def run(mode=1, limit=200000, count_all=False):
            if residual.invalid:
                return dict(status=0, visits=0, leaves=0, solutions=0, witness=None)
            status = self.function(
                len(residual.domains),
                arrays[0],
                arrays[1],
                len(residual.rows),
                arrays[2],
                arrays[3],
                arrays[4],
                arrays[5],
                target_array,
                mode,
                count_all,
                limit,
                first,
                counts,
            )
            if status < 0:
                raise ValueError("native enumerator rejected input")
            return dict(
                status=status,
                visits=counts[0],
                leaves=counts[1],
                solutions=counts[2],
                witness=list(first) if counts[2] else None,
            )

        return run
