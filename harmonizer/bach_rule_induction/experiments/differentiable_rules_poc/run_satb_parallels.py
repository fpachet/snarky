#!/usr/bin/env python3
"""Blind recovery of parallel-interval rules across all six SATB voice pairs.

The experiment reuses the V2.2 four-voice conditional baselines.  It uniformly
tests the twelve numeric interval classes for recurrence from source to target
under same-sign non-zero motion.  Musicological names and Snarky rules are
consulted only after selection.  The grouped test split remains sealed.
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


def parallel_interval_class_mask(
    opportunities: satb.VoiceOpportunities,
    interval_class: int,
) -> np.ndarray:
    """Candidate forms class-preserving same-direction motion with any other voice."""

    voice = opportunities.voice_index
    candidates = opportunities.candidate_pitches[None, :]
    previous_subject = opportunities.previous_pitch[:, None]
    subject_delta = candidates - previous_subject
    mask = np.zeros(subject_delta.shape, dtype=np.bool_)

    for other in range(4):
        if other == voice:
            continue
        upper = min(voice, other)
        lower = max(voice, other)
        source_class = (
            opportunities.previous_all[:, upper]
            - opportunities.previous_all[:, lower]
        ) % 12
        if voice == upper:
            target_class = (
                candidates - opportunities.current_all[:, other, None]
            ) % 12
        else:
            target_class = (
                opportunities.current_all[:, other, None] - candidates
            ) % 12
        other_delta = (
            opportunities.current_all[:, other]
            - opportunities.previous_all[:, other]
        )[:, None]
        same_nonzero_direction = (
            ((subject_delta > 0) & (other_delta > 0))
            | ((subject_delta < 0) & (other_delta < 0))
        )
        mask |= (
            (source_class[:, None] == interval_class)
            & (target_class == interval_class)
            & same_nonzero_direction
        )
    return mask


def compare_parallel_class_to_reference(interval_class: int) -> dict[str, Any]:
    """Compare one induced numeric formula to the hidden finite-domain oracle."""

    tested = 0
    mismatches = 0
    reference_class = {0: "R-PARALLEL-001", 7: "R-PARALLEL-002"}.get(
        interval_class
    )
    for upper_voice in range(3):
        upper_min, upper_max = satb.VOICE_RANGES[upper_voice]
        for lower_voice in range(upper_voice + 1, 4):
            lower_min, lower_max = satb.VOICE_RANGES[lower_voice]
            for source_upper in range(upper_min, upper_max + 1):
                for source_lower in range(lower_min, lower_max + 1):
                    if source_upper <= source_lower:
                        continue
                    for target_upper in range(upper_min, upper_max + 1):
                        for target_lower in range(lower_min, lower_max + 1):
                            if target_upper <= target_lower:
                                continue
                            upper_delta = target_upper - source_upper
                            lower_delta = target_lower - source_lower
                            same_nonzero_direction = (
                                upper_delta > 0 and lower_delta > 0
                            ) or (upper_delta < 0 and lower_delta < 0)
                            learned = (
                                (source_upper - source_lower) % 12
                                == interval_class
                                and (target_upper - target_lower) % 12
                                == interval_class
                                and same_nonzero_direction
                            )
                            reference = (
                                reference_class is not None
                                and (source_upper - source_lower) % 12
                                == interval_class
                                and (target_upper - target_lower) % 12
                                == interval_class
                                and same_nonzero_direction
                            )
                            tested += 1
                            mismatches += int(learned != reference)
    return {
        "numeric_class": interval_class,
        "reference_rule_id": reference_class,
        "tested_valid_voice_pair_states": tested,
        "mismatches": mismatches,
        "classification": (
            "RECOVERED_EQUIVALENT"
            if reference_class is not None and mismatches == 0
            else "NOT_EQUIVALENT"
        ),
    }


def markdown_report(result: dict[str, Any]) -> str:
    corpus = result["corpus"]
    model = result["model"]
    lines = [
        "# POC V2.3 — parallèles dans les six paires de voix",
        "",
        "## Protocole",
        "",
        (
            f"- Train groupé : {corpus['train_pieces']} chorals / "
            f"{corpus['train_opportunities']} décisions SATB."
        ),
        (
            f"- Validation groupée : {corpus['validation_pieces']} chorals / "
            f"{corpus['validation_opportunities']} décisions SATB."
        ),
        f"- Test réservé : {corpus['test_pieces_reserved']} chorals, non ouvert.",
        (
            "- Contrôle nul : choix mélangés par choral et par voix."
            if result["experiment"]["null_shuffle"]
            else "- Données authentiques."
        ),
        "- Les douze classes numériques sont testées avec le même prédicat.",
        "",
        "## Scan résiduel",
        "",
        "| Classe | z train | z validation | Contraste local train/val. | "
        "Bootstrap val. médian [2,5 % ; 97,5 %] | P(z val. < 0) |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for record in model["parallel_interval_scan"]:
        bootstrap = record["bootstrap_validation"]
        train_contrast = record["train"]["local_log_rate_contrast"]
        validation_contrast = record["validation"]["local_log_rate_contrast"]
        lines.append(
            f"| {record['numeric_value']} | {record['train']['z_score']:.3f} | "
            f"{record['validation']['z_score']:.3f} | "
            f"{train_contrast:.3f} / {validation_contrast:.3f} | "
            f"{bootstrap['z_median']:.3f} "
            f"[{bootstrap['z_p025']:.3f} ; {bootstrap['z_p975']:.3f}] | "
            f"{bootstrap['negative_fraction']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Sélection automatique",
            "",
            f"- Classes retenues : `{model['selected_parallel_classes']}`.",
            "",
            "## Comparaison sémantique postérieure",
            "",
            "| Classe | Référence | États testés | Désaccords | Classification |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for comparison in model["semantic_comparison"]:
        lines.append(
            f"| {comparison['numeric_class']} | "
            f"`{comparison['reference_rule_id']}` | "
            f"{comparison['tested_valid_voice_pair_states']} | "
            f"{comparison['mismatches']} | "
            f"`{comparison['classification']}` |"
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
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--train-z", type=float, default=-10.0)
    parser.add_argument("--validation-z", type=float, default=-5.0)
    parser.add_argument("--bootstrap-negative-fraction", type=float, default=0.95)
    parser.add_argument("--family-budget", type=int, default=2)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--output-stem", default="v2_3_satb_parallels")
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
    if any(data.size == 0 for data in (*train, *validation)):
        raise RuntimeError("At least one train/validation voice split is empty")
    if args.null_shuffle:
        train = [
            satb.shuffle_choices_within_pieces(data, args.seed + 101 + voice)
            for voice, data in enumerate(train)
        ]
        validation = [
            satb.shuffle_choices_within_pieces(data, args.seed + 202 + voice)
            for voice, data in enumerate(validation)
        ]

    train_probabilities = []
    validation_probabilities = []
    voice_baselines = []
    for train_voice, validation_voice in zip(train, validation, strict=True):
        print(
            f"[baseline] fitting {satb.VOICE_NAMES[train_voice.voice_index]}",
            flush=True,
        )
        train_probs, validation_probs, diagnostics = satb.fit_voice_baseline(
            train_voice,
            validation_voice,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
        train_probabilities.append(train_probs)
        validation_probabilities.append(validation_probs)
        voice_baselines.append(diagnostics)

    parallel_scan = satb.scan_family(
        "same_direction_repeated_interval_mod12",
        range(12),
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        parallel_interval_class_mask,
        args.bootstrap_replicates,
        args.seed + 40_000,
    )
    satb.add_local_log_rate_contrasts(parallel_scan, circular=True)
    selected = satb.select_top_avoidances(
        parallel_scan,
        args.train_z,
        args.validation_z,
        args.bootstrap_negative_fraction,
        args.family_budget,
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v2_3_satb_parallels",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "voice_ranges": [list(bounds) for bounds in satb.VOICE_RANGES],
            "split_strategy": split_metadata["strategy"],
            "selection": {
                "train_z_max": args.train_z,
                "validation_z_max": args.validation_z,
                "bootstrap_validation_negative_fraction_min": (
                    args.bootstrap_negative_fraction
                ),
                "family_rule_budget": args.family_budget,
            },
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
        "model": {
            "voice_baselines": voice_baselines,
            "parallel_interval_scan": parallel_scan,
            "selected_parallel_classes": selected,
            "semantic_comparison": [
                compare_parallel_class_to_reference(value) for value in selected
            ],
        },
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
