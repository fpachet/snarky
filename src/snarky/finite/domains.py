"""Finite domains stored as reversible bit masks, without candidate facts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..terms import Atom, Term
from .model import FiniteVariable


@dataclass(frozen=True, slots=True)
class DomainRemoval:
    variable: Term
    values: frozenset[Term]
    cause: Atom


@dataclass(frozen=True, slots=True)
class DomainCheckpoint:
    owner: object
    token: int
    trail_position: int
    removal_position: int


class FiniteDomains:
    """Stable value indexes with trailed masks and explicit changed-variable events."""

    def __init__(self, variables: tuple[FiniteVariable, ...]) -> None:
        self._values: dict[Term, tuple[Term, ...]] = {
            variable.name: variable.domain for variable in variables
        }
        self._bits = {
            variable: {value: 1 << i for i, value in enumerate(values)}
            for variable, values in self._values.items()
        }
        self._masks = {
            var: (1 << len(values)) - 1 for var, values in self._values.items()
        }
        self._trail: list[tuple[Term, int]] = []
        self._checkpoints: list[DomainCheckpoint] = []
        self._owner = object()
        self._token = 0
        self._removals: list[DomainRemoval] = []
        self._changed = set(self._values)

    def values(self, variable: Term) -> tuple[Term, ...]:
        mask = self._masks[variable]
        values = self._values[variable]
        selected = []
        while mask:
            bit = mask & -mask
            selected.append(values[bit.bit_length() - 1])
            mask ^= bit
        return tuple(selected)

    def size(self, variable: Term) -> int:
        return self._masks[variable].bit_count()

    @property
    def empty(self) -> bool:
        return any(mask == 0 for mask in self._masks.values())

    @property
    def complete(self) -> bool:
        return all(mask.bit_count() == 1 for mask in self._masks.values())

    @property
    def removals(self) -> tuple[DomainRemoval, ...]:
        return tuple(self._removals)

    def snapshot(self) -> Mapping[Term, frozenset[Term]]:
        from types import MappingProxyType

        return MappingProxyType(
            {var: frozenset(self.values(var)) for var in self._values}
        )

    def take_changed(self) -> set[Term]:
        changed = self._changed
        self._changed = set()
        return changed

    def retain(
        self, variable: Term, supported: set[Term] | frozenset[Term], cause: Atom
    ) -> bool:
        mask = 0
        for value in supported:
            mask |= self._bits[variable].get(value, 0)
        previous = self._masks[variable]
        mask &= previous
        if mask == previous:
            return False
        removed = frozenset(
            value for value in self.values(variable) if value not in supported
        )
        if self._checkpoints:
            self._trail.append((variable, previous))
        self._masks[variable] = mask
        self._removals.append(DomainRemoval(variable, removed, cause))
        self._changed.add(variable)
        return True

    def checkpoint(self) -> DomainCheckpoint:
        checkpoint = DomainCheckpoint(
            self._owner, self._token, len(self._trail), len(self._removals)
        )
        self._token += 1
        self._checkpoints.append(checkpoint)
        return checkpoint

    def rollback(self, checkpoint: DomainCheckpoint) -> None:
        if checkpoint.owner is not self._owner or checkpoint not in self._checkpoints:
            raise ValueError("checkpoint is foreign, released, or abandoned")
        while len(self._trail) > checkpoint.trail_position:
            variable, mask = self._trail.pop()
            self._masks[variable] = mask
            self._changed.add(variable)
        del self._removals[checkpoint.removal_position :]
        del self._checkpoints[self._checkpoints.index(checkpoint) + 1 :]

    def release(self, checkpoint: DomainCheckpoint) -> None:
        if not self._checkpoints or self._checkpoints[-1] != checkpoint:
            raise ValueError("checkpoints must be released in nesting order")
        self._checkpoints.pop()
        if not self._checkpoints:
            self._trail.clear()
