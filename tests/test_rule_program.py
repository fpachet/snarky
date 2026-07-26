import pytest

from snarky import (
    ChoiceEventKind,
    ChoiceSearchStatus,
    ChoiceSearchStep,
    Fact,
    ForwardEngine,
    RuleChoiceProvider,
    RuleProgram,
    SessionChoiceSearch,
    parse_rule_groups,
    parse_rule_program,
    parse_term,
)


def _group(name: str):
    return parse_rule_groups(
        f"""
        GROUP {name}
            RULE {name}_rule
            WHEN
                (object state open)
            THEN
                ADD (object visited {name})
            END
        END_GROUP
        """
    )[0]


def test_rule_program_exposes_phase_and_execution_order() -> None:
    prepare = _group("prepare")
    choose = _group("choose")
    propagate = _group("propagate")
    interpret = _group("interpret")
    program = RuleProgram(
        "example",
        preparation_groups=(prepare,),
        choice_groups=(choose,),
        propagation_groups=(propagate,),
        interpretation_groups=(interpret,),
    )

    assert tuple(group.name for group in program.search_groups) == (
        "choose",
        "propagate",
        "interpret",
    )
    assert tuple(group.name for group in program.all_groups) == (
        "prepare",
        "choose",
        "propagate",
        "interpret",
    )


def test_rule_program_rejects_ambiguous_duplicate_groups() -> None:
    group = _group("shared")

    with pytest.raises(ValueError, match="duplicate group names"):
        RuleProgram(
            "ambiguous",
            preparation_groups=(group,),
            propagation_groups=(group,),
        )


def test_program_manifest_parses_named_sequential_steps() -> None:
    prepare = _group("prepare")
    choose_plan = _group("choose_plan")
    realize = _group("realize")
    propagate = _group("propagate")

    def constraint(session) -> None:
        del session

    program = parse_rule_program(
        """
        PROGRAM staged_example
            PREPARE prepare
            STEP plan
                GROUP choose_plan
            END_STEP
            STEP realization
                GROUP realize
                CONSTRAINT geometry
            END_STEP
            PROPAGATE propagate
        END_PROGRAM
        """,
        (prepare, choose_plan, realize, propagate),
        constraints={"geometry": constraint},
    )

    assert program.manifest() == (
        ("preparation", ("prepare",)),
        ("step:plan", ("choose_plan",)),
        ("step:realization", ("realize", "CONSTRAINT geometry")),
        ("propagation", ("propagate",)),
        ("interpretation", ()),
    )
    assert program.steps[1].propagators == (constraint,)


def test_staged_search_backtracks_across_a_step_boundary() -> None:
    plan, realization, reject = parse_rule_groups(
        """
        GROUP choose_plan
            RULE choose_color
            WHEN
                (problem state open)
            THEN
                CHOICE (problem color $color)
                FROM
                    (palette color $color)
                END_CHOICE
            END
        END_GROUP

        GROUP choose_realization
            RULE choose_shape
            WHEN
                (problem color $color)
            THEN
                CHOICE (problem shape $shape)
                FROM
                    (palette shape $shape)
                END_CHOICE
            END
        END_GROUP

        GROUP reject_bad_combination
            RULE reject_blue_square
            WHEN
                (problem color blue)
                (problem shape square)
            THEN
                ADD (problem state contradiction)
            END
        END_GROUP
        """
    )
    plan_provider = RuleChoiceProvider((plan,))
    realization_provider = RuleChoiceProvider((realization,))
    session = ForwardEngine(()).create_session(
        (
            Fact(parse_term("(problem state open)")),
            Fact(parse_term("(palette color blue)")),
            Fact(parse_term("(palette color red)")),
            Fact(parse_term("(palette shape square)")),
        )
    )
    result = SessionChoiceSearch(
        (reject,),
        lambda current: (),
        lambda current: Fact(parse_term("(problem color red)")) in current.facts
        and Fact(parse_term("(problem shape square)")) in current.facts,
        lambda current: Fact(
            parse_term("(problem state contradiction)")
        )
        in current.facts,
        steps=(
            ChoiceSearchStep(
                "plan",
                plan_provider.propagation_groups,
                plan_provider,
            ),
            ChoiceSearchStep(
                "realization",
                realization_provider.propagation_groups,
                realization_provider,
            ),
        ),
    ).solve(session)

    assert result.status is ChoiceSearchStatus.SOLVED
    assert Fact(parse_term("(problem color red)")) in result.solutions[0].session.facts
    assert any(event.kind is ChoiceEventKind.STEP for event in result.events)
    assert result.failed_branches == 1
