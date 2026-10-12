"""Compiled integer contributions and exact supports in candidate-mask coordinates.

Inequalities and bounded-span integer equalities use this path. Wider equalities
and noninteger alphabets retain the reference kernels. Caches are mask-tagged,
not search-depth-tagged, so rollback needs no cache trail.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right

from ..terms import Number, Term
from .constraints import (
    AnyOfConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from .domains import FiniteDomains

# Bound extra compiled entries, not the domain store or integer magnitudes.
_MAX_COLUMN = 4096
_MAX_ENTRIES = 262144
_MAX_EQUALITY_SPAN = 4096
_MAX_EQUALITY_TOTAL_BITS = 1_048_576


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
        self.equal_masks: tuple[int, ...] | None = None
        self.equal_target: int | None = None
        self.equal_result: tuple[int, ...] | None = None

    def supports(self, domains: FiniteDomains, target: int) -> tuple[int, ...] | None:
        masks = tuple(domains.mask(c.variable) for c in self.columns)
        if not all(masks):
            return None
        if self.operator is ConstraintOperator.EQUAL:
            if len(masks) > 2:
                if masks == self.equal_masks and target == self.equal_target:
                    return self.equal_result
                result = self._equality_supports(masks, target)
                # Exact supports are a fixpoint. Tag successful results with the
                # filtered masks, including after rollback or sibling visits.
                self.equal_masks = masks if result is None else result
                self.equal_target = target
                self.equal_result = result
                return result
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

    def _equality_supports(
        self, masks: tuple[int, ...], target: int
    ) -> tuple[int, ...] | None:
        extrema = [c.extrema(m) for c, m in zip(self.columns, masks, strict=True)]
        lower = sum(low for low, _ in extrema)
        span = sum(high - low for low, high in extrema)
        residual = target - lower
        if not 0 <= residual <= span:
            return None
        # Fixed terms contribute only to the residual. Avoid building arithmetic
        # tables for them, and use direct supports near a line's completion.
        active = [i for i, mask in enumerate(masks) if mask & (mask - 1)]
        if not active:
            return masks
        if len(active) == 1:
            index = active[0]
            position = self.columns[index].positions.get(
                target - lower + extrema[index][0]
            )
            support_mask = 0 if position is None else masks[index] & (1 << position)
            if not support_mask:
                return None
            result = list(masks)
            result[index] = support_mask
            return tuple(result)
        if len(active) == 2:
            left, right = sorted(active, key=lambda i: masks[i].bit_count())
            remaining = target - lower + extrema[left][0] + extrema[right][0]
            pending = masks[left]
            result = list(masks)
            result[left] = result[right] = 0
            while pending:
                bit = pending & -pending
                pending ^= bit
                value = self.columns[left].values[bit.bit_length() - 1]
                position = self.columns[right].positions.get(remaining - value)
                if position is not None:
                    other = masks[right] & (1 << position)
                    if other:
                        result[left] |= bit
                        result[right] |= other
            return tuple(result) if result[left] else None
        # Normalizing current minima handles signed coefficients and enormous
        # translations without using absolute integer magnitudes as bit indexes.
        reflect = residual > span - residual
        if reflect:
            residual = span - residual
        candidates = []
        for index in active:
            column, mask = self.columns[index], masks[index]
            low, high = extrema[index]
            offsets = []
            while mask:
                bit = mask & -mask
                mask ^= bit
                value = column.values[bit.bit_length() - 1]
                shifted = high - value if reflect else value - low
                if shifted <= residual:
                    offsets.append((bit, shifted))
            candidates.append(offsets)
        limit = (1 << (residual + 1)) - 1
        prefix = [1]
        for offsets in candidates:
            reachable = 0
            for _, shifted in offsets:
                reachable |= prefix[-1] << shifted
            prefix.append(reachable & limit)
        if not prefix[-1] & (1 << residual):
            return None
        backward = 1 << residual
        supported = list(masks)
        for index in range(len(active) - 1, -1, -1):
            reachable = 0
            variable = active[index]
            supported[variable] = 0
            for bit, shifted in candidates[index]:
                suffix = backward >> shifted
                if prefix[index] & suffix:
                    supported[variable] |= bit
                    reachable |= suffix
            backward = reachable
        return tuple(supported)


class NumericPlans:
    """Per-state immutable column sharing and bounded, lazy plan compilation."""

    def __init__(self, domains: FiniteDomains) -> None:
        self.domains = domains
        self.columns: dict[tuple[Term, int], NumericColumn] = {}
        self.plans: dict[
            int, tuple[LinearSumConstraint | SumConstraint, NumericPlan | None]
        ] = {}
        self.entries = 0
        self.disjunctions: dict[
            int, tuple[AnyOfConstraint, NumericDisjunction | None]
        ] = {}

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

    def disjunction(
        self, index: int, constraint: AnyOfConstraint
    ) -> NumericDisjunction | None:
        previous = self.disjunctions.get(index)
        if previous is not None and previous[0] is constraint:
            return previous[1]
        plan = None
        alternatives = constraint.alternatives
        if len(alternatives) == 2 and all(
            isinstance(c, LinearSumConstraint) for c in alternatives
        ):
            left, right = alternatives
            assert isinstance(left, LinearSumConstraint)
            assert isinstance(right, LinearSumConstraint)
            if len(left.terms) == 2 and set(left.variables) == set(right.variables):
                a = self._compile(left.terms, left.operator)
                b = self._compile(right.terms, right.operator)
                if a is not None and b is not None:
                    plan = NumericDisjunction((a, b))
        self.disjunctions[index] = (constraint, plan)
        return plan

    def _compile(
        self, terms: tuple[tuple[int, Term], ...], operator: ConstraintOperator
    ) -> NumericPlan | None:
        if not terms:
            return None
        if operator is ConstraintOperator.EQUAL and len(terms) > 2:
            # Preflight representation limits before publishing any columns.
            # Sparse huge spans retain the existing exact sparse/GCD fallback.
            span = 0
            for coefficient, variable in terms:
                alphabet = self.domains.alphabet(variable)
                if not alphabet or any(
                    not isinstance(v, Number) or not isinstance(v.value, int)
                    for v in alphabet
                ):
                    return None
                contributions = [
                    coefficient * v.value
                    for v in alphabet
                    if isinstance(v, Number) and isinstance(v.value, int)
                ]
                span += max(contributions) - min(contributions)
                if span > _MAX_EQUALITY_SPAN:
                    return None
            if (span + 1) * (len(terms) + 2) > _MAX_EQUALITY_TOTAL_BITS:
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


class NumericDisjunction:
    """Exact union of two local numeric support sets; never prune an OR branch.

    Both alternatives must cover the same two variables. Keeping alternative
    supports separate is essential: applying either to global domains would turn
    a disjunction into a conjunction. Mask-tagged caches remain rollback-safe.
    """

    def __init__(self, plans: tuple[NumericPlan, NumericPlan]) -> None:
        self.plans = plans
        self.variables = tuple(c.variable for c in plans[0].columns)
        self.positions = tuple(
            tuple(self.variables.index(c.variable) for c in p.columns) for p in plans
        )

    def supports(
        self, domains: FiniteDomains, targets: tuple[int, int]
    ) -> tuple[int, ...] | None:
        union = [0, 0]
        for plan, positions, target in zip(
            self.plans, self.positions, targets, strict=True
        ):
            supported = plan.supports(domains, target)
            if supported is not None:
                for position, mask in zip(positions, supported, strict=True):
                    union[position] |= mask
        return tuple(union) if all(union) else None
