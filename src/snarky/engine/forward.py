"""Deterministic forward chaining, persistent sessions, and rule groups."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import Protocol

from ..actions import (
    Action,
    AddFact,
    Choice,
    ForEach,
    Fresh,
    Let,
    RemoveFact,
)
from ..facts import Fact
from ..instantiation import (
    IndexedInstantiationStrategy,
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
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import (
    Atom,
    FiniteSequence,
    FiniteSet,
    Term,
    Triple,
    Variable,
)
from .agenda import (
    ActivationKey,
    _AgendaMemory,
    _evaluate_agenda,
    _fact_delta,
)
from .conflict import (
    AgendaCandidate,
    AgendaMetrics,
    AgendaSelection,
    ConflictResolutionStrategy,
)
from .events import FactMutationKind, InferenceEvent
from .provenance import Derivation, Provenance
from .session_state import (
    SessionCheckpoint as SessionCheckpoint,
)
from .session_state import (
    _TimeTagMutation,
)


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
class RunResult:
    facts: tuple[Fact, ...]
    derived_facts: tuple[Fact, ...]
    derivations: tuple[Derivation, ...]
    cycles: int
    fired_activation_count: int
    provenance: Provenance
    events: tuple[InferenceEvent, ...] = ()
    agenda_selections: tuple[AgendaSelection, ...] = ()


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


@dataclass(frozen=True, slots=True)
class _ActivationOutcome:
    added_facts: tuple[Fact, ...]
    removed_facts: tuple[Fact, ...]

    @property
    def mutation_count(self) -> int:
        return len(self.added_facts) + len(self.removed_facts)


@dataclass(frozen=True, slots=True)
class _NegativeRefractionPlan:
    group_name: str
    rule: Rule
    simple_dependencies: tuple[FactPremise, ...]
    complex_dependencies: tuple[FactPremise, ...]


class InferenceSession:
    """Persistent working memory shared by successive rule-group invocations."""

    def __init__(
        self,
        initial_facts: tuple[Fact, ...],
        strategy: InstantiationStrategy | None = None,
        limits: EngineLimits | None = None,
        conflict_strategy: ConflictResolutionStrategy | None = None,
        *,
        truth_maintenance: bool = False,
    ) -> None:
        self.strategy = (
            strategy
            if strategy is not None
            else SemiNaiveInstantiationStrategy()
        )
        self.limits = limits or EngineLimits()
        self.conflict_strategy = conflict_strategy
        self.truth_maintenance = truth_maintenance
        self._store = NaiveFactStore(initial_facts)
        self._provenance = Provenance(self._store.facts)
        self._initial_facts = frozenset(self._store.facts)
        self._assumed_facts: set[Fact] = set()
        self._fired: set[ActivationKey] = set()
        self._fired_supports: dict[ActivationKey, tuple[Fact, ...]] = {}
        self._fired_activation_total = 0
        self._derivations: list[Derivation] = []
        self._events: list[InferenceEvent] = []
        self._agenda_selections: list[AgendaSelection] = []
        self.agenda_metrics = AgendaMetrics()
        self._agenda_memories: dict[str, _AgendaMemory] = {}
        self._previous_event_counts: dict[tuple[str, str], int] = {}
        self._force_full_evaluation: set[tuple[str, str]] = set()
        self._groups: dict[str, RuleGroup] = {}
        self._negative_refraction_plans: list[_NegativeRefractionPlan] = []
        self._cycles = 0
        self._fresh_counters: dict[str, int] = {}
        self._fact_time_tags = {
            fact: time_tag
            for time_tag, fact in enumerate(self._store.facts, start=1)
        }
        self._next_time_tag = len(self._fact_time_tags)
        self._reserved_atom_names = {
            name
            for fact in self._store.facts
            for name in (
                *_atom_names_in(fact.entity),
                *_atom_names_in(fact.status),
            )
        }
        self._time_tag_trail: list[_TimeTagMutation] = []
        self._checkpoint_tokens: list[int] = []
        self._next_checkpoint_token = 0

    @property
    def facts(self) -> tuple[Fact, ...]:
        """Return the current insertion-ordered fact snapshot."""

        return self._store.facts

    @property
    def provenance(self) -> Provenance:
        """Return cumulative provenance for the session."""

        return self._provenance

    @property
    def events(self) -> tuple[InferenceEvent, ...]:
        """Return the cumulative chronological mutation journal."""

        return tuple(self._events)

    @property
    def agenda_selections(self) -> tuple[AgendaSelection, ...]:
        """Return cumulative conflict-set choices for agenda-driven sessions."""

        return tuple(self._agenda_selections)

    def inspect_agenda(
        self,
        group: RuleGroup,
    ) -> tuple[AgendaCandidate, ...]:
        """Return the current unfired conflict set without selecting from it."""

        return self._agenda_candidates(group)

    def assume(self, *facts: Fact, label: str = "hypothesis") -> tuple[Fact, ...]:
        """Assert branch-local depth-zero facts for explicit search clients."""

        added: list[Fact] = []
        for fact in facts:
            self._provenance.assume(fact)
            self._assumed_facts.add(fact)
            if not self._store.add(fact):
                continue
            self._reserve_fact_atoms(fact)
            self._next_time_tag += 1
            self._set_fact_time_tag(fact, self._next_time_tag)
            added.append(fact)
            self._events.append(
                InferenceEvent(
                    sequence=len(self._events) + 1,
                    kind=FactMutationKind.ADD,
                    fact=fact,
                    rule_name=f"<{label}>",
                    rule_group="<assumptions>",
                    substitution=EMPTY_SUBSTITUTION,
                    premises=(),
                    cycle=self._cycles,
                )
            )
        if len(self._store) > self.limits.max_facts:
            raise InferenceLimitError(
                f"maximum fact count ({self.limits.max_facts}) exceeded"
            )
        if added and self._negative_refraction_plans:
            self._reconcile_negative_refraction(tuple(added))
        return tuple(added)

    def retract(
        self,
        *facts: Fact,
        label: str = "external",
    ) -> tuple[Fact, ...]:
        """Retract facts and optionally cascade unsupported conclusions."""

        removed: list[Fact] = []
        for fact in facts:
            self._assumed_facts.discard(fact)
            if not self._store.remove(fact):
                continue
            self._set_fact_time_tag(fact, None)
            removed.append(fact)
            self._record_external_removal(fact, label)
        if self.truth_maintenance and removed:
            removed.extend(self._cascade_unsupported())
        absent = frozenset(removed)
        if absent:
            self.strategy.invalidate(absent)
            self._expire_removed_supports(absent)
        return tuple(removed)

    def snapshot(self) -> RunResult:
        """Return the cumulative state using the historical result shape."""

        facts = self._store.facts
        return RunResult(
            facts=facts,
            derived_facts=tuple(
                fact for fact in facts if fact not in self._initial_facts
            ),
            derivations=tuple(self._derivations),
            cycles=self._cycles,
            fired_activation_count=self._fired_activation_total,
            provenance=self._provenance,
            events=tuple(self._events),
            agenda_selections=tuple(self._agenda_selections),
        )

    def fork(
        self,
        *,
        strategy: InstantiationStrategy | None = None,
    ) -> InferenceSession:
        """Return an isolated continuation of the current inference state.

        The branch inherits facts, history, provenance and refraction, but all
        subsequent mutations remain local. This is a simulation primitive,
        not an automatic search or backtracking policy.
        """

        branch = object.__new__(InferenceSession)
        branch.strategy = (
            strategy if strategy is not None else deepcopy(self.strategy)
        )
        branch.limits = self.limits
        branch.conflict_strategy = (
            deepcopy(self.conflict_strategy)
            if self.conflict_strategy is not None
            else None
        )
        branch.truth_maintenance = self.truth_maintenance
        branch._store = self._store.clone()
        branch._provenance = self._provenance.clone()
        branch._initial_facts = self._initial_facts
        branch._assumed_facts = self._assumed_facts.copy()
        branch._fired = self._fired.copy()
        branch._fired_supports = self._fired_supports.copy()
        branch._fired_activation_total = self._fired_activation_total
        branch._derivations = self._derivations.copy()
        branch._events = self._events.copy()
        branch._agenda_selections = self._agenda_selections.copy()
        branch.agenda_metrics = deepcopy(self.agenda_metrics)
        branch._agenda_memories = self._agenda_memories.copy()
        branch._previous_event_counts = self._previous_event_counts.copy()
        branch._force_full_evaluation = self._force_full_evaluation.copy()
        branch._groups = self._groups.copy()
        branch._negative_refraction_plans = (
            self._negative_refraction_plans.copy()
        )
        branch._cycles = self._cycles
        branch._fresh_counters = self._fresh_counters.copy()
        branch._fact_time_tags = self._fact_time_tags.copy()
        branch._next_time_tag = self._next_time_tag
        branch._reserved_atom_names = self._reserved_atom_names.copy()
        branch._time_tag_trail = []
        branch._checkpoint_tokens = []
        branch._next_checkpoint_token = 0
        return branch

    def checkpoint(self) -> SessionCheckpoint:
        """Open a nested reversible scope over the complete session state.

        Mutations remain immediately visible. :meth:`rollback` restores this
        exact state in place, and :meth:`release` closes the scope. Checkpoints
        are nested and must be released in last-in, first-out order.
        """

        self._next_checkpoint_token += 1
        token = self._next_checkpoint_token
        store_checkpoint = self._store.checkpoint()
        provenance_checkpoint = self._provenance.checkpoint()
        self._checkpoint_tokens.append(token)
        return SessionCheckpoint(
            owner=id(self),
            token=token,
            store=store_checkpoint,
            provenance=provenance_checkpoint,
            assumed_facts=frozenset(self._assumed_facts),
            fired=frozenset(self._fired),
            fired_supports=tuple(self._fired_supports.items()),
            fired_activation_total=self._fired_activation_total,
            derivation_count=len(self._derivations),
            event_count=len(self._events),
            agenda_selection_count=len(self._agenda_selections),
            agenda_metrics=deepcopy(self.agenda_metrics),
            agenda_memories=tuple(self._agenda_memories.items()),
            previous_event_counts=tuple(
                self._previous_event_counts.items()
            ),
            force_full_evaluation=frozenset(
                self._force_full_evaluation
            ),
            groups=tuple(self._groups.items()),
            negative_refraction_plan_count=len(
                self._negative_refraction_plans
            ),
            cycles=self._cycles,
            fresh_counters=tuple(self._fresh_counters.items()),
            time_tag_trail_size=len(self._time_tag_trail),
            next_time_tag=self._next_time_tag,
            reserved_atom_names=frozenset(self._reserved_atom_names),
            conflict_strategy=deepcopy(self.conflict_strategy),
        )

    def rollback(
        self,
        checkpoint: SessionCheckpoint,
        *,
        invalidate_strategy: bool = True,
    ) -> None:
        """Restore *checkpoint* without closing its reusable scope.

        Search orchestrators that replace the complete strategy immediately
        may disable invalidation to preserve a detached branch template.
        """

        self._validate_checkpoint(checkpoint)
        self._store.rollback(checkpoint.store)
        self._provenance.rollback(checkpoint.provenance)
        while len(self._time_tag_trail) > checkpoint.time_tag_trail_size:
            mutation = self._time_tag_trail.pop()
            if mutation.had_value:
                self._fact_time_tags[mutation.fact] = (
                    mutation.previous_value
                )
            else:
                self._fact_time_tags.pop(mutation.fact, None)
        self._assumed_facts = set(checkpoint.assumed_facts)
        self._fired = set(checkpoint.fired)
        self._fired_supports = dict(checkpoint.fired_supports)
        self._fired_activation_total = checkpoint.fired_activation_total
        del self._derivations[checkpoint.derivation_count :]
        del self._events[checkpoint.event_count :]
        del self._agenda_selections[checkpoint.agenda_selection_count :]
        self.agenda_metrics = deepcopy(checkpoint.agenda_metrics)
        self._agenda_memories = dict(checkpoint.agenda_memories)
        self._previous_event_counts = dict(
            checkpoint.previous_event_counts
        )
        self._force_full_evaluation = set(
            checkpoint.force_full_evaluation
        )
        self._groups = dict(checkpoint.groups)
        del self._negative_refraction_plans[
            checkpoint.negative_refraction_plan_count :
        ]
        self._cycles = checkpoint.cycles
        self._fresh_counters = dict(checkpoint.fresh_counters)
        self._next_time_tag = checkpoint.next_time_tag
        self._reserved_atom_names = set(checkpoint.reserved_atom_names)
        self.conflict_strategy = deepcopy(checkpoint.conflict_strategy)
        if invalidate_strategy:
            self.strategy.invalidate()

    def release(self, checkpoint: SessionCheckpoint) -> None:
        """Close the active checkpoint, retaining the current state."""

        self._validate_checkpoint(checkpoint)
        self._store.release(checkpoint.store)
        self._provenance.release(checkpoint.provenance)
        self._checkpoint_tokens.pop()
        if not self._checkpoint_tokens:
            self._time_tag_trail.clear()

    def _validate_checkpoint(self, checkpoint: SessionCheckpoint) -> None:
        if (
            checkpoint.owner != id(self)
            or not self._checkpoint_tokens
            or self._checkpoint_tokens[-1] != checkpoint.token
            or checkpoint.derivation_count > len(self._derivations)
            or checkpoint.event_count > len(self._events)
            or checkpoint.time_tag_trail_size > len(self._time_tag_trail)
        ):
            raise ValueError("checkpoint is not the active session checkpoint")

    def _set_fact_time_tag(self, fact: Fact, value: int | None) -> None:
        previous = self._fact_time_tags.get(fact)
        if self._checkpoint_tokens:
            self._time_tag_trail.append(
                _TimeTagMutation(
                    fact,
                    previous is not None,
                    previous or 0,
                )
            )
        if value is None:
            self._fact_time_tags.pop(fact, None)
        else:
            self._fact_time_tags[fact] = value

    def run_group(
        self,
        group: RuleGroup,
        *,
        mode: GroupExecutionMode = GroupExecutionMode.SATURATE,
        until: StopCondition | None = None,
    ) -> GroupRunResult:
        """Execute *group* according to *mode* while preserving session state."""

        if mode is GroupExecutionMode.UNTIL and until is None:
            raise ValueError("UNTIL mode requires a stop condition")
        if mode is not GroupExecutionMode.UNTIL and until is not None:
            raise ValueError("a stop condition is only valid in UNTIL mode")
        registered = self._groups.get(group.name)
        if registered is None:
            self._groups[group.name] = group
            self._register_negative_refraction_plans(group)
        elif registered != group:
            raise ValueError(
                f"rule group {group.name!r} was already registered "
                "with a different definition"
            )

        start_derivation_count = len(self._derivations)
        start_event_count = len(self._events)
        start_agenda_count = len(self._agenda_selections)
        start_fired_count = self._fired_activation_total
        if until is not None and until(self):
            return self._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
                cycles=0,
                stop_reason=GroupStopReason.CONDITION_MET,
            )

        if self.conflict_strategy is not None:
            return self._run_group_with_conflict_resolution(
                group,
                mode,
                until,
                start_derivation_count,
                start_event_count,
                start_agenda_count,
                start_fired_count,
            )

        for local_cycle in range(1, self.limits.max_cycles + 1):
            self._cycles += 1
            mutations_this_cycle = 0
            for rule in group.rules:
                facts_snapshot = self._store.facts
                state_key = (group.name, rule.name)
                previous_count = self._previous_event_counts.get(state_key)
                delta = (
                    None
                    if (
                        previous_count is None
                        or state_key in self._force_full_evaluation
                    )
                    else _fact_delta(
                        tuple(self._events[previous_count:]),
                        facts_snapshot,
                        revision=len(self._events),
                    )
                )
                self._force_full_evaluation.discard(state_key)
                self._previous_event_counts[state_key] = len(self._events)
                for activation in self.strategy.instantiate(
                    rule,
                    facts_snapshot,
                    delta,
                ):
                    if any(
                        fact not in self._store
                        for fact in activation.premise_facts
                    ):
                        continue
                    key = ActivationKey(
                        group.name,
                        rule.name,
                        activation.substitution.key,
                    )
                    if key in self._fired:
                        continue
                    self._fired.add(key)
                    self._fired_supports[key] = activation.premise_facts
                    self._fired_activation_total += 1
                    outcome = self._fire_activation(
                        group,
                        rule,
                        activation.substitution,
                        activation.premise_facts,
                    )
                    mutations_this_cycle += outcome.mutation_count

                    if until is not None and until(self):
                        return self._group_result(
                            group,
                            mode,
                            start_derivation_count,
                            start_event_count,
                            start_agenda_count,
                            start_fired_count,
                            cycles=local_cycle,
                            stop_reason=GroupStopReason.CONDITION_MET,
                        )
                    if (
                        mode is GroupExecutionMode.FIRST_CHANGE
                        and outcome.mutation_count
                    ):
                        return self._group_result(
                            group,
                            mode,
                            start_derivation_count,
                            start_event_count,
                            start_agenda_count,
                            start_fired_count,
                            cycles=local_cycle,
                            stop_reason=GroupStopReason.FIRST_CHANGE,
                        )

            if mode is GroupExecutionMode.ONE_CYCLE:
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_agenda_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.ONE_CYCLE,
                )
            if mutations_this_cycle == 0:
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_agenda_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.FIXED_POINT,
                )

        raise InferenceLimitError(
            f"rule group {group.name!r} did not stop after "
            f"{self.limits.max_cycles} cycles"
        )

    def _run_group_with_conflict_resolution(
        self,
        group: RuleGroup,
        mode: GroupExecutionMode,
        until: StopCondition | None,
        start_derivation_count: int,
        start_event_count: int,
        start_agenda_count: int,
        start_fired_count: int,
    ) -> GroupRunResult:
        """Resolve one complete conflict set before every activation."""

        assert self.conflict_strategy is not None
        local_cycle = 0
        while local_cycle < self.limits.max_cycles:
            candidates = self._agenda_candidates(group)
            if not candidates:
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_agenda_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.FIXED_POINT,
                )

            selected = self.conflict_strategy.select(candidates)
            local_cycle += 1
            self._cycles += 1
            key = ActivationKey(
                group.name,
                selected.rule.name,
                selected.activation.substitution.key,
            )
            self._fired.add(key)
            self._fired_supports[key] = selected.activation.premise_facts
            self._fired_activation_total += 1
            self._agenda_selections.append(
                AgendaSelection(
                    sequence=len(self._agenda_selections) + 1,
                    strategy_name=self.conflict_strategy.name,
                    rule_group=group.name,
                    rule_name=selected.rule.name,
                    substitution=selected.activation.substitution,
                    premise_facts=selected.activation.premise_facts,
                    focus_fact=selected.focus_fact,
                    focus_time_tag=selected.focus_time_tag,
                    lexicographic_time_tags=(
                        selected.lexicographic_time_tags
                    ),
                    cycle=self._cycles,
                )
            )
            outcome = self._fire_activation(
                group,
                selected.rule,
                selected.activation.substitution,
                selected.activation.premise_facts,
            )

            if until is not None and until(self):
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_agenda_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.CONDITION_MET,
                )
            if (
                mode is GroupExecutionMode.FIRST_CHANGE
                and outcome.mutation_count
            ):
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_agenda_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.FIRST_CHANGE,
                )
            if mode is GroupExecutionMode.ONE_CYCLE:
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_agenda_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.ONE_CYCLE,
                )

        raise InferenceLimitError(
            f"rule group {group.name!r} did not stop after "
            f"{self.limits.max_cycles} agenda selections"
        )

    def _agenda_candidates(
        self,
        group: RuleGroup,
    ) -> tuple[AgendaCandidate, ...]:
        """Build the complete current set of unfired activations."""

        facts_snapshot = self._store.facts
        memory = self._agenda_memories.get(group.name)
        updated_memory, candidates = _evaluate_agenda(
            group,
            facts_snapshot,
            self._events,
            memory,
            self.strategy,
            self._store,
            self._force_full_evaluation,
            self._fired,
            self._fact_time_tags,
            self.agenda_metrics,
        )
        self._agenda_memories[group.name] = updated_memory
        return candidates

    def _fire_activation(
        self,
        group: RuleGroup,
        rule: Rule,
        substitution: Substitution,
        premise_facts: tuple[Fact, ...],
    ) -> _ActivationOutcome:
        staged: list[tuple[FactMutationKind, Fact, Substitution]] = []
        self._stage_actions(rule.actions, substitution, staged)

        added: list[Fact] = []
        removed: list[Fact] = []
        for kind, fact, action_substitution in staged:
            if kind is FactMutationKind.ADD:
                derivation = self._provenance.record(
                    fact,
                    rule.name,
                    action_substitution,
                    premise_facts,
                    self._cycles,
                    rule_group=group.name,
                )
                self._derivations.append(derivation)
                if not self._store.add(fact):
                    continue
                self._next_time_tag += 1
                self._set_fact_time_tag(fact, self._next_time_tag)
                added.append(fact)
                if len(self._store) > self.limits.max_facts:
                    raise InferenceLimitError(
                        f"maximum fact count ({self.limits.max_facts}) exceeded"
                    )
            elif self._store.remove(fact):
                self._assumed_facts.discard(fact)
                self._set_fact_time_tag(fact, None)
                removed.append(fact)
            else:
                continue
            self._events.append(
                InferenceEvent(
                    sequence=len(self._events) + 1,
                    kind=kind,
                    fact=fact,
                    rule_name=rule.name,
                    rule_group=group.name,
                    substitution=action_substitution,
                    premises=premise_facts,
                    cycle=self._cycles,
                )
            )

        if self.truth_maintenance and removed:
            removed.extend(self._cascade_unsupported())
        if removed:
            absent_after_activation = frozenset(
                fact for fact in removed if fact not in self._store
            )
            if absent_after_activation:
                self.strategy.invalidate(absent_after_activation)
            self._expire_removed_supports(absent_after_activation)
        present_additions = tuple(
            fact for fact in added if fact in self._store
        )
        if present_additions and self._negative_refraction_plans:
            self._reconcile_negative_refraction(present_additions)
        return _ActivationOutcome(tuple(added), tuple(removed))

    def _cascade_unsupported(self) -> list[Fact]:
        """Retract facts outside the grounded positive justification closure."""

        current = frozenset(self._store.facts)
        supported = {
            fact
            for fact in current
            if fact in self._initial_facts or fact in self._assumed_facts
        }
        changed = True
        while changed:
            changed = False
            for fact in current - supported:
                if any(
                    all(premise in supported for premise in derivation.premises)
                    for derivation in self._provenance.derivations(fact)
                ):
                    supported.add(fact)
                    changed = True
        cascaded: list[Fact] = []
        for fact in self._store.facts:
            if fact in supported or not self._store.remove(fact):
                continue
            self._set_fact_time_tag(fact, None)
            cascaded.append(fact)
            self._record_external_removal(fact, "tms")
        return cascaded

    def _record_external_removal(self, fact: Fact, label: str) -> None:
        self._events.append(
            InferenceEvent(
                sequence=len(self._events) + 1,
                kind=FactMutationKind.REMOVE,
                fact=fact,
                rule_name=f"<{label}>",
                rule_group="<truth-maintenance>",
                substitution=EMPTY_SUBSTITUTION,
                premises=(),
                cycle=self._cycles,
            )
        )

    def _stage_actions(
        self,
        actions: tuple[Action, ...],
        substitution: Substitution,
        staged: list[tuple[FactMutationKind, Fact, Substitution]],
    ) -> Substitution:
        action_substitution = substitution
        for action in actions:
            if isinstance(action, Let):
                action_substitution = action.apply(action_substitution)
                continue
            if isinstance(action, Fresh):
                value = self._next_fresh_atom(action.prefix)
                action_substitution = action.apply(action_substitution, value)
                continue
            if isinstance(action, AddFact):
                fact = action.instantiate(action_substitution)
                self._reserve_fact_atoms(fact)
                staged.append(
                    (FactMutationKind.ADD, fact, action_substitution)
                )
                continue
            if isinstance(action, RemoveFact):
                staged.append(
                    (
                        FactMutationKind.REMOVE,
                        action.instantiate(action_substitution),
                        action_substitution,
                    )
                )
                continue
            if isinstance(action, ForEach):
                collection = action_substitution.apply(action.collection)
                if not isinstance(collection, (FiniteSet, FiniteSequence)):
                    raise TypeError(
                        "FOR EACH collection must be a ground finite "
                        "set or sequence"
                    )
                if action.variable in action_substitution:
                    raise ValueError(
                        f"FOR EACH variable ${action.variable.name} "
                        "is already bound"
                    )
                for element in collection.elements:
                    self._stage_actions(
                        action.actions,
                        action_substitution.bind(action.variable, element),
                        staged,
                    )
                continue
            if isinstance(action, Choice):
                raise RuntimeError(
                    "CHOICE actions require RuleChoiceProvider and "
                    "SessionChoiceSearch"
                )
            raise TypeError(f"unsupported action: {action!r}")
        return action_substitution

    def _next_fresh_atom(self, prefix: str) -> Atom:
        counter = self._fresh_counters.get(prefix, 0)
        while True:
            counter += 1
            name = f"{prefix}-{counter}"
            if name not in self._reserved_atom_names:
                self._fresh_counters[prefix] = counter
                self._reserved_atom_names.add(name)
                return Atom(name)

    def _reserve_fact_atoms(self, fact: Fact) -> None:
        self._reserved_atom_names.update(_atom_names_in(fact.entity))
        self._reserved_atom_names.update(_atom_names_in(fact.status))

    def _register_negative_refraction_plans(self, group: RuleGroup) -> None:
        for rule in group.rules:
            simple, complex_ = _negative_dependency_plan(rule.premises)
            if not simple and not complex_:
                continue
            self._negative_refraction_plans.append(
                _NegativeRefractionPlan(
                    group.name,
                    rule,
                    simple,
                    complex_,
                )
            )

    def _expire_removed_supports(self, removed: frozenset[Fact]) -> None:
        expired = {
            key
            for key, supports in self._fired_supports.items()
            if any(fact in removed for fact in supports)
        }
        self._fired.difference_update(expired)
        for key in expired:
            self._fired_supports.pop(key, None)

    def _reconcile_negative_refraction(
        self,
        added: tuple[Fact, ...],
    ) -> None:
        """Expire fired negative activations invalidated by fact additions."""

        oracle: IndexedInstantiationStrategy | None = None
        facts = self._store.facts
        matcher = PatternMatcher()
        for plan in self._negative_refraction_plans:
            fired_count_before = len(self._fired)
            fired_for_rule = {
                key
                for key in self._fired
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
            self._expire_activation_keys(directly_expired)
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
                if len(self._fired) != fired_count_before:
                    self._force_full_evaluation.add(
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
            self._expire_activation_keys(remaining - active)
            if len(self._fired) != fired_count_before:
                self._force_full_evaluation.add(
                    (plan.group_name, plan.rule.name)
                )

    def _expire_activation_keys(
        self,
        expired: set[ActivationKey],
    ) -> None:
        self._fired.difference_update(expired)
        for key in expired:
            self._fired_supports.pop(key, None)

    def _group_result(
        self,
        group: RuleGroup,
        mode: GroupExecutionMode,
        start_derivation_count: int,
        start_event_count: int,
        start_agenda_count: int,
        start_fired_count: int,
        *,
        cycles: int,
        stop_reason: GroupStopReason,
    ) -> GroupRunResult:
        facts = self._store.facts
        events = tuple(self._events[start_event_count:])
        return GroupRunResult(
            group_name=group.name,
            mode=mode,
            facts=facts,
            added_facts=tuple(
                event.fact
                for event in events
                if event.kind is FactMutationKind.ADD
            ),
            derivations=tuple(self._derivations[start_derivation_count:]),
            cycles=cycles,
            fired_activation_count=(
                self._fired_activation_total - start_fired_count
            ),
            stop_reason=stop_reason,
            provenance=self._provenance,
            removed_facts=tuple(
                event.fact
                for event in events
                if event.kind is FactMutationKind.REMOVE
            ),
            events=events,
            agenda_selections=tuple(
                self._agenda_selections[start_agenda_count:]
            ),
        )


class ForwardEngine:
    """Forward engine with semi-naïve instantiation and refraction by default."""

    def __init__(
        self,
        rules: tuple[Rule, ...],
        strategy: InstantiationStrategy | None = None,
        limits: EngineLimits | None = None,
        conflict_strategy: ConflictResolutionStrategy | None = None,
        *,
        truth_maintenance: bool = False,
    ) -> None:
        self.rules = tuple(rules)
        self.default_group = RuleGroup("default", self.rules)
        self.strategy = (
            strategy
            if strategy is not None
            else SemiNaiveInstantiationStrategy()
        )
        self.limits = limits or EngineLimits()
        self.conflict_strategy = conflict_strategy
        self.truth_maintenance = truth_maintenance

    def create_session(
        self,
        initial_facts: tuple[Fact, ...],
    ) -> InferenceSession:
        """Create a persistent session using this engine's strategy and limits."""

        return InferenceSession(
            initial_facts,
            self.strategy,
            self.limits,
            self.conflict_strategy,
            truth_maintenance=self.truth_maintenance,
        )

    def run(self, initial_facts: tuple[Fact, ...]) -> RunResult:
        session = self.create_session(initial_facts)
        session.run_group(self.default_group)
        return session.snapshot()


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


def _atom_names_in(term: Term) -> tuple[str, ...]:
    if isinstance(term, Atom):
        return (term.name,)
    if isinstance(term, Triple):
        return (
            *_atom_names_in(term.subject),
            *_atom_names_in(term.relation),
            *_atom_names_in(term.object),
        )
    if isinstance(term, FiniteSet):
        return tuple(
            name
            for element in term.elements
            for name in _atom_names_in(element)
        )
    if isinstance(term, FiniteSequence):
        return tuple(
            name
            for element in term.elements
            for name in _atom_names_in(element)
        )
    return ()
