#!/usr/bin/env python3
"""Compare Bach and V5.5–V5.7 generations on the same rhythmic skeleton."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
GENERATED = REPOSITORY / "harmonizer/generated"


def _bass_signature(block: np.ndarray) -> int:
    bass = int(block[3])
    result = 0
    for pitch in block:
        result |= 1 << ((int(pitch) - bass) % 12)
    return result


def _analyzed_key(path: Path) -> str:
    from music21 import converter

    return str(converter.parse(path).analyze("key"))


def _metrics(
    path: Path,
    piece_id: str,
    tonal_logits: np.ndarray,
) -> dict[str, Any]:
    lattice = k3.extract_piece_lattice(path, piece_id)
    repetitions = {}
    repetition_rates = {}
    for voice, name in enumerate(k3.VOICE_NAMES):
        opportunities = lattice.attacks[1:, voice]
        repeated = opportunities & (
            lattice.blocks[1:, voice] == lattice.blocks[:-1, voice]
        )
        repetitions[name] = int(repeated.sum())
        repetition_rates[name] = float(repeated.sum() / opportunities.sum())
    signatures = np.asarray(
        [_bass_signature(block) for block in lattice.blocks],
        dtype=np.int16,
    )
    distinct_counts = np.asarray(
        [len({int(pitch) % 12 for pitch in block}) for block in lattice.blocks]
    )
    tonal_surprises = []
    rare = []
    for time in range(lattice.size):
        for voice in range(4):
            if not lattice.attacks[time, voice]:
                continue
            relative = (int(lattice.blocks[time, voice]) - lattice.tonic_pc) % 12
            log_probability = tonal_logits[voice, lattice.mode, relative]
            tonal_surprises.append(-log_probability)
            rare.append(math.exp(log_probability) < 0.02)
    return {
        "analyzed_key": _analyzed_key(path),
        "attacked_repetitions": repetitions,
        "attacked_repetition_rates": repetition_rates,
        "lower_voice_attacked_repetitions": sum(
            repetitions[name] for name in k3.VOICE_NAMES[1:]
        ),
        "bass_attacked_repetitions": repetitions["Bass"],
        "triadic_block_rate": float(
            np.isin(signatures, np.asarray([145, 137, 265])).mean()
        ),
        "selected_structural_block_rate": float(
            np.isin(signatures, np.asarray([145, 137, 265, 329])).mean()
        ),
        "two_class_block_rate": float((distinct_counts == 2).mean()),
        "tonal_surprise": float(np.mean(tonal_surprises)),
        "rare_tonal_attack_rate": float(np.mean(rare)),
    }


def _markdown(result: dict[str, Any]) -> str:
    rows = result["rows"]
    lines = [
        "# V5.7 — boucle générative avant/après",
        "",
        "Même soprano, même squelette rythmique, même graine `5517` et `12`",
        "balayages Gibbs. Les 51 chorals de test restent fermés.",
        "",
        "| Version | Tonalité analysée | Répétitions basse | Répétitions voix "
        "inférieures | Attaques tonales rares | Blocs triadiques | "
        "Blocs structurels | Blocs à 2 classes |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ("Bach", "V5.5", "V5.6", "V5.7"):
        row = rows[label]
        lines.append(
            f"| {label} | {row['analyzed_key']} | "
            f"{row['bass_attacked_repetitions']} | "
            f"{row['lower_voice_attacked_repetitions']} | "
            f"{100 * row['rare_tonal_attack_rate']:.2f} % | "
            f"{100 * row['triadic_block_rate']:.2f} % | "
            f"{100 * row['selected_structural_block_rate']:.2f} % | "
            f"{100 * row['two_class_block_rate']:.2f} % |"
        )
    models = result["models"]
    lines.extend(
        [
            "",
            "## Pouvoir prédictif tenu à part",
            "",
            "| Modèle | Règles | NLL validation |",
            "|---|---:|---:|",
        ]
    )
    for label in ("V5.5", "V5.6", "V5.7"):
        model = models[label]
        lines.append(
            f"| {label} | {model['rule_count']} | {model['validation_nll']:.6f} |"
        )
    repeat = result["bass_repeat_rule"]
    lines.extend(
        [
            "",
            "## Lacune ciblée",
            "",
            "La répétition attaquée générale n'entrait pas dans le budget V5.6.",
            "Après séparation par voix, la clause numérique",
            f"`{repeat['label']}` est sélectionnée au rang `{repeat['rank']}` :",
            "",
            f"- z de sélection : `{repeat['z_score']:+.3f}` ;",
            f"- poids appris : `{repeat['weight']:+.6f}` ;",
            f"- facteur d'odds isolé : `{math.exp(repeat['weight']):.3f}`.",
            "",
            "## Lecture",
            "",
            "- V5.6 corrige principalement la tonalité et les sonorités verticales.",
            "- V5.7 conserve cette amélioration et réduit fortement les répétitions",
            "  de basse sans les interdire.",
            "- Les taux génératifs portent sur un seul choral du train et ne",
            "  remplacent pas une campagne multi-pièces tenue à part.",
            "- Les exports canoniques sont produits par MuSES ; music21 n'est utilisé",
            "  que pour importer le corpus MXL et conserver une vue de sa notation.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bach",
        type=Path,
        default=HERE / "work/scores/bwv108.6.mxl",
    )
    parser.add_argument(
        "--v55",
        type=Path,
        default=GENERATED / "v5_5_bwv108.6_seed_5517_source_layout.musicxml",
    )
    parser.add_argument(
        "--v56",
        type=Path,
        default=GENERATED / "v5_6_bwv108.6_seed_5517_source_layout.musicxml",
    )
    parser.add_argument(
        "--v57",
        type=Path,
        default=GENERATED / "v5_7_bwv108.6_seed_5517_source_layout.musicxml",
    )
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_paths = {
        "V5.5": HERE / "results/v5_1_k3_compact_model.json",
        "V5.6": HERE / "results/v5_6_k3_contextual_model.json",
        "V5.7": HERE / "results/v5_7_k3_contextual_model.json",
    }
    payloads = {
        label: json.loads(path.read_text(encoding="utf-8"))
        for label, path in model_paths.items()
    }
    tonal_logits = np.asarray(
        payloads["V5.7"]["model"]["tonal_logits"],
        dtype=np.float64,
    )
    paths = {
        "Bach": args.bach,
        "V5.5": args.v55,
        "V5.6": args.v56,
        "V5.7": args.v57,
    }
    rows = {
        label: _metrics(path, args.piece_id, tonal_logits)
        for label, path in paths.items()
    }
    models = {
        label: {
            "rule_count": len(payload["model"]["rules"]),
            "validation_nll": float(payload["model"]["validation_nll"]),
        }
        for label, payload in payloads.items()
    }
    repeat_index, repeat_rule = next(
        (index, rule)
        for index, rule in enumerate(
            payloads["V5.7"]["model"]["rules"],
            start=1,
        )
        if rule["feature"]["kind"] == "attacked_repeat_from_previous"
        and rule["feature"]["target_voice"] == 3
    )
    result = {
        "experiment": {
            "id": "V5.7-K3-CONTEXTUAL-GENERATION-COMPARISON",
            "test_loaded": False,
            "piece_id": args.piece_id,
            "seed": 5517,
            "sweeps": 12,
        },
        "rows": rows,
        "models": models,
        "bass_repeat_rule": {
            "rank": repeat_index,
            "label": repeat_rule["feature"]["label"],
            "z_score": repeat_rule["selection"]["z_score"],
            "weight": repeat_rule["weight"],
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_7_contextual_generation_comparison.json"
    report_path = args.output_dir / "V5_7_CONTEXTUAL_GENERATION_COMPARISON.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-comparison] wrote {json_path}")
    print(f"[k3-comparison] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
