"""Conflict-set selection policies for agenda-driven inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..facts import Fact
from ..instantiation import Activation
from ..rules import Rule
from ..substitutions import Substitution


@dataclass(slots=True)
class AgendaMetrics:
    """Counters for dependency-driven rule and conflict-set maintenance."""

    rebuilds: int = 0
    rule_recomputations: int = 0
    rule_reuses: int = 0


@dataclass(frozen=True, slots=True)
class AgendaCandidate:
    """One unfired activation enriched with deterministic agenda metadata."""

    rule: Rule
    activation: Activation
    rule_order: int
    candidate_order: int
    focus_fact: Fact | None
    focus_time_tag: int
    lexicographic_time_tags: tuple[int, ...]

    @property
    def specificity(self) -> int:
        """Return the number of premises used as the final MEA tie-breaker."""

        return len(self.rule.premises)


class ConflictResolutionStrategy(Protocol):
    """Select one activation from a complete current conflict set."""

    @property
    def name(self) -> str: ...

    def select(
        self,
        candidates: tuple[AgendaCandidate, ...],
    ) -> AgendaCandidate: ...


@dataclass(frozen=True, slots=True)
class MEAConflictStrategy:
    """OPS-style means-ends analysis using explicit or default local focus.

    A ``FOCUS`` premise is primary. Without one, the first supporting fact
    remains the backward-compatible default. Remaining ties use a LEX-like
    vector, rule specificity and source order.
    """

    name: str = "mea"

    def select(
        self,
        candidates: tuple[AgendaCandidate, ...],
    ) -> AgendaCandidate:
        if not candidates:
            raise ValueError("MEA requires at least one agenda candidate")
        return max(candidates, key=self._priority)

    @staticmethod
    def _priority(
        candidate: AgendaCandidate,
    ) -> tuple[int, tuple[int, ...], int, int, int]:
        return (
            candidate.focus_time_tag,
            candidate.lexicographic_time_tags,
            candidate.specificity,
            -candidate.rule_order,
            -candidate.candidate_order,
        )


@dataclass(frozen=True, slots=True)
class AgendaSelection:
    """Observable record of one conflict-set choice."""

    sequence: int
    strategy_name: str
    rule_group: str
    rule_name: str
    substitution: Substitution
    premise_facts: tuple[Fact, ...]
    focus_fact: Fact | None
    focus_time_tag: int
    lexicographic_time_tags: tuple[int, ...]
    cycle: int
