"""Immutable finite-domain constraint definitions, independent of inference sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..terms import Atom, Term


@dataclass(frozen=True, slots=True)
class AllDifferentConstraint:
    """Require the scoped variables to take pairwise-distinct values."""

    name: Atom
    variables: tuple[Term, ...]

    def __post_init__(self) -> None:
        _validate_scope("ALL_DIFFERENT", self.variables)
        object.__setattr__(self, "variables", tuple(self.variables))


@dataclass(frozen=True, slots=True)
class SumConstraint:
    """Require the scoped integer variables to sum exactly to ``target``."""

    name: Atom
    variables: tuple[Term, ...]
    target: int

    def __post_init__(self) -> None:
        _validate_scope("SUM", self.variables)
        object.__setattr__(self, "variables", tuple(self.variables))


class ConstraintOperator(StrEnum):
    """Comparison operators shared by numeric aggregate constraints."""

    EQUAL = "EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_EQUAL = "GREATER_EQUAL"


class BinaryComparisonOperator(StrEnum):
    """Operators supported by persistent binary comparisons."""

    LESS_EQUAL = "LESS_EQUAL"
    LESS_THAN = "LESS_THAN"
    NOT_EQUAL = "NOT_EQUAL"


@dataclass(frozen=True, slots=True)
class LinearSumConstraint:
    """Constrain an integer weighted sum with ``=``, ``<=``, or ``>=``."""

    name: Atom
    terms: tuple[tuple[int, Term], ...]
    operator: ConstraintOperator
    target: int

    def __post_init__(self) -> None:
        terms = tuple(self.terms)
        if not terms:
            raise ValueError("LINEAR_SUM requires at least one term")
        if any(
            isinstance(coefficient, bool)
            or not isinstance(coefficient, int)
            or coefficient == 0
            for coefficient, _ in terms
        ):
            raise ValueError("LINEAR_SUM coefficients must be non-zero integers")
        variables = tuple(variable for _, variable in terms)
        _validate_scope("LINEAR_SUM", variables)
        if isinstance(self.target, bool) or not isinstance(self.target, int):
            raise ValueError("LINEAR_SUM target must be an integer")
        object.__setattr__(self, "terms", terms)
        object.__setattr__(
            self,
            "operator",
            ConstraintOperator(self.operator),
        )

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return the variables participating in the weighted sum."""

        return tuple(variable for _, variable in self.terms)


@dataclass(frozen=True, slots=True)
class BinaryComparisonConstraint:
    """Compare two finite-domain variables."""

    name: Atom
    left: Term
    right: Term
    operator: BinaryComparisonOperator

    def __post_init__(self) -> None:
        if self.left == self.right:
            raise ValueError("binary comparison variables must be distinct")
        object.__setattr__(
            self,
            "operator",
            BinaryComparisonOperator(self.operator),
        )

    @property
    def variables(self) -> tuple[Term, Term]:
        """Return the two compared variables."""

        return (self.left, self.right)


@dataclass(frozen=True, slots=True)
class ElementConstraint:
    """Require ``value`` to equal ``array[index]`` using one-based indices."""

    name: Atom
    index: Term
    array: tuple[Term, ...]
    value: Term

    def __post_init__(self) -> None:
        array = tuple(self.array)
        _validate_scope("ELEMENT array", array)
        variables = (self.index, *array, self.value)
        if len(set(variables)) != len(variables):
            raise ValueError(
                "ELEMENT index, array, and value variables must be distinct"
            )
        object.__setattr__(self, "array", array)

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return index, array, and result variables."""

        return (self.index, *self.array, self.value)


@dataclass(frozen=True, slots=True)
class CountConstraint:
    """Count occurrences of one value in a finite-domain scope."""

    name: Atom
    variables: tuple[Term, ...]
    value: Term
    operator: ConstraintOperator
    target: int

    def __post_init__(self) -> None:
        _validate_scope("COUNT", self.variables)
        if isinstance(self.target, bool) or not isinstance(self.target, int):
            raise ValueError("COUNT target must be an integer")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(
            self,
            "operator",
            ConstraintOperator(self.operator),
        )


@dataclass(frozen=True, slots=True)
class GlobalCardinalityConstraint:
    """Bound the number of occurrences of selected values in a scope.

    ``bounds`` contains ``(value, lower, upper)`` triples. Values without an
    explicit entry retain the default interval ``[0, number of variables]``.
    """

    name: Atom
    variables: tuple[Term, ...]
    bounds: tuple[tuple[Term, int, int], ...]

    def __post_init__(self) -> None:
        _validate_scope("GCC", self.variables)
        bounds = tuple(self.bounds)
        values = tuple(value for value, _, _ in bounds)
        if len(set(values)) != len(values):
            raise ValueError("GCC values must have unique bounds")
        for _, lower, upper in bounds:
            if lower < 0 or upper < lower:
                raise ValueError("GCC bounds require 0 <= lower <= upper")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "bounds", bounds)


@dataclass(frozen=True, slots=True)
class TableConstraint:
    """Require the scoped variables to match one allowed tuple."""

    name: Atom
    variables: tuple[Term, ...]
    allowed: tuple[tuple[Term, ...], ...]

    def __post_init__(self) -> None:
        _validate_scope("TABLE", self.variables)
        allowed = tuple(tuple(row) for row in self.allowed)
        if not allowed:
            raise ValueError("TABLE requires at least one allowed tuple")
        if any(len(row) != len(self.variables) for row in allowed):
            raise ValueError("TABLE tuple arity must match its scope")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "allowed", tuple(dict.fromkeys(allowed)))


@dataclass(frozen=True, slots=True)
class LexLessEqualConstraint:
    """Require one sequence of numeric variables to be lexicographically <= another."""

    name: Atom
    left: tuple[Term, ...]
    right: tuple[Term, ...]

    def __post_init__(self) -> None:
        left = tuple(self.left)
        right = tuple(self.right)
        if not left or len(left) != len(right):
            raise ValueError(
                "LEX_LESS_EQUAL requires non-empty sequences of equal length"
            )
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)

    @property
    def variables(self) -> tuple[Term, ...]:
        """Return the distinct variables observed by this constraint."""

        return tuple(dict.fromkeys((*self.left, *self.right)))


type PersistentConstraint = (
    AllDifferentConstraint
    | SumConstraint
    | LinearSumConstraint
    | BinaryComparisonConstraint
    | ElementConstraint
    | CountConstraint
    | GlobalCardinalityConstraint
    | TableConstraint
    | LexLessEqualConstraint
)


def _validate_scope(kind: str, variables: tuple[Term, ...]) -> None:
    variables = tuple(variables)
    if not variables:
        raise ValueError(f"{kind} requires at least one variable")
    if len(set(variables)) != len(variables):
        raise ValueError(f"{kind} variables must be distinct")
