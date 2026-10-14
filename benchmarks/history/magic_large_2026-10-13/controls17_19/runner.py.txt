"""Measured sequential restarts toward 20x20, with independently checked witnesses."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
from pathlib import Path
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query, ResultStatus
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .magic_portfolio import schedule
from .magic_search_tuning import RankedDomains, RankedState, prepare
from .sum_distinct import DistinctSumState


def settings(seeds):
    specs = list(schedule(seeds))
    transfer = dict(
        policy="dom_wdeg", order="random", tie="random", symmetry=False, seed=1
    )
    specs = [specs[0], transfer, *(s for s in specs[1:] if s != transfer)]
    extra = [
        dict(policy=p, order=o, tie="degree", symmetry=True, seed=0)
        for p, o in [
            ("mrv", "line_average"),
            ("dom_wdeg", "line_average"),
            ("mrv", "line_midpoints"),
        ]
    ]
    return specs[:5] + extra + specs[5:]


def trial(size, spec, mode, limit, *, progress_interval=5):
    gc.collect()  # cleanup is outside the attempt, inside portfolio wall time
    started = perf_counter()
    original, model = prepare(
        size, spec["order"], spec["tie"], spec["symmetry"], seed=spec["seed"]
    )
    state = RankedState.__new__(RankedState)
    state.native = (
        NativeState(model)
        if mode == "native"
        else DistinctSumState(
            model,
            max_active=3,
            max_candidates=24 if mode == "exact" else 0,
            pair_fast=True,
            exact_three=True,
            max_pairs=64 if mode == "pairs" else 0,
        )
    )
    state.model = model
    state.domains = RankedDomains(state.native.domains, model, spec["order"])
    prepared = perf_counter()
    observations = dict(max_depth=0, max_fixed_observed=0)
    next_report = prepared + progress_interval

    def progress(event):
        nonlocal next_report
        observations["max_depth"] = max(observations["max_depth"], event.depth)
        now = perf_counter()
        if event.event == "node" and now >= next_report:
            fixed = sum(state.domains.size(v.name) == 1 for v in model.variables)
            observations["max_fixed_observed"] = max(
                observations["max_fixed_observed"], fixed
            )
            print(
                json.dumps(
                    dict(
                        event="progress",
                        size=size,
                        mode=mode,
                        **spec,
                        elapsed_seconds=now - started,
                        nodes=event.explored_nodes,
                        depth=event.depth,
                        fixed_at_observation=fixed,
                    )
                ),
                flush=True,
            )
            next_report = now + progress_interval

    remaining = limit - (prepared - started)
    result = (
        search(
            state,
            Query(time_limit_seconds=remaining),
            policy=spec["policy"],
            on_progress=progress,
        )
        if remaining > 0
        else None
    )
    finished = perf_counter()
    if result is not None and result.status is ResultStatus.INFEASIBLE:
        raise AssertionError("blank normal magic square is feasible")
    squares = (
        [validate(size, s.assignment, original) for s in result.solutions]
        if result
        else []
    )
    if squares:
        observations["max_fixed_observed"] = size * size
    return dict(
        size=size,
        mode=mode,
        **spec,
        total_seconds=finished - started,
        prepare_seconds=prepared - started,
        search_seconds=finished - prepared,
        solved=bool(squares),
        termination=result.termination.value if result else "setup_budget",
        nodes=result.explored_nodes if result else 0,
        failures=result.failed_branches if result else 0,
        revisions=result.constraint_revisions if result else 0,
        squares=squares,
        observations=observations,
        stats=state.native.stats if mode != "native" else {},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[15, 17, 18, 19, 20])
    parser.add_argument("--mode", choices=["native", "exact", "pairs"], default="exact")
    parser.add_argument("--budget", type=float, default=60)
    parser.add_argument("--slice", type=float, default=10)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(20)))
    parser.add_argument(
        "--settings", type=Path, help="explicit ordered settings list for replay"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.budget <= 0 or args.slice <= 0 or any(n < 3 for n in args.sizes):
        parser.error("positive budgets and sizes >=3 required")
    args.output.mkdir(parents=True, exist_ok=False)
    specs = (
        json.loads(args.settings.read_text()) if args.settings else settings(args.seeds)
    )
    paths = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        *(
            Path(__file__).with_name(n)
            for n in [
                "sum_distinct.py",
                "magic_portfolio.py",
                "magic_search_tuning.py",
                "optimize_magic6.py",
            ]
        ),
        Path("benchmarks/alice_magic.py"),
    ]
    if args.settings:
        paths.append(args.settings)
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    frozen = dict(
        python=platform.python_version(),
        platform=platform.platform(),
        pythonhashseed=os.environ.get("PYTHONHASHSEED"),
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        schedule=specs,
        source_hashes=hashes,
        scope=(
            "Blank-square generic DFS; no constructed solution, hint or initial "
            "assignment. Attempt includes setup/search/solution explanations; "
            "portfolio includes failed attempts, cleanup, independent validation "
            "and recording. Imports excluded. Progress observers included; "
            "observed fixed counts do not estimate remaining time."
        ),
    )
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    (args.output / "runner.py.txt").write_bytes(Path(__file__).read_bytes())
    summaries = []
    for size in args.sizes:
        started = perf_counter()
        attempts = []
        for index, spec in enumerate(specs):
            remaining = args.budget - (perf_counter() - started)
            if remaining <= 0:
                break
            row = dict(
                attempt=index,
                limit_seconds=min(args.slice, remaining),
                **trial(size, spec, args.mode, min(args.slice, remaining)),
            )
            attempts.append(row)
            with (args.output / "runs.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(
                json.dumps(
                    {k: v for k, v in row.items() if k not in ["squares", "stats"]}
                ),
                flush=True,
            )
            if row["solved"]:
                break
        winner = next((r for r in attempts if r["solved"]), None)
        summary = dict(
            size=size,
            mode=args.mode,
            solved=winner is not None,
            portfolio_seconds=perf_counter() - started,
            attempts=len(attempts),
            nodes=sum(r["nodes"] for r in attempts),
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
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha
        for p, sha in hashes.items()
    )


if __name__ == "__main__":
    main()
