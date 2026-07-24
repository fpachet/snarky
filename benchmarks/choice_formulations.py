"""Compare extensional and intensional choice-search formulations."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from functools import partial
from typing import Any

from csp_solver.four_queens import (
    n_queens_facts,
    n_queens_intensional_facts,
    solve_n_queens,
    solve_n_queens_intensional,
)
from csp_solver.solver import solve_binary_csp
from harmonizer.solver import HarmonizerModel, build_harmonizer_model
from snarky import ChoiceSearchResult, ChoiceTraversal


def _measure(
    operation: Callable[[], ChoiceSearchResult],
    repeat: int,
    fact_count: int,
) -> dict[str, Any]:
    samples: list[float] = []
    counters: tuple[int, int, int] | None = None
    for _ in range(repeat):
        started = time.perf_counter()
        result = operation()
        samples.append(time.perf_counter() - started)
        current = (
            result.explored_nodes,
            result.failed_branches,
            len(result.solutions),
        )
        if counters is not None and current != counters:
            raise AssertionError("search counters changed between repetitions")
        counters = current
    assert counters is not None
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "fact_count": fact_count,
        "explored_nodes": counters[0],
        "failed_branches": counters[1],
        "solutions": counters[2],
    }


def _comparison(
    extensional: dict[str, Any],
    intensional: dict[str, Any],
) -> dict[str, Any]:
    extensional_seconds = extensional["median_seconds"]
    intensional_seconds = intensional["median_seconds"]
    return {
        "extensional": extensional,
        "intensional": intensional,
        "speedup": extensional_seconds / intensional_seconds,
        "reduction_percent": (
            100.0
            * (extensional_seconds - intensional_seconds)
            / extensional_seconds
        ),
    }


def _solve_harmonizer(model: HarmonizerModel) -> ChoiceSearchResult:
    return solve_binary_csp(
        model.csp,
        max_solutions=3,
        traversal=ChoiceTraversal.BEST_FIRST,
    )


def run(repeat: int) -> dict[str, Any]:
    queens_size = 14
    queens_extensional = n_queens_facts(queens_size)
    queens_intensional = n_queens_intensional_facts(queens_size)
    melody_two = (67, 72)
    melody_four = (67, 72, 67, 72)

    results: dict[str, Any] = {}
    results["n_queens_14"] = _comparison(
        _measure(
            lambda: solve_n_queens(queens_size),
            repeat,
            len(queens_extensional.facts),
        ),
        _measure(
            lambda: solve_n_queens_intensional(queens_size),
            repeat,
            len(queens_intensional.facts),
        ),
    )
    for name, melody in (
        ("harmonizer_two_positions", melody_two),
        ("harmonizer_four_positions", melody_four),
    ):
        extensional = build_harmonizer_model(
            melody,
            intensional_transitions=False,
        )
        intensional = build_harmonizer_model(
            melody,
            intensional_transitions=True,
        )
        results[name] = _comparison(
            _measure(
                partial(_solve_harmonizer, extensional),
                repeat,
                len(extensional.csp.facts),
            ),
            _measure(
                partial(_solve_harmonizer, intensional),
                repeat,
                len(intensional.csp.facts),
            ),
        )
    return {
        "benchmark": "choice_formulations",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=3)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("repeat must be positive")
    print(json.dumps(run(arguments.repeat), indent=2))


if __name__ == "__main__":
    main()
