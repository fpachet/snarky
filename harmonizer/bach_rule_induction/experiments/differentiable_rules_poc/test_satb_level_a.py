from __future__ import annotations

import numpy as np
import run_satb_level_a as satb


def example_opportunities(voice_index: int) -> satb.VoiceOpportunities:
    candidate_min, candidate_max = satb.VOICE_RANGES[voice_index]
    return satb.VoiceOpportunities(
        piece_ids=np.asarray(["a", "b"]),
        offsets_previous=np.asarray([0.0, 1.0]),
        offsets_current=np.asarray([1.0, 2.0]),
        previous_pitch=np.asarray([60, 62]),
        chosen_pitch=np.asarray([66, 64]),
        previous_all=np.asarray([[72, 67, 60, 48], [74, 69, 62, 50]]),
        current_all=np.asarray([[74, 66, 59, 47], [76, 68, 64, 49]]),
        voice_index=voice_index,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )


def test_melodic_interval_mask_finds_numeric_class_six() -> None:
    opportunities = example_opportunities(0)
    mask = satb.melodic_interval_mask(opportunities, 6)
    assert mask[0, 66 - opportunities.candidate_min]
    assert mask[0, 78 - opportunities.candidate_min]
    assert mask[1, 68 - opportunities.candidate_min]
    assert not mask[1, 64 - opportunities.candidate_min]


def test_overlap_masks_are_directionally_symmetric() -> None:
    upper = example_opportunities(0)
    upper_mask = satb.overlap_depth_mask(upper, 0)
    assert upper_mask is not None
    assert upper_mask[0, 66 - upper.candidate_min]
    assert not upper_mask[0, 68 - upper.candidate_min]

    lower = example_opportunities(1)
    lower_mask = satb.reverse_overlap_depth_mask(lower, 0)
    assert lower_mask is not None
    assert lower_mask[0, 73 - lower.candidate_min]
    assert not lower_mask[0, 71 - lower.candidate_min]
    combined = satb.any_overlap_depth_mask(lower, 0)
    upper_from_alto = satb.overlap_depth_mask(lower, 0)
    assert upper_from_alto is not None
    assert np.array_equal(combined, lower_mask | upper_from_alto)


def test_selection_uses_gradient_validation_and_bootstrap() -> None:
    record = {
        "numeric_value": 6,
        "train": {"z_score": -4.0},
        "validation": {"z_score": -2.5},
        "bootstrap_validation": {"negative_fraction": 0.97},
    }
    assert satb.select_avoidances([record], -3.0, -2.0, 0.95) == [6]
    record["bootstrap_validation"]["negative_fraction"] = 0.94
    assert satb.select_avoidances([record], -3.0, -2.0, 0.95) == []


def test_intelligibility_budget_keeps_strongest_rule() -> None:
    records = [
        {
            "numeric_value": value,
            "train": {"z_score": train_z},
            "validation": {"z_score": validation_z},
            "bootstrap_validation": {"negative_fraction": 0.99},
        }
        for value, train_z, validation_z in ((3, -4.0, -2.1), (6, -5.0, -3.0))
    ]
    assert satb.select_top_avoidances(records, -3.0, -2.0, 0.95, 1) == [6]


def test_local_notch_prefers_isolated_dip() -> None:
    records = []
    for value, observed in enumerate((0.5, 0.4, 0.1, 0.4, 0.3)):
        records.append(
            {
                "numeric_value": value,
                "train": {
                    "z_score": -4.0,
                    "observed_rate": observed,
                    "expected_rate": 0.5,
                },
                "validation": {
                    "z_score": -3.0,
                    "observed_rate": observed,
                    "expected_rate": 0.5,
                },
                "bootstrap_validation": {"negative_fraction": 0.99},
            }
        )
    satb.add_local_log_rate_contrasts(records)
    assert satb.select_local_notches(records, -3.0, -2.0, 0.95, -0.5, 1) == [2]


def test_recovered_formulas_match_level_a_references() -> None:
    assert satb.compare_melodic_class_to_reference(6)["mismatches"] == 0
    assert satb.compare_overlap_threshold_to_reference(0)["mismatches"] == 0
