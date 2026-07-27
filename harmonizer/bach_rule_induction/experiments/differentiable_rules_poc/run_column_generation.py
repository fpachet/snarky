#!/usr/bin/env python3
"""Residual column generation for the second differentiable-rule POC.

The experiment keeps the V1 corpus, split and primitive numeric vocabulary.
Generic one-atom effects form a nuisance baseline. A beam search then proposes
short interactions from the conditional residual of the current model, one
column at a time. The sealed test split is never loaded or evaluated.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import run_poc as base


@dataclass(frozen=True)
class ResidualStatistic:
    """Conditional residual evidence for one candidate clause."""

    clause: base.Clause
    gradient: float
    hessian: float
    z_score: float
    approximate_nll_gain: float
    observed_rate: float
    expected_rate: float
    testable_opportunities: int
    piece_support: int
    maximum_redundancy: float
    description_cost: float
    redundancy_cost: float
    column_score: float


def baseline_clauses() -> list[base.Clause]:
    """Return generic main effects learned before interaction discovery."""

    clauses = [
        base.Clause((base.Atom("target_interval_mod12", value),)) for value in range(12)
    ]
    clauses.extend(
        base.Clause((base.Atom("soprano_direction", value),)) for value in (-1, 0, 1)
    )
    clauses.extend(
        base.Clause((base.Atom("soprano_leap_gt", value),))
        for value in (1, 2, 4, 7, 12)
    )
    clauses.append(base.Clause((base.Atom("learned_same_nonzero_sign", 1),)))
    return clauses


def probability_matrix(
    opportunities: base.Opportunities,
    clauses: list[base.Clause],
    masks: dict[base.Atom, np.ndarray],
    weights: np.ndarray,
) -> np.ndarray:
    """Return current conditional probabilities, including the empty model."""

    if not clauses:
        candidate_count = opportunities.candidate_pitches.shape[0]
        return np.full(
            (opportunities.size, candidate_count),
            1.0 / candidate_count,
            dtype=np.float64,
        )
    matrix = base.feature_matrix(clauses, masks)
    return base.probabilities(matrix, weights)


def chosen_vectors(
    clauses: list[base.Clause],
    masks: dict[base.Atom, np.ndarray],
    chosen_indices: np.ndarray,
) -> list[np.ndarray]:
    """Represent selected columns on observed choices for redundancy checks."""

    rows = np.arange(chosen_indices.shape[0])
    return [base.clause_mask(clause, masks)[rows, chosen_indices] for clause in clauses]


def maximum_jaccard(
    chosen: np.ndarray,
    selected_chosen: list[np.ndarray],
) -> float:
    """Maximum Jaccard overlap with an already selected observed column."""

    maximum = 0.0
    for existing in selected_chosen:
        union = int(np.logical_or(chosen, existing).sum())
        if union == 0:
            continue
        overlap = float(np.logical_and(chosen, existing).sum() / union)
        maximum = max(maximum, overlap)
    return maximum


def residual_statistic_for_clause(
    clause: base.Clause,
    masks: dict[base.Atom, np.ndarray],
    probabilities: np.ndarray,
    opportunities: base.Opportunities,
    selected_chosen: list[np.ndarray],
    complexity_penalty: float,
    redundancy_penalty: float,
) -> ResidualStatistic | None:
    """Score a Boolean column under the current conditional model.

    For a Boolean feature, the diagonal Fisher curvature in one opportunity is
    q(1-q), where q is the model probability mass covered by the feature. The
    one-step likelihood gain is approximated by g²/(2h).
    """

    mask = base.clause_mask(clause, masks)
    any_candidate = mask.any(axis=1)
    all_candidates = mask.all(axis=1)
    testable = any_candidate & ~all_candidates
    testable_count = int(testable.sum())
    if testable_count == 0:
        return None

    rows = np.arange(opportunities.size)
    chosen = mask[rows, opportunities.chosen_indices]
    expected = np.sum(probabilities * mask, axis=1)
    residual = chosen.astype(np.float64) - expected
    residual_sum = float(residual.sum())
    variance = float(np.sum(expected * (1.0 - expected)))
    if variance <= 1e-12:
        return None

    size = opportunities.size
    gradient = residual_sum / size
    hessian = variance / size
    z_score = residual_sum / math.sqrt(variance)
    approximate_nll_gain = 0.5 * gradient * gradient / hessian
    piece_support = int(np.unique(opportunities.piece_ids[testable]).shape[0])
    redundancy = maximum_jaccard(chosen, selected_chosen)
    log_size = math.log(max(size, 2))
    description_cost = complexity_penalty * clause.complexity * log_size / size
    redundancy_cost = redundancy_penalty * redundancy * log_size / size
    column_score = approximate_nll_gain - description_cost - redundancy_cost
    return ResidualStatistic(
        clause=clause,
        gradient=gradient,
        hessian=hessian,
        z_score=z_score,
        approximate_nll_gain=approximate_nll_gain,
        observed_rate=float(chosen[testable].mean()),
        expected_rate=float(expected[testable].mean()),
        testable_opportunities=testable_count,
        piece_support=piece_support,
        maximum_redundancy=redundancy,
        description_cost=description_cost,
        redundancy_cost=redundancy_cost,
        column_score=column_score,
    )


def search_residual_clauses(
    opportunities: base.Opportunities,
    masks: dict[base.Atom, np.ndarray],
    probabilities: np.ndarray,
    selected_clauses: list[base.Clause],
    max_depth: int,
    beam_size: int,
    min_testable: int,
    min_piece_support: int,
    complexity_penalty: float,
    redundancy_penalty: float,
    column_direction: str,
) -> list[ResidualStatistic]:
    """Beam-search the best new conjunction under the current residual."""

    atom_list = list(masks)
    selected_keys = {clause.key for clause in selected_clauses}
    selected_chosen = chosen_vectors(
        selected_clauses, masks, opportunities.chosen_indices
    )
    beam = [base.Clause((atom,)) for atom in atom_list]
    all_statistics: dict[str, ResidualStatistic] = {}

    for depth in range(1, max_depth + 1):
        admissible: list[ResidualStatistic] = []
        for clause in beam:
            statistic = residual_statistic_for_clause(
                clause,
                masks,
                probabilities,
                opportunities,
                selected_chosen,
                complexity_penalty,
                redundancy_penalty,
            )
            if (
                statistic is None
                or statistic.testable_opportunities < min_testable
                or statistic.piece_support < min_piece_support
            ):
                continue
            if column_direction == "avoid" and statistic.gradient >= 0:
                continue
            if column_direction == "prefer" and statistic.gradient <= 0:
                continue
            admissible.append(statistic)
            if clause.key not in selected_keys:
                all_statistics[clause.key] = statistic

        admissible.sort(key=lambda item: item.column_score, reverse=True)
        kept = admissible[:beam_size]
        print(
            f"[column-search] depth={depth} evaluated={len(beam)} "
            f"admissible={len(admissible)} kept={len(kept)}",
            flush=True,
        )
        if depth == max_depth:
            break

        # All singleton prefixes are extended. Some source-context atoms have
        # zero marginal effect but become informative in an interaction.
        prefixes = beam if depth == 1 else [statistic.clause for statistic in kept]
        extensions: dict[str, base.Clause] = {}
        for clause in prefixes:
            last_family = base.FAMILY_INDEX[clause.atoms[-1].family]
            used = {atom.family for atom in clause.atoms}
            for atom in atom_list:
                if atom.family in used:
                    continue
                if base.FAMILY_INDEX[atom.family] <= last_family:
                    continue
                extended = base.Clause(clause.atoms + (atom,))
                extensions[extended.key] = extended
        beam = list(extensions.values())
        if not beam:
            break

    return sorted(
        all_statistics.values(),
        key=lambda item: item.column_score,
        reverse=True,
    )


def fit_clauses(
    clauses: list[base.Clause],
    train_masks: dict[base.Atom, np.ndarray],
    validation_masks: dict[base.Atom, np.ndarray],
    train: base.Opportunities,
    validation: base.Opportunities,
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> tuple[np.ndarray, dict[str, Any], float, float]:
    """Fit one fixed catalogue and return train/validation losses."""

    train_matrix = base.feature_matrix(clauses, train_masks)
    validation_matrix = base.feature_matrix(clauses, validation_masks)
    weights, diagnostics = base.fit_sparse_conditional_model(
        train_matrix,
        train.chosen_indices,
        validation_matrix,
        validation.chosen_indices,
        l1=l1,
        max_steps=max_steps,
        learning_rate=learning_rate,
    )
    train_nll = base.conditional_nll(train_matrix, train.chosen_indices, weights)
    validation_nll = base.conditional_nll(
        validation_matrix, validation.chosen_indices, weights
    )
    return weights, diagnostics, train_nll, validation_nll


def serialize_residual_statistic(
    statistic: ResidualStatistic,
) -> dict[str, Any]:
    return {
        "clause": statistic.clause.key,
        "atoms": [
            {
                "family": atom.family,
                "value": atom.value,
                "label": atom.label,
            }
            for atom in statistic.clause.atoms
        ],
        "complexity": statistic.clause.complexity,
        "gradient": statistic.gradient,
        "hessian": statistic.hessian,
        "z_score": statistic.z_score,
        "approximate_nll_gain": statistic.approximate_nll_gain,
        "observed_rate": statistic.observed_rate,
        "expected_rate": statistic.expected_rate,
        "testable_opportunities": statistic.testable_opportunities,
        "piece_support": statistic.piece_support,
        "maximum_redundancy": statistic.maximum_redundancy,
        "description_cost": statistic.description_cost,
        "redundancy_cost": statistic.redundancy_cost,
        "column_score": statistic.column_score,
    }


def direct_arrival_clauses() -> list[base.Clause]:
    """Uniformly enumerate the twelve V2 target interactions."""

    learned = base.Atom("learned_same_nonzero_sign", 1)
    leap = base.Atom("soprano_leap_gt", 2)
    return [
        base.Clause(
            (
                base.Atom("target_interval_mod12", interval_class),
                leap,
                learned,
            )
        )
        for interval_class in range(12)
    ]


def scan_clauses(
    clauses: list[base.Clause],
    train: base.Opportunities,
    validation: base.Opportunities,
    train_masks: dict[base.Atom, np.ndarray],
    validation_masks: dict[base.Atom, np.ndarray],
    selected_clauses: list[base.Clause],
    weights: np.ndarray,
    complexity_penalty: float,
    redundancy_penalty: float,
) -> list[dict[str, Any]]:
    """Measure the same hypotheses before and after conditioning."""

    uniform_train = probability_matrix(
        train, [], train_masks, np.asarray([], dtype=np.float64)
    )
    uniform_validation = probability_matrix(
        validation,
        [],
        validation_masks,
        np.asarray([], dtype=np.float64),
    )
    fitted_train = probability_matrix(train, selected_clauses, train_masks, weights)
    fitted_validation = probability_matrix(
        validation, selected_clauses, validation_masks, weights
    )
    train_selected_chosen = chosen_vectors(
        selected_clauses, train_masks, train.chosen_indices
    )
    validation_selected_chosen = chosen_vectors(
        selected_clauses,
        validation_masks,
        validation.chosen_indices,
    )

    records: list[dict[str, Any]] = []
    for interval_class, clause in enumerate(clauses):
        stages: dict[str, dict[str, Any] | None] = {}
        for name, opportunities, masks, probabilities, selected in (
            (
                "uniform_train",
                train,
                train_masks,
                uniform_train,
                [],
            ),
            (
                "uniform_validation",
                validation,
                validation_masks,
                uniform_validation,
                [],
            ),
            (
                "residual_train",
                train,
                train_masks,
                fitted_train,
                train_selected_chosen,
            ),
            (
                "residual_validation",
                validation,
                validation_masks,
                fitted_validation,
                validation_selected_chosen,
            ),
        ):
            statistic = residual_statistic_for_clause(
                clause,
                masks,
                probabilities,
                opportunities,
                selected,
                complexity_penalty,
                redundancy_penalty,
            )
            stages[name] = (
                serialize_residual_statistic(statistic)
                if statistic is not None
                else None
            )
        records.append(
            {
                "numeric_class": interval_class,
                "clause": clause.key,
                **stages,
            }
        )
    return records


def select_direct_family_classes(
    scan: list[dict[str, Any]],
    train_z_threshold: float,
    validation_z_threshold: float,
) -> list[int]:
    """Select numeric classes by identical train/validation criteria."""

    return [
        int(record["numeric_class"])
        for record in scan
        if record["residual_train"]["z_score"] <= train_z_threshold
        and record["residual_validation"]["z_score"] <= validation_z_threshold
    ]


def compare_direct_clause_to_reference(
    interval_class: int,
    upper_range: range = range(60, 82),
    lower_range: range = range(36, 61),
) -> dict[str, int | str]:
    """Compare the induced formula with the held-out Snarky oracle.

    Only valid outer-voice states are enumerated: the upper voice remains above
    the lower voice at source and target. The oracle is consulted after
    induction and does not contribute labels or predicates to the learner.
    """

    tested = 0
    learned_positive = 0
    reference_positive = 0
    mismatches = 0
    for source_upper in upper_range:
        for source_lower in lower_range:
            if source_upper <= source_lower:
                continue
            for target_upper in upper_range:
                upper_delta = target_upper - source_upper
                for target_lower in lower_range:
                    if target_upper <= target_lower:
                        continue
                    lower_delta = target_lower - source_lower
                    same_nonzero_sign = (upper_delta > 0 and lower_delta > 0) or (
                        upper_delta < 0 and lower_delta < 0
                    )
                    learned = (
                        abs(target_upper - target_lower) % 12 == interval_class
                        and abs(upper_delta) > 2
                        and same_nonzero_sign
                    )
                    reference = (
                        target_upper - target_lower
                    ) % 12 == interval_class and (
                        (upper_delta > 2 and lower_delta > 0)
                        or (upper_delta < -2 and lower_delta < 0)
                    )
                    tested += 1
                    learned_positive += int(learned)
                    reference_positive += int(reference)
                    mismatches += int(learned != reference)
    return {
        "numeric_class": interval_class,
        "tested_valid_outer_voice_states": tested,
        "learned_positive_states": learned_positive,
        "reference_positive_states": reference_positive,
        "mismatches": mismatches,
        "classification": (
            "RECOVERED_EQUIVALENT" if mismatches == 0 else "RECOVERED_REFINED_OR_WEAKER"
        ),
    }


def run_column_generation(
    train: base.Opportunities,
    validation: base.Opportunities,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Fit the baseline and greedily add residual interaction columns."""

    atom_list = base.atoms(include_derived=True)
    train_masks = base.atom_masks(train, atom_list)
    validation_masks = base.atom_masks(validation, atom_list)
    selected = baseline_clauses()
    weights, diagnostics, train_nll, validation_nll = fit_clauses(
        selected,
        train_masks,
        validation_masks,
        train,
        validation,
        args.l1,
        args.max_steps,
        args.learning_rate,
    )
    baseline_validation_nll = validation_nll
    best_validation_nll = validation_nll
    best_selected = list(selected)
    best_weights = weights.copy()
    patience_left = args.patience
    history: list[dict[str, Any]] = [
        {
            "round": 0,
            "kind": "generic_main_effect_baseline",
            "clause_count": len(selected),
            "active_count": int((np.abs(weights) >= args.active_threshold).sum()),
            "train_nll": train_nll,
            "validation_nll": validation_nll,
            "fit": diagnostics,
        }
    ]

    for round_index in range(1, args.max_columns + 1):
        current_probabilities = probability_matrix(
            train, selected, train_masks, weights
        )
        searched = search_residual_clauses(
            train,
            train_masks,
            current_probabilities,
            selected,
            max_depth=args.max_depth,
            beam_size=args.beam_size,
            min_testable=args.min_testable,
            min_piece_support=args.min_piece_support,
            complexity_penalty=args.complexity_penalty,
            redundancy_penalty=args.redundancy_penalty,
            column_direction=args.column_direction,
        )
        if not searched or searched[0].column_score <= 0:
            print("[column] no positive penalized residual gain", flush=True)
            break

        proposed = searched[0]
        selected.append(proposed.clause)
        print(
            f"[column] round={round_index} score={proposed.column_score:.6g} "
            f"z={proposed.z_score:.3f} {proposed.clause.key}",
            flush=True,
        )
        weights, diagnostics, train_nll, validation_nll = fit_clauses(
            selected,
            train_masks,
            validation_masks,
            train,
            validation,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
        new_weight = float(weights[-1])
        history.append(
            {
                "round": round_index,
                "kind": "residual_column",
                "proposed": serialize_residual_statistic(proposed),
                "fitted_weight": new_weight,
                "clause_count": len(selected),
                "active_count": int((np.abs(weights) >= args.active_threshold).sum()),
                "train_nll": train_nll,
                "validation_nll": validation_nll,
                "fit": diagnostics,
                "top_residual_candidates": [
                    serialize_residual_statistic(item)
                    for item in searched[: args.report_candidates]
                ],
            }
        )

        if validation_nll < best_validation_nll - args.validation_min_delta:
            best_validation_nll = validation_nll
            best_selected = list(selected)
            best_weights = weights.copy()
            patience_left = args.patience
        else:
            patience_left -= 1
        if patience_left <= 0:
            print("[column] validation patience exhausted", flush=True)
            break

    active = np.abs(best_weights) >= args.active_threshold
    active_clauses = [
        clause for clause, keep in zip(best_selected, active, strict=True) if keep
    ]
    active_weights = best_weights[active]
    # Refit after pruning only for a coherent final residual.
    if active_clauses:
        (
            active_weights,
            final_diagnostics,
            final_train_nll,
            final_validation_nll,
        ) = fit_clauses(
            active_clauses,
            train_masks,
            validation_masks,
            train,
            validation,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
    else:
        final_diagnostics = {}
        final_train_nll = math.log(train.candidate_pitches.shape[0])
        final_validation_nll = final_train_nll

    direct_clauses = direct_arrival_clauses()
    scan_before_refinement = scan_clauses(
        direct_clauses,
        train,
        validation,
        train_masks,
        validation_masks,
        active_clauses,
        active_weights,
        args.complexity_penalty,
        args.redundancy_penalty,
    )
    active_keys = {clause.key for clause in active_clauses}
    selected_family_classes = select_direct_family_classes(
        scan_before_refinement,
        args.family_train_z,
        args.family_validation_z,
    )
    family_candidates = [
        direct_clauses[interval_class]
        for interval_class in selected_family_classes
        if direct_clauses[interval_class].key not in active_keys
    ]
    family_refinement: dict[str, Any] = {
        "train_z_threshold": args.family_train_z,
        "validation_z_threshold": args.family_validation_z,
        "candidate_classes": [clause.atoms[0].value for clause in family_candidates],
        "accepted": False,
        "validation_nll_before": final_validation_nll,
    }
    if family_candidates:
        refined_clauses = [*active_clauses, *family_candidates]
        (
            refined_weights,
            refined_diagnostics,
            refined_train_nll,
            refined_validation_nll,
        ) = fit_clauses(
            refined_clauses,
            train_masks,
            validation_masks,
            train,
            validation,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
        family_refinement.update(
            {
                "validation_nll_after": refined_validation_nll,
                "candidate_weights": {
                    str(clause.atoms[0].value): float(weight)
                    for clause, weight in zip(
                        family_candidates,
                        refined_weights[-len(family_candidates) :],
                        strict=True,
                    )
                },
            }
        )
        if refined_validation_nll < final_validation_nll:
            family_refinement["accepted"] = True
            active_clauses = refined_clauses
            active_weights = refined_weights
            final_diagnostics = refined_diagnostics
            final_train_nll = refined_train_nll
            final_validation_nll = refined_validation_nll

    selected_records = []
    baseline_keys = {clause.key for clause in baseline_clauses()}
    family_keys = {clause.key for clause in family_candidates}
    for clause, weight in zip(active_clauses, active_weights, strict=True):
        if clause.key in baseline_keys:
            kind = "baseline_main_effect"
        elif clause.key in family_keys:
            kind = "direct_family_refinement"
        else:
            kind = "residual_interaction"
        selected_records.append(
            {
                "clause": clause.key,
                "complexity": clause.complexity,
                "weight": float(weight),
                "kind": kind,
            }
        )
    selected_records.sort(key=lambda item: abs(item["weight"]), reverse=True)

    scan = scan_clauses(
        direct_clauses,
        train,
        validation,
        train_masks,
        validation_masks,
        active_clauses,
        active_weights,
        args.complexity_penalty,
        args.redundancy_penalty,
    )
    return {
        "baseline_validation_nll": baseline_validation_nll,
        "best_prefix_validation_nll": best_validation_nll,
        "final_train_nll": final_train_nll,
        "final_validation_nll": final_validation_nll,
        "selected_clause_count": len(active_clauses),
        "selected_residual_interaction_count": sum(
            record["kind"] == "residual_interaction" for record in selected_records
        ),
        "selected_direct_family_count": sum(
            record["kind"] == "direct_family_refinement" for record in selected_records
        ),
        "selected_rules": selected_records,
        "history": history,
        "final_fit": final_diagnostics,
        "direct_family_refinement": family_refinement,
        "semantic_comparison": [
            compare_direct_clause_to_reference(interval_class)
            for interval_class in family_refinement["candidate_classes"]
        ],
        "direct_arrival_scan_before_refinement": scan_before_refinement,
        "direct_arrival_scan": scan,
    }


def markdown_report(result: dict[str, Any]) -> str:
    """Render the compact, auditable V2 report."""

    corpus = result["corpus"]
    model = result["model"]
    lines = [
        "# POC V2.1 — génération de colonnes résiduelle",
        "",
        "## Protocole",
        "",
        (
            f"- Corpus : {corpus['pieces_total']} chorals, "
            f"{corpus['opportunities_total']} décisions disponibles."
        ),
        (
            f"- Train : {corpus['train_pieces']} pièces / "
            f"{corpus['train_opportunities']} décisions."
        ),
        (
            f"- Validation : {corpus['validation_pieces']} pièces / "
            f"{corpus['validation_opportunities']} décisions."
        ),
        "- Le jeu de test reste scellé et n'est pas chargé par ce programme.",
        (
            "- Contrôle nul : choix mélangés à l'intérieur des pièces."
            if result["experiment"]["null_shuffle"]
            else "- Données authentiques."
        ),
        (
            "- Direction des colonnes résiduelles : "
            f"`{result['experiment']['column_direction']}`."
        ),
        "- `LEARNED_PREDICATE_001` est réutilisé comme résultat du V1.",
        "",
        "## Modèle parcimonieux",
        "",
        (f"- NLL validation du socle : `{model['baseline_validation_nll']:.6f}`."),
        (
            f"- Meilleur préfixe de colonnes : "
            f"`{model['best_prefix_validation_nll']:.6f}`."
        ),
        f"- NLL finale après élagage : `{model['final_validation_nll']:.6f}`.",
        (
            f"- Clauses actives : {model['selected_clause_count']}, dont "
            f"{model['selected_residual_interaction_count']} interactions "
            "résiduelles et "
            f"{model['selected_direct_family_count']} raffinements de famille."
        ),
        "",
        "## Colonnes proposées",
        "",
        "| Tour | z résiduel | Score pénalisé | Poids ajusté | "
        "NLL validation | Clause |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for entry in model["history"][1:]:
        proposal = entry["proposed"]
        lines.append(
            f"| {entry['round']} | {proposal['z_score']:.3f} | "
            f"{proposal['column_score']:.6f} | "
            f"{entry['fitted_weight']:.3f} | "
            f"{entry['validation_nll']:.6f} | "
            f"`{proposal['clause']}` |"
        )

    lines.extend(
        [
            "",
            "## Scan uniforme des arrivées après saut en même direction",
            "",
            "Les classes `0..11` sont testées symétriquement. Le premier z est le",
            "marginal uniforme ; le second précède le raffinement de famille et",
            "le troisième suit son éventuelle acceptation.",
            "",
            "| Classe | z train uniforme | z validation uniforme | "
            "z train avant | z validation avant | "
            "z train après | z validation après |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for before, after in zip(
        model["direct_arrival_scan_before_refinement"],
        model["direct_arrival_scan"],
        strict=True,
    ):
        lines.append(
            f"| {before['numeric_class']} | "
            f"{before['uniform_train']['z_score']:.3f} | "
            f"{before['uniform_validation']['z_score']:.3f} | "
            f"{before['residual_train']['z_score']:.3f} | "
            f"{before['residual_validation']['z_score']:.3f} | "
            f"{after['residual_train']['z_score']:.3f} | "
            f"{after['residual_validation']['z_score']:.3f} |"
        )

    refinement = model["direct_family_refinement"]
    lines.extend(
        [
            "",
            "## Raffinement uniforme de la famille",
            "",
            (
                f"- Seuils : z train ≤ `{refinement['train_z_threshold']}` "
                f"et z validation ≤ `{refinement['validation_z_threshold']}`."
            ),
            (f"- Classes proposées : `{refinement['candidate_classes']}`."),
            f"- Raffinement accepté : `{refinement['accepted']}`.",
            (f"- NLL validation avant : `{refinement['validation_nll_before']:.6f}`."),
            (
                f"- NLL validation après : "
                f"`{refinement.get('validation_nll_after', math.nan):.6f}`."
            ),
            "",
            "## Comparaison sémantique postérieure",
            "",
            "| Classe | États valides testés | Positifs appris | "
            "Désaccords | Classification |",
            "|---:|---:|---:|---:|---|",
        ]
    )
    for comparison in model["semantic_comparison"]:
        lines.append(
            f"| {comparison['numeric_class']} | "
            f"{comparison['tested_valid_outer_voice_states']} | "
            f"{comparison['learned_positive_states']} | "
            f"{comparison['mismatches']} | "
            f"`{comparison['classification']}` |"
        )
    lines.extend(
        [
            "",
            "## Règles actives",
            "",
            "| Type | Poids | Clause |",
            "|---|---:|---|",
        ]
    )
    for record in model["selected_rules"]:
        lines.append(
            f"| {record['kind']} | {record['weight']:.3f} | `{record['clause']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=base.default_archive_path())
    parser.add_argument("--manifest", type=Path, default=base.default_manifest_path())
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--candidate-min", type=int, default=60)
    parser.add_argument("--candidate-max", type=int, default=81)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--beam-size", type=int, default=512)
    parser.add_argument("--min-testable", type=int, default=150)
    parser.add_argument("--min-piece-support", type=int, default=20)
    parser.add_argument("--max-columns", type=int, default=12)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--complexity-penalty", type=float, default=0.1)
    parser.add_argument("--redundancy-penalty", type=float, default=0.25)
    parser.add_argument(
        "--column-direction",
        choices=("both", "avoid", "prefer"),
        default="both",
        help="restrict residual proposals by the sign of their gradient",
    )
    parser.add_argument("--active-threshold", type=float, default=0.05)
    parser.add_argument("--validation-min-delta", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--report-candidates", type=int, default=20)
    parser.add_argument("--family-train-z", type=float, default=-3.0)
    parser.add_argument("--family-validation-z", type=float, default=-2.0)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--output-stem", default="v2_result")
    parser.add_argument("--results-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
    work = root / "work"
    results_dir = (
        args.results_dir.resolve() if args.results_dir is not None else root / "results"
    )
    archive = args.archive.resolve()
    manifest_path = args.manifest.resolve()
    actual_hash = base.sha256_file(archive)
    if actual_hash != base.EXPECTED_ARCHIVE_SHA256:
        raise ValueError(
            f"Unexpected archive hash {actual_hash}; "
            f"expected {base.EXPECTED_ARCHIVE_SHA256}"
        )

    manifest, included_pieces = base.load_included_pieces(manifest_path)
    splits = base.deterministic_splits(
        [piece["id"] for piece in included_pieces], args.seed
    )
    selected_pieces = included_pieces
    cache_suffix = "full"
    if args.max_pieces is not None:
        selected_ids = set((splits["train"] + splits["validation"])[: args.max_pieces])
        selected_pieces = [
            piece for piece in included_pieces if piece["id"] in selected_ids
        ]
        cache_suffix = f"smoke-{args.max_pieces}"

    cache_path = work / f"opportunities-{cache_suffix}.npz"
    if cache_path.exists():
        print(f"[corpus] loading cache {cache_path}", flush=True)
        all_opportunities = base.load_opportunities(cache_path)
    else:
        score_paths = base.materialize_scores(archive, selected_pieces, work / "scores")
        all_opportunities = base.build_opportunities(
            score_paths, args.candidate_min, args.candidate_max
        )
        base.save_opportunities(cache_path, all_opportunities)

    available = set(all_opportunities.piece_ids.tolist())
    train_ids = [piece for piece in splits["train"] if piece in available]
    validation_ids = [piece for piece in splits["validation"] if piece in available]
    if args.max_pieces is not None and not validation_ids:
        smoke_ids = sorted(available)
        split_at = max(1, int(0.8 * len(smoke_ids)))
        train_ids = smoke_ids[:split_at]
        validation_ids = smoke_ids[split_at:]
    train = base.subset_for_piece_ids(all_opportunities, train_ids)
    validation = base.subset_for_piece_ids(all_opportunities, validation_ids)
    if train.size == 0 or validation.size == 0:
        raise RuntimeError(
            f"Empty split: train={train.size}, validation={validation.size}"
        )
    if args.null_shuffle:
        train = base.shuffle_choices_within_pieces(train, args.seed + 101)
        validation = base.shuffle_choices_within_pieces(validation, args.seed + 202)

    print(
        f"[corpus] train={train.size} validation={validation.size}",
        flush=True,
    )
    model = run_column_generation(train, validation, args)
    result = {
        "schema_version": 2,
        "experiment": {
            "name": "differentiable_rules_poc_v2_column_generation",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "candidate_pitch_range": [
                args.candidate_min,
                args.candidate_max,
            ],
            "max_clause_depth": args.max_depth,
            "beam_size": args.beam_size,
            "complexity_penalty": args.complexity_penalty,
            "redundancy_penalty": args.redundancy_penalty,
            "column_direction": args.column_direction,
            "l1": args.l1,
            "family_train_z": args.family_train_z,
            "family_validation_z": args.family_validation_z,
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "music21": __import__("music21").__version__,
        },
        "source": {
            "archive": str(archive),
            "archive_sha256": actual_hash,
            "manifest": str(manifest_path),
            "manifest_schema_version": manifest["schema_version"],
        },
        "corpus": {
            "pieces_total": len(available),
            "opportunities_total": all_opportunities.size,
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "train_opportunities": train.size,
            "validation_opportunities": validation.size,
            "test_opened": False,
        },
        "model": model,
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / f"{args.output_stem}.json"
    report_path = results_dir / f"{args.output_stem.upper()}_REPORT.md"
    base.json_dump(json_path, result)
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"[done] wrote {json_path}", flush=True)
    print(f"[done] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
