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


@dataclass(frozen=True, slots=True)
class RuleGroup:
    """A named set of rules that can be executed as one control unit."""

    name: str
    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule group name cannot be empty")
        rules = tuple(self.rules)
        names = [rule.name for rule in rules]
        if len(set(names)) != len(names):
            raise ValueError(f"rule group {self.name!r} contains duplicate rule names")
        object.__setattr__(self, "rules", rules)


def when(entity: Term, status: Term = Status.VRAI) -> FactPremise:
    """Public convenience constructor for a positive fact premise."""

    return FactPremise(entity, status)
