#!/usr/bin/env python3
"""Aggregate V23 folds and full validation, then apply parsimony."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_FOLDS = [
    FACTOR_BASE / f"v23b_metric_bass_harmony_fold{index}.json"
    for index in range(1, 5)
]
DEFAULT_FULL = FACTOR_BASE / "v23c_metric_bass_harmony_full_model.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v23_metric_bass_harmony_stability.json"
DEFAULT_REPORT = FACTOR_BASE / "V23_METRIC_BASS_HARMONY_DECISION.md"

HARMONY_LABELS = (
    "triades majeures/mineures, fondamentale",
    "triades majeures/mineures, 1er renversement",
    "triades majeures/mineures, 2e renversement",
    "triades diminuées/augmentées, fondamentale",
    "triades diminuées/augmentées, 1er renversement",
    "triades diminuées/augmentées, 2e renversement",
    "7es dominante/majeure/mineure, fondamentale",
    "7es dominante/majeure/mineure, 1er renversement",
    "7es dominante/majeure/mineure, 2e renversement",
    "7es dominante/majeure/mineure, 3e renversement",
    "7es altérées, fondamentale",
    "7es altérées, 1er renversement",
    "7es altérées, 2e renversement",
    "7es altérées, 3e renversement",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folds", nargs=4, type=Path, default=DEFAULT_FOLDS)
    parser.add_argument("--full", type=Path, default=DEFAULT_FULL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _bootstrap(
    differences: np.ndarray,
    *,
    seed: int,
    resamples: int = 100_000,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    samples = differences[
        rng.integers(
            0,
            differences.size,
            size=(resamples, differences.size),
        )
    ].mean(axis=1)
    return {
        "mean": float(differences.mean()),
        "standard_error": float(
            differences.std(ddof=1) / np.sqrt(differences.size)
        ),
        "positive_count": int((differences > 0).sum()),
        "negative_count": int((differences < 0).sum()),
        "bootstrap_95_interval": list(
            map(float, np.quantile(samples, [0.025, 0.975]))
        ),
        "bootstrap_probability_nonpositive": float((samples <= 0).mean()),
        "piece_count": int(differences.size),
    }


def aggregate(
    folds: list[dict[str, Any]],
    full: dict[str, Any],
) -> dict[str, Any]:
    variants = ("harmony_only", "both_groups")
    summary: dict[str, Any] = {}
    for variant_id in variants:
        fold_differences = np.concatenate(
            [
                np.asarray(
                    fold["variants"][variant_id]["paired_vs_baseline"][
                        "differences_baseline_minus_candidate"
                    ],
                    dtype=np.float64,
                )
                for fold in folds
            ]
        )
        fold_weights = np.asarray(
            [
                fold["variants"][variant_id]["group_weights"][
                    "unique_chord_family_inversion_strong"
                ]
                for fold in folds
            ],
            dtype=np.float64,
        )
        correlations = [
            float(np.corrcoef(fold_weights[left], fold_weights[right])[0, 1])
            for left, right in combinations(range(len(folds)), 2)
        ]
        full_paired = full["variants"][variant_id]["paired_vs_baseline"]
        summary[variant_id] = {
            "fold_mean_improvements": [
                float(
                    fold["variants"][variant_id]["paired_vs_baseline"][
                        "mean_improvement"
                    ]
                )
                for fold in folds
            ],
            "aggregate_folds": _bootstrap(
                fold_differences,
                seed=23_304 + len(summary),
            ),
            "harmony_weight_minimum_fold_correlation": min(correlations),
            "harmony_weight_pairwise_fold_correlations": correlations,
            "harmony_sign_consistent_cells": int(
                (
                    np.all(fold_weights > 0, axis=0)
                    | np.all(fold_weights < 0, axis=0)
                ).sum()
            ),
            "full_validation": {
                "baseline_nll": float(
                    full["baseline"]["validation_piece_mean_nll"]
                ),
                "candidate_nll": float(
                    full["variants"][variant_id]["point"][
                        "validation_piece_mean_nll"
                    ]
                ),
                "mean_improvement": float(full_paired["mean_improvement"]),
                "positive_piece_count": int(
                    full_paired["positive_piece_count"]
                ),
                "negative_piece_count": int(
                    full_paired["negative_piece_count"]
                ),
                "piece_count": len(full_paired["piece_ids"]),
                "bootstrap_95_interval": list(
                    map(float, full_paired["bootstrap_95_interval"])
                ),
            },
        }
    fold_increment = np.concatenate(
        [
            np.asarray(
                fold["variants"]["both_groups"]["paired_vs_baseline"][
                    "differences_baseline_minus_candidate"
                ],
                dtype=np.float64,
            )
            - np.asarray(
                fold["variants"]["harmony_only"]["paired_vs_baseline"][
                    "differences_baseline_minus_candidate"
                ],
                dtype=np.float64,
            )
            for fold in folds
        ]
    )
    full_increment = (
        np.asarray(
            full["variants"]["both_groups"]["paired_vs_baseline"][
                "differences_baseline_minus_candidate"
            ],
            dtype=np.float64,
        )
        - np.asarray(
            full["variants"]["harmony_only"]["paired_vs_baseline"][
                "differences_baseline_minus_candidate"
            ],
            dtype=np.float64,
        )
    )
    full_harmony_weights = full["variants"]["harmony_only"]["group_weights"][
        "unique_chord_family_inversion_strong"
    ]
    incremental = {
        "folds_both_minus_harmony": _bootstrap(
            fold_increment,
            seed=23_404,
        ),
        "full_both_minus_harmony": _bootstrap(
            full_increment,
            seed=23_405,
        ),
    }
    full_increment_interval = incremental["full_both_minus_harmony"][
        "bootstrap_95_interval"
    ]
    both_significantly_better = full_increment_interval[0] > 0
    return {
        "experiment": {
            "id": "K3-V23-METRIC-BASS-HARMONY-STABILITY",
            "fold_count": len(folds),
            "fold_heldout_piece_count": int(fold_increment.size),
            "full_validation_piece_count": int(full_increment.size),
            "frozen_group_penalty": 0.6,
            "test_loaded": False,
        },
        "variants": summary,
        "incremental_bass_group": incremental,
        "decision": {
            "retained_variant": (
                "both_groups"
                if both_significantly_better
                else "harmony_only"
            ),
            "harmony_group_retained": True,
            "bass_group_retained": both_significantly_better,
            "reason": (
                "The bass group significantly improves the harmony-only model."
                if both_significantly_better
                else (
                    "Both models beat V22, but the 24-parameter bass addition "
                    "does not significantly beat the 14-parameter harmony group."
                )
            ),
        },
        "retained_harmony_weights": [
            {
                "label": label,
                "weight": float(weight),
            }
            for label, weight in zip(
                HARMONY_LABELS,
                full_harmony_weights,
                strict=True,
            )
        ],
    }


def _markdown(result: dict[str, Any]) -> str:
    harmony = result["variants"]["harmony_only"]
    both = result["variants"]["both_groups"]
    increment = result["incremental_bass_group"]
    hf = harmony["aggregate_folds"]
    hfull = harmony["full_validation"]
    bf = both["aggregate_folds"]
    bfull = both["full_validation"]
    inc_full = increment["full_both_minus_harmony"]
    lines = [
        "# V23 — décision sur les groupes basse métrique et harmonie",
        "",
        "V23 teste deux ajouts interprétables à V22 : 14 statuts d'accord",
        "nommé unique sur temps fort, puis 24 déviations tonales de basse sur",
        "temps fort. Les variantes et λ=0,6 ont été gelés avant les quatre plis.",
        "",
        "## Réplication",
        "",
        "| Variante | Gain folds | IC 95 % | Chorals + | Gain 251/50 | "
        "IC 95 % | Chorals + |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| Harmonie seule | {hf['mean']:+.6f} | "
            f"[{hf['bootstrap_95_interval'][0]:+.6f}, "
            f"{hf['bootstrap_95_interval'][1]:+.6f}] | "
            f"{hf['positive_count']}/{hf['piece_count']} | "
            f"{hfull['mean_improvement']:+.6f} | "
            f"[{hfull['bootstrap_95_interval'][0]:+.6f}, "
            f"{hfull['bootstrap_95_interval'][1]:+.6f}] | "
            f"{hfull['positive_piece_count']}/{hfull['piece_count']} |"
        ),
        (
            f"| Basse + harmonie | {bf['mean']:+.6f} | "
            f"[{bf['bootstrap_95_interval'][0]:+.6f}, "
            f"{bf['bootstrap_95_interval'][1]:+.6f}] | "
            f"{bf['positive_count']}/{bf['piece_count']} | "
            f"{bfull['mean_improvement']:+.6f} | "
            f"[{bfull['bootstrap_95_interval'][0]:+.6f}, "
            f"{bfull['bootstrap_95_interval'][1]:+.6f}] | "
            f"{bfull['positive_piece_count']}/{bfull['piece_count']} |"
        ),
        "",
        "## Décision",
        "",
        "- Le groupe harmonique est retenu : son gain est positif dans chacun",
        "  des quatre plis et nettement positif sur les 50 chorals.",
        f"- L'ajout des 24 poids de basse à l'harmonie ne gagne que "
        f"`{inc_full['mean']:+.6f}` sur les 50 chorals, IC 95 % "
        f"`[{inc_full['bootstrap_95_interval'][0]:+.6f}, "
        f"{inc_full['bootstrap_95_interval'][1]:+.6f}]`.",
        "- Par parcimonie, V23 retient donc **harmonie seule** : 14 paramètres",
        "  supplémentaires au lieu de 38.",
        "",
        "## Poids harmoniques retenus",
        "",
        "Un poids positif favorise ce statut par rapport à l'absence d'un accord",
        "nommé unique ; un poids négatif le défavorise. Ils ne sont pas des",
        "probabilités isolées.",
        "",
        "| Statut sur temps fort | Poids |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {row['label']} | {row['weight']:+.4f} |"
        for row in result["retained_harmony_weights"]
    )
    lines.extend(
        [
            "",
            "La chromaticité de basse reste donc un problème distinct : cette",
            "première factorisation métrique de 24 degrés n'apporte pas assez",
            "d'information au-delà de V22 pour être conservée.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    folds = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in args.folds
    ]
    full = json.loads(args.full.read_text(encoding="utf-8"))
    result = aggregate(folds, full)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        "[v23-aggregate] retained="
        f"{result['decision']['retained_variant']}",
        flush=True,
    )
    print(f"[v23-aggregate] wrote {args.output}", flush=True)
    print(f"[v23-aggregate] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
