import pytest

from snarky import ParseError
from snarky.parser import (
    _parse_compact_existential as historical_parse_compact_existential,
)
from snarky.parser import (
    _parse_computed_call as historical_parse_computed_call,
)
from snarky.parser import (
    _parse_premise as historical_parse_premise,
)
from snarky.parser import (
    _parse_premise_block as historical_parse_premise_block,
)
from snarky.parser import (
    _parse_window as historical_parse_window,
)
from snarky.parser import (
    _top_level_operator as historical_top_level_operator,
)
from snarky.parser_lexer import _tokenize
from snarky.parser_premises import (
    _parse_compact_existential,
    _parse_computed_call,
    _parse_premise,
    _parse_premise_block,
    _parse_window,
    _top_level_operator,
)
from snarky.premises import (
    BindPremise,
    CollectPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    UniquePremise,
)


def test_premise_parser_preserves_historical_import_identities() -> None:
    assert historical_parse_premise_block is _parse_premise_block
    assert historical_parse_compact_existential is _parse_compact_existential
    assert historical_parse_premise is _parse_premise
    assert historical_parse_computed_call is _parse_computed_call
    assert historical_parse_window is _parse_window
    assert historical_top_level_operator is _top_level_operator


def test_premise_block_preserves_nested_aggregate_boundaries() -> None:
    lines = (
        "EXISTS",
        "(item kind useful)",
        "END_EXISTS",
        "COUNT >= 1",
        "(item value $value)",
        "END_COUNT",
        "UNIQUE",
        "(item label $label)",
        "END_UNIQUE",
        "COLLECT $values := $value",
        "(item value $value)",
        "END_COLLECT",
        "THEN",
    )

    premises, position = _parse_premise_block(lines, 0, "THEN", None)

    assert position == 12
    assert tuple(type(premise) for premise in premises) == (
        ExistsPremise,
        CountPremise,
        UniquePremise,
        CollectPremise,
    )


def test_compact_existential_and_window_expansion_are_preserved() -> None:
    compact = _parse_compact_existential(
        "NOT EXISTS (item rejected yes)",
        None,
    )
    window = _parse_window(
        "WINDOW $path := SEQ[first second third] VIA precedes"
    )

    assert compact is not None
    assert len(compact.premises) == 1
    assert isinstance(compact.premises[0], FactPremise)
    assert len(window) == 3
    assert all(isinstance(premise, FactPremise) for premise in window[:2])
    assert isinstance(window[-1], BindPremise)


def test_specialized_dispatch_preserves_whitespace_and_atom_fallbacks() -> None:
    bind = _parse_premise("BIND\t$target := value")
    ordinary = _parse_premise("(BINDING relation value)")

    assert isinstance(bind, BindPremise)
    assert isinstance(ordinary, FactPremise)


def test_top_level_operator_ignores_nested_terms_and_sequences() -> None:
    tokens = _tokenize("(left relation [one two]) == SEQ[one two]")

    assert _top_level_operator(tokens) == (8, "==")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("left == right != other", "only one top-level operator"),
        ("left)", "unexpected closing parenthesis"),
        ("[left", "unclosed finite set"),
    ],
)
def test_top_level_operator_preserves_error_families(
    text: str,
    message: str,
) -> None:
    with pytest.raises(ParseError, match=message):
        _top_level_operator(_tokenize(text))
