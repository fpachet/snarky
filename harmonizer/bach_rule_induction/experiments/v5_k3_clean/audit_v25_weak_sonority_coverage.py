#!/usr/bin/env python3
"""Audit the frozen V25 weak-sonority vocabulary before learning weights."""

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
DEFAULT_CONFIG = FACTOR_BASE / "v25_weak_sonority_config.yaml"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_OUTPUT = FACTOR_BASE / "v25_weak_sonority_coverage.json"
DEFAULT_REPORT = FACTOR_BASE / "V25_WEAK_SONORITY_COVERAGE.md"


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
    experiment = result["experiment"]
    lines = [
        "# V25 — couverture des sonorités faibles résiduelles",
        "",
        "Audit exécuté avant tout apprentissage. Contrairement à V10–V14,",
        "les catégories sont mutuellement exclusives et le potentiel appartient",
        "au bloc vertical, pas à chaque paire de voix.",
        "",
        f"- Chorals : `{experiment['pieces']}`.",
        f"- Blocs faibles distincts : `{experiment['weak_blocks']}`.",
        f"- Accords nommés uniques de référence : "
        f"`{experiment['strict_unique_named_weak_blocks']}`.",
        f"- Blocs résiduels classés V25 : "
        f"`{experiment['v25_residual_weak_blocks']}`.",
        "",
        "| Statut V25 | Blocs Bach | Chorals Bach | Alternatives exactes | "
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
            "Les deux catégories `unlicensed` sont des restes déterministes,",
            "non des interdictions expertes. Leur signe doit être appris.",
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
    weak_representatives = representatives & (context.metric_levels < 2)
    chosen_statuses = k3.central_residual_weak_sonority_statuses(
        context,
        context.chosen_pitches[:, None],
    )[:, 0]
    all_statuses = k3.central_residual_weak_sonority_statuses(context)
    weak_rows = context.metric_levels < 2
    coverage = config["coverage"]
    cells = []
    for status, label in enumerate(k3.RESIDUAL_WEAK_SONORITY_NAMES):
        authentic = weak_representatives & (chosen_statuses == status)
        opportunities = weak_rows[:, None] & (all_statuses == status)
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
                    testable
                    >= int(coverage["minimum_testable_opportunities"])
                    and piece_support >= int(coverage["minimum_piece_support"])
                ),
            }
        )
    residual = weak_representatives & (chosen_statuses >= 0)
    result = {
        "experiment": {
            "id": config["id"],
            "status": "COVERAGE_ONLY",
            "split": "structure_train",
            "pieces": len(np.unique(context.piece_ids)),
            "weak_blocks": int(weak_representatives.sum()),
            "strict_unique_named_weak_blocks": int(
                (weak_representatives & (chosen_statuses < 0)).sum()
            ),
            "v25_residual_weak_blocks": int(residual.sum()),
            "all_residual_blocks_have_one_status": bool(
                residual.sum()
                == sum(cell["authentic_unique_blocks"] for cell in cells)
            ),
            "weights_fitted": False,
            "validation_effects_loaded": False,
            "test_loaded": False,
        },
        "eligible_cell_count": sum(
            bool(cell["coverage_eligible"]) for cell in cells
        ),
        "cell_count": len(cells),
        "cells": cells,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v25-coverage] eligible={result['eligible_cell_count']}/"
        f"{result['cell_count']} residual={int(residual.sum())}",
        flush=True,
    )
    print(f"[v25-coverage] wrote {args.output}", flush=True)
    print(f"[v25-coverage] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
