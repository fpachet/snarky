"""Deterministic scan-based fact store used as the reference implementation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from ..facts import Fact


@dataclass(frozen=True, slots=True)
class FactStoreCheckpoint:
    """Opaque position in a reversible fact-store mutation trail."""

    owner: int
    token: int
    trail_size: int


@dataclass(slots=True)
class _FactNode:
    fact: Fact
    previous: _FactNode | None = None
    next: _FactNode | None = None


@dataclass(frozen=True, slots=True)
class _FactMutation:
    added: bool
    node: _FactNode
    previous: _FactNode | None
    next: _FactNode | None


class NaiveFactStore:
    """An insertion-ordered set of facts supporting multiple statuses."""

    __slots__ = (
        "_checkpoints",
        "_facts",
        "_head",
        "_next_checkpoint_token",
        "_tail",
        "_trail",
    )

    def __init__(self, facts: Iterable[Fact] = ()) -> None:
        self._facts: dict[Fact, _FactNode] = {}
        self._head: _FactNode | None = None
        self._tail: _FactNode | None = None
        self._trail: list[_FactMutation] = []
        self._checkpoints: list[int] = []
        self._next_checkpoint_token = 0
        for fact in facts:
            self.add(fact)

    def add(self, fact: Fact) -> bool:
        """Add *fact* and report whether it was new."""

        if fact in self._facts:
            return False
        node = _FactNode(fact, self._tail)
        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node
        self._tail = node
        self._facts[fact] = node
        if self._checkpoints:
            self._trail.append(_FactMutation(True, node, node.previous, None))
        return True

    def remove(self, fact: Fact) -> bool:
        """Remove *fact* and report whether it was present."""

        node = self._facts.pop(fact, None)
        if node is None:
            return False
        previous = node.previous
        next_node = node.next
        if self._checkpoints:
            self._trail.append(
                _FactMutation(False, node, previous, next_node)
            )
        self._unlink(node)
        return True

    def checkpoint(self) -> FactStoreCheckpoint:
        """Start a nested reversible scope at the current store state."""

        self._next_checkpoint_token += 1
        token = self._next_checkpoint_token
        self._checkpoints.append(token)
        return FactStoreCheckpoint(id(self), token, len(self._trail))

    def rollback(self, checkpoint: FactStoreCheckpoint) -> None:
        """Undo mutations since *checkpoint* while keeping it reusable."""

        self._validate_checkpoint(checkpoint)
        while len(self._trail) > checkpoint.trail_size:
            mutation = self._trail.pop()
            if mutation.added:
                self._facts.pop(mutation.node.fact, None)
                self._unlink(mutation.node)
            else:
                self._relink(
                    mutation.node,
                    mutation.previous,
                    mutation.next,
                )
                self._facts[mutation.node.fact] = mutation.node

    def release(self, checkpoint: FactStoreCheckpoint) -> None:
        """Close *checkpoint* after its state is no longer needed."""

        self._validate_checkpoint(checkpoint)
        self._checkpoints.pop()
        if not self._checkpoints:
            self._trail.clear()

    def _validate_checkpoint(self, checkpoint: FactStoreCheckpoint) -> None:
        if (
            checkpoint.owner != id(self)
            or not self._checkpoints
            or self._checkpoints[-1] != checkpoint.token
            or checkpoint.trail_size > len(self._trail)
        ):
            raise ValueError("checkpoint is not the active store checkpoint")

    def _unlink(self, node: _FactNode) -> None:
        previous = node.previous
        next_node = node.next
        if previous is None:
            self._head = next_node
        else:
            previous.next = next_node
        if next_node is None:
            self._tail = previous
        else:
            next_node.previous = previous
        node.previous = None
        node.next = None

    def _relink(
        self,
        node: _FactNode,
        previous: _FactNode | None,
        next_node: _FactNode | None,
    ) -> None:
        node.previous = previous
        node.next = next_node
        if previous is None:
            self._head = node
        else:
            previous.next = node
        if next_node is None:
            self._tail = node
        else:
            next_node.previous = node

    def __contains__(self, fact: object) -> bool:
        return fact in self._facts

    def __iter__(self) -> Iterator[Fact]:
        node = self._head
        while node is not None:
            yield node.fact
            node = node.next

    def __len__(self) -> int:
        return len(self._facts)

    @property
    def facts(self) -> tuple[Fact, ...]:
        """Return a stable snapshot suitable for backtracking."""

        return tuple(self)
