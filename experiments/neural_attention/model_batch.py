"""Experimental generic/model-specialized native propagation episodes.

The generated executor shares filtering, cache rules, queue order and storage
with the generic executor. Specialization embeds scopes, layouts and targets;
SUM clones use fixed column counts and mask/contribution offsets. Search is
not generated. No changes to installed solver defaults.
"""

from __future__ import annotations

import ctypes as ct
import hashlib
import json
import re
import sys
import weakref
from collections import deque
from pathlib import Path
from time import perf_counter

from snarky import Number
from snarky.finite.alldifferent import AllDifferentPlans
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.domains import FiniteDomains
from snarky.finite.numeric import NumericPlans
from snarky.finite.propagation import NativeState

from .magic_residual_enumeration import Kernel

HERE = Path(__file__).parent
PRIME, SEED, UINT64 = 1099511628211, 1469598103934665603, (1 << 64) - 1


def offsets(lengths):
    result = [0]
    for length in lengths:
        result.append(result[-1] + length)
    return result


class ModelSpec:
    def __init__(self, model):
        if model.rules or model.context or model.objective or model.measure:
            raise ValueError("batch experiment requires pure finite feasibility")
        if sys.byteorder != "little" or not 1 <= len(model.variables) <= 2048:
            raise ValueError("unsupported platform or variable count")
        self.model = model
        self.names = tuple(v.name for v in model.variables)
        indices = {v: i for i, v in enumerate(self.names)}
        self.alphabets = []
        for variable in model.variables:
            if any(
                not isinstance(v, Number) or type(v.value) is not int
                for v in variable.domain
            ):
                raise ValueError("batch experiment requires integer alphabets")
            values = tuple(v.value for v in variable.domain)
            if not 1 <= len(values) <= 2048 or len(set(values)) != len(values):
                raise ValueError("unsupported alphabet")
            self.alphabets.append(values)
        self.lengths = list(map(len, self.alphabets))
        if sum(self.lengths) > 262144:
            raise ValueError("model alphabet budget exceeded")
        self.word_lengths = [(n + 63) // 64 for n in self.lengths]
        self.word_offsets = offsets(self.word_lengths)
        self.byte_lengths = [8 * n for n in self.word_lengths]
        self.byte_offsets = offsets(self.byte_lengths)
        self.full = tuple((1 << n) - 1 for n in self.lengths)
        self.rows = []
        self.adjacency = [[] for _ in self.names]
        for constraint in model.constraints:
            scope = [indices[v] for v in constraint.variables]
            if not scope or len(set(scope)) != len(scope):
                raise ValueError("unsupported empty or repeated scope")
            starts = offsets([self.lengths[v] for v in scope])
            local = offsets([self.word_lengths[v] for v in scope])
            row = dict(scope=scope, starts=starts, local=local)
            if isinstance(constraint, AllDifferentConstraint):
                canonical = {}
                values = []
                for v in scope:
                    for value in self.alphabets[v]:
                        if value not in canonical:
                            canonical[value] = len(canonical)
                        values.append(canonical[value])
                if len(canonical) > 2048 or len(values) > 262144:
                    raise ValueError("ALLDIFF layout exceeds kernel limits")
                row.update(kind=0, op=0, target=0, count=len(canonical), values=values)
            elif isinstance(constraint, (SumConstraint, LinearSumConstraint)):
                terms = (
                    [(1, v) for v in scope]
                    if isinstance(constraint, SumConstraint)
                    else [(c, indices[v]) for c, v in constraint.terms]
                )
                op = (
                    0
                    if isinstance(constraint, SumConstraint)
                    else {
                        ConstraintOperator.EQUAL: 0,
                        ConstraintOperator.LESS_EQUAL: 1,
                        ConstraintOperator.GREATER_EQUAL: 2,
                    }[constraint.operator]
                )
                if len(scope) > 64:
                    raise ValueError("SUM scope exceeds kernel limits")
                values, origin, span = [], 0, 0
                for coefficient, v in terms:
                    contributions = [coefficient * x for x in self.alphabets[v]]
                    low = min(contributions)
                    origin += low
                    span += max(contributions) - low
                    values.extend(x - low for x in contributions)
                if span > 16384 or (
                    op == 0
                    and len(scope) > 2
                    and (span + 1) * (len(scope) + 2) > 1048576
                ):
                    raise ValueError("SUM span exceeds existing Python plan limits")
                row.update(
                    kind=1,
                    op=op,
                    target=max(-1, min(span + 1, constraint.target - origin)),
                    values=values,
                )
            else:
                raise ValueError("unsupported constraint in batch experiment")
            self.rows.append(row)
            for v in scope:
                self.adjacency[v].append(len(self.rows) - 1)
        if (
            not 1 <= len(self.rows) <= 4096
            or sum(len(r["scope"]) for r in self.rows) > 262144
        ):
            raise ValueError("unsupported constraint budget")
        self.cache_offsets = offsets([r["local"][-1] for r in self.rows])
        if self.cache_offsets[-1] > 1048576:
            raise ValueError("batch scratch budget exceeded")
        record = dict(alphabets=self.alphabets, rows=self.rows)
        self.key = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()

    def encode(self, masks):
        if len(masks) != len(self.names) or any(
            m < 0 or m & ~f for m, f in zip(masks, self.full, strict=True)
        ):
            raise ValueError("mask outside original alphabet")
        packed = b"".join(
            m.to_bytes(n, "little")
            for m, n in zip(masks, self.byte_lengths, strict=True)
        )
        result = (ct.c_uint64 * self.word_offsets[-1])()
        ct.memmove(result, packed, len(packed))
        return result

    def decode(self, array):
        packed = ct.string_at(array, self.byte_offsets[-1])
        return tuple(
            int.from_bytes(packed[a:b], "little")
            for a, b in zip(self.byte_offsets, self.byte_offsets[1:], strict=False)
        )


def int_array(values):
    return (ct.c_int * len(values))(*values)


def source(spec=None):
    sums = (HERE / "sum_support.c").read_text()
    prefix = "#define MODEL_SPECIALIZED 1\n" if spec else ""
    if spec and any(row["kind"] == 1 and row["op"] != 0 for row in spec.rows):
        prefix += "#define MODEL_HAS_INEQUALITY 1\n"
    parts = [
        prefix,
        sums,
        (HERE / "alldiff_support.c").read_text(),
        (HERE / "model_batch_runtime.c").read_text(),
    ]
    if spec is None:
        parts.append('const char *batch_model_key(void) { return ""; }\n')
        return "\n".join(parts)
    parts.append(f'const char *batch_model_key(void) {{ return "{spec.key}"; }}\n')
    shapes, kernels = {}, {}
    body = sums[sums.index("int sum_supports(") :]
    body = body[body.index("{") + 1 :]
    for c, row in enumerate(spec.rows):
        if row["kind"] != 1 or row["op"] != 0 or not 0 <= row["target"] <= 16384:
            continue
        key = tuple(row["starts"]), tuple(row["local"]), row["target"]
        if key not in shapes:
            tag = f"sum_shape_{len(shapes)}"
            shapes[key] = tag
            starts = ",".join(map(str, row["starts"]))
            masks = ",".join(map(str, row["local"]))
            clone = body.replace("s->starts", f"{tag}_starts").replace(
                "s->masks", f"{tag}_masks"
            )
            clone = re.sub(r"s->n\b", str(len(row["scope"])), clone)
            clone = re.sub(r"s->words\b", str(row["local"][-1]), clone)
            parts.append(
                f"static const int {tag}_starts[] = {{{starts}}};\n"
                f"static const int {tag}_masks[] = {{{masks}}};\n"
                f"static inline int {tag}(void *pointer, "
                "const uint64_t *masks, uint64_t *output) {\n"
                f"const int target = {row['target']};\n" + clone
            )
        kernels[c] = shapes[key]
    parts.append("static void batch_special_notify(Batch *b, int v) { switch (v) {")
    for v, adjacent in enumerate(spec.adjacency):
        parts.append(
            f"case {v}: "
            + "".join(f"batch_enqueue(b, {c});" for c in adjacent)
            + "break;"
        )
    parts.append("default: break; } }")
    for c, row in enumerate(spec.rows):
        words = row["local"][-1]
        lines = [f"static int batch_step_{c}(Batch *b) {{", "int status;"]
        for j, v in enumerate(row["scope"]):
            lines.append(
                f"memcpy(b->input+{row['local'][j]}, "
                f"b->domains+{spec.word_offsets[v]}, {8 * spec.word_lengths[v]});"
            )
        lines += [f"if (batch_cached(b, {c}, {words})) return 1;", "++b->counts[1];"]
        if row["kind"] == 0:
            call = f"alldiff_supports(b->plans[{c}], b->input, b->output)"
        elif row["op"] == 0:
            if row["target"] < 0 or row["target"] > 16384:
                call = "0"
            else:
                call = f"{kernels[c]}(b->plans[{c}], b->input, b->output)"
        else:
            call = (
                f"batch_inequality(b->plans[{c}], b->input, "
                f"{row['target']}, {row['op']}, b->output)"
            )
        lines += [
            f"status = {call};",
            "if (status <= 0) return status;",
            f"memcpy(b->cache+{spec.cache_offsets[c]}, b->output, {8 * words}); "
            f"b->cached[{c}] = 1;",
        ]
        for j, v in enumerate(row["scope"]):
            lines += [
                f"status = batch_store(b, {c}, {v}, {row['local'][j]}, "
                f"{spec.word_offsets[v]}, {spec.word_lengths[v]});",
                "if (status < 0) return status;",
            ]
        parts.append("\n".join([*lines, "return 1; }"]))
    parts.append("static int batch_special_step(Batch *b, int c) { switch (c) {")
    for c in range(len(spec.rows)):
        parts.append(f"case {c}: return batch_step_{c}(b);")
    parts.append("default: return -1; } }")
    return "\n".join(parts)


class BatchKernel(Kernel):
    def __init__(self, library):
        self.library = ct.CDLL(str(Path(library).resolve()))
        ip, up, vp = (
            ct.POINTER(ct.c_int),
            ct.POINTER(ct.c_uint64),
            ct.POINTER(ct.c_void_p),
        )
        self.key = self.library.batch_model_key
        self.key.argtypes, self.key.restype = [], ct.c_char_p
        for name, args, result in [
            ("sum_create", [ct.c_int, ip, ip], ct.c_void_p),
            ("alldiff_create", [ct.c_int, ct.c_int, ip, ip], ct.c_void_p),
            ("sum_free", [ct.c_void_p], None),
            ("alldiff_free", [ct.c_void_p], None),
            ("batch_free", [ct.c_void_p], None),
            (
                "batch_create",
                [ct.c_int, ct.c_int, ip, ip, ip, ip, ip, ip, vp],
                ct.c_void_p,
            ),
            (
                "batch_run",
                [
                    ct.c_void_p,
                    up,
                    up,
                    ct.c_int,
                    up,
                    ct.c_int,
                    up,
                    ct.c_int,
                    ct.c_double,
                ],
                ct.c_int,
            ),
        ]:
            function = getattr(self.library, name)
            function.argtypes, function.restype = args, result
            setattr(self, name, function)

    @classmethod
    def build_model(cls, output, spec=None, *, cache_dir=None):
        generated = source(spec)
        path = Path(output).with_suffix(".c")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generated)
        kernel, report = super().build(
            output,
            cache_dir=cache_dir or "generated/neural_attention/model_batch_cache",
            source=path,
        )
        report.update(
            source_bytes=len(generated.encode()),
            binary_bytes=Path(report["library"]).stat().st_size,
            model_key=spec.key if spec else None,
        )
        return kernel, report


