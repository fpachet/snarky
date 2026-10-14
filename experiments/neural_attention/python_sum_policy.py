"""Opt-in pure-Python equality bounds and budgeted exact-support filtering.

Representation preflight and fallback remain NumericPlans' responsibility.
Bounds maintain mask-tagged contribution extrema and reconcile widening. Bounds
passes reach their own fixpoint before using NumericPlan's output-tag cache.
No installed solver default changes, no compiler or native library required.
"""

from collections import Counter

from snarky.finite.constraints import ConstraintOperator
from snarky.finite.numeric import NumericPlan, NumericPlans


class BudgetEqualityPlan(NumericPlan):
    def __init__(self, original, budget, mode, stats):
        super().__init__(original.columns, original.operator, original._domain_store)
        self.budget, self.mode, self.stats = budget, mode, stats
        self.bound_masks = [-1] * len(self.columns)
        self.lows, self.highs = [0] * len(self.columns), [0] * len(self.columns)
        self.lower = self.upper = 0

    def _bounds(self, masks, target):
        passes = 0
        while True:
            passes += 1
            for i, (column, mask) in enumerate(zip(self.columns, masks, strict=True)):
                if mask != self.bound_masks[i]:
                    low, high = column.extrema(mask)
                    self.lower += low - self.lows[i]
                    self.upper += high - self.highs[i]
                    self.lows[i], self.highs[i], self.bound_masks[i] = low, high, mask
            if not self.lower <= target <= self.upper:
                self.stats["bound_passes"] += passes
                return None
            result = tuple(
                column.threshold(
                    column.threshold(mask, target - self.lower + low, True),
                    target - self.upper + high,
                    False,
                )
                for column, mask, low, high in zip(
                    self.columns, masks, self.lows, self.highs, strict=True
                )
            )
            if not all(result):
                self.stats["bound_passes"] += passes
                return None
            if result == masks:
                self.stats["bound_passes"] += passes
                return result
            masks = result

    def _equality_supports(self, masks, target):
        self.stats["calls"] += 1
        if sum(bool(mask & (mask - 1)) for mask in masks) <= 2:
            self.stats["direct_exact_calls"] += 1
            return super()._equality_supports(masks, target)
        reduced = self._bounds(masks, target)
        if reduced is None:
            self.stats["bounds_failures"] += 1
            return None
        active = [mask.bit_count() for mask in reduced if mask & (mask - 1)]
        residual = min(target - self.lower, self.upper - target)
        # Python shifts operate on whole bigints. This proxy deliberately uses
        # a wider chunk than the C policy; thresholds are benchmarked separately.
        work = sum(active) * (1 + residual // 256)
        exact = (
            self.mode == "always"
            or len(active) <= 2
            or (self.mode == "budget" and work <= self.budget)
        )
        if exact:
            self.stats["exact_calls"] += 1
            return super()._equality_supports(reduced, target)
        self.stats["bounds_only"] += 1
        return reduced


class BudgetNumericPlans(NumericPlans):
    def __init__(self, domains, *, budget=4000, mode="budget", min_span=0):
        super().__init__(domains)
        if type(budget) is not int or budget < 0:
            raise ValueError("budget must be a nonnegative integer")
        if mode not in ("budget", "bounds", "always"):
            raise ValueError("unsupported equality policy")
        if type(min_span) is not int or min_span < 0:
            raise ValueError("min_span must be a nonnegative integer")
        self.budget, self.mode, self.min_span, self.stats = (
            budget,
            mode,
            min_span,
            Counter(),
        )

    def _compile(self, terms, operator):
        plan = super()._compile(terms, operator)
        if (
            plan is not None
            and operator is ConstraintOperator.EQUAL
            and len(plan.columns) > 2
        ):
            span = sum(c.ordered[-1] - c.ordered[0] for c in plan.columns)
            if span < self.min_span:
                self.stats["preserved_exact_plans"] += 1
                return plan
            self.stats["compiled_plans"] += 1
            return BudgetEqualityPlan(plan, self.budget, self.mode, self.stats)
        return plan


def enable(native, *, budget=4000, mode="budget", min_span=0):
    """Enable before propagation. Only eligible multi-column equalities change."""
    if native._initialized:
        raise ValueError("enable Python SUM policy before propagation")
    native._numeric = BudgetNumericPlans(
        native.domains, budget=budget, mode=mode, min_span=min_span
    )
    return native
