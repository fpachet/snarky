"""The SEND + MORE = MONEY cryptarithm using persistent LINEAR_SUM."""

from __future__ import annotations

from functools import cache
from pathlib import Path

from snarky import Atom, ChoiceSearchResult, ChoiceSolution, Fact, Number, Triple

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

PROBLEM = Atom("send_more_money")
CRYPTARITHM_LETTER = Atom("cryptarithm_letter")
CRYPTARITHM_TERM = Atom("cryptarithm_term")
POSITION = Atom("position")
COEFFICIENT = Atom("coefficient")
LETTER = Atom("letter")
LETTERS = tuple(Atom(letter) for letter in "SENDMORY")
COEFFICIENTS = {
    Atom("S"): 1000,
    Atom("E"): 91,
    Atom("N"): -90,
    Atom("D"): 1,
    Atom("M"): -9000,
    Atom("O"): -900,
    Atom("R"): 10,
    Atom("Y"): -1,
}


def send_more_money_model() -> FiniteCSP:
    """Build the classical alphametic as one weighted equation."""

    facts: list[Fact] = [Fact(Triple(PROBLEM, KIND, CSP_PROBLEM))]
    for letter in LETTERS:
        domain = range(1, 10) if letter in {Atom("S"), Atom("M")} else range(10)
        facts.extend(
            (
                Fact(Triple(PROBLEM, VARIABLE, letter)),
                Fact(Triple(letter, KIND, CSP_VARIABLE)),
                Fact(Triple(letter, KIND, CRYPTARITHM_LETTER)),
                *(
                    Fact(Triple(letter, CANDIDATE, Number(value)))
                    for value in domain
                ),
            )
        )
    for position, letter in enumerate(LETTERS, start=1):
        term = Atom(f"cryptarithm_term_{position}")
        facts.extend(
            (
                Fact(Triple(term, KIND, CRYPTARITHM_TERM)),
                Fact(Triple(term, POSITION, Number(position))),
                Fact(
                    Triple(
                        term,
                        COEFFICIENT,
                        Number(COEFFICIENTS[letter]),
                    )
                ),
                Fact(Triple(term, LETTER, letter)),
            )
        )
    fact_tuple = tuple(facts)
    return FiniteCSP(
        PROBLEM,
        fact_tuple,
        {},
        constraints=instantiate_constraint_templates(
            _templates(),
            fact_tuple,
        ),
    )


@cache
def _templates() -> tuple[PersistentConstraintTemplate, ...]:
    path = Path(__file__).with_suffix(".constraints")
    return parse_constraint_templates(path.read_text())


def solve_send_more_money(
    *,
    max_solutions: int = 1,
    max_nodes: int = 100_000,
) -> ChoiceSearchResult:
    model = send_more_money_model()
    return solve_finite_csp(
        model,
        max_solutions=max_solutions,
        max_nodes=max_nodes,
        rule_groups=finite_csp_rule_library().finite_domain_groups,
    )


def words_from_solution(
    solution: ChoiceSolution,
) -> tuple[int, int, int]:
    assignment = assignment_from_solution(solution, PROBLEM)

    def word(text: str) -> int:
        return int(
            "".join(
                str(_integer(assignment[Atom(letter)]))
                for letter in text
            )
        )

    return word("SEND"), word("MORE"), word("MONEY")


def _integer(term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise ValueError("a cryptarithm letter must contain an integer")
    return term.value


def main() -> None:
    result = solve_send_more_money()
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        send, more, money = words_from_solution(solution)
        print(f"{send} + {more} = {money}")


if __name__ == "__main__":
    main()
