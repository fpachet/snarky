"""Deterministic forward chaining, persistent sessions, and rule groups."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from ..actions import Action
from ..facts import Fact
from ..instantiation import (
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from ..rules import Rule, RuleGroup
from ..stores.naive import NaiveFactStore
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
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
from .events import FactMutationKind, InferenceEvent
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
    _atom_names_in,
    _cascade_unsupported,
    _fire_activation,
    _next_fresh_atom,
    _record_external_removal,
    _reserve_fact_atoms,
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
    SessionCheckpoint as SessionCheckpoint,
)
from .session_state import (
    _TimeTagMutation,
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

        return _run_group(self, group, mode, until)

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
        return _fire_activation(
            self,
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
