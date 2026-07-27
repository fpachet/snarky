from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_satb_level_a as satb
import run_tonal_tendency as tonal

ROOT = Path(__file__).resolve().parent


def example() -> satb.VoiceOpportunities:
    return satb.VoiceOpportunities(
        piece_ids=np.asarray(["c-major", "a-minor"]),
        offsets_previous=np.asarray([0.0, 0.0]),
        offsets_current=np.asarray([1.0, 1.0]),
        previous_pitch=np.asarray([71, 68]),
        chosen_pitch=np.asarray([72, 69]),
        previous_all=np.asarray([[71, 67, 60, 48], [76, 68, 60, 45]]),
        current_all=np.asarray([[72, 67, 60, 48], [76, 69, 60, 45]]),
        voice_index=0,
        candidate_min=60,
        candidate_max=81,
    )


def test_global_leading_tone_is_class_eleven_in_both_modes() -> None:
    opportunities = example()
    classes = tonal.tonic_relative_source_classes(
        opportunities,
        {"c-major": 0, "a-minor": 9},
    )
    assert classes.tolist() == [11, 11]


def test_key_map_wrapper_discards_only_mode_map(monkeypatch) -> None:
    expected_audit = {"pieces_audited": 1}

    def fake_maps(_score_paths):
        return {"piece": 0}, {"piece": "major"}, expected_audit

    monkeypatch.setattr(tonal, "build_tonal_status_maps", fake_maps)
    tonic_map, audit = tonal.build_key_map({"piece": object()})
    assert tonic_map == {"piece": 0}
    assert audit is expected_audit


def test_upward_semitone_conclusion_does_not_encode_context_name() -> None:
    opportunities = example()
    mask = tonal.upward_semitone_mask(
        opportunities,
        11,
        {"c-major": 0, "a-minor": 9},
    )
    assert mask[0, 72 - 60]
    assert mask[1, 69 - 60]
    assert not mask[0, 70 - 60]


def test_obligation_selection_uses_positive_tail() -> None:
    records = [
        {
            "numeric_value": value,
            "train": {
                "z_score": train_z,
                "local_log_rate_contrast": local_peak,
            },
            "validation": {
                "z_score": validation_z,
                "local_log_rate_contrast": local_peak,
            },
            "bootstrap_validation": {"positive_fraction": positive_fraction},
        }
        for value, train_z, validation_z, positive_fraction, local_peak in (
            (4, 4.0, 2.5, 0.96, 1.6),
            (11, 8.0, 5.0, 1.0, 2.0),
        )
    ]
    assert tonal.select_top_obligations(
        records, 3.0, 2.0, 0.95, 1.4, 1.5, 1
    ) == [11]


def test_canonical_tonal_artifacts_select_only_eleven_and_keep_test_sealed() -> None:
    authentic = json.loads(
        (ROOT / "results/v3_1_global_tonal_tendency.json").read_text(
            encoding="utf-8"
        )
    )
    null = json.loads(
        (ROOT / "results/v3_1_global_tonal_tendency_null.json").read_text(
            encoding="utf-8"
        )
    )
    assert authentic["model"]["selected_source_classes"] == [11]
    assert null["model"]["selected_source_classes"] == []
    assert authentic["experiment"]["test_opened"] is False
    assert null["experiment"]["test_opened"] is False
