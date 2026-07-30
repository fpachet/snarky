from __future__ import annotations

import json
from pathlib import Path

import run_exact_factor_reinduction as exact
from build_v23_selected_cache import selected_features

HERE = Path(__file__).resolve().parent
FACTOR_BASE = HERE.parents[1] / "factor_bases/k3_v6_induced"


def test_v23_selected_feature_blocks_are_complete_and_disjoint() -> None:
    source = json.loads(
        (FACTOR_BASE / "v6_induced_model.json").read_text(encoding="utf-8")
    )
    baseline = json.loads(
        (FACTOR_BASE / "v22_shared_root_motion_model.json").read_text(
            encoding="utf-8"
        )
    )
    grammar = exact._load_grammar(
        FACTOR_BASE / "grammar_v23_metric_bass_harmony.yaml"
    )
    groups = [
        {
            "id": "bass",
            "feature_kind": "central_bass_tonal_strong_mode",
            "size": 24,
        },
        {
            "id": "harmony",
            "feature_kind": (
                "central_unique_chord_family_inversion_strong"
            ),
            "size": 14,
        },
    ]
    features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=HERE / "work/k3-train-validation-context-full.npz",
        groups=groups,
    )

    assert len(features) == 19 + 24 + 24 + 14
    assert len({feature.key for feature in features}) == len(features)
    assert sum(
        feature.kind == "central_bass_tonal_strong_mode"
        for feature in features
    ) == 24
    assert sum(
        feature.kind == "central_unique_chord_family_inversion_strong"
        for feature in features
    ) == 14
