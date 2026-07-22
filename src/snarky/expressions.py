"""Safe arithmetic expression nodes and deterministic evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .substitutions import Substitution
from .terms import Number, Variable


class ArithmeticEvaluationError(ValueError):
    """Raised when a ``LET`` expression cannot be evaluated numerically."""


class BinaryArithmeticOperator(StrEnum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"


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


type NumericExpression = (
    Number | Variable | BinaryArithmeticExpression | UnaryArithmeticExpression
)


def evaluate_arithmetic(
    expression: NumericExpression,
    substitution: Substitution,
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
        raise ArithmeticEvaluationError(
            f"unsupported binary operator: {expression.operator}"
        )
    raise ArithmeticEvaluationError(f"unsupported expression: {expression!r}")
