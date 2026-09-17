"""Incident-constraint scheduling over native domains; no inference sessions."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter

from ..facts import Fact
from ..terms import Atom, Term, Triple
from . import kernels
from .constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    NValueConstraint,
    PersistentConstraint,
    SumConstraint,
    TableConstraint,
)
from .domains import DomainCheckpoint, FiniteDomains
from .model import (
    VALUE,
    FactConstraint,
    FiniteModel,
    GuardedConstraint,
    PredicateConstraint,
    Solution,
    score_solution,
)
from .numeric import NumericPlan, NumericPlans
from .nvalue import revise_nvalue


class TableSupports:
    """Immutable per-value row masks shared across revisions and search branches."""

    def __init__(self, constraint: TableConstraint) -> None:
        self.all_rows = (1 << len(constraint.allowed)) - 1
        self.supports: dict[Term, dict[Term, int]] = {
            var: {} for var in constraint.variables
        }
        for i, row in enumerate(constraint.allowed):
            for var, value in zip(constraint.variables, row, strict=True):
                supports = self.supports[var]
                supports[value] = supports.get(value, 0) | (1 << i)

    def revise(self, scoped: dict[Term, set[Term]]) -> bool:
        active = self.all_rows
        for var, values in scoped.items():
            supported_rows = 0
            for value in values:
                supported_rows |= self.supports[var].get(value, 0)
            active &= supported_rows
            if not active:
                return False
        for var, values in scoped.items():
            values.intersection_update(
                value
                for value in tuple(values)
                if self.supports[var].get(value, 0) & active
            )
        return True


@dataclass(frozen=True, slots=True)
class NativeCheckpoint:
    domains: DomainCheckpoint
    failure: Atom | None
    initialized: bool


class NativeState:
    """Reversible finite problem state; constraint state is branch-local."""

    def __init__(self, model: FiniteModel, *, numeric_masks: bool = True) -> None:
        self.model = model
        self.domains = FiniteDomains(model.variables)
        self._numeric = NumericPlans(self.domains) if numeric_masks else None
        self.failure: Atom | None = None
        self.revisions = 0
        self._adjacency: dict[Term, list[int]] = {
            var.name: [] for var in model.variables
        }
        self._tables: dict[int, TableSupports] = {}
        self._matchings: dict[int, dict[Term, Term]] = {}
        self._guarded: list[int] = []
        for index, constraint in enumerate(model.constraints):
            for var in constraint.variables:
                self._adjacency[var].append(index)
            if isinstance(constraint, GuardedConstraint):
                self._guarded.append(index)
                constraint = constraint.constraint
            if isinstance(constraint, TableConstraint):
                self._tables[index] = TableSupports(constraint)
        self._initialized = False

    def checkpoint(self) -> NativeCheckpoint:
        return NativeCheckpoint(
            self.domains.checkpoint(), self.failure, self._initialized
        )

    def rollback(self, checkpoint: NativeCheckpoint) -> None:
        self.domains.rollback(checkpoint.domains)
        self.failure = checkpoint.failure
        self._initialized = checkpoint.initialized

    def release(self, checkpoint: NativeCheckpoint) -> None:
        self.domains.release(checkpoint.domains)

    def restrict(self, variable: Term, value: Term) -> None:
        self.domains.retain(variable, {value}, Atom("decision"))

    def propagate(
        self,
        *,
        deadline: float | None = None,
        facts: frozenset[Fact] | None = None,
        objective_cut: LinearSumConstraint | None = None,
    ) -> bool:
        changed = self.domains.take_changed()
        indices = (
            set(range(len(self.model.constraints)))
            if not self._initialized
            else {index for var in changed for index in self._adjacency[var]}
        )
        self._initialized = True
        indices.update(self._guarded)
        # The search controller supplies its latest incumbent cut on every call,
        # including after rollback. Only the resulting domain reductions trail;
        # neither the immutable model nor checkpoint state owns the incumbent.
        cut_index = len(self.model.constraints)
        cut_variables = frozenset(objective_cut.variables) if objective_cut else ()
        pending = deque(
            ([cut_index] if objective_cut is not None else []) + sorted(indices)
        )
        queued = set(pending)
        while pending:
            if deadline is not None and perf_counter() >= deadline:
                self._initialized = False
                raise TimeoutError("constraint propagation time limit")
            index = pending.popleft()
            queued.remove(index)
            constraint = (
                objective_cut if index == cut_index else self.model.constraints[index]
            )
            assert constraint is not None
            cause = constraint.name
            if isinstance(constraint, GuardedConstraint):
                known = self.closed_facts() if facts is None else facts
                if constraint.guard not in known:
                    continue
                constraint = constraint.constraint
            # These have only complete-state semantics until an explicit
            # propagator or the mixed coordinator supplies partial-state behavior.
            if isinstance(constraint, (PredicateConstraint, FactConstraint)):
                continue
            self.revisions += 1
            plan = (
                self._numeric.get(index, constraint)
                if self._numeric is not None
                and isinstance(constraint, (LinearSumConstraint, SumConstraint))
                else None
            )
            if plan is not None:
                assert isinstance(constraint, (LinearSumConstraint, SumConstraint))
                if not self._revise_numeric(index, constraint, plan, cause):
                    self.failure = cause
                    return False
            else:
                scoped = {
                    var: set(self.domains.values(var)) for var in constraint.variables
                }
                if any(not values for values in scoped.values()) or not self._revise(
                    index, constraint, scoped
                ):
                    self.failure = cause
                    return False
                for var, values in scoped.items():
                    if len(values) != self.domains.size(var):
                        self.domains.retain(var, values, cause)
            for var in self.domains.take_changed():
                if var in cut_variables and cut_index not in queued:
                    queued.add(cut_index)
                    pending.append(cut_index)
                for incident in (*self._adjacency[var], *self._guarded):
                    if incident not in queued:
                        queued.add(incident)
                        pending.append(incident)
        return self.failure is None and not self.domains.empty

    def _revise_numeric(
        self,
        index: int,
        constraint: LinearSumConstraint | SumConstraint,
        plan: NumericPlan,
        cause: Atom,
    ) -> bool:
        supported = plan.supports(self.domains, constraint.target)
        if supported is None:
            return False
        for column, mask in zip(plan.columns, supported, strict=True):
            self.domains.retain_mask(column.variable, mask, cause)
        return True

    def _revise(
        self,
        index: int,
        constraint: PersistentConstraint,
        scoped: dict[Term, set[Term]],
    ) -> bool:
        if isinstance(constraint, TableConstraint):
            return self._tables[index].revise(scoped)
        if isinstance(constraint, AllDifferentConstraint):
            valid, matching = kernels._revise_all_different_with_matching(
                constraint,
                scoped,
                self._matchings.get(index),
            )
            if matching is not None:
                self._matchings[index] = matching
            return valid
        if isinstance(constraint, LinearSumConstraint):
            return kernels._revise_linear_sum(constraint, scoped)
        if isinstance(constraint, SumConstraint):
            return kernels._revise_sum(constraint, scoped)
        if isinstance(constraint, BinaryComparisonConstraint):
            return kernels._revise_binary_comparison(constraint, scoped)
        if isinstance(constraint, ElementConstraint):
            return kernels._revise_element(constraint, scoped)
        if isinstance(constraint, NValueConstraint):
            return revise_nvalue(constraint, scoped)
        if isinstance(constraint, CountConstraint):
            return kernels._revise_count(constraint, scoped)
        if isinstance(constraint, GlobalCardinalityConstraint):
            return kernels._revise_gcc(constraint, scoped)
        if isinstance(constraint, LexLessEqualConstraint):
            return kernels._revise_lex_less_equal(constraint, scoped)
        raise TypeError(f"unsupported constraint {constraint!r}")

    def assignment(self) -> Mapping[Term, Term]:
        if not self.domains.complete:
            raise ValueError("assignment requires singleton domains")
        return {
            var.name: self.domains.values(var.name)[0] for var in self.model.variables
        }

    def closed_facts(self) -> frozenset[Fact]:
        return frozenset(
            (
                *self.model.context,
                *(
                    Fact(Triple(var.name, VALUE, self.domains.values(var.name)[0]))
                    for var in self.model.variables
                    if self.domains.size(var.name) == 1
                ),
            )
        )

    def solution(self) -> Solution:
        assignment = self.assignment()
        facts = self.closed_facts()
        score, contributions = score_solution(self.model, assignment, facts)
        return Solution(
            assignment,
            facts,
            score,
            reductions=self.domains.removals,
            contributions=contributions,
        )
