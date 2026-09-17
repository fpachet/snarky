"""Exact multiplicative assignment relaxation for permutation chain objectives."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from math import prod
from time import perf_counter

from ..terms import Term
from .constraints import AllDifferentConstraint
from .model import FiniteModel
from .product_objective import ProductChainBound


def maximum_product_assignment(
    weights: Sequence[Sequence[Fraction]], *, deadline: float | None = None
) -> Fraction:
    """Maximum product perfect matching; zero means no positive matching.

    Hungarian shortest augmenting paths over the ordered multiplicative group of
    positive rationals. Multiplication/division replace addition/subtraction of
    logarithmic costs, so comparisons and the returned optimum are exact. Zero
    edges are absent. Empty matching has product one. No floating logs are used.
    """
    n = len(weights)
    if any(len(row) != n for row in weights):
        raise ValueError("assignment weights must be square")
    if any(weight < 0 for row in weights for weight in row):
        raise ValueError("assignment weights must be nonnegative")
    u = [Fraction(1)] * (n + 1)
    v = [Fraction(1)] * (n + 1)
    matching = [0] * (n + 1)
    previous = [0] * (n + 1)
    for row in range(1, n + 1):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("product assignment bound time limit")
        matching[0] = row
        column = 0
        distances: list[Fraction | None] = [None] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[column] = True
            current_row = matching[column]
            delta = None
            following = 0
            for candidate in range(1, n + 1):
                if used[candidate]:
                    continue
                weight = weights[current_row - 1][candidate - 1]
                distance = distances[candidate]
                if weight:
                    reduced = 1 / (weight * u[current_row] * v[candidate])
                    if distance is None or reduced < distance:
                        distance = reduced
                        distances[candidate] = distance
                        previous[candidate] = column
                if distance is not None and (delta is None or distance < delta):
                    delta = distance
                    following = candidate
            if delta is None:
                return Fraction(0)
            for candidate in range(n + 1):
                if used[candidate]:
                    u[matching[candidate]] *= delta
                    v[candidate] /= delta
                elif (distance := distances[candidate]) is not None:
                    distances[candidate] = distance / delta
            column = following
            if matching[column] == 0:
                break
        while column:
            following = previous[column]
            matching[column] = matching[following]
            column = following
    return prod(
        (weights[matching[column] - 1][column - 1] for column in range(1, n + 1)),
        start=Fraction(1),
    )


def supports_product_permutation(model: FiniteModel, *, max_symbols: int = 64) -> bool:
    """Require a small whole-alphabet permutation and fixed distinct endpoints."""
    variables = model.variables
    if not 2 <= len(variables) <= max_symbols or len(variables[0].domain) != 1:
        return False
    if len(variables[-1].domain) != 1:
        return False
    if variables[0].domain == variables[-1].domain:
        return False
    names = frozenset(v.name for v in variables)
    alphabet = {value for v in variables for value in v.domain}
    return len(alphabet) == len(variables) and any(
        isinstance(c, AllDifferentConstraint)
        and len(c.variables) == len(names)
        and frozenset(c.variables) == names
        for c in model.constraints
    )


class ProductPermutationBound(ProductChainBound):
    """Upper bound from successor/predecessor matching, relaxing cycles/positions.

    Every feasible permutation path induces a perfect matching from all symbols
    except the fixed end to all symbols except the fixed start. For each edge use
    its maximum weight over currently compatible adjacent positions. Multiplying
    the best matching by the fixed initial factor and constant bounds every path.
    Unary and position-dependent pair factors are already folded into the edges.
    Other hard constraints are relaxed. Zero bounds do not imply infeasibility.
    """

    def __init__(self, model: FiniteModel, *, deadline: float | None = None) -> None:
        super().__init__(model, deadline=deadline)
        self.alphabet = tuple(
            dict.fromkeys(x for v in model.variables for x in v.domain)
        )
        self.index = {value: i for i, value in enumerate(self.alphabet)}
        start, end = model.variables[0].domain[0], model.variables[-1].domain[0]
        self.rows = tuple(i for i, value in enumerate(self.alphabet) if value != end)
        self.columns = tuple(
            i for i, value in enumerate(self.alphabet) if value != start
        )
        self.initial = self.constant * dict(self.edges[0].get(None, ())).get(
            start, Fraction(0)
        )
        self.indexed_edges = tuple(
            tuple(
                (self.index[left], self.index[right], weight)
                for left, successors in layer.items()
                for right, weight in successors
                if left is not None and left != right and left != end and right != start
            )
            for layer in self.edges[1:]
        )

    def __call__(
        self, domains: Mapping[Term, frozenset[Term]]
    ) -> tuple[Fraction, Fraction]:
        masks = [sum(1 << self.index[x] for x in domains[name]) for name in self.names]
        fixed = 0
        for mask in masks:
            if mask == 0:
                return Fraction(0), Fraction(0)
            if mask.bit_count() == 1:
                if fixed & mask:
                    return Fraction(0), Fraction(0)
                fixed |= mask
        # Value ranking calls bounds before propagation. Apply the elementary
        # all-different consequences of singletons here as well.
        masks = [m if m.bit_count() == 1 else m & ~fixed for m in masks]
        n = len(self.alphabet)
        weights = [[Fraction(0)] * n for _ in range(n)]
        for position, edges in enumerate(self.indexed_edges):
            if self.deadline is not None and perf_counter() >= self.deadline:
                raise TimeoutError("permutation bound time limit")
            left_mask, right_mask = masks[position : position + 2]
            for left, right, weight in edges:
                if (left_mask >> left) & 1 and (right_mask >> right) & 1:
                    weights[left][right] = max(weights[left][right], weight)
        matching = maximum_product_assignment(
            [[weights[i][j] for j in self.columns] for i in self.rows],
            deadline=self.deadline,
        )
        return Fraction(0), self.initial * matching
