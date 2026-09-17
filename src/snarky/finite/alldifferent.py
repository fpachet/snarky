"""Exact all-different filtering in compiled candidate/value coordinates.

Matching is only a hint: every reuse validates its edges against current masks,
including after rollback. Domain reductions use the ordinary reversible store.
"""

from __future__ import annotations

from collections import deque

from ..terms import Term
from .constraints import AllDifferentConstraint
from .domains import FiniteDomains
from .kernels import _bit_components, _bit_reachable

_MAX_VALUES = 2048
_MAX_ENTRIES = 262144


def _sparse_components(graph: list[int], reverse: list[int], allowed: int) -> list[int]:
    """Iterative Kosaraju traversal; avoid repeated floods on long sparse chains."""
    unseen = allowed
    order = []
    while unseen:
        bit = unseen & -unseen
        unseen ^= bit
        vertex = bit.bit_length() - 1
        stack = [(vertex, graph[vertex] & allowed)]
        while stack:
            vertex, pending = stack[-1]
            pending &= unseen
            if not pending:
                order.append(vertex)
                stack.pop()
                continue
            bit = pending & -pending
            stack[-1] = (vertex, pending ^ bit)
            unseen ^= bit
            child = bit.bit_length() - 1
            stack.append((child, graph[child] & allowed))
    components = [0] * len(graph)
    unseen = allowed
    for vertex in reversed(order):
        if not unseen & (1 << vertex):
            continue
        component = _bit_reachable(reverse, 1 << vertex, unseen)
        unseen &= ~component
        pending = component
        while pending:
            bit = pending & -pending
            pending ^= bit
            components[bit.bit_length() - 1] = component
    return components


class MaskColumn:
    def __init__(self, positions: tuple[int, ...]) -> None:
        self.positions = positions
        self.offset = positions[0] if positions else 0
        self.shifted = positions == tuple(
            range(self.offset, self.offset + len(positions))
        )
        self.last_mask = 0
        self.last_values = 0

    def encode(self, mask: int) -> int:
        if self.shifted:
            return mask << self.offset
        changed = mask ^ self.last_mask
        while changed:
            bit = changed & -changed
            changed ^= bit
            self.last_values ^= 1 << self.positions[bit.bit_length() - 1]
        self.last_mask = mask
        return self.last_values

    def decode(self, mask: int, supported: int) -> int:
        if self.shifted:
            return mask & (supported >> self.offset)
        result = 0
        while mask:
            bit = mask & -mask
            mask ^= bit
            if supported & (1 << self.positions[bit.bit_length() - 1]):
                result |= bit
        return result


class AllDifferentPlan:
    def __init__(
        self, variables: tuple[Term, ...], columns: tuple[MaskColumn, ...], count: int
    ) -> None:
        self.variables = variables
        self.columns = columns
        self.matching = [-1] * len(variables)
        self.owners = [-1] * count
        self.last_supported: tuple[int, ...] | None = None

    def _match(self, masks: tuple[int, ...]) -> bool:
        # Retain valid matching edges across revisions and sibling branches.
        for variable, value in enumerate(self.matching):
            if value >= 0 and not masks[variable] & (1 << value):
                self.matching[variable] = -1
                self.owners[value] = -1
        occupied = 0
        for value in self.matching:
            if value >= 0:
                occupied |= 1 << value
        for start in sorted(range(len(masks)), key=lambda i: masks[i].bit_count()):
            if self.matching[start] >= 0:
                continue
            free = masks[start] & ~occupied
            if free:
                bit = free & -free
                value = bit.bit_length() - 1
                self.matching[start] = value
                self.owners[value] = start
                occupied |= bit
                continue
            # Breadth-first augmenting path. Parent entries also mark visited values.
            parents = [-1] * len(self.owners)
            pending = deque([start])
            seen = 0
            end = -1
            while pending and end < 0:
                variable = pending.popleft()
                choices = masks[variable] & ~seen
                seen |= choices
                while choices:
                    bit = choices & -choices
                    choices ^= bit
                    value = bit.bit_length() - 1
                    parents[value] = variable
                    owner = self.owners[value]
                    if owner < 0:
                        end = value
                        break
                    pending.append(owner)
            if end < 0:
                return False
            occupied |= 1 << end
            while end >= 0:
                variable = parents[end]
                previous = self.matching[variable]
                self.matching[variable] = end
                self.owners[end] = variable
                end = previous
        return True

    def supports(self, domains: FiniteDomains) -> tuple[int, ...] | None:
        local = tuple(domains.mask(v) for v in self.variables)
        if not all(local):
            return None
        if local == self.last_supported:
            return local
        masks = tuple(c.encode(m) for c, m in zip(self.columns, local, strict=True))
        universe = 0
        for mask in masks:
            universe |= mask
        if universe.bit_count() < len(masks) or not self._match(masks):
            return None
        graph = [0] * len(self.owners)
        reverse = [0] * len(self.owners)
        matched = 0
        edges = 0
        for value, mask in zip(self.matching, masks, strict=True):
            own = 1 << value
            matched |= own
            graph[value] = mask
            edges += mask.bit_count()
            pending = mask
            while pending:
                bit = pending & -pending
                pending ^= bit
                reverse[bit.bit_length() - 1] |= own
        reaches_free = _bit_reachable(reverse, universe & ~matched, universe)
        if reaches_free == universe:
            result = local
        else:
            component_fn = (
                _bit_components
                if universe.bit_count() <= 64 or edges >= 4 * universe.bit_count()
                else _sparse_components
            )
            components = component_fn(graph, reverse, universe & ~reaches_free)
            result = tuple(
                original
                if mask & ~(reaches_free | components[value] | (1 << value)) == 0
                else column.decode(
                    original, reaches_free | components[value] | (1 << value)
                )
                for column, original, mask, value in zip(
                    self.columns, local, masks, self.matching, strict=True
                )
            )
        self.last_supported = result
        return result


class AllDifferentPlans:
    def __init__(self, domains: FiniteDomains) -> None:
        self.domains = domains
        self.plans: dict[int, AllDifferentPlan | None] = {}
        self.entries = 0

    def get(
        self, index: int, constraint: AllDifferentConstraint
    ) -> AllDifferentPlan | None:
        if index not in self.plans:
            self.plans[index] = self._compile(constraint)
        return self.plans[index]

    def _compile(self, constraint: AllDifferentConstraint) -> AllDifferentPlan | None:
        alphabets = tuple(self.domains.alphabet(v) for v in constraint.variables)
        entries = sum(map(len, alphabets))
        if self.entries + entries > _MAX_ENTRIES:
            return None
        positions: dict[Term, int] = {}
        for alphabet in alphabets:
            for value in alphabet:
                if value not in positions:
                    if len(positions) == _MAX_VALUES:
                        return None
                    positions[value] = len(positions)
        columns = tuple(MaskColumn(tuple(positions[v] for v in a)) for a in alphabets)
        self.entries += entries
        return AllDifferentPlan(constraint.variables, columns, len(positions))
