"""Negative-premise refraction planning and activation expiry."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING

from ..facts import Fact
from ..instantiation import IndexedInstantiationStrategy
from ..matching import PatternMatcher
from ..premises import (
    CollectPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from ..rules import Rule, RuleGroup
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import Variable
from .agenda import ActivationKey

if TYPE_CHECKING:
    from .forward import InferenceSession


@dataclass(frozen=True, slots=True)
class _NegativeRefractionPlan:
    group_name: str
    rule: Rule
    simple_dependencies: tuple[FactPremise, ...]
    complex_dependencies: tuple[FactPremise, ...]


def _register_negative_refraction_plans(
    session: InferenceSession,
    group: RuleGroup,
) -> None:
    for rule in group.rules:
        simple, complex_ = _negative_dependency_plan(rule.premises)
        if not simple and not complex_:
            continue
        session._negative_refraction_plans.append(
            _NegativeRefractionPlan(
                group.name,
                rule,
                simple,
                complex_,
            )
        )


def _expire_removed_supports(
    session: InferenceSession,
    removed: frozenset[Fact],
) -> None:
    expired = {
        key
        for key, supports in session._fired_supports.items()
        if any(fact in removed for fact in supports)
    }
    session._fired.difference_update(expired)
    for key in expired:
        session._fired_supports.pop(key, None)


def _reconcile_negative_refraction(
    session: InferenceSession,
    added: tuple[Fact, ...],
) -> None:
    """Expire fired negative activations invalidated by fact additions."""

    oracle: IndexedInstantiationStrategy | None = None
    facts = session._store.facts
    matcher = PatternMatcher()
    for plan in session._negative_refraction_plans:
        fired_count_before = len(session._fired)
        fired_for_rule = {
            key
            for key in session._fired
            if (
                key.rule_group == plan.group_name
                and key.rule_name == plan.rule.name
            )
        }
        negative_dependencies = (
            *plan.simple_dependencies,
            *plan.complex_dependencies,
        )
        if (
            not fired_for_rule
            or not any(
                premise.match(
                    fact,
                    EMPTY_SUBSTITUTION,
                    matcher,
                )
                is not None
                for premise in negative_dependencies
                for fact in added
            )
        ):
            continue

        directly_expired = {
            key
            for key in fired_for_rule
            if any(
                premise.match(
                    fact,
                    _substitution_from_key(key),
                    matcher,
                )
                is not None
                for premise in plan.simple_dependencies
                for fact in added
            )
        }
        session._expire_activation_keys(directly_expired)
        remaining = fired_for_rule - directly_expired
        complex_change = any(
            premise.match(
                fact,
                EMPTY_SUBSTITUTION,
                matcher,
            )
            is not None
            for premise in plan.complex_dependencies
            for fact in added
        )
        if not remaining or not complex_change:
            if len(session._fired) != fired_count_before:
                session._force_full_evaluation.add(
                    (plan.group_name, plan.rule.name)
                )
            continue

        if oracle is None:
            oracle = IndexedInstantiationStrategy()
        active: set[ActivationKey] = set()
        for activation in oracle.instantiate(plan.rule, facts):
            active.add(
                ActivationKey(
                    plan.group_name,
                    plan.rule.name,
                    activation.substitution.key,
                )
            )
        session._expire_activation_keys(remaining - active)
        if len(session._fired) != fired_count_before:
            session._force_full_evaluation.add(
                (plan.group_name, plan.rule.name)
            )


def _expire_activation_keys(
    session: InferenceSession,
    expired: set[ActivationKey],
) -> None:
    session._fired.difference_update(expired)
    for key in expired:
        session._fired_supports.pop(key, None)


@cache
def _negative_fact_premises(
    premises: tuple[Premise, ...],
    *,
    inside_negative: bool = False,
) -> tuple[FactPremise, ...]:
    dependencies: list[FactPremise] = []
    for premise in premises:
        if isinstance(premise, FactPremise):
            if inside_negative:
                dependencies.append(premise)
            continue
        if isinstance(premise, NotExistsPremise):
            dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=True,
                )
            )
            continue
        if isinstance(premise, ExistsPremise):
            dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=inside_negative,
                )
            )
            continue
        if isinstance(premise, (CountPremise, UniquePremise, CollectPremise)):
            dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=True,
                )
            )
    return tuple(dependencies)


@cache
def _negative_dependency_plan(
    premises: tuple[Premise, ...],
) -> tuple[tuple[FactPremise, ...], tuple[FactPremise, ...]]:
    """Split directly watchable top-level blockers from complex negatives."""

    simple: list[FactPremise] = []
    complex_dependencies: list[FactPremise] = []
    for premise in premises:
        if isinstance(premise, ExistsPremise):
            complex_dependencies.extend(
                _negative_fact_premises(premise.premises)
            )
            continue
        if isinstance(premise, (CountPremise, UniquePremise, CollectPremise)):
            complex_dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=True,
                )
            )
            continue
        if not isinstance(premise, NotExistsPremise):
            continue
        if (
            len(premise.premises) == 1
            and isinstance(premise.premises[0], FactPremise)
        ):
            simple.append(premise.premises[0])
        else:
            complex_dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=True,
                )
            )
    return tuple(simple), tuple(complex_dependencies)


def _substitution_from_key(key: ActivationKey) -> Substitution:
    return Substitution(
        (Variable(name), term)
        for name, term in key.substitution
    )
