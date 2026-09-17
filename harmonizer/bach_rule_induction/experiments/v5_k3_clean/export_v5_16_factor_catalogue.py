#!/usr/bin/env python3
"""Export frozen V5.16 rules as one canonical probabilistic factor catalogue."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import k3
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
DEFAULT_MODEL = HERE / "results/v5_16_interpolated_generative_model.json"
DEFAULT_OUTPUT = (
    REPOSITORY
    / "harmonizer/bach_rule_induction/rule_bases/k3_clean/v5_16_factors.yaml"
)


def _layer(index: int, model: dict[str, Any]) -> str:
    base = int(model.get("base_rule_count", 20))
    chromatic = int(model.get("calibration_rule_count", 8))
    explicit = int(model.get("v5_14_rule_count", 12))
    if index < base:
        return "v5_7_contextual_base"
    if index < base + chromatic:
        return "v5_9_chromatic_calibration"
    if index < base + chromatic + explicit:
        return "v5_14_explicit_calibration"
    return "v5_16_interpolated_bass_correction"


def factor_grounding(feature: k3.FeatureSpec) -> str:
    """Return the unique joint-energy instantiation policy."""

    if feature.kind == "bass_pcset_transition":
        return "once_per_k3_transition"
    if feature.kind in k3.SHARED_POTENTIAL_KINDS:
        return "once_per_vertical_block"
    if feature.target_voice in range(4):
        return "once_per_target_voice_attack"
    return "once_per_attack_decision"


def factor_scope(feature: k3.FeatureSpec) -> dict[str, Any]:
    if feature.kind == "bass_pcset_transition":
        blocks = ["current", "following"]
    elif "from_previous" in feature.kind:
        blocks = ["previous", "current"]
    elif "to_next" in feature.kind:
        blocks = ["current", "following"]
    elif "three_block" in feature.kind or "resolution" in feature.kind:
        blocks = ["previous", "current", "following"]
    else:
        blocks = ["current"]
    voices = (
        ["decision_voice"]
        if feature.target_voice == -1
        else [k3.VOICE_NAMES[feature.target_voice].lower()]
    )
    if feature.other_voice is not None:
        voices.append(k3.VOICE_NAMES[feature.other_voice].lower())
    if feature.kind in k3.SHARED_POTENTIAL_KINDS:
        voices = [name.lower() for name in k3.VOICE_NAMES]
    return {"blocks": blocks, "voices": voices}


def merge_rules(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge additive corrections of an identical feature into one factor."""

    merged: dict[str, dict[str, Any]] = {}
    for index, rule in enumerate(model["rules"]):
        feature = k3.feature_from_model_record(rule)
        weight = float(rule["weight"])
        entry = merged.setdefault(
            feature.key,
            {
                "feature": feature,
                "log_weight": 0.0,
                "sources": [],
            },
        )
        entry["log_weight"] += weight
        source: dict[str, Any] = {
            "layer": _layer(index, model),
            "source_index": index,
            "log_weight": weight,
        }
        selection = rule.get("selection")
        if isinstance(selection, dict):
            source["selection"] = {
                key: selection[key]
                for key in ("bach_rate", "gibbs_rate", "gradient", "z_score")
                if key in selection
            }
        if "source_weight" in rule:
            source["unscaled_source_weight"] = float(rule["source_weight"])
        entry["sources"].append(source)
    return [merged[key] for key in sorted(merged)]


def _factor_record(index: int, entry: dict[str, Any]) -> dict[str, Any]:
    feature: k3.FeatureSpec = entry["feature"]
    weight = float(entry["log_weight"])
    return {
        "id": f"F-K3-V5.16-{index:03d}",
        "key": feature.key,
        "label": feature.label,
        "scope": factor_scope(feature),
        "grounding": factor_grounding(feature),
        "feature": {
            key: value
            for key, value in feature.to_dict().items()
            if key not in {"key", "label"}
        },
        "parameter": {
            "scale": "log_energy_contribution",
            "log_weight": weight,
            "odds_multiplier_isolated": math.exp(weight),
            "sign": (
                "preference"
                if weight > 0
                else "avoidance"
                if weight < 0
                else "neutral"
            ),
        },
        "sources": entry["sources"],
    }


def build_catalogue(payload: dict[str, Any], model_path: Path) -> dict[str, Any]:
    model = payload["model"]
    merged = merge_rules(model)
    try:
        portable_model_path = str(model_path.resolve().relative_to(REPOSITORY))
    except ValueError:
        portable_model_path = str(model_path)
    return {
        "schema_version": 1,
        "id": "S-K3-LEARNED-V5.16-FACTORS",
        "status": "PROBABILISTIC_CONFIRMED_NOT_YET_COMPILED_TO_RULE_DSL",
        "source_model": portable_model_path,
        "probability_model": {
            "family": "conditional_log_linear_with_gibbs_joint_generation",
            "score": "baseline(candidate) + sum(log_weight * feature)",
            "choice_weight": "exp(local_score - max_local_score)",
            "hard_constraints": "remove_candidate_before_normalization",
        },
        "locality": {
            "kernel": "K3",
            "radius": 1,
            "blocks": 3,
            "attack_hold_semantics": True,
        },
        "grounding_semantics": {
            "shared_potentials_counted_once": True,
            "introduced_in": "V5.14",
        },
        "counts": {
            "source_weight_terms": len(model["rules"]),
            "canonical_factors_after_merge": len(merged),
            "merged_additive_terms": len(model["rules"]) - len(merged),
        },
        "baselines": {
            "register_logits": "embedded_in_source_model",
            "voice_mode_tonal_logits": "embedded_in_source_model",
        },
        "confirmation": {
            "pieces": 10,
            "seeds_per_piece": 3,
            "sweeps": 6,
            "report": (
                "../../experiments/v5_k3_clean/results/"
                "V5_16_MULTISEED_CONFIRMATION_AUDIT.md"
            ),
            "stable_audited_residuals": 0,
            "test_split_loaded": False,
        },
        "factors": [
            _factor_record(index, entry)
            for index, entry in enumerate(merged, start=1)
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    import json

    args = parse_args()
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    catalogue = build_catalogue(payload, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(
            catalogue,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        ),
        encoding="utf-8",
    )
    print(
        "[k3-factor-export] "
        f"{catalogue['counts']['source_weight_terms']} terms -> "
        f"{catalogue['counts']['canonical_factors_after_merge']} factors"
    )
    print(f"[k3-factor-export] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
