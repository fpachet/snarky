#!/usr/bin/env python3
"""Find empirical prohibition and obligation candidates in exact K3 worlds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_v6_factor_induction as v6
import run_v18_explanatory_sparse_induction as sparse
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v22_shared_root_motion_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-v22-catalogue-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v22_constraint_candidate_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V22_CONSTRAINT_CANDIDATE_AUDIT.md"


def factor_extreme_statistics(
    matrix: np.ndarray,
    chosen: np.ndarray,
    piece_ids: np.ndarray,
) -> dict[str, Any]:
    """Measure authentic choices only where a predicate can change."""

    if matrix.ndim != 2:
        raise ValueError("One factor matrix must have shape (rows, candidates)")
    rows = np.arange(chosen.size)
    can_be_true = matrix.any(axis=1)
    can_be_false = (~matrix).any(axis=1)
    testable = can_be_true & can_be_false
    chosen_active = matrix[rows, chosen]
    opportunities = int(testable.sum())
    activations = int((chosen_active & testable).sum())
    opportunity_pieces = int(np.unique(piece_ids[testable]).size)
    activation_pieces = int(
        np.unique(piece_ids[chosen_active & testable]).size
    )
    inactive = testable & ~chosen_active
    inactive_pieces = int(np.unique(piece_ids[inactive]).size)
    candidate_true_cells = int(matrix[testable].sum())
    candidate_false_cells = int((~matrix[testable]).sum())
    return {
        "testable_opportunities": opportunities,
        "opportunity_piece_support": opportunity_pieces,
        "authentic_activations": activations,
        "authentic_inactivations": opportunities - activations,
        "authentic_activation_rate": (
            activations / opportunities if opportunities else 0.0
        ),
        "activation_piece_support": activation_pieces,
        "inactivation_piece_support": inactive_pieces,
        "counterfactual_true_cells": candidate_true_cells,
        "counterfactual_false_cells": candidate_false_cells,
    }


def classify_candidate(
    train: dict[str, Any],
    validation: dict[str, Any],
    *,
    minimum_train_opportunities: int,
    minimum_train_pieces: int,
    minimum_validation_opportunities: int,
    near_exception_rate: float,
) -> str | None:
    """Classify only patterns already extreme in train and confirmed in validation."""

    if (
        train["testable_opportunities"] < minimum_train_opportunities
        or train["opportunity_piece_support"] < minimum_train_pieces
        or validation["testable_opportunities"]
        < minimum_validation_opportunities
    ):
        return None
    prohibition_exceptions = (
        train["authentic_activations"]
        + validation["authentic_activations"]
    )
    obligation_exceptions = (
        train["authentic_inactivations"]
        + validation["authentic_inactivations"]
    )
    if prohibition_exceptions == 0:
        return "exact_empirical_prohibition"
    if obligation_exceptions == 0:
        return "exact_empirical_obligation"
    if (
        train["authentic_activation_rate"] <= near_exception_rate
        and validation["authentic_activation_rate"] <= near_exception_rate
    ):
        return "near_empirical_prohibition"
    if (
        train["authentic_activation_rate"] >= 1.0 - near_exception_rate
        and validation["authentic_activation_rate"]
        >= 1.0 - near_exception_rate
    ):
        return "near_empirical_obligation"
    return None


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    candidates = result["candidates"]
    lines = [
        "# V22 — audit des candidats contraintes",
        "",
        "Une contrainte candidate est recherchée uniquement parmi les prédicats",
        "lisibles et seulement dans les décisions où ce prédicat peut changer",
        "entre deux notes candidates. Aucun candidat n'est encore transformé en",
        "filtre dur.",
        "",
        "## Protocole",
        "",
        f"- Prédicats lisibles audités : `{experiment['readable_factors']}`.",
        f"- Décisions train/validation : "
        f"`{experiment['train_decisions']}/{experiment['validation_decisions']}`.",
        f"- Occasions train minimales : "
        f"`{experiment['minimum_train_opportunities']}`.",
        f"- Support train minimal : "
        f"`{experiment['minimum_train_pieces']}` chorals.",
        f"- Occasions validation minimales : "
        f"`{experiment['minimum_validation_opportunities']}`.",
        f"- Taux maximal d'exception pour « presque invariant » : "
        f"`{100 * experiment['near_exception_rate']:.2f} %`.",
        "- Test réservé chargé : `false`.",
        "",
        "## Résumé",
        "",
    ]
    for kind, count in result["summary"].items():
        lines.append(f"- `{kind}` : `{count}`.")
    for polarity, title in (
        ("prohibition", "Interdictions candidates"),
        ("obligation", "Obligations candidates"),
    ):
        rows = [
            row
            for row in candidates
            if polarity in row["classification"]
        ]
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                "| Statut | Prédicat | Train exceptions/occasions | "
                "Validation exceptions/occasions |",
                "|---|---|---:|---:|",
            ]
        )
        for row in rows[:40]:
            if polarity == "prohibition":
                train_exceptions = row["train"]["authentic_activations"]
                validation_exceptions = row["validation"][
                    "authentic_activations"
                ]
            else:
                train_exceptions = row["train"]["authentic_inactivations"]
                validation_exceptions = row["validation"][
                    "authentic_inactivations"
                ]
            lines.append(
                f"| `{row['classification']}` | {row['clause']} | "
                f"{train_exceptions}/"
                f"{row['train']['testable_opportunities']} | "
                f"{validation_exceptions}/"
                f"{row['validation']['testable_opportunities']} |"
            )
    lines.extend(
        [
            "",
            "Ces lignes restent des invariants empiriques. Une absence dans un",
            "petit corpus ne prouve pas une impossibilité logique. La promotion",
            "en contrainte requiert encore la stabilité inter-plis, l'examen des",
            "doublons logiques et une validation sur le corpus train complet.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--minimum-train-opportunities", type=int, default=100)
    parser.add_argument("--minimum-train-pieces", type=int, default=10)
    parser.add_argument(
        "--minimum-validation-opportunities",
        type=int,
        default=30,
    )
    parser.add_argument("--near-exception-rate", type=float, default=0.01)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    grammar = exact._load_grammar(
        (FACTOR_BASE / config["source_grammar"]).resolve()
    )
    catalogue = sparse._load_catalogue(source, grammar, args.context)
    family_by_kind = v6._feature_family_map(grammar)
    readable_indices = [
        index
        for index, feature in enumerate(catalogue)
        if family_by_kind[feature.kind] != "observed_vertical_set"
    ]
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in catalogue]:
        raise ValueError("Constraint audit cache and catalogue disagree")
    context = k3.load_k3_dataset(args.context).with_domain(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]),
    )
    train_context = k3.subset_for_piece_ids(context, metadata["train_ids"])
    validation_context = k3.subset_for_piece_ids(
        context,
        metadata["validation_ids"],
    )
    candidates = []
    for index in readable_indices:
        feature = catalogue[index]
        train = factor_extreme_statistics(
            k3.feature_mask(train_context, feature),
            train_context.chosen_indices,
            train_context.piece_ids,
        )
        validation = factor_extreme_statistics(
            k3.feature_mask(validation_context, feature),
            validation_context.chosen_indices,
            validation_context.piece_ids,
        )
        classification = classify_candidate(
            train,
            validation,
            minimum_train_opportunities=args.minimum_train_opportunities,
            minimum_train_pieces=args.minimum_train_pieces,
            minimum_validation_opportunities=(
                args.minimum_validation_opportunities
            ),
            near_exception_rate=args.near_exception_rate,
        )
        if classification is None:
            continue
        candidates.append(
            {
                "classification": classification,
                "clause": sparse._human_clause(feature),
                "family": family_by_kind[feature.kind],
                "feature": feature.to_dict(),
                "complexity": feature.complexity,
                "train": train,
                "validation": validation,
            }
        )
    candidates.sort(
        key=lambda row: (
            0 if row["classification"].startswith("exact") else 1,
            row["complexity"],
            -row["train"]["testable_opportunities"],
            row["feature"]["key"],
        )
    )
    summary: dict[str, int] = {}
    for row in candidates:
        summary[row["classification"]] = (
            summary.get(row["classification"], 0) + 1
        )
    result = {
        "experiment": {
            "id": "K3-V22-CONSTRAINT-CANDIDATE-AUDIT-1",
            "status": "EMPIRICAL_CANDIDATES_NOT_HARD_CONSTRAINTS",
            "grounding": "direct_local_predicate_not_segment_energy_total",
            "readable_factors": len(readable_indices),
            "train_decisions": train_context.size,
            "validation_decisions": validation_context.size,
            "minimum_train_opportunities": args.minimum_train_opportunities,
            "minimum_train_pieces": args.minimum_train_pieces,
            "minimum_validation_opportunities": (
                args.minimum_validation_opportunities
            ),
            "near_exception_rate": args.near_exception_rate,
            "test_loaded": False,
        },
        "summary": dict(sorted(summary.items())),
        "candidates": candidates,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v22-constraints] readable={len(readable_indices)} "
        f"candidates={len(candidates)} summary={summary}",
        flush=True,
    )
    print(f"[v22-constraints] wrote {args.output}", flush=True)
    print(f"[v22-constraints] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
