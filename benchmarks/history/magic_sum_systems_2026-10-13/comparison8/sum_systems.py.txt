"""Opt-in discovery of small closed residual equality systems; no solver patches."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from time import perf_counter

from snarky import Atom, Number
from snarky.finite.constraints import (
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.propagation import NativeState


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


@dataclass(frozen=True)
class Equation:
    terms: tuple[tuple[int, int], ...]
    target: int
    scope: int


@dataclass(frozen=True)
class System:
    equations: tuple[int, ...]
    variables: tuple[int, ...]
    reduced: tuple[tuple[Fraction, ...], ...]
    transform: tuple[tuple[Fraction, ...], ...]
    pivots: tuple[int, ...]


def factor(equations, group, scope, deadline=None):
    """Exact RREF and its row-operation certificate, independent of branch values."""
    selected, variables = tuple(bits(group)), tuple(bits(scope))
    rows = [
        [Fraction({v: c for c, v in equations[i].terms}.get(v, 0)) for v in variables]
        for i in selected
    ]
    original = tuple(tuple(row) for row in rows)
    transform = [
        [Fraction(i == j) for j in range(len(selected))] for i in range(len(selected))
    ]
    pivots = []
    for column in range(len(variables)):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("experimental sum-system deadline")
        pivot = next(
            (i for i in range(len(pivots), len(rows)) if rows[i][column]), None
        )
        if pivot is None:
            continue
        rank = len(pivots)
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        transform[rank], transform[pivot] = transform[pivot], transform[rank]
        scale = rows[rank][column]
        rows[rank] = [v / scale for v in rows[rank]]
        transform[rank] = [v / scale for v in transform[rank]]
        for i in range(len(rows)):
            if i == rank or not rows[i][column]:
                continue
            scale = rows[i][column]
            rows[i] = [a - scale * b for a, b in zip(rows[i], rows[rank], strict=True)]
            transform[i] = [
                a - scale * b
                for a, b in zip(transform[i], transform[rank], strict=True)
            ]
        pivots.append(column)
    # Check every compiled equation's exact linear-combination certificate.
    assert all(
        rows[i][j]
        == sum(transform[i][k] * original[k][j] for k in range(len(selected)))
        for i in range(len(rows))
        for j in range(len(variables))
    )
    return System(
        selected,
        variables,
        tuple(map(tuple, rows)),
        tuple(map(tuple, transform)),
        tuple(pivots),
    )


class SumSystemState(NativeState):
    """Native propagation followed by a bounded, exact experimental propagator.

    Only unconditional integer equalities participate. Structural plans are
    valid for one actual unresolved-variable mask, checked after every native
    fixpoint, including rollback. RHS values and domain membership are never
    cached. Ordinary domain reductions use the native trail and event queue.
    """

    def __init__(
        self, model, *, max_variables=4, max_equations=4, budget=128, deductions=True
    ):
        if max_variables < 2 or max_equations < 2 or budget < 1:
            raise ValueError("require at least two variables/equations and budget > 0")
        super().__init__(model)
        self.max_variables = max_variables
        self.max_equations = max_equations
        self.budget = budget
        self.deductions = deductions
        self.names = tuple(v.name for v in model.variables)
        positions = {name: i for i, name in enumerate(self.names)}
        integers = {
            v.name
            for v in model.variables
            if all(isinstance(x, Number) and type(x.value) is int for x in v.domain)
        }
        equations = []
        self.incidence = [0] * len(self.names)
        for constraint in model.constraints:
            if isinstance(constraint, SumConstraint):
                terms = tuple((1, v) for v in constraint.variables)
            elif (
                isinstance(constraint, LinearSumConstraint)
                and constraint.operator is ConstraintOperator.EQUAL
            ):
                terms = constraint.terms
            else:
                continue
            if type(constraint.target) is not int or any(
                v not in integers for _, v in terms
            ):
                continue
            terms = tuple((coefficient, positions[v]) for coefficient, v in terms)
            scope = sum(1 << v for _, v in terms)
            for _, v in terms:
                self.incidence[v] |= 1 << len(equations)
            equations.append(Equation(terms, constraint.target, scope))
        self.equations = tuple(equations)
        self.relevant = sum(1 << i for i, mask in enumerate(self.incidence) if mask)
        self.active = [e.scope for e in self.equations]
        self.unresolved = None
        self.eligible = 0
        self.systems = ()
        self.stats = dict.fromkeys(
            (
                "fixpoints",
                "topology_updates",
                "scope_updates",
                "expansions",
                "budget_hits",
                "factorizations",
                "full_rank",
                "rank_deficient",
                "evaluations",
                "assignments",
                "contradictions",
                "native_calls",
            ),
            0,
        )
        self.stats.update(discovery_seconds=0.0, evaluation_seconds=0.0)

    def discover(self, unresolved, deadline):
        started = perf_counter()
        delta = (
            self.relevant if self.unresolved is None else unresolved ^ self.unresolved
        )
        affected = 0
        for v in bits(delta):
            affected |= self.incidence[v]
        for i in bits(affected):
            self.active[i] = self.equations[i].scope & unresolved
            self.eligible &= ~(1 << i)
            if 2 <= self.active[i].bit_count() <= self.max_variables:
                self.eligible |= 1 << i
        self.unresolved = unresolved
        self.stats["topology_updates"] += 1
        self.stats["scope_updates"] += affected.bit_count()
        # Breadth first with the shortest residual equations first. Every node
        # and extension is bounded; missing a group only loses an optimization.
        frontier = [
            (1 << i, self.active[i])
            for i in sorted(
                bits(self.eligible), key=lambda i: (self.active[i].bit_count(), i)
            )
        ]
        seen = {group for group, _ in frontier}
        systems = []
        cursor, work, truncated = 0, 0, False
        while cursor < len(frontier) and work < self.budget:
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("experimental sum-system deadline")
            group, scope = frontier[cursor]
            cursor += 1
            work += 1
            count = group.bit_count()
            if count >= scope.bit_count():
                system = factor(self.equations, group, scope, deadline)
                systems.append(system)
                self.stats["factorizations"] += 1
                key = (
                    "full_rank"
                    if len(system.pivots) == len(system.variables)
                    else "rank_deficient"
                )
                self.stats[key] += 1
            if count >= self.max_equations:
                continue
            neighbors = 0
            for v in bits(scope):
                neighbors |= self.incidence[v]
            neighbors &= self.eligible & ~group
            candidates = sorted(
                bits(neighbors),
                key=lambda i: ((self.active[i] & ~scope).bit_count(), i),
            )
            for i in candidates:
                if work >= self.budget:
                    truncated = True
                    break
                work += 1
                extended = group | (1 << i)
                union = scope | self.active[i]
                if extended not in seen and union.bit_count() <= self.max_variables:
                    seen.add(extended)
                    frontier.append((extended, union))
        self.stats["expansions"] += work
        self.stats["budget_hits"] += int(truncated or cursor < len(frontier))
        self.systems = tuple(systems)
        self.stats["discovery_seconds"] += perf_counter() - started

    def evaluate(self, deadline):
        started = perf_counter()
        fixed = {}
        rhs = {}
        assignments = {}
        contradiction = False
        for system in self.systems:
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("experimental sum-system deadline")
            targets = []
            for i in system.equations:
                if i not in rhs:
                    value = self.equations[i].target
                    for coefficient, v in self.equations[i].terms:
                        if not self.unresolved & (1 << v):
                            if v not in fixed:
                                fixed[v] = self.domains.values(self.names[v])[0].value
                            value -= coefficient * fixed[v]
                    rhs[i] = value
                targets.append(rhs[i])
            reduced_rhs = tuple(
                sum(c * t for c, t in zip(row, targets, strict=True))
                for row in system.transform
            )
            self.stats["evaluations"] += 1
            rank = len(system.pivots)
            if any(reduced_rhs[rank:]):
                contradiction = True
                break
            if rank != len(system.variables):
                continue
            for row, column in enumerate(system.pivots):
                v, value = system.variables[column], reduced_rhs[row]
                if value.denominator != 1:
                    contradiction = True
                    break
                value = Number(value.numerator)
                if (
                    value not in self.domains.values(self.names[v])
                    or v in assignments
                    and assignments[v] != value
                ):
                    contradiction = True
                    break
                assignments[v] = value
            if contradiction:
                break
        if contradiction:
            self.stats["contradictions"] += 1
            # Deliberately outside dom_wdeg's original constraint weights;
            # report this attribution limitation rather than biasing one sum.
            self.failure = Atom("experimental_sum_system")
        else:
            for v, value in assignments.items():
                if self.domains.retain(
                    self.names[v], {value}, Atom("experimental_sum_system")
                ):
                    self.stats["assignments"] += 1
        self.stats["evaluation_seconds"] += perf_counter() - started
        return not contradiction, bool(assignments)

    def propagate(self, *, deadline=None, facts=None, objective_cut=None):
        while True:
            self.stats["native_calls"] += 1
            if not super().propagate(
                deadline=deadline, facts=facts, objective_cut=objective_cut
            ):
                return False
            self.stats["fixpoints"] += 1
            unresolved = sum(
                1 << v
                for v in bits(self.relevant)
                if self.domains.size(self.names[v]) > 1
            )
            if unresolved != self.unresolved:
                self.discover(unresolved, deadline)
            if not self.systems or not self.deductions:
                return True
            consistent, changed = self.evaluate(deadline)
            if not consistent:
                return False
            if not changed:
                return True
