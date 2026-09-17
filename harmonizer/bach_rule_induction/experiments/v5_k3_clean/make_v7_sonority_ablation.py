#!/usr/bin/env python3
"""Remove the overcorrecting V7 bass family and retain sonority factors."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v7_residual_six_factor_model.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v7_sonority_four_factor_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V7_SONORITY_FOUR_FACTOR_MODEL.md"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def _markdown(result: dict[str, Any]) -> str:
    ablation = result["model"]["v7_sonority_ablation"]
    lines = [
        "# V7-Sonority — ablation de la famille basse",
        "",
        "Les deux facteurs `bass_motion` de V7 sont retirés après leur",
        "surcorrection significative des grands sauts aux horizons 6 et 30.",
        "Les 30 facteurs V6 et les quatre facteurs métriques/de transition",
        "conservent exactement leurs poids.",
        "",
        f"- Facteurs retirés : `{ablation['removed_factor_ids']}`.",
        f"- Facteurs V7 conservés : `{ablation['retained_factor_ids']}`.",
        (
            f"- NLL conditionnelle validation : "
            f"`{ablation['source_validation_nll']:.6f}` → "
            f"`{ablation['validation_nll']:.6f}`."
        ),
        "",
        "Ce modèle reste candidat jusqu'aux audits génératifs à 6 et 30 sweeps.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = json.loads(args.model.read_text(encoding="utf-8"))
    factors = source["model"]["factors"]
    rules = source["model"]["rules"]
    if len(factors) != len(rules):
        raise ValueError("Rules and factors must remain aligned")
    retained_pairs = []
    removed = []
    retained_v7 = []
    for factor, rule in zip(factors, rules, strict=True):
        is_v7 = factor["id"].startswith("F-K3-V7-")
        if is_v7 and factor["family"] == "bass_motion":
            removed.append(factor["id"])
            continue
        retained_pairs.append((factor, rule))
        if is_v7:
            retained_v7.append(factor["id"])
    if len(removed) != 2 or len(retained_v7) != 4:
        raise ValueError("Expected exactly two removed and four retained V7 factors")

    output = copy.deepcopy(source)
    output["model"]["factors"] = [copy.deepcopy(pair[0]) for pair in retained_pairs]
    output["model"]["rules"] = [copy.deepcopy(pair[1]) for pair in retained_pairs]
    features = tuple(
        k3.feature_from_model_record(rule) for _, rule in retained_pairs
    )
    weights = np.asarray(
        [rule["weight"] for _, rule in retained_pairs],
        dtype=np.float64,
    )
    corpus = output["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(
        output["model"]["register_logits"],
        dtype=np.float64,
    )
    tonal_logits = np.asarray(
        output["model"]["tonal_logits"],
        dtype=np.float64,
    )
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    full = k3.load_k3_dataset(args.cache)
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, outside = k3.filter_to_domain(
        validation,
        candidate_min,
        candidate_max,
    )
    if outside:
        raise ValueError("Validation choices fall outside the train domain")
    validation_nll = generative._conditional_validation_nll(
        validation,
        register_logits,
        tonal_logits,
        features,
        weights,
    )
    source_nll = float(output["model"]["validation_nll"])
    output["model"]["validation_nll"] = validation_nll
    output["model"]["v7_sonority_ablation"] = {
        "method": "family_ablation_without_refit",
        "removed_factor_ids": removed,
        "retained_factor_ids": retained_v7,
        "source_validation_nll": source_nll,
        "validation_nll": validation_nll,
        "base_v6_weights_changed": False,
        "retained_v7_weights_changed": False,
        "test_loaded": False,
    }
    output["experiment"] = {
        **source["experiment"],
        "id": "F-K3-V7-SONORITY-FOUR-FACTOR",
        "status": "PENDING_GENERATIVE_AUDIT",
        "source_model": str(args.model.resolve()),
        "new_factor_count": 4,
        "ablation_without_refit": True,
        "test_loaded": False,
    }
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(output), encoding="utf-8")
    print(f"[v7-ablation] wrote {args.output}", flush=True)
    print(f"[v7-ablation] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
