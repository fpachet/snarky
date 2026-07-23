from pathlib import Path

import pytest

from snarky import (
    Atom,
    ComparisonPremise,
    FactPremise,
    ParseError,
    Status,
    Triple,
    Variable,
    parse_rules,
    parse_term,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_parse_recursive_term_with_relation_variable() -> None:
    assert parse_term("($x $relation (bob humain VRAI))") == Triple(
        Variable("x"),
        Variable("relation"),
        Triple(Atom("bob"), Atom("humain"), Status.VRAI),
    )


def test_parse_mini_snarky_rules() -> None:
    text = (PROJECT_ROOT / "tests/rulebases/debug/mini_snarky.rules").read_text()

    rules = parse_rules(text)

    assert [rule.name for rule in rules] == [
        "grand_parent",
        "transitive_relation",
        "knows_modus_ponens",
        "expose_alarm_status",
    ]
    assert len(rules[1].premises) == 4
    assert isinstance(rules[1].premises[-1], ComparisonPremise)
    status_premise = rules[-1].premises[0]
    assert isinstance(status_premise, FactPremise)
    assert status_premise.status == Variable("status")


def test_parser_rejects_malformed_or_unsupported_input() -> None:
    with pytest.raises(ParseError):
        parse_term("(only two)")
    with pytest.raises(ParseError):
        parse_rules("RULE broken\nWHEN\n(x r y)\nTHEN\nREPLACE (x r y)\nEND")
    with pytest.raises(ParseError):
        parse_rules("RULE broken\nWHEN\n(x r y)\nTHEN\nLET $z = 1 + 2\nEND")
    with pytest.raises(ParseError):
        parse_rules("RULE broken\nWHEN\n(x r y)\nTHEN\nLET $z := 1 +\nEND")
