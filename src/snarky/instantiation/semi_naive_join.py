"""Delta-anchored joins for semi-naïve rule instantiation."""

from __future__ import annotations

from collections.abc import Sequence

from ..computed import ComputedPremise
from ..facts import Fact
from ..premises import (
    BindPremise,
    CollectPremise,
    CountPremise,
    ExistsPremise,
    NotExistsPremise,
    UniquePremise,
)
from ..rules import Rule
from ..substitutions import BindingFrame
from ..terms import Term, is_ground
from .base import Activation, InstantiationMetrics
from .compiled import (
    CompiledBindPremise,
    CompiledBlock,
    CompiledCombinationsPremise,
    CompiledComparisonPremise,
    CompiledFactPremise,
    compile_rule,
)
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
    metrics: InstantiationMetrics,
) -> list[Activation]:
    """Enumerate unique joins containing at least one newly added fact."""

    block = compile_rule(rule).block
    fact_premises = tuple(
        position
        for position, premise in enumerate(block.premises)
        if isinstance(premise, CompiledFactPremise)
    )
    premise_groups = _premise_groups(block)
    delta_start = index.delta_start(added)
    unique: dict[
        tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
        Activation,
    ] = {}
    for anchor in fact_premises:
        for activation in _join_delta_variant(
            block,
            index,
            premise_groups,
            anchor,
            delta_start,
            metrics,
        ):
            key = activation.substitution.key, activation.premise_facts
            unique.setdefault(key, activation)
    return sorted(unique.values(), key=index.activation_order)


def _join_delta_variant(
    block: CompiledBlock,
    index: FactIndex,
    premise_groups: PremiseGroups,
    anchor: int,
    delta_start: int,
    metrics: InstantiationMetrics,
) -> list[Activation]:
    """Join from the delta premise, then restore textual support order."""

    activations: list[Activation] = []
    _extend_delta_variant(
        block,
        index,
        premise_groups=premise_groups,
        group_index=0,
        remaining=premise_groups[0][0],
        anchor=anchor,
        delta_start=delta_start,
        frame=BindingFrame(),
        supports=(),
        output=activations,
        metrics=metrics,
    )
    return activations


def _extend_delta_variant(
    block: CompiledBlock,
    index: FactIndex,
    premise_groups: PremiseGroups,
    group_index: int,
    remaining: tuple[int, ...],
    anchor: int,
    delta_start: int,
    frame: BindingFrame,
    supports: tuple[tuple[int, Fact], ...],
    output: list[Activation],
    metrics: InstantiationMetrics,
) -> None:
    if group_index == len(premise_groups):
        ordered_supports = tuple(
            fact for _, fact in sorted(supports, key=lambda item: item[0])
        )
        output.append(Activation(frame.freeze(), ordered_supports))
        return

    if not remaining:
        next_group = group_index + 1
        next_remaining = (
            premise_groups[next_group][0]
            if next_group < len(premise_groups)
            else ()
        )
        barrier_index = premise_groups[group_index][1]
        if barrier_index is None:
            _extend_delta_variant(
                block,
                index,
                premise_groups,
                next_group,
                next_remaining,
                anchor,
                delta_start,
                frame,
                supports,
                output,
                metrics,
            )
            return
        barrier = block.premises[barrier_index]
        if isinstance(barrier, CompiledComparisonPremise):
            if barrier.source.evaluate(frame):
                _extend_delta_variant(
                    block,
                    index,
                    premise_groups,
                    next_group,
                    next_remaining,
                    anchor,
                    delta_start,
                    frame,
                    supports,
                    output,
                    metrics,
                )
            return
        if isinstance(barrier, CompiledBindPremise):
            checkpoint = frame.checkpoint()
            if _apply_compiled_binding(barrier.source, frame):
                _extend_delta_variant(
                    block,
                    index,
                    premise_groups,
                    next_group,
                    next_remaining,
                    anchor,
                    delta_start,
                    frame,
                    supports,
                    output,
                    metrics,
                )
            frame.rollback(checkpoint)
            return
        if isinstance(barrier, CompiledCombinationsPremise):
            for value in barrier.source.values(frame):
                checkpoint = frame.checkpoint()
                if frame.bind_ground(barrier.source.target, value):
                    _extend_delta_variant(
                        block,
                        index,
                        premise_groups,
                        next_group,
                        next_remaining,
                        anchor,
                        delta_start,
                        frame,
                        supports,
                        output,
                        metrics,
                    )
                frame.rollback(checkpoint)
            return
        raise TypeError(f"unsupported delta barrier: {barrier!r}")

    choices: list[
        tuple[int, int, Sequence[Fact], CompiledFactPremise]
    ] = []
    group_positions = premise_groups[group_index][0]
    group_started = len(remaining) < len(group_positions)
    positions = (
        (anchor,) if anchor in remaining and not group_started else remaining
    )
    for premise_index in positions:
        premise = block.premises[premise_index]
        if not isinstance(premise, CompiledFactPremise):
            raise TypeError(f"expected fact premise, got: {premise!r}")
        if premise_index == anchor:
            candidates = index.candidates_compiled_partitioned(
                premise,
                frame,
                delta_start,
                new=True,
            )
        elif premise_index < anchor:
            candidates = index.candidates_compiled_partitioned(
                premise,
                frame,
                delta_start,
                new=False,
            )
        else:
            candidates = index.candidates_compiled(premise, frame)
        choices.append((len(candidates), premise_index, candidates, premise))
    _, premise_index, candidates, premise = min(
        choices,
        key=lambda choice: (choice[0], choice[1]),
    )
    next_remaining = tuple(item for item in remaining if item != premise_index)
    metrics.candidate_facts += len(candidates)
    for fact in candidates:
        metrics.match_attempts += 1
        checkpoint = frame.checkpoint()
        if premise.match(fact.entity, fact.status, frame):
            _extend_delta_variant(
                block,
                index,
                premise_groups,
                group_index,
                next_remaining,
                anchor,
                delta_start,
                frame,
                (*supports, (premise_index, fact)),
                output,
                metrics,
            )
        frame.rollback(checkpoint)


def _premise_groups(block: CompiledBlock) -> PremiseGroups:
    groups: list[tuple[tuple[int, ...], int | None]] = []
    facts: list[int] = []
    for position, premise in enumerate(block.premises):
        if isinstance(premise, CompiledFactPremise):
            facts.append(position)
        elif isinstance(
            premise,
            (
                CompiledComparisonPremise,
                CompiledBindPremise,
                CompiledCombinationsPremise,
            ),
        ):
            groups.append((tuple(facts), position))
            facts = []
        else:
            raise TypeError(f"unsupported premise: {premise!r}")
    groups.append((tuple(facts), None))
    return tuple(groups)


def _apply_compiled_binding(
    premise: BindPremise | ComputedPremise,
    frame: BindingFrame,
) -> bool:
    if isinstance(premise, BindPremise):
        bound_value = frame.apply(premise.value)
        return is_ground(bound_value) and frame.bind_ground(
            premise.target,
            bound_value,
        )
    accepted, computed_value = premise.resolve(frame)
    if not accepted:
        return False
    if premise.target is None:
        return True
    assert computed_value is not None
    return frame.bind_ground(premise.target, computed_value)
