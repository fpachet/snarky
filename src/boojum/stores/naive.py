"""Deterministic scan-based fact store used as the reference implementation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from ..facts import Fact


class NaiveFactStore:
    """An insertion-ordered set of facts supporting multiple statuses."""

    __slots__ = ("_facts",)

    def __init__(self, facts: Iterable[Fact] = ()) -> None:
        self._facts: dict[Fact, None] = {}
        for fact in facts:
            self.add(fact)

    def add(self, fact: Fact) -> bool:
        """Add *fact* and report whether it was new."""

        if fact in self._facts:
            return False
        self._facts[fact] = None
        return True

    def __contains__(self, fact: object) -> bool:
        return fact in self._facts

    def __iter__(self) -> Iterator[Fact]:
        return iter(self._facts)

    def __len__(self) -> int:
        return len(self._facts)

    @property
    def facts(self) -> tuple[Fact, ...]:
        """Return a stable snapshot suitable for backtracking."""

        return tuple(self._facts)
