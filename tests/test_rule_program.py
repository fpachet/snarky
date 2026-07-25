import pytest

from snarky import RuleProgram, parse_rule_groups


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