class BatchContext:
    def __init__(self, spec, kernel, *, audit=False):
        key = kernel.key().decode()
        if key and key != spec.key:
            raise ValueError("specialized library belongs to another model")
        self.spec, self.kernel = spec, kernel
        handles = []
        try:
            for row in spec.rows:
                args = (
                    len(row["scope"]),
                    int_array(row["starts"]),
                    int_array(row["values"]),
                )
                handle = (
                    kernel.alldiff_create(args[0], row["count"], args[1], args[2])
                    if row["kind"] == 0
                    else kernel.sum_create(*args)
                )
                if not handle:
                    raise ValueError("native plan creation rejected")
                handles.append(handle)
            starts = offsets([len(r["scope"]) for r in spec.rows])
            self.handle = kernel.batch_create(
                len(spec.names),
                len(spec.rows),
                int_array(spec.lengths),
                int_array(starts),
                int_array([v for r in spec.rows for v in r["scope"]]),
                int_array([r["kind"] for r in spec.rows]),
                int_array([r["op"] for r in spec.rows]),
                int_array([r["target"] for r in spec.rows]),
                (ct.c_void_p * len(handles))(*handles),
            )
            if not self.handle:
                raise ValueError("native batch workspace rejected")
        except Exception:
            for row, handle in zip(spec.rows, handles, strict=False):
                (kernel.alldiff_free if row["kind"] == 0 else kernel.sum_free)(handle)
            raise
        self._finalizer = weakref.finalize(self, kernel.batch_free, self.handle)
        self.outputs = (ct.c_uint64 * spec.word_offsets[-1])()
        self.counts = (ct.c_uint64 * 6)()
        self.log_capacity = sum(spec.lengths) if audit else 0
        self.log_stride = max(spec.word_lengths) + 2
        self.log = (
            (ct.c_uint64 * (self.log_capacity * self.log_stride))() if audit else None
        )

    def execute(self, packed, *, reset=True, max_revisions=1000000, seconds=-1):
        if len(packed) != self.spec.word_offsets[-1]:
            raise ValueError("incorrect packed mask length")
        return self.kernel.batch_run(
            self.handle,
            packed,
            self.outputs,
            reset,
            self.log,
            self.log_capacity,
            self.counts,
            max_revisions,
            seconds,
        )

    def result(self, status):
        if status < 0:
            raise RuntimeError(f"native propagation interrupted/rejected: {status}")
        log = None
        if self.log is not None:
            log = []
            for k in range(self.counts[3]):
                base = k * self.log_stride
                c, v = int(self.log[base]), int(self.log[base + 1])
                mask = sum(
                    int(self.log[base + w + 2]) << (64 * w)
                    for w in range(self.spec.word_lengths[v])
                )
                log.append((c, v, mask))
        return dict(
            consistent=bool(status),
            masks=self.spec.decode(self.outputs),
            revisions=int(self.counts[0]),
            support_calls=int(self.counts[1]),
            cache_hits=int(self.counts[2]),
            reductions=int(self.counts[3]),
            digest=int(self.counts[4]),
            failure=int(self.counts[5]) - 1,
            log=log,
        )

    def run(self, masks, **kwargs):
        return self.result(self.execute(self.spec.encode(masks), **kwargs))


