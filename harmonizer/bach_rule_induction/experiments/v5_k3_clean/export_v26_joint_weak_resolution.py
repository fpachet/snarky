#!/usr/bin/env python3
"""Export the selected V26 conditional candidate as model and Snarky factors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import yaml
from export_v5_16_factor_program import render_factor_program

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_BASELINE = FACTOR_BASE / "v24_contrastive_moment_model.json"
DEFAULT_FIT = FACTOR_BASE / "v26_joint_weak_resolution_model.json"
DEFAULT_MODEL = FACTOR_BASE / "v26_conditional_candidate_model.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v26_conditional_full_factors.yaml"
DEFAULT_PROGRAM = FACTOR_BASE / "v26_conditional_full.factors"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--fit", type=Path, default=DEFAULT_FIT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--program", type=Path, default=DEFAULT_PROGRAM)
    return parser.parse_args()


def _factor_record(rule: dict[str, Any]) -> dict[str, Any]:
    weight = float(rule["weight"])
    is_v26 = rule["feature"]["kind"] == "central_joint_weak_resolution_status"
    record = {
        "id": rule["id"],
        "family": rule["family"],
        "feature": rule["feature"],
        "parameter": {
            "scale": "log_energy_contribution",
            "log_weight": weight,
            "sign": (
                "preference" if weight > 0 else "avoidance" if weight < 0 else "neutral"
            ),
        },
        "origin": rule["origin"],
        "human_authored": False,
        "preference_human_authored": False,
        "feature_definition_human_authored": True,
        "grounding": "k3_feature_evaluator",
        "member_role": (
            "joint_weak_resolution_status" if is_v26 else "retained_v24_baseline"
        ),
    }
    if is_v26:
        record["rule_group"] = "RG-LEARNED-V26-001"
    return record


def main() -> int:
    args = parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    if not fit["selection"]["group_retained"]:
        raise ValueError("V26 was not selected by the frozen protocol")
    parameters = fit["selected_parameters"]
    features = k3.joint_weak_resolution_feature_catalogue()
    baseline_rules = baseline["model"]["rules"]
    baseline_count = len(baseline_rules)
    weights = list(map(float, parameters["factor_weights"]))
    if len(weights) != baseline_count + len(features):
        raise ValueError("V26 selected parameter vector has the wrong size")

    candidate = json.loads(json.dumps(baseline))
    candidate["experiment"] = {
        **baseline["experiment"],
        "id": "K3-V26-CONDITIONAL-CANDIDATE-1",
        "status": "CONDITIONAL_VALIDATION_CANDIDATE",
        "source_fit": fit["experiment"]["id"],
        "selected_penalty": fit["selection"]["selected_penalty"],
        "learned_factor_count": len(weights),
        "new_joint_weak_resolution_factor_count": len(features),
        "rule_group_count": int(baseline["experiment"]["rule_group_count"]) + 1,
        "generated_bwv108_6_used_for_learning": False,
        "test_loaded": False,
    }
    candidate["model"]["register_logits"] = parameters["register_logits"]
    candidate["model"]["tonal_logits"] = parameters["tonal_logits"]
    for rule, weight in zip(
        candidate["model"]["rules"],
        weights[:baseline_count],
        strict=True,
    ):
        rule["weight"] = weight
        rule["origin"] = "joint_conditional_mle_v26_refit"
    candidate["model"]["rules"].extend(
        {
            "id": f"F-K3-V26-{index:03d}",
            "family": "joint_weak_resolution_status",
            "clause": feature.label,
            "feature": feature.to_dict(),
            "weight": weight,
            "origin": "joint_conditional_mle_from_bach_corpus",
            "human_authored": False,
            "calls_other_rules": False,
            "rule_group": "RG-LEARNED-V26-001",
        }
        for index, (feature, weight) in enumerate(
            zip(features, weights[baseline_count:], strict=True),
            start=1,
        )
    )

    factors = [_factor_record(rule) for rule in candidate["model"]["rules"]]
    catalogue = {
        "schema_version": 1,
        "id": "K3-V26-CONDITIONAL-JOINT-WEAK-RESOLUTION",
        "model_id": candidate["experiment"]["id"],
        "source_model": str(args.model.resolve()),
        "factor_group": "k3_v26_conditional_joint_weak_resolution",
        "status": "CONDITIONAL_VALIDATION_CANDIDATE",
        "counts": {
            "canonical_factors_after_merge": len(factors),
            "retained_v24_factors": baseline_count,
            "new_joint_weak_resolution_cells": len(features),
            "rule_groups": candidate["experiment"]["rule_group_count"],
        },
        "factors": factors,
    }
    program = render_factor_program(
        catalogue,
        group_name="k3_v26_conditional_joint_weak_resolution",
        source_label=args.catalogue.name,
    )
    (parsed,) = parse_factor_groups(program)
    if len(parsed.factors) != len(factors):
        raise ValueError("V26 Snarky program lost factors during parsing")

    args.model.write_text(
        json.dumps(candidate, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    args.program.write_text(program, encoding="utf-8")
    print(f"[v26-export] wrote {args.model}", flush=True)
    print(f"[v26-export] wrote {args.catalogue}", flush=True)
    print(f"[v26-export] wrote {args.program}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
