#!/usr/bin/env python3
"""Export retained V23 harmony statuses as a standard model and FACTOR base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import run_exact_factor_reinduction as exact
import yaml
from build_v23_selected_cache import selected_features
from export_v5_16_factor_program import render_factor_program

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
RULES_DIRECTORY = REPOSITORY / "harmonizer/bach_rule_induction/rules/v23_metric_harmony"
DEFAULT_FIT = FACTOR_BASE / "v23d_retained_harmony_full_fit.json"
DEFAULT_STABILITY = FACTOR_BASE / "v23_metric_bass_harmony_stability.json"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_BASELINE = FACTOR_BASE / "v22_shared_root_motion_model.json"
DEFAULT_GRAMMAR = FACTOR_BASE / "grammar_v23_metric_bass_harmony.yaml"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CORPUS_TEMPLATE = FACTOR_BASE / "v22_shared_root_motion_full_model.json"
DEFAULT_MODEL = FACTOR_BASE / "v23_metric_harmony_full_model.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v23_metric_harmony_full_factors.yaml"
DEFAULT_PROGRAM = FACTOR_BASE / "v23_metric_harmony_full.factors"
DEFAULT_GROUP_CARD = RULES_DIRECTORY / "RG-LEARNED-V23-001.yaml"
DEFAULT_MANIFEST = RULES_DIRECTORY / "manifest.yaml"


def _factor(
    index: int,
    feature: k3.FeatureSpec,
    weight: float,
    *,
    retained_group: bool,
) -> dict[str, Any]:
    record = {
        "id": f"F-K3-V23-{index:03d}",
        "family": (
            "unique_chord_family_inversion_strong"
            if retained_group
            else "v22_baseline"
        ),
        "feature": feature.to_dict(),
        "parameter": {
            "scale": "log_energy_contribution",
            "log_weight": float(weight),
            "sign": (
                "preference"
                if weight > 0
                else "avoidance"
                if weight < 0
                else "neutral"
            ),
        },
        "origin": "learned_from_bach_corpus",
        "human_authored": False,
        "preference_human_authored": False,
        "feature_definition_human_authored": True,
        "grounding": "k3_feature_evaluator",
        "member_role": (
            "strong_named_harmony_status"
            if retained_group
            else "retained_v22_baseline"
        ),
    }
    if retained_group:
        record["rule_group"] = "RG-LEARNED-V23-001"
    return record


def build_artifacts(
    fit: dict[str, Any],
    stability: dict[str, Any],
    corpus_template: dict[str, Any],
    features: tuple[k3.FeatureSpec, ...],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if stability["decision"]["retained_variant"] != "harmony_only":
        raise ValueError("V23 exporter requires the retained harmony-only decision")
    variant = fit["variants"]["harmony_only"]
    parameters = variant["model_parameters"]
    if list(parameters["feature_keys"]) != [
        feature.key for feature in features
    ]:
        raise ValueError("V23 retained fit and reconstructed features disagree")
    weights = list(map(float, parameters["factor_weights"]))
    if len(features) != len(weights):
        raise ValueError("V23 feature and parameter counts disagree")
    harmony_start = next(
        (
            index
            for index, feature in enumerate(features)
            if feature.kind
            == "central_unique_chord_family_inversion_strong"
        ),
        len(features),
    )
    if len(features) - harmony_start != 14:
        raise ValueError("V23 retained harmony group must contain 14 cells")
    rules = []
    factors = []
    for index, (feature, weight) in enumerate(
        zip(features, weights, strict=True),
        start=1,
    ):
        retained_group = index > harmony_start
        rule = {
            "id": f"F-K3-V23-{index:03d}",
            "family": (
                "unique_chord_family_inversion_strong"
                if retained_group
                else "v22_baseline"
            ),
            "clause": feature.label,
            "feature": feature.to_dict(),
            "weight": weight,
            "origin": "learned_from_bach_corpus",
            "human_authored": False,
            "calls_other_rules": False,
        }
        if retained_group:
            rule["rule_group"] = "RG-LEARNED-V23-001"
        rules.append(rule)
        factors.append(
            _factor(
                index,
                feature,
                weight,
                retained_group=retained_group,
            )
        )
    model = {
        "experiment": {
            "id": "K3-V23-METRIC-HARMONY-FULL-1",
            "status": "SUPPORTED_PRETEST",
            "source_fit": fit["experiment"]["id"],
            "learned_factor_count": len(rules),
            "retained_v22_factor_count": harmony_start,
            "new_harmony_factor_count": 14,
            "rule_group_count": 2,
            "hard_constraint_count": 0,
            "test_loaded": False,
        },
        "corpus": corpus_template["corpus"],
        "model": {
            "register_logits": parameters["register_logits"],
            "tonal_logits": parameters["tonal_logits"],
            "rules": rules,
        },
    }
    catalogue = {
        "schema_version": 1,
        "id": "K3-V23-METRIC-HARMONY",
        "model_id": model["experiment"]["id"],
        "source_model": str(DEFAULT_MODEL.resolve()),
        "factor_group": "k3_v23_metric_harmony",
        "status": "FROZEN_EXPLANATORY_PRETEST",
        "counts": {
            "canonical_factors_after_merge": len(factors),
            "retained_v22_factors": harmony_start,
            "new_harmony_cells": 14,
            "rule_groups": 2,
        },
        "factors": factors,
    }
    full = stability["variants"]["harmony_only"]["full_validation"]
    folds = stability["variants"]["harmony_only"]["aggregate_folds"]
    group_card = {
        "schema_version": 1,
        "id": "RG-LEARNED-V23-001",
        "title": "Famille d'accord nommée et renversement sur temps fort",
        "lifecycle": "SUPPORTED_PRETEST",
        "status": "RULE_GROUP",
        "statement": (
            "Quand le bloc vertical fort possède une analyse d'accord nommée "
            "unique, pondérer conjointement sa famille et son renversement ; "
            "l'absence d'analyse unique constitue l'état de référence."
        ),
        "scope": {
            "voices": "SATB",
            "window": ["current"],
            "metric": "strong",
            "attack_hold_semantics": True,
            "requires_unique_named_chord_analysis": True,
        },
        "parameterization": {
            "dimensions": ["chord_family", "inversion"],
            "parameter_count": 14,
            "reference_state": "no_strict_unique_named_chord",
            "joint_learning": "exact_conditional_pseudolikelihood",
            "group_penalty": 0.6,
        },
        "statistics": {
            "four_fold_mean_nll_improvement": folds["mean"],
            "four_fold_positive_pieces": (
                f"{folds['positive_count']}/{folds['piece_count']}"
            ),
            "four_fold_bootstrap_95_interval": folds[
                "bootstrap_95_interval"
            ],
            "full_validation_mean_nll_improvement": full[
                "mean_improvement"
            ],
            "full_validation_positive_pieces": (
                f"{full['positive_piece_count']}/{full['piece_count']}"
            ),
            "full_validation_bootstrap_95_interval": full[
                "bootstrap_95_interval"
            ],
        },
        "conclusion": {
            "kind": "joint_factor_group",
            "absolute_prohibition": False,
            "weights": stability["retained_harmony_weights"],
        },
        "provenance": {
            "origin": "learned_from_bach_corpus",
            "human_authored_rule": False,
            "human_authored_parameter_sharing": True,
            "historical_rules_loaded": False,
            "test_opened": False,
        },
    }
    return model, catalogue, group_card


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fit", type=Path, default=DEFAULT_FIT)
    parser.add_argument("--stability", type=Path, default=DEFAULT_STABILITY)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument(
        "--corpus-template",
        type=Path,
        default=DEFAULT_CORPUS_TEMPLATE,
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--program", type=Path, default=DEFAULT_PROGRAM)
    parser.add_argument("--group-card", type=Path, default=DEFAULT_GROUP_CARD)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    stability = json.loads(args.stability.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    grammar = exact._load_grammar(args.grammar)
    all_features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=args.context,
        groups=[
            {
                "id": "bass_tonal_strong_mode",
                "feature_kind": "central_bass_tonal_strong_mode",
                "size": 24,
            },
            {
                "id": "unique_chord_family_inversion_strong",
                "feature_kind": (
                    "central_unique_chord_family_inversion_strong"
                ),
                "size": 14,
            },
        ],
    )
    by_key = {feature.key: feature for feature in all_features}
    fit_keys = fit["variants"]["harmony_only"]["model_parameters"][
        "feature_keys"
    ]
    features = tuple(by_key[key] for key in fit_keys)
    corpus_template = json.loads(
        args.corpus_template.read_text(encoding="utf-8")
    )
    model, catalogue, group_card = build_artifacts(
        fit,
        stability,
        corpus_template,
        features,
    )
    catalogue["source_model"] = str(args.model.resolve())
    args.model.write_text(
        json.dumps(model, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    program = render_factor_program(
        catalogue,
        group_name="k3_v23_metric_harmony",
        source_label=args.catalogue.name,
    )
    (parsed_group,) = parse_factor_groups(program)
    if len(parsed_group.factors) != len(catalogue["factors"]):
        raise ValueError("V23 Snarky program lost factors during parsing")
    args.program.write_text(program, encoding="utf-8")
    args.group_card.parent.mkdir(parents=True, exist_ok=True)
    args.group_card.write_text(
        yaml.safe_dump(group_card, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "id": "S-LEARNED-V23-METRIC-HARMONY",
        "status": "SUPPORTED_PRETEST",
        "model": str(args.model.resolve()),
        "factor_catalogue": str(args.catalogue.resolve()),
        "factor_program": str(args.program.resolve()),
        "rule_groups": [
            "../v22_shared_root_motion/RG-LEARNED-V22-001.yaml",
            args.group_card.name,
        ],
        "hard_constraints": [],
        "test_opened": False,
    }
    args.manifest.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[v23-export] wrote {args.model}", flush=True)
    print(f"[v23-export] wrote {args.catalogue}", flush=True)
    print(f"[v23-export] wrote {args.program}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
