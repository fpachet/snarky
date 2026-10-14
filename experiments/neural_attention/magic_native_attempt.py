"""Time-limited first-solution attempt with native SUM/ALLDIFF and throughput logs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .alldiff_kernel import AllDiffKernel
from .alldiff_kernel import enable as enable_alldiff
from .magic_residual_enumeration import Kernel
from .magic_residual_evaluation import HybridState
from .magic_residual_study import freeze, settings
from .magic_search_tuning import prepare
from .sum_kernel import SumKernel
from .sum_kernel import enable as enable_sum


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--limit", type=float, default=300)
    parser.add_argument("--sample-seconds", type=float, default=5)
    args = parser.parse_args()
    if args.size < 3 or args.limit <= 0 or args.sample_seconds <= 0:
        parser.error("require size >=3 and positive time/sample limits")
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    config.update(
        remaining=20,
        mode=4,
        work_limit=200000,
        scope=(
            "First solution; no hints or constructed square; cached native libraries; "
            "search time includes progress callbacks and rollback, excludes model "
            "setup/compilation/loading/validation/output."
        ),
        node_definition=(
            "Entered DFS nodes, including a potentially unfinished final "
            "propagation; not residual enumeration visits."
        ),
    )
    freeze(
        args.output,
        config,
        extra_files=[
            Path(__file__),
            Path(__file__).with_name("sum_kernel.py"),
            Path(__file__).with_name("sum_support.c"),
            Path(__file__).with_name("alldiff_kernel.py"),
            Path(__file__).with_name("alldiff_support.c"),
        ],
    )
    residual, residual_build = Kernel.build(args.output / "residual.so")
    sums, sum_build = SumKernel.build(args.output / "sum.so")
    alldiff, alldiff_build = AllDiffKernel.build(args.output / "alldiff.so")
    save(
        args.output / "compile.json",
        dict(
            residual=residual_build,
            sums=sum_build,
            alldiff=alldiff_build,
        ),
    )
    spec = settings(args.size)
    started = perf_counter()
    original, model = prepare(
        args.size,
        spec["order"],
        spec["tie"],
        spec["symmetry"],
        seed=spec.get("seed", 0),
    )
    state = HybridState(model, spec["order"], residual, 20, 4, 200000)
    enable_sum(state.native, sums)
    enable_alldiff(state.native, alldiff)
    setup_seconds = perf_counter() - started
    milestones = []
    minimum, maximum_depth = args.size**2, 0

    def progress(event):
        nonlocal minimum, maximum_depth
        if event.event == "node":
            minimum = min(minimum, state.native.domains._unfixed_count)
            maximum_depth = max(maximum_depth, event.depth)
        previous = milestones[-1] if milestones else dict(seconds=0, nodes=0)
        if (
            event.event != "finished"
            and event.elapsed_seconds - previous["seconds"] < args.sample_seconds
        ):
            return
        elapsed = event.elapsed_seconds
        row = dict(
            event=event.event,
            seconds=elapsed,
            nodes=event.explored_nodes,
            failures=event.failed_branches,
            revisions=event.constraint_revisions,
            depth=event.depth,
            max_depth=maximum_depth,
            min_unfixed_before_propagation=minimum,
            average_nodes_per_second=event.explored_nodes / elapsed if elapsed else 0,
            interval_nodes_per_second=(event.explored_nodes - previous["nodes"])
            / (elapsed - previous["seconds"])
            if elapsed > previous["seconds"]
            else 0,
        )
        milestones.append(row)
        with (args.output / "progress.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)

    result = search(
        state,
        Query(time_limit_seconds=args.limit),
        policy=spec["policy"],
        on_progress=progress,
    )
    squares = [validate(args.size, s.assignment, original) for s in result.solutions]
    assert state.native.domains.snapshot() == model.domains
    row = dict(
        size=args.size,
        settings=spec,
        setup_seconds=setup_seconds,
        search_seconds=result.elapsed_seconds,
        nodes=result.explored_nodes,
        nodes_per_second=result.explored_nodes / result.elapsed_seconds,
        failures=result.failed_branches,
        revisions=result.constraint_revisions,
        termination=result.termination.value,
        status=result.status.value,
        squares=squares,
        min_unfixed_before_propagation=minimum,
        max_depth=maximum_depth,
        sum_stats=dict(state.native._numeric.stats),
        alldiff_stats=dict(state.native._alldifferent.stats),
        residual_stats=dict(state.stats),
        restored=True,
    )
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
        for p, h in frozen["source_hashes"].items()
    ), "sources changed during run"
    save(args.output / "result.json", row)
    print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
