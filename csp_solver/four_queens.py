"""Four queens as a finite binary CSP searched through Snarky rules."""

from __future__ import annotations

from functools import cache
from itertools import combinations
from pathlib import Path

from snarky import (
    Atom,
    ChoiceSearchResult,
    Fact,
    Number,
    RuleGroup,
    Triple,
    parse_rule_groups,
)

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
QUEEN = Atom("queen")
COLUMN = Atom("column")


def n_queens_problem(size: int) -> Atom:
    if size < 1:
        raise ValueError("the board size must be positive")
    return PROBLEM if size == 4 else Atom(f"{size}_queens")


def n_queens_facts(size: int) -> BinaryCSP:
    """Build the declarative finite CSP for an arbitrary board size."""

    problem = n_queens_problem(size)
    variables = tuple(
        Atom(f"queen_{column}") for column in range(1, size + 1)
    )
    rows = tuple(Number(row) for row in range(1, size + 1))
    facts: list[Fact] = [
        Fact(Triple(problem, KIND, CSP_PROBLEM)),
    ]
    for variable in variables:
        facts.append(Fact(Triple(problem, VARIABLE, variable)))
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
    return BinaryCSP(problem, tuple(facts), {})


def four_queens_facts() -> BinaryCSP:
    return n_queens_facts(4)


def n_queens_intensional_facts(size: int) -> BinaryCSP:
    """Build N queens without materialized binary allowed-pair tables."""

    problem = n_queens_problem(size)
    rows = tuple(Number(row) for row in range(1, size + 1))
    facts: list[Fact] = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for column in range(1, size + 1):
        variable = Atom(f"queen_{column}")
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                Fact(Triple(variable, KIND, QUEEN)),
                Fact(Triple(variable, COLUMN, Number(column))),
                *(
                    Fact(Triple(variable, CANDIDATE, row))
                    for row in rows
                ),
            )
        )
    return BinaryCSP(
        problem,
        tuple(facts),
        {},
        _n_queens_intensional_groups(),
    )


@cache
def _n_queens_intensional_groups() -> tuple[RuleGroup, ...]:
    rules_path = (
        Path(__file__).resolve().parent / "n_queens_intensional.rules"
    )
    return parse_rule_groups(rules_path.read_text())


def solve_n_queens(
    size: int,
    *,
    max_solutions: int = 1,
    reversible_depth_first: bool = True,
) -> ChoiceSearchResult:
    return solve_binary_csp(
        n_queens_facts(size),
        max_solutions=max_solutions,
        reversible_depth_first=reversible_depth_first,
    )


def solve_n_queens_intensional(
    size: int,
    *,
    max_solutions: int = 1,
) -> ChoiceSearchResult:
    return solve_binary_csp(
        n_queens_intensional_facts(size),
        max_solutions=max_solutions,
    )


def solve_four_queens(
    *,
    max_solutions: int = 2,
    reversible_depth_first: bool = True,
) -> ChoiceSearchResult:
    return solve_n_queens(
        4,
        max_solutions=max_solutions,
        reversible_depth_first=reversible_depth_first,
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
