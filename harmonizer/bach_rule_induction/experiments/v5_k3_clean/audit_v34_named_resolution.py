#!/usr/bin/env python3
"""Audit named dissonant strong chords and their next-strong resolutions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import v34_harmony

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_SCORE = DEFAULT_SCORES / "bwv108.6.mxl"
DEFAULT_V33 = FACTOR_BASE / "two_loop_full_generation_v33.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v34_named_resolution_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V34_NAMED_RESOLUTION_AUDIT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--v33", type=Path, default=DEFAULT_V33)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "transitions": len(rows),
        "families": dict(sorted(Counter(row["family"] for row in rows).items())),
        "family_resolution": dict(
            sorted(
                Counter(
                    f"{row['family']}__{row['resolution_outcome']}" for row in rows
                ).items()
            )
        ),
        "seventh_resolution": dict(
            sorted(Counter(row["seventh_resolution"] for row in rows).items())
        ),
        "leading_tone_resolution": dict(
            sorted(Counter(row["leading_tone_resolution"] for row in rows).items())
        ),
        "tritone_resolution": dict(
            sorted(Counter(row["tritone_resolution"] for row in rows).items())
        ),
    }


def _aggregate(all_rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
    flattened = [row for piece in all_rows for row in piece]
    profile = _profile(flattened)
    profile["pieces"] = len(all_rows)
    profile["pieces_with_transitions"] = sum(bool(piece) for piece in all_rows)
    return profile


def _rate(counts: dict[str, int], key: str, alternatives: tuple[str, ...]) -> float:
    denominator = sum(counts.get(item, 0) for item in alternatives)
    return 0.0 if denominator == 0 else counts.get(key, 0) / denominator


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# V34 — audit des accords nommés et de leur résolution",
        "",
        "Les états sont calculés directement depuis les notes aux temps",
        "forts. Ils ne sont ni latents ni annotés à la main. Cette grammaire",
        "se distingue de V29/V30 en visant les familles nommées dissonantes",
        "et le prochain temps fort, pas le bloc vertical immédiatement voisin.",
        "",
        "| Corpus | Transitions nommées dissonantes | Pièces touchées |",
        "|---|---:|---:|",
    ]
    for split in ("train251", "validation50", "test51"):
        row = payload["bach_corpus"][split]
        lines.append(
            f"| {split} | {row['transitions']} | "
            f"{row['pieces_with_transitions']} / {row['pieces']} |"
        )
    lines.extend(
        [
            "",
            "## BWV 108.6 apparié",
            "",
            "| Mesure | Bach | V33 |",
            "|---|---:|---:|",
        ]
    )
    for label, field, key, alternatives in (
        (
            "Septièmes résolues vers le bas",
            "seventh_resolution",
            "resolved_down",
            ("resolved_down", "not_resolved_down"),
        ),
        (
            "Sensibles résolues à la tonique",
            "leading_tone_resolution",
            "resolved_to_tonic",
            ("resolved_to_tonic", "not_resolved_to_tonic"),
        ),
        (
            "Tritons résolus par pas contraires",
            "tritone_resolution",
            "resolved_by_contrary_steps",
            ("resolved_by_contrary_steps", "not_resolved_by_contrary_steps"),
        ),
    ):
        values = [
            100 * _rate(payload["paired_bwv108_6"][system][field], key, alternatives)
            for system in ("Bach", "V33")
        ]
        lines.append(f"| {label} | {values[0]:.3f} % | {values[1]:.3f} % |")
    lines.extend(
        [
            "",
            "L'audit est descriptif : il ne sélectionne aucune cellule et",
            "n'ajuste aucun poids.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    split_ids = {
        "train251": sorted(splits["train"], key=generative._stable_order),
        "validation50": list(splits["validation"]),
        "test51": list(splits["test"]),
    }
    corpus = {}
    for split, piece_ids in split_ids.items():
        all_rows = []
        for piece_id in piece_ids:
            lattice = k3.extract_piece_lattice(
                generative._score_path(args.scores, piece_id),
                piece_id,
            )
            all_rows.append(v34_harmony.strong_transition_rows(lattice, lattice.blocks))
        corpus[split] = _aggregate(all_rows)

    reference = k3.extract_piece_lattice(args.score, args.piece_id)
    v33_payload = json.loads(args.v33.read_text(encoding="utf-8"))
    v33_blocks = np.asarray(v33_payload["solution"]["blocks"], dtype=np.int16)
    paired_rows = {
        "Bach": v34_harmony.strong_transition_rows(reference, reference.blocks),
        "V33": v34_harmony.strong_transition_rows(reference, v33_blocks),
    }
    payload = {
        "experiment": {
            "id": "K3-V34-NAMED-RESOLUTION-AUDIT-1",
            "status": "PRE_GRAMMAR_AUDIT",
            "redundant_with_v29_v30": False,
            "weights_fitted": False,
            "generated_piece_used_for_weight_learning": False,
            "test_loaded": True,
        },
        "grammar": {
            "families": list(v34_harmony.DISSONANT_FAMILIES),
            "resolution_outcomes": list(v34_harmony.RESOLUTION_OUTCOMES),
            "separate_voice_leading_observables": [
                "seventh_resolution",
                "leading_tone_resolution",
                "tritone_resolution",
            ],
        },
        "bach_corpus": corpus,
        "paired_bwv108_6": {
            system: {**_profile(rows), "rows": rows}
            for system, rows in paired_rows.items()
        },
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    print(
        "[v34-named-resolution] "
        f"train={corpus['train251']['transitions']} "
        f"Bach108={len(paired_rows['Bach'])} V33={len(paired_rows['V33'])}",
        flush=True,
    )
    print(f"[v34-named-resolution] wrote {args.output}", flush=True)
    print(f"[v34-named-resolution] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
