import pytest

import snarky
import snarky.engine as engine_api
from snarky import (
    Fact,
    FactExists,
    ForwardEngine,
    GroupExecutionMode,
    GroupStopReason,
    ParseError,
    RuleGroup,
    Status,
    parse_rule_groups,
    parse_rules,
    parse_term,
    when,
)
from snarky.engine import forward, group_execution


def _fact(text: str) -> Fact:
    return Fact(parse_term(text), Status.VRAI)


@pytest.mark.parametrize(
    "name",
    (
        "EngineLimits",
        "FactExists",
        "GroupExecutionMode",
        "GroupRunResult",
        "GroupStopReason",
        "InferenceLimitError",
        "StopCondition",
    ),
)
def test_group_execution_types_keep_public_import_paths(name: str) -> None:
    public_type = getattr(snarky, name)

    assert public_type is getattr(engine_api, name)
    assert public_type is getattr(forward, name)
    assert public_type is getattr(group_execution, name)


def test_parse_named_rule_groups() -> None:
    groups = parse_rule_groups(
        """
        GROUP prepare
            RULE make_middle
            WHEN
                start
            THEN
                ADD middle
            END
        END_GROUP

        GROUP finish
            RULE make_done
            WHEN
                middle
            THEN
                ADD done
            END
        END_GROUP
        """
    )

    assert [group.name for group in groups] == ["prepare", "finish"]
    assert [rule.name for rule in groups[0].rules] == ["make_middle"]
    assert [rule.name for rule in groups[1].rules] == ["make_done"]


def test_group_parser_rejects_missing_end_and_duplicate_names() -> None:
    with pytest.raises(ParseError, match="missing END_GROUP"):
        parse_rule_groups("GROUP broken")
    with pytest.raises(ParseError, match="duplicate group name"):
        parse_rule_groups("GROUP same\nEND_GROUP\nGROUP same\nEND_GROUP")


def test_groups_share_facts_refraction_and_provenance_in_one_session() -> None:
    prepare, finish = parse_rule_groups(
        """
        GROUP prepare
            RULE make_middle
            WHEN
                start
            THEN
                ADD middle
            END
        END_GROUP

        GROUP finish
            RULE make_done
            WHEN
                middle
            THEN
                ADD done
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session((_fact("start"),))

    prepare_result = session.run_group(prepare)
    finish_result = session.run_group(finish)
    repeated_result = session.run_group(prepare)

    assert prepare_result.added_facts == (_fact("middle"),)
    assert finish_result.added_facts == (_fact("done"),)
    assert repeated_result.added_facts == ()
    assert repeated_result.fired_activation_count == 0
    assert session.facts == (_fact("start"), _fact("middle"), _fact("done"))

    derivation = session.provenance.minimal_derivation(_fact("done"))
    assert derivation is not None
    assert derivation.rule_name == "make_done"
    assert derivation.rule_group == "finish"


def test_one_cycle_can_resume_the_same_group_later() -> None:
    rules = parse_rules(
        """
        RULE make_done
        WHEN
            middle
        THEN
            ADD done
        END

        RULE make_middle
        WHEN
            start
        THEN
            ADD middle
        END
        """
    )
    group = RuleGroup("solve", rules)
    session = ForwardEngine(()).create_session((_fact("start"),))

    first = session.run_group(group, mode=GroupExecutionMode.ONE_CYCLE)
    second = session.run_group(group, mode=GroupExecutionMode.ONE_CYCLE)

    assert first.added_facts == (_fact("middle"),)
    assert first.stop_reason is GroupStopReason.ONE_CYCLE
    assert second.added_facts == (_fact("done"),)
    assert second.stop_reason is GroupStopReason.ONE_CYCLE


def test_first_change_stops_after_one_atomic_activation() -> None:
    rules = parse_rules(
        """
        RULE first
        WHEN
            start
        THEN
            ADD first_result
            ADD first_trace
        END

        RULE second
        WHEN
            start
        THEN
            ADD second_result
        END
        """
    )
    session = ForwardEngine(()).create_session((_fact("start"),))

    result = session.run_group(
        RuleGroup("step", rules),
        mode=GroupExecutionMode.FIRST_CHANGE,
    )

    assert result.added_facts == (_fact("first_result"), _fact("first_trace"))
    assert result.fired_activation_count == 1
    assert result.stop_reason is GroupStopReason.FIRST_CHANGE


def test_until_stops_after_the_activation_that_satisfies_a_fact_pattern() -> None:
    rules = parse_rules(
        """
        RULE reach_goal
        WHEN
            start
        THEN
            ADD (problem state solved)
        END

        RULE continue_after_goal
        WHEN
            start
        THEN
            ADD unwanted
        END
        """
    )
    group = RuleGroup("solve", rules)
    session = ForwardEngine(()).create_session((_fact("start"),))

    result = session.run_group(
        group,
        mode=GroupExecutionMode.UNTIL,
        until=FactExists(when(parse_term("($problem state solved)"))),
    )

    assert result.added_facts == (_fact("(problem state solved)"),)
    assert _fact("unwanted") not in session.facts
    assert result.stop_reason is GroupStopReason.CONDITION_MET
    assert result.cycles == 1


def test_until_checks_a_condition_before_firing_any_rule() -> None:
    rules = parse_rules(
        """
        RULE unnecessary
        WHEN
            start
        THEN
            ADD unwanted
        END
        """
    )
    session = ForwardEngine(()).create_session(
        (_fact("start"), _fact("(case state solved)"))
    )

    result = session.run_group(
        RuleGroup("solve", rules),
        mode=GroupExecutionMode.UNTIL,
        until=FactExists(when(parse_term("($case state solved)"))),
    )

    assert result.added_facts == ()
    assert result.fired_activation_count == 0
    assert result.cycles == 0
    assert result.stop_reason is GroupStopReason.CONDITION_MET


def test_until_argument_and_group_redefinition_are_validated() -> None:
    session = ForwardEngine(()).create_session((_fact("start"),))
    original = RuleGroup("same", ())
    changed = RuleGroup(
        "same",
        parse_rules(
            """
            RULE changed
            WHEN
                start
            THEN
                ADD changed
            END
            """
        ),
    )

    with pytest.raises(ValueError, match="requires a stop condition"):
        session.run_group(original, mode=GroupExecutionMode.UNTIL)
    with pytest.raises(ValueError, match="only valid in UNTIL"):
        session.run_group(
            original,
            until=FactExists(when(parse_term("start"))),
        )

    session.run_group(original)
    with pytest.raises(ValueError, match="different definition"):
        session.run_group(changed)
