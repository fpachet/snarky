from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_satb_ablation as ablation
import run_satb_level_a as satb


def example(voice_index: int = 0) -> satb.VoiceOpportunities:
    candidate_min, candidate_max = satb.VOICE_RANGES[voice_index]
    return satb.VoiceOpportunities(
        piece_ids=np.asarray(["a"]),
        offsets_previous=np.asarray([0.0]),
        offsets_current=np.asarray([1.0]),
        previous_pitch=np.asarray([72]),
        chosen_pitch=np.asarray([74]),
        previous_all=np.asarray([[72, 65, 60, 48]]),
        current_all=np.asarray([[74, 67, 62, 51]]),
        voice_index=voice_index,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )


def test_catalogue_contains_seven_independent_masks() -> None:
    masks = ablation.readable_rule_masks(example())
    assert tuple(masks) == ablation.RULE_IDS
    assert all(mask.shape == (1, 22) for mask in masks.values())


def test_direct_masks_apply_only_to_soprano_choices() -> None:
    soprano = example(0)
    assert ablation.direct_outer_mask(soprano, 0)[0, 75 - 60]
    alto = example(1)
    assert not ablation.direct_outer_mask(alto, 0).any()


def test_nuisance_baseline_reserves_large_leap_rule() -> None:
    opportunities = example()
    matrix = ablation.nuisance_baseline_matrix(opportunities)
    large_leap = np.abs(
        opportunities.candidate_pitches[None, :]
        - opportunities.previous_pitch[:, None]
    ) > 12
    assert not any(
        np.array_equal(matrix[:, :, index].astype(bool), large_leap)
        for index in range(matrix.shape[2])
    )


def test_canonical_ablation_gain_exceeds_null_control() -> None:
    results = Path(__file__).resolve().parent / "results"
    authentic = json.loads(
        (results / "v2_4_satb_ablation.json").read_text(encoding="utf-8")
    )
    null = json.loads(
        (results / "v2_4_satb_ablation_null.json").read_text(encoding="utf-8")
    )
    authentic_gain = authentic["model"]["validation_nll_gain"]
    null_gain = null["model"]["validation_nll_gain"]
    assert authentic["experiment"]["test_opened"] is False
    assert null["experiment"]["test_opened"] is False
    assert authentic_gain > 0.05
    assert authentic_gain > 5 * null_gain
    assert all(
        record["validation_nll_penalty"] > 0
        for record in authentic["model"]["fixed_weight_zeroing_ablation"]
    )
