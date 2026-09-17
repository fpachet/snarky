#!/usr/bin/env python3
"""Audit attacked-note ABA/ABAB cycles in Bach and full Snarky generations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_SCORE = DEFAULT_SCORES / "bwv108.6.mxl"
DEFAULT_V28 = FACTOR_BASE / "two_loop_full_generation_v28.json"
DEFAULT_V29 = FACTOR_BASE / "two_loop_full_generation_v29.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v31_two_note_cycle_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V31_TWO_NOTE_CYCLE_AUDIT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--v28", type=Path, default=DEFAULT_V28)
    parser.add_argument("--v29", type=Path, default=DEFAULT_V29)
    parser.add_argument("--train-pieces", type=int, default=32)
    parser.add_argument("--validation-pieces", type=int, default=50)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _safe_rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _profile(blocks: np.ndarray, attacks: np.ndarray) -> dict[str, Any]:
    voices = {}
    for voice, name in enumerate(k3.VOICE_NAMES):
        pitches = k3.attacked_pitch_sequence(blocks, attacks, voice)
        counts = k3.two_note_cycle_counts(pitches)
        voices[name] = {
            **counts,
            "lag2_return_rate": _safe_rate(
                counts["lag2_returns"],
                counts["lag2_opportunities"],
            ),
            "continued_cycle_rate": _safe_rate(
                counts["continued_cycles"],
                counts["continuation_opportunities"],
            ),
        }
    return voices


def _aggregate(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for name in k3.VOICE_NAMES:
        rows = [profile[name] for profile in profiles]
        totals = {
            key: sum(int(row[key]) for row in rows)
            for key in (
                "attacks",
                "lag2_opportunities",
                "lag2_returns",
                "continuation_opportunities",
                "continued_cycles",
                "runs",
                "runs_ge4",
                "runs_ge5",
            )
        }
        result[name] = {
            **totals,
            "lag2_return_rate": _safe_rate(
                totals["lag2_returns"],
                totals["lag2_opportunities"],
            ),
            "continued_cycle_rate": _safe_rate(
                totals["continued_cycles"],
                totals["continuation_opportunities"],
            ),
            "maximum_run_length": max(
                (int(row["maximum_run_length"]) for row in rows),
                default=0,
            ),
            "pieces_with_run_ge4": sum(int(row["runs_ge4"]) > 0 for row in rows),
            "pieces_with_run_ge5": sum(int(row["runs_ge5"]) > 0 for row in rows),
        }
    return result


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V31 — audit des cycles de deux notes",
        "",
        "Les calculs portent uniquement sur les notes attaquées. Une tenue ne",
        "compte pas comme répétition. `ABA` est un retour à retard 2 ; `ABAB`",
        "et au-delà sont des continuations du même cycle.",
        "",
        "## BWV 108.6 apparié",
        "",
        "| Voix | Mesure | Bach | V28 | V29 |",
        "|---|---|---:|---:|---:|",
    ]
    paired = result["paired_bwv108_6"]
    for voice in k3.VOICE_NAMES:
        for label, key, scale in (
            ("Retours ABA", "lag2_return_rate", 100),
            ("Continuations ABAB", "continued_cycle_rate", 100),
            ("Runs ≥ 4", "runs_ge4", 1),
            ("Longueur maximale", "maximum_run_length", 1),
        ):
            values = [
                paired[system][voice][key] * scale
                for system in ("Bach", "V28", "V29")
            ]
            suffix = " %" if scale == 100 else ""
            lines.append(
                f"| {voice} | {label} | "
                + " | ".join(f"{value:.3f}{suffix}" for value in values)
                + " |"
            )
    lines.extend(
        [
            "",
            "## Corpus Bach réservé",
            "",
            "| Split | Voix | Retours ABA | Continuations ABAB | "
            "Runs ≥ 4 | Max |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for split in ("train32", "validation50"):
        for voice in k3.VOICE_NAMES:
            row = result["bach_corpus"][split][voice]
            lines.append(
                f"| {split} | {voice} | "
                f"{100 * row['lag2_return_rate']:.3f} % | "
                f"{100 * row['continued_cycle_rate']:.3f} % | "
                f"{row['runs_ge4']} | {row['maximum_run_length']} |"
            )
    lines.extend(
        [
            "",
            "Cet audit est descriptif : aucun poids ni seuil n'est ajusté.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    split_ids = {
        "train32": sorted(splits["train"], key=generative._stable_order)[
            : args.train_pieces
        ],
        "validation50": list(splits["validation"])[: args.validation_pieces],
    }
    corpus = {}
    for split, piece_ids in split_ids.items():
        profiles = []
        for piece_id in piece_ids:
            lattice = k3.extract_piece_lattice(
                generative._score_path(args.scores, piece_id),
                piece_id,
            )
            profiles.append(_profile(lattice.blocks, lattice.attacks))
        corpus[split] = _aggregate(profiles)

    reference = k3.extract_piece_lattice(args.score, args.piece_id)
    paired = {"Bach": _profile(reference.blocks, reference.attacks)}
    for label, path in (("V28", args.v28), ("V29", args.v29)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        blocks = np.asarray(payload["solution"]["blocks"], dtype=np.int16)
        if blocks.shape != reference.blocks.shape:
            raise ValueError(f"{label} generation shape disagrees with source")
        paired[label] = _profile(blocks, reference.attacks)

    result = {
        "experiment": {
            "id": "K3-V31-TWO-NOTE-CYCLE-AUDIT-1",
            "status": "PRE_INDUCTION_AUDIT",
            "train_pieces": len(split_ids["train32"]),
            "validation_pieces": len(split_ids["validation50"]),
            "generated_bwv108_6_used_for_weight_learning": False,
            "weights_fitted": False,
            "test_loaded": False,
        },
        "bach_corpus": corpus,
        "paired_bwv108_6": paired,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    bass = paired["V29"]["Bass"]
    print(
        f"[v31-cycle-audit] V29 bass lag2="
        f"{bass['lag2_return_rate']:.4f} continued="
        f"{bass['continued_cycle_rate']:.4f} max={bass['maximum_run_length']}",
        flush=True,
    )
    print(f"[v31-cycle-audit] wrote {args.output}", flush=True)
    print(f"[v31-cycle-audit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
