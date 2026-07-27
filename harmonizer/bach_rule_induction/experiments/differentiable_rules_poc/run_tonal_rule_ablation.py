#!/usr/bin/env python3
"""Compare the learned tonal proxy with its exact harmonic specialization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base
import run_satb_level_a as satb
import run_tonal_tendency as tonal

PROXY_RULE_ID = "TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4"
HARMONIC_RULE_ID = "TONAL_EXACT_VII6_TO_I6"
MODEL_SPECS = {
    "baseline": (),
    "proxy": (PROXY_RULE_ID,),
    "harmonic": (HARMONIC_RULE_ID,),
    "both": (PROXY_RULE_ID, HARMONIC_RULE_ID),
}


def mode_rows(
    opportunities: satb.VoiceOpportunities,
    mode_by_piece: dict[str, str],
    required_mode: str,
) -> np.ndarray:
    return (
        np.asarray(
            [mode_by_piece[piece_id] for piece_id in opportunities.piece_ids]
        )
        == required_mode
    )


def proxy_rule_mask(
    opportunities: satb.VoiceOpportunities,
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
) -> np.ndarray:
    shape = (opportunities.size, opportunities.candidate_pitches.size)
    if opportunities.voice_index != 1:
        return np.zeros(shape, dtype=np.bool_)
    tonics = np.asarray(
        [tonic_by_piece[piece_id] for piece_id in opportunities.piece_ids],
        dtype=np.int16,
    )
    context = (
        mode_rows(opportunities, mode_by_piece, "major")
        & ((opportunities.previous_pitch - tonics) % 12 == 11)
        & ((opportunities.previous_all[:, 3] - tonics) % 12 == 2)
        & ((opportunities.current_all[:, 3] - tonics) % 12 == 4)
    )
    candidates = opportunities.candidate_pitches[None, :]
    conclusion = candidates == opportunities.previous_pitch[:, None] + 1
    return context[:, None] & conclusion


def exact_signature_rows(
    states: np.ndarray,
    tonics: np.ndarray,
    required_classes: tuple[int, ...],
) -> np.ndarray:
    relative = (states - tonics[:, None]) % 12
    allowed = np.isin(relative, np.asarray(required_classes))
    present = np.stack(
        [(relative == value).any(axis=1) for value in required_classes],
        axis=1,
    ).all(axis=1)
    return allowed.all(axis=1) & present


def candidate_target_signature_mask(
    opportunities: satb.VoiceOpportunities,
    tonics: np.ndarray,
    required_classes: tuple[int, ...],
) -> np.ndarray:
    candidates = opportunities.candidate_pitches
    relative_other = (
        opportunities.current_all - tonics[:, None]
    ) % 12
    other_indices = [
        voice for voice in range(4) if voice != opportunities.voice_index
    ]
    other = relative_other[:, other_indices]
    other_allowed = np.isin(other, np.asarray(required_classes)).all(axis=1)
    candidate_relative = (candidates[None, :] - tonics[:, None]) % 12
    candidate_allowed = np.isin(
        candidate_relative,
        np.asarray(required_classes),
    )
    present = np.ones(candidate_relative.shape, dtype=np.bool_)
    for value in required_classes:
        present &= (other == value).any(axis=1)[:, None] | (
            candidate_relative == value
        )
    return other_allowed[:, None] & candidate_allowed & present


def harmonic_rule_mask(
    opportunities: satb.VoiceOpportunities,
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
) -> np.ndarray:
    shape = (opportunities.size, opportunities.candidate_pitches.size)
    if opportunities.voice_index != 1:
        return np.zeros(shape, dtype=np.bool_)
    tonics = np.asarray(
        [tonic_by_piece[piece_id] for piece_id in opportunities.piece_ids],
        dtype=np.int16,
    )
    source_exact = exact_signature_rows(
        opportunities.previous_all,
        tonics,
        (2, 5, 11),
    )
    target_exact = candidate_target_signature_mask(
        opportunities,
        tonics,
        (0, 4, 7),
    )
    candidates = opportunities.candidate_pitches[None, :]
    conclusion = candidates == opportunities.previous_pitch[:, None] + 1
    context = (
        mode_rows(opportunities, mode_by_piece, "major")
        & source_exact
        & ((opportunities.previous_pitch - tonics) % 12 == 11)
        & ((opportunities.previous_all[:, 3] - tonics) % 12 == 2)
        & ((opportunities.current_all[:, 3] - tonics) % 12 == 4)
    )
    return context[:, None] & target_exact & conclusion


def rule_masks(
    opportunities: satb.VoiceOpportunities,
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
) -> dict[str, np.ndarray]:
    return {
        PROXY_RULE_ID: proxy_rule_mask(
            opportunities,
            tonic_by_piece,
            mode_by_piece,
        ),
        HARMONIC_RULE_ID: harmonic_rule_mask(
            opportunities,
            tonic_by_piece,
            mode_by_piece,
        ),
    }


def row_nll(
    matrix: np.ndarray,
    chosen_indices: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    probabilities = base.probabilities(matrix, weights)
    chosen = probabilities[np.arange(probabilities.shape[0]), chosen_indices]
    return -np.log(np.maximum(chosen, 1e-12))


def bootstrap_nll_gain_by_piece(
    reference_losses: np.ndarray,
    alternative_losses: np.ndarray,
    piece_ids: np.ndarray,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    pieces = np.unique(piece_ids)
    gain_by_piece = np.zeros(pieces.size, dtype=np.float64)
    count_by_piece = np.zeros(pieces.size, dtype=np.int64)
    for index, piece in enumerate(pieces):
        rows = piece_ids == piece
        gain_by_piece[index] = float(
            (reference_losses[rows] - alternative_losses[rows]).sum()
        )
        count_by_piece[index] = int(rows.sum())
    generator = np.random.default_rng(seed)
    sampled = generator.integers(0, pieces.size, size=(replicates, pieces.size))
    gains = gain_by_piece[sampled].sum(axis=1) / np.maximum(
        count_by_piece[sampled].sum(axis=1),
        1,
    )
    quantiles = np.quantile(gains, (0.025, 0.5, 0.975))
    return {
        "replicates": replicates,
        "piece_count": int(pieces.size),
        "gain_p025": float(quantiles[0]),
        "gain_median": float(quantiles[1]),
        "gain_p975": float(quantiles[2]),
        "positive_fraction": float(np.mean(gains > 0)),
    }


def fit_model_specs(
    train: satb.VoiceOpportunities,
    validation: satb.VoiceOpportunities,
    train_baseline: np.ndarray,
    validation_baseline: np.ndarray,
    train_masks: dict[str, np.ndarray],
    validation_masks: dict[str, np.ndarray],
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    records = {}
    losses = {}
    for model_name, rule_ids in MODEL_SPECS.items():
        if rule_ids:
            train_rules = np.stack(
                [train_masks[rule_id] for rule_id in rule_ids],
                axis=2,
            )
            validation_rules = np.stack(
                [validation_masks[rule_id] for rule_id in rule_ids],
                axis=2,
            )
            train_matrix = np.concatenate(
                (train_baseline, train_rules),
                axis=2,
            )
            validation_matrix = np.concatenate(
                (validation_baseline, validation_rules),
                axis=2,
            )
        else:
            train_matrix = train_baseline
            validation_matrix = validation_baseline
        print(f"[tonal-ablation] fitting {model_name}", flush=True)
        weights, diagnostics = base.fit_sparse_conditional_model(
            train_matrix,
            train.chosen_indices,
            validation_matrix,
            validation.chosen_indices,
            l1=l1,
            max_steps=max_steps,
            learning_rate=learning_rate,
        )
        train_losses = row_nll(train_matrix, train.chosen_indices, weights)
        validation_losses = row_nll(
            validation_matrix,
            validation.chosen_indices,
            weights,
        )
        losses[f"{model_name}_train"] = train_losses
        losses[f"{model_name}_validation"] = validation_losses
        rule_weights = (
            weights[-len(rule_ids) :]
            if rule_ids
            else np.asarray([], dtype=np.float64)
        )
        proxy_rows_train = train_masks[PROXY_RULE_ID].any(axis=1)
        proxy_rows_validation = validation_masks[PROXY_RULE_ID].any(axis=1)
        harmonic_rows_train = train_masks[HARMONIC_RULE_ID].any(axis=1)
        harmonic_rows_validation = validation_masks[HARMONIC_RULE_ID].any(
            axis=1
        )
        records[model_name] = {
            "rule_ids": list(rule_ids),
            "train_nll": float(train_losses.mean()),
            "validation_nll": float(validation_losses.mean()),
            "train_proxy_context_nll": float(
                train_losses[proxy_rows_train].mean()
            ),
            "validation_proxy_context_nll": float(
                validation_losses[proxy_rows_validation].mean()
            ),
            "train_harmonic_context_nll": float(
                train_losses[harmonic_rows_train].mean()
            ),
            "validation_harmonic_context_nll": float(
                validation_losses[harmonic_rows_validation].mean()
            ),
            "rule_weights": {
                rule_id: float(weight)
                for rule_id, weight in zip(
                    rule_ids,
                    rule_weights,
                    strict=True,
                )
            },
            "fit": diagnostics,
        }
    return records, losses


def selected_rate(
    data: satb.VoiceOpportunities,
    mask: np.ndarray,
) -> dict[str, Any]:
    premise = mask.any(axis=1)
    rows = np.flatnonzero(premise)
    chosen = mask[np.arange(data.size), data.chosen_indices]
    return {
        "opportunities": int(premise.sum()),
        "piece_support": int(np.unique(data.piece_ids[premise]).size),
        "conclusion_chosen": int(chosen[premise].sum()),
        "conclusion_rate": float(chosen[premise].mean()) if rows.size else 0.0,
    }


def comparison_records(
    models: dict[str, Any],
    losses: dict[str, np.ndarray],
    train: satb.VoiceOpportunities,
    validation: satb.VoiceOpportunities,
    bootstrap_replicates: int,
    seed: int,
) -> list[dict[str, Any]]:
    comparisons = (
        ("baseline_to_proxy", "baseline", "proxy"),
        ("baseline_to_harmonic", "baseline", "harmonic"),
        ("baseline_to_both", "baseline", "both"),
        ("proxy_to_both_harmonic_increment", "proxy", "both"),
        ("harmonic_to_both_proxy_increment", "harmonic", "both"),
    )
    records = []
    for index, (name, reference, alternative) in enumerate(comparisons):
        train_gain = (
            models[reference]["train_nll"] - models[alternative]["train_nll"]
        )
        validation_gain = (
            models[reference]["validation_nll"]
            - models[alternative]["validation_nll"]
        )
        records.append(
            {
                "comparison": name,
                "reference_model": reference,
                "alternative_model": alternative,
                "train_nll_gain": train_gain,
                "validation_nll_gain": validation_gain,
                "bootstrap_train": bootstrap_nll_gain_by_piece(
                    losses[f"{reference}_train"],
                    losses[f"{alternative}_train"],
                    train.piece_ids,
                    bootstrap_replicates,
                    seed + 2 * index,
                ),
                "bootstrap_validation": bootstrap_nll_gain_by_piece(
                    losses[f"{reference}_validation"],
                    losses[f"{alternative}_validation"],
                    validation.piece_ids,
                    bootstrap_replicates,
                    seed + 2 * index + 1,
                ),
            }
        )
    return records


def markdown_report(result: dict[str, Any]) -> str:
    model = result["model"]
    bootstrap_replicates = result["experiment"]["bootstrap_replicates"]
    bootstrap_label = f"{bootstrap_replicates:,}".replace(",", " ")
    lines = [
        "# POC V3.6 — ablation du proxy tonal et de son noyau harmonique",
        "",
        "## Protocole",
        "",
        "- Tâche conditionnelle : choix de la note d'alto.",
        "- Même baseline numérique que V3.1–V3.4.",
        "- Quatre modèles sont réajustés depuis zéro.",
        (
            "- Bootstrap par chorals entiers à poids ajustés fixes, "
            f"{bootstrap_label} réplications."
        ),
        "- Le test final reste scellé.",
        (
            "- Contrôle nul ciblé par permutation."
            if result["experiment"]["null_shuffle"]
            else "- Chorals authentiques."
        ),
        "",
        "## Couverture des colonnes",
        "",
        "| Colonne | Train | Validation |",
        "|---|---:|---:|",
    ]
    for rule_id in (PROXY_RULE_ID, HARMONIC_RULE_ID):
        coverage = model["rule_coverage"][rule_id]
        lines.append(
            f"| `{rule_id}` | "
            f"{coverage['train']['conclusion_chosen']}/"
            f"{coverage['train']['opportunities']} | "
            f"{coverage['validation']['conclusion_chosen']}/"
            f"{coverage['validation']['opportunities']} |"
        )
    lines.extend(
        [
            "",
            "## Modèles réajustés",
            "",
            "| Modèle | Colonnes | NLL validation | "
            "NLL contexte proxy | NLL contexte harmonique | Poids |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for model_name in MODEL_SPECS:
        record = model["models"][model_name]
        weights = ", ".join(
            f"{rule_id}={weight:.3f}"
            for rule_id, weight in record["rule_weights"].items()
        )
        lines.append(
            f"| {model_name} | {', '.join(record['rule_ids']) or '—'} | "
            f"{record['validation_nll']:.6f} | "
            f"{record['validation_proxy_context_nll']:.6f} | "
            f"{record['validation_harmonic_context_nll']:.6f} | "
            f"{weights or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Comparaisons et ablations réajustées",
            "",
            "| Comparaison | Gain NLL validation | Bootstrap validation, "
            "médiane [95 %] | P(gain > 0) |",
            "|---|---:|---:|---:|",
        ]
    )
    for record in model["comparisons"]:
        bootstrap = record["bootstrap_validation"]
        lines.append(
            f"| `{record['comparison']}` | "
            f"{record['validation_nll_gain']:+.8f} | "
            f"{bootstrap['gain_median']:+.8f} "
            f"[{bootstrap['gain_p025']:+.8f} ; "
            f"{bootstrap['gain_p975']:+.8f}] | "
            f"{bootstrap['positive_fraction']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = base.experiment_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=base.default_archive_path())
    parser.add_argument("--manifest", type=Path, default=base.default_manifest_path())
    parser.add_argument(
        "--splits",
        type=Path,
        default=column.default_variant_safe_splits_path(),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument(
        "--family-calibration",
        type=Path,
        default=root / "results/v3_4_tonal_family_calibration.json",
    )
    parser.add_argument(
        "--harmonic-audit",
        type=Path,
        default=root / "results/v3_5_selected_tonal_harmonic_audit.json",
    )
    parser.add_argument("--results-dir", type=Path, default=root / "results")
    parser.add_argument("--output-stem", default="v3_6_tonal_rule_ablation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
    work = root / "work"
    archive = args.archive.resolve()
    family_calibration = args.family_calibration.resolve()
    harmonic_audit = args.harmonic_audit.resolve()
    actual_hash = base.sha256_file(archive)
    if actual_hash != base.EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"Unexpected archive hash {actual_hash}")
    manifest, included_pieces = base.load_included_pieces(args.manifest.resolve())
    splits, split_metadata = column.load_experiment_splits(
        [piece["id"] for piece in included_pieces],
        args.seed,
        args.splits.resolve(),
    )
    selected_pieces = included_pieces
    cache_suffix = "full"
    if args.max_pieces is not None:
        selected_ids = set((splits["train"] + splits["validation"])[: args.max_pieces])
        selected_pieces = [
            piece for piece in included_pieces if piece["id"] in selected_ids
        ]
        cache_suffix = f"smoke-{args.max_pieces}"
    score_paths = base.materialize_scores(
        archive,
        selected_pieces,
        work / "scores",
    )
    tonic_by_piece, mode_by_piece, tonal_audit = tonal.build_tonal_status_maps(
        score_paths
    )
    all_opportunities = satb.load_satb_opportunities(
        work / f"satb-opportunities-{cache_suffix}.npz"
    )
    available = set(np.concatenate([data.piece_ids for data in all_opportunities]))
    train_ids = [piece for piece in splits["train"] if piece in available]
    validation_ids = [piece for piece in splits["validation"] if piece in available]
    if args.max_pieces is not None and not validation_ids:
        smoke_ids = sorted(available)
        split_at = max(1, int(0.8 * len(smoke_ids)))
        train_ids, validation_ids = smoke_ids[:split_at], smoke_ids[split_at:]
    train_all = [
        satb.subset_for_piece_ids(data, train_ids)
        for data in all_opportunities
    ]
    validation_all = [
        satb.subset_for_piece_ids(data, validation_ids)
        for data in all_opportunities
    ]
    train = train_all[1]
    validation = validation_all[1]
    if args.null_shuffle:
        train = satb.shuffle_choices_within_pieces(train, args.seed + 102)
        validation = satb.shuffle_choices_within_pieces(
            validation,
            args.seed + 203,
        )

    train_baseline = satb.baseline_matrix(train)
    validation_baseline = satb.baseline_matrix(validation)
    train_masks = rule_masks(train, tonic_by_piece, mode_by_piece)
    validation_masks = rule_masks(
        validation,
        tonic_by_piece,
        mode_by_piece,
    )
    if not np.all(
        train_masks[HARMONIC_RULE_ID] <= train_masks[PROXY_RULE_ID]
    ):
        raise AssertionError("Harmonic rule must be nested inside proxy rule")
    models, losses = fit_model_specs(
        train,
        validation,
        train_baseline,
        validation_baseline,
        train_masks,
        validation_masks,
        args.l1,
        args.max_steps,
        args.learning_rate,
    )
    comparisons = comparison_records(
        models,
        losses,
        train,
        validation,
        args.bootstrap_replicates,
        args.seed + 70_000,
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_6_tonal_rule_ablation",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "split_strategy": split_metadata["strategy"],
            "max_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
            "bootstrap_replicates": args.bootstrap_replicates,
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "music21": __import__("music21").__version__,
        },
        "source": {
            "archive": str(archive),
            "archive_sha256": actual_hash,
            "manifest": str(args.manifest.resolve()),
            "manifest_schema_version": manifest["schema_version"],
            "split": split_metadata["source"],
            "family_calibration": {
                "path": str(family_calibration),
                "sha256": base.sha256_file(family_calibration),
            },
            "harmonic_audit": {
                "path": str(harmonic_audit),
                "sha256": base.sha256_file(harmonic_audit),
            },
        },
        "tonal_status_audit": tonal_audit,
        "corpus": {
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "train_alto_opportunities": train.size,
            "validation_alto_opportunities": validation.size,
            "test_opened": False,
        },
        "model": {
            "rule_ids": [PROXY_RULE_ID, HARMONIC_RULE_ID],
            "rule_coverage": {
                rule_id: {
                    "train": selected_rate(train, train_masks[rule_id]),
                    "validation": selected_rate(
                        validation,
                        validation_masks[rule_id],
                    ),
                }
                for rule_id in (PROXY_RULE_ID, HARMONIC_RULE_ID)
            },
            "models": models,
            "comparisons": comparisons,
        },
    }
    results_dir = args.results_dir.resolve()
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
