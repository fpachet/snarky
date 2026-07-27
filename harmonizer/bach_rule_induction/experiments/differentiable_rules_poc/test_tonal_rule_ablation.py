from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_satb_level_a as satb
import run_tonal_rule_ablation as ablation

ROOT = Path(__file__).resolve().parent


def alto_example() -> satb.VoiceOpportunities:
    return satb.VoiceOpportunities(
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


def test_harmonic_rule_is_nested_inside_numeric_proxy() -> None:
    data = alto_example()
    tonic = {"major": 0}
    mode = {"major": "major"}
    proxy = ablation.proxy_rule_mask(data, tonic, mode)
    harmonic = ablation.harmonic_rule_mask(data, tonic, mode)
    assert harmonic.any()
    assert np.all(harmonic <= proxy)
    assert harmonic[0, 72 - data.candidate_min]


def test_harmonic_rule_rejects_non_tonic_target_signature() -> None:
    data = alto_example()
    data.current_all[0, 0] = 65
    harmonic = ablation.harmonic_rule_mask(
        data,
        {"major": 0},
        {"major": "major"},
    )
    assert not harmonic.any()


def test_harmonic_mask_does_not_read_observed_alto_target() -> None:
    data = alto_example()
    expected = ablation.harmonic_rule_mask(
        data,
        {"major": 0},
        {"major": "major"},
    )
    data.current_all[0, data.voice_index] = 61
    actual = ablation.harmonic_rule_mask(
        data,
        {"major": 0},
        {"major": "major"},
    )
    assert np.array_equal(actual, expected)


def test_piece_bootstrap_reports_positive_deterministic_gain() -> None:
    result = ablation.bootstrap_nll_gain_by_piece(
        reference_losses=np.asarray([2.0, 2.0, 3.0]),
        alternative_losses=np.asarray([1.0, 1.5, 2.0]),
        piece_ids=np.asarray(["a", "a", "b"]),
        replicates=100,
        seed=17,
    )
    assert result["positive_fraction"] == 1.0
    assert result["gain_p025"] > 0


def comparison(result: dict, name: str) -> dict:
    return next(
        record
        for record in result["model"]["comparisons"]
        if record["comparison"] == name
    )


def test_canonical_ablation_separates_real_signal_from_null() -> None:
    authentic = json.loads(
        (ROOT / "results/v3_6_tonal_rule_ablation.json").read_text(
            encoding="utf-8"
        )
    )
    null = json.loads(
        (ROOT / "results/v3_6_tonal_rule_ablation_null.json").read_text(
            encoding="utf-8"
        )
    )
    assert authentic["experiment"]["test_opened"] is False
    assert null["experiment"]["test_opened"] is False
    authentic_coverage = authentic["model"]["rule_coverage"]
    assert authentic_coverage[ablation.PROXY_RULE_ID]["validation"][
        "conclusion_rate"
    ] == 1.0
    assert authentic_coverage[ablation.HARMONIC_RULE_ID]["train"][
        "opportunities"
    ] == 43
    assert authentic_coverage[ablation.HARMONIC_RULE_ID]["train"][
        "conclusion_chosen"
    ] == 41
    assert comparison(authentic, "baseline_to_both")[
        "bootstrap_validation"
    ]["gain_p025"] > 0
    assert comparison(
        authentic,
        "harmonic_to_both_proxy_increment",
    )["bootstrap_validation"]["gain_p025"] > 0
    assert comparison(
        authentic,
        "proxy_to_both_harmonic_increment",
    )["bootstrap_validation"]["positive_fraction"] >= 0.95
    for name in (
        "baseline_to_proxy",
        "baseline_to_harmonic",
        "baseline_to_both",
    ):
        assert comparison(null, name)["bootstrap_validation"]["gain_p025"] <= 0
