"""Bounded Golomb rulers using weighted equalities and ALL_DIFFERENT."""

from __future__ import annotations

import argparse
from functools import cache
from itertools import combinations
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

GOLOMB_MARK = Atom("golomb_mark")
GOLOMB_DISTANCE = Atom("golomb_distance")
GOLOMB_ORDERING = Atom("golomb_ordering")
GOLOMB_EQUATION = Atom("golomb_equation")
MEMBER = Atom("member")
TERM = Atom("term")


def golomb_problem(mark_count: int, maximum_length: int) -> Atom:
    if mark_count < 2:
        raise ValueError("a Golomb ruler requires at least two marks")
    if maximum_length < mark_count - 1:
        raise ValueError("the maximum length is too small")
    return Atom(f"golomb_{mark_count}_{maximum_length}")


def mark(index: int) -> Atom:
    return Atom(f"golomb_mark_{index}")


def distance(left: int, right: int) -> Atom:
    return Atom(f"golomb_distance_{left}_{right}")


def golomb_ruler_model(
    mark_count: int = 5,
    maximum_length: int = 11,
) -> FiniteCSP:
    """Build a ruler whose final mark is at most ``maximum_length``."""

    problem = golomb_problem(mark_count, maximum_length)
    facts: list[Fact] = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for index in range(mark_count):
        variable = mark(index)
        lower = index
        upper = maximum_length - (mark_count - 1 - index)
        domain = (0,) if index == 0 else range(lower, upper + 1)
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                Fact(Triple(variable, KIND, GOLOMB_MARK)),
                *(
                    Fact(Triple(variable, CANDIDATE, Number(value)))
                    for value in domain
                ),
            )
        )
    for left, right in combinations(range(mark_count), 2):
        variable = distance(left, right)
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                Fact(Triple(variable, KIND, GOLOMB_DISTANCE)),
                *(
                    Fact(Triple(variable, CANDIDATE, Number(value)))
                    for value in range(1, maximum_length + 1)
                ),
            )
        )
        equation = Atom(f"golomb_equation_{left}_{right}")
        facts.append(Fact(Triple(equation, KIND, GOLOMB_EQUATION)))
        for position, coefficient, term_variable in (
            (1, 1, variable),
            (2, 1, mark(left)),
            (3, -1, mark(right)),
        ):
            facts.append(
                Fact(
                    Triple(
                        equation,
                        TERM,
                        FiniteSequence(
                            (
                                Number(position),
                                Number(coefficient),
                                term_variable,
                            )
                        ),
                    )
                )
            )
    ordered_pairs = [
        (mark(index), mark(index + 1))
        for index in range(mark_count - 1)
    ]
    if mark_count > 2:
        ordered_pairs.append(
            (distance(0, 1), distance(mark_count - 2, mark_count - 1))
        )
    for index, (left, right) in enumerate(ordered_pairs, start=1):
        ordering = Atom(f"golomb_ordering_{index}")
        facts.extend(
            (
                Fact(Triple(ordering, KIND, GOLOMB_ORDERING)),
                Fact(
                    Triple(
                        ordering,
                        MEMBER,
                        FiniteSequence((Number(1), left)),
                    )
                ),
                Fact(
                    Triple(
                        ordering,
                        MEMBER,
                        FiniteSequence((Number(2), right)),
                    )
                ),
            )
        )
    fact_tuple = tuple(facts)
    return FiniteCSP(
        problem,
        fact_tuple,
        {},
        constraints=instantiate_constraint_templates(
            _templates(),
            fact_tuple,
        ),
    )


@cache
def _templates() -> tuple[PersistentConstraintTemplate, ...]:
    return parse_constraint_templates(
        Path(__file__).with_suffix(".constraints").read_text()
    )


def solve_golomb_ruler(
    mark_count: int = 5,
    maximum_length: int = 11,
    *,
    max_nodes: int = 200_000,
) -> ChoiceSearchResult:
    model = golomb_ruler_model(mark_count, maximum_length)
    return solve_finite_csp(
        model,
        max_nodes=max_nodes,
        rule_groups=finite_csp_rule_library().finite_domain_groups,
    )


def marks_from_solution(
    solution: ChoiceSolution,
    mark_count: int,
    maximum_length: int,
) -> tuple[int, ...]:
    assignment = assignment_from_solution(
        solution,
        golomb_problem(mark_count, maximum_length),
    )
    return tuple(_integer(assignment[mark(index)]) for index in range(mark_count))


def validate_ruler(marks: tuple[int, ...]) -> bool:
    if not marks or marks[0] != 0:
        return False
    if any(
        left >= right
        for left, right in zip(marks[:-1], marks[1:], strict=True)
    ):
        return False
    distances = [
        right - left
        for left, right in combinations(marks, 2)
    ]
    return len(distances) == len(set(distances))


def _integer(term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise ValueError("a Golomb variable must contain an integer")
    return term.value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("marks", nargs="?", type=int, default=5)
    parser.add_argument("maximum_length", nargs="?", type=int, default=11)
    arguments = parser.parse_args()
    result = solve_golomb_ruler(arguments.marks, arguments.maximum_length)
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        print(
            marks_from_solution(
                solution,
                arguments.marks,
                arguments.maximum_length,
            )
        )


if __name__ == "__main__":
    main()
