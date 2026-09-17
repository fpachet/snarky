"""Exact nonnegative rational-product objectives, independent of sampling measures."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from math import prod
from time import perf_counter
from typing import TYPE_CHECKING

from ..facts import Fact
from ..terms import Term
from .constraints import ConstraintOperator, CountConstraint
from .measure import WeightTable

if TYPE_CHECKING:
    from .model import FiniteModel


@dataclass(frozen=True, slots=True)
class RationalProductObjective:
    """Multiply exact nonnegative weight tables; absent rows use their defaults.

    Zero weight is a valid objective value, not a hard prohibition. Add hard
    tables separately when missing transitions must make a sequence infeasible.
    A product objective is not implicitly a normalized probability measure.
    """

    factors: tuple[WeightTable, ...] = ()

    def __post_init__(self) -> None:
        factors = tuple(self.factors)
        if any(not isinstance(factor, WeightTable) for factor in factors):
            raise TypeError("product objectives require WeightTable factors")
        if len({factor.name for factor in factors}) != len(factors):
            raise ValueError("duplicate product objective factor names")
        object.__setattr__(self, "factors", factors)

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(
            dict.fromkeys(v for factor in self.factors for v in factor.variables)
        )

    def evaluate(
        self, assignment: Mapping[Term, Term], facts: frozenset[Fact] = frozenset()
    ) -> Fraction:
        return prod((f.weight(assignment) for f in self.factors), start=Fraction(1))

    def bounds(
        self, domains: Mapping[Term, frozenset[Term]]
    ) -> tuple[Fraction, Fraction]:
        lower = upper = Fraction(1)
        for factor in self.factors:
            rows = [
                Fraction(value)
                for row, value in factor.values.items()
                if all(
                    value in domains[var]
                    for var, value in zip(factor.variables, row, strict=True)
                )
            ]
            possible = prod(len(domains[var]) for var in factor.variables)
            if possible == 0:
                return Fraction(0), Fraction(0)
            if len(rows) < possible:
                rows.append(Fraction(factor.default))
            lower *= min(rows)
            upper *= max(rows)
        return lower, upper


class ProductChainBound:
    """Exact max-product relaxation for unary/adjacent-pair factors.

    Hard constraints are relaxed except one small equality count, if present.
    The current domains are respected. A zero upper
    bound means no positive-weight path, not infeasibility. The lower bound of
    zero is deliberately conservative for minimization. Only positive edges need
    storage. Topology is immutable; messages are rebuilt for each domain snapshot.
    """

    def __init__(self, model: FiniteModel, *, deadline: float | None = None) -> None:
        assert isinstance(model.objective, RationalProductObjective)
        self.names = tuple(v.name for v in model.variables)
        self.deadline = deadline
        self.constant = Fraction(1)
        self.counter = next(
            (
                c
                for c in model.constraints
                if isinstance(c, CountConstraint)
                and c.operator is ConstraintOperator.EQUAL
                and 0 <= c.target <= 4
            ),
            None,
        )
        self.counted_scope = (
            frozenset(self.counter.variables) if self.counter else frozenset()
        )
        layers: list[list[WeightTable]] = [[] for _ in self.names]
        positions: dict[Term, int] = {name: i for i, name in enumerate(self.names)}
        for factor in model.objective.factors:
            if not factor.variables:
                self.constant *= factor.weight({})
            else:
                layers[max(positions[v] for v in factor.variables)].append(factor)
        self.edges: list[dict[Term | None, tuple[tuple[Term, Fraction], ...]]] = []
        for i, variable in enumerate(model.variables):
            previous = model.variables[i - 1].domain if i else (None,)
            # A zero-default pair factor gives a sparse superset of every
            # positive edge. Other factors can only remove or reweight edges.
            support = _sparse_pair(layers[i])
            candidates: dict[Term | None, list[Term]] | None = None
            if support is not None:
                candidates = {}
                left_index = support.variables.index(self.names[i - 1])
                for row, value in support.values.items():
                    if value:
                        candidates.setdefault(row[left_index], []).append(
                            row[1 - left_index]
                        )
            right_domain = frozenset(variable.domain)
            adjacency = {}
            for left in previous:
                if deadline is not None and perf_counter() >= deadline:
                    raise TimeoutError("product bound compilation time limit")
                successors = []
                rights = (
                    variable.domain if candidates is None else candidates.get(left, ())
                )
                for right in rights:
                    if right not in right_domain:
                        continue
                    assignment: dict[Term, Term] = {variable.name: right}
                    if i:
                        assert left is not None
                        assignment[self.names[i - 1]] = left
                    weight = prod(
                        (factor.weight(assignment) for factor in layers[i]),
                        start=Fraction(1),
                    )
                    if weight:
                        successors.append((right, weight))
                adjacency[left] = tuple(successors)
            self.edges.append(adjacency)

    def __call__(
        self, domains: Mapping[Term, frozenset[Term]]
    ) -> tuple[Fraction, Fraction]:
        if not self.names:
            return self.constant, self.constant
        current: dict[tuple[Term | None, int], Fraction] = {(None, 0): self.constant}
        for i, variable in enumerate(self.names):
            following: dict[tuple[Term | None, int], Fraction] = {}
            for (left, count), partial in current.items():
                if self.deadline is not None and perf_counter() >= self.deadline:
                    raise TimeoutError("product completion bound time limit")
                for right, weight in self.edges[i].get(left, ()):
                    if right in domains[variable]:
                        next_count = count + int(
                            self.counter is not None
                            and variable in self.counted_scope
                            and right == self.counter.value
                        )
                        if (
                            self.counter is not None
                            and next_count > self.counter.target
                        ):
                            continue
                        value = partial * weight
                        key = right, next_count
                        if value > following.get(key, Fraction(-1)):
                            following[key] = value
            if not following:
                return Fraction(0), Fraction(0)
            current = following
        return Fraction(0), max(
            (
                value
                for (_, count), value in current.items()
                if self.counter is None or count == self.counter.target
            ),
            default=Fraction(0),
        )


def supports_product_chain(model: FiniteModel, max_edges: int) -> bool:
    """Bound preparation volume and admit only factors local to adjacent positions."""
    assert isinstance(model.objective, RationalProductObjective)
    positions: dict[Term, int] = {v.name: i for i, v in enumerate(model.variables)}
    for factor in model.objective.factors:
        indices = [positions[v] for v in factor.variables]
        if indices and max(indices) - min(indices) > 1:
            return False
    sizes = [len(v.domain) for v in model.variables]
    volume = 0
    for i, size in enumerate(sizes):
        dense = size * (sizes[i - 1] if i else 1)
        layer = [
            f
            for f in model.objective.factors
            if f.variables and max(positions[v] for v in f.variables) == i
        ]
        sparse = _sparse_pair(layer)
        volume += min(dense, len(sparse.values)) if sparse is not None else dense
    return volume <= max_edges


def _sparse_pair(factors: list[WeightTable]) -> WeightTable | None:
    return min(
        (f for f in factors if len(f.variables) == 2 and not f.default),
        key=lambda f: len(f.values),
        default=None,
    )
