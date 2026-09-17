#!/usr/bin/env python3
"""Compare Bach and the paired V28/V29 full Snarky generations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
from run_explicit_generation_audit import _metrics

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_V28 = FACTOR_BASE / "two_loop_full_generation_v28.json"
DEFAULT_V29 = FACTOR_BASE / "two_loop_full_generation_v29.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v29_snarky_generation_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V29_SNARKY_GENERATION_AUDIT.md"
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
    parser.add_argument("--v28", type=Path, default=DEFAULT_V28)
    parser.add_argument("--v29", type=Path, default=DEFAULT_V29)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _row(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
) -> dict[str, float]:
    values = _metrics(blocks, lattice)
    return {metric: values[metric] for metric in METRICS}


def _markdown(result: dict[str, Any]) -> str:
    systems = ("Bach", "V28", "V29")
    lines = [
        "# V29 — audit apparié de la génération Snarky complète",
        "",
        "Même BWV 108.6, même soprano, même rythme et même moteur. Les voix",
        "inférieures de Bach ne sont consultées qu'après la génération.",
        "",
        "| Mesure | Bach | V28 | V29 |",
        "|---|---:|---:|---:|",
    ]
    labels = (
        ("Blocs triadiques", "triadic_block_rate", 100),
        ("Blocs forts non triadiques", "strong_nontriadic_rate", 100),
        ("Dissonances par bloc fort", "strong_pair_dissonances_per_block", 1),
        ("Dissonances par bloc faible", "weak_pair_dissonances_per_block", 1),
        ("Mouvements chromatiques de basse", "bass_semitone_rate", 100),
        ("Grands sauts de basse", "bass_large_leap_rate", 100),
        ("Basse hors gamme naturelle", "bass_outside_natural_scale_rate", 100),
    )
    for label, key, scale in labels:
        suffix = " %" if scale == 100 else ""
        values = [
            f"{result['systems'][system][key] * scale:.3f}{suffix}"
            for system in systems
        ]
        lines.append(f"| {label} | " + " | ".join(values) + " |")
    search = result["search"]
    lines.extend(
        [
            "",
            f"V29 termine en `{search['explored_nodes']}` nœuds, avec "
            f"`{search['backtracks']}` backtracks et "
            f"`{search['prefiltered_alternatives']}` alternatives retirées.",
            "",
            "La pseudo-vraisemblance tenue à part et cet audit génératif sont",
            "des critères distincts : l'un mesure la prédiction locale du",
            "corpus, l'autre le comportement d'une solution complète.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    payloads = {
        "V28": json.loads(args.v28.read_text(encoding="utf-8")),
        "V29": json.loads(args.v29.read_text(encoding="utf-8")),
    }
    blocks = {
        version: np.asarray(payload["solution"]["blocks"], dtype=np.int16)
        for version, payload in payloads.items()
    }
    if any(value.shape != lattice.blocks.shape for value in blocks.values()):
        raise ValueError("Paired generation shapes disagree")
    result = {
        "experiment": {
            "id": "K3-V29-SNARKY-FULL-GENERATION-AUDIT-1",
            "status": "POST_FIT_PAIRED_AUDIT",
            "piece_id": args.piece_id,
            "same_soprano": all(
                np.array_equal(value[:, 0], lattice.blocks[:, 0])
                for value in blocks.values()
            ),
            "generated_bwv108_6_used_for_learning": False,
            "test_loaded": False,
        },
        "systems": {
            "Bach": _row(lattice.blocks, lattice),
            **{version: _row(value, lattice) for version, value in blocks.items()},
        },
        "search": payloads["V29"]["search"],
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v29-audit] strong_nontriadic="
        f"{result['systems']['V28']['strong_nontriadic_rate']:.4f}->"
        f"{result['systems']['V29']['strong_nontriadic_rate']:.4f} "
        f"bass_semitone="
        f"{result['systems']['V28']['bass_semitone_rate']:.4f}->"
        f"{result['systems']['V29']['bass_semitone_rate']:.4f}",
        flush=True,
    )
    print(f"[v29-audit] wrote {args.output}", flush=True)
    print(f"[v29-audit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
