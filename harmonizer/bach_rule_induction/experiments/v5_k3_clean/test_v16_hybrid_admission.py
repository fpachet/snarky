from __future__ import annotations

import numpy as np
from aggregate_v16_candidate_admission import evaluate_candidate


def _candidate() -> dict:
    return {
        "rank": 1,
        "family": "test",
        "feature": {"label": "test_feature"},
        "conditional": {
            "column_score": 0.02,
            "approximate_nll_gain": 0.03,
            "gradient": 0.2,
        },
    }


def test_stable_corrective_candidate_is_admitted() -> None:
    residuals = np.asarray([[1.0, 0.0], [1.1, 0.0], [0.9, 0.0]])
    sensitivities = np.asarray([[1.0, 0.0], [1.1, 0.0], [0.9, 0.0]])
    result = evaluate_candidate(
        candidate=_candidate(),
        sensitivities=sensitivities,
        residuals=residuals,
        scales=np.ones_like(residuals),
        max_abs_step=0.15,
        minimum_effect_cosine=0.5,
        maximum_seed_regression=0.02,
        minimum_ensemble_improvement=0.05,
    )
    assert result["proposed_weight_step"] == 0.15
    assert result["stable_effect"]
    assert result["non_regressive_generation_projection"]
    assert result["admitted"]


def test_seed_unstable_candidate_is_rejected() -> None:
    residuals = np.asarray([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]])
    sensitivities = np.asarray([[1.0, 0.0], [-1.0, 0.0], [1.0, 0.0]])
    result = evaluate_candidate(
        candidate=_candidate(),
        sensitivities=sensitivities,
        residuals=residuals,
        scales=np.ones_like(residuals),
        max_abs_step=0.15,
        minimum_effect_cosine=0.5,
        maximum_seed_regression=0.02,
        minimum_ensemble_improvement=0.05,
    )
    assert not result["stable_effect"]
    assert not result["admitted"]
