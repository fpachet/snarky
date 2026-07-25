"""Incremental agenda memory and dependency helpers."""

from __future__ import annotations

from collections.abc import Sequence
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
from .conflict import AgendaCandidate, AgendaMetrics
from .events import FactMutationKind, InferenceEvent


@dataclass(frozen=True, slots=True)
class ActivationKey:
    rule_group: str
    rule_name: str
    substitution: tuple[tuple[str, Term], ...]


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


def _evaluate_agenda(
    group: RuleGroup,
    facts_snapshot: tuple[Fact, ...],
    events: Sequence[InferenceEvent],
    memory: _AgendaMemory | None,
    strategy: InstantiationStrategy,
    store: NaiveFactStore,
    force_full_evaluation: set[tuple[str, str]],
    fired: set[ActivationKey],
    fact_time_tags: dict[Fact, int],
    metrics: AgendaMetrics,
) -> tuple[_AgendaMemory, tuple[AgendaCandidate, ...]]:
    """Evaluate and materialize the current conflict set for *group*."""

    if memory is not None and memory.group != group:
        raise ValueError(
            f"agenda group {group.name!r} has a different definition"
        )
    if memory is None:
        dependencies = _build_rule_dependency_index(group)
        activation_rows = tuple(
            strategy.instantiate(rule, facts_snapshot, None)
            for rule in group.rules
        )
        metrics.rebuilds += 1
        metrics.rule_recomputations += len(group.rules)
    else:
        changed_events = tuple(events[memory.revision :])
        dirty = memory.dependencies.affected(changed_events)
        activation_rows_list = list(memory.activations)
        if dirty:
            delta = _fact_delta(
                changed_events,
                facts_snapshot,
                revision=len(events),
            )
            for rule_index in dirty:
                rule = group.rules[rule_index]
                state_key = (group.name, rule.name)
                force_full = (
                    not delta.changed
                    or state_key in force_full_evaluation
                )
                refreshed = strategy.instantiate(
                    rule,
                    facts_snapshot,
                    None if force_full else delta,
                )
                force_full_evaluation.discard(state_key)
                activation_rows_list[rule_index] = (
                    refreshed
                    if force_full
                    else _merge_agenda_activations(
                        rule,
                        activation_rows_list[rule_index],
                        refreshed,
                        delta,
                        strategy,
                        store,
                    )
                )
            metrics.rule_recomputations += len(dirty)
        metrics.rule_reuses += len(group.rules) - len(dirty)
        activation_rows = tuple(activation_rows_list)
        dependencies = memory.dependencies
    updated_memory = _AgendaMemory(
        group,
        activation_rows,
        len(events),
        dependencies,
    )
    candidates: list[AgendaCandidate] = []
    candidate_order = 0
    for rule_order, (rule, activations) in enumerate(
        zip(group.rules, activation_rows, strict=True)
    ):
        for activation in activations:
            if any(
                fact not in store
                for fact in activation.premise_facts
            ):
                continue
            key = ActivationKey(
                group.name,
                rule.name,
                activation.substitution.key,
            )
            if key in fired:
                continue
            time_tags = tuple(
                fact_time_tags.get(fact, 0)
                for fact in activation.premise_facts
            )
            focus_fact = _activation_focus_fact(rule, activation)
            candidates.append(
                AgendaCandidate(
                    rule=rule,
                    activation=activation,
                    rule_order=rule_order,
                    candidate_order=candidate_order,
                    focus_fact=focus_fact,
                    focus_time_tag=(
                        fact_time_tags.get(focus_fact, 0)
                        if focus_fact is not None
                        else 0
                    ),
                    lexicographic_time_tags=tuple(
                        sorted(time_tags, reverse=True)
                    ),
                )
            )
            candidate_order += 1
    return updated_memory, tuple(candidates)


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


def _fact_delta(
    events: tuple[InferenceEvent, ...],
    current_facts: tuple[Fact, ...],
    *,
    revision: int,
) -> FactDelta:
    """Reduce a mutation journal slice to its net per-rule fact delta."""

    del current_facts
    initial_presence: dict[Fact, bool] = {}
    final_presence: dict[Fact, bool] = {}
    removed_then_added: set[Fact] = set()
    last_add_order: dict[Fact, int] = {}
    for order, event in enumerate(events):
        if event.fact not in initial_presence:
            initial_presence[event.fact] = (
                event.kind is FactMutationKind.REMOVE
            )
        elif (
            event.kind is FactMutationKind.ADD
            and initial_presence[event.fact]
            and not final_presence[event.fact]
        ):
            removed_then_added.add(event.fact)
        added = event.kind is FactMutationKind.ADD
        final_presence[event.fact] = added
        if added:
            last_add_order[event.fact] = order
    added_set = {
        fact
        for fact, present in final_presence.items()
        if present and (
            not initial_presence[fact] or fact in removed_then_added
        )
    }
    removed = frozenset(
        fact
        for fact, present in final_presence.items()
        if (
            (not present and initial_presence[fact])
            or fact in removed_then_added
        )
    )
    return FactDelta(
        added=tuple(
            sorted(
                added_set,
                key=last_add_order.__getitem__,
            )
        ),
        removed=removed,
        revision=revision,
    )
