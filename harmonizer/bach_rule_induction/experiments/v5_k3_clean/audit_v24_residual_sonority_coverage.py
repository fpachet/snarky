#!/usr/bin/env python3
"""Audit V24 residual-sonority coverage before fitting any weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import yaml
from audit_v23_status_coverage import coverage_rows
from build_v24_selected_cache import selected_features

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v24_residual_sonority_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-v24-selected-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v24_residual_sonority_coverage.json"
DEFAULT_REPORT = FACTOR_BASE / "V24_RESIDUAL_SONORITY_COVERAGE.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V24 — couverture du groupe de sonorités résiduelles",
        "",
        "Cet audit est exécuté avant l'apprentissage. Les huit statuts couvrent",
        "exactement le complément des accords nommés uniques V23 sur temps fort.",
        "Aucun effet ni poids n'est consulté.",
        "",
        f"- Chorals : `{experiment['pieces']}`.",
        f"- Blocs forts distincts : `{experiment['strong_blocks']}`.",
        f"- Accords V23 nommés uniques : "
        f"`{experiment['v23_unique_named_strong_blocks']}`.",
        f"- Blocs couverts par V24 : `{experiment['v24_residual_strong_blocks']}`.",
        "",
        "| Statut V24 | Blocs Bach | Chorals Bach | Opportunités exactes | "
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
            "Le statut `other_unlicensed` n'est pas une règle experte : c'est le",
            "reste déterministe du vocabulaire. Son signe et son poids seront",
            "appris conjointement avec les sept autres cellules.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    baseline = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    grammar = exact._load_grammar(FACTOR_BASE / config["source_grammar"])
    features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=args.context,
        group=config["group"],
    )
    baseline_count = len(baseline["model"]["rules"])
    group_features = features[baseline_count:]
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in features]:
        raise ValueError("V24 cache and frozen features disagree")
    coverage = config["coverage"]
    rows = coverage_rows(
        archive["train_factors"][:, :, baseline_count:],
        archive["train_chosen"],
        archive["train_piece_ids"],
        group_features,
        minimum_testable=int(coverage["minimum_testable_opportunities"]),
        minimum_piece_support=int(coverage["minimum_piece_support"]),
    )
    context = k3.load_k3_dataset(args.context)
    context = k3.subset_for_piece_ids(
        context,
        metadata["train_ids"],
    ).with_domain(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]),
    )
    _, piece_groups = np.unique(context.piece_ids, return_inverse=True)
    representatives = k3.shared_potential_rows(context, piece_groups)
    strong = representatives & (context.metric_levels >= 2)
    statuses = k3.central_residual_strong_sonority_statuses(
        context,
        context.chosen_pitches[:, None],
    )[:, 0]
    for status, row in enumerate(rows):
        active = strong & (statuses == status)
        row["authentic_unique_blocks"] = int(active.sum())
        row["authentic_unique_piece_support"] = int(
            np.unique(context.piece_ids[active]).size
        )
    residual = strong & (statuses >= 0)
    result = {
        "experiment": {
            "id": "K3-V24-RESIDUAL-SONORITY-COVERAGE",
            "split": "structure_train",
            "pieces": len(np.unique(context.piece_ids)),
            "strong_blocks": int(strong.sum()),
            "v23_unique_named_strong_blocks": int(
                (strong & (statuses < 0)).sum()
            ),
            "v24_residual_strong_blocks": int(residual.sum()),
            "all_residual_blocks_have_one_status": bool(
                residual.sum()
                == sum(row["authentic_unique_blocks"] for row in rows)
            ),
            "weights_fitted": False,
            "validation_effects_loaded": False,
            "test_loaded": False,
        },
        "eligible_cell_count": sum(
            bool(row["coverage_eligible"]) for row in rows
        ),
        "cell_count": len(rows),
        "cells": rows,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v24-coverage] eligible={result['eligible_cell_count']}/"
        f"{result['cell_count']} residual_blocks={int(residual.sum())}",
        flush=True,
    )
    print(f"[v24-coverage] wrote {args.output}", flush=True)
    print(f"[v24-coverage] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
