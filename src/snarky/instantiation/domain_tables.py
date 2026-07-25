"""Compact extensional tables used by finite-domain filtering."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping, Sequence
from dataclasses import dataclass

from ..facts import Fact
from ..substitutions import BindingFrame
from ..terms import Term, Variable


@dataclass(frozen=True, slots=True)
class _DomainRow:
    fact: Fact
    bindings: tuple[tuple[Variable, Term], ...]

    def value(self, variable: Variable) -> Term:
        for candidate, value in self.bindings:
            if candidate == variable:
                return value
        raise KeyError(variable)

    def compatible(self, domains: Mapping[Variable, set[Term]]) -> bool:
        return all(
            value in domains[variable] for variable, value in self.bindings
        )


@dataclass(slots=True)
class _CompactTableDefinition:
    """Extensional rows plus bitset supports for each variable value."""

    rows: dict[Fact, _DomainRow]
    slots: list[_DomainRow | None]
    slot_by_fact: dict[Fact, int]
    support_masks: dict[Variable, dict[Term, int]]
    present_mask: int

    @classmethod
    def build(
        cls,
        rows: Mapping[Fact, _DomainRow],
        variables: Sequence[Variable],
    ) -> _CompactTableDefinition:
        table = cls(
            {},
            [],
            {},
            {variable: {} for variable in variables},
            0,
        )
        for row in rows.values():
            table.add(row)
        return table

    def __len__(self) -> int:
        return len(self.rows)

    def add(self, row: _DomainRow) -> int | None:
        if row.fact in self.rows:
            return None
        slot = len(self.slots)
        self.slots.append(row)
        bit = 1 << slot
        self.rows[row.fact] = row
        self.slot_by_fact[row.fact] = slot
        self.present_mask |= bit
        for variable, value in row.bindings:
            masks = self.support_masks[variable]
            masks[value] = masks.get(value, 0) | bit
        return bit

    def remove(self, fact: Fact) -> tuple[_DomainRow, int] | None:
        row = self.rows.pop(fact, None)
        if row is None:
            return None
        slot = self.slot_by_fact.pop(fact)
        bit = 1 << slot
        self.slots[slot] = None
        self.present_mask &= ~bit
        for variable, value in row.bindings:
            masks = self.support_masks[variable]
            remaining = masks[value] & ~bit
            if remaining:
                masks[value] = remaining
            else:
                del masks[value]
        return row, bit

    def facts(self, mask: int) -> tuple[Fact, ...]:
        selected = mask
        facts: list[Fact] = []
        while selected:
            bit = selected & -selected
            row = self.slots[bit.bit_length() - 1]
            if row is not None:
                facts.append(row.fact)
            selected ^= bit
        return tuple(facts)

    def rows_for_mask(self, mask: int) -> Iterator[_DomainRow]:
        while mask:
            bit = mask & -mask
            row = self.slots[bit.bit_length() - 1]
            if row is not None:
                yield row
            mask ^= bit

    def mask_for_frame(
        self,
        active_mask: int,
        variables: Sequence[Variable],
        frame: BindingFrame,
    ) -> tuple[int, int]:
        mask = active_mask
        intersections = 0
        for variable in variables:
            value = frame.value(variable)
            if value is None:
                continue
            mask &= self.support_masks[variable].get(value, 0)
            intersections += 1
            if not mask:
                break
        return mask, intersections


@dataclass(slots=True)
class _CompactTableState:
    """Branch-local masks derived from a shareable table definition."""

    active_mask: int
    applied_domains: dict[Variable, frozenset[Term]]

    @classmethod
    def initial(
        cls,
        definition: _CompactTableDefinition,
    ) -> _CompactTableState:
        return cls(definition.present_mask, {})

    def reset(self, definition: _CompactTableDefinition) -> None:
        self.active_mask = definition.present_mask
        self.applied_domains.clear()


def _add_row_projection(
    row: _DomainRow,
    counts: MutableMapping[Variable, dict[Term, int]],
    base_domains: MutableMapping[Variable, set[Term]] | None = None,
) -> None:
    for variable, value in row.bindings:
        value_counts = counts[variable]
        value_counts[value] = value_counts.get(value, 0) + 1
        if base_domains is not None:
            base_domains[variable].add(value)


def _remove_row_projection(
    row: _DomainRow,
    counts: MutableMapping[Variable, dict[Term, int]],
    base_domains: MutableMapping[Variable, set[Term]],
) -> None:
    for variable, value in row.bindings:
        value_counts = counts[variable]
        remaining = value_counts[value] - 1
        if remaining:
            value_counts[value] = remaining
            continue
        del value_counts[value]
        base_domains[variable].discard(value)
