"""Declarative choice models and rule-based choice production."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from .actions import Action, AddFact, Choice, ForEach
from .engine import InferenceSession
from .facts import Fact
from .instantiation import (
    Activation,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    QueryableInstantiationStrategy,
)
from .premises import BindPremise, FactPremise, Premise
from .rules import Rule, RuleGroup
from .substitutions import Substitution
from .terms import (
    Atom,
    Term,
    Triple,
    render_term,
    variables_in,
)


@dataclass(frozen=True, slots=True)
class ChoiceAlternative:
    """One feasible branch of a declarative choice point."""

    name: str
    facts: tuple[Fact, ...]
    value: Term | None = None
    weight: float = 1.0
    metadata: Mapping[str, object] = field(
        default_factory=dict,
        compare=False,
        hash=False,
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a choice alternative needs a name")
        facts = tuple(self.facts)
        if not facts:
            raise ValueError("a choice alternative must assert at least one fact")
        if not math.isfinite(self.weight) or self.weight < 0:
            raise ValueError("a choice weight must be finite and non-negative")
        object.__setattr__(self, "facts", facts)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class ChoicePoint:
    """A finite set of alternatives emitted from one search state."""

    name: str
    alternatives: tuple[ChoiceAlternative, ...]
    variable: Term | None = None
    metadata: Mapping[str, object] = field(
        default_factory=dict,
        compare=False,
        hash=False,
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a choice point needs a name")
        alternatives = tuple(self.alternatives)
        if not alternatives:
            raise ValueError("a choice point needs at least one alternative")
        names = tuple(alternative.name for alternative in alternatives)
        if len(set(names)) != len(names):
            raise ValueError("choice alternative names must be unique")
        object.__setattr__(self, "alternatives", alternatives)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


type ChoiceProvider = Callable[
    [InferenceSession],
    tuple[ChoicePoint, ...],
]


class RuleChoiceProvider:
    """Expose ``CHOICE`` actions from rules as search choice points.

    Choice rules are excluded from ordinary forward chaining. Their ``WHEN``
    part establishes one stable object context; each sequential ``CHOICE``
    instantiates one target fact inside a branch.
    """

    def __init__(self, groups: Sequence[RuleGroup]) -> None:
        self.groups = tuple(groups)
        choice_rules: list[tuple[str, Rule, tuple[Choice, ...]]] = []
        propagation_groups: list[RuleGroup] = []
        for group in self.groups:
            deterministic: list[Rule] = []
            for rule in group.rules:
                if any(
                    isinstance(action, ForEach)
                    and _contains_nested_choice(action)
                    for action in rule.actions
                ):
                    raise ValueError(
                        "CHOICE inside FOR EACH is not supported"
                    )
                choices: list[Choice] = []
                terminal_actions: list[Action] = []
                terminal_started = False
                for action in rule.actions:
                    if isinstance(action, Choice):
                        if terminal_started:
                            raise ValueError(
                                f"choice rule {rule.name!r} cannot place "
                                "CHOICE after deterministic actions"
                            )
                        choices.append(action)
                    else:
                        terminal_started = True
                        terminal_actions.append(action)
                if not choices:
                    deterministic.append(rule)
                    continue
                choice_rules.append(
                    (group.name, rule, tuple(choices))
                )
                if terminal_actions:
                    completion_name = f"{rule.name}__after_choices"
                    deterministic.append(
                        Rule(
                            completion_name,
                            (
                                *rule.premises,
                                *(
                                    premise
                                    for choice in choices
                                    for premise in (
                                        FactPremise(
                                            choice.entity,
                                            choice.status,
                                        ),
                                        *choice.premises,
                                    )
                                ),
                            ),
                            tuple(terminal_actions),
                            {
                                **rule.metadata,
                                "choice_completion_of": rule.name,
                            },
                        )
                    )
            if deterministic:
                propagation_groups.append(
                    RuleGroup(group.name, tuple(deterministic))
                )
        self.choice_rules = tuple(choice_rules)
        self.propagation_groups = tuple(propagation_groups)

    def __call__(
        self,
        session: InferenceSession,
    ) -> tuple[ChoicePoint, ...]:
        facts = session.facts
        query_strategy = _choice_query_strategy(session)
        points: dict[str, ChoicePoint] = {}
        for group_name, rule, actions in self.choice_rules:
            outer_activations = query_strategy.instantiate(
                rule,
                facts,
            )
            for activation in outer_activations:
                contexts: tuple[Substitution, ...] = (
                    activation.substitution,
                )
                for action_index, action in enumerate(actions):
                    continuing: list[Substitution] = []
                    for context in contexts:
                        existing = _query_premises(
                            (FactPremise(action.entity, action.status),),
                            facts,
                            context,
                            query_strategy,
                        )
                        if existing:
                            continuing.extend(
                                item.substitution for item in existing
                            )
                            continue
                        point = _choice_point_from_action(
                            group_name,
                            rule,
                            action_index,
                            action,
                            context,
                            facts,
                            query_strategy,
                        )
                        if point is not None:
                            previous = points.get(point.name)
                            points[point.name] = (
                                point
                                if previous is None
                                else _merge_choice_points(previous, point)
                            )
                    contexts = tuple(continuing)
                    if not contexts:
                        break
        return tuple(points.values())


def _choice_query_strategy(
    session: InferenceSession,
) -> InstantiationStrategy:
    strategy = session.strategy
    if isinstance(strategy, QueryableInstantiationStrategy):
        return strategy.query_view()
    return IndexedInstantiationStrategy()


def _contains_nested_choice(action: ForEach) -> bool:
    return any(
        isinstance(nested, Choice)
        or (
            isinstance(nested, ForEach)
            and _contains_nested_choice(nested)
        )
        for nested in action.actions
    )


def _choice_point_from_action(
    group_name: str,
    rule: Rule,
    action_index: int,
    action: Choice,
    context: Substitution,
    facts: tuple[Fact, ...],
    strategy: InstantiationStrategy,
) -> ChoicePoint | None:
    candidates = _query_premises(
        action.premises,
        facts,
        context,
        strategy,
    )
    alternatives_by_fact: dict[Fact, ChoiceAlternative] = {}
    introduced = tuple(
        sorted(
            (
                variable
                for variable in (
                    variables_in(action.entity)
                    | variables_in(action.status)
                )
                if variable not in context
            ),
            key=lambda variable: variable.name,
        )
    )
    for candidate in candidates:
        fact = action.instantiate(candidate.substitution)
        value: Term = (
            candidate.substitution.apply(introduced[0])
            if len(introduced) == 1
            else fact.entity
        )
        alternative = ChoiceAlternative(
            render_term(value),
            (fact,),
            value,
            action.resolved_weight(candidate.substitution),
            {
                "rule": rule.name,
                "rule_group": group_name,
                "substitution": candidate.substitution,
                "supports": candidate.premise_facts,
            },
        )
        previous = alternatives_by_fact.get(fact)
        if previous is not None and previous.weight != alternative.weight:
            raise ValueError(
                "the same CHOICE fact has conflicting weights: "
                f"{render_term(fact.entity)}"
            )
        alternatives_by_fact[fact] = alternative
    if not alternatives_by_fact:
        return None
    context_label = ",".join(
        f"{name}={render_term(value)}" for name, value in context.key
    )
    point_name = (
        f"{group_name}:{rule.name}:{action_index}"
        f"[{context_label}]"
    )
    target = context.apply(action.entity)
    decision_variable = (
        target.subject if isinstance(target, Triple) else target
    )
    return ChoicePoint(
        point_name,
        tuple(alternatives_by_fact.values()),
        decision_variable,
        {
            "rule": rule.name,
            "rule_group": group_name,
            "action_index": action_index,
            "substitution": context,
        },
    )


def _merge_choice_points(
    left: ChoicePoint,
    right: ChoicePoint,
) -> ChoicePoint:
    alternatives = {
        alternative.name: alternative
        for alternative in left.alternatives
    }
    for alternative in right.alternatives:
        previous = alternatives.get(alternative.name)
        if previous is not None and previous.facts != alternative.facts:
            raise ValueError(
                f"CHOICE alternative {alternative.name!r} is ambiguous"
            )
        alternatives[alternative.name] = alternative
    return ChoicePoint(
        left.name,
        tuple(alternatives.values()),
        left.variable,
        left.metadata,
    )


def _query_premises(
    premises: tuple[Premise, ...],
    facts: tuple[Fact, ...],
    initial: Substitution,
    strategy: InstantiationStrategy,
) -> tuple[Activation, ...]:
    bindings = tuple(
        BindPremise(variable, initial.apply(value))
        for variable, value in initial.items()
    )
    query = Rule(
        "__choice_query__",
        (*bindings, *premises),
        (AddFact(Atom("__choice_query_result__")),),
    )
    return strategy.instantiate(query, facts)
