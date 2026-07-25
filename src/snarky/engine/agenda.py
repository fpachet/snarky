"""Incremental agenda memory and dependency helpers."""

from __future__ import annotations

from dataclasses import dataclass

from ..facts import Fact
from ..instantiation import (
    Activation,
    FactDelta,
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
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
from ..stores.naive import NaiveFactStore
from ..terms import Term, Triple, is_ground
from .events import InferenceEvent


@dataclass(frozen=True, slots=True)
class _AgendaMemory:
    group: RuleGroup
    activations: tuple[tuple[Activation, ...], ...]
    revision: int
    dependencies: _RuleDependencyIndex


@dataclass(frozen=True, slots=True)
class _RuleDependencyIndex:
    by_token: dict[tuple[str, Term], frozenset[int]]
    wildcard: frozenset[int]

    def affected(self, events: tuple[InferenceEvent, ...]) -> frozenset[int]:
        if not events:
            return frozenset()
        affected = set(self.wildcard)
        for event in events:
            for token in _dependency_tokens_for_fact(event.fact):
                affected.update(self.by_token.get(token, ()))
        return frozenset(affected)


def _build_rule_dependency_index(
    group: RuleGroup,
) -> _RuleDependencyIndex:
    by_token: dict[tuple[str, Term], set[int]] = {}
    wildcard: set[int] = set()
    for rule_index, rule in enumerate(group.rules):
        fact_premises = _all_fact_premises(rule.premises)
        if not fact_premises:
            wildcard.add(rule_index)
            continue
        for premise in fact_premises:
            tokens = _dependency_tokens_for_premise(premise)
            if not tokens:
                wildcard.add(rule_index)
                break
            for token in tokens:
                by_token.setdefault(token, set()).add(rule_index)
    return _RuleDependencyIndex(
        {
            token: frozenset(rule_indices)
            for token, rule_indices in by_token.items()
        },
        frozenset(wildcard),
    )


def _merge_agenda_activations(
    rule: Rule,
    previous: tuple[Activation, ...],
    refreshed: tuple[Activation, ...],
    delta: FactDelta,
    strategy: InstantiationStrategy,
    store: NaiveFactStore,
) -> tuple[Activation, ...]:
    """Adapt delta-only semi-naïve results to a materialized agenda row."""

    has_non_monotonic_query = any(
        isinstance(
            premise,
            (
                ExistsPremise,
                NotExistsPremise,
                CountPremise,
                UniquePremise,
                CollectPremise,
            ),
        )
        for premise in rule.premises
    )
    if (
        not isinstance(strategy, SemiNaiveInstantiationStrategy)
        or delta.removed
        or has_non_monotonic_query
    ):
        return refreshed
    retained = (
        activation
        for activation in previous
        if all(fact in store for fact in activation.premise_facts)
    )
    unique: dict[
        tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
        Activation,
    ] = {}
    for activation in (*retained, *refreshed):
        unique.setdefault(
            (activation.substitution.key, activation.premise_facts),
            activation,
        )
    return tuple(unique.values())


def _activation_focus_fact(
    rule: Rule,
    activation: Activation,
) -> Fact | None:
    focused = next(
        (
            premise
            for premise in rule.premises
            if isinstance(premise, FactPremise) and premise.focused
        ),
        None,
    )
    if focused is not None:
        matcher = PatternMatcher()
        for fact in activation.premise_facts:
            if (
                focused.match(
                    fact,
                    activation.substitution,
                    matcher,
                )
                is not None
            ):
                return fact
    return activation.premise_facts[0] if activation.premise_facts else None


def _all_fact_premises(
    premises: tuple[Premise, ...],
) -> tuple[FactPremise, ...]:
    facts: list[FactPremise] = []
    for premise in premises:
        if isinstance(premise, FactPremise):
            facts.append(premise)
        elif isinstance(
            premise,
            (
                ExistsPremise,
                NotExistsPremise,
                CountPremise,
                UniquePremise,
                CollectPremise,
            ),
        ):
            facts.extend(_all_fact_premises(premise.premises))
    return tuple(facts)


def _dependency_tokens_for_premise(
    premise: FactPremise,
) -> frozenset[tuple[str, Term]]:
    if is_ground(premise.entity):
        return frozenset((("entity", premise.entity),))
    if isinstance(premise.entity, Triple):
        for name, value in (
            ("relation", premise.entity.relation),
            ("subject", premise.entity.subject),
            ("object", premise.entity.object),
        ):
            if is_ground(value):
                return frozenset(((name, value),))
    if is_ground(premise.status):
        return frozenset((("status", premise.status),))
    return frozenset()


def _dependency_tokens_for_fact(
    fact: Fact,
) -> frozenset[tuple[str, Term]]:
    tokens = {
        ("entity", fact.entity),
        ("status", fact.status),
    }
    if isinstance(fact.entity, Triple):
        tokens.update(
            (
                ("subject", fact.entity.subject),
                ("relation", fact.entity.relation),
                ("object", fact.entity.object),
            )
        )
    return frozenset(tokens)
