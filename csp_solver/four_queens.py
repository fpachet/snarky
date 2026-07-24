"""Four queens as a finite binary CSP searched through Snarky rules."""

from __future__ import annotations

from itertools import combinations

from snarky import Atom, ChoiceSearchResult, Fact, Number, Triple

from .solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    BinaryCSP,
    assignment_from_solution,
    binary_constraint_facts,
    solve_binary_csp,
)

PROBLEM = Atom("four_queens")


def four_queens_facts() -> BinaryCSP:
    variables = tuple(Atom(f"queen_{column}") for column in range(1, 5))
    rows = tuple(Number(row) for row in range(1, 5))
    facts: list[Fact] = [
        Fact(Triple(PROBLEM, KIND, CSP_PROBLEM)),
    ]
    for variable in variables:
        facts.append(Fact(Triple(PROBLEM, VARIABLE, variable)))
        facts.append(Fact(Triple(variable, KIND, CSP_VARIABLE)))
        facts.extend(
            Fact(Triple(variable, CANDIDATE, row)) for row in rows
        )
    for (left_column, left), (right_column, right) in combinations(
        enumerate(variables, start=1),
        2,
    ):
        constraint = Atom(
            f"non_attacking_{left_column}_{right_column}"
        )
        relation = Atom(f"safe_{left_column}_{right_column}")
        distance = right_column - left_column
        allowed = tuple(
            (left_row, right_row)
            for left_row in rows
            for right_row in rows
            if left_row != right_row
            and abs(left_row.value - right_row.value) != distance
        )
        facts.extend(
            binary_constraint_facts(
                constraint,
                relation,
                left,
                right,
                allowed,
            )
        )
    return BinaryCSP(PROBLEM, tuple(facts), {})


def solve_four_queens(
    *,
    max_solutions: int = 2,
) -> ChoiceSearchResult:
    return solve_binary_csp(
        four_queens_facts(),
        max_solutions=max_solutions,
    )


def main() -> None:
    result = solve_four_queens()
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        assignment = assignment_from_solution(solution, PROBLEM)
        print(
            [
                assignment[Atom(f"queen_{column}")]
                for column in range(1, 5)
            ]
        )


if __name__ == "__main__":
    main()
