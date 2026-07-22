"""Rule model and public premise helper."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .actions import Action
from .premises import FactPremise, Premise
from .terms import Status, Term


@dataclass(frozen=True, slots=True)
class Rule:
    """An ordered set of premises followed by monotone actions."""

    name: str
    premises: tuple[Premise, ...]
    actions: tuple[Action, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule name cannot be empty")
        if not self.premises:
            raise ValueError(f"rule {self.name!r} must contain a premise")
        if not self.actions:
            raise ValueError(f"rule {self.name!r} must contain an action")
        object.__setattr__(self, "premises", tuple(self.premises))
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def when(entity: Term, status: Term = Status.VRAI) -> FactPremise:
    """Public convenience constructor for a positive fact premise."""

    return FactPremise(entity, status)
