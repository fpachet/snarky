#!/usr/bin/env python3
"""Audit the causal effect of the V32 attacked-note sequence factors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_v31_two_note_cycles as cycle_audit
import k3
import numpy as np
from run_explicit_generation_audit import _metrics

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_V29 = FACTOR_BASE / "two_loop_full_generation_v29.json"
DEFAULT_V32 = FACTOR_BASE / "two_loop_full_generation_v32.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v32_generation_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V32_GENERATION_AUDIT.md"
METRICS = (
    "triadic_block_rate",
    "strong_nontriadic_rate",
    "strong_pair_dissonances_per_block",
    "weak_pair_dissonances_per_block",
    "bass_semitone_rate",
    "bass_repeat_rate",
    "bass_large_leap_rate",
    "bass_outside_natural_scale_rate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--v29", type=Path, default=DEFAULT_V29)
    parser.add_argument("--v32", type=Path, default=DEFAULT_V32)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _metric_row(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
) -> dict[str, float]:
    values = _metrics(blocks, lattice)
    return {metric: float(values[metric]) for metric in METRICS}


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V32 — audit causal de la génération",
        "",
        "Même BWV 108.6, même soprano, même rythme, même socle V29 et même",
        "ordre de recherche. La seule différence est l'ajout des deux facteurs",
        "séquentiels V32 appris sur le corpus.",
        "",
        "## Cycles de deux notes attaquées",
        "",
        "| Voix | Mesure | Bach | V29 | V32 |",
        "|---|---|---:|---:|---:|",
    ]
    for voice in k3.VOICE_NAMES:
        for label, key, scale in (
            ("Retours ABA", "lag2_return_rate", 100.0),
            ("Continuations ABAB", "continued_cycle_rate", 100.0),
            ("Runs ≥ 4", "runs_ge4", 1.0),
            ("Longueur maximale", "maximum_run_length", 1.0),
        ):
            values = [
                result["cycles"][system][voice][key] * scale
                for system in ("Bach", "V29", "V32")
            ]
            suffix = " %" if scale == 100.0 else ""
            lines.append(
                f"| {voice} | {label} | "
                + " | ".join(f"{value:.3f}{suffix}" for value in values)
                + " |"
            )
    lines.extend(
        [
            "",
            "## Harmonie et basse",
            "",
            "| Mesure | Bach | V29 | V32 |",
            "|---|---:|---:|---:|",
        ]
    )
    labels = (
        ("Blocs triadiques", "triadic_block_rate", 100.0),
        ("Blocs forts non triadiques", "strong_nontriadic_rate", 100.0),
        ("Dissonances par bloc fort", "strong_pair_dissonances_per_block", 1.0),
        ("Dissonances par bloc faible", "weak_pair_dissonances_per_block", 1.0),
        ("Mouvements chromatiques de basse", "bass_semitone_rate", 100.0),
        ("Grands sauts de basse", "bass_large_leap_rate", 100.0),
        ("Basse hors gamme naturelle", "bass_outside_natural_scale_rate", 100.0),
    )
    for label, key, scale in labels:
        suffix = " %" if scale == 100.0 else ""
        values = [
            result["metrics"][system][key] * scale
            for system in ("Bach", "V29", "V32")
        ]
        lines.append(
            f"| {label} | "
            + " | ".join(f"{value:.3f}{suffix}" for value in values)
            + " |"
        )
    lines.extend(
        [
            "",
            f"V32 modifie `{result['difference']['changed_blocks']}` blocs et "
            f"`{result['difference']['changed_lower_attacks']}` attaques des "
            "voix inférieures par rapport à V29.",
            "",
            "Cet audit mesure l'effet génératif ; il ne sert pas à réajuster",
            "les poids V32.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    payloads = {
        "V29": json.loads(args.v29.read_text(encoding="utf-8")),
        "V32": json.loads(args.v32.read_text(encoding="utf-8")),
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
    changed_lower_attacks = int(
        (
            (blocks["V29"][:, 1:] != blocks["V32"][:, 1:])
            & lattice.attacks[:, 1:]
        ).sum()
    )
    result = {
        "experiment": {
            "id": "K3-V32-FULL-GENERATION-AUDIT-1",
            "status": "POST_FIT_CAUSAL_AUDIT",
            "piece_id": args.piece_id,
            "same_soprano": all(
                np.array_equal(value[:, 0], lattice.blocks[:, 0])
                for value in blocks.values()
            ),
            "generated_piece_used_for_weight_learning": False,
            "test_split_used_for_generation": False,
        },
        "cycles": {
            system: cycle_audit._profile(value, lattice.attacks)
            for system, value in blocks.items()
        },
        "metrics": {
            system: _metric_row(value, lattice)
            for system, value in blocks.items()
        },
        "difference": {
            "changed_blocks": int(
                np.any(blocks["V29"] != blocks["V32"], axis=1).sum()
            ),
            "changed_lower_attacks": changed_lower_attacks,
        },
        "search": payloads["V32"]["search"],
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    bass = result["cycles"]
    print(
        "[v32-audit] bass continued="
        f"{bass['V29']['Bass']['continued_cycle_rate']:.4f}->"
        f"{bass['V32']['Bass']['continued_cycle_rate']:.4f} "
        "strong_nontriadic="
        f"{result['metrics']['V29']['strong_nontriadic_rate']:.4f}->"
        f"{result['metrics']['V32']['strong_nontriadic_rate']:.4f}",
        flush=True,
    )
    print(f"[v32-audit] wrote {args.output}", flush=True)
    print(f"[v32-audit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
