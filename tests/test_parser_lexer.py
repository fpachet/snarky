import pytest

from snarky import ParseError
from snarky.parser import ParseError as HistoricalParseError
from snarky.parser_lexer import (
    ParseError as ExtractedParseError,
)
from snarky.parser_lexer import (
    _normalized_lines,
    _tokenize,
    _tokenize_arithmetic,
)


def test_parse_error_keeps_public_and_historical_import_identity() -> None:
    assert ParseError is ExtractedParseError
    assert HistoricalParseError is ExtractedParseError


def test_lexer_normalizes_rule_lines_without_comments_or_blanks() -> None:
    assert _normalized_lines(
        """
        # heading

          RULE example
            WHEN
        # ignored
            (x relation $value)
        """
    ) == ("RULE example", "WHEN", "(x relation $value)")


def test_term_and_arithmetic_lexers_preserve_token_kinds_and_values() -> None:
    assert tuple(
        (token.kind, token.value)
        for token in _tokenize("($x relation -2) ' FAUX")
    ) == (
        ("LPAREN", "("),
        ("VARIABLE", "$x"),
        ("ATOM", "relation"),
        ("NUMBER", "-2"),
        ("RPAREN", ")"),
        ("QUOTE", "'"),
        ("ATOM", "FAUX"),
    )
    assert tuple(
        (token.kind, token.value)
        for token in _tokenize_arithmetic("-($x + 2.5)")
    ) == (
        ("OP", "-"),
        ("LPAREN", "("),
        ("VARIABLE", "$x"),
        ("OP", "+"),
        ("NUMBER", "2.5"),
        ("RPAREN", ")"),
    )


def test_lexers_preserve_empty_and_invalid_token_errors() -> None:
    with pytest.raises(ExtractedParseError, match="expected a term"):
        _tokenize("   ")
    with pytest.raises(ExtractedParseError, match="invalid token near"):
        _tokenize("!")
    with pytest.raises(
        ExtractedParseError,
        match="expected an arithmetic expression",
    ):
        _tokenize_arithmetic("   ")
    with pytest.raises(
        ExtractedParseError,
        match="invalid arithmetic token near",
    ):
        _tokenize_arithmetic("name")
