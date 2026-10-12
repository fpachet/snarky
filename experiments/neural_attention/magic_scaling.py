"""Continue blank magic-square searches with saved settings and exact validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query, ResultStatus
from snarky.finite.search import search

from .magic_search_tuning import RankedState, prepare

PRESET = Path(__file__).with_name("magic_best_parameters.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=list(range(11, 17)))
    parser.add_argument("--limit", type=float, default=60)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1 or args.limit <= 0 or any(n < 3 for n in args.sizes):
        parser.error("require positive repeats/limit and square sizes at least three")
    args.output.mkdir(parents=True, exist_ok=False)
    preset = json.loads(PRESET.read_text())
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        PRESET,
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    frozen = {
        "python": platform.python_version(),
        "sizes": args.sizes,
        "limit": args.limit,
        "repeats": args.repeats,
        "preset": preset,
        "source_hashes": hashes,
    }
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    records, summaries = [], []
    for size in args.sizes:
        settings = {
            **preset["default"],
            **preset["known_size_overrides"].get(str(size), {}),
        }
        print(json.dumps({"event": "start_size", "size": size, **settings}), flush=True)
        runs = []
        for repeat in range(args.repeats):
            started = perf_counter()
            original, model = prepare(
                size, settings["order"], settings["tie"], settings["symmetry"]
            )
            prepared = perf_counter()
            state = RankedState(model, settings["order"])
            result = search(
                state, Query(time_limit_seconds=args.limit), policy=settings["policy"]
            )
            finished = perf_counter()
            if result.status is ResultStatus.INFEASIBLE:
                raise AssertionError("blank magic square is feasible")
            squares = [validate(size, s.assignment, original) for s in result.solutions]
            row = {
                "size": size,
                "repeat": repeat,
                **settings,
                "seconds": finished - prepared,
                "total_seconds": finished - started,
                "solved": bool(squares),
                "termination": result.termination.value,
                "nodes": result.explored_nodes,
                "failures": result.failed_branches,
                "revisions": result.constraint_revisions,
                "squares": squares,
            }
            records.append(row)
            runs.append(row)
            with (args.output / "runs.jsonl").open("a") as handle:
                handle.write(json.dumps(row) + "\n")
            print(
                json.dumps({k: v for k, v in row.items() if k != "squares"}), flush=True
            )
            # Timeouts do not stop testing larger sizes or get silently retried.
            if not squares:
                break
        solved = [r for r in runs if r["solved"]]
        summary = {
            "size": size,
            **settings,
            "magic_sum": size * (size * size + 1) // 2,
            "completed": len(solved),
            "attempted": len(runs),
            "limit_seconds": args.limit,
            "median_total_seconds": median(r["total_seconds"] for r in solved)
            if solved
            else None,
            "nodes": sorted({r["nodes"] for r in runs}),
            "square": solved[0]["squares"][0] if solved else None,
        }
        summaries.append(summary)
        (args.output / "summary.json").write_text(
            json.dumps(summaries, indent=2) + "\n"
        )
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )


if __name__ == "__main__":
    main()