class PythonEpisode:
    """Same deterministic queue as the C pair, using original Python filtering."""

    def __init__(self, spec):
        self.spec = spec
        self.domains = FiniteDomains(spec.model.variables)
        numeric, different = NumericPlans(self.domains), AllDifferentPlans(self.domains)
        self.plans = []
        for i, constraint in enumerate(spec.model.constraints):
            plan = (
                different.get(i, constraint)
                if isinstance(constraint, AllDifferentConstraint)
                else numeric.get(i, constraint)
            )
            if plan is None:
                raise ValueError("Python reference plan unavailable")
            self.plans.append(plan)

    def run(self, masks):
        self.spec.encode(masks)  # Validate representation before direct replay setup.
        self.domains._masks[:] = masks
        digest, revisions, log, failure = SEED, 0, [], -1
        if not all(masks):
            return dict(
                consistent=False,
                masks=tuple(masks),
                revisions=0,
                reductions=0,
                digest=digest,
                failure=-1,
                log=[],
            )
        pending, queued = deque(range(len(self.plans))), set(range(len(self.plans)))
        while pending:
            c = pending.popleft()
            queued.remove(c)
            revisions += 1
            row, constraint, plan = (
                self.spec.rows[c],
                self.spec.model.constraints[c],
                self.plans[c],
            )
            answer = (
                plan.supports(self.domains)
                if row["kind"] == 0
                else plan.supports(self.domains, constraint.target)
            )
            if answer is None:
                failure = c
                break
            for v, supported in zip(row["scope"], answer, strict=True):
                before = self.domains._masks[v]
                after = before & supported
                if before == after:
                    continue
                self.domains._masks[v] = after
                log.append((c, v, after))
                for value in (
                    c,
                    v,
                    *(
                        after >> (64 * w) & UINT64
                        for w in range(self.spec.word_lengths[v])
                    ),
                ):
                    digest = ((digest ^ value) * PRIME) & UINT64
                for incident in self.spec.adjacency[v]:
                    if incident not in queued:
                        pending.append(incident)
                        queued.add(incident)
        return dict(
            consistent=failure < 0,
            masks=tuple(self.domains._masks),
            revisions=revisions,
            reductions=len(log),
            digest=digest,
            failure=failure,
            log=log,
        )


