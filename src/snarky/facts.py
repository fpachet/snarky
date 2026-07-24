"""Facts stored and matched by Snarky."""

from __future__ import annotations

from dataclasses import dataclass

from .terms import Status, Term, _PreHashed, is_ground


@dataclass(frozen=True, slots=True)
class Fact(_PreHashed):
    """A ground entity associated with an explicit status."""

    entity: Term
    status: Term = Status.VRAI

    def __post_init__(self) -> None:
        if not is_ground(self.entity) or not is_ground(self.status):
            raise ValueError("stored facts must be ground")
        object.__setattr__(self, "_hash", hash((self.entity, self.status)))

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(self) -> tuple[type[Fact], tuple[Term, Term]]:
        return Fact, (self.entity, self.status)
