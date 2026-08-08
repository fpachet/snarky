from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from harmonizer.official_manual import DEFAULT_RULEBASE, audit_musicxml
from snarky import (
    ChoiceEventKind,
    ChoiceSearchStatus,
    Fact,
    ForwardEngine,
    MRVChoicePolicy,
    RuleChoiceProvider,
    SessionChoiceSearch,
    parse_factor_groups,
    parse_rule_groups,
    parse_term,
)

MANUAL_ROOT = Path(
    "/Users/francoispachet/IdeaProjects/cours_harmonie/bach-corpus-manual"
)
REPOSITORY = Path(__file__).resolve().parents[1]
V33_GENERATION = REPOSITORY / "harmonizer/generated/two_loop_full_v33_bwv108_6.musicxml"
EMPIRICAL_GENERATION = (
    REPOSITORY / "harmonizer/generated/official_manual_empirical_bwv108_6.musicxml"
)

TARGETS = {
    "parallel_fifth": ("violates", "MANUAL-PARALLEL-FIFTH"),
    "parallel_octave": ("violates", "MANUAL-PARALLEL-OCTAVE"),
    "direct_fifth": ("violates", "MANUAL-DIRECT-FIFTH"),
    "voice_crossing": ("violates", "MANUAL-VOICE-CROSSING"),
    "voice_overlap": ("violates", "MANUAL-VOICE-OVERLAP"),
    "common_tone": ("satisfies", "MANUAL-COMMON-TONE"),
    "contrary_motion": ("satisfies", "MANUAL-CONTRARY-OUTER"),
    "compensated_leap": ("satisfies", "MANUAL-COMPENSATED-LEAP"),
    "suspension_resolution": (
        "satisfies",
        "MANUAL-SUSPENSION-RESOLUTION",
    ),
    "leading_tone_resolution": ("satisfies", "MANUAL-LEADING-TONE"),
    "singable_line": ("violates", "MANUAL-SINGABLE-LINE"),
    "active_inner_voice": ("violates", "MANUAL-ACTIVE-INNER-VOICE"),
}


def test_official_manual_programs_parse_and_keep_factors_separate() -> None:
    rule_groups = parse_rule_groups(
        (DEFAULT_RULEBASE / "official_manual.rules").read_text(encoding="utf-8")
    )
    constraint_groups = parse_rule_groups(
        (DEFAULT_RULEBASE / "profile_constraints.rules").read_text(encoding="utf-8")
    )
    factor_groups = parse_factor_groups(
        (DEFAULT_RULEBASE / "official_manual.factors").read_text(encoding="utf-8")
    )
    empirical_groups = parse_rule_groups(
        (DEFAULT_RULEBASE / "empirical_budgets.rules").read_text(encoding="utf-8")
    )
    acceptance_groups = parse_rule_groups(
        (DEFAULT_RULEBASE / "empirical_acceptance.rules").read_text(encoding="utf-8")
    )

    assert len(rule_groups) == 4
    assert len(constraint_groups) == 1
    assert len(empirical_groups) == 1
    assert len(acceptance_groups) == 1
    assert {group.name for group in factor_groups} == {
        "official_manual_confirmed_voice_leading",
        "official_manual_confirmed_tendency",
    }


def test_official_manual_profiles_expose_three_distinct_semantics() -> None:
    payload = yaml.safe_load(
        (DEFAULT_RULEBASE / "profiles.yaml").read_text(encoding="utf-8")
    )
    profiles = payload["profiles"]

    assert set(profiles) == {
        "diagnostic",
        "bach_empirical",
        "pedagogical_strict",
    }
    assert profiles["diagnostic"]["hard_rules"] == []
    assert profiles["pedagogical_strict"]["hard_rules"]


@pytest.mark.skipif(not MANUAL_ROOT.exists(), reason="manual companion repo absent")
def test_all_twelve_manual_counterfactuals_change_the_targeted_diagnostic() -> None:
    checked = 0
    for directory in sorted((MANUAL_ROOT / "rules").iterdir()):
        metadata_path = directory / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        relation, rule_id = TARGETS[metadata["validation"]["code"]]
        authentic = audit_musicxml(directory / "authentic.musicxml")
        counterfactual = audit_musicxml(directory / "counterfactual.musicxml")
        authentic_count = authentic.count(relation, rule_id)
        counterfactual_count = counterfactual.count(relation, rule_id)

        if relation == "violates":
            assert counterfactual_count > authentic_count, directory.name
        else:
            assert authentic_count > counterfactual_count, directory.name
        checked += 1

    assert checked == 12


