#!/usr/bin/env python3
"""Export the retained V22 RuleGroup as a standard model and Snarky factors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import yaml
from export_v5_16_factor_program import render_factor_program

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = (
    REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
)
RULES_DIRECTORY = (
    REPOSITORY
    / "harmonizer/bach_rule_induction/rules/v22_shared_root_motion"
)
DEFAULT_GROUPED = FACTOR_BASE / "v22c_shared_root_motion_full_model.json"
DEFAULT_CORPUS_TEMPLATE = FACTOR_BASE / "v19_unanimous_full_model.json"
DEFAULT_MODEL = FACTOR_BASE / "v22_shared_root_motion_full_model.json"
DEFAULT_BASELINE_MODEL = FACTOR_BASE / "v22_baseline_refit_full_model.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v22_shared_root_motion_full_factors.yaml"
DEFAULT_PROGRAM = FACTOR_BASE / "v22_shared_root_motion_full.factors"
DEFAULT_GROUP_CARD = RULES_DIRECTORY / "RG-LEARNED-V22-001.yaml"
DEFAULT_MANIFEST = RULES_DIRECTORY / "manifest.yaml"


def _factor(
    index: int,
    feature: dict[str, Any],
    weight: float,
    *,
    family: str,
    member_role: str,
) -> dict[str, Any]:
    return {
        "id": f"F-K3-V22-{index:03d}",
        "family": family,
        "feature": feature,
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
        "rule_group": "RG-LEARNED-V22-001",
        "member_role": member_role,
    }


def build_artifacts(
    grouped: dict[str, Any],
    corpus_template: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not grouped["selection"]["group_retained"]:
        raise ValueError("Cannot export a rejected V22 group")
    baseline = grouped["selected_model"]["baseline_rules"]
    group_rows = grouped["selected_group"]["weights"]
    if len(group_rows) != 24:
        raise ValueError("V22 requires 24 shared root-motion cells")
    group_features = [
        k3.FeatureSpec(
            "central_named_root_motion_mode",
            -1,
            value=int(row["root_motion_class"]),
            second_value=0 if row["mode"] == "major" else 1,
            complexity=3,
        )
        for row in group_rows
    ]
    group_weights = np.asarray(
        [float(row["weight"]) for row in group_rows],
        dtype=np.float64,
    )
    if not np.allclose(group_weights.reshape(2, 12).sum(axis=1), 0.0):
        raise ValueError("V22 group lost its per-mode centering")

    model_rules = []
    factors = []
    for index, rule in enumerate(baseline, start=1):
        feature = dict(rule["feature"])
        weight = float(rule["weight"])
        model_rules.append(
            {
                "id": f"F-K3-V22-{index:03d}",
                "family": "v20b_identifiable_harmonic_status_baseline",
                "clause": feature["label"],
                "feature": feature,
                "weight": weight,
                "origin": "learned_from_bach_corpus",
                "human_authored": False,
                "calls_other_rules": False,
            }
        )
        factors.append(
            _factor(
                index,
                feature,
                weight,
                family="v20b_identifiable_harmonic_status_baseline",
                member_role="baseline",
            )
        )
    offset = len(model_rules)
    for local_index, (feature, weight) in enumerate(
        zip(group_features, group_weights, strict=True),
        start=1,
    ):
        index = offset + local_index
        feature_record = feature.to_dict()
        model_rules.append(
            {
                "id": f"F-K3-V22-{index:03d}",
                "family": "named_root_motion_mode",
                "clause": feature.label,
                "feature": feature_record,
                "weight": float(weight),
                "origin": "learned_from_bach_corpus",
                "human_authored": False,
                "calls_other_rules": False,
                "rule_group": "RG-LEARNED-V22-001",
            }
        )
        factors.append(
            _factor(
                index,
                feature_record,
                float(weight),
                family="named_root_motion_mode",
                member_role="shared_root_motion_cell",
            )
        )

    model = {
        "experiment": {
            "id": "K3-V22-SHARED-ROOT-MOTION-FULL-1",
            "status": "SUPPORTED_PRETEST",
            "source_grouped_fit": grouped["experiment"]["id"],
            "learned_factor_count": len(model_rules),
            "rule_group_count": 1,
            "hard_constraint_count": 0,
            "test_loaded": False,
        },
        "corpus": corpus_template["corpus"],
        "model": {
            "register_logits": grouped["selected_model"]["register_logits"],
            "tonal_logits": grouped["selected_model"]["tonal_logits"],
            "rules": model_rules,
        },
    }
    catalogue = {
        "schema_version": 1,
        "id": "K3-V22-SHARED-ROOT-MOTION",
        "model_id": model["experiment"]["id"],
        "source_model": str(DEFAULT_MODEL.resolve()),
        "factor_group": "k3_v22_shared_root_motion",
        "status": "FROZEN_EXPLANATORY_PRETEST",
        "counts": {
            "canonical_factors_after_merge": len(factors),
            "baseline_factors": len(baseline),
            "shared_group_cells": len(group_features),
            "rule_groups": 1,
        },
        "factors": factors,
    }
    group_card = {
        "schema_version": 1,
        "id": "RG-LEARNED-V22-001",
        "title": "Mouvement dirigé de la fondamentale selon le mode",
        "lifecycle": "SUPPORTED_PRETEST",
        "status": "RULE_GROUP",
        "statement": (
            "Quand deux blocs successifs ont chacun une analyse d'accord "
            "unique, pondérer leur mouvement de fondamentale par une table "
            "partagée de 12 classes dans chaque mode."
        ),
        "scope": {
            "voices": "SATB",
            "window": ["previous", "current"],
            "attack_hold_semantics": True,
            "requires_unique_named_chord_analysis": True,
        },
        "parameterization": {
            "dimensions": ["declared_mode", "directed_root_motion_class"],
            "shape": [2, 12],
            "parameter_count": 24,
            "identifiability": "sum_to_zero_over_motion_classes_per_mode",
            "joint_learning": "exact_conditional_pseudolikelihood",
            "group_penalty": 0.3,
        },
        "statistics": {
            "four_fold_mean_nll_improvement": 0.013859286566084737,
            "four_fold_positive_pieces": "27/32",
            "full_validation_mean_nll_improvement": 0.021475014647672954,
            "full_validation_positive_pieces": "46/50",
            "full_validation_bootstrap_95_interval": [
                0.017585369317497834,
                0.02532944660374424,
            ],
        },
        "conclusion": {
            "kind": "joint_factor_group",
            "absolute_prohibition": False,
            "weights": group_rows,
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
    parser.add_argument("--grouped", type=Path, default=DEFAULT_GROUPED)
    parser.add_argument(
        "--corpus-template",
        type=Path,
        default=DEFAULT_CORPUS_TEMPLATE,
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--baseline-model",
        type=Path,
        default=DEFAULT_BASELINE_MODEL,
    )
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--program", type=Path, default=DEFAULT_PROGRAM)
    parser.add_argument("--group-card", type=Path, default=DEFAULT_GROUP_CARD)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grouped = json.loads(args.grouped.read_text(encoding="utf-8"))
    corpus_template = json.loads(
        args.corpus_template.read_text(encoding="utf-8")
    )
    model, catalogue, group_card = build_artifacts(grouped, corpus_template)
    catalogue["source_model"] = str(args.model.resolve())
    baseline_count = len(grouped["selected_model"]["baseline_rules"])
    baseline_model = {
        "experiment": {
            "id": "K3-V22-BASELINE-REFIT-FULL-1",
            "status": "CONTROL_PRETEST",
            "source_grouped_fit": grouped["experiment"]["id"],
            "learned_factor_count": baseline_count,
            "rule_group_count": 0,
            "hard_constraint_count": 0,
            "test_loaded": False,
        },
        "corpus": model["corpus"],
        "model": {
            "register_logits": model["model"]["register_logits"],
            "tonal_logits": model["model"]["tonal_logits"],
            "rules": model["model"]["rules"][:baseline_count],
        },
    }
    args.model.write_text(
        json.dumps(model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.baseline_model.write_text(
        json.dumps(baseline_model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    program = render_factor_program(
        catalogue,
        group_name="k3_v22_shared_root_motion",
        source_label=args.catalogue.name,
    )
    (parsed_group,) = parse_factor_groups(program)
    if len(parsed_group.factors) != len(catalogue["factors"]):
        raise ValueError("V22 Snarky program lost factors during parsing")
    args.program.write_text(program, encoding="utf-8")
    args.group_card.parent.mkdir(parents=True, exist_ok=True)
    args.group_card.write_text(
        yaml.safe_dump(group_card, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "id": "S-LEARNED-V22-SHARED-ROOT-MOTION",
        "status": "SUPPORTED_PRETEST",
        "model": str(args.model.resolve()),
        "factor_catalogue": str(args.catalogue.resolve()),
        "factor_program": str(args.program.resolve()),
        "rule_groups": [args.group_card.name],
        "hard_constraints": [],
        "test_opened": False,
    }
    args.manifest.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(
        f"[v22-export] wrote {len(catalogue['factors'])} factors "
        "in one learned RuleGroup",
        flush=True,
    )
    print(f"[v22-export] wrote {args.model}", flush=True)
    print(f"[v22-export] wrote {args.baseline_model}", flush=True)
    print(f"[v22-export] wrote {args.program}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
