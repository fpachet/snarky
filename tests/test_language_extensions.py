import pytest

from snarky import (
    ArithmeticEvaluationError,
    Fact,
    FiniteSet,
    ForwardEngine,
    IndexedInstantiationStrategy,
    NaiveInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    parse_arithmetic_expression,
    parse_rule_groups,
    parse_term,
)
from snarky.expressions import evaluate_arithmetic
from snarky.substitutions import EMPTY_SUBSTITUTION


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_modulo_and_divisibility_are_available_in_the_dsl() -> None:
    (calendar,) = parse_rule_groups(
        """
        GROUP calendar
            RULE classify_leap_candidate
            WHEN
                (request year $year)
                DIVISIBLE $year BY 4
            THEN
                LET $century_remainder := $year % 100
                ADD ($year century_remainder $century_remainder)
            END
        END_GROUP
        """
    )

    result = ForwardEngine(()).create_session(
        (_fact("(request year 2024)"), _fact("(request year 2023)"))
    )
    result.run_group(calendar)

    assert _fact("(2024 century_remainder 24)") in result.facts
    assert _fact("(2023 century_remainder 23)") not in result.facts


def test_modulo_rejects_non_integer_operands_and_zero() -> None:
    with pytest.raises(ArithmeticEvaluationError, match="integer operands"):
        evaluate_arithmetic(
            parse_arithmetic_expression("5.5 % 2"),
            EMPTY_SUBSTITUTION,
        )
    with pytest.raises(ArithmeticEvaluationError, match="modulo by zero"):
        evaluate_arithmetic(
            parse_arithmetic_expression("5 % 0"),
            EMPTY_SUBSTITUTION,
        )


def test_fresh_creates_deterministic_non_colliding_atoms() -> None:
    (generate,) = parse_rule_groups(
        """
        GROUP generate
            RULE create_node
            WHEN
                ($request state pending)
            THEN
                FRESH $node PREFIX node
                ADD ($request generated $node)
                ADD ($node type generated_node)
            END
        END_GROUP
        """
    )
    initial = (
        _fact("(r1 state pending)"),
        _fact("(r2 state pending)"),
        _fact("(node-1 type reserved)"),
    )

    first = ForwardEngine(()).create_session(initial)
    second = ForwardEngine(()).create_session(initial)
    first.run_group(generate)
    second.run_group(generate)

    assert first.facts == second.facts
    assert _fact("(r1 generated node-2)") in first.facts
    assert _fact("(r2 generated node-3)") in first.facts
    assert first.events[0].substitution.apply(
        parse_term("$node")
    ) == parse_term("node-2")


@pytest.mark.parametrize(
    "strategy",
    (
        NaiveInstantiationStrategy(),
        IndexedInstantiationStrategy(),
        SemiNaiveInstantiationStrategy(),
    ),
)
def test_collect_binds_a_finite_set_with_the_same_semantics_for_all_strategies(
    strategy: object,
) -> None:
    (collect_notes,) = parse_rule_groups(
        """
        GROUP collect_notes
            RULE materialize_note_set
            WHEN
                ($chord type chord)
                COLLECT $notes := $note
                    ($chord contains $note)
                END_COLLECT
            THEN
                ADD ($chord notes $notes)
            END
        END_GROUP
        """
    )
    initial = (
        _fact("(c_major type chord)"),
        _fact("(c_major contains c)"),
        _fact("(c_major contains e)"),
        _fact("(c_major contains g)"),
        _fact("(empty_chord type chord)"),
    )
    session = ForwardEngine((), strategy=strategy).create_session(initial)  # type: ignore[arg-type]
    session.run_group(collect_notes)

    expected = Fact(
        parse_term("(c_major notes [c e g])")
    )
    assert expected in session.facts
    assert _fact("(empty_chord notes [])") in session.facts
    assert isinstance(expected.entity.object, FiniteSet)  # type: ignore[union-attr]


def test_collect_refires_when_its_projected_set_changes() -> None:
    collect_notes, add_note = parse_rule_groups(
        """
        GROUP collect_notes
            RULE materialize_note_set
            WHEN
                ($chord type chord)
                COLLECT $notes := $note
                    ($chord contains $note)
                END_COLLECT
            THEN
                ADD ($chord notes $notes)
            END
        END_GROUP

        GROUP add_note
            RULE add_fifth
            WHEN
                (request add_fifth c_major)
            THEN
                ADD (c_major contains g)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(
        (
            _fact("(c_major type chord)"),
            _fact("(c_major contains c)"),
            _fact("(c_major contains e)"),
            _fact("(request add_fifth c_major)"),
        )
    )

    session.run_group(collect_notes)
    session.run_group(add_note)
    session.run_group(collect_notes)

    assert _fact("(c_major notes [c e])") in session.facts
    assert _fact("(c_major notes [c e g])") in session.facts


def test_fork_is_an_isolated_continuation_without_automatic_backtracking() -> None:
    prepare, simulate = parse_rule_groups(
        """
        GROUP prepare
            RULE establish_state
            WHEN
                start
            THEN
                ADD (world state current)
            END
        END_GROUP

        GROUP simulate
            RULE change_branch_only
            WHEN
                (world state current)
            THEN
                REMOVE (world state current)
                ADD (world state hypothetical)
            END
        END_GROUP
        """
    )
    parent = ForwardEngine(()).create_session((_fact("start"),))
    parent.run_group(prepare)

    branch = parent.fork()
    branch.run_group(simulate)

    assert _fact("(world state current)") in parent.facts
    assert _fact("(world state hypothetical)") not in parent.facts
    assert _fact("(world state current)") not in branch.facts
    assert _fact("(world state hypothetical)") in branch.facts