# Experimental integration: ordinary Python search/trail, one native fixpoint call.
class BatchNative(NativeState):
    def __init__(self, model, spec, kernel):
        if spec.model != model:
            raise ValueError("batch spec/model mismatch")
        super().__init__(model)
        self.batch = BatchContext(spec, kernel, audit=True)
        self.batch_totals = dict(
            episodes=0, revisions=0, support_calls=0, cache_hits=0, reductions=0
        )

    def propagate(self, *, deadline=None, facts=None, objective_cut=None):
        if facts is not None or objective_cut is not None:
            raise ValueError("batch experiment supports pure finite feasibility")
        if deadline is not None and perf_counter() >= deadline:
            self._initialized = False
            raise TimeoutError("native batch deadline")
        spec, context = self.batch.spec, self.batch
        packed = spec.encode(self.domains._masks)
        remaining = -1 if deadline is None else max(0, deadline - perf_counter())
        status = context.execute(packed, reset=not self._initialized, seconds=remaining)
        self.revisions += int(context.counts[0])
        self.batch_totals["episodes"] += 1
        for key, i in [
            ("revisions", 0),
            ("support_calls", 1),
            ("cache_hits", 2),
            ("reductions", 3),
        ]:
            self.batch_totals[key] += int(context.counts[i])
        if status == -4 or deadline is not None and perf_counter() >= deadline:
            self._initialized = False
            raise TimeoutError("native batch deadline")
        if status < 0:
            raise RuntimeError(f"native batch interrupted/rejected: {status}")
        self._initialized = True
        self.domains.take_changed()
        raw = ct.string_at(context.log, int(context.counts[3]) * context.log_stride * 8)
        stride = context.log_stride * 8
        for base in range(0, len(raw), stride):
            c = int.from_bytes(raw[base : base + 8], "little")
            v = int.from_bytes(raw[base + 8 : base + 16], "little")
            mask = int.from_bytes(
                raw[base + 16 : base + 16 + spec.byte_lengths[v]], "little"
            )
            self.domains.retain_mask(
                spec.names[v], mask, self.model.constraints[c].name
            )
        self.domains.take_changed()
        if status == 0:
            c = int(context.counts[5]) - 1
            self.failure = self.model.constraints[c].name if c >= 0 else None
            return False
        return self.failure is None and not self.domains.empty
