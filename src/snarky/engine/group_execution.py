"""Rule-group execution modes, results, and session coordination."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import FactPremise
from ..rules import RuleGroup
from ..substitutions import EMPTY_SUBSTITUTION
from .agenda import (
    ActivationKey,
    _build_rule_dependency_index,
    _fact_delta,
    _RuleDependencyIndex,
)
from .conflict import AgendaSelection
from .events import InferenceEvent
from .provenance import Derivation, Provenance

if TYPE_CHECKING:
    from .forward import InferenceSession


class InferenceLimitError(RuntimeError):
    """Raised when a configured execution guard is exceeded."""


@dataclass(frozen=True, slots=True)
class EngineLimits:
    max_cycles: int = 1_000
    max_facts: int = 100_000

    def __post_init__(self) -> None:
        if self.max_cycles < 1 or self.max_facts < 1:
            raise ValueError("engine limits must be positive")


class GroupExecutionMode(StrEnum):
    """Ways to execute a rule group within a persistent session."""

    SATURATE = "saturate"
    ONE_CYCLE = "one_cycle"
    FIRST_CHANGE = "first_change"
    UNTIL = "until"


class GroupStopReason(StrEnum):
    """Reason why a rule-group invocation returned."""

    FIXED_POINT = "fixed_point"
    ONE_CYCLE = "one_cycle"
    FIRST_CHANGE = "first_change"
    CONDITION_MET = "condition_met"


class StopCondition(Protocol):
    """Condition evaluated against a persistent inference session."""

    def __call__(self, session: InferenceSession, /) -> bool: ...


@dataclass(frozen=True, slots=True)
class FactExists:
    """Stop when at least one fact matches a fact premise."""

    premise: FactPremise

    def __call__(self, session: InferenceSession, /) -> bool:
        matcher = PatternMatcher()
        return any(
            self.premise.match(fact, EMPTY_SUBSTITUTION, matcher) is not None
            for fact in session.facts
        )


@dataclass(frozen=True, slots=True)
class GroupRunResult:
    """Observable result of one rule-group invocation."""

    group_name: str
    mode: GroupExecutionMode
    facts: tuple[Fact, ...]
    added_facts: tuple[Fact, ...]
    derivations: tuple[Derivation, ...]
    cycles: int
    fired_activation_count: int
    stop_reason: GroupStopReason
    provenance: Provenance
    removed_facts: tuple[Fact, ...] = ()
    events: tuple[InferenceEvent, ...] = ()
    agenda_selections: tuple[AgendaSelection, ...] = ()

    @property
    def changed(self) -> bool:
        """Return whether this invocation mutated the working memory."""

        return bool(self.events)

    @property
    def mutation_count(self) -> int:
        """Return the number of effective additions and removals."""

        return len(self.events)


def _run_group(
    session: InferenceSession,
    group: RuleGroup,
    mode: GroupExecutionMode,
    until: StopCondition | None,
    materialize_result: bool,
) -> GroupRunResult | None:
    """Execute *group* against *session* without owning session state."""

    if mode is GroupExecutionMode.UNTIL and until is None:
        raise ValueError("UNTIL mode requires a stop condition")
    if mode is not GroupExecutionMode.UNTIL and until is not None:
        raise ValueError("a stop condition is only valid in UNTIL mode")
    registered = session._groups.get(group.name)
    if registered is None:
        session._groups[group.name] = group
        session._register_negative_refraction_plans(group)
    elif registered != group:
        raise ValueError(
            f"rule group {group.name!r} was already registered "
            "with a different definition"
        )

    start_derivation_count = len(session._derivations)
    start_event_count = len(session._events)
    start_agenda_count = len(session._agenda_selections)
    start_fired_count = session._fired_activation_total
    if until is not None and until(session):
        return session._group_result(
            group,
            mode,
            start_derivation_count,
            start_event_count,
            start_agenda_count,
            start_fired_count,
            cycles=0,
            stop_reason=GroupStopReason.CONDITION_MET,
            materialize_result=materialize_result,
        )

    if session.conflict_strategy is not None:
        return _run_group_with_conflict_resolution(
            session,
            group,
            mode,
            until,
            start_derivation_count,
            start_event_count,
            start_agenda_count,
            start_fired_count,
            materialize_result,
        )

    dependencies = _build_rule_dependency_index(group)
    pending = _initial_pending_rules(session, group, dependencies)
    if not pending:
        session._cycles += 1
        session.agenda_metrics.rule_reuses += len(group.rules)
        return session._group_result(
            group,
            mode,
            start_derivation_count,
            start_event_count,
            start_agenda_count,
            start_fired_count,
            cycles=1,
            stop_reason=(
                GroupStopReason.ONE_CYCLE
                if mode is GroupExecutionMode.ONE_CYCLE
                else GroupStopReason.FIXED_POINT
            ),
            materialize_result=materialize_result,
        )

    for local_cycle in range(1, session.limits.max_cycles + 1):
        session._cycles += 1
        next_pending: set[int] = set()
        evaluated = 0
        mutations_this_cycle = 0
        for rule_index, rule in enumerate(group.rules):
            if rule_index not in pending:
                continue
            evaluated += 1
            event_count_before_rule = len(session._events)
            state_key = (group.name, rule.name)
            previous_count = session._previous_event_counts.get(state_key)
            changes = (
                None
                if previous_count is None
                else _fact_delta(
                    tuple(session._events[previous_count:]),
                    revision=len(session._events),
                )
            )
            force_full = state_key in session._force_full_evaluation
            if force_full and changes is not None:
                synchronize = getattr(
                    session.strategy,
                    "synchronize",
                    None,
                )
                if synchronize is not None:
                    synchronize(session._instantiation_facts(), changes)
            delta = (
                None
                if previous_count is None or force_full
                else changes
            )
            session._force_full_evaluation.discard(state_key)
            session._previous_event_counts[state_key] = len(session._events)
            for activation in session.strategy.instantiate(
                rule,
                session._instantiation_facts(),
                delta,
            ):
                if any(
                    fact not in session._store
                    for fact in activation.premise_facts
                ):
                    continue
                key = ActivationKey(
                    group.name,
                    rule.name,
                    activation.substitution.key,
                )
                if key in session._fired:
                    continue
                session._fired.add(key)
                session._fired_supports[key] = activation.premise_facts
                session._fired_activation_total += 1
                outcome = session._fire_activation(
                    group,
                    rule,
                    activation.substitution,
                    activation.premise_facts,
                )
                mutations_this_cycle += outcome.mutation_count

                if until is not None and until(session):
                    session.agenda_metrics.rule_recomputations += evaluated
                    return session._group_result(
                        group,
                        mode,
                        start_derivation_count,
                        start_event_count,
                        start_agenda_count,
                        start_fired_count,
                        cycles=local_cycle,
                        stop_reason=GroupStopReason.CONDITION_MET,
                        materialize_result=materialize_result,
                    )
                if (
                    mode is GroupExecutionMode.FIRST_CHANGE
                    and outcome.mutation_count
                ):
                    session.agenda_metrics.rule_recomputations += evaluated
                    return session._group_result(
                        group,
                        mode,
                        start_derivation_count,
                        start_event_count,
                        start_agenda_count,
                        start_fired_count,
                        cycles=local_cycle,
                        stop_reason=GroupStopReason.FIRST_CHANGE,
                        materialize_result=materialize_result,
                    )

            changed_events = tuple(
                session._events[event_count_before_rule:]
            )
            for affected_index in dependencies.affected(changed_events):
                if affected_index > rule_index:
                    pending.add(affected_index)
                else:
                    next_pending.add(affected_index)

        session.agenda_metrics.rule_recomputations += evaluated
        session.agenda_metrics.rule_reuses += len(group.rules) - evaluated
        _advance_unaffected_rules(
            session,
            group,
            next_pending,
            len(session._events),
        )
        if mode is GroupExecutionMode.ONE_CYCLE:
            return session._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=local_cycle,
                stop_reason=GroupStopReason.ONE_CYCLE,
                materialize_result=materialize_result,
            )
        if not next_pending:
            if mutations_this_cycle:
                if local_cycle == session.limits.max_cycles:
                    break
                session._cycles += 1
                session.agenda_metrics.rule_reuses += len(group.rules)
                local_cycle += 1
            return session._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=local_cycle,
                stop_reason=GroupStopReason.FIXED_POINT,
                materialize_result=materialize_result,
            )
        pending = next_pending

    raise InferenceLimitError(
        f"rule group {group.name!r} did not stop after "
        f"{session.limits.max_cycles} cycles"
    )


def _initial_pending_rules(
    session: InferenceSession,
    group: RuleGroup,
    dependencies: _RuleDependencyIndex,
) -> set[int]:
    """Select rules invalidated since their previous ordered evaluation."""

    revision = len(session._events)
    oldest_revision = revision
    pending: set[int] = set()
    for rule_index, rule in enumerate(group.rules):
        state_key = (group.name, rule.name)
        previous = session._previous_event_counts.get(state_key)
        if previous is None or state_key in session._force_full_evaluation:
            pending.add(rule_index)
        if previous is not None:
            oldest_revision = min(oldest_revision, previous)
    if oldest_revision < revision:
        pending.update(
            dependencies.affected(
                tuple(session._events[oldest_revision:])
            )
        )
    _advance_unaffected_rules(session, group, pending, revision)
    return pending


def _advance_unaffected_rules(
    session: InferenceSession,
    group: RuleGroup,
    pending: set[int],
    revision: int,
) -> None:
    """Mark irrelevant journal events consumed without instantiating rules."""

    for rule_index, rule in enumerate(group.rules):
        if rule_index not in pending:
            session._previous_event_counts[(group.name, rule.name)] = revision


def _run_group_with_conflict_resolution(
    session: InferenceSession,
    group: RuleGroup,
    mode: GroupExecutionMode,
    until: StopCondition | None,
    start_derivation_count: int,
    start_event_count: int,
    start_agenda_count: int,
    start_fired_count: int,
    materialize_result: bool,
) -> GroupRunResult | None:
    """Resolve one complete conflict set before every activation."""

    assert session.conflict_strategy is not None
    local_cycle = 0
    while local_cycle < session.limits.max_cycles:
        candidates = session._agenda_candidates(group)
        if not candidates:
            return session._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=local_cycle,
                stop_reason=GroupStopReason.FIXED_POINT,
                materialize_result=materialize_result,
            )

        selected = session.conflict_strategy.select(candidates)
        local_cycle += 1
        session._cycles += 1
        key = ActivationKey(
            group.name,
            selected.rule.name,
            selected.activation.substitution.key,
        )
        session._fired.add(key)
        session._fired_supports[key] = selected.activation.premise_facts
        session._fired_activation_total += 1
        session._agenda_selections.append(
            AgendaSelection(
                sequence=len(session._agenda_selections) + 1,
                strategy_name=session.conflict_strategy.name,
                rule_group=group.name,
                rule_name=selected.rule.name,
                substitution=selected.activation.substitution,
                premise_facts=selected.activation.premise_facts,
                focus_fact=selected.focus_fact,
                focus_time_tag=selected.focus_time_tag,
                lexicographic_time_tags=(
                    selected.lexicographic_time_tags
                ),
                cycle=session._cycles,
            )
        )
        outcome = session._fire_activation(
            group,
            selected.rule,
            selected.activation.substitution,
            selected.activation.premise_facts,
        )

        if until is not None and until(session):
            return session._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=local_cycle,
                stop_reason=GroupStopReason.CONDITION_MET,
                materialize_result=materialize_result,
            )
        if (
            mode is GroupExecutionMode.FIRST_CHANGE
            and outcome.mutation_count
        ):
            return session._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=local_cycle,
                stop_reason=GroupStopReason.FIRST_CHANGE,
                materialize_result=materialize_result,
            )
        if mode is GroupExecutionMode.ONE_CYCLE:
            return session._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=local_cycle,
                stop_reason=GroupStopReason.ONE_CYCLE,
                materialize_result=materialize_result,
            )

    raise InferenceLimitError(
        f"rule group {group.name!r} did not stop after "
        f"{session.limits.max_cycles} agenda selections"
    )
