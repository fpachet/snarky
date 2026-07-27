"""Specialized delta handlers for simple monotone event rules."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import cast

from ..facts import Fact
from ..rules import Rule
from ..substitutions import BindingFrame
from .base import Activation, InstantiationMetrics
from .compiled import (
    CompiledComparisonPremise,
    CompiledFactPremise,
    compile_rule,
)


@dataclass(frozen=True, slots=True)
class EventRulePlan:
    """One fact pattern followed only by bound Boolean comparisons."""

    fact: CompiledFactPremise
    comparisons: tuple[CompiledComparisonPremise, ...]


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
