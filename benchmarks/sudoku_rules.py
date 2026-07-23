"""Reproducible benchmark for the native human-style Sudoku rule base."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
from time import perf_counter
from typing import Any

from snarky import IndexedInstantiationStrategy, TechniquePlanStatus
from sudoku import solve_level


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--levels", type=int, nargs="+", default=(1, 5, 6))
    parser.add_argument("--repeat", type=int, default=5)
    arguments = parser.parse_args()
    invalid_level = any(
        level not in range(1, 7) for level in arguments.levels
    )
    if arguments.repeat < 1 or invalid_level:
        parser.error("--repeat must be positive and levels must be in 1..6")

    results = [
        measure(level, arguments.repeat)
        for level in arguments.levels
    ]
    print(
        json.dumps(
            {
                "benchmark": "sudoku",
                "repeat": arguments.repeat,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "levels": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


def measure(level: int, repeat: int) -> dict[str, Any]:
    runs: list[dict[str, int | float]] = []
    for _ in range(repeat):
        strategy = IndexedInstantiationStrategy()
        start = perf_counter()
        result = solve_level(level, strategy=strategy)
        elapsed = perf_counter() - start
        if result.status is not TechniquePlanStatus.SOLVED:
            raise RuntimeError(f"p{level} was not solved")
        runs.append(
            {
                "seconds": elapsed,
                "match_attempts": strategy.metrics.match_attempts,
                "candidate_facts": strategy.metrics.candidate_facts,
                "witness_cache_hits": strategy.metrics.witness_cache_hits,
                "witness_cache_misses": strategy.metrics.witness_cache_misses,
                "witness_cache_invalidations": (
                    strategy.metrics.witness_cache_invalidations
                ),
                "query_counter_updates": (
                    strategy.metrics.query_counter_updates
                ),
                "activation_cache_hits": (
                    strategy.metrics.activation_cache_hits
                ),
                "partial_join_builds": (
                    strategy.metrics.partial_join_builds
                ),
                "partial_join_updates": (
                    strategy.metrics.partial_join_updates
                ),
                "partial_join_bypasses": (
                    strategy.metrics.partial_join_bypasses
                ),
                "cycles": result.inference.cycles,
                "fired_activations": result.inference.fired_activation_count,
            }
        )
    elapsed_values = [float(run["seconds"]) for run in runs]
    return {
        "level": level,
        "mean_seconds": statistics.mean(elapsed_values),
        "median_seconds": statistics.median(elapsed_values),
        "min_seconds": min(elapsed_values),
        "max_seconds": max(elapsed_values),
        "runs": runs,
    }


if __name__ == "__main__":
    main()
