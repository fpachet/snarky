from __future__ import annotations

import pytest

from harmonizer.bach_rule_induction import learned_generator
from harmonizer.bach_rule_induction.learned_generator import (
    evaluate_learned_transition,
    generate_with_learned_rules,
)


def _rule_ids(source: tuple[int, ...], target: tuple[int, ...]) -> set[str]:
    evaluation = evaluate_learned_transition(source, target)
    return {activation.rule_id for activation in evaluation.activations}


def test_autonomous_rules_detect_level_a_patterns() -> None:
    assert "R-LEARNED-MELODY-002" in _rule_ids(
        (72, 64, 60, 48),
        (72, 70, 60, 48),
    )
    assert "R-LEARNED-OVERLAP-001" in _rule_ids(
        (72, 64, 55, 48),
        (72, 53, 55, 48),
    )
    assert "R-LEARNED-PARALLEL-001" in _rule_ids(
        (72, 64, 55, 48),
        (74, 66, 57, 50),
    )
    assert "R-LEARNED-PARALLEL-002" in _rule_ids(
        (67, 64, 55, 48),
        (69, 66, 57, 50),
    )
    assert "R-LEARNED-DIRECT-001" in _rule_ids(
        (67, 64, 55, 48),
        (72, 67, 60, 60),
    )
    assert "R-LEARNED-DIRECT-002" in _rule_ids(
        (67, 64, 55, 48),
        (74, 67, 60, 55),
    )


def test_exact_tonal_context_has_learned_strength_two() -> None:
    evaluation = evaluate_learned_transition(
        (74, 71, 65, 50),
        (76, 72, 67, 52),
    )
    tonal = tuple(
        activation
        for activation in evaluation.activations
        if activation.rule_id == "R-LEARNED-LEADING-001"
    )

    assert len(tonal) == 1
    assert tonal[0].strength == 2
    assert tonal[0].log_contribution == pytest.approx(2 * 2.0214869830878857)


def test_diagnostic_generation_uses_only_learned_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        learned_generator,
        "_scaffolding_pools",
        lambda _profile: ((64, 67), (57, 60), (48, 52)),
    )

    first = generate_with_learned_rules((69, 71, 72, 69), seed=7)
    second = generate_with_learned_rules((69, 71, 72, 69), seed=7)

    assert first == second
    assert first.profile_id == "S-LEARNED"
    assert tuple(voicing[0] for voicing in first.voicings) == first.soprano
    assert first.decisions == 4
    assert all(
        activation.rule_id.startswith("R-LEARNED-") for activation in first.activations
    )
