"""Complete-assignment semantics; intentionally independent of propagation."""

from __future__ import annotations

from collections.abc import Mapping

from ..terms import Number, Term
from .constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
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
