"""Benchmark the generic Sudoku search and note-variable harmonizer."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from benchmarks.support import PROJECT_ROOT, git_commit, git_dirty
from csp_solver.solver import solve_finite_csp
from harmonizer import (
    build_harmonizer_model,
    build_note_harmonizer_model,
    solve_note_harmonizer,
)
from snarky import ChoiceTraversal
from sudoku import load_puzzle, solve_puzzle, solve_puzzle_with_search

type Counters = tuple[int, int, int]


def _measure(
    operation: Callable[[], Counters],
    repeat: int,
    counter_names: tuple[str, str, str] = (
        "explored_nodes",
        "failed_branches",
        "solutions",
    ),
) -> dict[str, Any]:
    samples: list[float] = []
    counters: Counters | None = None
    for _ in range(repeat):
        started = time.perf_counter()
        current = operation()
        samples.append(time.perf_counter() - started)
        if counters is not None and current != counters:
            raise AssertionError("logical counters changed between repetitions")
        counters = current
    assert counters is not None
    result = {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
    }
    result.update(dict(zip(counter_names, counters, strict=True)))
    return result


def run(repeat: int) -> dict[str, Any]:
    puzzle = load_puzzle(2)

    def sudoku_human_rules() -> Counters:
        result = solve_puzzle(puzzle)
        return len(result.steps), 0, int(result.grid is not None)

    def sudoku_choice_search() -> Counters:
        result = solve_puzzle_with_search(
            puzzle,
            techniques=("naked_singles",),
        )
        return (
            result.search.explored_nodes,
            result.search.failed_branches,
            len(result.search.solutions),
        )

    def whole_voicing_harmonizer() -> Counters:
        model = build_harmonizer_model()
        result = solve_finite_csp(
            model.csp,
            max_solutions=3,
            traversal=ChoiceTraversal.BEST_FIRST,
        )
        return (
            result.explored_nodes,
            result.failed_branches,
            len(result.solutions),
        )

    def note_variable_harmonizer() -> Counters:
        model = build_note_harmonizer_model()
        result = solve_note_harmonizer(model, max_solutions=3)
        return (
            result.explored_nodes,
            result.failed_branches,
            len(result.solutions),
        )

    return {
        "benchmark": "csp_harmonizer_next",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "snarky_commit": git_commit(PROJECT_ROOT),
        "snarky_dirty": git_dirty(PROJECT_ROOT),
        "sudoku_p2_full_human_rules": _measure(
            sudoku_human_rules,
            repeat,
            ("effective_steps", "inconsistent", "solved"),
        ),
        "sudoku_p2_naked_single_plus_choice": _measure(
            sudoku_choice_search,
            repeat,
        ),
        "harmonizer_whole_voicing": _measure(
            whole_voicing_harmonizer,
            repeat,
        ),
        "harmonizer_note_variables": _measure(
            note_variable_harmonizer,
            repeat,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=5)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("repeat must be positive")
    print(json.dumps(run(arguments.repeat), indent=2))


if __name__ == "__main__":
    main()
