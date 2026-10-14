"""Fresh CP/hybrid attribution with separate uninstrumented and profiler runs."""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import io
import json
import pstats
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_profile import MeasuredNative
from .magic_residual_enumeration import Kernel
from .magic_residual_evaluation import HybridState
from .magic_residual_study import freeze, settings
from .magic_search_tuning import RankedDomains, RankedState, prepare


class MeasuredCompiler:
    def __init__(self, compiler, times):
        self.compiler, self.times = compiler, times

    def extract(self, masks):
        started = perf_counter()
        try:
            return self.compiler.extract(masks)
        finally:
            self.times["residual_extraction"] += perf_counter() - started


class MeasuredKernel:
    def __init__(self, kernel, times):
        self.kernel, self.times = kernel, times

    def prepare(self, residual):
        started = perf_counter()
        try:
            function = self.kernel.prepare(residual)
        finally:
            self.times["residual_encoding"] += perf_counter() - started

        def run(*args, **kwargs):
            started = perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                # Includes ctypes invocation and Python result decoding. Native
                # instructions cannot be attributed internally with cProfile.
                self.times["residual_call"] += perf_counter() - started

        return run


class MeasuredSumKernel:
    def __init__(self, kernel, times):
        self.kernel, self.times = kernel, times

    def __getattr__(self, name):
        return getattr(self.kernel, name)

    def function(self, *args):
        started = perf_counter()
        try:
            return self.kernel.function(*args)
        finally:
            self.times["sum_native_call"] += perf_counter() - started


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def signature(row):
    return (
        row["nodes"],
        row["failures"],
        row["revisions"],
        row["termination"],
        row["squares"],
        {k: v for k, v in row["stats"].items() if k != "enum_seconds"},
        row.get("sum_stats", {}),
    )


