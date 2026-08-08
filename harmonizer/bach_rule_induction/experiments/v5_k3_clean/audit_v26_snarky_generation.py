#!/usr/bin/env python3
"""Compare the paired V23 and V26 full Snarky generations with Bach."""

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
DEFAULT_V23 = FACTOR_BASE / "two_loop_full_generation.json"
DEFAULT_V26 = FACTOR_BASE / "two_loop_full_generation_v26.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v26_snarky_generation_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V26_SNARKY_GENERATION_AUDIT.md"

METRICS = (
    "triadic_block_rate",
    "strong_nontriadic_rate",
    "strong_pair_dissonances_per_block",
    "weak_pair_dissonances_per_block",
    "bass_semitone_rate",
    "bass_repeat_rate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--v23", type=Path, default=DEFAULT_V23)
    parser.add_argument("--v26", type=Path, default=DEFAULT_V26)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _joint_metric(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
) -> dict[str, float | int]:
    size = lattice.size - 2
    data = k3.K3Dataset(
        piece_ids=np.full(size, lattice.piece_id),
        offsets=np.stack(
            (
                lattice.offsets[:-2],
                lattice.offsets[1:-1],
                lattice.offsets[2:],
            ),
            axis=1,
        ),
        voice_indices=np.zeros(size, dtype=np.int8),
        blocks=np.stack(
            (blocks[:-2], blocks[1:-1], blocks[2:]),
            axis=1,
        ),
        attacks=np.stack(
            (
                lattice.attacks[:-2],
                lattice.attacks[1:-1],
                lattice.attacks[2:],
            ),
            axis=1,
        ),
        candidate_min=36,
        candidate_max=81,
        tonic_pcs=np.full(size, lattice.tonic_pc, dtype=np.int8),
        modes=np.full(size, lattice.mode, dtype=np.int8),
        metric_levels=lattice.metric_levels[1:-1],
    )
    statuses = k3.central_joint_weak_resolution_statuses(
        data,
        blocks[1:-1, 0, None],
    )[:, 0]
    residual = statuses >= 0
    return {
        "residual_weak_blocks": int(residual.sum()),
        "unacceptable_following_rate": (
            float((statuses[residual] % 2 == 1).mean()) if np.any(residual) else 0.0
        ),
    }


def _row(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
) -> dict[str, Any]:
    metrics = _metrics(blocks, lattice)
    return {
        **{name: metrics[name] for name in METRICS},
        **_joint_metric(blocks, lattice),
    }


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V26 — audit apparié de la génération Snarky complète",
        "",
        "Même BWV 108.6, même soprano, même rythme et même ordre de recherche.",
        "Les voix inférieures de Bach ne sont utilisées que comme référence après",
        "les deux générations.",
        "",
        "| Mesure | Bach | V23 | V26 |",
        "|---|---:|---:|---:|",
    ]
    labels = (
        ("Blocs triadiques", "triadic_block_rate", 100),
        ("Blocs forts non triadiques", "strong_nontriadic_rate", 100),
        (
            "Dissonances par bloc fort",
            "strong_pair_dissonances_per_block",
            1,
        ),
        (
            "Dissonances par bloc faible",
            "weak_pair_dissonances_per_block",
            1,
        ),
        (
            "Faibles résiduels vers résolution inacceptable",
            "unacceptable_following_rate",
            100,
        ),
        ("Mouvements chromatiques de basse", "bass_semitone_rate", 100),
    )
    for label, key, scale in labels:
        values = [
            result["systems"][system][key] * scale for system in ("Bach", "V23", "V26")
        ]
        suffix = " %" if scale == 100 else ""
        lines.append(
            f"| {label} | {values[0]:.3f}{suffix} | "
            f"{values[1]:.3f}{suffix} | {values[2]:.3f}{suffix} |"
        )
    lines.extend(
        [
            "",
            "V26 améliore toutes les mesures harmoniques visées, mais ne ferme",
            "pas l'écart sur les temps forts et ne corrige presque pas la basse.",
            "Ce résultat est un audit post-apprentissage, pas un critère ayant",
            "servi à choisir les poids.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    v23 = np.asarray(
        json.loads(args.v23.read_text(encoding="utf-8"))["solution"]["blocks"],
        dtype=np.int16,
    )
    v26 = np.asarray(
        json.loads(args.v26.read_text(encoding="utf-8"))["solution"]["blocks"],
        dtype=np.int16,
    )
    if v23.shape != lattice.blocks.shape or v26.shape != lattice.blocks.shape:
        raise ValueError("Paired generation shapes disagree")
    result = {
        "experiment": {
            "id": "K3-V26-SNARKY-FULL-GENERATION-AUDIT-1",
            "status": "POST_FIT_PAIRED_AUDIT",
            "piece_id": args.piece_id,
            "same_soprano": bool(
                np.array_equal(v23[:, 0], v26[:, 0])
                and np.array_equal(v26[:, 0], lattice.blocks[:, 0])
            ),
            "v26_used_for_learning": False,
            "test_loaded": False,
        },
        "different_generated_blocks": int(np.any(v23 != v26, axis=1).sum()),
        "systems": {
            "Bach": _row(lattice.blocks, lattice),
            "V23": _row(v23, lattice),
            "V26": _row(v26, lattice),
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v26-audit] changed={result['different_generated_blocks']} "
        f"strong_nontriadic="
        f"{result['systems']['V23']['strong_nontriadic_rate']:.4f}->"
        f"{result['systems']['V26']['strong_nontriadic_rate']:.4f}",
        flush=True,
    )
    print(f"[v26-audit] wrote {args.output}", flush=True)
    print(f"[v26-audit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
