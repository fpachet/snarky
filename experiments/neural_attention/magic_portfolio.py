"""Bounded sequential restarts for blank magic squares, including failed attempts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query, ResultStatus
from snarky.finite.search import search

from .magic_search_tuning import RankedState, prepare


def schedule(seeds):
    """Fixed before any target run; first try the previously discovered 11x11 winner."""
    yield dict(policy="dom_wdeg", order="random", tie="random", symmetry=True, seed=1)
    for seed in seeds:
        for policy, symmetry in (
            ("dom_wdeg", True),
            ("mrv", True),
            ("dom_wdeg", False),
        ):
            spec = dict(
                policy=policy,
                order="random",
                tie="random",
                symmetry=symmetry,
                seed=seed,
            )
            if not (seed == 1 and policy == "dom_wdeg" and symmetry):
                yield spec
        if seed == seeds[0]:
            yield dict(
                policy="mrv", order="middle", tie="degree", symmetry=True, seed=0
            )


def trial(size, spec, limit):
    started = perf_counter()
    original, model = prepare(
        size, spec["order"], spec["tie"], spec["symmetry"], seed=spec["seed"]
    )
    state = RankedState(model, spec["order"])
    # Preparation is charged against the attempt and the overall portfolio budget.
    remaining = limit - (perf_counter() - started)
    if remaining <= 0:
        return dict(
            size=size,
            **spec,
            total_seconds=perf_counter() - started,
            solved=False,
            termination="setup_budget",
            nodes=0,
            failures=0,
            revisions=0,
            squares=[],
        )
    result = search(state, Query(time_limit_seconds=remaining), policy=spec["policy"])
    finished = perf_counter()
    if result.status is ResultStatus.INFEASIBLE:
        raise AssertionError("blank normal magic square is feasible")
    squares = [validate(size, s.assignment, original) for s in result.solutions]
    return dict(
        size=size,
        **spec,
        total_seconds=finished - started,
        solved=bool(squares),
        termination=result.termination.value,
        nodes=result.explored_nodes,
        failures=result.failed_branches,
        revisions=result.constraint_revisions,
        squares=squares,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[12, 13, 15, 16])
    parser.add_argument("--budget", type=float, default=60)
    parser.add_argument(
        "--transfer-limit", type=float, help="default: 10s below size 15, otherwise 15s"
    )
    parser.add_argument(
        "--slice", type=float, help="default: 4s below size 15, otherwise 15s"
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(20)))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(
        v is not None and v <= 0 for v in (args.budget, args.transfer_limit, args.slice)
    ) or any(n < 3 for n in args.sizes):
        parser.error("require positive time budgets and sizes at least three")
    args.output.mkdir(parents=True, exist_ok=False)
    specs = list(schedule(args.seeds))
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    frozen = dict(
        python=platform.python_version(),
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        schedule=specs,
        budgets_by_size={
            size: dict(
                transfer=args.transfer_limit or (15 if size >= 15 else 10),
                slice=args.slice or (15 if size >= 15 else 4),
            )
            for size in args.sizes
        },
        source_hashes=hashes,
        scope=(
            "Fixed sequential schedule on blank squares. Portfolio wall time includes "
            "setup, failures, validation and recording; interpreter imports excluded. "
            "Timeouts are not infeasibility."
        ),
    )
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    (args.output / "runner_snapshot.py").write_text(Path(__file__).read_text())
    summaries = []
    for size in args.sizes:
        started = perf_counter()
        attempts = []
        for index, spec in enumerate(specs):
            remaining = args.budget - (perf_counter() - started)
            if remaining <= 0:
                break
            budgets = frozen["budgets_by_size"][size]
            limit = min(
                remaining, budgets["transfer"] if index == 0 else budgets["slice"]
            )
            row = dict(attempt=index, limit_seconds=limit, **trial(size, spec, limit))
            attempts.append(row)
            with (args.output / "runs.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(
                json.dumps({k: v for k, v in row.items() if k != "squares"}), flush=True
            )
            if row["solved"]:
                break
        elapsed = perf_counter() - started
        winner = next((r for r in attempts if r["solved"]), None)
        summary = dict(
            size=size,
            solved=winner is not None,
            portfolio_seconds=elapsed,
            attempts=len(attempts),
            nodes=sum(r["nodes"] for r in attempts),
            failures=sum(r["failures"] for r in attempts),
            transfer_solved=attempts[0]["solved"],
            winner=winner,
        )
        summaries.append(summary)
        (args.output / "summary.json").write_text(
            json.dumps(summaries, indent=2) + "\n"
        )
        print(
            json.dumps({k: v for k, v in summary.items() if k != "winner"}), flush=True
        )
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )


if __name__ == "__main__":
    main()
