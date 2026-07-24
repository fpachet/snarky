"""Shared types for interchangeable instantiation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Protocol

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


class InstantiationStrategy(Protocol):
    """Structural interface consumed by the forward engine."""

    metrics: InstantiationMetrics

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]: ...

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        """Update or discard indexes after a non-append-only mutation."""


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
            variables.update(variables_in(premise.left))
            variables.update(variables_in(premise.right))
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
