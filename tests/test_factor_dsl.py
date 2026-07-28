from __future__ import annotations

import math

import pytest

from snarky import (
    Atom,
    Fact,
    FactorModel,
    FactorParameter,
    ParseError,
    Triple,
    WeightedFactor,
    evaluate_factor_model,
    parse_factor_groups,
    parse_factors,
)


def _facts() -> tuple[Fact, ...]:
    return (
        Fact(Triple(Atom("decision"), Atom("candidate"), Atom("do"))),
        Fact(Triple(Atom("decision"), Atom("candidate"), Atom("re"))),
        Fact(Triple(Atom("do"), Atom("small_motion"), Atom("yes"))),
        Fact(Triple(Atom("re"), Atom("small_motion"), Atom("yes"))),
        Fact(Triple(Atom("do"), Atom("chord_tone"), Atom("yes"))),
        Fact(Triple(Atom("do"), Atom("repeat"), Atom("yes"))),
    )


def _factor_text() -> str:
    return """
    FACTOR_GROUP learned_bach
        FACTOR small_motion
        SCOPE SEQ[$decision $candidate]
        LOG_WEIGHT 0.7
        WHEN
            ($decision candidate $candidate)
            ($candidate small_motion yes)
        END_FACTOR

        FACTOR chord_tone
        SCOPE SEQ[$decision $candidate]
        LOG_WEIGHT 1.1
        WHEN
            ($decision candidate $candidate)
            ($candidate chord_tone yes)
        END_FACTOR

        FACTOR attacked_repeat
        SCOPE SEQ[$decision $candidate]
        LOG_WEIGHT -0.8
        WHEN
            ($decision candidate $candidate)
            ($candidate repeat yes)
        END_FACTOR
    END_FACTOR_GROUP
    """


def test_factor_syntax_has_no_then_or_actions() -> None:
    (group,) = parse_factor_groups(_factor_text())

    assert group.name == "learned_bach"
    assert [factor.name for factor in group.factors] == [
        "small_motion",
        "chord_tone",
        "attacked_repeat",
    ]
    assert group.factors[0].parameter == FactorParameter("small_motion", 0.7)

    with pytest.raises(ParseError):
        parse_factors(
            """
            FACTOR impure
            SCOPE $candidate
            LOG_WEIGHT 1
            WHEN
                (decision candidate $candidate)
            THEN
                ADD ($candidate activated impure)
            END_FACTOR
            """
        )


def test_factor_evaluation_is_pure_additive_and_explainable() -> None:
    (group,) = parse_factor_groups(_factor_text())
    model = FactorModel("toy", (group,))
    facts = _facts()
    before = tuple(facts)

    evaluation = evaluate_factor_model(model, facts)

    assert facts == before
    do_scope = next(
        activation.scope
        for activation in evaluation.activations
        if activation.factor_name == "chord_tone"
    )
    re_scope = next(
        activation.scope
        for activation in evaluation.activations
        if activation.factor_name == "small_motion" and activation.scope != do_scope
    )
    assert math.isclose(evaluation.score_for_scope(do_scope), 1.0)
    assert math.isclose(evaluation.score_for_scope(re_scope), 0.7)
    assert {
        activation.factor_name for activation in evaluation.for_scope(do_scope)
    } == {"small_motion", "chord_tone", "attacked_repeat"}


def test_factor_is_counted_once_per_ground_scope_with_multiple_witnesses() -> None:
    (factor,) = parse_factors(
        """
        FACTOR supported
        SCOPE $candidate
        LOG_WEIGHT 2.0
        WHEN
            ($candidate evidence $witness)
        END_FACTOR
        """
    )
    facts = (
        Fact(Triple(Atom("do"), Atom("evidence"), Atom("one"))),
        Fact(Triple(Atom("do"), Atom("evidence"), Atom("two"))),
    )

    evaluation = evaluate_factor_model(
        FactorModel(
            "deduplicated",
            (
                parse_factor_groups(
                    """
            FACTOR_GROUP learned
                FACTOR supported
                SCOPE $candidate
                LOG_WEIGHT 2.0
                WHEN
                    ($candidate evidence $witness)
                END_FACTOR
            END_FACTOR_GROUP
            """
                )[0],
            ),
        ),
        facts,
    )

    assert factor.name == "supported"
    assert len(evaluation.activations) == 1
    assert evaluation.activations[0].witness_count == 2
    assert evaluation.log_score == 2.0


def test_changing_a_parameter_does_not_change_factor_activations() -> None:
    (group,) = parse_factor_groups(_factor_text())
    original = evaluate_factor_model(FactorModel("original", (group,)), _facts())
    first = group.factors[0]
    changed = WeightedFactor(
        first.definition,
        FactorParameter(first.name, 4.2),
    )
    changed_group = type(group)(
        group.name,
        (changed, *group.factors[1:]),
    )
    refitted = evaluate_factor_model(
        FactorModel("refitted", (changed_group,)),
        _facts(),
    )

    assert [
        (activation.factor_name, activation.scope)
        for activation in original.activations
    ] == [
        (activation.factor_name, activation.scope)
        for activation in refitted.activations
    ]
    assert original.log_score != refitted.log_score


def test_factor_scope_must_be_bound_and_weights_must_be_finite() -> None:
    with pytest.raises(ParseError, match="unbound variables"):
        parse_factors(
            """
            FACTOR broken_scope
            SCOPE $other
            LOG_WEIGHT 1
            WHEN
                (decision candidate $candidate)
            END_FACTOR
            """
        )
    with pytest.raises(ParseError, match="finite"):
        parse_factors(
            """
            FACTOR broken_weight
            SCOPE $candidate
            LOG_WEIGHT inf
            WHEN
                (decision candidate $candidate)
            END_FACTOR
            """
        )


def test_factor_activations_are_not_facts_and_cannot_chain() -> None:
    (group,) = parse_factor_groups(
        """
        FACTOR_GROUP isolated
            FACTOR first
            SCOPE $candidate
            LOG_WEIGHT 1
            WHEN
                (decision candidate $candidate)
            END_FACTOR

            FACTOR would_require_side_effect
            SCOPE $candidate
            LOG_WEIGHT 100
            WHEN
                ($candidate factor_activation first)
            END_FACTOR
        END_FACTOR_GROUP
        """
    )

    evaluation = evaluate_factor_model(FactorModel("isolated", (group,)), _facts())

    assert {activation.factor_name for activation in evaluation.activations} == {
        "first"
    }
