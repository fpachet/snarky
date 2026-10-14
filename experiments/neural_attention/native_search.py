"""Opt-in C finite search experiment, reusing validated batch propagators.

No installed defaults change. Only ModelSpec's explicit feasibility subset is
supported. The model's alphabet order defines value order; MRV or dom/wdeg
defines variable choice. Each call starts a fresh search with private state.
"""

from __future__ import annotations

import ctypes as ct
import math
from pathlib import Path
from time import perf_counter

from .model_batch import BatchContext, BatchKernel, ModelSpec, source


class SearchKernel(BatchKernel):
    def __init__(self, library):
        super().__init__(library)
        self.search = self.library.native_search
        self.search.argtypes = [
            ct.c_void_p,
            ct.POINTER(ct.c_uint64),
            ct.c_int,
            ct.c_uint64,
            ct.c_uint64,
            ct.c_double,
            ct.POINTER(ct.c_int),
            ct.c_int,
            ct.POINTER(ct.c_uint64),
        ]
        self.search.restype = ct.c_int

    @classmethod
    def build_search(cls, output, *, cache_dir=None):
        path = Path(output).with_suffix(".c")
        path.parent.mkdir(parents=True, exist_ok=True)
        generated = (
            "#define _POSIX_C_SOURCE 200809L\n"
            + source()
            + Path(__file__).with_suffix(".c").read_text()
        )
        path.write_text(generated)
        return cls.build(
            output,
            cache_dir=cache_dir or "generated/neural_attention/native_search_cache",
            source=path,
        )


COUNTERS = (
    "nodes",
    "failures",
    "revisions",
    "support_calls",
    "cache_hits",
    "reductions",
    "solution_count",
    "peak_depth",
    "peak_trail_entries",
    "work_digest",
)
TERMINATIONS = ("exhausted", "solution_limit", "node_limit", "time_limit")


def solve(
    spec: ModelSpec,
    kernel: SearchKernel,
    *,
    masks=None,
    policy="mrv",
    max_nodes=0,
    max_solutions=1,
    seconds=60,
    collect_limit=1,
):
    if policy not in ("mrv", "dom_wdeg"):
        raise ValueError("unsupported variable policy")
    if any(
        type(v) is not int or not 0 <= v < 2**64 for v in (max_nodes, max_solutions)
    ):
        raise ValueError("limits require uint64 integers; zero means unlimited")
    if type(collect_limit) is not int or not 1 <= collect_limit <= 10000:
        raise ValueError("collect_limit must be 1..10000")
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("require finite nonnegative seconds")
    started = perf_counter()
    context = BatchContext(spec, kernel)
    try:
        packed = spec.encode(spec.full if masks is None else masks)
        stats = (ct.c_uint64 * len(COUNTERS))()
        output = (ct.c_int * (collect_limit * len(spec.names)))()
        entered = perf_counter()
        status = kernel.search(
            context.handle,
            packed,
            policy == "dom_wdeg",
            max_nodes,
            max_solutions,
            seconds,
            output,
            collect_limit,
            stats,
        )
        finished = perf_counter()
        if status < 0:
            raise RuntimeError(f"native search error/resource interruption: {status}")
        rows = [
            tuple(output[k * len(spec.names) + v] for v in range(len(spec.names)))
            for k in range(min(collect_limit, stats[6]))
        ]
        result = dict(zip(COUNTERS, map(int, stats), strict=True))
        result.update(
            termination=TERMINATIONS[status],
            candidate_solutions=rows,
            solutions=[
                tuple(spec.alphabets[v][p] for v, p in enumerate(row)) for row in rows
            ],
            search_seconds=finished - entered,
            setup_and_search_seconds=finished - started,
        )
        if hasattr(kernel, "metrics"):
            result["profile"] = kernel.metrics(context.handle)
        return result
    finally:
        context._finalizer()
