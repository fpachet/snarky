#!/usr/bin/env python3
"""Refit the compact V5.1 K3 model after removing each learned rule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE / "work/k3-train-validation-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_MODEL = HERE / "results/v5_1_k3_compact_model.json"


def _load_data(
    cache_path: Path,
    splits_path: Path,
) -> tuple[k3.K3Dataset, k3.K3Dataset, dict[str, list[str]]]:
    data = k3.load_k3_dataset(cache_path)
    split_payload = json.loads(splits_path.read_text(encoding="utf-8"))
    source = split_payload.get("grouped_split", split_payload)
    splits = {name: list(source[name]) for name in ("train", "validation", "test")}
    train = k3.subset_for_piece_ids(data, splits["train"])
    validation = k3.subset_for_piece_ids(data, splits["validation"])
    minimum, maximum = k3.training_domain(train)
    train, train_removed = k3.filter_to_domain(train, minimum, maximum)
    validation, validation_removed = k3.filter_to_domain(validation, minimum, maximum)
    if train_removed or validation_removed:
        raise ValueError("Ablation domain unexpectedly removed observed choices")
    return train, validation, splits


def remove_column(matrix: np.ndarray, index: int) -> np.ndarray:
    """Return a feature matrix without one declared rule column."""

    if not 0 <= index < matrix.shape[2]:
        raise IndexError(index)
    return np.concatenate((matrix[:, :, :index], matrix[:, :, index + 1 :]), axis=2)


def _nll_with_neutralized_weight(
    dataset: k3.K3Dataset,
    register_logits: np.ndarray,
    matrix: np.ndarray,
    weights: np.ndarray,
    index: int,
) -> float:
    neutralized = weights.copy()
    neutralized[index] = 0.0
    return k3.conditional_nll(dataset, register_logits, matrix, neutralized)


def run_ablation(
    train: k3.K3Dataset,
    validation: k3.K3Dataset,
    model_payload: dict[str, Any],
    *,
    max_steps: int,
    learning_rate: float,
    l1: float,
) -> dict[str, Any]:
    """Fit the full catalogue, then refit after each single-rule removal."""

    rules = model_payload["model"]["rules"]
    features = [k3.feature_from_model_record(rule) for rule in rules]
    register_logits = k3.learn_register_logits(train)
    train_matrix = k3.feature_matrix(train, features)
    validation_matrix = k3.feature_matrix(validation, features)
    full_weights, full_diagnostics = k3.fit_weights(
        train,
        validation,
        register_logits,
        train_matrix,
        validation_matrix,
        l1=l1,
        max_steps=max_steps,
        learning_rate=learning_rate,
    )
    full_train_nll = k3.conditional_nll(
        train, register_logits, train_matrix, full_weights
    )
    full_validation_nll = k3.conditional_nll(
        validation, register_logits, validation_matrix, full_weights
    )
    records = []
    for index, feature in enumerate(features):
        print(
            f"[k3-ablation] {index + 1}/{len(features)} removing {feature.label}",
            flush=True,
        )
        ablated_train = remove_column(train_matrix, index)
        ablated_validation = remove_column(validation_matrix, index)
        ablated_weights, diagnostics = k3.fit_weights(
            train,
            validation,
            register_logits,
            ablated_train,
            ablated_validation,
            l1=l1,
            max_steps=max_steps,
            learning_rate=learning_rate,
        )
        train_nll = k3.conditional_nll(
            train, register_logits, ablated_train, ablated_weights
        )
        validation_nll = k3.conditional_nll(
            validation,
            register_logits,
            ablated_validation,
            ablated_weights,
        )
        neutralized_train_nll = _nll_with_neutralized_weight(
            train, register_logits, train_matrix, full_weights, index
        )
        neutralized_validation_nll = _nll_with_neutralized_weight(
            validation, register_logits, validation_matrix, full_weights, index
        )
        records.append(
            {
                "rule_index": index + 1,
                "feature": feature.to_dict(),
                "full_weight": float(full_weights[index]),
                "neutralized_train_nll_penalty": (
                    neutralized_train_nll - full_train_nll
                ),
                "neutralized_validation_nll_penalty": (
                    neutralized_validation_nll - full_validation_nll
                ),
                "refit_train_nll": train_nll,
                "refit_validation_nll": validation_nll,
                "refit_train_nll_penalty": train_nll - full_train_nll,
                "refit_validation_nll_penalty": (validation_nll - full_validation_nll),
                "remaining_weights": ablated_weights.tolist(),
                "fit": diagnostics,
            }
        )
    return {
        "register_logits": register_logits.tolist(),
        "full_model": {
            "weights": full_weights.tolist(),
            "train_nll": full_train_nll,
            "validation_nll": full_validation_nll,
            "fit": full_diagnostics,
        },
        "ablations": records,
    }


def _markdown(result: dict[str, Any]) -> str:
    model = result["model"]
    full = model["full_model"]
    lines = [
        "# V5.3 — ablation réajustée des règles K3",
        "",
        "## Protocole",
        "",
        "- Les douze règles V5.1 sont réajustées conjointement depuis zéro.",
        "- Chaque règle est d'abord neutralisée à poids fixe.",
        "- Elle est ensuite retirée et les onze autres poids sont réappris.",
        "- Une pénalité NLL positive indique une contribution utile.",
        "- Le test de 51 chorals reste fermé.",
        "",
        "## Modèle complet réajusté",
        "",
        f"- NLL train : `{full['train_nll']:.6f}`.",
        f"- NLL validation : `{full['validation_nll']:.6f}`.",
        "",
        "## Résultats",
        "",
        "| # | Règle numérique | Poids | Neutralisation validation | "
        "Retrait + réajustement validation |",
        "|---:|---|---:|---:|---:|",
    ]
    for record in model["ablations"]:
        lines.append(
            f"| {record['rule_index']} | `{record['feature']['label']}` | "
            f"{record['full_weight']:+.6f} | "
            f"{record['neutralized_validation_nll_penalty']:+.6f} | "
            f"{record['refit_validation_nll_penalty']:+.6f} |"
        )
    positive = [
        record
        for record in model["ablations"]
        if record["refit_validation_nll_penalty"] > 0
    ]
    nonpositive = [
        record
        for record in model["ablations"]
        if record["refit_validation_nll_penalty"] <= 0
    ]
    lines.extend(
        [
            "",
            "## Lecture",
            "",
            (
                f"`{len(positive)}` règles sur `{len(model['ablations'])}` "
                "conservent une pénalité positive après réajustement."
            ),
        ]
    )
    if nonpositive:
        labels = ", ".join(f"`{record['feature']['label']}`" for record in nonpositive)
        lines.append(
            "Règles sans gain propre positif dans cette ablation : " + labels + "."
        )
    lines.extend(
        [
            "",
            "Cette expérience mesure la redondance interne du catalogue fixé. Elle",
            "ne remplace pas la calibration du processus de recherche sur plusieurs",
            "permutations.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    train, validation, splits = _load_data(args.cache, args.splits)
    model_payload = json.loads(args.model.read_text(encoding="utf-8"))
    result = {
        "experiment": {
            "id": "V5.3-K3-REFIT-ABLATION",
            "source_model": str(args.model.resolve()),
            "test_loaded": False,
            "max_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
        },
        "corpus": {
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
        },
        "model": run_ablation(
            train,
            validation,
            model_payload,
            max_steps=args.max_steps,
            learning_rate=args.learning_rate,
            l1=args.l1,
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_3_k3_refit_ablation.json"
    report_path = args.output_dir / "V5_3_K3_REFIT_ABLATION.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-ablation] wrote {json_path}", flush=True)
    print(f"[k3-ablation] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
