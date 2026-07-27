from __future__ import annotations

import numpy as np
import run_satb_level_a as satb
import run_satb_parallels as parallels


def example_soprano_opportunities() -> satb.VoiceOpportunities:
    return satb.VoiceOpportunities(
        piece_ids=np.asarray(["a"]),
        offsets_previous=np.asarray([0.0]),
        offsets_current=np.asarray([1.0]),
        previous_pitch=np.asarray([72]),
        chosen_pitch=np.asarray([74]),
        previous_all=np.asarray([[72, 65, 60, 48]]),
        current_all=np.asarray([[74, 67, 62, 50]]),
        voice_index=0,
        candidate_min=60,
        candidate_max=81,
    )


def test_parallel_mask_discovers_classes_zero_and_seven() -> None:
    opportunities = example_soprano_opportunities()
    fifth = parallels.parallel_interval_class_mask(opportunities, 7)
    octave = parallels.parallel_interval_class_mask(opportunities, 0)
    assert fifth[0, 74 - opportunities.candidate_min]
    assert octave[0, 74 - opportunities.candidate_min]
    assert not fifth[0, 73 - opportunities.candidate_min]


def test_parallel_mask_requires_same_nonzero_direction() -> None:
    opportunities = example_soprano_opportunities()
    mask = parallels.parallel_interval_class_mask(opportunities, 7)
    assert not mask[0, 70 - opportunities.candidate_min]
    stationary_other = opportunities.take(np.asarray([0]))
    stationary_other.current_all = stationary_other.current_all.copy()
    stationary_other.current_all[0, 1] = stationary_other.previous_all[0, 1]
    mask = parallels.parallel_interval_class_mask(stationary_other, 7)
    assert not mask[0, 72 - opportunities.candidate_min]


def test_reference_comparison_for_known_parallel_classes() -> None:
    for interval_class in (0, 7):
        comparison = parallels.compare_parallel_class_to_reference(interval_class)
        assert comparison["mismatches"] == 0
        assert comparison["classification"] == "RECOVERED_EQUIVALENT"
