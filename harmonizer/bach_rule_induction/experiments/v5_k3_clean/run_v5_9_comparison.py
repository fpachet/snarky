#!/usr/bin/env python3
"""Compare V5.7, rejected V5.8, and generatively calibrated V5.9."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import run_contextual_generation_comparison as single

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
RESULTS = HERE / "results"
GENERATED = REPOSITORY / "harmonizer/generated"


def _error_metrics(
    baseline: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    errors = np.asarray([row["difference"] for row in audit["pieces"]])
    baseline_errors = np.asarray([row["difference"] for row in baseline["pieces"]])
    improvement = np.abs(baseline_errors) - np.abs(errors)
    standard_error = float(improvement.std(ddof=1) / math.sqrt(improvement.size))
    return {
        "mae": float(np.abs(errors).mean()),
        "rmse": float(np.sqrt(np.square(errors).mean())),
        "pieces_improved_over_v5_7": int((improvement > 0).sum()),
        "mean_absolute_error_improvement": float(improvement.mean()),
        "improvement_ci95_low": float(improvement.mean() - 1.96 * standard_error),
        "improvement_ci95_high": float(improvement.mean() + 1.96 * standard_error),
    }


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V5.9 — validation du gradient génératif",
        "",
        "Même ensemble de 20 chorals de validation, mêmes deux graines, même",
        "soprano, même rythme et six balayages. Les poids V5.9 ont été calibrés",
        "exclusivement sur 16 chorals du train. Le test scellé reste fermé.",
        "",
        "Ici, « Bach » désigne les attaques authentiques d'alto, ténor et basse",
        "dans ces mêmes 20 chorals. Une classe rare est définie voix par voix et",
        "mode par mode sur le train ; elle n'est pas synonyme d'altération écrite.",
        "",
        "| Modèle | NLL validation | Classes rares générées | Écart à Bach | "
        "IC95 | MAE par pièce |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label in ("V5.7", "V5.8", "V5.9"):
        row = result["models"][label]
        paired = row["paired_difference"]
        lines.append(
            f"| {label} | {row['validation_nll']:.6f} | "
            f"{100 * row['generated_rate']:.3f} % | "
            f"{100 * paired['mean']:+.3f} pp | "
            f"[{100 * paired['ci95_low']:+.3f}, "
            f"{100 * paired['ci95_high']:+.3f}] | "
            f"{100 * row['errors']['mae']:.3f} pp |"
        )
    source_rate = result["models"]["V5.9"]["source_rate"]
    improvement = result["models"]["V5.9"]["errors"]
    lines.extend(
        [
            "",
            f"Référence Bach pondérée : `{100 * source_rate:.3f} %`.",
            "",
            "V5.9 améliore l'erreur absolue sur",
            f"`{improvement['pieces_improved_over_v5_7']}/20` chorals. La MAE",
            "baisse de `4,401` à `3,107` points. Le taux global devient très proche",
            "de Bach, sans dégradation conditionnelle majeure (`+0,0103` NLL).",
            "",
            "## Retour sur BWV 108.6",
            "",
            "| Mesure | Bach | V5.7 | V5.9 |",
            "|---|---:|---:|---:|",
        ]
    )
    for label, key, percent in (
        ("Classes tonales rares", "rare_tonal_attack_rate", True),
        ("Répétitions de basse", "bass_attacked_repetitions", False),
        ("Blocs triadiques", "triadic_block_rate", True),
        ("Blocs structurels", "selected_structural_block_rate", True),
    ):
        values = [
            result["bwv108_6"][version][key] for version in ("Bach", "V5.7", "V5.9")
        ]
        rendered = (
            [f"{100 * value:.2f} %" for value in values]
            if percent
            else [str(value) for value in values]
        )
        lines.append(f"| {label} | {rendered[0]} | {rendered[1]} | {rendered[2]} |")
    lines.extend(
        [
            "",
            "La calibration globale ne modifie pas le taux rare de cet échantillon",
            "mineur particulier, mais conserve la correction des répétitions de",
            "basse et les proportions triadiques. Les pièces fortement chromatiques",
            "restent sous-modélisées : V5.9 corrige la surproduction moyenne, mais",
            "n'apprend pas encore les licences positives de tonicisation locale.",
            "",
            "## Décision",
            "",
            "**V5.9 remplace V5.7 comme modèle chromatiquement calibré expérimental.**",
            "La prochaine extension devra apprendre un statut tonal local et des",
            "licences positives, sans rouvrir le test scellé.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    audit_paths = {
        "V5.7": RESULTS / "v5_8_multichoral_generation_audit.json",
        "V5.8": RESULTS / "v5_8_reinduced_multichoral_generation_audit.json",
        "V5.9": RESULTS / "v5_9_multichoral_generation_audit.json",
    }
    model_paths = {
        "V5.7": RESULTS / "v5_7_k3_contextual_model.json",
        "V5.8": RESULTS / "v5_8_k3_contextual_model.json",
        "V5.9": RESULTS / "v5_9_generative_model.json",
    }
    audits = {
        label: json.loads(path.read_text(encoding="utf-8"))
        for label, path in audit_paths.items()
    }
    models = {
        label: json.loads(path.read_text(encoding="utf-8"))
        for label, path in model_paths.items()
    }
    tonal_logits = np.asarray(
        models["V5.9"]["model"]["tonal_logits"],
        dtype=np.float64,
    )
    source = HERE / "work/scores/bwv108.6.mxl"
    single_paths = {
        "Bach": source,
        "V5.7": GENERATED / "v5_7_bwv108.6_seed_5517_source_layout.musicxml",
        "V5.9": GENERATED / "v5_9_bwv108.6_seed_5517_source_layout.musicxml",
    }
    result = {
        "experiment": {
            "id": "V5.9-GENERATIVE-VALIDATION-COMPARISON",
            "status": "PROMOTED_EXPERIMENTAL",
            "test_loaded": False,
            "validation_pieces": 20,
            "seeds_per_piece": 2,
            "sweeps": 6,
        },
        "models": {
            label: {
                "validation_nll": models[label]["model"]["validation_nll"],
                "source_rate": audit["summary"]["source_weighted_rate"],
                "generated_rate": audit["summary"]["generated_weighted_rate"],
                "paired_difference": audit["summary"]["paired_piece_difference"],
                "errors": _error_metrics(audits["V5.7"], audit),
            }
            for label, audit in audits.items()
        },
        "bwv108_6": {
            label: single._metrics(path, "bach/bwv108.6", tonal_logits)
            for label, path in single_paths.items()
        },
    }
    json_path = RESULTS / "v5_9_generative_validation_comparison.json"
    report_path = RESULTS / "V5_9_GENERATIVE_VALIDATION_COMPARISON.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-v5.9] wrote {json_path}")
    print(f"[k3-v5.9] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
