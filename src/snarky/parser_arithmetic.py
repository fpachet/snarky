"""Safe arithmetic-expression parsing shared by premises and actions."""

from __future__ import annotations

from .expressions import (
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    NumericExpression,
    UnaryArithmeticExpression,
    UnaryArithmeticOperator,
)
from .parser_lexer import ParseError, _Token, _tokenize_arithmetic
from .terms import Number, Variable


def parse_arithmetic_expression(text: str) -> NumericExpression:
    """Parse one safe arithmetic expression with standard precedence."""

    tokens = _tokenize_arithmetic(text)
    expression, position = _parse_arithmetic_sum(tokens, 0)
    if position != len(tokens):
        raise ParseError(f"unexpected token {tokens[position].value!r}")
    return expression


def _parse_arithmetic_sum(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    left, position = _parse_arithmetic_product(tokens, position)
    while position < len(tokens) and tokens[position].value in {"+", "-"}:
        operator = BinaryArithmeticOperator(tokens[position].value)
        right, position = _parse_arithmetic_product(tokens, position + 1)
        left = BinaryArithmeticExpression(left, operator, right)
    return left, position


def _parse_arithmetic_product(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    left, position = _parse_arithmetic_unary(tokens, position)
    while position < len(tokens) and tokens[position].value in {"*", "/", "%"}:
        operator = BinaryArithmeticOperator(tokens[position].value)
        right, position = _parse_arithmetic_unary(tokens, position + 1)
        left = BinaryArithmeticExpression(left, operator, right)
    return left, position


def _parse_arithmetic_unary(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    if position < len(tokens) and tokens[position].value in {"+", "-"}:
        operator = UnaryArithmeticOperator(tokens[position].value)
        operand, position = _parse_arithmetic_unary(tokens, position + 1)
        return UnaryArithmeticExpression(operator, operand), position
    return _parse_arithmetic_primary(tokens, position)


def _parse_arithmetic_primary(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    if position >= len(tokens):
        raise ParseError("expected an arithmetic operand")
    token = tokens[position]
    if token.kind == "NUMBER":
        value = float(token.value) if "." in token.value else int(token.value)
        return Number(value), position + 1
    if token.kind == "VARIABLE":
        return Variable(token.value[1:]), position + 1
    if token.kind == "LPAREN":
        expression, position = _parse_arithmetic_sum(tokens, position + 1)
        if position >= len(tokens) or tokens[position].kind != "RPAREN":
            raise ParseError("unclosed arithmetic parenthesis")
        return expression, position + 1
    raise ParseError(f"expected an arithmetic operand, got {token.value!r}")
