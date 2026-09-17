from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_selected_tonal_harmonic_audit as audit

ROOT = Path(__file__).resolve().parent


def test_relative_signature_discards_register_and_doubling() -> None:
    pitches = np.asarray([71, 65, 62, 50])
    assert audit.relative_pitch_class_signature(pitches, tonic=0) == (2, 5, 11)


def test_summary_separates_exact_progression_from_other_contexts() -> None:
    rows = [
        {
            "piece_id": "a",
            "resolved": True,
            "source_signature": [2, 5, 11],
            "target_signature": [0, 4, 7],
            "source_matches_hypothesis": True,
            "target_matches_hypothesis": True,
            "progression_matches_hypothesis": True,
        },
        {
            "piece_id": "b",
            "resolved": False,
            "source_signature": [2, 5, 11],
            "target_signature": [0, 4, 9],
            "source_matches_hypothesis": True,
            "target_matches_hypothesis": False,
            "progression_matches_hypothesis": False,
        },
    ]
    summary = audit.summarize_rows(rows)
    assert summary["exact_progression_matches"] == 1
    assert summary["exact_progression_resolution_rate"] == 1.0
    assert summary["nonexact_progression_resolution_rate"] == 0.0
    assert summary["distinct_progression_signatures"] == 2


def test_fisher_exact_detects_exception_free_exact_subset() -> None:
    p_value = audit.fisher_exact_greater(
        exact_resolutions=41,
        exact_exceptions=0,
        nonexact_resolutions=6,
        nonexact_exceptions=7,
    )
    assert p_value < 0.001


def test_proxy_classification_requires_replication_across_splits() -> None:
    train = {"exact_progression_match_rate": 0.95}
    validation = {"exact_progression_match_rate": 0.91}
    assert (
        audit.proxy_classification(train, validation)
        == "PITCH_CLASS_PROXY_CONFIRMED"
    )
    validation["exact_progression_match_rate"] = 0.49
    assert (
        audit.proxy_classification(train, validation)
        == "PITCH_CLASS_PROXY_NOT_CONFIRMED"
    )


def test_canonical_harmonic_audit_keeps_partial_proxy_and_test_sealed() -> None:
    result = json.loads(
        (
            ROOT / "results/v3_5_selected_tonal_harmonic_audit.json"
        ).read_text(encoding="utf-8")
    )
    record = result["audits"][0]
    assert result["experiment"]["test_opened"] is False
    assert record["classification"] == "PITCH_CLASS_PROXY_PARTIAL"
    assert record["train"]["exact_progression_resolutions"] == 41
    assert record["train"]["exact_progression_exceptions"] == 0
    assert record["validation"]["exact_progression_resolutions"] == 12
    assert record["validation"]["exact_progression_exceptions"] == 0
