"""Benchmark classical CSPs and the Sudoku rule/constraint hybrid."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from benchmarks.support import PROJECT_ROOT, git_commit, git_dirty
from csp_solver.latin_square import (
    latin_square_facts,
    latin_square_from_solution,
    solve_latin_square,
)
from csp_solver.magic_square import (
    magic_constant,
    magic_square_facts,
    solve_magic_square,
    square_from_solution,
)
from snarky import ChoiceSearchResult, ChoiceSearchStatus
from sudoku import load_puzzle
from sudoku.rulebase import TECHNIQUE_ORDER
from sudoku.search import solve_puzzle_with_search


def _measure(
    operation: Callable[[], ChoiceSearchResult],
    repeat: int,
) -> dict[str, Any]:
    samples: list[float] = []
    counters: tuple[ChoiceSearchStatus, int, int] | None = None
    for _ in range(repeat):
        started = time.perf_counter()
        result = operation()
        samples.append(time.perf_counter() - started)
        current = (
            result.status,
            result.explored_nodes,
            result.failed_branches,
        )
        if counters is not None and current != counters:
            raise AssertionError("search counters changed between repetitions")
        counters = current
    assert counters is not None
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "status": counters[0].value,
        "explored_nodes": counters[1],
        "failed_branches": counters[2],
    }


def _magic(
    size: int,
    *,
    symmetry_breaking: bool,
    propagation_guided: bool,
    dom_wdeg_only: bool,
) -> ChoiceSearchResult:
    result = solve_magic_square(
        size,
        symmetry_breaking=symmetry_breaking,
        propagation_guided=propagation_guided,
        dom_wdeg_only=dom_wdeg_only,
    )
    if result.status is not ChoiceSearchStatus.SOLVED:
        raise AssertionError(f"order-{size} magic square was not solved")
    square = square_from_solution(result.solutions[0], size)
    target = magic_constant(size)
    if sorted(value for row in square for value in row) != list(
        range(1, size * size + 1)
    ):
        raise AssertionError("magic-square values are invalid")
    if any(sum(row) != target for row in square):
        raise AssertionError("magic-square row is invalid")
    if any(
        sum(square[row][column] for row in range(size)) != target
        for column in range(size)
    ):
        raise AssertionError("magic-square column is invalid")
    return result


def _latin(size: int) -> ChoiceSearchResult:
    result = solve_latin_square(size)
    if result.status is not ChoiceSearchStatus.SOLVED:
        raise AssertionError(f"order-{size} Latin square was not solved")
    square = latin_square_from_solution(result.solutions[0], size)
    expected = set(range(1, size + 1))
    if any(set(row) != expected for row in square):
        raise AssertionError("Latin-square row is invalid")
    if any(
        {square[row][column] for row in range(size)} != expected
        for column in range(size)
    ):
        raise AssertionError("Latin-square column is invalid")
    return result


def _sudoku(
    techniques: tuple[str, ...],
) -> ChoiceSearchResult:
    puzzle = load_puzzle(7)
    result = solve_puzzle_with_search(
        puzzle,
        techniques=techniques,
    )
    if result.grid != puzzle.solution:
        raise AssertionError("Sudoku result differs from its oracle")
    return result.search


def run(
    repeat: int,
    *,
    magic_sizes: tuple[int, ...] = (3, 4, 5),
    include_other: bool = True,
    magic_symmetry_breaking: bool = False,
    magic_propagation_guided: bool = False,
    magic_dom_wdeg_only: bool = False,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for size in magic_sizes:
        model = magic_square_facts(
            size,
            symmetry_breaking=magic_symmetry_breaking,
        )
        results[f"magic_square_{size}"] = {
            **_measure(
                lambda size=size: _magic(
                    size,
                    symmetry_breaking=magic_symmetry_breaking,
                    propagation_guided=magic_propagation_guided,
                    dom_wdeg_only=magic_dom_wdeg_only,
                ),
                repeat,
            ),
            "facts": len(model.facts),
            "constraints": len(model.constraints),
        }
    if include_other:
        for size in (5, 7):
            model = latin_square_facts(size)
            results[f"latin_square_{size}"] = {
                **_measure(lambda size=size: _latin(size), repeat),
                "facts": len(model.facts),
                "constraints": len(model.constraints),
            }
        results["sudoku_p7_constraints_only"] = _measure(
            lambda: _sudoku(()),
            repeat,
        )
        results["sudoku_p7_constraints_and_rules"] = _measure(
            lambda: _sudoku(TECHNIQUE_ORDER),
            repeat,
        )
    return {
        "benchmark": "classical_csp",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "snarky_commit": git_commit(PROJECT_ROOT),
        "snarky_dirty": git_dirty(PROJECT_ROOT),
        "magic_symmetry_breaking": magic_symmetry_breaking,
        "magic_propagation_guided": magic_propagation_guided,
        "magic_dom_wdeg_only": magic_dom_wdeg_only,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument(
        "--magic-sizes",
        type=int,
        nargs="+",
        default=(3, 4, 5),
    )
    parser.add_argument(
        "--only-magic",
        action="store_true",
        help="skip Latin-square and Sudoku cases",
    )
    parser.add_argument(
        "--magic-symmetry-breaking",
        action="store_true",
    )
    magic_value_ordering = parser.add_mutually_exclusive_group()
    magic_value_ordering.add_argument(
        "--magic-propagation-guided",
        action="store_true",
    )
    magic_value_ordering.add_argument(
        "--magic-dom-wdeg-only",
        action="store_true",
    )
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("repeat must be positive")
    if any(size < 1 for size in arguments.magic_sizes):
        parser.error("magic-square sizes must be positive")
    print(
        json.dumps(
            run(
                arguments.repeat,
                magic_sizes=tuple(arguments.magic_sizes),
                include_other=not arguments.only_magic,
                magic_symmetry_breaking=(
                    arguments.magic_symmetry_breaking
                ),
                magic_propagation_guided=(
                    arguments.magic_propagation_guided
                ),
                magic_dom_wdeg_only=arguments.magic_dom_wdeg_only,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
