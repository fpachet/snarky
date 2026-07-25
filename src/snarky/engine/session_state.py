"""Checkpoint data and reversible session bookkeeping."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..facts import Fact
from ..instantiation import InstantiationStrategy
from ..rules import RuleGroup
from ..stores.naive import FactStoreCheckpoint
from .agenda import ActivationKey, _AgendaMemory
from .conflict import (
    AgendaMetrics,
    AgendaSelection,
    ConflictResolutionStrategy,
)
from .events import InferenceEvent
from .provenance import (
    Derivation,
    Provenance,
    ProvenanceCheckpoint,
)

if TYPE_CHECKING:
    from .forward import InferenceSession


@dataclass(frozen=True, slots=True)
class _TimeTagMutation:
    fact: Fact
    had_value: bool
    previous_value: int


@dataclass(frozen=True, slots=True)
class SessionCheckpoint:
    """Opaque reversible position in an inference session."""

    owner: int
    token: int
    store: FactStoreCheckpoint
    provenance: ProvenanceCheckpoint
    assumed_facts: frozenset[Fact]
    fired: frozenset[ActivationKey]
    fired_supports: tuple[
        tuple[ActivationKey, tuple[Fact, ...]],
        ...,
    ]
    fired_activation_total: int
    derivation_count: int
    event_count: int
    agenda_selection_count: int
    agenda_metrics: AgendaMetrics
    agenda_memories: tuple[tuple[str, _AgendaMemory], ...]
    previous_event_counts: tuple[
        tuple[tuple[str, str], int],
        ...,
    ]
    force_full_evaluation: frozenset[tuple[str, str]]
    groups: tuple[tuple[str, RuleGroup], ...]
    negative_refraction_plan_count: int
    cycles: int
    fresh_counters: tuple[tuple[str, int], ...]
    time_tag_trail_size: int
    next_time_tag: int
    reserved_atom_names: frozenset[str]
    conflict_strategy: ConflictResolutionStrategy | None


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


def _snapshot(session: InferenceSession) -> RunResult:
    facts = session._store.facts
    return RunResult(
        facts=facts,
        derived_facts=tuple(
            fact for fact in facts if fact not in session._initial_facts
        ),
        derivations=tuple(session._derivations),
        cycles=session._cycles,
        fired_activation_count=session._fired_activation_total,
        provenance=session._provenance,
        events=tuple(session._events),
        agenda_selections=tuple(session._agenda_selections),
    )


def _fork(
    session: InferenceSession,
    session_type: type[InferenceSession],
    strategy: InstantiationStrategy | None,
) -> InferenceSession:
    branch = object.__new__(session_type)
    branch.strategy = (
        strategy if strategy is not None else deepcopy(session.strategy)
    )
    branch.limits = session.limits
    branch.conflict_strategy = (
        deepcopy(session.conflict_strategy)
        if session.conflict_strategy is not None
        else None
    )
    branch.truth_maintenance = session.truth_maintenance
    branch._store = session._store.clone()
    branch._provenance = session._provenance.clone()
    branch._initial_facts = session._initial_facts
    branch._assumed_facts = session._assumed_facts.copy()
    branch._fired = session._fired.copy()
    branch._fired_supports = session._fired_supports.copy()
    branch._fired_activation_total = session._fired_activation_total
    branch._derivations = session._derivations.copy()
    branch._events = session._events.copy()
    branch._agenda_selections = session._agenda_selections.copy()
    branch.agenda_metrics = deepcopy(session.agenda_metrics)
    branch._agenda_memories = session._agenda_memories.copy()
    branch._previous_event_counts = session._previous_event_counts.copy()
    branch._force_full_evaluation = session._force_full_evaluation.copy()
    branch._groups = session._groups.copy()
    branch._negative_refraction_plans = (
        session._negative_refraction_plans.copy()
    )
    branch._cycles = session._cycles
    branch._fresh_counters = session._fresh_counters.copy()
    branch._fact_time_tags = session._fact_time_tags.copy()
    branch._next_time_tag = session._next_time_tag
    branch._reserved_atom_names = session._reserved_atom_names.copy()
    branch._time_tag_trail = []
    branch._checkpoint_tokens = []
    branch._next_checkpoint_token = 0
    return branch


def _checkpoint(session: InferenceSession) -> SessionCheckpoint:
    session._next_checkpoint_token += 1
    token = session._next_checkpoint_token
    store_checkpoint = session._store.checkpoint()
    provenance_checkpoint = session._provenance.checkpoint()
    session._checkpoint_tokens.append(token)
    return SessionCheckpoint(
        owner=id(session),
        token=token,
        store=store_checkpoint,
        provenance=provenance_checkpoint,
        assumed_facts=frozenset(session._assumed_facts),
        fired=frozenset(session._fired),
        fired_supports=tuple(session._fired_supports.items()),
        fired_activation_total=session._fired_activation_total,
        derivation_count=len(session._derivations),
        event_count=len(session._events),
        agenda_selection_count=len(session._agenda_selections),
        agenda_metrics=deepcopy(session.agenda_metrics),
        agenda_memories=tuple(session._agenda_memories.items()),
        previous_event_counts=tuple(
            session._previous_event_counts.items()
        ),
        force_full_evaluation=frozenset(
            session._force_full_evaluation
        ),
        groups=tuple(session._groups.items()),
        negative_refraction_plan_count=len(
            session._negative_refraction_plans
        ),
        cycles=session._cycles,
        fresh_counters=tuple(session._fresh_counters.items()),
        time_tag_trail_size=len(session._time_tag_trail),
        next_time_tag=session._next_time_tag,
        reserved_atom_names=frozenset(session._reserved_atom_names),
        conflict_strategy=deepcopy(session.conflict_strategy),
    )


def _rollback(
    session: InferenceSession,
    checkpoint: SessionCheckpoint,
    *,
    invalidate_strategy: bool = True,
) -> None:
    session._validate_checkpoint(checkpoint)
    session._store.rollback(checkpoint.store)
    session._provenance.rollback(checkpoint.provenance)
    while len(session._time_tag_trail) > checkpoint.time_tag_trail_size:
        mutation = session._time_tag_trail.pop()
        if mutation.had_value:
            session._fact_time_tags[mutation.fact] = (
                mutation.previous_value
            )
        else:
            session._fact_time_tags.pop(mutation.fact, None)
    session._assumed_facts = set(checkpoint.assumed_facts)
    session._fired = set(checkpoint.fired)
    session._fired_supports = dict(checkpoint.fired_supports)
    session._fired_activation_total = checkpoint.fired_activation_total
    del session._derivations[checkpoint.derivation_count :]
    del session._events[checkpoint.event_count :]
    del session._agenda_selections[checkpoint.agenda_selection_count :]
    session.agenda_metrics = deepcopy(checkpoint.agenda_metrics)
    session._agenda_memories = dict(checkpoint.agenda_memories)
    session._previous_event_counts = dict(
        checkpoint.previous_event_counts
    )
    session._force_full_evaluation = set(
        checkpoint.force_full_evaluation
    )
    session._groups = dict(checkpoint.groups)
    del session._negative_refraction_plans[
        checkpoint.negative_refraction_plan_count :
    ]
    session._cycles = checkpoint.cycles
    session._fresh_counters = dict(checkpoint.fresh_counters)
    session._next_time_tag = checkpoint.next_time_tag
    session._reserved_atom_names = set(checkpoint.reserved_atom_names)
    session.conflict_strategy = deepcopy(checkpoint.conflict_strategy)
    if invalidate_strategy:
        session.strategy.invalidate()


def _release(
    session: InferenceSession,
    checkpoint: SessionCheckpoint,
) -> None:
    session._validate_checkpoint(checkpoint)
    session._store.release(checkpoint.store)
    session._provenance.release(checkpoint.provenance)
    session._checkpoint_tokens.pop()
    if not session._checkpoint_tokens:
        session._time_tag_trail.clear()


def _validate_checkpoint(
    session: InferenceSession,
    checkpoint: SessionCheckpoint,
) -> None:
    if (
        checkpoint.owner != id(session)
        or not session._checkpoint_tokens
        or session._checkpoint_tokens[-1] != checkpoint.token
        or checkpoint.derivation_count > len(session._derivations)
        or checkpoint.event_count > len(session._events)
        or checkpoint.time_tag_trail_size > len(session._time_tag_trail)
    ):
        raise ValueError("checkpoint is not the active session checkpoint")


def _set_fact_time_tag(
    session: InferenceSession,
    fact: Fact,
    value: int | None,
) -> None:
    previous = session._fact_time_tags.get(fact)
    if session._checkpoint_tokens:
        session._time_tag_trail.append(
            _TimeTagMutation(
                fact,
                previous is not None,
                previous or 0,
            )
        )
    if value is None:
        session._fact_time_tags.pop(fact, None)
    else:
        session._fact_time_tags[fact] = value
