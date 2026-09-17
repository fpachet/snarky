#!/usr/bin/env python3
"""Audit V18 rule-weight stability across piece-level train folds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import run_exact_factor_reinduction as exact
import run_v18_explanatory_sparse_induction as v18
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v18_explanatory_sparse_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_MODEL = FACTOR_BASE / "v18_explanatory_sparse_model.json"
DEFAULT_CACHE = HERE / "work/k3-exact-catalogue-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v18_explanatory_weight_stability.json"
DEFAULT_REPORT = FACTOR_BASE / "V18_EXPLANATORY_WEIGHT_STABILITY.md"


def _subset(data: dict[str, np.ndarray], pieces: set[str]) -> dict[str, np.ndarray]:
    mask = np.asarray(
        [str(piece) in pieces for piece in data["piece_ids"]],
        dtype=bool,
    )
    return {key: value[mask] for key, value in data.items()}


def _sign(value: float, threshold: float = 0.05) -> int:
    if value > threshold:
        return 1
    if value < -threshold:
        return -1
    return 0


def _summarize_weights(
    rules: list[dict[str, Any]],
    fold_weights: np.ndarray,
) -> list[dict[str, Any]]:
    summaries = []
    for index, rule in enumerate(rules):
        values = fold_weights[:, index]
        signs = [_sign(float(value)) for value in values]
        nonzero_signs = {sign for sign in signs if sign}
        summaries.append(
            {
                "id": rule["id"],
                "clause": rule["clause"],
                "full_weight": float(rule["weight"]),
                "fold_weights": values.tolist(),
                "mean": float(values.mean()),
                "standard_deviation": float(values.std(ddof=1)),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "nonzero_fold_count": int(sum(sign != 0 for sign in signs)),
                "sign_stable": (
                    len(nonzero_signs) == 1
                    and next(iter(nonzero_signs), 0) == _sign(rule["weight"])
                ),
            }
        )
    return summaries


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V18 — stabilité des poids explicatifs",
        "",
        "Les 32 chorals de structure sont divisés en quatre groupes par pièce.",
        "Chaque estimation apprend les mêmes 19 règles sur 24 chorals et mesure",
        "la NLL sur les huit chorals retirés. Ce test porte sur la stabilité des",
        "poids conditionnellement à la structure retenue, pas encore sur la",
        "stabilité de la découverte elle-même.",
        "",
        "## Résumé",
        "",
        f"- Règles testées : `{experiment['rule_count']}`.",
        f"- Signes stables : `{experiment['stable_sign_count']}`.",
        f"- Poids non nuls dans les quatre replis : "
        f"`{experiment['nonzero_all_folds_count']}`.",
        "",
        "| Règle | Poids complet | Moyenne replis | Étendue | Signe stable |",
        "|---|---:|---:|---:|:---:|",
    ]
    for rule in result["rules"]:
        lines.append(
            f"| {rule['clause']} | {rule['full_weight']:+.4f} | "
            f"{rule['mean']:+.4f} | "
            f"[{rule['minimum']:+.4f}, {rule['maximum']:+.4f}] | "
            f"{'oui' if rule['sign_stable'] else 'non'} |"
        )
    lines.extend(
        [
            "",
            "## NLL des chorals retirés",
            "",
            "| Repli | Sans règles | Avec 19 règles | Gain |",
            "|---:|---:|---:|---:|",
        ]
    )
    for fold in result["folds"]:
        lines.append(
            f"| {fold['fold']} | {fold['baseline_holdout_nll']:.6f} | "
            f"{fold['model_holdout_nll']:.6f} | "
            f"{fold['nll_gain']:.6f} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fold-count", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    model = json.loads(args.model.read_text(encoding="utf-8"))
    rules = model["model"]["rules"]
    selected_keys = [rule["feature"]["key"] for rule in rules]
    complexities = np.asarray(
        [rule["feature"]["complexity"] for rule in rules],
        dtype=np.float64,
    )

    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    key_to_index = {
        key: index for index, key in enumerate(metadata["feature_keys"])
    }
    selected_indices = np.asarray(
        [key_to_index[key] for key in selected_keys],
        dtype=np.int64,
    )
    train = v18._split_from_archive(archive, "train", selected_indices)
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    source_register = np.asarray(
        source["model"]["register_logits"],
        dtype=np.float64,
    )
    source_tonal = np.asarray(
        source["model"]["tonal_logits"],
        dtype=np.float64,
    )
    pieces = sorted(map(str, np.unique(train["piece_ids"])))
    folds = [
        set(pieces[offset :: args.fold_count])
        for offset in range(args.fold_count)
    ]
    fold_records = []
    weights = []
    for fold_index, holdout_pieces in enumerate(folds, start=1):
        fit_pieces = set(pieces) - holdout_pieces
        fit_data = _subset(train, fit_pieces)
        holdout_data = _subset(train, holdout_pieces)
        empty_fit = v18._select(fit_data, [])
        empty_holdout = v18._select(holdout_data, [])
        baseline, _ = v18._fit_selected(
            empty_fit,
            empty_holdout,
            candidates,
            exact.Parameters(
                source_register,
                source_tonal,
                np.empty(0, dtype=np.float64),
            ),
            np.empty(0, dtype=np.float64),
            config,
        )
        fitted, _ = v18._fit_selected(
            fit_data,
            holdout_data,
            candidates,
            exact.Parameters(
                source_register,
                source_tonal,
                np.zeros(len(rules), dtype=np.float64),
            ),
            complexities,
            config,
        )
        baseline_nll = exact._nll(
            empty_holdout["chosen"],
            empty_holdout["voices"],
            empty_holdout["modes"],
            empty_holdout["tonics"],
            candidates,
            empty_holdout["factors"],
            baseline,
        )
        model_nll = exact._nll(
            holdout_data["chosen"],
            holdout_data["voices"],
            holdout_data["modes"],
            holdout_data["tonics"],
            candidates,
            holdout_data["factors"],
            fitted,
        )
        weights.append(fitted.factor_weights)
        fold_records.append(
            {
                "fold": fold_index,
                "fit_piece_count": len(fit_pieces),
                "holdout_piece_count": len(holdout_pieces),
                "holdout_pieces": sorted(holdout_pieces),
                "baseline_holdout_nll": baseline_nll,
                "model_holdout_nll": model_nll,
                "nll_gain": baseline_nll - model_nll,
            }
        )
        print(
            f"[v18-stability] fold={fold_index} "
            f"baseline={baseline_nll:.6f} model={model_nll:.6f}",
            flush=True,
        )

    summaries = _summarize_weights(rules, np.asarray(weights))
    result = {
        "experiment": {
            "id": "K3-V18-EXPLANATORY-WEIGHT-STABILITY-1",
            "status": "DEVELOPMENT_WEIGHT_STABILITY",
            "rule_count": len(rules),
            "fold_count": len(folds),
            "fit_pieces_per_fold": len(pieces) - len(folds[0]),
            "test_loaded": False,
            "structure_reselected_per_fold": False,
            "stable_sign_count": sum(
                rule["sign_stable"] for rule in summaries
            ),
            "nonzero_all_folds_count": sum(
                rule["nonzero_fold_count"] == len(folds)
                for rule in summaries
            ),
        },
        "folds": fold_records,
        "rules": summaries,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v18-stability] wrote {args.output}", flush=True)
    print(f"[v18-stability] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
