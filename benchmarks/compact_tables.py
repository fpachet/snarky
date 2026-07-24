"""Benchmark scanned tables, bitset filtering, and compact-table joins."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from snarky import (
    ConstraintInstantiationStrategy,
    InstantiationStrategy,
    TechniquePlanStatus,
)
from sudoku import solve_level

type StrategyFactory = Callable[[], InstantiationStrategy]


def _scanned() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_compact_tables=False,
        use_compact_join=False,
    )


def _bitset_filter() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_compact_join=False,
    )


_STRATEGIES: dict[str, StrategyFactory] = {
    "scanned": _scanned,
    "bitset-filter": _bitset_filter,
    "compact": ConstraintInstantiationStrategy,
}


def measure(
    level: int,
    repeat: int,
    strategy_name: str,
) -> dict[str, Any]:
    samples: list[float] = []
    final_strategy: InstantiationStrategy | None = None
    for _ in range(repeat):
        strategy = _STRATEGIES[strategy_name]()
        started = time.perf_counter()
        result = solve_level(level, strategy=strategy)
        samples.append(time.perf_counter() - started)
        if result.status is not TechniquePlanStatus.SOLVED:
            raise RuntimeError(f"p{level} was not solved")
        final_strategy = strategy
    assert final_strategy is not None
    metrics = final_strategy.metrics
    return {
        "name": strategy_name,
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "match_attempts": metrics.match_attempts,
        "domain_rows_examined": metrics.domain_rows_examined,
        "domain_bitset_value_events": metrics.domain_bitset_value_events,
        "domain_bitset_support_checks": (
            metrics.domain_bitset_support_checks
        ),
        "domain_bitset_intersections": (
            metrics.domain_bitset_intersections
        ),
        "domain_compact_join_rows": metrics.domain_compact_join_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--levels", type=int, nargs="+", default=(1, 6, 7))
    parser.add_argument("--repeat", type=int, default=7)
    arguments = parser.parse_args()
    if arguments.repeat < 1 or any(
        level not in range(1, 8) for level in arguments.levels
    ):
        parser.error("--repeat must be positive and levels must be in 1..7")

    levels = []
    for level in arguments.levels:
        strategies = [
            measure(level, arguments.repeat, name)
            for name in _STRATEGIES
        ]
        scanned = strategies[0]
        compact = strategies[-1]
        levels.append(
            {
                "level": level,
                "strategies": strategies,
                "compact_speedup": (
                    float(scanned["median_seconds"])
                    / float(compact["median_seconds"])
                ),
            }
        )
    print(
        json.dumps(
            {
                "benchmark": "compact_tables",
                "repeat": arguments.repeat,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "levels": levels,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
