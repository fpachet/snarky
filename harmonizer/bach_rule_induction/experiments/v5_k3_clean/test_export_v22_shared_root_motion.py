from __future__ import annotations

from export_v22_shared_root_motion import build_artifacts


def test_build_artifacts_preserves_one_centered_group() -> None:
    weights = [float(index - 5.5) for index in range(12)] * 2
    grouped = {
        "experiment": {"id": "source"},
        "selection": {"group_retained": True},
        "selected_model": {
            "register_logits": [[0.0]],
            "tonal_logits": [[0.0]],
            "baseline_rules": [
                {
                    "feature": {
                        "complexity": 1,
                        "key": "abs_class_from_previous:0:-:1:-",
                        "kind": "abs_class_from_previous",
                        "label": "feature",
                        "other_voice": None,
                        "second_value": None,
                        "target_voice": 0,
                        "value": 1,
                    },
                    "weight": 0.5,
                }
            ],
        },
        "selected_group": {
            "weights": [
                {
                    "mode": "major" if index < 12 else "minor",
                    "root_motion_class": index % 12,
                    "weight": weight,
                }
                for index, weight in enumerate(weights)
            ]
        },
    }
    corpus = {"corpus": {"candidate_min": 36, "candidate_max": 81}}

    model, catalogue, card = build_artifacts(grouped, corpus)

    assert len(model["model"]["rules"]) == 25
    assert catalogue["counts"]["shared_group_cells"] == 24
    assert card["parameterization"]["shape"] == [2, 12]
    assert model["experiment"]["hard_constraint_count"] == 0
