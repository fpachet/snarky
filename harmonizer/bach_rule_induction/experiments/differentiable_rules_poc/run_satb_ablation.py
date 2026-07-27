#!/usr/bin/env python3
"""Joint predictive ablation of the readable SATB Level-A rule catalogue.

Seven recovered avoidance rules are fitted together on top of the V2.2
nuisance baseline.  The experiment reports the full validation gain and a
fixed-model zeroing ablation for every readable rule.  The sealed test split
is never loaded or evaluated.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base
import run_satb_level_a as satb
import run_satb_parallels as parallels

RULE_IDS = (
    "R-MELODY-001",
    "R-MELODY-002",
    "R-OVERLAP-001",
    "R-PARALLEL-001",
    "R-PARALLEL-002",
    "R-DIRECT-001",
    "R-DIRECT-002",
)


def nuisance_baseline_matrix(
    opportunities: satb.VoiceOpportunities,
) -> np.ndarray:
    """V2.2 baseline with the >12 leap feature reserved for the rule catalogue."""

    candidates = opportunities.candidate_pitches[None, :]
    previous = opportunities.previous_pitch[:, None]
    delta = candidates - previous
    features = [candidates == pitch for pitch in opportunities.candidate_pitches]
    features.extend(np.sign(delta) == direction for direction in (-1, 0, 1))
    features.extend(np.abs(delta) > threshold for threshold in (1, 2, 4, 7))
    for other_voice in range(4):
        if other_voice == opportunities.voice_index:
            continue
        harmonic_class = (
            np.abs(candidates - opportunities.current_all[:, other_voice, None]) % 12
        )
        features.extend(
            harmonic_class == interval_class for interval_class in range(12)
        )
    if opportunities.voice_index < 3:
        separation = (
            candidates
            - opportunities.previous_all[:, opportunities.voice_index + 1, None]
        ) / 12.0
        features.extend((separation, separation**2))
    if opportunities.voice_index > 0:
        separation = (
            opportunities.previous_all[:, opportunities.voice_index - 1, None]
            - candidates
        ) / 12.0
        features.extend((separation, separation**2))
    shape = delta.shape
    return np.stack(
        [np.broadcast_to(feature, shape) for feature in features],
        axis=2,
    ).astype(np.float32)


def direct_outer_mask(
    opportunities: satb.VoiceOpportunities,
    target_class: int,
) -> np.ndarray:
    """Recovered direct-motion clause on soprano choice opportunities."""

    shape = (opportunities.size, opportunities.candidate_pitches.size)
    if opportunities.voice_index != 0:
        return np.zeros(shape, dtype=np.bool_)
    candidates = opportunities.candidate_pitches[None, :]
    soprano_delta = candidates - opportunities.previous_pitch[:, None]
    bass_delta = (
        opportunities.current_all[:, 3] - opportunities.previous_all[:, 3]
    )[:, None]
    same_nonzero_direction = (
        ((soprano_delta > 0) & (bass_delta > 0))
        | ((soprano_delta < 0) & (bass_delta < 0))
    )
    target_interval = (
        candidates - opportunities.current_all[:, 3, None]
    ) % 12
    return (
        (target_interval == target_class)
        & (np.abs(soprano_delta) > 2)
        & same_nonzero_direction
    )


def readable_rule_masks(
    opportunities: satb.VoiceOpportunities,
) -> dict[str, np.ndarray]:
    candidates = opportunities.candidate_pitches[None, :]
    previous = opportunities.previous_pitch[:, None]
    return {
        "R-MELODY-001": np.abs(candidates - previous) > 12,
        "R-MELODY-002": satb.melodic_interval_mask(opportunities, 6),
        "R-OVERLAP-001": satb.any_overlap_depth_mask(opportunities, 0),
        "R-PARALLEL-001": parallels.parallel_interval_class_mask(
            opportunities, 0
        ),
        "R-PARALLEL-002": parallels.parallel_interval_class_mask(
            opportunities, 7
        ),
        "R-DIRECT-001": direct_outer_mask(opportunities, 0),
        "R-DIRECT-002": direct_outer_mask(opportunities, 7),
    }


def combined_nll(
    records: list[dict[str, Any]],
    key: str,
    size_key: str,
) -> float:
    total = sum(record[size_key] for record in records)
    return sum(record[key] * record[size_key] for record in records) / total


def fit_joint_catalogue(
    train: list[satb.VoiceOpportunities],
    validation: list[satb.VoiceOpportunities],
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> dict[str, Any]:
    """Fit per-voice nuisance terms plus the same readable rule catalogue."""

    voice_records: list[dict[str, Any]] = []
    for train_voice, validation_voice in zip(train, validation, strict=True):
        voice_name = satb.VOICE_NAMES[train_voice.voice_index]
        print(f"[ablation] fitting {voice_name}", flush=True)
        train_baseline = nuisance_baseline_matrix(train_voice)
        validation_baseline = nuisance_baseline_matrix(validation_voice)
        baseline_weights, baseline_fit = base.fit_sparse_conditional_model(
            train_baseline,
            train_voice.chosen_indices,
            validation_baseline,
            validation_voice.chosen_indices,
            l1=l1,
            max_steps=max_steps,
            learning_rate=learning_rate,
        )
        baseline_train_nll = base.conditional_nll(
            train_baseline, train_voice.chosen_indices, baseline_weights
        )
        baseline_validation_nll = base.conditional_nll(
            validation_baseline,
            validation_voice.chosen_indices,
            baseline_weights,
        )

        train_masks = readable_rule_masks(train_voice)
        validation_masks = readable_rule_masks(validation_voice)
        train_rules = np.stack([train_masks[rule] for rule in RULE_IDS], axis=2)
        validation_rules = np.stack(
            [validation_masks[rule] for rule in RULE_IDS], axis=2
        )
        train_full = np.concatenate((train_baseline, train_rules), axis=2)
        validation_full = np.concatenate(
            (validation_baseline, validation_rules), axis=2
        )
        full_weights, full_fit = base.fit_sparse_conditional_model(
            train_full,
            train_voice.chosen_indices,
            validation_full,
            validation_voice.chosen_indices,
            l1=l1,
            max_steps=max_steps,
            learning_rate=learning_rate,
        )
        full_train_nll = base.conditional_nll(
            train_full, train_voice.chosen_indices, full_weights
        )
        full_validation_nll = base.conditional_nll(
            validation_full,
            validation_voice.chosen_indices,
            full_weights,
        )
        baseline_feature_count = train_baseline.shape[2]
        rule_weights = full_weights[baseline_feature_count:]
        ablated_validation_nll: dict[str, float] = {}
        for rule_index, rule_id in enumerate(RULE_IDS):
            ablated_weights = full_weights.copy()
            ablated_weights[baseline_feature_count + rule_index] = 0.0
            ablated_validation_nll[rule_id] = base.conditional_nll(
                validation_full,
                validation_voice.chosen_indices,
                ablated_weights,
            )
        voice_records.append(
            {
                "voice": voice_name,
                "train_opportunities": train_voice.size,
                "validation_opportunities": validation_voice.size,
                "baseline_feature_count": baseline_feature_count,
                "baseline_train_nll": baseline_train_nll,
                "baseline_validation_nll": baseline_validation_nll,
                "full_train_nll": full_train_nll,
                "full_validation_nll": full_validation_nll,
                "rule_weights": {
                    rule_id: float(weight)
                    for rule_id, weight in zip(
                        RULE_IDS, rule_weights, strict=True
                    )
                },
                "ablated_validation_nll": ablated_validation_nll,
                "baseline_fit": baseline_fit,
                "full_fit": full_fit,
            }
        )

    baseline_train_nll = combined_nll(
        voice_records, "baseline_train_nll", "train_opportunities"
    )
    baseline_validation_nll = combined_nll(
        voice_records,
        "baseline_validation_nll",
        "validation_opportunities",
    )
    full_train_nll = combined_nll(
        voice_records, "full_train_nll", "train_opportunities"
    )
    full_validation_nll = combined_nll(
        voice_records, "full_validation_nll", "validation_opportunities"
    )
    total_validation = sum(
        record["validation_opportunities"] for record in voice_records
    )
    ablation_records = []
    for rule_id in RULE_IDS:
        ablated_nll = sum(
            record["ablated_validation_nll"][rule_id]
            * record["validation_opportunities"]
            for record in voice_records
        ) / total_validation
        ablation_records.append(
            {
                "rule_id": rule_id,
                "ablated_validation_nll": ablated_nll,
                "validation_nll_penalty": ablated_nll - full_validation_nll,
            }
        )
    ablation_records.sort(
        key=lambda record: record["validation_nll_penalty"], reverse=True
    )
    return {
        "voice_models": voice_records,
        "baseline_train_nll": baseline_train_nll,
        "baseline_validation_nll": baseline_validation_nll,
        "full_train_nll": full_train_nll,
        "full_validation_nll": full_validation_nll,
        "validation_nll_gain": baseline_validation_nll - full_validation_nll,
        "fixed_weight_zeroing_ablation": ablation_records,
    }


def markdown_report(result: dict[str, Any]) -> str:
    model = result["model"]
    corpus = result["corpus"]
    lines = [
        "# POC V2.4 — ablation conjointe du catalogue SATB",
        "",
        "## Protocole",
        "",
        (
            f"- Train : {corpus['train_pieces']} chorals / "
            f"{corpus['train_opportunities']} décisions."
        ),
        (
            f"- Validation : {corpus['validation_pieces']} chorals / "
            f"{corpus['validation_opportunities']} décisions."
        ),
        f"- Test réservé : {corpus['test_pieces_reserved']} chorals, non ouvert.",
        (
            "- Contrôle nul : choix mélangés par choral et par voix."
            if result["experiment"]["null_shuffle"]
            else "- Données authentiques."
        ),
        "- Sept règles lisibles sont ajustées conjointement.",
        "",
        "## Gain conjoint",
        "",
        "| Modèle | NLL train | NLL validation |",
        "|---|---:|---:|",
        (
            f"| Socle de nuisance | {model['baseline_train_nll']:.6f} | "
            f"{model['baseline_validation_nll']:.6f} |"
        ),
        (
            f"| Socle + sept règles | {model['full_train_nll']:.6f} | "
            f"{model['full_validation_nll']:.6f} |"
        ),
        "",
        f"Gain NLL validation : `{model['validation_nll_gain']:.6f}`.",
        "",
        "## Poids par voix",
        "",
        "| Règle | Soprano | Alto | Ténor | Basse |",
        "|---|---:|---:|---:|---:|",
    ]
    by_voice = {
        record["voice"]: record for record in model["voice_models"]
    }
    for rule_id in RULE_IDS:
        weights = [
            by_voice[voice]["rule_weights"][rule_id]
            for voice in satb.VOICE_NAMES
        ]
        lines.append(
            f"| `{rule_id}` | {weights[0]:.3f} | {weights[1]:.3f} | "
            f"{weights[2]:.3f} | {weights[3]:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Ablation par neutralisation d'un poids",
            "",
            "Les autres poids restent fixes : cette mesure isole l'information",
            "portée par chaque colonne dans le modèle conjoint.",
            "",
            "| Règle neutralisée | NLL validation | Pénalité |",
            "|---|---:|---:|",
        ]
    )
    for record in model["fixed_weight_zeroing_ablation"]:
        lines.append(
            f"| `{record['rule_id']}` | "
            f"{record['ablated_validation_nll']:.6f} | "
            f"{record['validation_nll_penalty']:+.6f} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
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
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--output-stem", default="v2_4_satb_ablation")
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
    cache_path = work / f"satb-opportunities-{cache_suffix}.npz"
    if cache_path.exists():
        print(f"[satb-corpus] loading cache {cache_path}", flush=True)
        all_opportunities = satb.load_satb_opportunities(cache_path)
    else:
        score_paths = base.materialize_scores(archive, selected_pieces, work / "scores")
        all_opportunities = satb.build_satb_opportunities(score_paths)
        satb.save_satb_opportunities(cache_path, all_opportunities)

    available = set(np.concatenate([data.piece_ids for data in all_opportunities]))
    train_ids = [piece for piece in splits["train"] if piece in available]
    validation_ids = [piece for piece in splits["validation"] if piece in available]
    if args.max_pieces is not None and not validation_ids:
        smoke_ids = sorted(available)
        split_at = max(1, int(0.8 * len(smoke_ids)))
        train_ids, validation_ids = smoke_ids[:split_at], smoke_ids[split_at:]
    train = [satb.subset_for_piece_ids(data, train_ids) for data in all_opportunities]
    validation = [
        satb.subset_for_piece_ids(data, validation_ids)
        for data in all_opportunities
    ]
    if args.null_shuffle:
        train = [
            satb.shuffle_choices_within_pieces(data, args.seed + 101 + voice)
            for voice, data in enumerate(train)
        ]
        validation = [
            satb.shuffle_choices_within_pieces(data, args.seed + 202 + voice)
            for voice, data in enumerate(validation)
        ]

    model = fit_joint_catalogue(
        train,
        validation,
        args.l1,
        args.max_steps,
        args.learning_rate,
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v2_4_joint_ablation",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "rule_ids": list(RULE_IDS),
            "ablation_kind": "fixed_fitted_weight_zeroing",
            "split_strategy": split_metadata["strategy"],
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
        },
        "corpus": {
            "pieces_total": len(available),
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "train_opportunities": sum(data.size for data in train),
            "validation_opportunities": sum(data.size for data in validation),
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
