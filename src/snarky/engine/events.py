"""Chronological working-memory mutation events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..facts import Fact
from ..substitutions import Substitution


class FactMutationKind(StrEnum):
    """Kinds of effective working-memory mutations."""

    ADD = "add"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class InferenceEvent:
    """One effective fact mutation caused by a rule activation."""

    sequence: int
    kind: FactMutationKind
    fact: Fact
    rule_name: str
    rule_group: str
    substitution: Substitution
    premises: tuple[Fact, ...]
    cycle: int
