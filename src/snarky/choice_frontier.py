"""Traversal-specific pending storage for explicit choice search."""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol, runtime_checkable


class ChoiceTraversal(StrEnum):
    DEPTH_FIRST = "depth_first"
    BREADTH_FIRST = "breadth_first"
    BEST_FIRST = "best_first"


@runtime_checkable
class _BestFirstItem(Protocol):
    @property
    def log_weight(self) -> float: ...

    @property
    def insertion_order(self) -> int: ...


class _SearchFrontier[PendingT]:
    """Traversal-specific pending storage with a stable best-first heap."""

    def __init__(self, traversal: ChoiceTraversal) -> None:
        self.traversal = traversal
        self._items: list[PendingT] = []
        self._queue: deque[PendingT] = deque()
        self._heap: list[tuple[float, int, PendingT]] = []

    def push(self, item: PendingT) -> None:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            if not isinstance(item, _BestFirstItem):
                raise AssertionError("DFS frames cannot enter best-first")
            heapq.heappush(
                self._heap,
                (-item.log_weight, item.insertion_order, item),
            )
            return
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            self._queue.append(item)
            return
        self._items.append(item)

    def extend(self, items: Sequence[PendingT]) -> None:
        for item in items:
            self.push(item)

    def pop(self) -> PendingT:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            return heapq.heappop(self._heap)[2]
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return self._queue.popleft()
        return self._items.pop()

    def first(self) -> PendingT:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            return self._heap[0][2]
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return self._queue[0]
        return self._items[0]

    def __bool__(self) -> bool:
        if self.traversal is ChoiceTraversal.BEST_FIRST:
            return bool(self._heap)
        if self.traversal is ChoiceTraversal.BREADTH_FIRST:
            return bool(self._queue)
        return bool(self._items)