def attribute(row):
    times = row["times"]
    cp = times.get("propagation", 0)
    numeric = sum(
        v
        for k, v in times.items()
        if k.startswith(("SumConstraint:", "LinearSumConstraint:"))
    )
    alldiff = sum(
        v for k, v in times.items() if k.startswith("AllDifferentConstraint:")
    )
    enumeration = row["stats"].get("enum_seconds", 0)
    state = sum(
        times.get(k, 0) for k in ("checkpoint", "rollback", "release", "restrict")
    )
    categories = dict(
        sum_filtering=numeric,
        alldiff_filtering=alldiff,
        cp_propagation_other=cp - numeric - alldiff,
        residual_extraction=times.get("residual_extraction", 0),
        residual_encoding=times.get("residual_encoding", 0),
        residual_call=times.get("residual_call", 0),
        residual_adapter_other=enumeration
        - sum(
            times.get(k, 0)
            for k in ("residual_extraction", "residual_encoding", "residual_call")
        ),
        state_operations=state,
        search_other=row["search_seconds"] - cp - enumeration - state,
    )
    assert min(categories.values()) >= -1e-8
    return {
        k: dict(seconds=v, percent=100 * v / row["search_seconds"])
        for k, v in categories.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--sizes", type=int, nargs="+", default=[8, 9, 11, 13, 14, 16, 20]
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=float, default=60)
    parser.add_argument("--large-nodes", type=int, default=30)
    parser.add_argument("--native-sum", action="store_true")
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.limit <= 0
        or args.large_nodes < 1
        or any(n < 3 for n in args.sizes)
    ):
        parser.error("require positive repeats/time and square sizes >=3")
    extra = [Path(__file__).with_name("magic_profile.py")]
    if args.native_sum:
        extra.extend(
            [
                Path(__file__).with_name("sum_kernel.py"),
                Path(__file__).with_name("sum_support.c"),
            ]
        )
    freeze(
        args.output,
        dict(
            output=str(args.output),
            sizes=args.sizes,
            repeats=args.repeats,
            limit=args.limit,
            native_sum=args.native_sum,
            large_nodes=args.large_nodes,
            scope=(
                "Search excludes model/state setup, imports, compilation, output "
                "and validation. Separate wall timers/cProfile runs; "
                "instrumented times are not benchmark medians."
            ),
            hybrid=dict(remaining=20, mode=4, work_limit=200000),
            node_limits=(
                f"5000 for sizes <=16;{args.large_nodes} "
                "for larger sizes (prefix only)"
            ),
        ),
        extra_files=extra,
    )
    kernel, compiled = Kernel.build(args.output / "enumerator.so")
    save(args.output / "compile.json", compiled)
    sum_kernel = None
    if args.native_sum:
        from .sum_kernel import SumKernel

        sum_kernel, compiled = SumKernel.build(args.output / "sum.so")
        save(args.output / "sum_compile.json", compiled)
    schedule = [
        (n, v, "baseline", r)
        for n in args.sizes
        for v in ("cp", "hybrid")
        for r in range(args.repeats)
    ]
    Random(141026).shuffle(schedule)
    # Instrumented passes are sequential and separate from uninstrumented runs.
    schedule.extend(
        (n, v, phase, 0)
        for n in args.sizes
        for v in ("cp", "hybrid")
        for phase in ("wall_timers", "cprofile")
    )
    save(args.output / "schedule.json", schedule)
    rows, signatures = [], {}
    for n, variant, phase, repeat in schedule:
        spec = settings(n)
        started = perf_counter()
        original, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        state = (
            RankedState(model, spec["order"])
            if variant == "cp"
            else HybridState(model, spec["order"], kernel, 20, 4, 200000)
        )
        if phase == "wall_timers":
            state.native = MeasuredNative(model)
            state.domains = RankedDomains(state.native.domains, model, spec["order"])
            if variant == "hybrid":
                state.compiler = MeasuredCompiler(state.compiler, state.native.times)
                state.kernel = MeasuredKernel(kernel, state.native.times)
        if sum_kernel is not None:
            from .sum_kernel import enable

            enable(
                state.native,
                MeasuredSumKernel(sum_kernel, state.native.times)
                if phase == "wall_timers"
                else sum_kernel,
            )
        setup = perf_counter() - started
        profiler = cProfile.Profile() if phase == "cprofile" else None
        if profiler is not None:
            profiler.enable()
        started = perf_counter()
        result = search(
            state,
            Query(
                max_nodes=5000 if n <= 16 else args.large_nodes,
                time_limit_seconds=args.limit,
            ),
            policy=spec["policy"],
        )
        seconds = perf_counter() - started
        if profiler is not None:
            profiler.disable()
        row = dict(
            size=n,
            variant=variant,
            phase=phase,
            repeat=repeat,
            settings=spec,
            setup_seconds=setup,
            search_seconds=seconds,
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
            termination=result.termination.value,
            squares=[validate(n, s.assignment, original) for s in result.solutions],
            stats=dict(state.stats) if variant == "hybrid" else {},
            sum_stats=dict(state.native._numeric.stats)
            if sum_kernel is not None
            else {},
        )
        assert row["termination"] != "time_limit", (
            "profiling interrupted; search cannot be compared"
        )
        key = n, variant
        if key in signatures:
            assert signature(row) == signatures[key], "instrumentation changed search"
        signatures[key] = signature(row)
        if phase == "wall_timers":
            row.update(times=dict(state.native.times), calls=dict(state.native.calls))
            row["attribution"] = attribute(row)
            if sum_kernel is not None:
                call = row["times"].get("sum_native_call", 0)
                total = row["attribution"]["sum_filtering"]["seconds"]
                assert 0 <= call <= total
                row["sum_breakdown"] = dict(
                    native_call_seconds=call,
                    native_call_percent=100 * call / seconds,
                    python_adapter_and_application_seconds=total - call,
                    python_adapter_and_application_percent=100
                    * (total - call)
                    / seconds,
                )
        if profiler is not None:
            profiler.dump_stats(str(args.output / f"magic{n}_{variant}.prof"))
            stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.strip_dirs().sort_stats("cumulative").print_stats(45)
            stats.sort_stats("tottime").print_stats(45)
            (args.output / f"magic{n}_{variant}.txt").write_text(stream.getvalue())
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {
                    k: v
                    for k, v in row.items()
                    if k not in ("squares", "settings", "attribution", "times", "calls")
                }
            ),
            flush=True,
        )
    summary = []
    for n in args.sizes:
        for variant in ("cp", "hybrid"):
            group = [r for r in rows if r["size"] == n and r["variant"] == variant]
            wall = next(r for r in group if r["phase"] == "wall_timers")
            baseline = [r for r in group if r["phase"] == "baseline"]
            summary.append(
                dict(
                    size=n,
                    variant=variant,
                    solved=bool(wall["squares"]),
                    termination=wall["termination"],
                    nodes=wall["nodes"],
                    median_search_seconds=median(r["search_seconds"] for r in baseline),
                    median_setup_seconds=median(r["setup_seconds"] for r in baseline),
                    wall_seconds=wall["search_seconds"],
                    attribution=wall["attribution"],
                    stats=wall["stats"],
                    calls=wall["calls"],
                    sum_breakdown=wall.get("sum_breakdown", {}),
                )
            )
    save(args.output / "summary.json", summary)
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
        for name, digest in frozen["source_hashes"].items()
    ), "sources changed during profiling"
    print(json.dumps(dict(runs=len(rows), signatures=len(signatures)), indent=2))


if __name__ == "__main__":
    main()
