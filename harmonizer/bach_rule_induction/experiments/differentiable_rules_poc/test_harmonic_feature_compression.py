from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_harmonic_feature_compression as compression
import run_tonal_rule_ablation as ablation

ROOT = Path(__file__).resolve().parent


def example() -> tuple:
    data = ablation.satb.VoiceOpportunities(
        piece_ids=np.asarray(["major"]),
        offsets_previous=np.asarray([0.0]),
        offsets_current=np.asarray([1.0]),
        previous_pitch=np.asarray([71]),
        chosen_pitch=np.asarray([72]),
        previous_all=np.asarray([[65, 71, 62, 50]]),
        current_all=np.asarray([[64, 72, 67, 52]]),
        voice_index=1,
        candidate_min=55,
        candidate_max=74,
    )
    return data, {"major": 0}, {"major": "major"}


def test_statuses_are_nested_and_graded_feature_has_two_levels() -> None:
    data, tonics, modes = example()
    masks = compression.feature_masks(data, tonics, modes)
    proxy = masks[ablation.PROXY_RULE_ID]
    for spec in compression.STATUS_SPECS:
        assert np.all(masks[spec.rule_id] <= proxy)
    graded, _ = compression.model_rule_columns("graded_exact", masks)
    assert graded is not None
    assert graded[0, 72 - data.candidate_min, 0] == 2


def test_dominant_core_accepts_dominant_or_leading_tone_colour() -> None:
    tonics = np.asarray([0, 0, 0])
    states = np.asarray(
        [
            [65, 71, 62, 50],
            [67, 71, 62, 50],
            [66, 71, 62, 50],
        ]
    )
    assert compression.dominant_function_rows(states, tonics).tolist() == [
        True,
        True,
        False,
    ]


def test_duplicate_components_keep_known_variants_together() -> None:
    pieces = ["a", "b", "c"]
    payload = {
        "audit": {
            "soprano_duplicate_groups": [
                {"members": ["a", "b"], "new_split": "train"}
            ]
        }
    }
    assert sorted(
        compression.duplicate_components(pieces, payload)
    ) == [["a", "b"], ["c"]]


def test_selection_requires_retention_and_positive_bootstrap_bound() -> None:
    records = {}
    for model_name in compression.CROSSFIT_MODELS:
        records[model_name] = {
            **compression.MODEL_METADATA[model_name],
            "description_bits": compression.description_bits(model_name),
            "crossfit_nll": 1.0,
            "crossfit_gain_retention_vs_both": 1.0,
            "bootstrap_vs_baseline": {"gain_p025": 0.1},
        }
    records["proxy"]["crossfit_gain_retention_vs_both"] = 0.9
    selected = compression.select_compressed_model(records, 0.95)
    assert selected["selected_model"] == "graded_exact"


def test_canonical_compression_selects_signal_only_in_authentic_data() -> None:
    authentic = json.loads(
        (
            ROOT / "results/v3_7_harmonic_feature_compression.json"
        ).read_text(encoding="utf-8")
    )
    null = json.loads(
        (
            ROOT / "results/v3_7_harmonic_feature_compression_null.json"
        ).read_text(encoding="utf-8")
    )
    assert authentic["experiment"]["test_opened"] is False
    assert authentic["atypical_audit"]["train"]["atypical_count"] == 13
    assert authentic["selection"]["selected_model"] == "graded_exact"
    selected = authentic["models"]["graded_exact"]
    assert selected["parameter_count"] == 1
    assert selected["crossfit_gain_retention_vs_both"] >= 0.99
    assert selected["bootstrap_vs_baseline"]["gain_p025"] > 0
    assert null["selection"]["selected_model"] is None
