"""Reduced Latin squares using persistent ALL_DIFFERENT constraints."""

from __future__ import annotations

import argparse
from functools import cache
from pathlib import Path

from snarky import (
    Atom,
    ChoiceSearchResult,
    ChoiceSolution,
    Fact,
    FiniteSequence,
    Number,
    Triple,
)

from .constraint_syntax import (
    PersistentConstraintTemplate,
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from .solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    FiniteCSP,
    assignment_from_solution,
    finite_csp_rule_library,
    solve_finite_csp,
)

LATIN_CELL = Atom("latin_cell")
LATIN_LINE = Atom("latin_line")
SIZE = Atom("size")
ROW = Atom("row")
COLUMN = Atom("column")
CELL = Atom("cell")


def latin_square_problem(size: int) -> Atom:
    if size < 1:
        raise ValueError("the Latin-square size must be positive")
    return Atom(f"latin_square_{size}")


def latin_cell(row: int, column: int) -> Atom:
    if row < 1 or column < 1:
        raise ValueError("Latin-square coordinates are one-based")
    return Atom(f"latin_cell_{row}_{column}")


def latin_square_facts(
    size: int,
    *,
    reduced: bool = True,
) -> FiniteCSP:
    """Build an order-``size`` Latin square.

    Reduced squares fix the first row and column to ``1..size``. This removes
    value and row/column symmetries without changing the reusable constraint
    declaration.
    """

    problem = latin_square_problem(size)
    facts: list[Fact] = [
        Fact(Triple(problem, KIND, CSP_PROBLEM)),
        Fact(Triple(problem, SIZE, Number(size))),
    ]
    for row in range(1, size + 1):
        for column in range(1, size + 1):
            variable = latin_cell(row, column)
            domain = (
                (column,)
                if reduced and row == 1
                else (
                    (row,)
                    if reduced and column == 1
                    else tuple(range(1, size + 1))
                )
            )
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, variable)),
                    Fact(Triple(variable, KIND, CSP_VARIABLE)),
                    Fact(Triple(variable, KIND, LATIN_CELL)),
                    Fact(Triple(variable, ROW, Number(row))),
                    Fact(Triple(variable, COLUMN, Number(column))),
                    *(
                        Fact(Triple(variable, CANDIDATE, Number(value)))
                        for value in domain
                    ),
                )
            )

    lines = [
        *(
            (
                Atom(f"latin_row_{row}"),
                tuple(
                    latin_cell(row, column)
                    for column in range(1, size + 1)
                ),
            )
            for row in range(1, size + 1)
        ),
        *(
            (
                Atom(f"latin_column_{column}"),
                tuple(
                    latin_cell(row, column)
                    for row in range(1, size + 1)
                ),
            )
            for column in range(1, size + 1)
        ),
    ]
    for line, cells in lines:
        facts.append(Fact(Triple(line, KIND, LATIN_LINE)))
        facts.extend(
            Fact(
                Triple(
                    line,
                    CELL,
                    FiniteSequence((Number(position), cell)),
                )
            )
            for position, cell in enumerate(cells, start=1)
        )

    fact_tuple = tuple(facts)
    return FiniteCSP(
        problem,
        fact_tuple,
        {},
        constraints=instantiate_constraint_templates(
            _latin_square_templates(),
            fact_tuple,
        ),
    )


@cache
def _latin_square_templates() -> tuple[PersistentConstraintTemplate, ...]:
    path = Path(__file__).resolve().parent / "latin_square.constraints"
    return parse_constraint_templates(path.read_text())


def solve_latin_square(
    size: int = 4,
    *,
    max_solutions: int = 1,
    max_nodes: int = 100_000,
    reduced: bool = True,
) -> ChoiceSearchResult:
    model = latin_square_facts(size, reduced=reduced)
    return solve_finite_csp(
        model,
        max_solutions=max_solutions,
        max_nodes=max_nodes,
        rule_groups=(
            *finite_csp_rule_library().finite_domain_groups,
            *model.groups,
        ),
    )


def latin_square_from_solution(
    solution: ChoiceSolution,
    size: int,
) -> tuple[tuple[int, ...], ...]:
    assignment = assignment_from_solution(
        solution,
        latin_square_problem(size),
    )
    return tuple(
        tuple(
            _integer(assignment[latin_cell(row, column)])
            for column in range(1, size + 1)
        )
        for row in range(1, size + 1)
    )


# Concise application-local compatibility name.
square_from_solution = latin_square_from_solution


def _integer(term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise ValueError("a Latin-square cell must contain an integer")
    return term.value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", nargs="?", type=int, default=4)
    parser.add_argument("--solutions", type=int, default=1)
    parser.add_argument("--unreduced", action="store_true")
    arguments = parser.parse_args()
    result = solve_latin_square(
        arguments.size,
        max_solutions=arguments.solutions,
        reduced=not arguments.unreduced,
    )
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        for row in latin_square_from_solution(solution, arguments.size):
            print(" ".join(map(str, row)))
        print()


if __name__ == "__main__":
    main()
