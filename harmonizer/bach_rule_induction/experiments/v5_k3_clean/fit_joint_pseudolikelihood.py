#!/usr/bin/env python3
"""Jointly learn all retained K3 factor weights by pseudo-likelihood."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_contextual_induction as contextual

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_STRUCTURE_MODEL = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_GENERATIVE_REFERENCE = (
    FACTOR_BASE / "v6_train64_multimetric_iteration2_model.json"
)
DEFAULT_RESIDUAL = FACTOR_BASE / "v6_iteration3_residual_feature_diagnostic.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v8_joint_pseudolikelihood_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V8_JOINT_PSEUDOLIKELIHOOD_MODEL.md"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_MANIFEST = (
    REPOSITORY / "harmonizer/bach_rule_induction/corpus/manifest.music21-3.1.0.json"
)
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_ARCHIVE = (
    REPOSITORY.parent / "deepbach-reference/resources/cache/music21-3.1.0.tar.gz"
)


def _combined_records(
    structure_payload: dict[str, Any],
    residual_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return one canonical record per factor, preserving deterministic order."""

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rule in structure_payload["model"]["rules"]:
        feature = k3.feature_from_model_record(rule)
        if feature.key in seen:
            continue
        seen.add(feature.key)
        records.append(
            {
                "feature": feature,
                "origin": "v6_structure",
                "description": feature.label,
                "family": next(
                    (
                        factor["family"]
                        for factor in structure_payload["model"].get("factors", [])
                        if factor["feature"]["key"] == feature.key
                    ),
                    "v6_selected",
                ),
                "selection": rule.get("selection", {}),
            }
        )
    for candidate in residual_payload["selected"]:
        feature = k3.feature_from_model_record(candidate)
        if feature.key in seen:
            continue
        seen.add(feature.key)
        records.append(
            {
                "feature": feature,
                "origin": "v6_iteration3_residual",
                "description": candidate["description"],
                "family": candidate["family"],
                "selection": {
                    key: candidate[key]
                    for key in (
                        "bach_rate",
                        "gibbs_rate",
                        "gradient",
                        "z_score",
                        "seed_sign_agreement",
                    )
                },
            }
        )
    return records


