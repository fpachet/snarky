"""Adaptive policy for selecting finite-domain filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from ..rules import Rule
from .domain_planning import _DomainPlan


class _FilterAssessment(StrEnum):
    SELECT = "select"
    REJECT = "reject"
    DEFER = "defer"
    PROBE = "probe"


@dataclass(slots=True)
class _AdaptiveFilterSelector:
    """Own adaptive thresholds and per-rule selection state."""

    enabled: bool = False
    minimum_domain_rows: int = 128
    minimum_bucket_ratio: float = 8.0
    minimum_candidate_reduction: float = 0.10
    minimum_observed_speedup: float = 1.05
    cost_probe_reduction_ceiling: float = 0.75
    minimum_cost_probe_uses: int = 8
    decisions: dict[Rule, bool] = field(default_factory=dict)
    cost_ratios: dict[Rule, float] = field(default_factory=dict)
    use_counts: dict[Rule, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.minimum_domain_rows < 1:
            raise ValueError("minimum_domain_rows must be positive")
        if self.minimum_bucket_ratio < 1:
            raise ValueError("minimum_bucket_ratio must be at least one")
        if not 0 <= self.minimum_candidate_reduction <= 1:
            raise ValueError(
                "minimum_candidate_reduction must be between zero and one"
            )
        if self.minimum_observed_speedup <= 0:
            raise ValueError("minimum_observed_speedup must be positive")
        if not 0 <= self.cost_probe_reduction_ceiling <= 1:
            raise ValueError(
                "cost_probe_reduction_ceiling must be between zero and one"
            )
        if self.minimum_cost_probe_uses < 1:
            raise ValueError("minimum_cost_probe_uses must be positive")

    def decision(self, rule: Rule) -> bool | None:
        return self.decisions.get(rule)

    def select(self, rule: Rule) -> None:
        self.decisions[rule] = True

    def reject(self, rule: Rule) -> None:
        self.decisions[rule] = False

    def accepts_shape(
        self,
        plan: _DomainPlan,
        fact_count: int,
        *,
        comparisons_supported: bool,
    ) -> bool:
        if (
            plan.comparisons
            and not comparisons_supported
        ):
            return False
        if (
            not plan.comparisons
            and (len(plan.tables) < 3 or not plan.cyclic)
        ):
            return False
        return (
            fact_count * len(plan.tables)
            >= self.minimum_domain_rows
        )

    def accepts_tables(
        self,
        plan: _DomainPlan,
        sizes: tuple[int, ...],
        *,
        comparisons_supported: bool,
    ) -> bool:
        if not sizes or sum(sizes) < self.minimum_domain_rows:
            return False
        if any(size == 0 for size in sizes):
            return True
        if plan.comparisons:
            return comparisons_supported
        return (
            len(sizes) >= 3
            and plan.cyclic
            and max(sizes) / min(sizes) >= self.minimum_bucket_ratio
        )

    def assess(
        self,
        rule: Rule,
        *,
        row_count: int,
        retained_count: int,
        consistent: bool,
    ) -> _FilterAssessment:
        reduction = (
            1 - retained_count / row_count if row_count else 0.0
        )
        if not consistent:
            self.select(rule)
            return _FilterAssessment.SELECT
        if reduction < self.minimum_candidate_reduction:
            self.reject(rule)
            return _FilterAssessment.REJECT
        if reduction >= self.cost_probe_reduction_ceiling:
            self.select(rule)
            return _FilterAssessment.SELECT
        uses = self.use_counts.get(rule, 0) + 1
        self.use_counts[rule] = uses
        if uses >= self.minimum_cost_probe_uses:
            return _FilterAssessment.PROBE
        return _FilterAssessment.DEFER

    def record_probe(
        self,
        rule: Rule,
        *,
        filter_elapsed: float,
        fallback_elapsed: float,
    ) -> bool:
        observed_speedup = (
            fallback_elapsed / filter_elapsed
            if filter_elapsed
            else float("inf")
        )
        self.cost_ratios[rule] = observed_speedup
        selected = observed_speedup >= self.minimum_observed_speedup
        self.decisions[rule] = selected
        return selected

    def clear(self) -> None:
        self.decisions.clear()
        self.cost_ratios.clear()
        self.use_counts.clear()