@pytest.mark.skipif(not MANUAL_ROOT.exists(), reason="manual companion repo absent")
def test_strict_profile_turns_a_targeted_violation_into_a_contradiction() -> None:
    variant = MANUAL_ROOT / "rules/rule_001_parallel_fifths/counterfactual.musicxml"

    diagnostic = audit_musicxml(variant, profile="pedagogical_strict")

    assert diagnostic.contradiction
    assert any(
        row["rule_id"] == "MANUAL-PARALLEL-FIFTH" for row in diagnostic.hard_violations
    )


@pytest.mark.skipif(not MANUAL_ROOT.exists(), reason="manual companion repo absent")
def test_diagnostic_profile_never_confuses_a_factor_with_a_hard_constraint() -> None:
    variant = MANUAL_ROOT / "rules/rule_001_parallel_fifths/counterfactual.musicxml"

    diagnostic = audit_musicxml(variant)

    assert not diagnostic.contradiction
    assert diagnostic.hard_violations == ()
    assert any(
        row["factor"] == "manual_parallel_fifth"
        for row in diagnostic.factor_activations
    )


def test_repair_choice_backtracks_from_a_preferred_invalid_candidate() -> None:
    choose, validate = parse_rule_groups(
        (DEFAULT_RULEBASE / "repair_choices.rules").read_text(encoding="utf-8")
    )
    provider = RuleChoiceProvider((choose,))
    session = ForwardEngine(()).create_session(
        tuple(
            Fact(parse_term(text))
            for text in (
                "(repair problem exercise)",
                "(exercise candidate counterfactual)",
                "(exercise candidate authentic)",
                "(counterfactual repair_weight 2)",
                "(authentic repair_weight 1)",
                "(counterfactual hard_violation MANUAL-PARALLEL-FIFTH)",
            )
        )
    )
    contradiction = Fact(parse_term("(search state contradiction)"))
    authentic = Fact(parse_term("(exercise selected authentic)"))

    result = SessionChoiceSearch(
        (validate,),
        provider,
        lambda current: authentic in current.facts,
        lambda current: contradiction in current.facts,
        policy=MRVChoicePolicy(prefer_high_weight=True),
        max_solutions=1,
    ).solve(session)

    assert result.status is ChoiceSearchStatus.SOLVED
    assert authentic in result.solutions[0].session.facts
    assert any(event.kind is ChoiceEventKind.BACKTRACK for event in result.events)


@pytest.mark.skipif(not MANUAL_ROOT.exists(), reason="manual companion repo absent")
def test_independent_score_audit_exposes_global_voice_criteria() -> None:
    score = MANUAL_ROOT / "rules/rule_012_active_inner_voices/authentic.musicxml"

    diagnostic = audit_musicxml(score)

    assert {row["voice"] for row in diagnostic.voice_summaries} == {
        "soprano",
        "alto",
        "tenor",
        "bass",
    }
    assert all("step_rate" in row for row in diagnostic.voice_summaries)
    assert {row["rule_id"] for row in diagnostic.criteria} == {
        rule_id for _, rule_id in TARGETS.values()
    }


def test_empirical_budget_protocol_never_uses_test_for_fitting() -> None:
    payload = yaml.safe_load(
        (DEFAULT_RULEBASE / "empirical_budgets.yaml").read_text(encoding="utf-8")
    )

    assert payload["protocol"]["threshold_estimation_split"] == "train251"
    assert payload["protocol"]["promotion_split"] == "validation50"
    assert not payload["protocol"]["test_split_used_for_fit_or_promotion"]
    assert payload["maximum_exceeded_budgets"] == 2
    assert {row["group_id"] for row in payload["group_budgets"]} == {
        "contrapuntal",
        "tendency",
        "leap",
        "repetition",
        "conjunct_motion",
    }


@pytest.mark.skipif(
    not (V33_GENERATION.exists() and EMPIRICAL_GENERATION.exists()),
    reason="generated comparison scores absent",
)
def test_empirical_profile_rejects_v33_and_accepts_new_generation() -> None:
    v33 = audit_musicxml(V33_GENERATION, profile="bach_empirical")
    improved = audit_musicxml(EMPIRICAL_GENERATION, profile="bach_empirical")

    assert v33.contradiction
    assert {row["metric_id"] for row in v33.empirical_budget_exceedances} == {
        "alto_longest_repeat_run",
        "tenor_maximum_leap",
        "bass_longest_repeat_run",
    }
    assert not improved.contradiction
    assert [row["metric_id"] for row in improved.empirical_budget_exceedances] == [
        "alto_longest_repeat_run"
    ]
