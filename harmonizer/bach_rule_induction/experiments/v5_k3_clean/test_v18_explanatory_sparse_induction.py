from __future__ import annotations

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_v18_explanatory_sparse_induction as v18


def test_one_standard_error_selects_shortest_admissible_model() -> None:
    frontier = [
        {
            "validation_piece_mean_nll": 1.00,
            "validation_piece_standard_error": 0.01,
        },
        {
            "validation_piece_mean_nll": 0.92,
            "validation_piece_standard_error": 0.02,
        },
        {
            "validation_piece_mean_nll": 0.90,
            "validation_piece_standard_error": 0.03,
        },
        {
            "validation_piece_mean_nll": 0.895,
            "validation_piece_standard_error": 0.04,
        },
    ]

    index, threshold = v18._one_standard_error_index(frontier)

    assert np.isclose(threshold, 0.935)
    assert index == 1


def test_complexity_weighted_l1_shrinks_complex_rule_more() -> None:
    train = {
        "chosen": np.asarray([0], dtype=np.int16),
        "voices": np.asarray([0], dtype=np.int8),
        "modes": np.asarray([0], dtype=np.int8),
        "tonics": np.asarray([0], dtype=np.int8),
        "factors": np.zeros((1, 2, 2), dtype=np.uint8),
    }
    validation = {key: value.copy() for key, value in train.items()}
    initial = exact.Parameters(
        register=np.zeros((4, 2), dtype=np.float64),
        tonal=np.zeros((4, 2, 12), dtype=np.float64),
        factor_weights=np.asarray([1.0, 1.0], dtype=np.float64),
    )
    config = {
        "estimation": {
            "maximum_steps_per_refit": 1,
            "learning_rate": 0.1,
            "l1": 0.1,
            "l2": 0.0,
        }
    }

    fitted, _ = v18._fit_selected(
        train,
        validation,
        np.asarray([60, 61], dtype=np.int16),
        initial,
        np.asarray([1.0, 3.0]),
        config,
    )

    assert np.allclose(fitted.factor_weights, [0.99, 0.97])


def test_human_clause_exposes_parallel_fifth_predicate() -> None:
    feature = k3.FeatureSpec(
        "pair_abs_class_preserved_same_sign",
        0,
        other_voice=3,
        value=7,
        complexity=4,
    )

    clause = v18._human_clause(feature)

    assert "soprano avec basse" in clause
    assert "classe 7" in clause
    assert "mouvement direct" in clause
