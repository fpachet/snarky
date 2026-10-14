"""Measure compiling unrolled C loops for individual captured residual states."""

from __future__ import annotations

import argparse
import ctypes as ct
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from statistics import median
from time import perf_counter

from .magic_residual_enumeration import Compiler, Kernel
from .magic_residual_evaluation import check_witness
from .magic_residual_study import freeze
from .magic_search_tuning import prepare


def generate(residual):
    """Same static-bound checks as mode 2, with literal domains and unrolled depth."""
    code = [
        "#include <stdint.h>",
        "int specialized(uint64_t limit, int *first, uint64_t *counts) {",
        "uint64_t visits = 0; unsigned char used[4096] = {0};",
        "counts[0] = counts[1] = counts[2] = 0;",
    ]
    impossible_constant = any(
        not terms
        and not (target == 0 if op == 0 else target >= 0 if op == 1 else target <= 0)
        for op, terms, target in residual.rows
    )
    if residual.invalid or impossible_constant:
        return "\n".join([*code, "return 0; }"])
    for i, domain in enumerate(residual.domains):
        code.append(f"static const int d{i}[] = {{{','.join(map(str, domain))}}};")
    for i, domain in enumerate(residual.domains):
        code.extend(
            [
                f"for (int p{i}=0; p{i}<{len(domain)}; ++p{i}) {{",
                "if (visits >= limit) { counts[0]=visits; return 2; }",
                "++visits;",
                f"int x{i}=d{i}[p{i}];",
                f"if (used[x{i}]) continue;",
            ]
        )
        for op, terms, target in residual.rows:
            if not any(v == i for v, _ in terms):
                continue
            expression = (
                " + ".join(f"({c}LL * x{v})" for v, c in terms if v <= i) or "0LL"
            )
            lo = hi = 0
            for v, c in terms:
                if v > i:
                    values = [c * x for x in residual.domains[v]]
                    lo += min(values)
                    hi += max(values)
            clauses = []
            if op in (0, 1):
                clauses.append(f"({expression}) + ({lo}LL) <= ({target}LL)")
            if op in (0, 2):
                clauses.append(f"({expression}) + ({hi}LL) >= ({target}LL)")
            code.append(f"if (!({' && '.join(clauses)})) continue;")
        code.append(f"used[x{i}] = 1;")
    for i in range(len(residual.domains)):
        code.append(f"first[{i}]=x{i};")
    code.append("counts[0]=visits; counts[1]=counts[2]=1; return 1;")
    for i in reversed(range(len(residual.domains))):
        code.extend([f"used[x{i}] = 0;", "}"])
    code.append("counts[0]=visits; return 0; }")
    return "\n".join(code) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    freeze(args.output, {k: str(v) for k, v in vars(args).items()})
    kernel, compile_generic = Kernel.build(args.output / "generic.so")
    rows = [
        json.loads(s) for s in (args.replay / "runs.jsonl").read_text().splitlines()
    ]
    selected = []
    for n in (8, 9, 13, 16):
        group = [r for r in rows if r["size"] == n and not r["invalid"]]
        completed = [r for r in group if r["variants"]["2"]["status"] != 2]
        if completed:
            selected.append(max(completed, key=lambda r: r["variants"]["2"]["visits"]))
        if n == 16:
            pending = [r for r in group if r["variants"]["2"]["status"] == 2]
            if pending:
                selected.append(pending[0])
    reports = []
    for index, row in enumerate(selected):
        with gzip.open(args.capture / f"states_{row['size']}.json.gz", "rt") as f:
            capture = json.load(f)
        spec = capture["settings"]
        _, model = prepare(
            row["size"],
            spec["order"],
            spec["tie"],
            spec["symmetry"],
            seed=spec.get("seed", 0),
        )
        sample = next(s for s in capture["samples"] if s["node"] == row["node"])
        residual = Compiler(model).extract(sample["masks"])
        generic = kernel.prepare(residual)
        source = args.output / f"case_{index}.c"
        source.write_text(generate(residual))
        library_path = args.output / f"case_{index}.so"
        started = perf_counter()
        process = subprocess.run(
            ["cc", "-O3", "-shared", "-fPIC", str(source), "-o", str(library_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        compilation = perf_counter() - started
        library = ct.CDLL(str(library_path.resolve()))
        function = library.specialized
        function.argtypes = [ct.c_uint64, ct.POINTER(ct.c_int), ct.POINTER(ct.c_uint64)]
        function.restype = ct.c_int
        first = (ct.c_int * len(residual.domains))()
        counts = (ct.c_uint64 * 3)()
        generic_times, specialized_times = [], []
        for _ in range(7):
            t = perf_counter()
            expected = generic(2, 200000)
            generic_times.append(perf_counter() - t)
            t = perf_counter()
            status = function(200000, first, counts)
            specialized_times.append(perf_counter() - t)
            assert status == expected["status"]
            assert list(counts) == [
                expected[k] for k in ("visits", "leaves", "solutions")
            ]
            if status == 1:
                assert list(first) == expected["witness"]
                check_witness(residual, list(first))
        g, s = median(generic_times), median(specialized_times)
        report = dict(
            size=row["size"],
            node=row["node"],
            remaining=len(residual.indices),
            status=status,
            visits=counts[0],
            compile_seconds=compilation,
            command=process.args,
            stderr=process.stderr,
            generic_kernel_seconds=g,
            specialized_kernel_seconds=s,
            break_even_calls=compilation / (g - s) if g > s else None,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        reports.append(report)
        print(json.dumps(report), flush=True)
    (args.output / "summary.json").write_text(
        json.dumps(dict(generic_compilation=compile_generic, cases=reports), indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
