from __future__ import annotations

import json
from pathlib import Path

import yaml

EXPERIMENT_ROOT = Path(__file__).resolve().parent
RULES_ROOT = EXPERIMENT_ROOT.parents[1] / "rules"


def test_direct_rule_cards_match_canonical_experiment() -> None:
    result = json.loads(
        (EXPERIMENT_ROOT / "results/v2_variant_safe.json").read_text(encoding="utf-8")
    )
    refinement = result["model"]["direct_family_refinement"]
    assert refinement["candidate_classes"] == [0, 7]
    assert result["experiment"]["test_opened"] is False

    for interval_class, suffix, reference in (
        (0, "001", "R-DIRECT-001"),
        (7, "002", "R-DIRECT-002"),
    ):
        path = RULES_ROOT / f"R-LEARNED-DIRECT-{suffix}.yaml"
        card = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert card["lifecycle"] == "SUPPORTED"
        assert card["statistics"]["test"]["opened"] is False
        assert card["semantic_comparison"]["reference_rule_id"] == reference
        assert card["semantic_comparison"]["mismatches"] == 0
        assert (
            card["statistics"]["fitted_weight"]
            == refinement["candidate_weights"][str(interval_class)]
        )


def test_satb_level_a_rule_cards_match_canonical_experiment() -> None:
    result = json.loads(
        (EXPERIMENT_ROOT / "results/v2_2_satb_level_a.json").read_text(
            encoding="utf-8"
        )
    )
    null = json.loads(
        (EXPERIMENT_ROOT / "results/v2_2_satb_level_a_null.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["model"]["selected_melodic_intervals"] == [6]
    assert result["model"]["selected_overlap_thresholds"] == [0]
    assert null["model"]["selected_melodic_intervals"] == []
    assert null["model"]["selected_overlap_thresholds"] == []
    assert result["experiment"]["test_opened"] is False

    for filename, scan_name, value, reference in (
        (
            "R-LEARNED-MELODY-002.yaml",
            "melodic_interval_scan",
            6,
            "R-MELODY-002",
        ),
        (
            "R-LEARNED-OVERLAP-001.yaml",
            "overlap_scan",
            0,
            "R-OVERLAP-001",
        ),
    ):
        card = yaml.safe_load((RULES_ROOT / filename).read_text(encoding="utf-8"))
        scan = next(
            record
            for record in result["model"][scan_name]
            if record["numeric_value"] == value
        )
        assert card["lifecycle"] == "SUPPORTED"
        assert card["statistics"]["test"]["opened"] is False
        assert card["semantic_comparison"]["reference_rule_id"] == reference
        assert card["semantic_comparison"]["mismatches"] == 0
        assert card["statistics"]["train"]["residual_z"] == scan["train"]["z_score"]
        assert (
            card["statistics"]["validation"]["local_log_rate_contrast"]
            == scan["validation"]["local_log_rate_contrast"]
        )


def test_satb_parallel_rule_cards_match_canonical_experiment() -> None:
    result = json.loads(
        (EXPERIMENT_ROOT / "results/v2_3_satb_parallels.json").read_text(
            encoding="utf-8"
        )
    )
    null = json.loads(
        (EXPERIMENT_ROOT / "results/v2_3_satb_parallels_null.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["model"]["selected_parallel_classes"] == [0, 7]
    assert null["model"]["selected_parallel_classes"] == []
    assert result["experiment"]["test_opened"] is False

    for interval_class, suffix, reference in (
        (0, "001", "R-PARALLEL-001"),
        (7, "002", "R-PARALLEL-002"),
    ):
        card = yaml.safe_load(
            (RULES_ROOT / f"R-LEARNED-PARALLEL-{suffix}.yaml").read_text(
                encoding="utf-8"
            )
        )
        scan = next(
            record
            for record in result["model"]["parallel_interval_scan"]
            if record["numeric_value"] == interval_class
        )
        assert card["lifecycle"] == "SUPPORTED"
        assert card["statistics"]["test"]["opened"] is False
        assert card["semantic_comparison"]["reference_rule_id"] == reference
        assert card["semantic_comparison"]["mismatches"] == 0
        assert card["statistics"]["train"]["residual_z"] == scan["train"]["z_score"]


def test_leading_tone_candidate_card_matches_canonical_experiments() -> None:
    result = json.loads(
        (
            EXPERIMENT_ROOT / "results/v3_1_global_tonal_tendency.json"
        ).read_text(encoding="utf-8")
    )
    refinement = json.loads(
        (
            EXPERIMENT_ROOT / "results/v3_3_mode_stratified_leading_tone.json"
        ).read_text(encoding="utf-8")
    )
    null = json.loads(
        (
            EXPERIMENT_ROOT
            / "results/v3_3_mode_stratified_leading_tone_null.json"
        ).read_text(encoding="utf-8")
    )
    card = yaml.safe_load(
        (RULES_ROOT / "R-LEARNED-LEADING-001.yaml").read_text(encoding="utf-8")
    )
    source_class = next(
        record
        for record in result["model"]["source_class_scan"]
        if record["numeric_value"] == 11
    )
    assert result["model"]["selected_source_classes"] == [11]
    assert len(refinement["model"]["selected_refinements"]) == 7
    assert null["model"]["selected_refinements"] == []
    assert card["lifecycle"] == "CANDIDATE"
    assert card["statistics"]["test"]["opened"] is False
    assert (
        card["statistics"]["validation"]["residual_z"]
        == source_class["validation"]["z_score"]
    )
    assert card["refinements"]["candidate_count"] == 7
