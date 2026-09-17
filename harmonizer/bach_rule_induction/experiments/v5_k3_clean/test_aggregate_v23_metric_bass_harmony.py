from __future__ import annotations

import numpy as np
from aggregate_v23_metric_bass_harmony import _bootstrap


def test_bootstrap_summarizes_paired_improvements() -> None:
    summary = _bootstrap(
        np.asarray([0.1, 0.2, -0.05, 0.3]),
        seed=1,
        resamples=1_000,
    )

    assert summary["mean"] == np.mean([0.1, 0.2, -0.05, 0.3])
    assert summary["positive_count"] == 3
    assert summary["negative_count"] == 1
    assert summary["piece_count"] == 4
