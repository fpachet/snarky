"""Shared types for interchangeable instantiation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..facts import Fact
from ..premises import (
    ComparisonPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
)
from ..rules import Rule
from ..substitutions import Substitution
from ..terms import Term, Variable, variables_in


@dataclass(frozen=True, slots=True)
class Activation:
    """A complete rule instantiation and its supporting facts."""

    substitution: Substitution
    premise_facts: tuple[Fact, ...]


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


class InstantiationStrategy(Protocol):
    """Structural interface consumed by the forward engine."""

    metrics: InstantiationMetrics

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None = None,
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

    variables = _variables_in_premises(premises)
    correlated = tuple(
        sorted(
            (
                (variable.name, substitution.apply(variable))
                for variable in variables
                if variable in substitution
            ),
            key=lambda item: item[0],
        )
    )
    return premises, correlated


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
        elif isinstance(premise, (ExistsPremise, NotExistsPremise)):
            variables.update(_variables_in_premises(premise.premises))
        else:
            raise TypeError(f"unsupported premise: {premise!r}")
    return frozenset(variables)
