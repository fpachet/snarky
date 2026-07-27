"""Specialized delta handlers for monotone event rules."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import cast

from ..facts import Fact
from ..premises import variables_in_comparison_operand
from ..rules import Rule
from ..substitutions import BindingFrame
from ..terms import Term, Triple, Variable, is_ground, variables_in
from .base import Activation, InstantiationMetrics
from .compiled import (
    CompiledComparisonPremise,
    CompiledFactPremise,
    compile_rule,
)
from .fact_index import FactIndex


@dataclass(frozen=True, slots=True)
class EventRulePlan:
    """One fact pattern followed only by bound Boolean comparisons."""

    fact: CompiledFactPremise
    comparisons: tuple[CompiledComparisonPremise, ...]


@dataclass(frozen=True, slots=True)
class FactorizedEventRulePlan:
    """Positive conjunction whose comparisons stay textually bound."""

    facts: tuple[CompiledFactPremise, ...]
    anchor_filters: tuple[_EventAnchorFilter, ...]
    comparisons: tuple[CompiledComparisonPremise, ...]


@dataclass(frozen=True, slots=True)
class _EventAnchorFilter:
    entity: Term | None
    status: Term | None
    triple_parts: tuple[Term | None, Term | None, Term | None] | None


@cache
def compile_event_rule(rule: Rule) -> EventRulePlan | None:
    """Return a direct event plan for the conservative supported subset."""

    premises = compile_rule(rule).block.premises
    if not premises or not isinstance(premises[0], CompiledFactPremise):
        return None
    comparisons = premises[1:]
    if not all(
        isinstance(premise, CompiledComparisonPremise)
        for premise in comparisons
    ):
        return None
    return EventRulePlan(
        premises[0],
        cast(tuple[CompiledComparisonPremise, ...], comparisons),
    )


@cache
def compile_factorized_event_rule(
    rule: Rule,
) -> FactorizedEventRulePlan | None:
    """Compile a safe delta-anchored multi-fact event plan.

    Fact premises may be reordered because they are positive conjunctions.
    Comparisons remain safe only when their operands were already bound at
    their original textual position. This excludes rules whose established
    semantics deliberately evaluate an unbound comparison as false.
    """

    premises = compile_rule(rule).block.premises
    if not all(
        isinstance(
            premise,
            (CompiledFactPremise, CompiledComparisonPremise),
        )
        for premise in premises
    ):
        return None
    facts: list[CompiledFactPremise] = []
    comparisons: list[CompiledComparisonPremise] = []
    bound: set[Variable] = set()
    seen_comparison = False
    fact_after_comparison = False
    for premise in premises:
        if isinstance(premise, CompiledFactPremise):
            if premise.source.focused:
                return None
            fact_after_comparison = fact_after_comparison or seen_comparison
            facts.append(premise)
            bound.update(variables_in(premise.source.entity))
            bound.update(variables_in(premise.source.status))
            continue
        if not isinstance(premise, CompiledComparisonPremise):
            return None
        required = variables_in_comparison_operand(
            premise.source.left
        ) | variables_in_comparison_operand(premise.source.right)
        if not required.issubset(bound):
            return None
        comparisons.append(premise)
        seen_comparison = True
    if (
        len(facts) < 2
        or not comparisons
        or not fact_after_comparison
    ):
        return None
    return FactorizedEventRulePlan(
        tuple(facts),
        tuple(_compile_event_anchor_filter(fact) for fact in facts),
        tuple(comparisons),
    )


def instantiate_event_rule(
    plan: EventRulePlan,
    candidates: Sequence[Fact],
    metrics: InstantiationMetrics,
) -> list[Activation]:
    """Match candidate facts directly without constructing a generic join."""

    activations: list[Activation] = []
    metrics.event_rule_evaluations += 1
    metrics.event_rule_candidates += len(candidates)
    metrics.candidate_facts += len(candidates)
    for fact in candidates:
        metrics.match_attempts += 1
        frame = BindingFrame()
        if not plan.fact.match(fact.entity, fact.status, frame):
            continue
        if not all(
            comparison.source.evaluate(frame)
            for comparison in plan.comparisons
        ):
            continue
        activations.append(Activation(frame.freeze(), (fact,)))
    return activations


def instantiate_factorized_event_rule(
    plan: FactorizedEventRulePlan,
    index: FactIndex,
    candidates: Sequence[Fact],
    metrics: InstantiationMetrics,
) -> tuple[Activation, ...]:
    """Join outward from added facts without materializing prefix products."""

    metrics.factorized_event_evaluations += 1
    metrics.factorized_event_candidates += len(candidates)
    unique: dict[
        tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
        Activation,
    ] = {}
    for candidate in candidates:
        for anchor, premise in enumerate(plan.facts):
            if not _matches_fixed_event_fields(
                plan.anchor_filters[anchor],
                candidate,
            ):
                continue
            metrics.candidate_facts += 1
            metrics.match_attempts += 1
            frame = BindingFrame()
            if not premise.match(
                candidate.entity,
                candidate.status,
                frame,
            ):
                continue
            supports: list[Fact | None] = [None] * len(plan.facts)
            supports[anchor] = candidate
            _extend_factorized_event_rule(
                plan,
                index,
                frame,
                tuple(
                    position
                    for position in range(len(plan.facts))
                    if position != anchor
                ),
                supports,
                unique,
                metrics,
            )
    return tuple(sorted(unique.values(), key=index.activation_order))


def _extend_factorized_event_rule(
    plan: FactorizedEventRulePlan,
    index: FactIndex,
    frame: BindingFrame,
    remaining: tuple[int, ...],
    supports: list[Fact | None],
    output: dict[
        tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
        Activation,
    ],
    metrics: InstantiationMetrics,
) -> None:
    if not remaining:
        if not all(
            comparison.source.evaluate(frame)
            for comparison in plan.comparisons
        ):
            return
        ordered_supports = tuple(
            fact for fact in supports if fact is not None
        )
        substitution = frame.freeze()
        activation = Activation(substitution, ordered_supports)
        output.setdefault(
            (substitution.key, ordered_supports),
            activation,
        )
        return

    position = remaining[0]
    selected = index.candidates_compiled(
        plan.facts[position],
        frame,
    )
    premise = plan.facts[position]
    next_remaining = remaining[1:]
    metrics.factorized_event_lookups += 1
    metrics.candidate_facts += len(selected)
    for fact in selected:
        metrics.match_attempts += 1
        checkpoint = frame.checkpoint()
        if premise.match(fact.entity, fact.status, frame):
            supports[position] = fact
            _extend_factorized_event_rule(
                plan,
                index,
                frame,
                next_remaining,
                supports,
                output,
                metrics,
            )
            supports[position] = None
        frame.rollback(checkpoint)


def _matches_fixed_event_fields(
    anchor_filter: _EventAnchorFilter,
    fact: Fact,
) -> bool:
    """Reject anchors using only constant top-level pattern fields."""

    if (
        anchor_filter.status is not None
        and anchor_filter.status != fact.status
    ):
        return False
    if anchor_filter.entity is not None:
        return anchor_filter.entity == fact.entity
    if anchor_filter.triple_parts is None:
        return True
    if not isinstance(fact.entity, Triple):
        return False
    return all(
        pattern is None or pattern == value
        for pattern, value in zip(
            anchor_filter.triple_parts,
            (
                fact.entity.subject,
                fact.entity.relation,
                fact.entity.object,
            ),
            strict=True,
        )
    )


def _compile_event_anchor_filter(
    premise: CompiledFactPremise,
) -> _EventAnchorFilter:
    source = premise.source
    entity = source.entity if is_ground(source.entity) else None
    status = source.status if is_ground(source.status) else None
    triple_parts = (
        (
            (
                source.entity.subject
                if is_ground(source.entity.subject)
                else None
            ),
            (
                source.entity.relation
                if is_ground(source.entity.relation)
                else None
            ),
            (
                source.entity.object
                if is_ground(source.entity.object)
                else None
            ),
        )
        if entity is None and isinstance(source.entity, Triple)
        else None
    )
    return _EventAnchorFilter(
        entity=entity,
        status=status,
        triple_parts=triple_parts,
    )
