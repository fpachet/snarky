"""Admissible min/max completion bounds from a bounded-window relaxation.

The immutable model is unchanged. A compiled bound includes all table objective
factors and only hard constraints fitting its window; other constraints are
relaxed. Domains are the current branch's domains. Cached edge costs depend only
on immutable model definitions and complete local assignments, never branch state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from time import perf_counter

from ..terms import Term
from .constraints import PersistentConstraint
from .factors import FactorObjective, TableFactor
from .model import FactConstraint, FiniteModel, GuardedConstraint, PredicateConstraint
from .predicates import accepts
from .product_assignment import ProductPermutationBound, supports_product_permutation
from .product_objective import (
    ProductChainBound,
    RationalProductObjective,
    supports_product_chain,
)


class NoObjectiveCompletion(Exception):
    """Even the relaxed problem has no completion; the branch is infeasible."""


type ObjectiveBound = Callable[
    [Mapping[Term, frozenset[Term]]], tuple[int | Fraction, int | Fraction] | None
]


@dataclass(frozen=True, slots=True)
class _Layer:
    variables: tuple[Term, ...]
    hard: tuple[PersistentConstraint, ...]
    factors: tuple[TableFactor, ...]


class ChainBound:
    """Min-plus/max-plus DP; no enumeration of complete configurations."""

    def __init__(
        self,
        model: FiniteModel,
        width: int,
        *,
        cache_limit: int,
        deadline: float | None = None,
    ) -> None:
        assert isinstance(model.objective, FactorObjective)
        self.names = tuple(var.name for var in model.variables)
        positions: dict[Term, int] = {var: i for i, var in enumerate(self.names)}
        tables = tuple(f for f in model.objective.factors if isinstance(f, TableFactor))
        self.offset = model.objective.offset + sum(
            f.contribution({}).value for f in tables if not f.variables
        )
        hard = tuple(
            c
            for c in model.constraints
            if not isinstance(
                c, (FactConstraint, GuardedConstraint, PredicateConstraint)
            )
        )
        self.layers = tuple(
            _Layer(
                self.names[max(0, time - width) : time + 1],
                tuple(
                    c
                    for c in hard
                    if max(positions[v] for v in c.variables) == time
                    and min(positions[v] for v in c.variables) >= time - width
                ),
                tuple(
                    f
                    for f in tables
                    if f.variables and max(positions[v] for v in f.variables) == time
                ),
            )
            for time in range(len(self.names))
        )
        self.width = width
        self.cache_limit = cache_limit
        self.deadline = deadline
        self._edges: dict[tuple[int, tuple[Term, ...]], int | None] = {}

    def _cost(self, time: int, values: tuple[Term, ...]) -> int | None:
        key = time, values
        if key in self._edges:
            return self._edges[key]
        layer = self.layers[time]
        assignment = dict(zip(layer.variables, values, strict=True))
        cost = (
            sum(f.contribution(assignment).value for f in layer.factors)
            if all(accepts(c, assignment) for c in layer.hard)
            else None
        )
        if len(self._edges) < self.cache_limit:
            self._edges[key] = cost
        return cost

    def __call__(self, domains: Mapping[Term, frozenset[Term]]) -> tuple[int, int]:
        current: dict[tuple[Term, ...], tuple[int, int]] = {
            (): (self.offset, self.offset)
        }
        for time, variable in enumerate(self.names):
            following: dict[tuple[Term, ...], tuple[int, int]] = {}
            for context, (lower, upper) in current.items():
                if self.deadline is not None and perf_counter() >= self.deadline:
                    raise TimeoutError("objective completion bound exceeded deadline")
                for value in domains[variable]:
                    values = (*context, value)
                    cost = self._cost(time, values)
                    if cost is None:
                        continue
                    target = values[-self.width :] if self.width else ()
                    low, high = lower + cost, upper + cost
                    if target in following:
                        previous = following[target]
                        low, high = min(low, previous[0]), max(high, previous[1])
                    following[target] = low, high
            if not following:
                raise NoObjectiveCompletion
            current = following
        return min(pair[0] for pair in current.values()), max(
            pair[1] for pair in current.values()
        )


def compile_objective_bound(
    model: FiniteModel,
    *,
    max_window: int = 2,
    max_edges: int = 100000,
    deadline: float | None = None,
    use_permutation: bool = True,
) -> ObjectiveBound:
    """Prefer an affordable chain relaxation; otherwise use the objective's bounds."""
    objective = model.objective
    if objective is None:
        return lambda domains: None
    if isinstance(objective, RationalProductObjective):
        if max_window >= 1 and supports_product_chain(model, max_edges):
            if use_permutation and supports_product_permutation(model):
                return ProductPermutationBound(model, deadline=deadline)
            return ProductChainBound(model, deadline=deadline)
        return objective.bounds
    if not isinstance(objective, FactorObjective) or any(
        not isinstance(f, TableFactor) for f in objective.factors
    ):
        return objective.bounds
    positions: dict[Term, int] = {v.name: i for i, v in enumerate(model.variables)}
    width = max(
        (
            max(positions[v] for v in f.variables)
            - min(positions[v] for v in f.variables)
            for f in objective.factors
            if f.variables
        ),
        default=0,
    )
    if width > max_window:
        return objective.bounds
    # Bound the compilation/state volume before allocating edge caches. This
    # estimate overcounts pruned states and is independent of the search branch.
    estimated = 0
    sizes = [len(v.domain) for v in model.variables]
    for time in range(len(sizes)):
        count = 1
        for size in sizes[max(0, time - width) : time + 1]:
            count *= size
        estimated += count
    if estimated > max_edges:
        return objective.bounds
    return ChainBound(model, width, cache_limit=max_edges, deadline=deadline)
