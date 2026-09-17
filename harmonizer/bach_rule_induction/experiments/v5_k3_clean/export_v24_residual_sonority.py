#!/usr/bin/env python3
"""Export the V24 contrastive model as a Snarky FACTOR base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from export_v5_16_factor_program import render_factor_program

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
RULES_DIRECTORY = (
    REPOSITORY / "harmonizer/bach_rule_induction/rules/v24_residual_sonority"
)
DEFAULT_MODEL = FACTOR_BASE / "v24_contrastive_moment_model.json"
DEFAULT_FIT = FACTOR_BASE / "v24c_contrastive_moment_fit.json"
DEFAULT_VALIDATION = FACTOR_BASE / "v24c_v23_generation_validation10x5_sweep6.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v24_contrastive_full_factors.yaml"
DEFAULT_PROGRAM = FACTOR_BASE / "v24_contrastive_full.factors"
DEFAULT_GROUP_CARD = RULES_DIRECTORY / "RG-LEARNED-V24-001.yaml"
DEFAULT_MANIFEST = RULES_DIRECTORY / "manifest.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--fit", type=Path, default=DEFAULT_FIT)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--program", type=Path, default=DEFAULT_PROGRAM)
    parser.add_argument("--group-card", type=Path, default=DEFAULT_GROUP_CARD)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def _factor(rule: dict[str, Any]) -> dict[str, Any]:
    weight = float(rule["weight"])
    retained = rule["feature"]["kind"] != "central_residual_strong_sonority_status"
    record = {
        "id": rule["id"],
        "family": rule["family"],
        "feature": rule["feature"],
        "parameter": {
            "scale": "log_energy_contribution",
            "log_weight": weight,
            "sign": (
                "preference"
                if weight > 0
                else "avoidance"
                if weight < 0
                else "neutral"
            ),
        },
        "origin": rule["origin"],
        "human_authored": False,
        "preference_human_authored": False,
        "feature_definition_human_authored": True,
        "grounding": "k3_feature_evaluator",
        "member_role": (
            "retained_v23_baseline"
            if retained
            else "residual_strong_sonority_status"
        ),
    }
    if not retained:
        record["rule_group"] = "RG-LEARNED-V24-001"
    return record


def main() -> int:
    args = parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    validation = json.loads(args.validation.read_text(encoding="utf-8"))
    rules = model["model"]["rules"]
    factors = [_factor(rule) for rule in rules]
    residual = [
        rule
        for rule in rules
        if rule["feature"]["kind"] == "central_residual_strong_sonority_status"
    ]
    if len(residual) != 8:
        raise ValueError("V24 export requires exactly eight residual statuses")
    catalogue = {
        "schema_version": 1,
        "id": "K3-V24-CONTRASTIVE-RESIDUAL-SONORITY",
        "model_id": model["experiment"]["id"],
        "source_model": str(args.model.resolve()),
        "factor_group": "k3_v24_contrastive_residual_sonority",
        "status": "GENERATIVELY_SUPPORTED_PRETEST",
        "counts": {
            "canonical_factors_after_merge": len(factors),
            "retained_v23_factors": len(factors) - len(residual),
            "new_residual_sonority_cells": len(residual),
            "rule_groups": 3,
        },
        "factors": factors,
    }
    program = render_factor_program(
        catalogue,
        group_name="k3_v24_contrastive_residual_sonority",
        source_label=args.catalogue.name,
    )
    (parsed_group,) = parse_factor_groups(program)
    if len(parsed_group.factors) != len(factors):
        raise ValueError("V24 Snarky program lost factors during parsing")
    final_history = fit["history"][-1]
    validation_summary = validation["summary"]
    group_card = {
        "schema_version": 1,
        "id": "RG-LEARNED-V24-001",
        "title": "Statut résiduel des sonorités sur temps fort",
        "lifecycle": "GENERATIVELY_SUPPORTED_PRETEST",
        "status": "RULE_GROUP",
        "statement": (
            "Lorsqu'un bloc fort n'a pas l'analyse nommée unique de V23, "
            "le classer dans un statut exhaustif de complétude ou de note "
            "étrangère localement licenciée, puis pondérer ces huit statuts."
        ),
        "scope": {
            "voices": "SATB",
            "window": ["previous", "current", "next"],
            "metric": "strong",
            "attack_hold_semantics": True,
            "reference_group": "RG-LEARNED-V23-001",
        },
        "parameterization": {
            "dimension": "residual_strong_sonority_status",
            "parameter_count": len(residual),
            "joint_learning": "bach_minus_generated_maxent_moments",
            "learning_iterations": fit["experiment"]["iterations"],
            "validation_used_during_updates": False,
        },
        "statistics": {
            "train_authentic_residual_rate": final_history[
                "authentic_residual_rate"
            ],
            "train_generated_residual_rate": final_history[
                "generated_residual_rate"
            ],
            "train_final_moment_mae": final_history["moment_mae"],
            "validation_v23_strong_nontriadic_rate": validation_summary["V23"][
                "strong_nontriadic_rate"
            ]["mean"],
            "validation_v24_strong_nontriadic_rate": validation_summary["V24C"][
                "strong_nontriadic_rate"
            ]["mean"],
            "validation_v23_strong_dissonances": validation_summary["V23"][
                "strong_pair_dissonances_per_block"
            ]["mean"],
            "validation_v24_strong_dissonances": validation_summary["V24C"][
                "strong_pair_dissonances_per_block"
            ]["mean"],
        },
        "conclusion": {
            "kind": "joint_factor_group",
            "absolute_prohibition": False,
            "conditional_pseudolikelihood_replication": "REJECTED",
            "generative_validation": "IMPROVED_HARMONY_METRICS",
            "weights": [
                {
                    "status": name,
                    "weight": float(rule["weight"]),
                }
                for name, rule in zip(
                    (
                        "exact_named_ambiguous",
                        "incomplete_consonant_triad",
                        "triad_plus_one_ambiguous",
                        "triad_plus_passing_or_neighbor",
                        "triad_plus_suspension",
                        "triad_plus_appoggiatura",
                        "triad_plus_unlicensed",
                        "other_unlicensed",
                    ),
                    residual,
                    strict=True,
                )
            ],
        },
        "provenance": {
            "origin": "learned_from_bach_minus_generated_moments",
            "human_authored_rule": False,
            "human_authored_status_vocabulary": True,
            "historical_rules_loaded": False,
            "test_opened": False,
        },
    }
    manifest = {
        "schema_version": 1,
        "id": "S-LEARNED-V24-RESIDUAL-SONORITY",
        "status": "GENERATIVELY_SUPPORTED_PRETEST",
        "model": str(args.model.resolve()),
        "factor_catalogue": str(args.catalogue.resolve()),
        "factor_program": str(args.program.resolve()),
        "rule_groups": [
            "../v22_shared_root_motion/RG-LEARNED-V22-001.yaml",
            "../v23_metric_harmony/RG-LEARNED-V23-001.yaml",
            args.group_card.name,
        ],
        "hard_constraints": [],
        "test_opened": False,
    }
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    args.program.write_text(program, encoding="utf-8")
    args.group_card.parent.mkdir(parents=True, exist_ok=True)
    args.group_card.write_text(
        yaml.safe_dump(group_card, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    args.manifest.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[v24-export] wrote {args.catalogue}", flush=True)
    print(f"[v24-export] wrote {args.program}", flush=True)
    print(f"[v24-export] wrote {args.group_card}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
