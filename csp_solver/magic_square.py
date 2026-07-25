"""Normal magic squares as finite CSPs searched through Snarky rules."""

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

MAGIC_CELL = Atom("magic_cell")
MAGIC_LINE = Atom("magic_line")
SIZE = Atom("size")
TARGET = Atom("target")
ROW = Atom("row")
COLUMN = Atom("column")
CELL = Atom("cell")


def magic_constant(size: int) -> int:
    """Return the common row, column, and diagonal sum for order ``size``."""

    if size < 1:
        raise ValueError("the square size must be positive")
    return size * (size * size + 1) // 2


def magic_square_problem(size: int) -> Atom:
    """Return the stable problem atom for a square of the requested order."""

    if size < 1:
        raise ValueError("the square size must be positive")
    return Atom(f"magic_square_{size}")


def magic_cell(row: int, column: int) -> Atom:
    """Return the CSP variable naming one cell."""

    if row < 1 or column < 1:
        raise ValueError("magic-square coordinates are one-based")
    return Atom(f"cell_{row}_{column}")


def magic_square_facts(size: int) -> FiniteCSP:
    """Build a normal order-``size`` magic square as declarative Snarky facts.

    Cell variables range over ``1..size²``.  One persistent global
    ``ALL_DIFFERENT`` covers all cells and one persistent ``SUM`` covers each
    row, column, and diagonal.  These constraints filter candidate facts
    before ordinary rules and ``CHOICE`` inspect them.
    """

    problem = magic_square_problem(size)
    target = magic_constant(size)
    maximum_value = size * size
    facts: list[Fact] = [
        Fact(Triple(problem, KIND, CSP_PROBLEM)),
        Fact(Triple(problem, SIZE, Number(size))),
        Fact(Triple(problem, TARGET, Number(target))),
    ]

    for row in range(1, size + 1):
        for column in range(1, size + 1):
            variable = magic_cell(row, column)
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, variable)),
                    Fact(Triple(variable, KIND, CSP_VARIABLE)),
                    Fact(Triple(variable, KIND, MAGIC_CELL)),
                    Fact(Triple(variable, ROW, Number(row))),
                    Fact(Triple(variable, COLUMN, Number(column))),
                    *(
                        Fact(Triple(variable, CANDIDATE, Number(value)))
                        for value in range(1, maximum_value + 1)
                    ),
                )
            )

    lines = [
        *(
            tuple(magic_cell(row, column) for column in range(1, size + 1))
            for row in range(1, size + 1)
        ),
        *(
            tuple(magic_cell(row, column) for row in range(1, size + 1))
            for column in range(1, size + 1)
        ),
        tuple(magic_cell(index, index) for index in range(1, size + 1)),
        tuple(
            magic_cell(index, size + 1 - index)
            for index in range(1, size + 1)
        ),
    ]
    for line_number, cells in enumerate(lines, start=1):
        line = Atom(f"magic_line_{line_number}")
        facts.extend(
            (
                Fact(Triple(line, KIND, MAGIC_LINE)),
                Fact(Triple(line, TARGET, Number(target))),
                *(
                    Fact(
                        Triple(
                            line,
                            CELL,
                            FiniteSequence((Number(position), cell)),
                        )
                    )
                    for position, cell in enumerate(cells, start=1)
                ),
            )
        )
    fact_tuple = tuple(facts)

    return FiniteCSP(
        problem,
        fact_tuple,
        {},
        constraints=instantiate_constraint_templates(
            _magic_square_templates(),
            fact_tuple,
        ),
    )


@cache
def _magic_square_templates() -> tuple[PersistentConstraintTemplate, ...]:
    path = Path(__file__).resolve().parent / "magic_square.constraints"
    return parse_constraint_templates(path.read_text())


def solve_magic_square(
    size: int = 3,
    *,
    max_solutions: int = 1,
    max_nodes: int = 100_000,
) -> ChoiceSearchResult:
    """Solve a normal magic square using Snarky propagation and choices."""

    model = magic_square_facts(size)
    return solve_finite_csp(
        model,
        max_solutions=max_solutions,
        max_nodes=max_nodes,
        rule_groups=(
            *finite_csp_rule_library().finite_domain_groups,
            *model.groups,
        ),
    )


def square_from_solution(
    solution: ChoiceSolution,
    size: int,
) -> tuple[tuple[int, ...], ...]:
    """Project one Snarky solution into an integer grid."""

    assignment = assignment_from_solution(
        solution,
        magic_square_problem(size),
    )
    rows: list[tuple[int, ...]] = []
    for row in range(1, size + 1):
        values: list[int] = []
        for column in range(1, size + 1):
            term = assignment[magic_cell(row, column)]
            if not isinstance(term, Number) or not isinstance(term.value, int):
                raise ValueError("a magic-square cell must contain an integer")
            values.append(term.value)
        rows.append(tuple(values))
    return tuple(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", nargs="?", type=int, default=3)
    parser.add_argument("--solutions", type=int, default=1)
    arguments = parser.parse_args()

    result = solve_magic_square(
        arguments.size,
        max_solutions=arguments.solutions,
    )
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        for row in square_from_solution(solution, arguments.size):
            print(" ".join(f"{value:2}" for value in row))
        print()


if __name__ == "__main__":
    main()
