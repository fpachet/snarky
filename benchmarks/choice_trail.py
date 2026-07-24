"""Compare lazy forked DFS with reversible-trail DFS on N queens."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from csp_solver.four_queens import solve_n_queens


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
    explored, failed, decisions = counters
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "explored_nodes": explored,
        "failed_branches": failed,
        "solution_decisions": decisions,
    }


def run(sizes: tuple[int, ...], repeat: int) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for size in sizes:
        modes: dict[str, Any] = {}
        for label, reversible in (
            ("lazy_forks", False),
            ("reversible_trail", True),
        ):

            def solve(
                *,
                board_size: int = size,
                use_trail: bool = reversible,
            ) -> tuple[int, int, int]:
                result = solve_n_queens(
                    board_size,
                    reversible_depth_first=use_trail,
                )
                return (
                    result.explored_nodes,
                    result.failed_branches,
                    len(result.solutions[0].decisions),
                )

            modes[label] = _measure(solve, repeat)
        fork_seconds = modes["lazy_forks"]["median_seconds"]
        trail_seconds = modes["reversible_trail"]["median_seconds"]
        modes["trail_speedup"] = fork_seconds / trail_seconds
        modes["trail_reduction_percent"] = (
            100.0 * (fork_seconds - trail_seconds) / fork_seconds
        )
        results[f"n_queens_{size}"] = modes
    return {
        "benchmark": "choice_trail",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=(8, 10, 12, 14),
    )
    parser.add_argument("--repeat", type=int, default=3)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("repeat must be positive")
    if any(size < 1 for size in arguments.sizes):
        parser.error("sizes must be positive")
    print(json.dumps(run(tuple(arguments.sizes), arguments.repeat), indent=2))


if __name__ == "__main__":
    main()
