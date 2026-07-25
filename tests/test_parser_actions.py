from collections.abc import Callable

import pytest

from snarky import ParseError
from snarky.actions import (
    AddFact,
    Choice,
    ForEach,
    Fresh,
    Let,
    RemoveFact,
)
from snarky.parser import (
    _parse_action as historical_parse_action,
)
from snarky.parser import (
    _parse_action_block as historical_parse_action_block,
)
from snarky.parser import (
    _parse_choice_block as historical_parse_choice_block,
)
from snarky.parser import (
    _parse_fact_template as historical_parse_fact_template,
)
from snarky.parser_actions import (
    _parse_action,
    _parse_action_block,
    _parse_choice_block,
    _parse_fact_template,
)
from snarky.terms import Atom, Status


def test_action_parser_preserves_historical_import_identities() -> None:
    assert historical_parse_action is _parse_action
    assert historical_parse_action_block is _parse_action_block
    assert historical_parse_choice_block is _parse_choice_block
    assert historical_parse_fact_template is _parse_fact_template


def test_simple_action_families_and_explicit_status_are_preserved() -> None:
    add = _parse_action("ADD added")
    remove = _parse_action("REMOVE removed ' FAUX")
    let = _parse_action("LET $result := 1 + 2")
    fresh = _parse_action("FRESH $node PREFIX generated")

    assert isinstance(add, AddFact)
    assert isinstance(remove, RemoveFact)
    assert isinstance(let, Let)
    assert isinstance(fresh, Fresh)
    assert remove.status is Status.FAUX
    assert fresh.prefix == "generated"


def test_nested_for_each_block_preserves_terminator_position() -> None:
    lines = (
        "FOR EACH $item IN SEQ[first second]",
        "ADD ($item selected yes)",
        "END_FOR_EACH",
        "END",
    )

    actions, position = _parse_action_block(lines, 0, "END", None)

    assert position == 3
    assert len(actions) == 1
    assert isinstance(actions[0], ForEach)
    assert len(actions[0].actions) == 1


def test_choice_block_preserves_source_weight_status_and_position() -> None:
    lines = (
        "CHOICE ($item selected $value) ' FAUX WEIGHT 2",
        "FROM",
        "($item candidate $value)",
        "END_CHOICE",
        "END",
    )

    choice, position = _parse_choice_block(lines, 0, None)

    assert position == 4
    assert isinstance(choice, Choice)
    assert choice.status is Status.FAUX
    assert len(choice.premises) == 1


def test_fact_template_preserves_default_and_explicit_statuses() -> None:
    default_entity, default_status = _parse_fact_template("entity", "ADD")
    explicit_entity, explicit_status = _parse_fact_template(
        "entity ' FAUX",
        "REMOVE",
    )

    assert default_entity == explicit_entity == Atom("entity")
    assert default_status is Status.VRAI
    assert explicit_status is Status.FAUX


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: _parse_action("REPLACE entity"), "unsupported action"),
        (lambda: _parse_action("LET $value = 1"), "malformed LET action"),
        (
            lambda: _parse_fact_template("left == right", "ADD"),
            "only accepts an optional status",
        ),
        (
            lambda: _parse_action_block(
                (
                    "FOR EACH $item IN SEQ[first]",
                    "ADD $item",
                ),
                0,
                "END",
                None,
            ),
            "missing END_FOR_EACH",
        ),
        (
            lambda: _parse_choice_block(
                ("CHOICE entity", "ADD other"),
                0,
                None,
            ),
            "must be followed by FROM",
        ),
    ],
)
def test_action_parser_preserves_error_families(
    call: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(ParseError, match=message):
        call()
