from __future__ import annotations

import json
from pathlib import Path

import run_frozen_harmonic_test as frozen

ROOT = Path(__file__).resolve().parent


def test_frozen_protocol_matches_implementation_and_discovery_results() -> None:
    protocol = json.loads(
        (ROOT / "FROZEN_V3_8_TEST_PROTOCOL.json").read_text(encoding="utf-8")
    )
    frozen.verify_frozen_protocol(
        protocol,
        ROOT / "run_harmonic_feature_compression.py",
        ROOT / "results/v3_7_harmonic_feature_compression.json",
        ROOT / "results/v3_7_harmonic_feature_compression_null.json",
    )
    assert protocol["evaluation"]["open_once"] is True
    assert protocol["acceptance"]["no_retuning_after_test"] is True


def test_acceptance_requires_all_frozen_criteria() -> None:
    protocol = {
        "frozen_model": "graded_exact",
        "acceptance": {
            "minimum_gain_retention_vs_both": 0.9,
            "no_retuning_after_test": True,
        },
    }
    records = {
        "baseline": {"test_nll": 2.0},
        "both": {"test_gain_vs_baseline": 0.1},
        "graded_exact": {
            "test_nll": 1.91,
            "test_gain_vs_baseline": 0.091,
            "bootstrap_vs_baseline": {"gain_p025": 0.01},
        },
    }
    assert frozen.acceptance_decision(records, protocol)["accepted"] is True
    records["graded_exact"]["bootstrap_vs_baseline"]["gain_p025"] = -0.01
    assert frozen.acceptance_decision(records, protocol)["accepted"] is False


def test_canonical_frozen_test_passes_every_preregistered_criterion() -> None:
    result = json.loads(
        (ROOT / "results/v3_8_frozen_harmonic_test.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["experiment"]["test_opened"] is True
    assert result["acceptance"]["accepted"] is True
    assert all(result["acceptance"]["criteria"].values())
    assert result["acceptance"]["gain_retention_vs_both"] >= 0.99
