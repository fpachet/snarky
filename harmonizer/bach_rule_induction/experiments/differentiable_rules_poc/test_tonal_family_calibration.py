from __future__ import annotations

import json
from pathlib import Path

import run_tonal_family_calibration as calibration

ROOT = Path(__file__).resolve().parent


def test_empirical_max_p_value_includes_finite_sample_correction() -> None:
    result = calibration.empirical_max_p_value(3.0, [None, 2.0, 3.0, 4.0])
    assert result == {
        "exceedances": 2,
        "replicates": 4,
        "p_value": 0.6,
    }


def test_candidate_result_uses_weaker_split_as_joint_statistic() -> None:
    record = {
        "mode": "minor",
        "subject_voice": "Tenor",
        "subject_voice_index": 2,
        "source_bass_class": 7,
        "target_bass_class": 8,
        "interpretation": "MINOR_DECEPTIVE_CADENCE_PROXY",
        "train": {"z_score": 8.0},
        "validation": {"z_score": 3.0},
    }
    result = calibration.candidate_result(record, [2.0] * 19)
    assert result["joint_min_z"] == 3.0
    assert result["empirical_fwer"]["p_value"] == 0.05
    assert result["classification"] == "PASSES_EMPIRICAL_FWER_0_05"


def test_quantiles_ignore_replicates_without_an_eligible_null_candidate() -> None:
    result = calibration.calibration_quantiles([None, 1.0, 2.0, 3.0])
    assert result == {
        "q50": 2.0,
        "q90": 3.0,
        "q95": 3.0,
        "maximum": 3.0,
    }


def test_canonical_family_calibration_retains_one_context_and_seals_test() -> None:
    result = json.loads(
        (ROOT / "results/v3_4_tonal_family_calibration.json").read_text(
            encoding="utf-8"
        )
    )
    retained = [
        record
        for record in result["candidate_results"]
        if record["classification"] == "PASSES_EMPIRICAL_FWER_0_05"
    ]
    assert result["experiment"]["test_opened"] is False
    assert result["calibration"]["replicates"] == 49
    assert result["calibration"]["defined_null_maxima"] == 49
    assert result["calibration"]["null_maximum_quantiles"]["maximum"] < 8.05
    assert [
        (
            record["mode"],
            record["subject_voice"],
            record["source_bass_class"],
            record["target_bass_class"],
        )
        for record in retained
    ] == [("major", "Alto", 2, 4)]
    assert retained[0]["empirical_fwer"]["p_value"] == 0.02
