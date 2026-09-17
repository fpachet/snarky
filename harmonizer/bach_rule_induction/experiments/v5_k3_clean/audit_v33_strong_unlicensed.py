#!/usr/bin/env python3
"""Audit strong unlicensed sonorities before the V33 constraint ablation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
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
DEFAULT_V32 = FACTOR_BASE / "two_loop_full_generation_v32.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v33_strong_unlicensed_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V33_STRONG_UNLICENSED_AUDIT.md"
UNLICENSED_STATUSES = (6, 7)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--v32", type=Path, default=DEFAULT_V32)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _statuses(
    lattice: k3.RhythmicLattice,
    blocks: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    indices = np.arange(1, lattice.size - 1)
    dataset = k3.K3Dataset(
        piece_ids=np.asarray([lattice.piece_id] * indices.size),
        offsets=np.stack(
            (
                lattice.offsets[indices - 1],
                lattice.offsets[indices],
                lattice.offsets[indices + 1],
            ),
            axis=1,
        ),
        voice_indices=np.zeros(indices.size, dtype=np.int8),
        blocks=np.stack(
            (blocks[indices - 1], blocks[indices], blocks[indices + 1]),
            axis=1,
        ),
        attacks=np.stack(
            (
                lattice.attacks[indices - 1],
                lattice.attacks[indices],
                lattice.attacks[indices + 1],
            ),
            axis=1,
        ),
        candidate_min=int(blocks.min()),
        candidate_max=int(blocks.max()),
        tonic_pcs=np.full(indices.size, lattice.tonic_pc, dtype=np.int8),
        modes=np.full(indices.size, lattice.mode, dtype=np.int8),
        metric_levels=lattice.metric_levels[indices],
    )
    candidates = blocks[indices, 0, None]
    statuses = k3.central_residual_strong_sonority_statuses(
        dataset,
        candidates,
    )[:, 0]
    return indices, statuses


def _profile(
    lattice: k3.RhythmicLattice,
    blocks: np.ndarray,
) -> dict[str, Any]:
    indices, statuses = _statuses(lattice, blocks)
    strong = lattice.metric_levels[indices] >= 2
    counts = Counter(int(status) for status in statuses if status >= 0)
    unlicensed = np.isin(statuses, UNLICENSED_STATUSES)
    examples = [
        {
            "block": int(index),
            "offset": float(lattice.offsets[index]),
            "status": k3.RESIDUAL_STRONG_SONORITY_NAMES[int(status)],
            "pitches": [int(pitch) for pitch in blocks[index]],
        }
        for index, status in zip(indices, statuses, strict=True)
        if int(status) in UNLICENSED_STATUSES
    ]
    return {
        "strong_interior_blocks": int(strong.sum()),
        "unlicensed_strong_blocks": int(unlicensed.sum()),
        "unlicensed_strong_rate": (
            0.0 if not strong.any() else float(unlicensed.sum() / strong.sum())
        ),
        "status_counts": {
            k3.RESIDUAL_STRONG_SONORITY_NAMES[status]: count
            for status, count in sorted(counts.items())
        },
        "examples": examples,
    }


def _aggregate(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    strong = sum(row["strong_interior_blocks"] for row in profiles)
    unlicensed = sum(row["unlicensed_strong_blocks"] for row in profiles)
    return {
        "pieces": len(profiles),
        "strong_interior_blocks": strong,
        "unlicensed_strong_blocks": unlicensed,
        "unlicensed_strong_rate": unlicensed / strong,
        "pieces_with_unlicensed": sum(
            row["unlicensed_strong_blocks"] > 0 for row in profiles
        ),
        "maximum_unlicensed_in_one_piece": max(
            row["unlicensed_strong_blocks"] for row in profiles
        ),
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# V33 — audit préalable des sonorités fortes non licenciées",
        "",
        "Les deux statuts étudiés sont `triad_plus_unlicensed` et",
        "`other_unlicensed`. Ils dépendent du bloc précédent et du bloc",
        "suivant : une note étrangère correctement préparée ou résolue n'est",
        "donc pas comptée comme non licenciée.",
        "",
        "| Corpus | Blocs forts | Non licenciés | Taux | Pièces touchées |",
        "|---|---:|---:|---:|---:|",
    ]
    for split in ("train251", "validation50", "test51"):
        row = payload["bach_corpus"][split]
        lines.append(
            f"| {split} | {row['strong_interior_blocks']} | "
            f"{row['unlicensed_strong_blocks']} | "
            f"{100 * row['unlicensed_strong_rate']:.3f} % | "
            f"{row['pieces_with_unlicensed']} / {row['pieces']} |"
        )
    paired = payload["paired_bwv108_6"]
    lines.extend(
        [
            "",
            "## BWV 108.6 apparié",
            "",
            "| Système | Blocs forts | Non licenciés | Taux |",
            "|---|---:|---:|---:|",
        ]
    )
    for system in ("Bach", "V32"):
        row = paired[system]
        lines.append(
            f"| {system} | {row['strong_interior_blocks']} | "
            f"{row['unlicensed_strong_blocks']} | "
            f"{100 * row['unlicensed_strong_rate']:.3f} % |"
        )
    lines.extend(
        [
            "",
            "Cet audit décide si une interdiction absolue est défendable.",
            "Si Bach contient ces statuts, V33 reste une ablation générative",
            "et non une promotion dans la théorie apprise.",
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
        profiles = []
        for piece_id in piece_ids:
            lattice = k3.extract_piece_lattice(
                generative._score_path(args.scores, piece_id),
                piece_id,
            )
            profiles.append(_profile(lattice, lattice.blocks))
        corpus[split] = _aggregate(profiles)

    reference = k3.extract_piece_lattice(args.score, args.piece_id)
    v32_payload = json.loads(args.v32.read_text(encoding="utf-8"))
    v32_blocks = np.asarray(v32_payload["solution"]["blocks"], dtype=np.int16)
    paired = {
        "Bach": _profile(reference, reference.blocks),
        "V32": _profile(reference, v32_blocks),
    }
    payload = {
        "experiment": {
            "id": "K3-V33-STRONG-UNLICENSED-AUDIT-1",
            "status": "PRE_CONSTRAINT_AUDIT",
            "generated_piece_used_for_threshold_learning": False,
            "weights_fitted": False,
            "test_loaded": True,
        },
        "statuses": [
            k3.RESIDUAL_STRONG_SONORITY_NAMES[index]
            for index in UNLICENSED_STATUSES
        ],
        "bach_corpus": corpus,
        "paired_bwv108_6": paired,
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    print(
        "[v33-unlicensed-audit] "
        f"train={corpus['train251']['unlicensed_strong_rate']:.6f} "
        f"Bach108={paired['Bach']['unlicensed_strong_blocks']} "
        f"V32={paired['V32']['unlicensed_strong_blocks']}",
        flush=True,
    )
    print(f"[v33-unlicensed-audit] wrote {args.output}", flush=True)
    print(f"[v33-unlicensed-audit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
