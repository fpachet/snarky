from snarky import (
    Fact,
    FactExists,
    ForwardEngine,
    TechniquePlan,
    TechniquePlanStatus,
    parse_rule_groups,
    parse_term,
    when,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_plan_restarts_at_the_easiest_group_after_progress() -> None:
    easier, harder = parse_rule_groups(
        """
        GROUP easier
            RULE finish
            WHEN
                intermediate
            THEN
                ADD solved
            END
        END_GROUP

        GROUP harder
            RULE unlock
            WHEN
                seed
            THEN
                ADD intermediate
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session((_fact("seed"),))

    result = TechniquePlan((easier, harder)).solve(
        session,
        solved=FactExists(when(parse_term("solved"))),
    )

    assert result.status is TechniquePlanStatus.SOLVED
    assert result.attempted_groups == ("easier", "harder", "easier")
    assert tuple(step.group_name for step in result.effective_steps) == (
        "harder",
        "easier",
    )


def test_plan_reports_stuck_after_one_ineffective_pass() -> None:
    (technique,) = parse_rule_groups(
        """
        GROUP unavailable
            RULE needs_other_fact
            WHEN
                other
            THEN
                ADD solved
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session((_fact("seed"),))

    result = TechniquePlan((technique,)).solve(
        session,
        solved=FactExists(when(parse_term("solved"))),
    )

    assert result.status is TechniquePlanStatus.STUCK
    assert result.attempted_groups == ("unavailable",)
    assert result.effective_steps == ()
