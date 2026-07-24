"""Safe arithmetic expression nodes and deterministic evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .substitutions import TermBindings
from .terms import Number, Term, Variable, is_ground, variables_in


class ArithmeticEvaluationError(ValueError):
    """Raised when a ``LET`` expression cannot be evaluated numerically."""


class BinaryArithmeticOperator(StrEnum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"


class UnaryArithmeticOperator(StrEnum):
    POSITIVE = "+"
    NEGATIVE = "-"


@dataclass(frozen=True, slots=True)
class BinaryArithmeticExpression:
    left: NumericExpression
    operator: BinaryArithmeticOperator
    right: NumericExpression


@dataclass(frozen=True, slots=True)
class UnaryArithmeticExpression:
    operator: UnaryArithmeticOperator
    operand: NumericExpression


@dataclass(frozen=True, slots=True)
class DistinctCountExpression:
    """Number of distinct values taken by a finite tuple of terms."""

    values: tuple[Term, ...]

    def __post_init__(self) -> None:
        values = tuple(self.values)
        if not values:
            raise ValueError("distinct count requires at least one value")
        object.__setattr__(self, "values", values)


type NumericExpression = (
    Number
    | Variable
    | BinaryArithmeticExpression
    | UnaryArithmeticExpression
    | DistinctCountExpression
)


def evaluate_arithmetic(
    expression: NumericExpression,
    substitution: TermBindings,
) -> Number:
    """Evaluate a ground numeric expression without using ``eval``."""

    if isinstance(expression, Number):
        return expression
    if isinstance(expression, Variable):
        value = substitution.apply(expression)
        if not isinstance(value, Number):
            raise ArithmeticEvaluationError(
                f"${expression.name} is not bound to a number"
            )
        return value
    if isinstance(expression, DistinctCountExpression):
        resolved = tuple(
            substitution.apply(value) for value in expression.values
        )
        if not all(is_ground(value) for value in resolved):
            raise ArithmeticEvaluationError(
                "distinct count contains an unbound value"
            )
        return Number(len(set(resolved)))
    if isinstance(expression, UnaryArithmeticExpression):
        operand = evaluate_arithmetic(expression.operand, substitution).value
        if expression.operator is UnaryArithmeticOperator.POSITIVE:
            return Number(+operand)
        if expression.operator is UnaryArithmeticOperator.NEGATIVE:
            return Number(-operand)
        raise ArithmeticEvaluationError(
            f"unsupported unary operator: {expression.operator}"
        )
    if isinstance(expression, BinaryArithmeticExpression):
        left = evaluate_arithmetic(expression.left, substitution).value
        right = evaluate_arithmetic(expression.right, substitution).value
        if expression.operator is BinaryArithmeticOperator.ADD:
            return Number(left + right)
        if expression.operator is BinaryArithmeticOperator.SUBTRACT:
            return Number(left - right)
        if expression.operator is BinaryArithmeticOperator.MULTIPLY:
            return Number(left * right)
        if expression.operator is BinaryArithmeticOperator.DIVIDE:
            if right == 0:
                raise ArithmeticEvaluationError("division by zero in LET")
            return Number(left / right)
        if expression.operator is BinaryArithmeticOperator.MODULO:
            if not isinstance(left, int) or not isinstance(right, int):
                raise ArithmeticEvaluationError(
                    "modulo in LET requires integer operands"
                )
            if right == 0:
                raise ArithmeticEvaluationError("modulo by zero in LET")
            return Number(left % right)
        raise ArithmeticEvaluationError(
            f"unsupported binary operator: {expression.operator}"
        )
    raise ArithmeticEvaluationError(f"unsupported expression: {expression!r}")


def variables_in_arithmetic(
    expression: NumericExpression,
) -> frozenset[Variable]:
    """Return variables occurring in one numeric expression."""

    if isinstance(expression, Number):
        return frozenset()
    if isinstance(expression, Variable):
        return frozenset((expression,))
    if isinstance(expression, UnaryArithmeticExpression):
        return variables_in_arithmetic(expression.operand)
    if isinstance(expression, BinaryArithmeticExpression):
        return (
            variables_in_arithmetic(expression.left)
            | variables_in_arithmetic(expression.right)
        )
    if isinstance(expression, DistinctCountExpression):
        return frozenset(
            variable
            for value in expression.values
            for variable in variables_in(value)
        )
    raise TypeError(f"unsupported expression: {expression!r}")
