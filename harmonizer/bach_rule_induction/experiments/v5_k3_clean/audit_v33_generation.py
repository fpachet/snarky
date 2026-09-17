#!/usr/bin/env python3
"""Audit the strict V33 strong-unlicensed constraint ablation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_v31_two_note_cycles as cycle_audit
import audit_v32_generation as v32_audit
import audit_v33_strong_unlicensed as unlicensed_audit
import k3
import numpy as np

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_V29 = FACTOR_BASE / "two_loop_full_generation_v29.json"
DEFAULT_V32 = FACTOR_BASE / "two_loop_full_generation_v32.json"
DEFAULT_V33 = FACTOR_BASE / "two_loop_full_generation_v33.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v33_generation_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V33_GENERATION_AUDIT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--v29", type=Path, default=DEFAULT_V29)
    parser.add_argument("--v32", type=Path, default=DEFAULT_V32)
    parser.add_argument("--v33", type=Path, default=DEFAULT_V33)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# V33 — audit de l'ablation par contraintes fortes",
        "",
        "Même BWV 108.6, même soprano, même rythme, même modèle V29 et mêmes",
        "facteurs séquentiels V32. V33 ajoute seulement deux interdictions",
        "contextuelles : `triad_plus_unlicensed` et `other_unlicensed` sur",
        "les blocs forts.",
        "",
        "## Résultat principal",
        "",
        "| Système | Non licenciés forts | Triadiques | Forts non triadiques | "
        "Dissonances fortes |",
        "|---|---:|---:|---:|---:|",
    ]
    for system in ("Bach", "V29", "V32", "V33"):
        unlicensed = payload["unlicensed"][system]
        metrics = payload["metrics"][system]
        lines.append(
            f"| {system} | {unlicensed['unlicensed_strong_blocks']} / "
            f"{unlicensed['strong_interior_blocks']} | "
            f"{100 * metrics['triadic_block_rate']:.3f} % | "
            f"{100 * metrics['strong_nontriadic_rate']:.3f} % | "
            f"{metrics['strong_pair_dissonances_per_block']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Cycles ABAB",
            "",
            "| Voix | Bach | V29 | V32 | V33 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for voice in k3.VOICE_NAMES[1:]:
        values = [
            100 * payload["cycles"][system][voice]["continued_cycle_rate"]
            for system in ("Bach", "V29", "V32", "V33")
        ]
        lines.append(
            f"| {voice} | " + " | ".join(f"{value:.3f} %" for value in values) + " |"
        )
    search = payload["search"]
    lines.extend(
        [
            "",
            "## Recherche",
            "",
            f"- Nœuds : `{search['explored_nodes']}`.",
            f"- Backtracks : `{search['backtracks']}`.",
            f"- Alternatives retirées directement : "
            f"`{search['prefiltered_alternatives']}`.",
            f"- Rejets par propagation en avant : "
            f"`{search['forward_check_rejections']}`.",
            f"- Score : `{payload['score']['mean']:.6f}` pour un seuil de "
            f"`{payload['threshold']:.6f}`.",
            "",
            "## Statut scientifique",
            "",
            "Cette expérience est une ablation stricte, pas une nouvelle règle",
            "de Bach : le corpus contient lui-même ces deux statuts. Son rôle",
            "est de vérifier si leur suppression explique causalement les",
            "mauvaises sonorités de V32. Une version promouvable devra remplacer",
            "l'interdiction absolue par une enveloppe ou un budget appris.",
            "",
            "## Écoute",
            "",
            "- MusicXML : "
            "`harmonizer/generated/two_loop_full_v33_bwv108_6.musicxml`",
            "- MIDI : `harmonizer/generated/two_loop_full_v33_bwv108_6.mid`",
            "- MP3, piano acoustique : "
            "`harmonizer/generated/two_loop_full_v33_bwv108_6.mp3`",
            "",
            "## Décision",
            "",
            "L'ablation est causalement positive : les cinq statuts visés",
            "disparaissent, les dissonances fortes baissent de `1,077` à",
            "`0,885` par bloc et les blocs forts non triadiques de `57,69 %`",
            "à `50 %`. La propagation à un pas réduit la recherche à 298",
            "nœuds et permet 66 backtracks effectifs.",
            "",
            "Elle n'est toutefois pas promue. Bach contient ces statuts à un",
            "taux global de `10,999 %` dans le train et en contient un dans",
            "BWV 108.6. La prochaine version devra apprendre un budget de",
            "groupe conditionnel à la longueur et laisser Snarky choisir où",
            "dépenser ce budget, tout en maintenant un plancher harmonique",
            "séparé.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    payloads = {
        version: json.loads(path.read_text(encoding="utf-8"))
        for version, path in (
            ("V29", args.v29),
            ("V32", args.v32),
            ("V33", args.v33),
        )
    }
    blocks = {
        "Bach": lattice.blocks,
        **{
            version: np.asarray(payload["solution"]["blocks"], dtype=np.int16)
            for version, payload in payloads.items()
        },
    }
    if any(value.shape != lattice.blocks.shape for value in blocks.values()):
        raise ValueError("Paired generation shapes disagree")
    v33_payload = payloads["V33"]
    result = {
        "experiment": {
            "id": "K3-V33-STRICT-STRONG-UNLICENSED-ABLATION-1",
            "status": "STRICT_ABLATION_NOT_PROMOTED",
            "piece_id": args.piece_id,
            "generated_piece_used_for_constraint_discovery": False,
            "test_split_used_for_generation": False,
        },
        "metrics": {
            system: v32_audit._metric_row(value, lattice)
            for system, value in blocks.items()
        },
        "cycles": {
            system: cycle_audit._profile(value, lattice.attacks)
            for system, value in blocks.items()
        },
        "unlicensed": {
            system: unlicensed_audit._profile(lattice, value)
            for system, value in blocks.items()
        },
        "difference": {
            "changed_blocks_v32_to_v33": int(
                np.any(blocks["V32"] != blocks["V33"], axis=1).sum()
            ),
            "changed_lower_attacks_v32_to_v33": int(
                (
                    (blocks["V32"][:, 1:] != blocks["V33"][:, 1:])
                    & lattice.attacks[:, 1:]
                ).sum()
            ),
        },
        "search": v33_payload["search"],
        "score": v33_payload["solution"]["score"],
        "threshold": v33_payload["model"]["threshold"],
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        "[v33-generation-audit] unlicensed="
        f"{result['unlicensed']['V32']['unlicensed_strong_blocks']}->"
        f"{result['unlicensed']['V33']['unlicensed_strong_blocks']} "
        "strong_nontriadic="
        f"{result['metrics']['V32']['strong_nontriadic_rate']:.4f}->"
        f"{result['metrics']['V33']['strong_nontriadic_rate']:.4f} "
        f"backtracks={result['search']['backtracks']}",
        flush=True,
    )
    print(f"[v33-generation-audit] wrote {args.output}", flush=True)
    print(f"[v33-generation-audit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
