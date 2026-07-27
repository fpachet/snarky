from __future__ import annotations

import numpy as np
import run_vertical_order_induction as order

satb = order.satb


def _opportunities() -> satb.VoiceOpportunities:
    return satb.VoiceOpportunities(
        piece_ids=np.asarray(["piece", "piece"]),
        offsets_previous=np.asarray([0.0, 1.0], dtype=np.float32),
        offsets_current=np.asarray([1.0, 2.0], dtype=np.float32),
        previous_pitch=np.asarray([64, 64], dtype=np.int16),
        chosen_pitch=np.asarray([65, 65], dtype=np.int16),
        previous_all=np.asarray(
            [[72, 64, 55, 48], [72, 64, 55, 48]],
            dtype=np.int16,
        ),
        current_all=np.asarray(
            [[72, 64, 65, 48], [72, 65, 64, 48]],
            dtype=np.int16,
        ),
        voice_index=1,
        candidate_min=63,
        candidate_max=66,
    )


def test_simultaneous_order_mask_uses_current_adjacent_voices() -> None:
    data = _opportunities()
    mask = order.simultaneous_order_mask(data, -1)

    # Row 0: alto candidates below the simultaneous tenor 65 are violations.
    assert mask[0].tolist() == [True, True, False, False]
    # Row 1: the soprano is far above; no candidate crosses either neighbor.
    assert mask[1].tolist() == [True, False, False, False]


def test_one_column_fit_penalizes_avoided_candidates() -> None:
    data = _opportunities()
    probabilities = np.full((2, 4), 0.25)
    mask = order.simultaneous_order_mask(data, -1)

    weight = order._fit_one_weight((data,), (probabilities,), (mask,))

    assert weight < 0
