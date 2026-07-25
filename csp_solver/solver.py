"""Generic finite-CSP protocol expressed as Snarky facts and rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from snarky import (
    Atom,
    ChoicePolicy,
    ChoiceSearchResult,
    ChoiceSolution,
    ChoiceTraversal,
    DomWdegChoicePolicy,
    Fact,
    FiniteSequence,
    ForwardEngine,
    InferenceSession,
    MRVChoicePolicy,
    Number,
    PropagationGuidedChoicePolicy,
    RuleChoiceProvider,
    RuleGroup,
    SemiNaiveInstantiationStrategy,
    SessionChoiceSearch,
    Term,
    Triple,
    parse_rule_groups,
)

from .finite_domain_choice import FiniteDomainChoiceProvider
from .finite_domain_projection import FiniteDomainProjection
from .finite_domain_state import FiniteDomainStatePropagator
from .persistent_constraints import (
    PersistentConstraint,
    PersistentConstraintPropagator,
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
CHOICE_WEIGHT = Atom("choice_weight")
VIOLATED_CONSTRAINT = Atom("violated_constraint")
EMPTY_DOMAIN = Atom("empty_domain")


@dataclass(frozen=True, slots=True)
class FiniteCSP:
    """One finite CSP encoded as ground facts and declarative rule groups.

    Extensional binary relations are one representation, not a restriction
    of the protocol. ``groups`` may implement intensional, n-ary, global, or
    application-specific propagation. ``constraints`` remain active across
    the search and filter candidate facts before rules and choices inspect
    each stable state.
    """

    problem: Atom
    facts: tuple[Fact, ...]
    weights: Mapping[tuple[Term, Term], float]
    groups: tuple[RuleGroup, ...] = ()
    constraints: tuple[PersistentConstraint, ...] = ()

    def __post_init__(self) -> None:
        facts = tuple(self.facts)
        if not facts:
            raise ValueError("a finite CSP needs initial facts")
        object.__setattr__(self, "facts", facts)
        object.__setattr__(self, "weights", dict(self.weights))
        object.__setattr__(self, "groups", tuple(self.groups))
        object.__setattr__(self, "constraints", tuple(self.constraints))


# Compatibility name retained for the first public CSP project.
BinaryCSP = FiniteCSP


@dataclass(frozen=True, slots=True)
class FiniteCSPRuleLibrary:
    """Named reusable groups of the finite-CSP protocol."""

    choices: RuleGroup
    binary_constraints: RuleGroup
    domains: RuleGroup
    problems: RuleGroup

    @property
    def groups(self) -> tuple[RuleGroup, ...]:
        """All CSP groups in the legacy default order."""

        return (
            self.choices,
            self.binary_constraints,
            self.domains,
            self.problems,
        )

    @property
    def finite_domain_groups(self) -> tuple[RuleGroup, ...]:
        """Groups needed when propagation is supplied by global constraints."""

        return (
            self.choices,
            self.domains,
            self.problems,
        )


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
    model: FiniteCSP,
    *,
    max_solutions: int = 1,
    max_nodes: int = 10_000,
    policy: ChoicePolicy | None = None,
    traversal: ChoiceTraversal = ChoiceTraversal.DEPTH_FIRST,
    seed: int = 0,
    reversible_depth_first: bool = True,
    lazy_frontier: bool = True,
    rule_groups: Sequence[RuleGroup] | None = None,
) -> ChoiceSearchResult:
    """Compatibility wrapper for :func:`solve_finite_csp`."""

    return solve_finite_csp(
        model,
        max_solutions=max_solutions,
        max_nodes=max_nodes,
        policy=policy,
        traversal=traversal,
        seed=seed,
        reversible_depth_first=reversible_depth_first,
        lazy_frontier=lazy_frontier,
        rule_groups=rule_groups,
    )


def constraint_dom_wdeg_policy(
    model: FiniteCSP,
) -> DomWdegChoicePolicy:
    """Build a failure-attributed dom/wdeg policy for *model*."""

    scopes: dict[Term, tuple[Term, ...]] = {
        constraint.name: constraint.variables
        for constraint in model.constraints
    }
    incident_lists: dict[Term, list[Term]] = {}
    for constraint, variables in scopes.items():
        for variable in variables:
            incident_lists.setdefault(variable, []).append(constraint)
    incident = {
        variable: tuple(constraints)
        for variable, constraints in incident_lists.items()
    }

    def failures(session: InferenceSession) -> tuple[Term, ...]:
        violated = tuple(
            fact.entity.object
            for fact in session.facts
            if isinstance(fact.entity, Triple)
            and fact.entity.subject == model.problem
            and fact.entity.relation == VIOLATED_CONSTRAINT
        )
        if violated:
            return tuple(dict.fromkeys(violated))
        empty_variables = tuple(
            fact.entity.object
            for fact in session.facts
            if isinstance(fact.entity, Triple)
            and fact.entity.subject == model.problem
            and fact.entity.relation == EMPTY_DOMAIN
        )
        return tuple(
            dict.fromkeys(
                constraint
                for variable in empty_variables
                for constraint in incident.get(variable, ())
            )
        )

    return DomWdegChoicePolicy(scopes, failures)


def constraint_propagation_guided_policy(
    model: FiniteCSP,
    *,
    maximum_alternatives: int = 8,
) -> PropagationGuidedChoicePolicy:
    """Combine dom/wdeg with bounded least-constraining-value probes."""

    def remaining_candidates(session: InferenceSession) -> float:
        return float(
            sum(
                isinstance(fact.entity, Triple)
                and fact.entity.relation == CANDIDATE
                for fact in session.facts
            )
        )

    return PropagationGuidedChoicePolicy(
        constraint_dom_wdeg_policy(model),
        remaining_candidates,
        maximum_alternatives=maximum_alternatives,
    )


def solve_finite_csp(
    model: FiniteCSP,
    *,
    max_solutions: int = 1,
    max_nodes: int = 10_000,
    policy: ChoicePolicy | None = None,
    traversal: ChoiceTraversal = ChoiceTraversal.DEPTH_FIRST,
    seed: int = 0,
    reversible_depth_first: bool = True,
    lazy_frontier: bool = True,
    rule_groups: Sequence[RuleGroup] | None = None,
) -> ChoiceSearchResult:
    """Propagate and search a fact-encoded finite CSP using Snarky.

    ``rule_groups`` makes orchestration explicit when supplied.  The default
    remains the complete CSP library followed by the model groups for
    compatibility.
    """

    selected_groups = (
        (*_csp_groups(), *model.groups) if rule_groups is None else tuple(rule_groups)
    )
    rule_provider = RuleChoiceProvider(selected_groups)
    projection = FiniteDomainProjection()
    optimized_finite_domain = _supports_compiled_finite_domain(
        rule_provider
    )
    propagation_groups = rule_provider.propagation_groups
    state_propagator: FiniteDomainStatePropagator | None = None
    if optimized_finite_domain:
        library = finite_csp_rule_library()
        propagation_groups = tuple(
            group
            for group in propagation_groups
            if group.name
            not in {
                library.choices.name,
                library.domains.name,
                library.problems.name,
            }
        )
        state_propagator = FiniteDomainStatePropagator(
            model.problem,
            library.choices,
            library.domains,
            library.problems,
            projection,
        )
    provider = (
        FiniteDomainChoiceProvider(propagation_groups, projection)
        if optimized_finite_domain
        else rule_provider
    )
    existing_weights = _existing_choice_weights(model.facts)
    weighted_facts = tuple(
        Fact(
            Triple(
                fact.entity.subject,
                CHOICE_WEIGHT,
                FiniteSequence(
                    (
                        fact.entity.object,
                        Number(
                            model.weights.get(
                                (
                                    fact.entity.subject,
                                    fact.entity.object,
                                ),
                                1.0,
                            )
                        ),
                    )
                ),
            )
        )
        for fact in model.facts
        if isinstance(fact.entity, Triple)
        and fact.entity.relation == CANDIDATE
        and (fact.entity.subject, fact.entity.object) not in existing_weights
    )
    session = ForwardEngine(()).create_session((*model.facts, *weighted_facts))
    solved_fact = Fact(Triple(model.problem, STATE, SOLVED))
    contradiction_fact = Fact(Triple(model.problem, STATE, CONTRADICTION))
    invalid_choice_fact = Fact(Triple(SEARCH, STATE, CONTRADICTION))

    search = SessionChoiceSearch(
        provider.propagation_groups,
        provider,
        lambda current: solved_fact in current.facts,
        lambda current: (
            contradiction_fact in current.facts or invalid_choice_fact in current.facts
        ),
        policy=(
            policy
            or (
                constraint_dom_wdeg_policy(model)
                if model.constraints
                else MRVChoicePolicy()
            )
        ),
        traversal=traversal,
        max_nodes=max_nodes,
        max_solutions=max_solutions,
        seed=seed,
        branch_strategy_factory=SemiNaiveInstantiationStrategy,
        reversible_depth_first=reversible_depth_first,
        lazy_frontier=lazy_frontier,
        propagators=(
            *((state_propagator,) if state_propagator is not None else ()),
            *(
                (
                    PersistentConstraintPropagator(
                        model.problem,
                        model.constraints,
                        projection,
                    ),
                )
                if model.constraints
                else ()
            ),
        ),
    )
    return search.solve(session)


def _supports_compiled_finite_domain(
    provider: RuleChoiceProvider,
) -> bool:
    library = finite_csp_rule_library()
    return (
        len(provider.choice_rules) == 1
        and provider.choice_rules[0][0] == "apply_csp_choices"
        and provider.choice_rules[0][1].name == "choose_csp_value"
        and len(provider.choice_rules[0][2]) == 1
        and library.domains in provider.groups
        and library.problems in provider.groups
    )


def _existing_choice_weights(
    facts: tuple[Fact, ...],
) -> frozenset[tuple[Term, Term]]:
    output: set[tuple[Term, Term]] = set()
    for fact in facts:
        entity = fact.entity
        if (
            isinstance(entity, Triple)
            and entity.relation == CHOICE_WEIGHT
            and isinstance(entity.object, FiniteSequence)
            and len(entity.object.elements) == 2
        ):
            output.add((entity.subject, entity.object.elements[0]))
    return frozenset(output)


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
def finite_csp_rule_library() -> FiniteCSPRuleLibrary:
    """Load individually selectable groups implementing the CSP protocol."""

    root = Path(__file__).resolve().parents[1]
    decision_text = (root / "csp_solver" / "rules.rules").read_text()
    binary_text = (
        root / "rulebases" / "constraints" / "binary" / "rules.rules"
    ).read_text()
    (choices,) = parse_rule_groups(decision_text)
    binary_constraints, domains, problems = parse_rule_groups(binary_text)
    return FiniteCSPRuleLibrary(
        choices,
        binary_constraints,
        domains,
        problems,
    )


def _csp_groups() -> tuple[RuleGroup, ...]:
    return finite_csp_rule_library().groups
