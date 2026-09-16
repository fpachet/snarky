"""Opt-in pure-CSP diagnostics; independent profiles are not latency samples.

Select runtime sources before importing Snarky. Progress is flushed to stderr so
external hard kills preserve partial observations; only final result records can
claim a completed proof. This worker also supports uninstrumented paired runs.
"""

from __future__ import annotations

import argparse
import cProfile
import inspect
import io
import json
import pstats
import resource
import sys
import tracemalloc
from collections import defaultdict
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]


def worker(args):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.source / "src"))
    import snarky
    from benchmarks.prune_bridge import Bridge, validate_assignment
    from snarky.finite import Query, QueryKind
    from snarky.finite.propagation import NativeState
    from snarky.finite.search import search

    started = perf_counter()
    last_emission = -1.0
    families = defaultdict(
        lambda: dict(
            attempts=0, completed=0, failures=0, effective=0, removed=0, seconds=0.0
        )
    )
    progress = {}

    def emit(event, *, force=False, **fields):
        nonlocal last_emission
        now = perf_counter()
        if args.diagnostic and (force or now - last_emission >= 0.25):
            print(
                json.dumps(
                    dict(
                        event=event,
                        elapsed_seconds=now - started,
                        progress=progress,
                        families=dict(families),
                        **fields,
                    ),
                    default=str,
                ),
                file=sys.stderr,
                flush=True,
            )
            last_emission = now

    class MeasuredState(NativeState):
        def __init__(self, model):
            super().__init__(model)
            self.propagation_calls = 0
            self.root_seconds = 0.0
            self.propagation_seconds = 0.0

        def propagate(self, **kwargs):
            self.propagation_calls += 1
            tick = perf_counter()
            try:
                return super().propagate(**kwargs)
            finally:
                elapsed = perf_counter() - tick
                self.propagation_seconds += elapsed
                if self.propagation_calls == 1:
                    self.root_seconds = elapsed

        def _revise(self, index, constraint, scoped):
            family = type(constraint).__name__
            item = families[family]
            item["attempts"] += 1
            emit("revision_start", constraint_family=family, revisions=self.revisions)
            volume = sum(map(len, scoped.values()))
            tick = perf_counter()
            try:
                valid = super()._revise(index, constraint, scoped)
                item["completed"] += 1
                item["failures"] += not valid
                removed = volume - sum(map(len, scoped.values()))
                item["removed"] += removed
                item["effective"] += removed > 0
                return valid
            finally:
                item["seconds"] += perf_counter() - tick

    def observe(event):
        nonlocal progress
        progress = dict(
            event=event.event,
            nodes=event.explored_nodes,
            failures=event.failed_branches,
            pruned=event.pruned_branches,
            revisions=event.constraint_revisions,
            depth=event.depth,
            search_elapsed_seconds=event.elapsed_seconds,
            root_objective_bound=event.root_objective_bound,
            incumbent=event.incumbent.objective_value if event.incumbent else None,
        )
        fields = {}
        if event.event == "incumbent":
            assignment = bridge.raw_assignment(event.incumbent)
            validate_assignment(document, assignment)
            fields["validated_assignment"] = assignment
        emit(
            "search", force=event.event in ("start", "incumbent", "finished"), **fields
        )

    profiler = cProfile.Profile() if args.profile else None
    if args.allocation:
        tracemalloc.start()
    if profiler:
        profiler.enable()
    emit("construction_start", force=True)
    document = json.loads(args.model.read_text())
    bridge = Bridge(document)
    constructed = perf_counter()
    state = (
        MeasuredState(bridge.model) if args.diagnostic else NativeState(bridge.model)
    )
    prepared = perf_counter()
    emit(
        "prepared",
        force=True,
        variables=len(bridge.model.variables),
        constraints=len(bridge.model.constraints),
    )
    kind = {
        "satisfy": QueryKind.ENUMERATE if args.all else QueryKind.SOLVE,
        "minimize": QueryKind.MINIMIZE,
        "maximize": QueryKind.MAXIMIZE,
    }[document["solve"]["method"]]
    options = dict(policy="dom_wdeg")
    hook_available = "on_progress" in inspect.signature(search).parameters
    if args.diagnostic and hook_available:
        options["on_progress"] = observe
    result = search(
        state,
        Query(kind, max_nodes=args.nodes, time_limit_seconds=args.seconds),
        **options,
    )
    ended = perf_counter()
    if profiler:
        profiler.disable()
        profiler.dump_stats(str(args.profile))
        report = io.StringIO()
        stats = pstats.Stats(profiler, stream=report).strip_dirs()
        stats.sort_stats("cumulative").print_stats(40)
        stats.sort_stats("tottime").print_stats(30)
        args.profile.with_suffix(".txt").write_text(report.getvalue())
    allocation_peak = tracemalloc.get_traced_memory()[1] if args.allocation else None
    if args.allocation:
        tracemalloc.stop()
    output = ""
    for solution in result.solutions:
        validate_assignment(document, bridge.raw_assignment(solution))
        output += bridge.render(solution)
    if result.status.value == "infeasible":
        output += "=====UNSATISFIABLE=====\n"
    elif result.complete:
        output += "==========\n"
    elif not result.solutions:
        output += "=====UNKNOWN=====\n"
    record = dict(
        status=result.status.value,
        termination=result.termination.value,
        complete=result.complete,
        nodes=result.explored_nodes,
        failures=result.failed_branches,
        pruned=result.pruned_branches,
        revisions=result.constraint_revisions,
        objective=result.incumbent.objective_value if result.incumbent else None,
        objective_bound=result.objective_bound,
        incumbent_history=[
            dict(value=x.value, nodes=x.explored_nodes, seconds=x.elapsed_seconds)
            for x in result.incumbent_history
        ],
        construction_seconds=constructed - started,
        preparation_seconds=prepared - constructed,
        solve_seconds=ended - prepared,
        families=dict(families),
        root_propagation_seconds=getattr(state, "root_seconds", None),
        propagation_seconds=getattr(state, "propagation_seconds", None),
        traced_peak_bytes=allocation_peak,
        process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin"
        else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        rss_scope="whole process high-water mark, including imports",
        diagnostic=args.diagnostic,
        cpu_profile=bool(args.profile),
        allocation=args.allocation,
        progress_hook_available=hook_available,
        runtime_file=snarky.__file__,
        flat_output=output,
    )
    print(json.dumps(record, default=str), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--nodes", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--allocation", action="store_true")
    args = parser.parse_args()
    if args.profile and args.allocation:
        parser.error("CPU and allocation profiles must use separate runs")
    worker(args)


if __name__ == "__main__":
    main()
