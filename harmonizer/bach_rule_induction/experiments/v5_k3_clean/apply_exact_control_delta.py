#!/usr/bin/env python3
"""Apply a train-only generative control direction under an exact-NLL guard."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import run_exact_factor_reinduction as reinduction

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--exact-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--max-abs-step", type=float, default=0.1)
    parser.add_argument("--max-validation-nll-increase", type=float, default=0.02)
    return parser.parse_args()


def _exact_validation_nll(
    archive: Any,
    candidates: np.ndarray,
    register: np.ndarray,
    tonal: np.ndarray,
    weights: np.ndarray,
) -> float:
    return reinduction._nll(
        archive["validation_chosen"],
        archive["validation_voices"],
        archive["validation_modes"],
        archive["validation_tonics"],
        candidates,
        archive["validation_factors"],
        reinduction.Parameters(register, tonal, weights),
    )


def _markdown(payload: dict[str, Any]) -> str:
    correction = payload["model"]["exact_generative_control_correction"]
    return "\n".join(
        [
            "# V12 — correction générative sous garde conditionnelle exacte",
            "",
            "La structure V10 reste gelée. Une direction issue des covariances",
            "Gibbs sur train est appliquée une seule fois. Son amplitude respecte",
            "à la fois un rayon de confiance et une limite de dégradation de la",
            "pseudo-vraisemblance exacte sur validation.",
            "",
            f"- Échelle demandée : `{correction['requested_scale']:.6f}`.",
            f"- Échelle appliquée : `{correction['applied_scale']:.6f}`.",
            (
                "- Plus grand déplacement de poids : "
                f"`{correction['max_abs_applied_delta']:.6f}`."
            ),
            (
                "- NLL validation exacte : "
                f"`{correction['source_validation_nll']:.6f}` → "
                f"`{correction['validation_nll']:.6f}`."
            ),
            (
                "- Budget de dégradation : "
                f"`{correction['max_validation_nll_increase']:.6f}`."
            ),
            "- Facteurs ajoutés : `0`.",
            "- Test réservé chargé : `false`.",
            "",
            "Ce modèle reste un candidat jusqu'aux audits génératifs appariés.",
        ]
    )


def main() -> int:
    args = parse_args()
    source = json.loads(args.model.read_text(encoding="utf-8"))
    control = json.loads(args.control.read_text(encoding="utf-8"))
    if control["experiment"]["test_loaded"]:
        raise ValueError("The control direction must not use the test split")
    rules = source["model"]["rules"]
    keys = [rule["feature"]["key"] for rule in rules]
    archive = np.load(args.exact_cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != keys:
        raise ValueError("Exact cache and model factor structures differ")
    proposed = np.asarray(
        control["control"]["proposed_weight_delta"],
        dtype=np.float64,
    )
    if proposed.shape != (len(rules),):
        raise ValueError("Control direction and model have different sizes")
    if args.scale <= 0 or args.max_abs_step <= 0:
        raise ValueError("Scale and trust-region radius must be positive")
    source_weights = np.asarray(
        [float(rule["weight"]) for rule in rules],
        dtype=np.float64,
    )
    register = np.asarray(source["model"]["register_logits"], dtype=np.float64)
    tonal = np.asarray(source["model"]["tonal_logits"], dtype=np.float64)
    corpus = source["corpus"]
    candidates = np.arange(
        int(corpus["candidate_min"]),
        int(corpus["candidate_max"]) + 1,
        dtype=np.int16,
    )
    source_nll = _exact_validation_nll(
        archive,
        candidates,
        register,
        tonal,
        source_weights,
    )
    proposed_max = float(np.max(np.abs(proposed), initial=0.0))
    upper = min(args.scale, args.max_abs_step / max(proposed_max, 1e-12))
    nll_limit = source_nll + args.max_validation_nll_increase

    def evaluate(scale: float) -> float:
        return _exact_validation_nll(
            archive,
            candidates,
            register,
            tonal,
            source_weights + scale * proposed,
        )

    if evaluate(upper) > nll_limit:
        lower = 0.0
        for _ in range(40):
            middle = (lower + upper) / 2.0
            if evaluate(middle) <= nll_limit:
                lower = middle
            else:
                upper = middle
        applied_scale = lower
    else:
        applied_scale = upper
    delta = applied_scale * proposed
    weights = source_weights + delta
    validation_nll = evaluate(applied_scale)
    output = copy.deepcopy(source)
    output["experiment"] = {
        **source["experiment"],
        "id": args.experiment_id,
        "status": "EXACT_HYBRID_WEIGHT_CANDIDATE_PENDING_GENERATION_AUDIT",
        "source_model": str(args.model.resolve()),
        "control_analysis": str(args.control.resolve()),
        "factor_structure_frozen": True,
        "new_factor_count": 0,
        "test_loaded": False,
    }
    for rule, weight in zip(output["model"]["rules"], weights, strict=True):
        rule["weight"] = float(weight)
    output["model"]["validation_nll"] = validation_nll
    output["model"]["exact_generative_control_correction"] = {
        "method": "minimum_norm_covariance_projection_with_exact_nll_guard",
        "gradient_source": "train_only",
        "requested_scale": args.scale,
        "applied_scale": applied_scale,
        "max_abs_step": args.max_abs_step,
        "max_abs_applied_delta": float(np.max(np.abs(delta), initial=0.0)),
        "source_validation_nll": source_nll,
        "validation_nll": validation_nll,
        "max_validation_nll_increase": args.max_validation_nll_increase,
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
    args.report.write_text(_markdown(output) + "\n", encoding="utf-8")
    print(f"[exact-control] scale={applied_scale:.6f}")
    print(f"[exact-control] validation={source_nll:.6f}->{validation_nll:.6f}")
    print(f"[exact-control] wrote {args.output}")
    print(f"[exact-control] wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
