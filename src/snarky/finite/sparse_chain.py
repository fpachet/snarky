"""Sparse min/max-sum relaxation for adjacent table factors and hard tables."""

from __future__ import annotations

from collections.abc import Mapping
from math import prod
from time import perf_counter

from ..terms import Term
from .constraints import TableConstraint
from .factors import FactorObjective, TableFactor
from .model import FiniteModel


def _layers(model: FiniteModel) -> tuple[tuple[TableConstraint, ...], ...]:
    positions: dict[Term, int] = {v.name: i for i, v in enumerate(model.variables)}
    layers: list[list[TableConstraint]] = [[] for _ in model.variables]
    for constraint in model.constraints:
        if isinstance(constraint, TableConstraint):
            indices = [positions[v] for v in constraint.variables]
            if indices and max(indices) - min(indices) <= 1:
                layers[max(indices)].append(constraint)
    return tuple(tuple(layer) for layer in layers)


def _pair(layer: tuple[TableConstraint, ...]) -> TableConstraint | None:
    return min(
        (c for c in layer if len(c.variables) == 2),
        key=lambda c: len(c.allowed),
        default=None,
    )


def supports_sparse_sum(model: FiniteModel, max_edges: int) -> bool:
    """Caller has already checked that all factors are unary or adjacent pairs."""
    volume = 0
    sparse = False
    for i, layer in enumerate(_layers(model)):
        dense = prod(len(v.domain) for v in model.variables[max(0, i - 1) : i + 1])
        pair = _pair(layer)
        sparse |= pair is not None
        volume += min(dense, len(pair.allowed)) if pair is not None else dense
    return sparse and volume <= max_edges


class SparseSumChainBound:
    """Exact bounds for the chain relaxation; nonlocal constraints are omitted."""

    def __init__(self, model: FiniteModel, *, deadline: float | None = None) -> None:
        assert isinstance(model.objective, FactorObjective)
        self.names = tuple(v.name for v in model.variables)
        self.deadline = deadline
        self.offset = model.objective.offset
        positions: dict[Term, int] = {v: i for i, v in enumerate(self.names)}
        factors: list[list[TableFactor]] = [[] for _ in self.names]
        for factor in model.objective.factors:
            assert isinstance(factor, TableFactor)
            if factor.variables:
                factors[max(positions[v] for v in factor.variables)].append(factor)
            else:
                self.offset += factor.contribution({}).value
        self.edges: list[dict[Term | None, tuple[tuple[Term, int], ...]]] = []
        for i, layer in enumerate(_layers(model)):
            variable = model.variables[i]
            previous = model.variables[i - 1].domain if i else (None,)
            pair = _pair(layer)
            candidates: dict[Term | None, list[Term]] | None = None
            if pair is not None:
                candidates = {}
                left_index = pair.variables.index(self.names[i - 1])
                for row in pair.allowed:
                    candidates.setdefault(row[left_index], []).append(
                        row[1 - left_index]
                    )
            hard = [(c.variables, frozenset(c.allowed)) for c in layer]
            adjacency = {}
            domain = frozenset(variable.domain)
            for left in previous:
                if deadline is not None and perf_counter() >= deadline:
                    raise TimeoutError("sum bound compilation time limit")
                rights = (
                    variable.domain if candidates is None else candidates.get(left, ())
                )
                successors = []
                for right in rights:
                    if right not in domain:
                        continue
                    assignment: dict[Term, Term] = {variable.name: right}
                    if i:
                        assert left is not None
                        assignment[self.names[i - 1]] = left
                    if all(
                        tuple(assignment[v] for v in scope) in rows
                        for scope, rows in hard
                    ):
                        successors.append(
                            (
                                right,
                                sum(
                                    f.contribution(assignment).value for f in factors[i]
                                ),
                            )
                        )
                adjacency[left] = tuple(successors)
            self.edges.append(adjacency)

    def __call__(self, domains: Mapping[Term, frozenset[Term]]) -> tuple[int, int]:
        from .bounds import NoObjectiveCompletion

        current: dict[Term | None, tuple[int, int]] = {None: (self.offset, self.offset)}
        for i, name in enumerate(self.names):
            following: dict[Term | None, tuple[int, int]] = {}
            for left, (lower, upper) in current.items():
                if self.deadline is not None and perf_counter() >= self.deadline:
                    raise TimeoutError("sum completion bound time limit")
                for right, score in self.edges[i].get(left, ()):
                    if right not in domains[name]:
                        continue
                    low, high = lower + score, upper + score
                    if right in following:
                        low = min(low, following[right][0])
                        high = max(high, following[right][1])
                    following[right] = low, high
            if not following:
                raise NoObjectiveCompletion
            current = following
        return min(v[0] for v in current.values()), max(v[1] for v in current.values())
