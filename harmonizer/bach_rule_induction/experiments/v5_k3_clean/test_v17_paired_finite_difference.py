from __future__ import annotations

import numpy as np
from run_v17_paired_finite_difference import evaluate_paired_candidate


def test_paired_candidate_detects_consistent_improvement() -> None:
    bach = np.asarray([[0.0, 0.0, 0.0], [0.2, 0.2, 0.2]])
    baseline = np.asarray(
        [
            [[0.4, 0.4, 0.4], [0.5, 0.5, 0.5]],
            [[0.6, 0.6, 0.6], [0.7, 0.7, 0.7]],
        ]
    )
    candidate = baseline - 0.2
    result = evaluate_paired_candidate(
        baseline=baseline,
        candidate=candidate,
        bach=bach,
        scales=np.ones(3),
        metric_keys=(
            "bass_large_leap_rate",
            "strong_nontriadic_rate",
            "strong_pair_dissonances_per_block",
        ),
    )
    assert result["ensemble_relative_remaining"] < 1
    assert result["improves_every_seed"]
    assert result["passes_guarded_metrics"]


def test_guard_rejects_harmonic_regression() -> None:
    bach = np.zeros((2, 3))
    baseline = np.full((2, 2, 3), 0.2)
    candidate = baseline.copy()
    candidate[:, :, 2] += 0.1
    result = evaluate_paired_candidate(
        baseline=baseline,
        candidate=candidate,
        bach=bach,
        scales=np.ones(3),
        metric_keys=(
            "bass_semitone_rate",
            "triadic_block_rate",
            "strong_pair_dissonances_per_block",
        ),
    )
    assert not result["passes_guarded_metrics"]
