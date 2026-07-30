from __future__ import annotations

from aggregate_v22_shared_root_motion import _aggregate


def _model(offset: float, differences: list[float]) -> dict:
    baseline = {
        "label": "baseline",
        "validation_piece_mean_nll": 1.0,
    }
    group = {
        "label": "group",
        "validation_piece_mean_nll": 1.0 - sum(differences) / len(differences),
        "group_weights": [offset + index for index in range(24)],
        "paired_vs_baseline": {
            "differences_baseline_minus_candidate": differences,
            "mean_improvement": sum(differences) / len(differences),
            "positive_piece_count": sum(value > 0 for value in differences),
            "bootstrap_95_interval": [0.01, 0.03],
        },
    }
    return {
        "experiment": {"validation_piece_count": len(differences)},
        "path": [baseline, group],
        "selection": {"selected_index": 1},
    }


def test_aggregate_combines_paired_folds_and_full_fit() -> None:
    folds = [
        _model(0.0, [0.1, 0.2]),
        _model(0.1, [0.2, -0.1]),
        _model(0.2, [0.1, 0.1]),
        _model(0.3, [0.3, 0.1]),
    ]
    full = _model(0.15, [0.2, 0.1, -0.1])

    result = _aggregate(folds, full)

    assert result["heldout_piece_count"] == 8
    assert result["aggregate_heldout_positive_piece_count"] == 7
    assert result["sign_consistent_cell_count"] == 23
    assert result["full_validation_positive_piece_count"] == 2
