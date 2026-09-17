from __future__ import annotations

import k3
import numpy as np
from audit_v23_status_coverage import coverage_rows


def test_coverage_requires_both_active_and_inactive_alternatives() -> None:
    factors = np.asarray(
        [
            [[0], [1], [0]],
            [[1], [1], [1]],
            [[0], [0], [1]],
        ],
        dtype=np.uint8,
    )
    chosen = np.asarray([1, 0, 0])
    pieces = np.asarray(["a", "a", "b"])
    feature = k3.FeatureSpec(
        "central_bass_tonal_strong_mode",
        -1,
        value=0,
        second_value=0,
        complexity=2,
    )

    row = coverage_rows(
        factors,
        chosen,
        pieces,
        (feature,),
        minimum_testable=2,
        minimum_piece_support=2,
    )[0]

    assert row["testable_opportunities"] == 2
    assert row["opportunity_piece_support"] == 2
    assert row["authentic_activations"] == 2
    assert row["coverage_eligible"] is True
