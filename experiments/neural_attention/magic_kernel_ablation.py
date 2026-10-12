"""Interleave the saved and current equality kernels on identical fresh searches."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from random import Random
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.numeric import NumericPlan
from snarky.finite.search import search

from .magic_search_tuning import RankedState, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    # A saved local source snapshot, with its hash recorded below. Only its
    # equality method is reused; other state, propagation and search code match.
    spec = importlib.util.spec_from_file_location("snarky.finite._before", args.before)
    before = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(before)
    current = NumericPlan._equality_supports
    kernels = {"before": before.NumericPlan._equality_supports, "current": current}
    frozen = {
        "repeats": args.repeats,
        "symmetry": True,
        "limit_seconds": 10,
        "source_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                *Path("src/snarky").rglob("*.py"),
                Path(__file__),
                args.before,
                Path("experiments/neural_attention/magic_search_tuning.py"),
                Path("experiments/neural_attention/optimize_magic6.py"),
            ]
        },
    }
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    cases = [
        (size, order, kernel, repeat)
        for size in (6, 7)
        for order in ("middle", "middle_high")
        for kernel in kernels
        for repeat in range(args.repeats)
    ]
    Random(241026).shuffle(cases)
    try:
        for size, order, kernel, repeat in cases:
            NumericPlan._equality_supports = kernels[kernel]
            started = perf_counter()
            original, model = prepare(size, order, "row_major", True)
            result = search(
                RankedState(model, order), Query(time_limit_seconds=10), policy="mrv"
            )
            elapsed = perf_counter() - started
            if not result.solutions:
                raise AssertionError("previously completed case did not finish")
            squares = [validate(size, s.assignment, original) for s in result.solutions]
            row = {
                "size": size,
                "order": order,
                "kernel": kernel,
                "repeat": repeat,
                "total_seconds": elapsed,
                "nodes": result.explored_nodes,
                "revisions": result.constraint_revisions,
                "squares": squares,
            }
            with (args.output / "runs.jsonl").open("a") as handle:
                handle.write(json.dumps(row) + "\n")
            print(
                json.dumps({k: v for k, v in row.items() if k != "squares"}), flush=True
            )
    finally:
        NumericPlan._equality_supports = current


if __name__ == "__main__":
    main()
