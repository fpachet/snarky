import pytest

from snarky import ParseError, parse_term
from snarky.parser import (
    _parse_all as historical_parse_all,
)
from snarky.parser import (
    _parse_term_tokens as historical_parse_term_tokens,
)
from snarky.parser import (
    parse_term as historical_parse_term,
)
from snarky.parser_lexer import _tokenize
from snarky.parser_terms import (
    _parse_all,
    _parse_term_tokens,
)
from snarky.parser_terms import (
    parse_term as extracted_parse_term,
)
from snarky.terms import (
    Atom,
    FiniteSequence,
    FiniteSet,
    Number,
    Status,
    Triple,
    Variable,
)


def test_term_parser_keeps_public_and_historical_import_identities() -> None:
    assert parse_term is extracted_parse_term
    assert historical_parse_term is extracted_parse_term
    assert historical_parse_all is _parse_all
    assert historical_parse_term_tokens is _parse_term_tokens


def test_term_parser_preserves_recursive_term_families() -> None:
    assert parse_term("($subject relation SEQ[[one one two] -3.5 VRAI])") == Triple(
        Variable("subject"),
        Atom("relation"),
        FiniteSequence(
            (
                FiniteSet((Atom("one"), Atom("two"))),
                Number(-3.5),
                Status.VRAI,
            )
        ),
    )


def test_token_parser_preserves_position_for_composed_parsers() -> None:
    tokens = _tokenize("(left relation right) ' FAUX")

    term, position = _parse_term_tokens(tokens, 0)

    assert term == Triple(Atom("left"), Atom("relation"), Atom("right"))
    assert position == 5
    assert tokens[position].value == "'"
    assert _parse_all(tokens[position + 1 :]) is Status.FAUX


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "expected a term"),
        ("left right", "unexpected token 'right'"),
        ("(only two)", "expected a term, got '\\)'"),
        ("(one two three four)", "a triple must contain exactly three terms"),
        ("[one two", "unclosed finite set"),
        ("SEQ[one two", "unclosed finite sequence"),
        (")", "expected a term, got '\\)'"),
    ],
)
def test_term_parser_preserves_error_families(text: str, message: str) -> None:
    with pytest.raises(ParseError, match=message):
        parse_term(text)
