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


def test_plan_runs_maintenance_and_reports_inconsistency_first() -> None:
    (maintenance,) = parse_rule_groups(
        """
        GROUP validate
            RULE reject_bad_state
            WHEN
                bad
            THEN
                ADD inconsistent
            END
        END_GROUP
        """
    )
    (technique,) = parse_rule_groups(
        """
        GROUP technique
            RULE would_solve
            WHEN
                seed
            THEN
                ADD solved
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(
        (_fact("seed"), _fact("bad"))
    )

    result = TechniquePlan(
        (technique,),
        maintenance=(maintenance,),
    ).solve(
        session,
        solved=FactExists(when(parse_term("solved"))),
        inconsistent=FactExists(when(parse_term("inconsistent"))),
    )

    assert result.status is TechniquePlanStatus.INCONSISTENT
    assert result.attempted_groups == ()
    assert len(result.maintenance_runs) == 1


def test_plan_reports_its_effective_step_limit() -> None:
    (technique,) = parse_rule_groups(
        """
        GROUP advance
            RULE make_progress
            WHEN
                seed
            THEN
                ADD progress
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session((_fact("seed"),))

    result = TechniquePlan(
        (technique,),
        max_effective_steps=1,
    ).solve(
        session,
        solved=FactExists(when(parse_term("never_solved"))),
    )

    assert result.status is TechniquePlanStatus.LIMIT_REACHED
    assert len(result.effective_steps) == 1
