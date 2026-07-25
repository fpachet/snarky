"""Explicit CHOICE/backtracking over the native Sudoku rule base."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from csp_solver.constraint_syntax import (
    PersistentConstraintTemplate,
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from csp_solver.solver import (
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    FiniteCSP,
    finite_csp_rule_library,
    solve_finite_csp,
)
from snarky import (
    Atom,
    ChoicePolicy,
    ChoiceSearchResult,
    ChoiceTraversal,
    Fact,
    MRVChoicePolicy,
    Triple,
)

from .domain import (
    Grid,
    SudokuPuzzle,
    grid_from_facts,
    initial_facts,
    validate_complete_grid,
)
from .rulebase import TECHNIQUE_ORDER, load_rulebase

SUDOKU = Atom("sudoku")


@dataclass(frozen=True, slots=True)
class SudokuSearchResult:
    """A solved grid together with the generic search trace."""

    puzzle: SudokuPuzzle
    grid: Grid | None
    search: ChoiceSearchResult
    techniques: tuple[str, ...]


def solve_puzzle_with_search(
    puzzle: SudokuPuzzle,
    *,
    techniques: tuple[str, ...] = ("naked_singles",),
    max_nodes: int = 10_000,
    policy: ChoicePolicy | None = None,
    traversal: ChoiceTraversal = ChoiceTraversal.DEPTH_FIRST,
    seed: int = 0,
) -> SudokuSearchResult:
    """Solve *puzzle* by rules, then explicit generic choices when needed."""

    rulebase = load_rulebase()
    unknown = set(techniques) - set(TECHNIQUE_ORDER)
    if unknown:
        raise ValueError(f"unknown Sudoku techniques: {sorted(unknown)}")
    selected = tuple(rulebase.groups[name] for name in techniques)
    base_facts = initial_facts(puzzle)
    cells = tuple(
        fact.entity.subject
        for fact in base_facts
        if isinstance(fact.entity, Triple)
        and fact.entity.relation == Atom("row")
    )
    csp_facts = (
        Fact(Triple(SUDOKU, KIND, CSP_PROBLEM)),
        *(
            fact
            for cell in cells
            for fact in (
                Fact(Triple(SUDOKU, VARIABLE, cell)),
                Fact(Triple(cell, KIND, CSP_VARIABLE)),
            )
        ),
    )
    model = FiniteCSP(
        SUDOKU,
        (*base_facts, *csp_facts),
        {},
        (
            rulebase.derive_solved_cells,
            *selected,
            rulebase.validate_state,
        ),
        instantiate_constraint_templates(
            _sudoku_constraint_templates(),
            base_facts,
        ),
    )
    search = solve_finite_csp(
        model,
        max_nodes=max_nodes,
        policy=policy or MRVChoicePolicy(),
        traversal=traversal,
        seed=seed,
        rule_groups=(
            *finite_csp_rule_library().finite_domain_groups,
            *model.groups,
        ),
    )
    grid = (
        grid_from_facts(search.solutions[0].session.facts)
        if search.solutions
        else None
    )
    if grid is not None:
        validate_complete_grid(grid, clues=puzzle.grid)
    return SudokuSearchResult(puzzle, grid, search, techniques)


@cache
def _sudoku_constraint_templates() -> tuple[
    PersistentConstraintTemplate,
    ...,
]:
    path = Path(__file__).resolve().parent / "persistent.constraints"
    return parse_constraint_templates(path.read_text())
