from __future__ import annotations

import grouped_maxent
import numpy as np
import run_v21_grouped_transition as v21


def test_double_center_removes_departure_and_arrival_main_effects() -> None:
    weights = np.arange(2 * 3 * 3, dtype=np.float64)

    centered = grouped_maxent.double_center_transition_weights(
        weights,
        shape=(2, 3, 3),
    ).reshape(2, 3, 3)

    assert np.allclose(centered.sum(axis=1), 0.0)
    assert np.allclose(centered.sum(axis=2), 0.0)


def test_center_last_axis_removes_each_mode_mean() -> None:
    weights = np.arange(2 * 4, dtype=np.float64)

    centered = grouped_maxent.center_last_axis_weights(
        weights,
        shape=(2, 4),
    ).reshape(2, 4)

    assert np.allclose(centered.sum(axis=1), 0.0)


def test_sparse_group_prox_removes_a_group_as_one_object() -> None:
    weights = np.asarray([0.3, -0.4, 2.0])
    group = grouped_maxent.GroupPenalty(
        name="small",
        indices=np.asarray([0, 1]),
        strength=1.0,
        scale_by_sqrt_size=False,
    )

    result = grouped_maxent.sparse_group_prox(
        weights,
        learning_rate=0.6,
        l1=np.zeros(3),
        groups=(group,),
    )

    assert np.array_equal(result[:2], np.zeros(2))
    assert result[2] == 2.0


def test_sparse_group_prox_shrinks_norm_without_changing_direction() -> None:
    weights = np.asarray([3.0, 4.0])
    group = grouped_maxent.GroupPenalty(
        name="kept",
        indices=np.asarray([0, 1]),
        strength=1.0,
        scale_by_sqrt_size=False,
    )

    result = grouped_maxent.sparse_group_prox(
        weights,
        learning_rate=1.0,
        l1=np.zeros(2),
        groups=(group,),
    )

    assert np.allclose(result, np.asarray([2.4, 3.2]))
    assert np.isclose(np.linalg.norm(result), 4.0)


def test_one_standard_error_prefers_the_no_group_baseline() -> None:
    candidates = [
        {
            "validation_piece_mean_nll": 0.84,
            "validation_piece_standard_error": 0.02,
        },
        {
            "validation_piece_mean_nll": 0.82,
            "validation_piece_standard_error": 0.03,
        },
    ]

    selected, threshold, best = v21.select_one_standard_error(candidates)

    assert best == 1
    assert np.isclose(threshold, 0.85)
    assert selected == 0


def test_paired_improvement_uses_within_piece_differences() -> None:
    result = v21.paired_improvement(
        {"a": 1.0, "b": 3.0, "c": 2.0},
        {"a": 0.8, "b": 2.9, "c": 2.1},
        seed=7,
        resamples=1_000,
    )

    assert np.isclose(result["mean_improvement"], (0.2 + 0.1 - 0.1) / 3)
    assert result["positive_piece_count"] == 2
    assert result["negative_piece_count"] == 1


def test_paired_protocol_selects_the_strongest_confirmed_group_penalty() -> None:
    candidates = [
        {"validation_piece_mean_nll": 0.84},
        {
            "validation_piece_mean_nll": 0.82,
            "paired_vs_baseline": {
                "bootstrap_95_interval": [0.01, 0.03],
                "positive_piece_count": 8,
                "piece_ids": list("abcdefghij"),
            },
        },
        {
            "validation_piece_mean_nll": 0.81,
            "paired_vs_baseline": {
                "bootstrap_95_interval": [0.02, 0.04],
                "positive_piece_count": 9,
                "piece_ids": list("abcdefghij"),
            },
        },
    ]

    selected, threshold, best = v21.select_from_protocol(
        candidates,
        {
            "criterion": "paired_bootstrap_then_piece_disjoint_stability",
            "minimum_positive_piece_fraction": 0.6,
        },
    )

    assert selected == 1
    assert threshold is None
    assert best == 2
