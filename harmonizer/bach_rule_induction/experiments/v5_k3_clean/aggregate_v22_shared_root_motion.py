#!/usr/bin/env python3
"""Aggregate V22 shared-root-motion folds and the full validation fit."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = (
    REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
)
DEFAULT_FOLDS = [
    FACTOR_BASE / f"v22b_shared_root_motion_fold{index}.json"
    for index in range(1, 5)
]
DEFAULT_FULL = FACTOR_BASE / "v22c_shared_root_motion_full_model.json"
DEFAULT_GENERATIVE_AUDIT = (
    FACTOR_BASE / "v22_rulegroup_constraints_validation10x1_sweep6.json"
)
DEFAULT_OUTPUT = FACTOR_BASE / "v22_shared_root_motion_stability.json"
DEFAULT_REPORT = FACTOR_BASE / "V22_SHARED_ROOT_MOTION_DECISION.md"


def _selected_group(model: dict[str, Any]) -> dict[str, Any]:
    index = int(model["selection"]["selected_index"])
    if index == 0:
        raise ValueError("V22 aggregation requires a retained group")
    return model["path"][index]


def _aggregate(
    folds: list[dict[str, Any]],
    full: dict[str, Any],
    generative_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fold_points = [_selected_group(model) for model in folds]
    fold_weights = np.asarray(
        [point["group_weights"] for point in fold_points],
        dtype=np.float64,
    )
    if fold_weights.ndim != 2 or fold_weights.shape[1] != 24:
        raise ValueError("V22 expects four 24-cell group vectors")
    differences = np.concatenate(
        [
            np.asarray(
                point["paired_vs_baseline"][
                    "differences_baseline_minus_candidate"
                ],
                dtype=np.float64,
            )
            for point in fold_points
        ]
    )
    correlations = [
        {
            "left_fold": left + 1,
            "right_fold": right + 1,
            "correlation": float(
                np.corrcoef(fold_weights[left], fold_weights[right])[0, 1]
            ),
        }
        for left, right in combinations(range(len(folds)), 2)
    ]
    sign_consistent = np.all(fold_weights > 0, axis=0) | np.all(
        fold_weights < 0,
        axis=0,
    )
    rng = np.random.default_rng(22_304)
    bootstrap = differences[
        rng.integers(
            0,
            differences.size,
            size=(100_000, differences.size),
        )
    ].mean(axis=1)
    full_point = _selected_group(full)
    result = {
        "fold_count": len(folds),
        "heldout_piece_count": int(differences.size),
        "fold_mean_improvements": [
            float(point["paired_vs_baseline"]["mean_improvement"])
            for point in fold_points
        ],
        "aggregate_heldout_mean_improvement": float(differences.mean()),
        "aggregate_heldout_standard_error": float(
            differences.std(ddof=1) / np.sqrt(differences.size)
        ),
        "aggregate_heldout_positive_piece_count": int(
            (differences > 0).sum()
        ),
        "aggregate_heldout_bootstrap_95_interval": list(
            map(float, np.quantile(bootstrap, [0.025, 0.975]))
        ),
        "fold_weight_correlations": correlations,
        "minimum_fold_weight_correlation": min(
            row["correlation"] for row in correlations
        ),
        "sign_consistent_cell_count": int(sign_consistent.sum()),
        "fold_mean_group_weights": fold_weights.mean(axis=0).tolist(),
        "fold_minimum_group_weights": fold_weights.min(axis=0).tolist(),
        "fold_maximum_group_weights": fold_weights.max(axis=0).tolist(),
        "full_validation_piece_count": int(
            full["experiment"]["validation_piece_count"]
        ),
        "full_validation_baseline_nll": float(
            full["path"][0]["validation_piece_mean_nll"]
        ),
        "full_validation_group_nll": float(
            full_point["validation_piece_mean_nll"]
        ),
        "full_validation_mean_improvement": float(
            full_point["paired_vs_baseline"]["mean_improvement"]
        ),
        "full_validation_positive_piece_count": int(
            full_point["paired_vs_baseline"]["positive_piece_count"]
        ),
        "full_validation_bootstrap_95_interval": list(
            map(
                float,
                full_point["paired_vs_baseline"]["bootstrap_95_interval"],
            )
        ),
        "full_group_weights": list(map(float, full_point["group_weights"])),
    }
    if generative_audit is not None:
        result["generative_ablation"] = {
            label: {
                key: float(generative_audit["summary"][label][key]["mean"])
                for key in (
                    "bass_outside_natural_scale_rate",
                    "triadic_block_rate",
                    "strong_nontriadic_rate",
                    "strong_pair_dissonances_per_block",
                    "weak_pair_dissonances_per_block",
                )
            }
            for label in ("Bach", "Baseline", "V22", "V22+C")
        }
    return result


def _weight_table(weights: list[float]) -> list[str]:
    names = (
        "maintien",
        "2de min. ascendante",
        "2de maj. ascendante",
        "3ce min. ascendante",
        "3ce maj. ascendante",
        "4te ascendante / 5te descendante",
        "triton",
        "5te ascendante / 4te descendante",
        "3ce maj. descendante",
        "3ce min. descendante",
        "2de maj. descendante",
        "2de min. descendante",
    )
    return [
        f"| {name} | {weights[index]:+.3f} | "
        f"{weights[index + 12]:+.3f} |"
        for index, name in enumerate(names)
    ]


def _markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    fold_interval = summary["aggregate_heldout_bootstrap_95_interval"]
    full_interval = summary["full_validation_bootstrap_95_interval"]
    lines = [
        "# V22 — décision sur le groupe partagé des mouvements de fondamentale",
        "",
        "V22 remplace la table libre V21 de 288 coefficients par une seule",
        "règle factorielle structurée : pour chaque mode, le poids dépend",
        "uniquement de la classe dirigée du mouvement de fondamentale. Le",
        "groupe possède donc 24 paramètres (2 modes × 12 mouvements).",
        "",
        "## Résultat scientifique",
        "",
        f"- Quatre folds gelés : gain NLL moyen apparié "
        f"`{summary['aggregate_heldout_mean_improvement']:+.6f}` sur "
        f"`{summary['heldout_piece_count']}` chorals hors apprentissage ; "
        f"`{summary['aggregate_heldout_positive_piece_count']}/"
        f"{summary['heldout_piece_count']}` sont améliorés.",
        f"- IC bootstrap 95 % inter-folds : "
        f"`[{fold_interval[0]:+.6f}, {fold_interval[1]:+.6f}]`.",
        f"- Stabilité : corrélation minimale des poids entre folds "
        f"`{summary['minimum_fold_weight_correlation']:.3f}` ; "
        f"`{summary['sign_consistent_cell_count']}/24` coefficients gardent "
        "le même signe dans les quatre folds.",
        f"- Réapprentissage sur 251 chorals, validation sur 50 : "
        f"`{summary['full_validation_baseline_nll']:.6f}` → "
        f"`{summary['full_validation_group_nll']:.6f}`, soit un gain "
        f"`{summary['full_validation_mean_improvement']:+.6f}` ; "
        f"`{summary['full_validation_positive_piece_count']}/"
        f"{summary['full_validation_piece_count']}` chorals améliorés.",
        f"- IC bootstrap 95 % sur les 50 chorals : "
        f"`[{full_interval[0]:+.6f}, {full_interval[1]:+.6f}]`.",
        "",
        "Le groupe est donc **retenu**. Contrairement à V21, le gain se",
        "réplique dans tous les folds et sur le grand découpage réservé.",
        "Le partage des paramètres est bien la réduction de dimension qui",
        "manquait à l'apprentissage conjoint.",
        "",
        "## Règle apprise, sous forme lisible",
        "",
        "Un poids positif signifie que le mouvement rend le choix local de",
        "Bach plus probable relativement aux autres candidats disponibles ;",
        "un poids négatif le rend moins probable. Les poids sont centrés dans",
        "chaque mode : ils n'ont pas de sens comme probabilités isolées.",
        "",
        "| Mouvement de fondamentale | Majeur | Mineur |",
        "|---|---:|---:|",
        *_weight_table(summary["full_group_weights"]),
        "",
        "Ce tableau est une seule règle structurée, pas 24 interdictions.",
        "Ses contributions s'ajoutent aux autres facteurs avant la",
        "normalisation conditionnelle MaxEnt.",
        "",
        "## Séparation avec les contraintes",
        "",
        "L'audit indépendant des prédicats à fréquence nulle a trouvé 40",
        "lignes sans exception sur 251 + 50 chorals. Après suppression des",
        "orientations symétriques et seuils emboîtés, elles se regroupent en",
        "plusieurs schémas candidats :",
        "",
        "1. absence de croisement soprano–ténor, frontière directionnelle",
        "   alto–basse et espacement soprano–basse supérieur à un demi-ton ;",
        "2. absence de septième majeure mélodique et de saut supérieur à",
        "   l'octave au soprano, alto et ténor ;",
        "3. absence d'arrivée en mouvement direct sur une seconde mineure",
        "   entre alto–ténor et ténor–basse ;",
        "4. absence de seconde mineure ou septième majeure conservée par",
        "   mouvement direct entre deux voix ;",
        "5. absence, beaucoup plus spécifique, d'un accord de septième",
        "   majeure sur le degré chromatique +2.",
        "",
        "Les quatre premiers ensembles sont des candidats à formaliser puis à tester",
        "comme contraintes. Le cinquième doit rester un facteur doux tant",
        "qu'une analyse enharmonique et tonale n'a pas exclu un artefact de",
        "représentation. Les 23 prédicats retenus sont compilés dans Snarky",
        "comme filtres d'ablation pré-test, sans statut `MUST`.",
        "",
        "## Ablation générative",
        "",
    ]
    ablation = summary.get("generative_ablation")
    if ablation is None:
        lines.extend(
            (
                "L'ablation générative n'est pas encore disponible.",
                "",
            )
        )
    else:
        strong = "strong_pair_dissonances_per_block"
        outside = "bass_outside_natural_scale_rate"
        lines.extend(
            (
                "Sur dix chorals de validation, même état initial faisable,",
                "même soprano, rythme et graine :",
                "",
                "| Mesure | Bach | Socle | V22 | V22 + contraintes |",
                "|---|---:|---:|---:|---:|",
                (
                    "| Blocs triadiques | "
                    f"{100 * ablation['Bach']['triadic_block_rate']:.2f} % | "
                    f"{100 * ablation['Baseline']['triadic_block_rate']:.2f} % | "
                    f"{100 * ablation['V22']['triadic_block_rate']:.2f} % | "
                    f"{100 * ablation['V22+C']['triadic_block_rate']:.2f} % |"
                ),
                (
                    "| Dissonances/bloc faible | "
                    f"{ablation['Bach']['weak_pair_dissonances_per_block']:.3f} | "
                    f"{ablation['Baseline']['weak_pair_dissonances_per_block']:.3f} | "
                    f"{ablation['V22']['weak_pair_dissonances_per_block']:.3f} | "
                    f"{ablation['V22+C']['weak_pair_dissonances_per_block']:.3f} |"
                ),
                (
                    "| Dissonances/bloc fort | "
                    f"{ablation['Bach'][strong]:.3f} | "
                    f"{ablation['Baseline'][strong]:.3f} | "
                    f"{ablation['V22'][strong]:.3f} | "
                    f"{ablation['V22+C'][strong]:.3f} |"
                ),
                (
                    "| Basse hors gamme globale | "
                    f"{100 * ablation['Bach'][outside]:.2f} % | "
                    f"{100 * ablation['Baseline'][outside]:.2f} % | "
                    f"{100 * ablation['V22'][outside]:.2f} % | "
                    f"{100 * ablation['V22+C'][outside]:.2f} % |"
                ),
                "",
                "Les contraintes récupèrent une grande partie de la qualité",
                "triadique et des dissonances faibles perdues par V22, mais",
                "elles ne corrigent ni les dissonances fortes ni le",
                "chromatisme de basse. Le prochain groupe doit donc relier",
                "statut tonal de basse, force métrique et qualité d'accord,",
                "sans modifier rétroactivement le groupe V22.",
                "",
            )
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folds", type=Path, nargs="+", default=DEFAULT_FOLDS)
    parser.add_argument("--full", type=Path, default=DEFAULT_FULL)
    parser.add_argument(
        "--generative-audit",
        type=Path,
        default=DEFAULT_GENERATIVE_AUDIT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    folds = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.folds
    ]
    full = json.loads(args.full.read_text(encoding="utf-8"))
    generative_audit = (
        None
        if not args.generative_audit.exists()
        else json.loads(args.generative_audit.read_text(encoding="utf-8"))
    )
    summary = _aggregate(folds, full, generative_audit)
    result = {
        "experiment": {
            "id": "K3-V22-SHARED-ROOT-MOTION-STABILITY-1",
            "status": "GROUP_RETAINED_CONSTRAINTS_NOT_PROMOTED",
            "fold_models": [str(path.resolve()) for path in args.folds],
            "full_model": str(args.full.resolve()),
            "test_loaded": False,
        },
        "summary": summary,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        "[v22] "
        f"fold_gain={summary['aggregate_heldout_mean_improvement']:.6f} "
        f"full_gain={summary['full_validation_mean_improvement']:.6f}",
        flush=True,
    )
    print(f"[v22] wrote {args.output}", flush=True)
    print(f"[v22] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
