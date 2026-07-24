from snarky import (
    Fact,
    ForwardEngine,
    MEAConflictStrategy,
    parse_rule_groups,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_mea_prefers_a_new_subgoal_to_its_still_active_parent() -> None:
    (solve,) = parse_rule_groups(
        """
        GROUP solve
            RULE generate_child
            WHEN
                (root status active)
                seed
            THEN
                ADD (child parent root)
                ADD (child status active)
            END

            RULE parent_too_early
            WHEN
                (root status active)
                (child status active)
            THEN
                ADD parent_resumed_too_early
            END

            RULE solve_child
            WHEN
                (child status active)
            THEN
                REMOVE (child status active)
                ADD (child status satisfied)
            END

            RULE complete_parent
            WHEN
                (root status active)
                (child status satisfied)
            THEN
                REMOVE (root status active)
                ADD (root status satisfied)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(
        (),
        conflict_strategy=MEAConflictStrategy(),
    ).create_session((_fact("(root status active)"), _fact("seed")))

    result = session.run_group(solve)

    assert _fact("(root status satisfied)") in session.facts
    assert _fact("parent_resumed_too_early") not in session.facts
    assert [
        selection.rule_name for selection in result.agenda_selections
    ] == ["generate_child", "solve_child", "complete_parent"]
    assert (
        result.agenda_selections[1].focus_time_tag
        > result.agenda_selections[0].focus_time_tag
    )


def test_mea_uses_source_order_as_a_deterministic_final_tie_breaker() -> None:
    (choices,) = parse_rule_groups(
        """
        GROUP choices
            RULE first
            WHEN
                (goal status active)
            THEN
                ADD first_chosen
            END

            RULE second
            WHEN
                (goal status active)
            THEN
                ADD second_chosen
            END
        END_GROUP
        """
    )
    session = ForwardEngine(
        (),
        conflict_strategy=MEAConflictStrategy(),
    ).create_session((_fact("(goal status active)"),))

    session.run_group(choices)

    assert [
        selection.rule_name for selection in session.agenda_selections
    ] == ["first", "second"]
