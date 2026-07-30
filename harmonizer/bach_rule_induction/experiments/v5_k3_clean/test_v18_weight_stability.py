from __future__ import annotations

import numpy as np
from run_v18_weight_stability import _sign, _summarize_weights


def test_sign_uses_a_practical_zero_threshold() -> None:
    assert _sign(-0.051) == -1
    assert _sign(-0.049) == 0
    assert _sign(0.0) == 0
    assert _sign(0.049) == 0
    assert _sign(0.051) == 1


def test_summary_requires_fold_sign_to_match_full_fit() -> None:
    rules = [
        {"id": "a", "clause": "A", "weight": -1.0},
        {"id": "b", "clause": "B", "weight": 1.0},
    ]
    weights = np.asarray(
        [
            [-0.8, 0.7],
            [-0.9, -0.2],
            [-1.1, 0.8],
        ]
    )

    result = _summarize_weights(rules, weights)

    assert result[0]["sign_stable"]
    assert not result[1]["sign_stable"]
