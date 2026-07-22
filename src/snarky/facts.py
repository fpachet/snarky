"""Facts stored and matched by Snarky."""

from __future__ import annotations

from dataclasses import dataclass

from .terms import Status, Term, is_ground


@dataclass(frozen=True, slots=True)
class Fact:
    """A ground entity associated with an explicit status."""

    entity: Term
    status: Term = Status.VRAI

    def __post_init__(self) -> None:
        if not is_ground(self.entity) or not is_ground(self.status):
            raise ValueError("stored facts must be ground")
