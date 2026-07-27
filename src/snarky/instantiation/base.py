"""Shared types for interchangeable instantiation strategies."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import Protocol, runtime_checkable

from ..computed import ComputedPremise
from ..facts import Fact
from ..premises import (
    BindPremise,
    CollectPremise,
    CombinationsPremise,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
    variables_in_comparison_operand,
)
from ..rules import Rule
from ..substitutions import Substitution
from ..terms import Term, Variable, variables_in


@dataclass(frozen=True, slots=True)
class Activation:
    """A complete rule instantiation and its supporting facts."""

    substitution: Substitution
    premise_facts: tuple[Fact, ...]


@dataclass(frozen=True, slots=True)
class FactDelta:
    """Net working-memory changes since one rule's previous evaluation."""

    added: tuple[Fact, ...] = ()
    removed: frozenset[Fact] = frozenset()
    revision: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)


@dataclass(slots=True)
class InstantiationMetrics:
    """Cumulative counters collected by one strategy instance."""

    candidate_facts: int = 0
    match_attempts: int = 0
    activations_produced: int = 0
    index_builds: int = 0
    indexed_facts: int = 0
    index_removals: int = 0
    witness_cache_hits: int = 0
    witness_cache_misses: int = 0
    activation_cache_hits: int = 0
    activation_cache_filtered: int = 0
    witness_cache_invalidations: int = 0
    query_counter_updates: int = 0
    partial_join_builds: int = 0
    partial_join_updates: int = 0
    partial_join_bypasses: int = 0
    structural_index_builds: int = 0
    structural_index_lookups: int = 0
    adaptive_join_reorders: int = 0
    residual_witness_promotions: int = 0
    event_rule_evaluations: int = 0
    event_rule_candidates: int = 0
    domain_filter_runs: int = 0
    domain_filter_fallbacks: int = 0
    domain_filter_selections: int = 0
    domain_filter_rejections: int = 0
    domain_table_rebuilds: int = 0
    domain_table_updates: int = 0
    domain_candidate_facts: int = 0
    domain_match_attempts: int = 0
    domain_rows: int = 0
    domain_revisions: int = 0
    domain_propagator_revisions: int = 0
    domain_queue_pushes: int = 0
    domain_input_rows: int = 0
    domain_rows_examined: int = 0
    domain_combinations_tested: int = 0
    domain_specialized_revisions: int = 0
    domain_specialized_value_checks: int = 0
    domain_global_revisions: int = 0
    domain_global_value_checks: int = 0
    domain_projection_rows_examined: int = 0
    domain_projection_updates: int = 0
    domain_state_reuses: int = 0
    domain_component_resets: int = 0
    domain_bitset_builds: int = 0
    domain_bitset_updates: int = 0
    domain_bitset_resets: int = 0
    domain_bitset_intersections: int = 0
    domain_bitset_value_events: int = 0
    domain_bitset_support_checks: int = 0
    domain_compact_join_rows: int = 0
    domain_delta_join_variants: int = 0
    domain_delta_join_skips: int = 0
    domain_cost_probes: int = 0
    domain_cost_probe_deferrals: int = 0
    domain_cost_probe_rejections: int = 0
    domain_filter_probe_seconds: float = 0.0
    domain_fallback_probe_seconds: float = 0.0
    domain_values_removed: int = 0
    domain_candidates_removed: int = 0

    def reset(self) -> None:
        """Reset all counters before another measured run."""

        self.candidate_facts = 0
        self.match_attempts = 0
        self.activations_produced = 0
        self.index_builds = 0
        self.indexed_facts = 0
        self.index_removals = 0
        self.witness_cache_hits = 0
        self.witness_cache_misses = 0
        self.activation_cache_hits = 0
        self.activation_cache_filtered = 0
        self.witness_cache_invalidations = 0
        self.query_counter_updates = 0
        self.partial_join_builds = 0
        self.partial_join_updates = 0
        self.partial_join_bypasses = 0
        self.structural_index_builds = 0
        self.structural_index_lookups = 0
        self.adaptive_join_reorders = 0
        self.residual_witness_promotions = 0
        self.event_rule_evaluations = 0
        self.event_rule_candidates = 0
        self.domain_filter_runs = 0
        self.domain_filter_fallbacks = 0
        self.domain_filter_selections = 0
        self.domain_filter_rejections = 0
        self.domain_table_rebuilds = 0
        self.domain_table_updates = 0
        self.domain_candidate_facts = 0
        self.domain_match_attempts = 0
        self.domain_rows = 0
        self.domain_revisions = 0
        self.domain_propagator_revisions = 0
        self.domain_queue_pushes = 0
        self.domain_input_rows = 0
        self.domain_rows_examined = 0
        self.domain_combinations_tested = 0
        self.domain_specialized_revisions = 0
        self.domain_specialized_value_checks = 0
        self.domain_global_revisions = 0
        self.domain_global_value_checks = 0
        self.domain_projection_rows_examined = 0
        self.domain_projection_updates = 0
        self.domain_state_reuses = 0
        self.domain_component_resets = 0
        self.domain_bitset_builds = 0
        self.domain_bitset_updates = 0
        self.domain_bitset_resets = 0
        self.domain_bitset_intersections = 0
        self.domain_bitset_value_events = 0
        self.domain_bitset_support_checks = 0
        self.domain_compact_join_rows = 0
        self.domain_delta_join_variants = 0
        self.domain_delta_join_skips = 0
        self.domain_cost_probes = 0
        self.domain_cost_probe_deferrals = 0
        self.domain_cost_probe_rejections = 0
        self.domain_filter_probe_seconds = 0.0
        self.domain_fallback_probe_seconds = 0.0
        self.domain_values_removed = 0
        self.domain_candidates_removed = 0


