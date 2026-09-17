"""Compiled integer contributions and exact supports in candidate-mask coordinates.

Only inequalities and unary/binary equalities use this path. Other equalities
and noninteger alphabets retain the reference kernels. Caches are mask-tagged,
not search-depth-tagged, so rollback needs no cache trail.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right

from ..terms import Number, Term
from .constraints import ConstraintOperator, LinearSumConstraint, SumConstraint
from .domains import FiniteDomains

# Bound extra compiled entries, not the domain store or integer magnitudes.
_MAX_COLUMN = 4096
_MAX_ENTRIES = 262144


class NumericColumn:
    def __init__(self, variable: Term, contributions: tuple[int, ...]) -> None:
        self.variable = variable
        self.values = contributions
        self.positions = {value: i for i, value in enumerate(contributions)}
        self.ascending = all(
            a <= b for a, b in zip(contributions, contributions[1:], strict=False)
        )
        self.descending = all(
            a >= b for a, b in zip(contributions, contributions[1:], strict=False)
        )
        self.ordered = contributions if self.ascending else contributions[::-1]
        self.last_mask = -1
        self.last_extrema = (0, 0)

    def extrema(self, mask: int) -> tuple[int, int]:
        if mask != self.last_mask:
            if self.ascending or self.descending:
                first = self.values[(mask & -mask).bit_length() - 1]
                last = self.values[mask.bit_length() - 1]
                self.last_extrema = (first, last) if self.ascending else (last, first)
            else:
                pending = mask
                low = high = self.values[(mask & -mask).bit_length() - 1]
                while pending:
                    bit = pending & -pending
                    pending ^= bit
                    value = self.values[bit.bit_length() - 1]
                    low, high = min(low, value), max(high, value)
                self.last_extrema = (low, high)
            self.last_mask = mask
        return self.last_extrema

    def threshold(self, mask: int, bound: int, upper: bool) -> int:
        low, high = self.extrema(mask)
        if (high <= bound) if upper else (low >= bound):
            return mask
        if self.ascending or self.descending:
            count = (bisect_right if upper else bisect_left)(self.ordered, bound)
            prefix = (1 << count) - 1
            if self.descending:
                prefix <<= len(self.values) - count
            # Complement is intersected with the finite current mask.
            return mask & (prefix if upper else ~prefix)
        result = 0
        while mask:
            bit = mask & -mask
            mask ^= bit
            value = self.values[bit.bit_length() - 1]
            if (value <= bound) if upper else (value >= bound):
                result |= bit
        return result


class NumericPlan:
    def __init__(
        self, columns: tuple[NumericColumn, ...], operator: ConstraintOperator
    ) -> None:
        self.columns = columns
        self.operator = operator
        self.last_masks = [-1] * len(columns)
        self.extrema = [0] * len(columns)
        self.total = 0

    def supports(self, domains: FiniteDomains, target: int) -> tuple[int, ...] | None:
        masks = tuple(domains.mask(c.variable) for c in self.columns)
        if not all(masks):
            return None
        if self.operator is ConstraintOperator.EQUAL:
            if len(masks) == 1:
                index = self.columns[0].positions.get(target)
                mask = 0 if index is None else masks[0] & (1 << index)
                return (mask,) if mask else None
            left, right = (
                (0, 1) if masks[0].bit_count() <= masks[1].bit_count() else (1, 0)
            )
            pending = masks[left]
            supported = [0, 0]
            while pending:
                bit = pending & -pending
                pending ^= bit
                value = self.columns[left].values[bit.bit_length() - 1]
                index = self.columns[right].positions.get(target - value)
                if index is not None:
                    other = (1 << index) & masks[right]
                    if other:
                        supported[left] |= bit
                        supported[right] |= other
            return tuple(supported) if all(supported) else None
        upper = self.operator is ConstraintOperator.LESS_EQUAL
        for i, (column, mask) in enumerate(zip(self.columns, masks, strict=True)):
            if mask != self.last_masks[i]:
                value = column.extrema(mask)[0 if upper else 1]
                self.total += value - self.extrema[i]
                self.extrema[i] = value
                self.last_masks[i] = mask
        if (self.total > target) if upper else (self.total < target):
            return None
        return tuple(
            column.threshold(mask, target - self.total + own, upper)
            for column, mask, own in zip(self.columns, masks, self.extrema, strict=True)
        )


class NumericPlans:
    """Per-state immutable column sharing and bounded, lazy plan compilation."""

    def __init__(self, domains: FiniteDomains) -> None:
        self.domains = domains
        self.columns: dict[tuple[Term, int], NumericColumn] = {}
        self.plans: dict[
            int, tuple[LinearSumConstraint | SumConstraint, NumericPlan | None]
        ] = {}
        self.entries = 0

    def get(
        self, index: int, constraint: LinearSumConstraint | SumConstraint
    ) -> NumericPlan | None:
        if not isinstance(constraint.target, int):
            return None
        previous = self.plans.get(index)
        if previous is not None and previous[0] is constraint:
            return previous[1]
        terms = (
            constraint.terms
            if isinstance(constraint, LinearSumConstraint)
            else tuple((1, v) for v in constraint.variables)
        )
        operator = (
            constraint.operator
            if isinstance(constraint, LinearSumConstraint)
            else ConstraintOperator.EQUAL
        )
        if (
            previous is not None
            and isinstance(previous[0], LinearSumConstraint)
            and isinstance(constraint, LinearSumConstraint)
            and previous[0].terms == terms
            and previous[0].operator == operator
        ):
            # Incumbent targets change; their coefficients and candidate indexes do not.
            plan = previous[1]
        else:
            plan = self._compile(terms, operator)
        self.plans[index] = (constraint, plan)
        return plan

    def _compile(
        self, terms: tuple[tuple[int, Term], ...], operator: ConstraintOperator
    ) -> NumericPlan | None:
        if not terms or (operator is ConstraintOperator.EQUAL and len(terms) > 2):
            return None
        columns = []
        for coefficient, variable in terms:
            key = (variable, coefficient)
            column = self.columns.get(key)
            if column is None:
                alphabet = self.domains.alphabet(variable)
                if (
                    len(alphabet) > _MAX_COLUMN
                    or self.entries + len(alphabet) > _MAX_ENTRIES
                ):
                    return None
                # Decline, rather than validate early: an inactive guard or values
                # removed before first revision must retain reference semantics.
                if any(
                    not isinstance(v, Number) or not isinstance(v.value, int)
                    for v in alphabet
                ):
                    return None
                values = tuple(
                    coefficient * v.value
                    for v in alphabet
                    if isinstance(v, Number) and isinstance(v.value, int)
                )
                column = self.columns[key] = NumericColumn(variable, values)
                self.entries += len(alphabet)
            columns.append(column)
        return NumericPlan(tuple(columns), operator)
