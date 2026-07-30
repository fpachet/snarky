#!/usr/bin/env python3
"""Aggregate complete V18 reinductions and extract their unanimous core."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODELS = [
    FACTOR_BASE / "v18_explanatory_sparse_model.json",
    *(FACTOR_BASE / f"v18_structure_fold{index}_model.json" for index in range(1, 5)),
]
DEFAULT_OUTPUT = FACTOR_BASE / "v18_structure_stability.json"
DEFAULT_REPORT = FACTOR_BASE / "V18_STRUCTURE_STABILITY.md"


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def _aggregate(models: list[dict[str, Any]]) -> dict[str, Any]:
    occurrence: Counter[str] = Counter()
    records: dict[str, dict[str, Any]] = {}
    weights: defaultdict[str, list[float]] = defaultdict(list)
    model_sets = []
    for model in models:
        keys = set()
        for rule in model["model"]["rules"]:
            key = rule["feature"]["key"]
            keys.add(key)
            occurrence[key] += 1
            records[key] = rule
            weights[key].append(float(rule["weight"]))
        model_sets.append(keys)
    stability = []
    for key, count in sorted(
        occurrence.items(),
        key=lambda item: (-item[1], records[item[0]]["clause"]),
    ):
        values = weights[key]
        sign_stable = all(value > 0 for value in values) or all(
            value < 0 for value in values
        )
        stability.append(
            {
                "feature": records[key]["feature"],
                "family": records[key]["family"],
                "clause": records[key]["clause"],
                "selection_count": count,
                "selection_rate": count / len(models),
                "weights_when_selected": values,
                "minimum_weight": min(values),
                "maximum_weight": max(values),
                "sign_stable_when_selected": sign_stable,
            }
        )
    pairwise = [
        {
            "left": left + 1,
            "right": right + 1,
            "jaccard": _jaccard(model_sets[left], model_sets[right]),
        }
        for left, right in combinations(range(len(models)), 2)
    ]
    unanimous = [
        record
        for record in stability
        if record["selection_count"] == len(models)
        and record["sign_stable_when_selected"]
    ]
    return {
        "model_rule_counts": [len(keys) for keys in model_sets],
        "pairwise_jaccard": pairwise,
        "mean_pairwise_jaccard": (
            sum(row["jaccard"] for row in pairwise) / len(pairwise)
        ),
        "rules_selected_at_least_3": sum(
            row["selection_count"] >= 3 for row in stability
        ),
        "rules_selected_at_least_4": sum(
            row["selection_count"] >= 4 for row in stability
        ),
        "unanimous_core": unanimous,
        "stability": stability,
    }


def _markdown(result: dict[str, Any], title: str) -> str:
    summary = result["summary"]
    lines = [
        f"# {title}",
        "",
        "La procédure complète de génération de colonnes et de sélection à une",
        "erreur standard est répétée sur quatre partitions 24/8 des 32 chorals",
        "de structure. Le modèle original 32/10 constitue la cinquième",
        "réinduction.",
        "",
        "## Résumé",
        "",
        f"- Tailles des cinq bases : `{summary['model_rule_counts']}`.",
        f"- Jaccard moyen entre bases : "
        f"`{summary['mean_pairwise_jaccard']:.3f}`.",
        f"- Règles présentes dans au moins 3/5 bases : "
        f"`{summary['rules_selected_at_least_3']}`.",
        f"- Règles présentes dans au moins 4/5 bases : "
        f"`{summary['rules_selected_at_least_4']}`.",
        f"- Noyau unanime 5/5 : `{len(summary['unanimous_core'])}`.",
        "",
        "## Noyau explicatif unanime",
        "",
        "| Règle | Étendue des poids |",
        "|---|---:|",
    ]
    for rule in summary["unanimous_core"]:
        lines.append(
            f"| {rule['clause']} | "
            f"[{rule['minimum_weight']:+.3f}, "
            f"{rule['maximum_weight']:+.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Tous les prédicats rencontrés",
            "",
            "| Fréquence | Règle | Signe stable lorsqu'elle est sélectionnée |",
            "|---:|---|:---:|",
        ]
    )
    for rule in summary["stability"]:
        lines.append(
            f"| {rule['selection_count']}/5 | {rule['clause']} | "
            f"{'oui' if rule['sign_stable_when_selected'] else 'non'} |"
        )
    lines.extend(
        [
            "",
            "Le noyau 5/5 est retenu pour le réapprentissage complet. Les règles",
            "3/5 ou 4/5 restent des spécialisations candidates, mais ne sont pas",
            "nécessaires pour établir la première base explicative robuste.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        type=Path,
        nargs="+",
        default=DEFAULT_MODELS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--experiment-id",
        default="K3-V18-STRUCTURE-STABILITY-1",
    )
    parser.add_argument(
        "--title",
        default="V18 — stabilité de la découverte des règles",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    models = [json.loads(path.read_text(encoding="utf-8")) for path in args.models]
    summary = _aggregate(models)
    result = {
        "experiment": {
            "id": args.experiment_id,
            "status": "UNANIMOUS_CORE_SELECTED",
            "model_count": len(models),
            "models": [str(path.resolve()) for path in args.models],
            "unanimous_core_threshold": len(models),
            "test_loaded": False,
        },
        "summary": summary,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result, args.title), encoding="utf-8")
    print(
        f"[v18-structure] unanimous={len(summary['unanimous_core'])} "
        f"jaccard={summary['mean_pairwise_jaccard']:.3f}",
        flush=True,
    )
    print(f"[v18-structure] wrote {args.output}", flush=True)
    print(f"[v18-structure] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
