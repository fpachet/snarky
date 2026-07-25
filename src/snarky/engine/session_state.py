"""Checkpoint data and reversible session bookkeeping."""

from __future__ import annotations

from dataclasses import dataclass

from ..facts import Fact
from ..rules import RuleGroup
from ..stores.naive import FactStoreCheckpoint
from ..terms import Term
from .agenda import _AgendaMemory
from .conflict import (
    AgendaMetrics,
    ConflictResolutionStrategy,
)
from .provenance import ProvenanceCheckpoint


@dataclass(frozen=True, slots=True)
class ActivationKey:
    rule_group: str
    rule_name: str
    substitution: tuple[tuple[str, Term], ...]


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