def _model_nll(
    dataset: k3.K3Dataset,
    register: np.ndarray,
    tonal: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    weights: np.ndarray,
) -> float:
    base = k3.contextual_base_scores(dataset, register, tonal)
    matrix = k3.feature_matrix(dataset, features)
    return k3.conditional_nll(
        dataset,
        register,
        matrix,
        weights,
        base_scores=base,
    )


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    comparison = result["comparison"]
    model = result["model"]
    lines = [
        "# V8 — apprentissage conjoint par pseudo-vraisemblance",
        "",
        "Tous les facteurs retenus contribuent au score de chaque note candidate",
        "avant le softmax. Les poids sont appris simultanément sur les choix",
        "authentiques de Bach; aucun poids V6 n'est gelé. Le test réservé reste",
        "fermé.",
        "",
        "## Protocole",
        "",
        f"- Décisions train : `{experiment['train_decisions']}`.",
        f"- Décisions validation : `{experiment['validation_decisions']}`.",
        f"- Alternatives par décision : `{experiment['candidate_count']}`.",
        f"- Facteurs V6 : `{experiment['base_factor_count']}`.",
        f"- Facteurs résiduels candidats : `{experiment['residual_factor_count']}`.",
        f"- Facteurs appris conjointement : `{experiment['factor_count']}`.",
        f"- L1 : `{experiment['l1']}`; L2 : `{experiment['l2']}`.",
        "",
        "## Pseudo-vraisemblance conditionnelle",
        "",
        "| Modèle | NLL train | NLL validation |",
        "|---|---:|---:|",
        (
            f"| Baseline registre + tonalité | — | "
            f"{comparison['tonal_baseline_validation_nll']:.6f} |"
        ),
        (
            f"| V6 appris par pseudo-vraisemblance | "
            f"{comparison['v6_structure_train_nll']:.6f} | "
            f"{comparison['v6_structure_validation_nll']:.6f} |"
        ),
        (
            f"| Iteration 2 après calibration générative | — | "
            f"{comparison['iteration2_validation_nll']:.6f} |"
        ),
        (
            f"| V8 conjoint ({experiment['factor_count']} facteurs) | "
            f"{model['train_nll']:.6f} | {model['validation_nll']:.6f} |"
        ),
        "",
        (
            f"Gain V8 contre la structure V6 en validation : "
            f"`{comparison['gain_vs_v6_structure']:+.6f}` nats/décision."
        ),
        "",
        "## Poids résiduels appris",
        "",
        "| Famille | Facteur | Poids |",
        "|---|---|---:|",
    ]
    for rule in model["rules"]:
        if rule["origin"] != "v6_iteration3_residual":
            continue
        lines.append(
            f"| `{rule['family']}` | {rule['description']} | "
            f"{rule['weight']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "Ce résultat mesure la prédiction locale. Une promotion exige encore",
            "les audits génératifs appariés à 6 et 30 sweeps.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure-model", type=Path, default=DEFAULT_STRUCTURE_MODEL)
    parser.add_argument(
        "--generative-reference",
        type=Path,
        default=DEFAULT_GENERATIVE_REFERENCE,
    )
    parser.add_argument("--residual", type=Path, default=DEFAULT_RESIDUAL)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument("--l1", type=float, default=0.0005)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    structure_payload = json.loads(args.structure_model.read_text(encoding="utf-8"))
    reference_payload = json.loads(
        args.generative_reference.read_text(encoding="utf-8")
    )
    residual_payload = json.loads(args.residual.read_text(encoding="utf-8"))
    if structure_payload["experiment"]["test_loaded"]:
        raise ValueError("Structure model unexpectedly loaded the reserved test split")
    if residual_payload["experiment"]["test_loaded"]:
        raise ValueError(
            "Residual diagnostic unexpectedly loaded the reserved test split"
        )

    train, validation, manifest, splits = contextual._load_contextual_data(
        args.archive,
        args.manifest,
        args.splits,
        args.cache,
    )
    records = _combined_records(structure_payload, residual_payload)
    features = tuple(record["feature"] for record in records)
    base_count = sum(record["origin"] == "v6_structure" for record in records)
    residual_count = len(records) - base_count
    register = np.asarray(
        structure_payload["model"]["register_logits"],
        dtype=np.float64,
    )
    tonal = np.asarray(
        structure_payload["model"]["tonal_logits"],
        dtype=np.float64,
    )
    train_base = k3.contextual_base_scores(train, register, tonal)
    validation_base = k3.contextual_base_scores(validation, register, tonal)
    print(
        f"[joint-pl] materializing {len(features)} factors over "
        f"{train.size} train and {validation.size} validation decisions",
        flush=True,
    )
    train_matrix = k3.feature_matrix(train, features)
    validation_matrix = k3.feature_matrix(validation, features)
    structure_weight_by_key = {
        k3.feature_from_model_record(rule).key: float(rule["weight"])
        for rule in structure_payload["model"]["rules"]
    }
    initial_weights = np.asarray(
        [
            structure_weight_by_key.get(feature.key, 0.0)
            for feature in features
        ],
        dtype=np.float64,
    )
    print(
        f"[joint-pl] fitting all {len(features)} weights jointly "
        "(V6 pseudo-likelihood initialization, no frozen weights)",
        flush=True,
    )
    weights, diagnostics = k3.fit_weights(
        train,
        validation,
        register,
        train_matrix,
        validation_matrix,
        l1=args.l1,
        l2=args.l2,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        train_base_scores=train_base,
        validation_base_scores=validation_base,
        initial_weights=initial_weights,
    )
    train_nll = k3.conditional_nll(
        train,
        register,
        train_matrix,
        weights,
        base_scores=train_base,
    )
    validation_nll = k3.conditional_nll(
        validation,
        register,
        validation_matrix,
        weights,
        base_scores=validation_base,
    )

    structure_features = tuple(
        k3.feature_from_model_record(rule)
        for rule in structure_payload["model"]["rules"]
    )
    structure_weights = np.asarray(
        [rule["weight"] for rule in structure_payload["model"]["rules"]],
        dtype=np.float64,
    )
    reference_features = tuple(
        k3.feature_from_model_record(rule)
        for rule in reference_payload["model"]["rules"]
    )
    reference_weights = np.asarray(
        [rule["weight"] for rule in reference_payload["model"]["rules"]],
        dtype=np.float64,
    )
    baseline_validation = k3.conditional_nll(
        validation,
        register,
        base_scores=validation_base,
    )
    structure_train_nll = _model_nll(
        train,
        register,
        tonal,
        structure_features,
        structure_weights,
    )
    structure_validation_nll = _model_nll(
        validation,
        register,
        tonal,
        structure_features,
        structure_weights,
    )
    iteration2_validation_nll = _model_nll(
        validation,
        np.asarray(reference_payload["model"]["register_logits"], dtype=np.float64),
        np.asarray(reference_payload["model"]["tonal_logits"], dtype=np.float64),
        reference_features,
        reference_weights,
    )
    result = {
        "experiment": {
            "id": "F-K3-V8-JOINT-PSEUDOLIKELIHOOD",
            "status": "JOINT_PSEUDOLIKELIHOOD_CANDIDATE",
            "test_loaded": False,
            "historical_rules_loaded": False,
            "expert_constraints_loaded": False,
            "source_structure_model": str(args.structure_model.resolve()),
            "generative_reference": str(args.generative_reference.resolve()),
            "residual_source": str(args.residual.resolve()),
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
            "candidate_count": train.candidate_pitches.size,
            "base_factor_count": base_count,
            "residual_factor_count": residual_count,
            "factor_count": len(features),
            "optimizer": "adam_with_proximal_l1",
            "objective": "regularized_conditional_pseudolikelihood",
            "initialization": "v6_pseudolikelihood_weights_plus_zero_residuals",
            "frozen_weights": 0,
            "maximum_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
            "l2": args.l2,
        },
        "corpus": {
            "manifest_summary": manifest["summary"],
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
            "candidate_min": train.candidate_min,
            "candidate_max": train.candidate_max,
        },
        "comparison": {
            "tonal_baseline_validation_nll": baseline_validation,
            "v6_structure_train_nll": structure_train_nll,
            "v6_structure_validation_nll": structure_validation_nll,
            "iteration2_validation_nll": iteration2_validation_nll,
            "gain_vs_v6_structure": structure_validation_nll - validation_nll,
        },
        "model": {
            "register_logits": register.tolist(),
            "tonal_logits": tonal.tolist(),
            "train_nll": train_nll,
            "validation_nll": validation_nll,
            "active_weights_at_005": int((np.abs(weights) >= 0.05).sum()),
            "rules": [
                {
                    "feature": record["feature"].to_dict(),
                    "weight": float(weight),
                    "origin": record["origin"],
                    "family": record["family"],
                    "description": record["description"],
                    "selection": record["selection"],
                }
                for record, weight in zip(records, weights, strict=True)
            ],
            "fit": diagnostics,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[joint-pl] validation {structure_validation_nll:.6f} -> "
        f"{validation_nll:.6f}",
        flush=True,
    )
    print(f"[joint-pl] wrote {args.output}", flush=True)
    print(f"[joint-pl] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
