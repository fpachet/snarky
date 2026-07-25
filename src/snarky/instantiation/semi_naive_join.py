"""Delta-anchored joins for semi-naïve rule instantiation."""

from __future__ import annotations

from collections.abc import Sequence

from ..computed import ComputedPremise
from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import (
    BindPremise,
    CollectPremise,
    CombinationsPremise,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    UniquePremise,
)
from ..rules import Rule
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import Term
from .base import Activation, InstantiationMetrics
from .fact_index import FactIndex

type PremiseGroups = tuple[tuple[tuple[int, ...], int | None], ...]


def has_query_premise(rule: Rule) -> bool:
    """Return whether additions require a complete existential join."""

    return any(
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


def join_delta_variants(
    rule: Rule,
    index: FactIndex,
    added: tuple[Fact, ...],
    matcher: PatternMatcher,
    metrics: InstantiationMetrics,
) -> list[Activation]:
    """Enumerate unique joins containing at least one newly added fact."""

    fact_premises = tuple(
        position
        for position, premise in enumerate(rule.premises)
        if isinstance(premise, FactPremise)
    )
    premise_groups = _premise_groups(rule)
    delta_start = index.delta_start(added)
    unique: dict[
        tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
        Activation,
    ] = {}
    for anchor in fact_premises:
        for activation in _join_delta_variant(
            rule,
            index,
            premise_groups,
            anchor,
            delta_start,
            matcher,
            metrics,
        ):
            key = activation.substitution.key, activation.premise_facts
            unique.setdefault(key, activation)
    return sorted(unique.values(), key=index.activation_order)


def _join_delta_variant(
    rule: Rule,
    index: FactIndex,
    premise_groups: PremiseGroups,
    anchor: int,
    delta_start: int,
    matcher: PatternMatcher,
    metrics: InstantiationMetrics,
) -> list[Activation]:
    """Join from the delta premise, then restore textual support order."""

    activations: list[Activation] = []
    _extend_delta_variant(
        rule,
        index,
        premise_groups=premise_groups,
        group_index=0,
        remaining=premise_groups[0][0],
        anchor=anchor,
        delta_start=delta_start,
        substitution=EMPTY_SUBSTITUTION,
        supports=(),
        output=activations,
        matcher=matcher,
        metrics=metrics,
    )
    return activations


def _extend_delta_variant(
    rule: Rule,
    index: FactIndex,
    premise_groups: PremiseGroups,
    group_index: int,
    remaining: tuple[int, ...],
    anchor: int,
    delta_start: int,
    substitution: Substitution,
    supports: tuple[tuple[int, Fact], ...],
    output: list[Activation],
    matcher: PatternMatcher,
    metrics: InstantiationMetrics,
) -> None:
    if group_index == len(premise_groups):
        ordered_supports = tuple(
            fact for _, fact in sorted(supports, key=lambda item: item[0])
        )
        output.append(Activation(substitution, ordered_supports))
        return

    if not remaining:
        next_group = group_index + 1
        next_remaining = (
            premise_groups[next_group][0]
            if next_group < len(premise_groups)
            else ()
        )
        barrier_index = premise_groups[group_index][1]
        substitutions: tuple[Substitution, ...] = (substitution,)
        if barrier_index is not None:
            barrier = rule.premises[barrier_index]
            if isinstance(barrier, ComparisonPremise):
                substitutions = (
                    (substitution,)
                    if barrier.evaluate(substitution)
                    else ()
                )
            elif isinstance(barrier, (BindPremise, ComputedPremise)):
                bound = barrier.apply(substitution)
                substitutions = () if bound is None else (bound,)
            elif isinstance(barrier, CombinationsPremise):
                substitutions = tuple(
                    substitution.bind(barrier.target, value)
                    for value in barrier.values(substitution)
                )
            else:
                raise TypeError(f"unsupported delta barrier: {barrier!r}")
        for next_substitution in substitutions:
            _extend_delta_variant(
                rule,
                index,
                premise_groups,
                next_group,
                next_remaining,
                anchor,
                delta_start,
                next_substitution,
                supports,
                output,
                matcher,
                metrics,
            )
        return

    choices: list[tuple[int, int, Sequence[Fact], FactPremise]] = []
    group_positions = premise_groups[group_index][0]
    group_started = len(remaining) < len(group_positions)
    positions = (
        (anchor,) if anchor in remaining and not group_started else remaining
    )
    for premise_index in positions:
        premise = rule.premises[premise_index]
        if not isinstance(premise, FactPremise):
            raise TypeError(f"expected fact premise, got: {premise!r}")
        if premise_index == anchor:
            candidates = index.candidates_partitioned(
                premise,
                substitution,
                delta_start,
                new=True,
            )
        elif premise_index < anchor:
            candidates = index.candidates_partitioned(
                premise,
                substitution,
                delta_start,
                new=False,
            )
        else:
            candidates = index.candidates(premise, substitution)
        choices.append((len(candidates), premise_index, candidates, premise))
    _, premise_index, candidates, premise = min(
        choices,
        key=lambda choice: (choice[0], choice[1]),
    )
    next_remaining = tuple(item for item in remaining if item != premise_index)
    metrics.candidate_facts += len(candidates)
    for fact in candidates:
        metrics.match_attempts += 1
        matched = premise.match(fact, substitution, matcher)
        if matched is not None:
            _extend_delta_variant(
                rule,
                index,
                premise_groups,
                group_index,
                next_remaining,
                anchor,
                delta_start,
                matched,
                (*supports, (premise_index, fact)),
                output,
                matcher,
                metrics,
            )


def _premise_groups(rule: Rule) -> PremiseGroups:
    groups: list[tuple[tuple[int, ...], int | None]] = []
    facts: list[int] = []
    for position, premise in enumerate(rule.premises):
        if isinstance(premise, FactPremise):
            facts.append(position)
        elif isinstance(
            premise,
            (
                ComparisonPremise,
                BindPremise,
                CombinationsPremise,
                ComputedPremise,
            ),
        ):
            groups.append((tuple(facts), position))
            facts = []
        else:
            raise TypeError(f"unsupported premise: {premise!r}")
    groups.append((tuple(facts), None))
    return tuple(groups)
