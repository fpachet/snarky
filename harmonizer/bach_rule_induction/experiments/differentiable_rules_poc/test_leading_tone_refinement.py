from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_leading_tone_refinement as refinement
import run_satb_level_a as satb

ROOT = Path(__file__).resolve().parent


def example(voice_index: int) -> satb.VoiceOpportunities:
    candidate_min, candidate_max = satb.VOICE_RANGES[voice_index]
    return satb.VoiceOpportunities(
        piece_ids=np.asarray(["c-major"]),
        offsets_previous=np.asarray([0.0]),
        offsets_current=np.asarray([1.0]),
        previous_pitch=np.asarray([71]),
        chosen_pitch=np.asarray([72]),
        previous_all=np.asarray([[71, 67, 62, 55]]),
        current_all=np.asarray([[72, 67, 60, 48]]),
        voice_index=voice_index,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )


def test_refinement_uses_numeric_bass_transition_and_voice() -> None:
    soprano = example(0)
    mask = refinement.refinement_mask(
        soprano,
        subject_voice=0,
        source_bass_class=7,
        target_bass_class=0,
        tonic_by_piece={"c-major": 0},
    )
    assert mask[0, 72 - soprano.candidate_min]
    wrong_voice = refinement.refinement_mask(
        example(1),
        subject_voice=0,
        source_bass_class=7,
        target_bass_class=0,
        tonic_by_piece={"c-major": 0},
    )
    assert not wrong_voice.any()


def test_refinement_can_gate_the_same_numeric_context_by_mode() -> None:
    soprano = example(0)
    major = refinement.refinement_mask(
        soprano,
        subject_voice=0,
        source_bass_class=7,
        target_bass_class=0,
        tonic_by_piece={"c-major": 0},
        required_mode="major",
        mode_by_piece={"c-major": "major"},
    )
    minor = refinement.refinement_mask(
        soprano,
        subject_voice=0,
        source_bass_class=7,
        target_bass_class=0,
        tonic_by_piece={"c-major": 0},
        required_mode="minor",
        mode_by_piece={"c-major": "major"},
    )
    assert major.any()
    assert not minor.any()


def test_known_numeric_triples_receive_only_posthoc_names() -> None:
    assert (
        refinement.interpretation(
            {
                "mode": "all",
                "subject_voice_index": 0,
                "source_bass_class": 7,
                "target_bass_class": 0,
            }
        )
        == "OUTER_DOMINANT_TO_TONIC_CADENTIAL_PROXY"
    )
    assert (
        refinement.interpretation(
            {
                "mode": "all",
                "subject_voice_index": 1,
                "source_bass_class": 2,
                "target_bass_class": 0,
            }
        )
        == "LEADING_TONE_CHORD_6_TO_TONIC_ROOT_PROXY"
    )
    assert (
        refinement.interpretation(
            {
                "mode": "major",
                "subject_voice_index": 2,
                "source_bass_class": 5,
                "target_bass_class": 4,
            }
        )
        == "DOMINANT_SEVENTH_42_TO_TONIC_6_PROXY"
    )
    assert (
        refinement.interpretation(
            {
                "mode": "minor",
                "subject_voice_index": 1,
                "source_bass_class": 7,
                "target_bass_class": 3,
            }
        )
        == "MINOR_DOMINANT_TO_MEDIANT_DECEPTIVE_PROXY"
    )


def test_case_audit_separates_modes_and_outcomes() -> None:
    alto = satb.VoiceOpportunities(
        piece_ids=np.asarray(["major-piece", "minor-piece"]),
        offsets_previous=np.asarray([0.0, 4.0]),
        offsets_current=np.asarray([1.0, 5.0]),
        previous_pitch=np.asarray([71, 68]),
        chosen_pitch=np.asarray([72, 67]),
        previous_all=np.asarray([[76, 71, 62, 50], [72, 68, 60, 47]]),
        current_all=np.asarray([[76, 72, 60, 48], [72, 67, 60, 45]]),
        voice_index=1,
        candidate_min=55,
        candidate_max=74,
    )
    records = [
        {
            "mode": "all",
            "subject_voice_index": 1,
            "source_bass_class": 2,
            "target_bass_class": 0,
        }
    ]
    refinement.audit_selected_cases(
        records,
        [example(0), alto, example(2), example(3)],
        {"major-piece": 0, "minor-piece": 9},
        {"major-piece": "major", "minor-piece": "minor"},
        "validation",
        example_limit=1,
    )
    assert records[0]["validation_by_mode"] == {
        "major": {
            "opportunities": 1,
            "resolutions": 1,
            "exceptions": 0,
            "resolution_rate": 1.0,
        },
        "minor": {
            "opportunities": 1,
            "resolutions": 0,
            "exceptions": 1,
            "resolution_rate": 0.0,
        },
    }
    assert [row["resolved"] for row in records[0]["validation_examples"]] == [
        True,
        False,
    ]


def test_family_calibration_uses_maximum_joint_replication_statistic() -> None:
    def record(name, train_z, validation_z, train_rate=0.8, validation_rate=0.8):
        return {
            "mode": "major",
            "subject_voice_index": 0,
            "subject_voice": name,
            "source_bass_class": 7,
            "target_bass_class": 0,
            "train": {
                "testable_opportunities": 40,
                "observed_rate": train_rate,
                "z_score": train_z,
            },
            "validation": {
                "testable_opportunities": 10,
                "observed_rate": validation_rate,
                "z_score": validation_z,
            },
        }

    summary = refinement.family_calibration_summary(
        [
            record("train-only", 20.0, 1.0),
            record("replicated", 4.0, 3.0),
            record("low-rate", 9.0, 8.0, validation_rate=0.4),
        ],
        min_train_support=20,
        min_validation_support=8,
        min_train_confirmation=0.65,
        min_validation_confirmation=0.65,
        min_train_z=3.0,
        min_validation_z=2.0,
    )
    assert summary["maximum_supported"]["subject_voice"] == "low-rate"
    assert summary["maximum_confirmation_gated"]["subject_voice"] == "replicated"
    assert summary["maximum_confirmation_gated"]["joint_min_z"] == 3.0
    assert summary["threshold_passing_candidate_count"] == 1


def test_canonical_refinement_artifacts_keep_test_sealed() -> None:
    v2 = json.loads(
        (ROOT / "results/v3_2_leading_tone_refinement.json").read_text(
            encoding="utf-8"
        )
    )
    v2_null = json.loads(
        (ROOT / "results/v3_2_leading_tone_refinement_null.json").read_text(
            encoding="utf-8"
        )
    )
    v3 = json.loads(
        (ROOT / "results/v3_3_mode_stratified_leading_tone.json").read_text(
            encoding="utf-8"
        )
    )
    v3_null = json.loads(
        (ROOT / "results/v3_3_mode_stratified_leading_tone_null.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(v2["model"]["selected_refinements"]) == 4
    assert v2_null["model"]["selected_refinements"] == []
    assert len(v3["model"]["selected_refinements"]) == 7
    assert v3_null["model"]["selected_refinements"] == []
    assert all(
        artifact["experiment"]["test_opened"] is False
        for artifact in (v2, v2_null, v3, v3_null)
    )
