"""Separate wall-clock attribution from cProfile for fixed magic-square searches."""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import io
import json
import platform
import pstats
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .magic_search_tuning import RankedDomains, RankedState, prepare


class MeasuredNative(NativeState):
    def __init__(self, model):
        super().__init__(model)
        self.times = defaultdict(float)
        self.calls = defaultdict(int)

    def measure(self, key, operation, *args, **kwargs):
        started = perf_counter()
        try:
            return operation(*args, **kwargs)
        finally:
            self.times[key] += perf_counter() - started
            self.calls[key] += 1

    def propagate(self, **kwargs):
        root = not self.calls["propagation"]
        started = perf_counter()
        try:
            return self.measure("propagation", super().propagate, **kwargs)
        finally:
            if root:
                self.times["root_propagation"] = perf_counter() - started

    def _revise_numeric(self, index, constraint, plan, cause):
        return self.measure(
            type(constraint).__name__ + ":mask",
            super()._revise_numeric,
            index,
            constraint,
            plan,
            cause,
        )

    def _revise_alldifferent(self, plan, cause):
        return self.measure(
            "AllDifferentConstraint:mask", super()._revise_alldifferent, plan, cause
        )

    def _revise(self, index, constraint, scoped):
        return self.measure(
            type(constraint).__name__ + ":reference",
            super()._revise,
            index,
            constraint,
            scoped,
        )

    def checkpoint(self):
        return self.measure("checkpoint", super().checkpoint)

    def rollback(self, checkpoint):
        return self.measure("rollback", super().rollback, checkpoint)

    def release(self, checkpoint):
        return self.measure("release", super().release, checkpoint)

    def restrict(self, variable, value):
        return self.measure("restrict", super().restrict, variable, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", nargs="+", type=int, default=[10, 11, 14, 18])
    parser.add_argument(
        "--presets", type=Path, help="profile settings from a saved preset"
    )
    parser.add_argument(
        "--max-nodes", type=int, help="override every workload's node budget"
    )
    args = parser.parse_args()
    if (args.max_nodes is not None and args.max_nodes < 1) or any(
        n < 3 for n in args.sizes
    ):
        parser.error("require positive node budgets and sizes at least three")
    args.output.mkdir(parents=True, exist_ok=False)
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
    ]
    if args.presets:
        files.append(args.presets)
        preset = json.loads(args.presets.read_text())
        specs = [
            dict(
                size=size,
                **{
                    **preset["default"],
                    **preset["known_size_overrides"].get(str(size), {}),
                },
                max_nodes=args.max_nodes if args.max_nodes is not None else 1500,
            )
            for size in args.sizes
        ]
    else:
        specs = [
            dict(
                size=size,
                tie="degree" if size >= 14 else "row_major",
                symmetry=size >= 14,
                order="middle",
                policy="mrv",
                seed=0,
                max_nodes=args.max_nodes
                if args.max_nodes is not None
                else (
                    1500 if size in (11, 12, 13, 15, 16) else 30 if size >= 17 else None
                ),
            )
            for size in args.sizes
        ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    frozen = {
        "python": platform.python_version(),
        "source_hashes": hashes,
        "specs": specs,
        "scope": (
            "Search only, excluding model/state setup and validation. "
            "Node budgets are recorded per workload. "
            "Wall timers and cProfile use separate runs. "
            "No successful-path tracing."
        ),
    }
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    rows = []
    for spec in specs:
        size, order = spec["size"], spec["order"]
        original, model = prepare(
            size, order, spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        signatures = []
        row = dict(spec)
        for mode in ("baseline", "wall_timers", "cprofile"):
            print(json.dumps({"size": size, "mode": mode}), flush=True)
            state = RankedState.__new__(RankedState)
            state.model = model
            state.native = (MeasuredNative if mode == "wall_timers" else NativeState)(
                model
            )
            state.domains = RankedDomains(state.native.domains, model, order)
            profiler = cProfile.Profile() if mode == "cprofile" else None
            if profiler:
                profiler.enable()
            started = perf_counter()
            result = search(
                state,
                Query(max_nodes=spec["max_nodes"], time_limit_seconds=60),
                policy=spec["policy"],
            )
            seconds = perf_counter() - started
            if profiler:
                profiler.disable()
            squares = [
                validate(size, solution.assignment, original)
                for solution in result.solutions
            ]
            signatures.append(
                (
                    result.explored_nodes,
                    result.failed_branches,
                    result.constraint_revisions,
                    result.termination.value,
                    squares,
                )
            )
            row[mode] = {
                "seconds": seconds,
                "nodes": result.explored_nodes,
                "failures": result.failed_branches,
                "revisions": result.constraint_revisions,
                "termination": result.termination.value,
                "solved": bool(squares),
            }
            if mode == "wall_timers":
                row[mode].update(
                    times=dict(state.native.times), calls=dict(state.native.calls)
                )
            if profiler:
                profiler.dump_stats(str(args.output / f"magic{size}.prof"))
                report = io.StringIO()
                stats = pstats.Stats(profiler, stream=report)
                stats.strip_dirs().sort_stats("cumulative").print_stats(35)
                stats.sort_stats("tottime").print_stats(35)
                (args.output / f"magic{size}_profile.txt").write_text(report.getvalue())
            print(json.dumps({"size": size, "mode": mode, **row[mode]}), flush=True)
        assert signatures[0] == signatures[1] == signatures[2], (
            "profiling changed search work"
        )
        rows.append(row)
        (args.output / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )


if __name__ == "__main__":
    main()
