#!/usr/bin/env python3
"""Audit exact train-only coverage of the two frozen V23 factor groups."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import yaml
from build_v23_selected_cache import selected_features

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v23_metric_bass_harmony_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-v23-selected-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v23_status_coverage_structure_train.json"
DEFAULT_REPORT = FACTOR_BASE / "V23_STATUS_COVERAGE_STRUCTURE_TRAIN.md"

BASS_PC_NAMES = (
    "I",
    "♭II",
    "II",
    "♭III",
    "III",
    "IV",
    "♯IV",
    "V",
    "♭VI",
    "VI",
    "♭VII",
    "VII",
)
FAMILY_NAMES = (
    "triades majeures/mineures",
    "triades diminuées/augmentées",
    "septièmes dominante/majeure/mineure",
    "septièmes altérées",
)
INVERSION_NAMES = (
    "fondamentale",
    "premier renversement",
    "deuxième renversement",
    "troisième renversement",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def feature_label(feature: k3.FeatureSpec) -> str:
    if feature.kind == "central_bass_tonal_strong_mode":
        mode = "majeur" if feature.second_value == 0 else "mineur"
        return f"basse temps fort, mode {mode}, degré {BASS_PC_NAMES[feature.value]}"
    if feature.kind == "central_unique_chord_family_inversion_strong":
        family, inversion = divmod(int(feature.value), 4)
        return f"{FAMILY_NAMES[family]}, {INVERSION_NAMES[inversion]}"
    if feature.kind == "central_residual_strong_sonority_status":
        return k3.RESIDUAL_STRONG_SONORITY_NAMES[int(feature.value)]
    raise ValueError(f"Unsupported V23 coverage feature: {feature.kind}")


def coverage_rows(
    factors: np.ndarray,
    chosen: np.ndarray,
    piece_ids: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    *,
    minimum_testable: int,
    minimum_piece_support: int,
) -> list[dict[str, Any]]:
    """Describe opportunities without looking at effects or validation NLL."""

    rows = np.arange(chosen.size)
    result = []
    for index, feature in enumerate(features):
        column = factors[:, :, index].astype(bool)
        testable = column.any(axis=1) & (~column).any(axis=1)
        chosen_active = column[rows, chosen]
        opportunity_support = int(np.unique(piece_ids[testable]).size)
        authentic_support = int(np.unique(piece_ids[chosen_active]).size)
        testable_count = int(testable.sum())
        result.append(
            {
                "feature_index": index,
                "feature": feature.to_dict(),
                "label": feature_label(feature),
                "testable_opportunities": testable_count,
                "opportunity_piece_support": opportunity_support,
                "authentic_activations": int(chosen_active.sum()),
                "authentic_piece_support": authentic_support,
                "candidate_world_activations": int(column.sum()),
                "coverage_eligible": (
                    testable_count >= minimum_testable
                    and opportunity_support >= minimum_piece_support
                ),
            }
        )
    return result


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V23 — couverture structure-train des deux groupes",
        "",
        "Cet audit est antérieur à l'apprentissage. Il ne consulte ni le signe",
        "d'un effet, ni la NLL de validation : il vérifie seulement qu'un facteur",
        "peut changer entre le choix authentique et ses alternatives exactes.",
        "",
        f"- Décisions : `{experiment['decisions']}` sur "
        f"`{experiment['pieces']}` chorals.",
        f"- Seuil descriptif : `{experiment['minimum_testable_opportunities']}` "
        "opportunités et "
        f"`{experiment['minimum_piece_support']}` chorals.",
        "",
    ]
    for group_id, group in result["groups"].items():
        lines.extend(
            [
                f"## `{group_id}`",
                "",
                f"- Cellules : `{group['cell_count']}`.",
                f"- Cellules franchissant le seuil : "
                f"`{group['eligible_cell_count']}/{group['cell_count']}`.",
                "",
                "| Statut | Opportunités | Chorals possibles | "
                "Activations Bach | Chorals Bach | Seuil |",
                "|---|---:|---:|---:|---:|:---:|",
            ]
        )
        for row in group["cells"]:
            lines.append(
                f"| {row['label']} | {row['testable_opportunities']} | "
                f"{row['opportunity_piece_support']} | "
                f"{row['authentic_activations']} | "
                f"{row['authentic_piece_support']} | "
                f"{'oui' if row['coverage_eligible'] else 'non'} |"
            )
        lines.append("")
    lines.extend(
        [
            "Une cellule rare n'est pas supprimée parce que son poids semble faible",
            "ou défavorable. La décision de factorisation doit porter sur un schéma",
            "entier et être prise avant l'ajustement des poids.",
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
        groups=config["groups"],
    )
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in features]:
        raise ValueError("V23 coverage feature order disagrees with exact cache")
    first_v23 = (
        len(baseline["selected_model"]["baseline_rules"])
        + len(baseline["selected_group"]["weights"])
    )
    coverage = config["coverage"]
    v23_features = features[first_v23:]
    rows = coverage_rows(
        archive["train_factors"][:, :, first_v23:],
        archive["train_chosen"],
        archive["train_piece_ids"],
        v23_features,
        minimum_testable=int(coverage["minimum_testable_opportunities"]),
        minimum_piece_support=int(coverage["minimum_piece_support"]),
    )
    groups = {}
    for group in config["groups"]:
        cells = [
            row
            for row in rows
            if row["feature"]["kind"] == group["feature_kind"]
        ]
        groups[group["id"]] = {
            "cell_count": len(cells),
            "eligible_cell_count": sum(
                bool(row["coverage_eligible"]) for row in cells
            ),
            "cells": cells,
        }
    result = {
        "experiment": {
            "id": "K3-V23-STATUS-COVERAGE-STRUCTURE-TRAIN",
            "scope": "exact_gibbs_attack_hold_worlds",
            "split": "structure_train",
            "pieces": len(np.unique(archive["train_piece_ids"])),
            "decisions": int(archive["train_chosen"].size),
            "minimum_testable_opportunities": int(
                coverage["minimum_testable_opportunities"]
            ),
            "minimum_piece_support": int(
                coverage["minimum_piece_support"]
            ),
            "validation_loaded_for_statistics": False,
            "effect_sizes_computed": False,
            "test_loaded": False,
        },
        "groups": groups,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    for group_id, group in groups.items():
        print(
            f"[v23-coverage] {group_id}: "
            f"{group['eligible_cell_count']}/{group['cell_count']} eligible",
            flush=True,
        )
    print(f"[v23-coverage] wrote {args.output}", flush=True)
    print(f"[v23-coverage] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
