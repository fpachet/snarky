from __future__ import annotations

import json
from pathlib import Path

import run_deepbach_conditional_probe as probe

ROOT = Path(__file__).resolve().parent


def test_summary_separates_exact_and_nonexact_contexts() -> None:
    records = [
        {
            "exact_candidate_context": True,
            "bach_resolved": True,
            "deepbach_resolution_probability": 0.8,
            "deepbach_resolution_rank": 1,
            "deepbach_top_choice_is_resolution": True,
        },
        {
            "exact_candidate_context": False,
            "bach_resolved": False,
            "deepbach_resolution_probability": 0.2,
            "deepbach_resolution_rank": 3,
            "deepbach_top_choice_is_resolution": False,
        },
    ]
    summary = probe.summarize(records)
    assert summary["all"]["opportunities"] == 2
    assert summary["exact"]["mean_deepbach_resolution_probability"] == 0.8
    assert summary["nonexact"]["deepbach_top_choice_is_resolution"] == 0


def test_canonical_probe_finds_strong_preference_and_bach_exceptions() -> None:
    result = json.loads(
        (ROOT / "results/v3_9_deepbach_conditional_probe.json").read_text(
            encoding="utf-8"
        )
    )
    summary = result["summary"]["all"]
    assert summary["opportunities"] == 12
    assert summary["deepbach_top_choice_is_resolution"] == 12
    assert summary["mean_deepbach_resolution_probability"] > 0.9
    exceptions = [
        record for record in result["records"] if not record["bach_resolved"]
    ]
    assert len(exceptions) == 2
    assert all(
        record["deepbach_top_choice_is_resolution"] for record in exceptions
    )
