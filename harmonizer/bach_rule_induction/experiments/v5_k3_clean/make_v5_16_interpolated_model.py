#!/usr/bin/env python3
"""Interpolate the V5.15 bass correction onto the frozen V5.14 model."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def _description(feature: k3.FeatureSpec) -> str:
    if feature.kind == "abs_step_from_previous_gt":
        return f"saut de basse supérieur à {feature.value} demi-tons"
    if feature.kind == "abs_class_from_previous":
        return f"classe d'intervalle entrant {feature.value} à la basse"
    if feature.kind == "three_block_sign_shape":
        return (
            f"directions K3 de basse ({feature.value:+d}, "
            f"{feature.second_value:+d})"
        )
    return feature.label


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V5.16 — interpolation tenue à part des corrections de basse",
        "",
        "V5.14 sous-corrigeait le mouvement de basse et V5.15 le surcorrigeait.",
        "Le facteur `0,5` a été choisi sur les dix premiers chorals de validation",
        "utilisés comme développement. Les dix suivants restent tenus à part pour",
        "la confirmation. Le test scellé reste fermé.",
        "",
        "Seuls les quatre deltas V5.15 sont interpolés ;",
        "le socle harmonique V5.14 est inchangé.",
        "",
        "| Correction | Delta V5.15 | Delta V5.16 |",
        "|---|---:|---:|",
    ]
    for rule in result["model"]["v5_16_rules"]:
        feature = k3.feature_from_model_record(rule)
        lines.append(
            f"| {_description(feature)} | "
            f"{rule['source_weight']:+.4f} | {rule['weight']:+.4f} |"
        )
    lines.extend(
        [
            "",
            (
                "NLL conditionnelle de validation après interpolation : "
                f"`{result['model']['validation_nll']:.6f}`."
            ),
            "",
            "Cette interpolation est un hyperparamètre de calibration générative,",
            "pas une nouvelle règle musicale. Les deltas devront être fusionnés",
            "avec les poids des clauses identiques dans la base finale.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        type=Path,
        default=HERE / "results/v5_14_explicit_generative_model.json",
    )
    parser.add_argument(
        "--corrected",
        type=Path,
        default=HERE / "results/v5_15_explicit_generative_model.json",
    )
    parser.add_argument("--scale", type=float, default=0.5)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0.0 <= args.scale <= 1.0:
        raise ValueError("Interpolation scale must lie between zero and one")
    base = json.loads(args.base.read_text(encoding="utf-8"))
    corrected = json.loads(args.corrected.read_text(encoding="utf-8"))
    correction_rules = corrected["model"]["v5_15_rules"]
    expected_rule_count = len(base["model"]["rules"]) + len(correction_rules)
    if len(corrected["model"]["rules"]) != expected_rule_count:
        raise ValueError("V5.15 is not a direct four-rule extension of V5.14")

    output = copy.deepcopy(base)
    output["experiment"] = {
        "id": "V5_16-K3-INTERPOLATED-BASS-CALIBRATION",
        "version": "V5.16",
        "model_key": "v5_16",
        "status": "EXPLORATORY_FROZEN_FOR_CONFIRMATION",
        "test_loaded": False,
        "source_model": str(args.base.resolve()),
        "correction_model": str(args.corrected.resolve()),
        "interpolation_scale": args.scale,
        "scale_selection_pieces": "validation[0:10]",
        "confirmation_pieces": "validation[10:20]",
        "latent_states": False,
    }
    interpolated = []
    for rule in correction_rules:
        scaled = copy.deepcopy(rule)
        scaled["source_weight"] = float(rule["weight"])
        scaled["weight"] = args.scale * float(rule["weight"])
        interpolated.append(scaled)
    output["model"]["v5_16_rule_count"] = len(interpolated)
    output["model"]["v5_16_rules"] = interpolated
    output["model"]["v5_16_interpolation_scale"] = args.scale
    output["model"]["rules"].extend(interpolated)
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    full = k3.load_k3_dataset(args.cache)
    corpus = output["corpus"]
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, removed = k3.filter_to_domain(
        validation,
        int(corpus["candidate_min"]),
        int(corpus["candidate_max"]),
    )
    if removed:
        raise ValueError("Validation choices unexpectedly fall outside train domain")
    model = output["model"]
    features = tuple(
        k3.feature_from_model_record(rule) for rule in model["rules"]
    )
    weights = np.asarray(
        [rule["weight"] for rule in model["rules"]],
        dtype=np.float64,
    )
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    matrix = k3.feature_matrix(validation, features)
    base_scores = k3.contextual_base_scores(
        validation,
        register_logits,
        tonal_logits,
    )
    output["model"]["validation_nll"] = k3.conditional_nll(
        validation,
        register_logits,
        matrix,
        weights,
        base_scores=base_scores,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_16_interpolated_generative_model.json"
    report_path = args.output_dir / "V5_16_INTERPOLATED_GENERATIVE_MODEL.md"
    json_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(output), encoding="utf-8")
    print(f"[k3-v5.16] wrote {json_path}")
    print(f"[k3-v5.16] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
