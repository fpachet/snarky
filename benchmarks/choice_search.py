"""Benchmark the first choice/backtracking integration projects."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from csp_solver.four_queens import solve_four_queens
from csp_solver.solver import solve_binary_csp
from harmonizer.solver import build_harmonizer_model
from snarky import ChoiceTraversal


def _measure(
    operation: Callable[[], tuple[int, int, int]],
    repeat: int,
) -> dict[str, Any]:
    samples: list[float] = []
    counters: tuple[int, int, int] | None = None
    for _ in range(repeat):
        started = time.perf_counter()
        current = operation()
        samples.append(time.perf_counter() - started)
        if counters is not None and current != counters:
            raise AssertionError("search counters changed between repetitions")
        counters = current
    assert counters is not None
    explored, failed, solutions = counters
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "explored_nodes": explored,
        "failed_branches": failed,
        "solutions": solutions,
    }


def run(repeat: int) -> dict[str, Any]:
    harmonizer_model = build_harmonizer_model()
    harmonizer_four_position_model = build_harmonizer_model(
        (67, 72, 67, 72)
    )

    def queens() -> tuple[int, int, int]:
        result = solve_four_queens()
        return (
            result.explored_nodes,
            result.failed_branches,
            len(result.solutions),
        )

    def harmony() -> tuple[int, int, int]:
        result = solve_binary_csp(
            harmonizer_model.csp,
            max_solutions=3,
            traversal=ChoiceTraversal.BEST_FIRST,
        )
        return (
            result.explored_nodes,
            result.failed_branches,
            len(result.solutions),
        )

    def harmony_four_positions() -> tuple[int, int, int]:
        result = solve_binary_csp(
            harmonizer_four_position_model.csp,
            max_solutions=3,
            traversal=ChoiceTraversal.BEST_FIRST,
        )
        return (
            result.explored_nodes,
            result.failed_branches,
            len(result.solutions),
        )

    return {
        "benchmark": "choice_search",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "four_queens": _measure(queens, repeat),
        "harmonizer_two_positions": _measure(harmony, repeat),
        "harmonizer_four_positions": _measure(
            harmony_four_positions,
            repeat,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=5)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("repeat must be positive")
    print(json.dumps(run(arguments.repeat), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
