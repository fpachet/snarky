"""Deterministic forward chaining, persistent sessions, and rule groups."""

from __future__ import annotations

from typing import Literal, overload

from ..actions import Action
from ..facts import Fact
from ..instantiation import (
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from ..rules import Rule, RuleGroup
from ..stores.naive import NaiveFactStore
from ..substitutions import Substitution
from ..terms import Atom
from .agenda import (
    ActivationKey,
    _AgendaMemory,
    _evaluate_agenda,
)
from .conflict import (
    AgendaCandidate,
    AgendaMetrics,
    AgendaSelection,
    ConflictResolutionStrategy,
)
from .events import (
    FactMutationKind,
    InferenceEvent,
    InferenceEventCursor,
)
from .group_execution import (
    EngineLimits as EngineLimits,
)
from .group_execution import (
    FactExists as FactExists,
)
from .group_execution import (
    GroupExecutionMode as GroupExecutionMode,
)
from .group_execution import (
    GroupRunResult as GroupRunResult,
)
from .group_execution import (
    GroupStopReason as GroupStopReason,
)
from .group_execution import (
    InferenceLimitError as InferenceLimitError,
)
from .group_execution import (
    StopCondition as StopCondition,
)
from .group_execution import (
    _run_group,
)
from .mutations import (
    _ActivationOutcome,
    _assume,
    _atom_names_in,
    _cascade_unsupported,
    _fire_activation,
    _next_fresh_atom,
    _record_external_removal,
    _reserve_fact_atoms,
    _retract,
    _stage_actions,
)
from .provenance import Derivation, Provenance
from .refraction import (
    _expire_activation_keys,
    _expire_removed_supports,
    _NegativeRefractionPlan,
    _reconcile_negative_refraction,
    _register_negative_refraction_plans,
)
from .session_state import (
    RunResult as RunResult,
)
from .session_state import (
    SessionCheckpoint as SessionCheckpoint,
)
from .session_state import (
    _checkpoint,
    _fork,
    _release,
    _rollback,
    _set_fact_time_tag,
    _snapshot,
    _TimeTagMutation,
    _validate_checkpoint,
)


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
        self._event_generation = 0
        self._event_generation_origin = 0
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
    def event_count(self) -> int:
        """Return the current mutation-journal length without copying it."""

        return len(self._events)

    def events_since(self, position: int) -> tuple[InferenceEvent, ...]:
        """Return journal events appended after zero-based *position*."""

        if not 0 <= position <= len(self._events):
            raise ValueError("event position is outside the current journal")
        return tuple(self._events[position:])

    def event_cursor(self) -> InferenceEventCursor:
        """Return a journal cursor invalidated by rollback or another fork."""

        return InferenceEventCursor(
            id(self),
            self._event_generation,
            self._event_generation_origin,
            len(self._events),
        )

    def events_after(
        self,
        cursor: InferenceEventCursor,
    ) -> tuple[InferenceEvent, ...] | None:
        """Return events after *cursor*, or ``None`` when rollback expired it."""

        if cursor.owner != id(self):
            raise ValueError("event cursor belongs to another session")
        if cursor.generation != self._event_generation:
            return None
        if not 0 <= cursor.position <= len(self._events):
            return None
        return tuple(self._events[cursor.position:])

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

        return _assume(self, facts, label)

    def retract(
        self,
        *facts: Fact,
        label: str = "external",
    ) -> tuple[Fact, ...]:
        """Retract facts and optionally cascade unsupported conclusions."""

        return _retract(self, facts, label)

    def snapshot(self) -> RunResult:
        """Return the cumulative state using the historical result shape."""

        return _snapshot(self)

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

        return _fork(self, InferenceSession, strategy)

    def checkpoint(self) -> SessionCheckpoint:
        """Open a nested reversible scope over the complete session state.

        Mutations remain immediately visible. :meth:`rollback` restores this
        exact state in place, and :meth:`release` closes the scope. Checkpoints
        are nested and must be released in last-in, first-out order.
        """

        return _checkpoint(self)

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

        _rollback(
            self,
            checkpoint,
            invalidate_strategy=invalidate_strategy,
        )

    def release(self, checkpoint: SessionCheckpoint) -> None:
        """Close the active checkpoint, retaining the current state."""

        _release(self, checkpoint)

    def _validate_checkpoint(self, checkpoint: SessionCheckpoint) -> None:
        _validate_checkpoint(self, checkpoint)

    def _set_fact_time_tag(self, fact: Fact, value: int | None) -> None:
        _set_fact_time_tag(self, fact, value)

    def _instantiation_facts(self) -> NaiveFactStore | tuple[Fact, ...]:
        """Use a live view only for strategies that explicitly support it."""

        if getattr(self.strategy, "supports_fact_view", False):
            return self._store
        return self._store.facts

    @overload
    def run_group(
        self,
        group: RuleGroup,
        *,
        mode: GroupExecutionMode = GroupExecutionMode.SATURATE,
        until: StopCondition | None = None,
        materialize_result: Literal[True] = True,
    ) -> GroupRunResult: ...

    @overload
    def run_group(
        self,
        group: RuleGroup,
        *,
        mode: GroupExecutionMode = GroupExecutionMode.SATURATE,
        until: StopCondition | None = None,
        materialize_result: Literal[False],
    ) -> None: ...

    def run_group(
        self,
        group: RuleGroup,
        *,
        mode: GroupExecutionMode = GroupExecutionMode.SATURATE,
        until: StopCondition | None = None,
        materialize_result: bool = True,
    ) -> GroupRunResult | None:
        """Execute *group*, optionally skipping its immutable result snapshot."""

        return _run_group(
            self,
            group,
            mode,
            until,
            materialize_result,
        )

    def _agenda_candidates(
        self,
        group: RuleGroup,
    ) -> tuple[AgendaCandidate, ...]:
        """Build the complete current set of unfired activations."""

        memory = self._agenda_memories.get(group.name)
        updated_memory, candidates = _evaluate_agenda(
            group,
            self._instantiation_facts(),
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
        return _fire_activation(
            self,
            group,
            rule,
            substitution,
            premise_facts,
        )

    def _fire_compiled_activation(
        self,
        group: RuleGroup,
        rule: Rule,
        substitution: Substitution,
        premise_facts: tuple[Fact, ...],
    ) -> _ActivationOutcome | None:
        """Fire one prevalidated activation through normal refraction."""

        key = ActivationKey(
            group.name,
            rule.name,
            substitution.key,
        )
        if key in self._fired:
            return None
        self._fired.add(key)
        self._fired_supports[key] = premise_facts
        self._fired_activation_total += 1
        return self._fire_activation(
            group,
            rule,
            substitution,
            premise_facts,
        )

    def _cascade_unsupported(self) -> list[Fact]:
        """Retract facts outside the grounded positive justification closure."""

        return _cascade_unsupported(self)

    def _record_external_removal(self, fact: Fact, label: str) -> None:
        _record_external_removal(self, fact, label)

    def _stage_actions(
        self,
        actions: tuple[Action, ...],
        substitution: Substitution,
        staged: list[tuple[FactMutationKind, Fact, Substitution]],
    ) -> Substitution:
        return _stage_actions(self, actions, substitution, staged)

    def _next_fresh_atom(self, prefix: str) -> Atom:
        return _next_fresh_atom(self, prefix)

    def _reserve_fact_atoms(self, fact: Fact) -> None:
        _reserve_fact_atoms(self, fact)

    def _register_negative_refraction_plans(self, group: RuleGroup) -> None:
        _register_negative_refraction_plans(self, group)

    def _expire_removed_supports(self, removed: frozenset[Fact]) -> None:
        _expire_removed_supports(self, removed)

    def _reconcile_negative_refraction(
        self,
        added: tuple[Fact, ...],
    ) -> None:
        """Expire fired negative activations invalidated by fact additions."""

        _reconcile_negative_refraction(self, added)

    def _expire_activation_keys(
        self,
        expired: set[ActivationKey],
    ) -> None:
        _expire_activation_keys(self, expired)

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
        materialize_result: bool,
    ) -> GroupRunResult | None:
        if not materialize_result:
            return None
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
