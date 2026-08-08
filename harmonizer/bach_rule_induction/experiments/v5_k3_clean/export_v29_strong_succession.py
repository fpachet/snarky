#!/usr/bin/env python3
"""Export the confirmed V29 strong-succession model and Snarky factors."""

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
DEFAULT_BASELINE = FACTOR_BASE / "v28_bass_motion_full_model.json"
DEFAULT_FIT = FACTOR_BASE / "v29_strong_succession_confirmation50.json"
DEFAULT_MODEL = FACTOR_BASE / "v29_strong_succession_full_model.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v29_strong_succession_full_factors.yaml"
DEFAULT_PROGRAM = FACTOR_BASE / "v29_strong_succession_full.factors"


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
    is_v29 = rule["feature"]["kind"] == "central_strong_succession_status"
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
            "strong_succession_status" if is_v29 else "retained_v28_baseline"
        ),
    }
    if is_v29:
        record["rule_group"] = "RG-LEARNED-V29-001"
    return record


def main() -> int:
    args = parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    if not fit["selection"]["group_retained"]:
        raise ValueError("V29 was not confirmed by the frozen protocol")
    parameters = fit["selected_parameters"]
    features = k3.strong_succession_status_feature_catalogue()
    baseline_rules = baseline["model"]["rules"]
    baseline_count = len(baseline_rules)
    weights = list(map(float, parameters["factor_weights"]))
    if len(weights) != baseline_count + len(features):
        raise ValueError("V29 selected parameter vector has the wrong size")

    candidate = json.loads(json.dumps(baseline))
    candidate["experiment"] = {
        **baseline["experiment"],
        "id": "K3-V29-STRONG-SUCCESSION-FULL-1",
        "status": "CONDITIONALLY_CONFIRMED",
        "source_fit": fit["experiment"]["id"],
        "selected_penalty": fit["selection"]["selected_penalty"],
        "learned_factor_count": len(weights),
        "new_strong_succession_factor_count": len(features),
        "rule_group_count": int(baseline["experiment"]["rule_group_count"]) + 1,
        "confirmation_validation_pieces": fit["experiment"]["validation_piece_count"],
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
        rule["origin"] = "joint_conditional_mle_v29_refit"
    candidate["model"]["rules"].extend(
        {
            "id": f"F-K3-V29-{index:03d}",
            "family": "strong_succession_status",
            "clause": feature.label,
            "feature": feature.to_dict(),
            "weight": weight,
            "origin": "joint_conditional_mle_from_bach_corpus",
            "human_authored": False,
            "calls_other_rules": False,
            "rule_group": "RG-LEARNED-V29-001",
        }
        for index, (feature, weight) in enumerate(
            zip(features, weights[baseline_count:], strict=True),
            start=1,
        )
    )

    factors = [_factor_record(rule) for rule in candidate["model"]["rules"]]
    catalogue = {
        "schema_version": 1,
        "id": "K3-V29-CONFIRMED-STRONG-SUCCESSION",
        "model_id": candidate["experiment"]["id"],
        "source_model": str(args.model.resolve()),
        "factor_group": "k3_v29_confirmed_strong_succession",
        "status": "CONDITIONALLY_CONFIRMED",
        "counts": {
            "canonical_factors_after_merge": len(factors),
            "retained_v28_factors": baseline_count,
            "new_strong_succession_cells": len(features),
            "rule_groups": candidate["experiment"]["rule_group_count"],
        },
        "factors": factors,
    }
    program = render_factor_program(
        catalogue,
        group_name="k3_v29_confirmed_strong_succession",
        source_label=args.catalogue.name,
    )
    (parsed,) = parse_factor_groups(program)
    if len(parsed.factors) != len(factors):
        raise ValueError("V29 Snarky program lost factors during parsing")

    args.model.write_text(
        json.dumps(candidate, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    args.program.write_text(program, encoding="utf-8")
    print(f"[v29-export] wrote {args.model}", flush=True)
    print(f"[v29-export] wrote {args.catalogue}", flush=True)
    print(f"[v29-export] wrote {args.program}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
