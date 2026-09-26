"""Complete-assignment semantics; intentionally independent of propagation."""

from __future__ import annotations

from collections.abc import Mapping

from ..terms import Number, Term
from .constraints import (
    AllDifferentConstraint,
    AllOfConstraint,
    AnyOfConstraint,
    AvailabilityConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    CapacityConstraint,
    ConstraintOperator,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    NValueConstraint,
    PersistentConstraint,
    ResourceLoadConstraint,
    SumConstraint,
    TableConstraint,
    WorkloadConstraint,
)


def integer(term: Term) -> int:
    if not isinstance(term, Number) or type(term.value) is not int:
        raise TypeError("an integer Number is required")
    return term.value


def numeric(term: Term) -> int | float:
    if not isinstance(term, Number) or isinstance(term.value, bool):
        raise TypeError("a numeric Number is required")
    return term.value


def compare(total: int, operator: ConstraintOperator, target: int) -> bool:
    if operator is ConstraintOperator.EQUAL:
        return total == target
    if operator is ConstraintOperator.LESS_EQUAL:
        return total <= target
    return total >= target


def accepts(constraint: PersistentConstraint, assignment: Mapping[Term, Term]) -> bool:
    """Check the predicate directly, without consulting propagator output."""
    if isinstance(constraint, AllOfConstraint):
        return all(accepts(c, assignment) for c in constraint.constraints)
    if isinstance(constraint, AvailabilityConstraint):
        task = constraint.task
        if not _present(task.present, assignment):
            return True
        assert task.resource is not None
        start = integer(assignment[task.start])
        windows = dict(constraint.windows).get(assignment[task.resource], ())
        return any(lo <= start and start + task.duration <= hi for lo, hi in windows)
    if isinstance(constraint, WorkloadConstraint):
        load = 0
        for task in constraint.tasks:
            assert task.resource is not None
            if (
                not _present(task.present, assignment)
                or assignment[task.resource] != constraint.resource
            ):
                continue
            amount = task.duration
            if constraint.window is not None:
                lo, hi = constraint.window
                start = integer(assignment[task.start])
                amount = max(0, min(start + task.duration, hi) - max(start, lo))
            load += amount
        return constraint.minimum <= load <= constraint.maximum
    if isinstance(constraint, ResourceLoadConstraint):
        intervals = []
        for task, demand in zip(constraint.tasks, constraint.demands, strict=True):
            if not _present(task.present, assignment):
                continue
            if constraint.resources is not None:
                assert task.resource is not None
                if assignment[task.resource] not in constraint.resources:
                    continue
            start = integer(assignment[task.start])
            intervals.append((start, start + task.duration, demand))
        boundaries = {t for start, end, _ in intervals for t in (start, end)}
        if constraint.window is not None:
            lo, hi = constraint.window
            boundaries.add(lo)
            boundaries = {t for t in boundaries if lo <= t < hi}
        return all(
            constraint.minimum
            <= sum(d for start, end, d in intervals if start <= t < end)
            and (
                constraint.maximum is None
                or sum(d for start, end, d in intervals if start <= t < end)
                <= constraint.maximum
            )
            for t in boundaries
        )
    if isinstance(constraint, AnyOfConstraint):
        return any(accepts(c, assignment) for c in constraint.alternatives)
    if isinstance(constraint, CapacityConstraint):
        # Independently check the actual intervals. Peak load can only increase
        # at an interval's start, so this is equivalent to checking every slot.
        intervals = []
        for task, demand in zip(constraint.tasks, constraint.demands, strict=True):
            if task.present is not None:
                present = integer(assignment[task.present])
                if present not in (0, 1):
                    raise ValueError("task presence domains require Number(0/1)")
                if not present:
                    continue
            start = integer(assignment[task.start])
            intervals.append((start, start + task.duration, demand))
        return all(
            sum(d for start, end, d in intervals if start <= slot < end)
            <= constraint.capacity
            for slot, _, _ in intervals
        )
    values = tuple(assignment[var] for var in constraint.variables)
    if isinstance(constraint, AllDifferentConstraint):
        return len(set(values)) == len(values)
    if isinstance(constraint, SumConstraint):
        return sum(integer(value) for value in values) == constraint.target
    if isinstance(constraint, LinearSumConstraint):
        total = sum(
            coefficient * integer(assignment[var])
            for coefficient, var in constraint.terms
        )
        return compare(total, constraint.operator, constraint.target)
    if isinstance(constraint, BinaryComparisonConstraint):
        left, right = values
        if constraint.operator is BinaryComparisonOperator.NOT_EQUAL:
            return left != right
        if constraint.operator is BinaryComparisonOperator.LESS_THAN:
            return numeric(left) < numeric(right)
        return numeric(left) <= numeric(right)
    if isinstance(constraint, ElementConstraint):
        index = integer(assignment[constraint.index])
        return (
            1 <= index <= len(constraint.array)
            and assignment[constraint.array[index - 1]] == assignment[constraint.value]
        )
    if isinstance(constraint, NValueConstraint):
        target = (
            constraint.count
            if isinstance(constraint.count, int)
            else integer(assignment[constraint.count])
        )
        return (
            len({assignment[v] for v in constraint.scope} | set(constraint.constants))
            == target
        )
    if isinstance(constraint, CountConstraint):
        return compare(
            values.count(constraint.value), constraint.operator, constraint.target
        )
    if isinstance(constraint, GlobalCardinalityConstraint):
        return all(
            lower <= values.count(value) <= upper
            for value, lower, upper in constraint.bounds
        )
    if isinstance(constraint, TableConstraint):
        return values in constraint.allowed
    if isinstance(constraint, LexLessEqualConstraint):
        return tuple(numeric(assignment[var]) for var in constraint.left) <= tuple(
            numeric(assignment[var]) for var in constraint.right
        )
    raise TypeError(f"unsupported constraint: {type(constraint).__name__}")


def _present(variable: Term | None, assignment: Mapping[Term, Term]) -> bool:
    if variable is None:
        return True
    value = integer(assignment[variable])
    if value not in (0, 1):
        raise ValueError("task presence domains require Number(0/1)")
    return value == 1
