from __future__ import annotations

import json
from pathlib import Path

import run_exact_factor_reinduction as exact
from build_v23_selected_cache import selected_features
from export_v23_metric_harmony import build_artifacts

HERE = Path(__file__).resolve().parent
FACTOR_BASE = HERE.parents[1] / "factor_bases/k3_v6_induced"


def test_export_retains_v22_and_adds_exactly_fourteen_harmony_cells() -> None:
    fit = json.loads(
        (FACTOR_BASE / "v23d_retained_harmony_full_fit.json").read_text(
            encoding="utf-8"
        )
    )
    stability = json.loads(
        (FACTOR_BASE / "v23_metric_bass_harmony_stability.json").read_text(
            encoding="utf-8"
        )
    )
    corpus = json.loads(
        (FACTOR_BASE / "v22_shared_root_motion_full_model.json").read_text(
            encoding="utf-8"
        )
    )
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
    all_features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=HERE / "work/k3-train-validation-context-full.npz",
        groups=[
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
        ],
    )
    by_key = {feature.key: feature for feature in all_features}
    features = tuple(
        by_key[key]
        for key in fit["variants"]["harmony_only"]["model_parameters"][
            "feature_keys"
        ]
    )

    model, catalogue, card = build_artifacts(
        fit,
        stability,
        corpus,
        features,
    )

    assert len(model["model"]["rules"]) == 57
    assert catalogue["counts"]["new_harmony_cells"] == 14
    assert card["parameterization"]["reference_state"] == (
        "no_strict_unique_named_chord"
    )
