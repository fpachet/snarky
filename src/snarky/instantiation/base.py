"""Shared types for interchangeable instantiation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..facts import Fact
from ..rules import Rule
from ..substitutions import Substitution


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

    def reset(self) -> None:
        """Reset all counters before another measured run."""

        self.candidate_facts = 0
        self.match_attempts = 0
        self.activations_produced = 0
        self.index_builds = 0
        self.indexed_facts = 0


class InstantiationStrategy(Protocol):
    """Structural interface consumed by the forward engine."""

    metrics: InstantiationMetrics

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]: ...
