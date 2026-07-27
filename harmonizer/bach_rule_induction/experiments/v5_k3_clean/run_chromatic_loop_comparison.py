#!/usr/bin/env python3
"""Summarize the V5.8 chromatic loop and its generative rejection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _percentage(value: float) -> str:
    return f"{100 * value:.3f} %"


def _markdown(result: dict[str, Any]) -> str:
    conditional = result["conditional_validation"]
    v57 = result["generation"]["V5.7"]
    v58 = result["generation"]["V5.8"]
    lines = [
        "# V5.8 — boucle chromatique et critère de rejet",
        "",
        "## Question",
        "",
        "L'excès visuel de notes chromatiques dans BWV 108.6 vient-il d'une",
        "préférence conditionnelle erronée, d'une lacune de représentation locale",
        "ou de la dynamique de génération Gibbs ?",
        "",
        "## 1. Choix locaux authentiques",
        "",
        "Sur les 50 chorals de validation, V5.7 prévoit moins de classes rares",
        "que Bach :",
        "",
        f"- Bach observé : `{_percentage(conditional['observed_rate'])}` ;",
        f"- V5.7 attendu : `{_percentage(conditional['expected_rate'])}` ;",
        f"- z du résidu : `{conditional['z_score']:+.2f}`.",
        "",
        "Une interdiction chromatique globale est donc exclue. Parmi les choix",
        "rares authentiques, 82 % sont approchés par pas, 56 % ont une résolution",
        "immédiate par pas, 21 % sont des broderies et 25 % des passages.",
        "",
        "## 2. Génération multi-chorals",
        "",
        "Même soprano, même rythme, 20 chorals de validation, deux graines et six",
        "balayages. Les taux portent sur alto, ténor et basse.",
        "",
        "| Modèle | NLL validation | Classes rares générées | Écart apparié à Bach |"
        " IC95 |",
        "|---|---:|---:|---:|---:|",
        (
            f"| V5.7 | {v57['validation_nll']:.6f} | "
            f"{_percentage(v57['generated_rate'])} | "
            f"{100 * v57['paired_difference']['mean']:+.3f} pp | "
            f"[{100 * v57['paired_difference']['ci95_low']:+.3f}, "
            f"{100 * v57['paired_difference']['ci95_high']:+.3f}] |"
        ),
        (
            f"| V5.8 | {v58['validation_nll']:.6f} | "
            f"{_percentage(v58['generated_rate'])} | "
            f"{100 * v58['paired_difference']['mean']:+.3f} pp | "
            f"[{100 * v58['paired_difference']['ci95_low']:+.3f}, "
            f"{100 * v58['paired_difference']['ci95_high']:+.3f}] |"
        ),
        "",
        f"Référence Bach pondérée : `{_percentage(v57['source_rate'])}`.",
        "",
        "V5.8 reconstruit d'abord exactement les vingt règles de V5.7, puis ajoute",
        "huit régularités générales. Aucune des 72 interactions chromatiques",
        "candidates n'est sélectionnée. La NLL s'améliore, mais les générations",
        "deviennent significativement trop chromatiques.",
        "",
        "## Décision",
        "",
        "**V5.8 est rejeté comme successeur génératif de V5.7.** Il reste conservé",
        "comme résultat négatif : la pseudo-vraisemblance conditionnelle seule ne",
        "suffit pas à choisir une base de règles destinée à un Gibbs libre.",
        "",
        "## V5.9 proposé : gradient génératif",
        "",
        "Pour chaque règle lisible `r`, ajouter au gradient conditionnel un contraste",
        "de moments :",
        "",
        "`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.",
        "",
        "Une feature trop fréquente dans les générations reçoit ainsi un gradient",
        "négatif, même si elle améliore la prédiction locale. Les statuts de licence",
        "(approche conjointe, passage, broderie, résolution, métrique) peuvent",
        "recevoir simultanément des poids positifs. Le test scellé restera fermé",
        "pendant ce calibrage.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    residual = json.loads(
        (RESULTS / "v5_8_chromatic_residual_audit.json").read_text(encoding="utf-8")
    )
    v57_generation = json.loads(
        (RESULTS / "v5_8_multichoral_generation_audit.json").read_text(encoding="utf-8")
    )
    v58_generation = json.loads(
        (RESULTS / "v5_8_reinduced_multichoral_generation_audit.json").read_text(
            encoding="utf-8"
        )
    )
    v57_model = json.loads(
        (RESULTS / "v5_7_k3_contextual_model.json").read_text(encoding="utf-8")
    )
    v58_model = json.loads(
        (RESULTS / "v5_8_k3_contextual_model.json").read_text(encoding="utf-8")
    )
    overall = residual["validation"]["strata"]["overall"]
    result = {
        "experiment": {
            "id": "V5.8-CHROMATIC-LOOP-COMPARISON",
            "status": "REJECTED_GENERATIVE_SUCCESSOR",
            "test_loaded": False,
        },
        "conditional_validation": overall,
        "generation": {
            "V5.7": {
                "validation_nll": v57_model["model"]["validation_nll"],
                "source_rate": v57_generation["summary"]["source_weighted_rate"],
                "generated_rate": v57_generation["summary"]["generated_weighted_rate"],
                "paired_difference": v57_generation["summary"][
                    "paired_piece_difference"
                ],
            },
            "V5.8": {
                "validation_nll": v58_model["model"]["validation_nll"],
                "source_rate": v58_generation["summary"]["source_weighted_rate"],
                "generated_rate": v58_generation["summary"]["generated_weighted_rate"],
                "paired_difference": v58_generation["summary"][
                    "paired_piece_difference"
                ],
            },
        },
        "v5_8_rule_count": len(v58_model["model"]["rules"]),
        "v5_8_selected_chromatic_rule_count": sum(
            rule["feature"]["kind"].startswith("rare_tonal_")
            for rule in v58_model["model"]["rules"]
        ),
        "next_method": "conditional gradient plus Bach-minus-Gibbs moment contrast",
    }
    json_path = RESULTS / "v5_8_chromatic_loop_comparison.json"
    report_path = RESULTS / "V5_8_CHROMATIC_LOOP_COMPARISON.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-chromatic-loop] wrote {json_path}")
    print(f"[k3-chromatic-loop] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
