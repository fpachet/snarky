#!/usr/bin/env python3
"""Fit observable opening/closing chord factors on the frozen training split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import run_generative_moment_calibration as generative
import v34_harmony

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "boundary_chord_factors.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--alpha", type=float, default=0.5)
    return parser.parse_args()


def _record(
    piece_id: str,
    boundary: str,
    lattice: k3.RhythmicLattice,
    time: int,
) -> dict[str, Any] | None:
    block = lattice.blocks[time]
    analysis = v34_harmony.analyze_block(block, lattice.tonic_pc)
    if int(analysis["analysis_count"]) != 1:
        return None
    return {
        "piece_id": piece_id,
        "boundary": boundary,
        "mode": lattice.mode,
        "soprano_degree": (int(block[0]) - lattice.tonic_pc) % 12,
        "quality": int(analysis["quality"]),
        "root_degree": int(analysis["root_degree"]),
        "inversion_interval": int(analysis["inversion_interval"]),
        "lower_intervals_from_soprano": [
            int(block[0] - block[voice]) for voice in range(1, 4)
        ],
    }


def main() -> int:
    args = parse_args()
    if args.alpha <= 0:
        raise ValueError("--alpha must be positive")
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    records = []
    skipped = []
    for piece_id in sorted(splits["train"], key=generative._stable_order):
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        piece_records = tuple(
            row
            for row in (
                _record(piece_id, "opening", lattice, 0),
                _record(piece_id, "closing", lattice, lattice.size - 1),
            )
            if row is not None
        )
        records.extend(piece_records)
        if len(piece_records) != 2:
            skipped.append(piece_id)
    payload = {
        "schema_version": 1,
        "id": "K3-BOUNDARY-CHORD-FACTORS-1",
        "status": "TRAIN_ONLY_FROZEN_COUNTS",
        "estimator": "leave_one_piece_out_smoothed_categorical",
        "alpha": args.alpha,
        "training_split": "train251",
        "training_piece_count": len(splits["train"]),
        "validation_loaded": False,
        "test_loaded": False,
        "state": ["quality", "root_degree", "inversion_interval"],
        "voicing_factors": [
            "soprano_minus_alto",
            "soprano_minus_tenor",
            "soprano_minus_bass",
        ],
        "conditioning": ["boundary", "mode", "soprano_degree"],
        "records": records,
        "skipped_non_unique_boundary_pieces": skipped,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"[boundary-factors] records={len(records)} skipped={len(skipped)} "
        f"wrote={args.output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
