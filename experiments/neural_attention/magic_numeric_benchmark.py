"""Compare numeric optimizations at identical search work, with isolated ablations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite import numeric, propagation
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_search_tuning import RankedDomains, RankedState, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[6, 7, 8, 9, 10, 11, 14, 18, 20]
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--variants",
        nargs="+",
        default=["baseline", "optimized"],
        choices=["baseline", "rank_only", "span_only", "optimized"],
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location(
        "snarky.finite._numeric_before", args.before
    )
    before = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(before)
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        args.before,
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    frozen = {
        "python": platform.python_version(),
        "source_hashes": hashes,
        "repeats": args.repeats,
        "sizes": args.sizes,
        "variants": args.variants,
        "scope": (
            "Median sequential wall-clock timings of deterministic fixed-work "
            "searches. Setup included in total; imports and validation excluded. "
            "Unsolved large sizes use node limits, not time-limited counts."
        ),
    }
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    original_class, original_span = propagation.NumericPlans, numeric._MAX_EQUALITY_SPAN
    rows, signatures = [], {}
    rng = Random(20261012)
    try:
        for size in args.sizes:
            order = "middle_high" if size in (7, 8) else "middle"
            tie = "degree" if size >= 14 else "row_major"
            symmetry = size in (6, 7, 8) or size >= 14
            max_nodes = 1500 if size == 11 else 30 if size >= 17 else None
            specs = [
                (variant, repeat)
                for repeat in range(args.repeats)
                for variant in args.variants
            ]
            rng.shuffle(specs)
            for variant, repeat in specs:
                module = before if variant in ("baseline", "span_only") else numeric
                span = 4096 if variant in ("baseline", "rank_only") else original_span
                module._MAX_EQUALITY_SPAN = span
                propagation.NumericPlans = module.NumericPlans
                started = perf_counter()
                original, model = prepare(size, order, tie, symmetry)
                state = RankedState.__new__(RankedState)
                state.model = model
                state.native = propagation.NativeState(model)
                state.domains = RankedDomains(state.native.domains, model, order)
                prepared = perf_counter()
                result = search(
                    state,
                    Query(max_nodes=max_nodes, time_limit_seconds=120),
                    policy="mrv",
                )
                finished = perf_counter()
                squares = [
                    validate(size, s.assignment, original) for s in result.solutions
                ]
                signature = (
                    result.explored_nodes,
                    result.failed_branches,
                    result.constraint_revisions,
                    result.termination.value,
                    squares,
                )
                if size not in signatures:
                    signatures[size] = signature
                assert signatures[size] == signature, (
                    f"different search work for {size}: {variant}"
                )
                assert state.native.domains.snapshot() == model.domains
                assert not state.native.domains.removals
                row = {
                    "size": size,
                    "variant": variant,
                    "repeat": repeat,
                    "order": order,
                    "tie": tie,
                    "symmetry": symmetry,
                    "max_nodes": max_nodes,
                    "span_limit": span,
                    "seconds": finished - prepared,
                    "total_seconds": finished - started,
                    "nodes": result.explored_nodes,
                    "failures": result.failed_branches,
                    "revisions": result.constraint_revisions,
                    "termination": result.termination.value,
                    "solved": bool(squares),
                    "compiled_plans": sum(
                        plan is not None
                        for _, plan in state.native._numeric.plans.values()
                    ),
                    "fallback_plans": sum(
                        plan is None for _, plan in state.native._numeric.plans.values()
                    ),
                    "squares": squares,
                }
                rows.append(row)
                with (args.output / "runs.jsonl").open("a") as handle:
                    handle.write(json.dumps(row) + "\n")
                print(
                    json.dumps({k: v for k, v in row.items() if k != "squares"}),
                    flush=True,
                )
    finally:
        propagation.NumericPlans = original_class
        numeric._MAX_EQUALITY_SPAN = original_span
    summaries = []
    for size in args.sizes:
        variants = {}
        for variant in args.variants:
            runs = [r for r in rows if r["size"] == size and r["variant"] == variant]
            variants[variant] = {
                "median_total_seconds": median(r["total_seconds"] for r in runs),
                "median_solve_seconds": median(r["seconds"] for r in runs),
                "nodes": runs[0]["nodes"],
                "revisions": runs[0]["revisions"],
                "solved": runs[0]["solved"],
                "compiled_plans": runs[0]["compiled_plans"],
                "fallback_plans": runs[0]["fallback_plans"],
            }
        summary = {"size": size, "variants": variants}
        if "baseline" in variants and "optimized" in variants:
            summary["speedup"] = (
                variants["baseline"]["median_total_seconds"]
                / variants["optimized"]["median_total_seconds"]
            )
        summaries.append(summary)
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")


if __name__ == "__main__":
    main()
