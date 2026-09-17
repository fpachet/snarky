#!/usr/bin/env python3
"""Audit the frozen V27 bass-trajectory partition before fitting weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v27_bass_trajectory_config.yaml"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_OUTPUT = FACTOR_BASE / "v27_bass_trajectory_coverage.json"
DEFAULT_REPORT = FACTOR_BASE / "V27_BASS_TRAJECTORY_COVERAGE.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--pieces", type=int, default=32)
    return parser.parse_args()


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V27 — couverture des trajectoires de basse",
        "",
        "La partition est gelée avant l'apprentissage. Chaque bloc reçoit",
        "exactement un statut harmonique ou mélodique de basse.",
        "",
        "| Statut | Blocs Bach | Chorals Bach | Alternatives | "
        "Chorals possibles | Seuil |",
        "|---|---:|---:|---:|---:|:---:|",
    ]
    for row in result["cells"]:
        lines.append(
            f"| `{row['label']}` | {row['authentic_unique_blocks']} | "
            f"{row['authentic_unique_piece_support']} | "
            f"{row['testable_opportunities']} | "
            f"{row['opportunity_piece_support']} | "
            f"{'oui' if row['coverage_eligible'] else 'non'} |"
        )
    lines.extend(
        [
            "",
            "Les statuts chromatiques authentiques sont rares, mais toutes les",
            "cellules disposent d'assez d'alternatives contrefactuelles pour un",
            "apprentissage conjoint. Aucune rareté n'est convertie en interdit.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    piece_ids = sorted(splits["train"], key=generative._stable_order)[: args.pieces]
    context = k3.subset_for_piece_ids(
        k3.load_k3_dataset(args.context),
        piece_ids,
    )
    _, piece_groups = np.unique(context.piece_ids, return_inverse=True)
    representatives = k3.shared_potential_rows(context, piece_groups)
    chosen = k3.central_bass_trajectory_statuses(
        context,
        context.chosen_pitches[:, None],
    )[:, 0]
    alternatives = k3.central_bass_trajectory_statuses(context)
    coverage = config["coverage"]
    cells = []
    for status, label in enumerate(k3.BASS_TRAJECTORY_STATUS_NAMES):
        authentic = representatives & (chosen == status)
        opportunities = alternatives == status
        opportunity_rows = np.any(opportunities, axis=1)
        testable = int(opportunities.sum())
        piece_support = int(np.unique(context.piece_ids[opportunity_rows]).size)
        cells.append(
            {
                "status": status,
                "label": label,
                "authentic_unique_blocks": int(authentic.sum()),
                "authentic_unique_piece_support": int(
                    np.unique(context.piece_ids[authentic]).size
                ),
                "testable_opportunities": testable,
                "opportunity_piece_support": piece_support,
                "coverage_eligible": (
                    testable >= int(coverage["minimum_testable_opportunities"])
                    and piece_support >= int(coverage["minimum_piece_support"])
                ),
            }
        )
    result = {
        "experiment": {
            "id": config["id"],
            "status": "COVERAGE_ONLY",
            "split": "structure_train",
            "pieces": len(np.unique(context.piece_ids)),
            "representative_blocks": int(representatives.sum()),
            "all_blocks_have_one_status": bool(
                representatives.sum()
                == sum(cell["authentic_unique_blocks"] for cell in cells)
            ),
            "weights_fitted": False,
            "generated_bwv108_6_loaded": False,
            "validation_effects_loaded": False,
            "test_loaded": False,
        },
        "eligible_cell_count": sum(bool(cell["coverage_eligible"]) for cell in cells),
        "cell_count": len(cells),
        "cells": cells,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v27-coverage] eligible={result['eligible_cell_count']}/"
        f"{result['cell_count']} blocks="
        f"{result['experiment']['representative_blocks']}",
        flush=True,
    )
    print(f"[v27-coverage] wrote {args.output}", flush=True)
    print(f"[v27-coverage] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
