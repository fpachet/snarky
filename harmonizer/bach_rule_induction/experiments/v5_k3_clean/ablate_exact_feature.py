#!/usr/bin/env python3
"""Remove one learned factor without refit and recompute exact NLL."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import run_exact_factor_reinduction as reinduction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--exact-cache", type=Path, required=True)
    parser.add_argument("--feature-key", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    return parser.parse_args()


def _nll(
    archive: Any,
    split: str,
    candidates: np.ndarray,
    register: np.ndarray,
    tonal: np.ndarray,
    factors: np.ndarray,
    weights: np.ndarray,
) -> float:
    return reinduction._nll(
        archive[f"{split}_chosen"],
        archive[f"{split}_voices"],
        archive[f"{split}_modes"],
        archive[f"{split}_tonics"],
        candidates,
        factors,
        reinduction.Parameters(register, tonal, weights),
    )


def main() -> int:
    args = parse_args()
    source = json.loads(args.model.read_text(encoding="utf-8"))
    rules = source["model"]["rules"]
    keys = [rule["feature"]["key"] for rule in rules]
    matches = [index for index, key in enumerate(keys) if key == args.feature_key]
    if len(matches) != 1:
        raise ValueError(f"Expected one matching factor, found {len(matches)}")
    removed_index = matches[0]
    archive = np.load(args.exact_cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != keys:
        raise ValueError("Exact cache and model factor structures differ")
    retained = [index for index in range(len(rules)) if index != removed_index]
    weights = np.asarray(
        [rules[index]["weight"] for index in retained],
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
    train_factors = archive["train_factors"][:, :, retained]
    validation_factors = archive["validation_factors"][:, :, retained]
    train_nll = _nll(
        archive,
        "train",
        candidates,
        register,
        tonal,
        train_factors,
        weights,
    )
    validation_nll = _nll(
        archive,
        "validation",
        candidates,
        register,
        tonal,
        validation_factors,
        weights,
    )
    output = copy.deepcopy(source)
    removed = output["model"]["rules"].pop(removed_index)
    output["experiment"] = {
        **source["experiment"],
        "id": args.experiment_id,
        "status": "EXACT_SINGLE_FACTOR_ABLATION_PENDING_GENERATION_AUDIT",
        "source_model": str(args.model.resolve()),
        "ablation_without_refit": True,
        "test_loaded": False,
    }
    output["model"]["train_nll"] = train_nll
    output["model"]["validation_nll"] = validation_nll
    output["model"]["exact_single_factor_ablation"] = {
        "method": "remove_one_factor_without_refit",
        "removed_index_zero_based": removed_index,
        "removed_rule": removed,
        "source_train_nll": source["model"]["train_nll"],
        "train_nll": train_nll,
        "source_validation_nll": source["model"]["validation_nll"],
        "validation_nll": validation_nll,
        "retained_weights_changed": False,
        "test_loaded": False,
    }
    lines = [
        "# Ablation exacte d'un facteur sans refit",
        "",
        f"- Facteur retiré : `{removed['feature']['label']}`.",
        "- Poids des 29 facteurs restants inchangés.",
        (
            "- NLL validation exacte : "
            f"`{source['model']['validation_nll']:.6f}` → `{validation_nll:.6f}`."
        ),
        "- Test réservé chargé : `false`.",
        "",
        "Ce modèle sert uniquement à attribuer l'effet génératif du facteur.",
        "",
    ]
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"[exact-ablation] validation={validation_nll:.6f}")
    print(f"[exact-ablation] wrote {args.output}")
    print(f"[exact-ablation] wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
