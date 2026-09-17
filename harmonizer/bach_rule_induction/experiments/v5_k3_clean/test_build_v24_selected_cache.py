from __future__ import annotations

import json
from pathlib import Path

import run_exact_factor_reinduction as exact
from build_v24_selected_cache import selected_features

HERE = Path(__file__).resolve().parent
FACTOR_BASE = HERE.parents[1] / "factor_bases/k3_v6_induced"


def test_v24_cache_contains_v23_plus_eight_residual_statuses() -> None:
    source = json.loads(
        (FACTOR_BASE / "v6_induced_model.json").read_text(encoding="utf-8")
    )
    baseline = json.loads(
        (FACTOR_BASE / "v23_metric_harmony_full_model.json").read_text(
            encoding="utf-8"
        )
    )
    grammar = exact._load_grammar(
        FACTOR_BASE / "grammar_v24_residual_sonority.yaml"
    )
    features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=HERE / "work/k3-train-validation-context-full.npz",
        group={
            "feature_kind": "central_residual_strong_sonority_status",
            "size": 8,
        },
    )

    assert len(features) == 57 + 8
    assert sum(
        feature.kind == "central_residual_strong_sonority_status"
        for feature in features
    ) == 8
