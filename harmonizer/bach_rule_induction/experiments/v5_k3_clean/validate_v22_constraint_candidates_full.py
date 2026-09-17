#!/usr/bin/env python3
"""Validate structure-discovered constraint candidates on the full pretest split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_v22_constraint_candidates as audit
import k3

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CANDIDATES = FACTOR_BASE / "v22_constraint_candidate_audit.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_OUTPUT = FACTOR_BASE / "v22_constraint_candidate_full_validation.json"
DEFAULT_REPORT = FACTOR_BASE / "V22_CONSTRAINT_CANDIDATE_FULL_VALIDATION.md"


def constraint_family(feature: k3.FeatureSpec) -> str:
    if "ordered_gap" in feature.kind:
        return "voice_order_and_minimum_spacing"
    if feature.kind in {
        "abs_step_from_previous_gt",
        "abs_step_to_next_gt",
        "abs_class_from_previous",
        "abs_class_to_next",
    }:
        return "melodic_large_or_rare_interval"
    if "arrival_abs_class_same_sign" in feature.kind:
        return "direct_arrival_interval"
    if "preserved_same_sign" in feature.kind:
        return "parallel_preserved_interval"
    if feature.kind.startswith("central_named_chord"):
        return "named_harmonic_exclusion"
    return "other"


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V22 — validation élargie des contraintes candidates",
        "",
        "Les interdictions exactes découvertes sur 32/10 chorals sont réévaluées",
        "directement sur toutes les décisions des 251 chorals de train et des",
        "50 de validation. Le test réservé reste fermé.",
        "",
        "## Résumé",
        "",
        f"- Candidats exacts issus de la structure : "
        f"`{experiment['input_exact_candidates']}`.",
        f"- Toujours sans exception sur train et validation : "
        f"`{experiment['surviving_exact_candidates']}`.",
        f"- Décisions train/validation : "
        f"`{experiment['train_decisions']}/{experiment['validation_decisions']}`.",
        "",
        "## Familles survivantes",
        "",
        "| Famille | Candidats |",
        "|---|---:|",
    ]
    for family, count in result["family_summary"].items():
        lines.append(f"| `{family}` | {count} |")
    lines.extend(
        [
            "",
            "## Candidats exacts les mieux couverts",
            "",
            "| Famille | Prédicat | Train occasions | Validation occasions |",
            "|---|---|---:|---:|",
        ]
    )
    for row in result["survivors"][:60]:
        lines.append(
            f"| `{row['constraint_family']}` | {row['clause']} | "
            f"{row['full_train']['testable_opportunities']} | "
            f"{row['full_validation']['testable_opportunities']} |"
        )
    lines.extend(
        [
            "",
            "Ces candidats ne sont toujours pas des contraintes logiques. Les",
            "seuils emboîtés, les deux orientations d'une paire de voix et les",
            "prédicats impliqués par une règle plus générale doivent être",
            "fusionnés avant toute compilation en filtre dur.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    discovered = json.loads(args.candidates.read_text(encoding="utf-8"))
    exact_candidates = [
        row
        for row in discovered["candidates"]
        if row["classification"] == "exact_empirical_prohibition"
    ]
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    context = k3.load_k3_dataset(args.context)
    train = k3.subset_for_piece_ids(context, splits["train"])
    validation = k3.subset_for_piece_ids(context, splits["validation"])
    survivors = []
    rejected = []
    for row in exact_candidates:
        feature = k3.FeatureSpec.from_dict(row["feature"])
        train_stats = audit.factor_extreme_statistics(
            k3.feature_mask(train, feature),
            train.chosen_indices,
            train.piece_ids,
        )
        validation_stats = audit.factor_extreme_statistics(
            k3.feature_mask(validation, feature),
            validation.chosen_indices,
            validation.piece_ids,
        )
        payload: dict[str, Any] = {
            **row,
            "constraint_family": constraint_family(feature),
            "full_train": train_stats,
            "full_validation": validation_stats,
        }
        if (
            train_stats["authentic_activations"] == 0
            and validation_stats["authentic_activations"] == 0
        ):
            survivors.append(payload)
        else:
            rejected.append(payload)
    survivors.sort(
        key=lambda row: (
            -row["full_train"]["testable_opportunities"],
            row["complexity"],
            row["feature"]["key"],
        )
    )
    family_summary: dict[str, int] = {}
    for row in survivors:
        family = row["constraint_family"]
        family_summary[family] = family_summary.get(family, 0) + 1
    result = {
        "experiment": {
            "id": "K3-V22-CONSTRAINT-CANDIDATE-FULL-VALIDATION-1",
            "status": "PRETEST_EMPIRICAL_INVARIANTS_NOT_HARD_CONSTRAINTS",
            "input_exact_candidates": len(exact_candidates),
            "surviving_exact_candidates": len(survivors),
            "rejected_with_full_split": len(rejected),
            "train_pieces": len(set(map(str, train.piece_ids))),
            "validation_pieces": len(set(map(str, validation.piece_ids))),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
            "test_loaded": False,
        },
        "family_summary": dict(sorted(family_summary.items())),
        "survivors": survivors,
        "rejected": rejected,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v22-constraint-full] input={len(exact_candidates)} "
        f"survivors={len(survivors)} rejected={len(rejected)}",
        flush=True,
    )
    print(f"[v22-constraint-full] wrote {args.output}", flush=True)
    print(f"[v22-constraint-full] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
