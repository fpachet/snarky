"""Generic binary CSP protocol expressed as Snarky facts and rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from snarky import (
    Atom,
    ChoiceAlternative,
    ChoicePoint,
    ChoicePolicy,
    ChoiceSearchResult,
    ChoiceSolution,
    ChoiceTraversal,
    Fact,
    FiniteSequence,
    ForwardEngine,
    InferenceSession,
    MRVChoicePolicy,
    RuleGroup,
    SemiNaiveInstantiationStrategy,
    SessionChoiceSearch,
    Term,
    Triple,
    parse_rule_groups,
    render_term,
)

KIND = Atom("kind")
CSP_PROBLEM = Atom("csp_problem")
CSP_VARIABLE = Atom("csp_variable")
VARIABLE = Atom("variable")
CANDIDATE = Atom("candidate")
VALUE = Atom("value")
DECISION = Atom("decision")
STATE = Atom("state")
SOLVED = Atom("solved")
CONTRADICTION = Atom("contradiction")
BINARY_CONSTRAINT = Atom("binary_constraint")
RELATION = Atom("relation")
LEFT = Atom("left")
RIGHT = Atom("right")
ALLOWS = Atom("allows")
SEARCH = Atom("search")


@dataclass(frozen=True, slots=True)
class BinaryCSP:
    """One finite binary CSP encoded entirely as ground Snarky facts."""

    problem: Atom
    facts: tuple[Fact, ...]
    weights: Mapping[tuple[Term, Term], float]
    groups: tuple[RuleGroup, ...] = ()

    def __post_init__(self) -> None:
        facts = tuple(self.facts)
        if not facts:
            raise ValueError("a binary CSP needs initial facts")
        object.__setattr__(self, "facts", facts)
        object.__setattr__(self, "weights", dict(self.weights))
        object.__setattr__(self, "groups", tuple(self.groups))


def binary_constraint_facts(
    constraint: Atom,
    relation: Atom,
    left: Term,
    right: Term,
    allowed_pairs: Sequence[tuple[Term, Term]],
) -> tuple[Fact, ...]:
    """Return the standard fact representation of one extensional relation."""

    return (
        Fact(Triple(constraint, KIND, BINARY_CONSTRAINT)),
        Fact(Triple(constraint, RELATION, relation)),
        Fact(Triple(constraint, LEFT, left)),
        Fact(Triple(constraint, RIGHT, right)),
        *(
            Fact(
                Triple(
                    relation,
                    ALLOWS,
                    FiniteSequence((left_value, right_value)),
                )
            )
            for left_value, right_value in allowed_pairs
        ),
    )


def solve_binary_csp(
    model: BinaryCSP,
    *,
    max_solutions: int = 1,
    max_nodes: int = 10_000,
    policy: ChoicePolicy | None = None,
    traversal: ChoiceTraversal = ChoiceTraversal.DEPTH_FIRST,
    seed: int = 0,
) -> ChoiceSearchResult:
    """Propagate and search a fact-encoded CSP without a Python solver."""

    groups = (*_csp_groups(), *model.groups)
    session = ForwardEngine(()).create_session(model.facts)
    solved_fact = Fact(Triple(model.problem, STATE, SOLVED))
    contradiction_fact = Fact(
        Triple(model.problem, STATE, CONTRADICTION)
    )
    invalid_choice_fact = Fact(Triple(SEARCH, STATE, CONTRADICTION))

    def choices(current: InferenceSession) -> tuple[ChoicePoint, ...]:
        facts = current.facts
        variables = tuple(
            fact.entity.object
            for fact in facts
            if isinstance(fact.entity, Triple)
            and fact.entity.subject == model.problem
            and fact.entity.relation == VARIABLE
        )
        assigned = {
            fact.entity.subject
            for fact in facts
            if isinstance(fact.entity, Triple)
            and fact.entity.relation == VALUE
        }
        candidates: dict[Term, list[Term]] = {
            variable: [] for variable in variables if variable not in assigned
        }
        for fact in facts:
            entity = fact.entity
            if (
                isinstance(entity, Triple)
                and entity.relation == CANDIDATE
                and entity.subject in candidates
            ):
                candidates[entity.subject].append(entity.object)
        return tuple(
            ChoicePoint(
                f"assign:{render_term(variable)}",
                tuple(
                    ChoiceAlternative(
                        render_term(value),
                        (Fact(Triple(variable, DECISION, value)),),
                        value,
                        model.weights.get((variable, value), 1.0),
                        {"variable": variable},
                    )
                    for value in values
                ),
                variable,
            )
            for variable, values in candidates.items()
            if values
        )

    search = SessionChoiceSearch(
        groups,
        choices,
        lambda current: solved_fact in current.facts,
        lambda current: (
            contradiction_fact in current.facts
            or invalid_choice_fact in current.facts
        ),
        policy=policy or MRVChoicePolicy(),
        traversal=traversal,
        max_nodes=max_nodes,
        max_solutions=max_solutions,
        seed=seed,
        branch_strategy_factory=SemiNaiveInstantiationStrategy,
    )
    return search.solve(session)


def assignment_from_solution(
    solution: ChoiceSolution,
    problem: Atom,
) -> dict[Term, Term]:
    variables = {
        fact.entity.object
        for fact in solution.session.facts
        if isinstance(fact.entity, Triple)
        and fact.entity.subject == problem
        and fact.entity.relation == VARIABLE
    }
    return {
        fact.entity.subject: fact.entity.object
        for fact in solution.session.facts
        if isinstance(fact.entity, Triple)
        and fact.entity.relation == VALUE
        and fact.entity.subject in variables
    }


@cache
def _csp_groups() -> tuple[RuleGroup, ...]:
    root = Path(__file__).resolve().parents[1]
    decision_text = (root / "csp_solver" / "rules.rules").read_text()
    binary_text = (
        root / "rulebases" / "constraints" / "binary" / "rules.rules"
    ).read_text()
    return (*parse_rule_groups(decision_text), *parse_rule_groups(binary_text))
