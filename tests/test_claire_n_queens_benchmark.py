from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks.claire_n_queens import (
    ClaireNQueensPolicy,
    parse_claire_result,
    resolve_claire_binary,
    resolve_claire_root,
    validate_solution,
)
from csp_solver.four_queens import n_queens_intensional_facts
from csp_solver.solver import prepare_finite_csp_search
from snarky import ChoiceSearchStatus


def test_parse_claire_result_ignores_runtime_banner() -> None:
    output = (
        """\
-- CLAIRE run-time library v 4.1.6 [os: macos, compiler:go ] --
"""
        "SNARKY_CLAIRE_RESULT size=4 elapsed_ns=12000000 solved=1 "
        "branch_attempts=2 failed_branches=0 rule_firings=15 "
        "candidate_removals=18 solution=2,4,1,3\n"
    )

    assert parse_claire_result(output) == {
        "size": 4,
        "solved": True,
        "branch_attempts": 2,
        "failed_branches": 0,
        "rule_firings": 15,
        "candidate_removals": 18,
        "solution": (2, 4, 1, 3),
        "seconds": 0.012,
    }


@pytest.mark.parametrize(
    "solution",
    (
        (1, 2, 3, 4),
        (2, 4, 1),
        (2, 4, 1, 1),
    ),
)
def test_validate_solution_rejects_invalid_boards(
    solution: tuple[int, ...],
) -> None:
    with pytest.raises(ValueError):
        validate_solution(4, solution)


def test_validate_solution_accepts_four_queens_oracle() -> None:
    validate_solution(4, (2, 4, 1, 3))


def test_resolve_explicit_claire_checkout(tmp_path: Path) -> None:
    root = tmp_path / "CLAIRE4"
    binary = root / "interpreter" / "macos" / "claire4"
    binary.parent.mkdir(parents=True)
    (root / "README").write_text("CLAIRE4", encoding="utf-8")
    binary.write_bytes(b"binary")

    assert resolve_claire_root(root) == root
    assert resolve_claire_binary(root) == binary


def test_explicit_missing_claire_root_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resolve_claire_root(tmp_path)


def test_prepared_snarky_search_is_solvable() -> None:
    prepared = prepare_finite_csp_search(
        n_queens_intensional_facts(4),
        policy=ClaireNQueensPolicy(),
    )

    result = prepared.solve()

    assert result.status is ChoiceSearchStatus.SOLVED
