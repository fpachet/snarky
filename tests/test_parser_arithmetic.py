import pytest

from snarky import ParseError, parse_arithmetic_expression
from snarky.expressions import (
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    UnaryArithmeticExpression,
    UnaryArithmeticOperator,
)
from snarky.parser import (
    _parse_arithmetic_primary as historical_parse_arithmetic_primary,
)
from snarky.parser import (
    _parse_arithmetic_product as historical_parse_arithmetic_product,
)
from snarky.parser import (
    _parse_arithmetic_sum as historical_parse_arithmetic_sum,
)
from snarky.parser import (
    _parse_arithmetic_unary as historical_parse_arithmetic_unary,
)
from snarky.parser import (
    parse_arithmetic_expression as historical_parse_arithmetic_expression,
)
from snarky.parser_arithmetic import (
    _parse_arithmetic_primary,
    _parse_arithmetic_product,
    _parse_arithmetic_sum,
    _parse_arithmetic_unary,
)
from snarky.parser_arithmetic import (
    parse_arithmetic_expression as extracted_parse_arithmetic_expression,
)
from snarky.terms import Number, Variable


def test_arithmetic_parser_preserves_import_identities() -> None:
    assert parse_arithmetic_expression is extracted_parse_arithmetic_expression
    assert (
        historical_parse_arithmetic_expression
        is extracted_parse_arithmetic_expression
    )
    assert historical_parse_arithmetic_sum is _parse_arithmetic_sum
    assert historical_parse_arithmetic_product is _parse_arithmetic_product
    assert historical_parse_arithmetic_unary is _parse_arithmetic_unary
    assert historical_parse_arithmetic_primary is _parse_arithmetic_primary


def test_arithmetic_parser_preserves_precedence_and_unary_operations() -> None:
    assert parse_arithmetic_expression("-$value + 2 * 3") == (
            BinaryArithmeticExpression(
                UnaryArithmeticExpression(
                    UnaryArithmeticOperator.NEGATIVE,
                    Variable("value"),
                ),
            BinaryArithmeticOperator.ADD,
            BinaryArithmeticExpression(
                Number(2),
                BinaryArithmeticOperator.MULTIPLY,
                Number(3),
            ),
        )
    )


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "expected an arithmetic expression"),
        ("1 +", "expected an arithmetic operand"),
        ("(1 + 2", "unclosed arithmetic parenthesis"),
        ("name", "invalid arithmetic token"),
        ("1 2", "unexpected token '2'"),
    ],
)
def test_arithmetic_parser_preserves_error_families(
    text: str,
    message: str,
) -> None:
    with pytest.raises(ParseError, match=message):
        parse_arithmetic_expression(text)
