#!/usr/bin/env python3
"""Apply one train-derived controllability correction to frozen V6 weights."""

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
DEFAULT_MODEL = FACTOR_BASE / "v6_train64_generative_refit_model.json"
DEFAULT_CONTROL = FACTOR_BASE / "v6_train64_controllability.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v6_train64_controlled_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V6_TRAIN64_CONTROLLED_MODEL.md"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def trust_region_scale(
    proposed_delta: np.ndarray,
    requested_scale: float,
    max_abs_step: float | None,
) -> float:
    """Scale one complete direction without changing its relative components."""

    proposed = np.asarray(proposed_delta, dtype=np.float64)
    if proposed.ndim != 1 or not np.isfinite(proposed).all():
        raise ValueError("Proposed delta must be one finite vector")
    if not np.isfinite(requested_scale) or requested_scale <= 0:
        raise ValueError("Correction scale must be positive and finite")
    if max_abs_step is not None and (
        not np.isfinite(max_abs_step) or max_abs_step <= 0
    ):
        raise ValueError("Trust-region radius must be positive and finite")
    proposed_max = float(np.max(np.abs(proposed), initial=0.0))
    if max_abs_step is None or proposed_max == 0:
        return requested_scale
    return min(requested_scale, max_abs_step / proposed_max)


def _markdown(result: dict[str, Any]) -> str:
    correction = result["model"]["generative_control_correction"]
    max_abs_step = correction["max_abs_step"]
    rendered_max_abs_step = "none" if max_abs_step is None else str(max_abs_step)
    lines = [
        "# V6 — correction générative contrôlée, structure gelée",
        "",
        "Les 30 facteurs restent strictement identiques. Le vecteur de poids est",
        "déplacé une seule fois selon la correction linéaire minimale estimée",
        "sur le train par la matrice de covariance. Aucun réglage sur validation",
        "n'est effectué et le test réservé n'est pas chargé.",
        "",
        "## Paramètres",
        "",
        f"- Échelle demandée : `{correction['requested_scale']:.6f}`.",
        f"- Échelle effectivement appliquée : `{correction['scale']:.6f}`.",
        (
            f"- Rayon maximal du pas : "
            f"`{rendered_max_abs_step}`."
        ),
        f"- Facteurs modifiés : `{correction['changed_factor_count']}`.",
        (f"- Plus grand déplacement : `{correction['max_abs_applied_delta']:.6f}`."),
        (
            f"- NLL conditionnelle validation : "
            f"`{correction['source_validation_nll']:.6f}` → "
            f"`{correction['validation_nll']:.6f}`."
        ),
        "",
        "La décision dépend maintenant d'un nouvel audit génératif sur les mêmes",
        "pièces et graines que les modèles précédents.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--control", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument(
        "--experiment-id",
        default="F-K3-V6-TRAIN64-CONTROLLED-WEIGHTS",
    )
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument(
        "--max-abs-step",
        type=float,
        help=(
            "Trust-region radius. If needed, scale the complete proposed "
            "direction so no absolute weight displacement exceeds this value."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = json.loads(args.model.read_text(encoding="utf-8"))
    control = json.loads(args.control.read_text(encoding="utf-8"))
    if control["experiment"]["test_loaded"]:
        raise ValueError("A controllability correction cannot use the test split")
    if control["experiment"]["factor_structure_changed"]:
        raise ValueError("Controllability input unexpectedly changed factor structure")
    model = source["model"]
    factors = model["factors"]
    rules = model["rules"]
    proposed_delta = np.asarray(
        control["control"]["proposed_weight_delta"],
        dtype=np.float64,
    )
    if proposed_delta.shape != (len(rules),) or len(factors) != len(rules):
        raise ValueError("Control delta and frozen factor structure differ")
    effective_scale = trust_region_scale(
        proposed_delta,
        args.scale,
        args.max_abs_step,
    )
    delta = effective_scale * proposed_delta
    source_weights = np.asarray(
        [float(rule["weight"]) for rule in rules],
        dtype=np.float64,
    )
    weights = source_weights + delta

    corpus = source["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    features = tuple(k3.feature_from_model_record(rule) for rule in rules)
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    full = k3.load_k3_dataset(args.cache)
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, removed = k3.filter_to_domain(
        validation,
        candidate_min,
        candidate_max,
    )
    if removed:
        raise ValueError("Validation choices fall outside the train domain")
    validation_nll = generative._conditional_validation_nll(
        validation,
        register_logits,
        tonal_logits,
        features,
        weights,
    )

    output = copy.deepcopy(source)
    output["experiment"] = {
        **source["experiment"],
        "id": args.experiment_id,
        "status": "TRAIN_DERIVED_CONTROL_DELTA_PENDING_VALIDATION",
        "source_model": str(args.model.resolve()),
        "control_analysis": str(args.control.resolve()),
        "test_loaded": False,
        "factor_structure_frozen": True,
        "new_factor_count": 0,
    }
    output_rules = output["model"]["rules"]
    output_factors = output["model"]["factors"]
    for rule, factor, weight in zip(
        output_rules,
        output_factors,
        weights,
        strict=True,
    ):
        rule["weight"] = float(weight)
        factor["parameter"]["log_weight"] = float(weight)
        factor["parameter"]["sign"] = "preference" if weight > 0 else "avoidance"
    output["model"]["validation_nll"] = validation_nll
    output["model"]["generative_control_correction"] = {
        "method": "minimum_norm_covariance_projection",
        "gradient_source": "train_only",
        "requested_scale": args.scale,
        "scale": effective_scale,
        "max_abs_step": args.max_abs_step,
        "changed_factor_count": int(np.count_nonzero(delta)),
        "max_abs_applied_delta": float(np.max(np.abs(delta))),
        "source_validation_nll": float(model["validation_nll"]),
        "validation_nll": validation_nll,
        "applied_delta": delta.tolist(),
        "target_diagnostics": control["diagnostics"],
        "factor_structure_changed": False,
        "new_factor_count": 0,
        "test_loaded": False,
    }
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(output), encoding="utf-8")
    print(f"[v6-control-apply] wrote {args.output}", flush=True)
    print(f"[v6-control-apply] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
