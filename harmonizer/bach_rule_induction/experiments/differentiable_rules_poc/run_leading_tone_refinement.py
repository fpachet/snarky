#!/usr/bin/env python3
"""Mine short numeric refinements of the global leading-tone tendency.

The fixed premise is the V3.1 numeric source class 11.  The search uniformly
enumerates subject voice and the tonic-relative source/target bass classes,
then evaluates the upward-semitone conclusion with the conditional residual.
Musicological interpretations are attached only after numeric selection.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base
import run_satb_level_a as satb
import run_tonal_tendency as tonal


def refinement_mask(
    opportunities: satb.VoiceOpportunities,
    *,
    subject_voice: int,
    source_bass_class: int,
    target_bass_class: int,
    tonic_by_piece: dict[str, int],
    required_mode: str | None = None,
    mode_by_piece: dict[str, str] | None = None,
) -> np.ndarray:
    shape = (opportunities.size, opportunities.candidate_pitches.size)
    if opportunities.voice_index != subject_voice or subject_voice == 3:
        return np.zeros(shape, dtype=np.bool_)
    tonics = np.asarray(
        [tonic_by_piece[piece_id] for piece_id in opportunities.piece_ids],
        dtype=np.int16,
    )
    source_subject_class = (opportunities.previous_pitch - tonics) % 12
    source_bass = (opportunities.previous_all[:, 3] - tonics) % 12
    target_bass = (opportunities.current_all[:, 3] - tonics) % 12
    context = (
        (source_subject_class == 11)
        & (source_bass == source_bass_class)
        & (target_bass == target_bass_class)
    )
    if required_mode is not None:
        if mode_by_piece is None:
            raise ValueError("mode_by_piece is required for mode stratification")
        modes = np.asarray(
            [mode_by_piece[piece_id] for piece_id in opportunities.piece_ids]
        )
        context &= modes == required_mode
    candidates = opportunities.candidate_pitches[None, :]
    conclusion = candidates == opportunities.previous_pitch[:, None] + 1
    return context[:, None] & conclusion


def context_masks(
    datasets: list[satb.VoiceOpportunities],
    subject_voice: int,
    source_bass_class: int,
    target_bass_class: int,
    tonic_by_piece: dict[str, int],
    required_mode: str | None = None,
    mode_by_piece: dict[str, str] | None = None,
) -> list[np.ndarray]:
    return [
        refinement_mask(
            data,
            subject_voice=subject_voice,
            source_bass_class=source_bass_class,
            target_bass_class=target_bass_class,
            tonic_by_piece=tonic_by_piece,
            required_mode=required_mode,
            mode_by_piece=mode_by_piece,
        )
        for data in datasets
    ]


def scan_refinements(
    train: list[satb.VoiceOpportunities],
    validation: list[satb.VoiceOpportunities],
    train_probabilities: list[np.ndarray],
    validation_probabilities: list[np.ndarray],
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
    stratify_mode: bool,
) -> list[dict[str, Any]]:
    records = []
    modes: tuple[str | None, ...] = (
        ("major", "minor") if stratify_mode else (None,)
    )
    for required_mode in modes:
        for subject_voice in range(3):
            for source_bass_class in range(12):
                for target_bass_class in range(12):
                    train_masks = context_masks(
                        train,
                        subject_voice,
                        source_bass_class,
                        target_bass_class,
                        tonic_by_piece,
                        required_mode,
                        mode_by_piece,
                    )
                    validation_masks = context_masks(
                        validation,
                        subject_voice,
                        source_bass_class,
                        target_bass_class,
                        tonic_by_piece,
                        required_mode,
                        mode_by_piece,
                    )
                    records.append(
                        {
                            "mode": required_mode or "all",
                            "subject_voice_index": subject_voice,
                            "subject_voice": satb.VOICE_NAMES[subject_voice],
                            "source_bass_class": source_bass_class,
                            "target_bass_class": target_bass_class,
                            "train": satb.serialize_evidence(
                                satb.aggregate_evidence(
                                    train, train_probabilities, train_masks
                                )
                            ),
                            "validation": satb.serialize_evidence(
                                satb.aggregate_evidence(
                                    validation,
                                    validation_probabilities,
                                    validation_masks,
                                )
                            ),
                        }
                    )
    return records


def select_refinements(
    records: list[dict[str, Any]],
    min_train_support: int,
    min_validation_support: int,
    min_train_confirmation: float,
    min_validation_confirmation: float,
    min_train_z: float,
    min_validation_z: float,
    budget: int,
) -> list[dict[str, Any]]:
    selected = [
        record
        for record in records
        if record["train"]["testable_opportunities"] >= min_train_support
        and record["validation"]["testable_opportunities"]
        >= min_validation_support
        and record["train"]["observed_rate"] >= min_train_confirmation
        and record["validation"]["observed_rate"]
        >= min_validation_confirmation
        and record["train"]["z_score"] >= min_train_z
        and record["validation"]["z_score"] >= min_validation_z
    ]
    selected.sort(
        key=lambda record: (
            min(
                record["train"]["observed_rate"],
                record["validation"]["observed_rate"],
            ),
            record["train"]["z_score"] ** 2
            + record["validation"]["z_score"] ** 2,
        ),
        reverse=True,
    )
    return selected[:budget]


def candidate_identity(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": record["mode"],
        "subject_voice_index": record["subject_voice_index"],
        "subject_voice": record["subject_voice"],
        "source_bass_class": record["source_bass_class"],
        "target_bass_class": record["target_bass_class"],
    }


def family_calibration_summary(
    records: list[dict[str, Any]],
    min_train_support: int,
    min_validation_support: int,
    min_train_confirmation: float,
    min_validation_confirmation: float,
    min_train_z: float,
    min_validation_z: float,
) -> dict[str, Any]:
    """Summarize the maximum joint statistic searched across the whole family."""

    supported = [
        record
        for record in records
        if record["train"]["testable_opportunities"] >= min_train_support
        and record["validation"]["testable_opportunities"]
        >= min_validation_support
    ]
    confirmation_gated = [
        record
        for record in supported
        if record["train"]["observed_rate"] >= min_train_confirmation
        and record["validation"]["observed_rate"]
        >= min_validation_confirmation
    ]
    threshold_passing = [
        record
        for record in confirmation_gated
        if record["train"]["z_score"] >= min_train_z
        and record["validation"]["z_score"] >= min_validation_z
    ]

    def maximum(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        record = max(
            rows,
            key=lambda item: min(
                item["train"]["z_score"],
                item["validation"]["z_score"],
            ),
        )
        return {
            **candidate_identity(record),
            "joint_min_z": min(
                record["train"]["z_score"],
                record["validation"]["z_score"],
            ),
            "train_z": record["train"]["z_score"],
            "validation_z": record["validation"]["z_score"],
            "train_observed_rate": record["train"]["observed_rate"],
            "validation_observed_rate": record["validation"]["observed_rate"],
        }

    return {
        "statistic": "min(train_residual_z, validation_residual_z)",
        "candidate_count": len(records),
        "supported_candidate_count": len(supported),
        "confirmation_gated_candidate_count": len(confirmation_gated),
        "threshold_passing_candidate_count": len(threshold_passing),
        "maximum_supported": maximum(supported),
        "maximum_confirmation_gated": maximum(confirmation_gated),
    }


def interpretation(record: dict[str, Any]) -> str:
    triple = (
        record["subject_voice_index"],
        record["source_bass_class"],
        record["target_bass_class"],
    )
    if triple == (0, 7, 0):
        return "OUTER_DOMINANT_TO_TONIC_CADENTIAL_PROXY"
    if triple == (1, 2, 0):
        return "LEADING_TONE_CHORD_6_TO_TONIC_ROOT_PROXY"
    if triple == (1, 2, 4):
        return "LEADING_TONE_CHORD_6_TO_TONIC_6_PROXY"
    if triple == (2, 5, 4) and record["mode"] == "major":
        return "DOMINANT_SEVENTH_42_TO_TONIC_6_PROXY"
    if triple == (2, 7, 8) and record["mode"] == "minor":
        return "MINOR_DECEPTIVE_CADENCE_PROXY"
    if triple == (1, 7, 3) and record["mode"] == "minor":
        return "MINOR_DOMINANT_TO_MEDIANT_DECEPTIVE_PROXY"
    return "UNINTERPRETED_NUMERIC_REFINEMENT"


def audit_selected_cases(
    records: list[dict[str, Any]],
    datasets: list[satb.VoiceOpportunities],
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
    split_name: str,
    example_limit: int = 3,
) -> None:
    """Attach mode counts and traceable examples after selection."""

    for record in records:
        data = datasets[record["subject_voice_index"]]
        tonics = np.asarray(
            [tonic_by_piece[piece_id] for piece_id in data.piece_ids],
            dtype=np.int16,
        )
        context = (
            ((data.previous_pitch - tonics) % 12 == 11)
            & (
                (data.previous_all[:, 3] - tonics) % 12
                == record["source_bass_class"]
            )
            & (
                (data.current_all[:, 3] - tonics) % 12
                == record["target_bass_class"]
            )
            & (data.previous_pitch < data.candidate_max)
        )
        if record["mode"] != "all":
            modes = np.asarray(
                [mode_by_piece[piece_id] for piece_id in data.piece_ids]
            )
            context &= modes == record["mode"]
        indices = np.flatnonzero(context)
        resolved = data.chosen_pitch == data.previous_pitch + 1
        mode_counts: dict[str, Counter[str]] = {}
        for index in indices:
            mode = mode_by_piece[str(data.piece_ids[index])]
            counts = mode_counts.setdefault(mode, Counter())
            counts["opportunities"] += 1
            counts["resolutions" if resolved[index] else "exceptions"] += 1
        record[f"{split_name}_by_mode"] = {
            mode: {
                "opportunities": counts["opportunities"],
                "resolutions": counts["resolutions"],
                "exceptions": counts["exceptions"],
                "resolution_rate": (
                    counts["resolutions"] / counts["opportunities"]
                    if counts["opportunities"]
                    else 0.0
                ),
            }
            for mode, counts in sorted(mode_counts.items())
        }

        if example_limit <= 0:
            continue
        examples: list[dict[str, Any]] = []
        for outcome in (True, False):
            outcome_indices = indices[resolved[indices] == outcome][:example_limit]
            for index in outcome_indices:
                tonic = int(tonics[index])
                examples.append(
                    {
                        "piece_id": str(data.piece_ids[index]),
                        "mode": mode_by_piece[str(data.piece_ids[index])],
                        "offset_previous": float(data.offsets_previous[index]),
                        "offset_current": float(data.offsets_current[index]),
                        "resolved": bool(outcome),
                        "source_satb_midi": [
                            int(value) for value in data.previous_all[index]
                        ],
                        "target_satb_midi": [
                            int(value) for value in data.current_all[index]
                        ],
                        "source_satb_relative_classes": [
                            int((value - tonic) % 12)
                            for value in data.previous_all[index]
                        ],
                        "target_satb_relative_classes": [
                            int((value - tonic) % 12)
                            for value in data.current_all[index]
                        ],
                    }
                )
        record[f"{split_name}_examples"] = examples


def add_bootstrap(
    records: list[dict[str, Any]],
    train: list[satb.VoiceOpportunities],
    validation: list[satb.VoiceOpportunities],
    train_probabilities: list[np.ndarray],
    validation_probabilities: list[np.ndarray],
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
    replicates: int,
    seed: int,
) -> None:
    for index, record in enumerate(records):
        train_masks = context_masks(
            train,
            record["subject_voice_index"],
            record["source_bass_class"],
            record["target_bass_class"],
            tonic_by_piece,
            None if record["mode"] == "all" else record["mode"],
            mode_by_piece,
        )
        validation_masks = context_masks(
            validation,
            record["subject_voice_index"],
            record["source_bass_class"],
            record["target_bass_class"],
            tonic_by_piece,
            None if record["mode"] == "all" else record["mode"],
            mode_by_piece,
        )
        record["bootstrap_train"] = satb.bootstrap_by_piece(
            train,
            train_probabilities,
            train_masks,
            replicates,
            seed + 2 * index,
        )
        record["bootstrap_validation"] = satb.bootstrap_by_piece(
            validation,
            validation_probabilities,
            validation_masks,
            replicates,
            seed + 2 * index + 1,
        )
        record["interpretation"] = interpretation(record)


def markdown_report(result: dict[str, Any]) -> str:
    model = result["model"]
    version = "V3.3" if result["experiment"]["mode_stratified"] else "V3.2"
    lines = [
        f"# POC {version} — raffinements de la résolution de la sensible",
        "",
        "## Protocole",
        "",
        "- Prémisse fixe : classe source relative à la tonique `11`.",
        "- Conclusion : mouvement ascendant exact d'un demi-ton.",
        (
            "- Contextes énumérés : mode × voix × classe de basse source × "
            "classe de basse cible."
            if result["experiment"]["mode_stratified"]
            else "- Contextes énumérés : voix × classe de basse source × "
            "classe de basse cible."
        ),
        f"- {result['experiment']['candidate_count']} contextes numériques "
        "testés uniformément.",
        "- Le test final reste scellé.",
        (
            "- Contrôle nul par permutation."
            if result["experiment"]["null_shuffle"]
            else "- Chorals authentiques."
        ),
        "",
        "## Raffinements retenus",
        "",
        "| Mode | Voix | Basse | Support train/val. | Confirmation train/val. | "
        "z train/val. | Bootstrap val. médian [95 %] | Interprétation |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for record in model["selected_refinements"]:
        bootstrap = record["bootstrap_validation"]
        lines.append(
            f"| {record['mode']} | {record['subject_voice']} | "
            f"{record['source_bass_class']}→{record['target_bass_class']} | "
            f"{record['train']['testable_opportunities']}/"
            f"{record['validation']['testable_opportunities']} | "
            f"{record['train']['observed_rate']:.3f}/"
            f"{record['validation']['observed_rate']:.3f} | "
            f"{record['train']['z_score']:.3f}/"
            f"{record['validation']['z_score']:.3f} | "
            f"{bootstrap['z_median']:.3f} "
            f"[{bootstrap['z_p025']:.3f} ; {bootstrap['z_p975']:.3f}] | "
            f"`{record['interpretation']}` |"
        )
        mode_summary = "; ".join(
            f"{mode}: train "
            f"{record['train_by_mode'].get(mode, {}).get('resolutions', 0)}/"
            f"{record['train_by_mode'].get(mode, {}).get('opportunities', 0)}, "
            f"val. "
            f"{record['validation_by_mode'].get(mode, {}).get('resolutions', 0)}/"
            f"{record['validation_by_mode'].get(mode, {}).get('opportunities', 0)}"
            for mode in sorted(
                set(record["train_by_mode"]) | set(record["validation_by_mode"])
            )
        )
        lines.append(
            f"| ↳ audit | — | — | — | — | — | — | {mode_summary or '—'} |"
        )
    if not model["selected_refinements"]:
        lines.append("| — | — | — | — | — | — | — | AUCUN |")
    lines.extend(
        [
            "",
            "Ces résultats restent des raffinements candidats malgré le contrôle",
            "nul et l'audit des exemples. Une calibration familiale répétée et",
            "une analyse harmonique indépendante précèdent le statut `SUPPORTED`.",
            "",
        ]
    )
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
    parser.add_argument("--min-train-support", type=int, default=30)
    parser.add_argument("--min-validation-support", type=int, default=8)
    parser.add_argument("--min-train-confirmation", type=float, default=0.65)
    parser.add_argument("--min-validation-confirmation", type=float, default=0.65)
    parser.add_argument("--min-train-z", type=float, default=3.0)
    parser.add_argument("--min-validation-z", type=float, default=2.0)
    parser.add_argument("--candidate-budget", type=int, default=5)
    parser.add_argument("--stratify-mode", action="store_true")
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--output-stem", default="v3_2_leading_tone_refinement")
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
    score_paths = base.materialize_scores(archive, selected_pieces, work / "scores")
    cache_path = work / f"satb-opportunities-{cache_suffix}.npz"
    all_opportunities = satb.load_satb_opportunities(cache_path)
    tonic_by_piece, mode_by_piece, tonal_audit = tonal.build_tonal_status_maps(
        score_paths
    )

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

    train_probabilities = []
    validation_probabilities = []
    for train_voice, validation_voice in zip(train, validation, strict=True):
        print(
            f"[baseline] fitting {satb.VOICE_NAMES[train_voice.voice_index]}",
            flush=True,
        )
        train_probs, validation_probs, _ = satb.fit_voice_baseline(
            train_voice,
            validation_voice,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
        train_probabilities.append(train_probs)
        validation_probabilities.append(validation_probs)

    scan = scan_refinements(
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        tonic_by_piece,
        mode_by_piece,
        args.stratify_mode,
    )
    selected = select_refinements(
        scan,
        args.min_train_support,
        args.min_validation_support,
        args.min_train_confirmation,
        args.min_validation_confirmation,
        args.min_train_z,
        args.min_validation_z,
        args.candidate_budget,
    )
    add_bootstrap(
        selected,
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        tonic_by_piece,
        mode_by_piece,
        args.bootstrap_replicates,
        args.seed + 60_000,
    )
    audit_selected_cases(
        selected,
        train,
        tonic_by_piece,
        mode_by_piece,
        "train",
        example_limit=0,
    )
    audit_selected_cases(
        selected,
        validation,
        tonic_by_piece,
        mode_by_piece,
        "validation",
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": (
                "differentiable_rules_poc_v3_3_mode_stratified_refinement"
                if args.stratify_mode
                else "differentiable_rules_poc_v3_2_leading_tone_refinement"
            ),
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "split_strategy": split_metadata["strategy"],
            "candidate_count": len(scan),
            "mode_stratified": args.stratify_mode,
            "selection": {
                "min_train_support": args.min_train_support,
                "min_validation_support": args.min_validation_support,
                "min_train_confirmation": args.min_train_confirmation,
                "min_validation_confirmation": args.min_validation_confirmation,
                "min_train_z": args.min_train_z,
                "min_validation_z": args.min_validation_z,
                "candidate_budget": args.candidate_budget,
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
        "tonal_status_audit": tonal_audit,
        "corpus": {
            "pieces_total": len(available),
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "test_opened": False,
        },
        "model": {
            "selected_refinements": selected,
            "all_candidate_count": len(scan),
            "family_calibration": family_calibration_summary(
                scan,
                args.min_train_support,
                args.min_validation_support,
                args.min_train_confirmation,
                args.min_validation_confirmation,
                args.min_train_z,
                args.min_validation_z,
            ),
            "reference_rule_id": "R-LEADING-001",
            "semantic_status": "CANDIDATE_REFINEMENT",
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