class InstantiationStrategy(Protocol):
    """Structural interface consumed by the forward engine."""

    metrics: InstantiationMetrics

    def instantiate(
        self,
        rule: Rule,
        facts: Sequence[Fact],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]: ...

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        """Update or discard indexes after a non-append-only mutation."""


@runtime_checkable
class BranchableInstantiationStrategy(Protocol):
    """Optional lifecycle contract for efficiently isolated search branches."""

    def fork_for_branch(self) -> InstantiationStrategy:
        """Return an isolated strategy prepared for a child branch."""


@runtime_checkable
class QueryableInstantiationStrategy(Protocol):
    """Optional lifecycle contract for isolated read-only rule queries."""

    def query_view(self) -> InstantiationStrategy:
        """Return a strategy view for queries over the current fact snapshot."""


type Witness = tuple[Fact, ...] | None
type WitnessCacheKey = tuple[
    tuple[Premise, ...],
    tuple[tuple[str, Term], ...],
]
type WitnessCache = dict[WitnessCacheKey, Witness]


def witness_cache_key(
    premises: tuple[Premise, ...],
    substitution: Substitution,
) -> WitnessCacheKey:
    """Project a substitution onto variables visible in an existential block."""

    correlated = tuple(
        (variable.name, substitution.apply(variable))
        for variable in _ordered_variables_in_premises(premises)
        if variable in substitution
    )
    return premises, correlated


@cache
def _ordered_variables_in_premises(
    premises: tuple[Premise, ...],
) -> tuple[Variable, ...]:
    return tuple(
        sorted(
            _variables_in_premises(premises),
            key=lambda variable: variable.name,
        )
    )


@cache
def _variables_in_premises(
    premises: tuple[Premise, ...],
) -> frozenset[Variable]:
    variables: set[Variable] = set()
    for premise in premises:
        if isinstance(premise, FactPremise):
            variables.update(variables_in(premise.entity))
            variables.update(variables_in(premise.status))
        elif isinstance(premise, ComparisonPremise):
            variables.update(variables_in_comparison_operand(premise.left))
            variables.update(variables_in_comparison_operand(premise.right))
        elif isinstance(premise, BindPremise):
            variables.add(premise.target)
            variables.update(variables_in(premise.value))
        elif isinstance(premise, ComputedPremise):
            if premise.target is not None:
                variables.add(premise.target)
            for argument in premise.arguments:
                variables.update(variables_in(argument))
        elif isinstance(premise, CombinationsPremise):
            variables.add(premise.target)
            variables.update(variables_in(premise.source))
        elif isinstance(premise, CollectPremise):
            variables.add(premise.target)
            variables.update(variables_in(premise.projection))
            variables.update(_variables_in_premises(premise.premises))
        elif isinstance(
            premise,
            (
                ExistsPremise,
                NotExistsPremise,
                CountPremise,
                UniquePremise,
            ),
        ):
            variables.update(_variables_in_premises(premise.premises))
        else:
            raise TypeError(f"unsupported premise: {premise!r}")
    return frozenset(variables)
