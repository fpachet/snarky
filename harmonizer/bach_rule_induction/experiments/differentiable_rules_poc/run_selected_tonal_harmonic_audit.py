#!/usr/bin/env python3
"""Audit full SATB pitch-class content behind family-calibrated tonal clauses."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base
import run_satb_level_a as satb
import run_tonal_tendency as tonal

HARMONIC_HYPOTHESES = {
    "LEADING_TONE_CHORD_6_TO_TONIC_6_PROXY": {
        "source_relative_pitch_class_set": [2, 5, 11],
        "target_relative_pitch_class_set": [0, 4, 7],
        "posthoc_label": "vii°6_to_I6",
    }
}


def relative_pitch_class_signature(
    pitches: np.ndarray,
    tonic: int,
) -> tuple[int, ...]:
    return tuple(sorted({int((pitch - tonic) % 12) for pitch in pitches}))


def selected_context_indices(
    data: satb.VoiceOpportunities,
    candidate: dict[str, Any],
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
) -> np.ndarray:
    tonics = np.asarray(
        [tonic_by_piece[piece_id] for piece_id in data.piece_ids],
        dtype=np.int16,
    )
    modes = np.asarray([mode_by_piece[piece_id] for piece_id in data.piece_ids])
    context = (
        (modes == candidate["mode"])
        & ((data.previous_pitch - tonics) % 12 == 11)
        & (
            (data.previous_all[:, 3] - tonics) % 12
            == candidate["source_bass_class"]
        )
        & (
            (data.current_all[:, 3] - tonics) % 12
            == candidate["target_bass_class"]
        )
        & (data.previous_pitch < data.candidate_max)
    )
    return np.flatnonzero(context)


def signature_rows(
    data: satb.VoiceOpportunities,
    indices: np.ndarray,
    tonic_by_piece: dict[str, int],
    expected_source: tuple[int, ...],
    expected_target: tuple[int, ...],
) -> list[dict[str, Any]]:
    rows = []
    for index in indices:
        piece_id = str(data.piece_ids[index])
        tonic = tonic_by_piece[piece_id]
        source_signature = relative_pitch_class_signature(
            data.previous_all[index],
            tonic,
        )
        target_signature = relative_pitch_class_signature(
            data.current_all[index],
            tonic,
        )
        source_matches = source_signature == expected_source
        target_matches = target_signature == expected_target
        rows.append(
            {
                "piece_id": piece_id,
                "offset_previous": float(data.offsets_previous[index]),
                "offset_current": float(data.offsets_current[index]),
                "resolved": bool(
                    data.chosen_pitch[index] == data.previous_pitch[index] + 1
                ),
                "source_signature": list(source_signature),
                "target_signature": list(target_signature),
                "source_matches_hypothesis": source_matches,
                "target_matches_hypothesis": target_matches,
                "progression_matches_hypothesis": source_matches and target_matches,
                "source_satb_relative_classes": [
                    int((pitch - tonic) % 12)
                    for pitch in data.previous_all[index]
                ],
                "target_satb_relative_classes": [
                    int((pitch - tonic) % 12)
                    for pitch in data.current_all[index]
                ],
            }
        )
    return rows


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def fisher_exact_greater(
    exact_resolutions: int,
    exact_exceptions: int,
    nonexact_resolutions: int,
    nonexact_exceptions: int,
) -> float:
    """One-sided Fisher exact p for a higher resolution rate in exact rows."""

    population = (
        exact_resolutions
        + exact_exceptions
        + nonexact_resolutions
        + nonexact_exceptions
    )
    successes = exact_resolutions + nonexact_resolutions
    draws = exact_resolutions + exact_exceptions
    denominator = math.comb(population, draws)
    upper = min(successes, draws)
    probability = 0.0
    for value in range(exact_resolutions, upper + 1):
        failures_drawn = draws - value
        if failures_drawn > population - successes:
            continue
        probability += (
            math.comb(successes, value)
            * math.comb(population - successes, failures_drawn)
            / denominator
        )
    return probability


def summarize_rows(rows: list[dict[str, Any]], example_limit: int = 5) -> dict:
    source_matches = sum(row["source_matches_hypothesis"] for row in rows)
    target_matches = sum(row["target_matches_hypothesis"] for row in rows)
    progression_matches = sum(
        row["progression_matches_hypothesis"] for row in rows
    )
    resolved = sum(row["resolved"] for row in rows)
    exact_rows = [row for row in rows if row["progression_matches_hypothesis"]]
    nonexact_rows = [
        row for row in rows if not row["progression_matches_hypothesis"]
    ]
    exact_resolutions = sum(row["resolved"] for row in exact_rows)
    nonexact_resolutions = sum(row["resolved"] for row in nonexact_rows)
    exact_exceptions = len(exact_rows) - exact_resolutions
    nonexact_exceptions = len(nonexact_rows) - nonexact_resolutions
    progressions = Counter(
        (tuple(row["source_signature"]), tuple(row["target_signature"]))
        for row in rows
    )
    return {
        "opportunities": len(rows),
        "piece_support": len({row["piece_id"] for row in rows}),
        "resolutions": resolved,
        "exceptions": len(rows) - resolved,
        "resolution_rate": ratio(resolved, len(rows)),
        "source_signature_matches": source_matches,
        "source_signature_match_rate": ratio(source_matches, len(rows)),
        "target_signature_matches": target_matches,
        "target_signature_match_rate": ratio(target_matches, len(rows)),
        "exact_progression_matches": progression_matches,
        "exact_progression_match_rate": ratio(progression_matches, len(rows)),
        "exact_progression_resolutions": exact_resolutions,
        "exact_progression_exceptions": exact_exceptions,
        "exact_progression_resolution_rate": ratio(
            exact_resolutions,
            len(exact_rows),
        ),
        "nonexact_progression_resolutions": nonexact_resolutions,
        "nonexact_progression_exceptions": nonexact_exceptions,
        "nonexact_progression_resolution_rate": ratio(
            nonexact_resolutions,
            len(nonexact_rows),
        ),
        "exact_vs_nonexact_fisher_greater_p": fisher_exact_greater(
            exact_resolutions,
            exact_exceptions,
            nonexact_resolutions,
            nonexact_exceptions,
        ),
        "distinct_progression_signatures": len(progressions),
        "top_progression_signatures": [
            {
                "source_signature": list(source),
                "target_signature": list(target),
                "count": count,
            }
            for (source, target), count in sorted(
                progressions.items(),
                key=lambda item: (-item[1], item[0]),
            )[:10]
        ],
        "examples": rows[:example_limit],
        "exceptions_examples": [
            row for row in rows if not row["resolved"]
        ][:example_limit],
    }


def proxy_classification(
    train_summary: dict[str, Any],
    validation_summary: dict[str, Any],
) -> str:
    if (
        train_summary["exact_progression_match_rate"] >= 0.9
        and validation_summary["exact_progression_match_rate"] >= 0.9
    ):
        return "PITCH_CLASS_PROXY_CONFIRMED"
    if (
        train_summary["exact_progression_match_rate"] >= 0.5
        and validation_summary["exact_progression_match_rate"] >= 0.5
    ):
        return "PITCH_CLASS_PROXY_PARTIAL"
    return "PITCH_CLASS_PROXY_NOT_CONFIRMED"


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# POC V3.5 — audit harmonique de la clause tonale retenue",
        "",
        "## Protocole",
        "",
        "- Entrée : clauses passant la calibration familiale V3.4.",
        "- Audit indépendant : ensembles complets de classes des quatre voix.",
        "- Ces ensembles n'ont pas participé à la sélection V3.1–V3.4.",
        "- Le test final reste scellé.",
        "",
    ]
    for record in result["audits"]:
        candidate = record["candidate"]
        hypothesis = record["harmonic_hypothesis"]
        lines.extend(
            [
                f"## {candidate['mode']} · {candidate['subject_voice']} · "
                f"basse {candidate['source_bass_class']}→"
                f"{candidate['target_bass_class']}",
                "",
                (
                    f"Hypothèse postérieure : `{hypothesis['posthoc_label']}`, "
                    f"source `{hypothesis['source_relative_pitch_class_set']}`, "
                    f"cible `{hypothesis['target_relative_pitch_class_set']}`."
                ),
                "",
                "| Split | Occurrences | Résolutions | Source exacte | "
                "Cible exacte | Progression exacte | Résolution exacte/autre |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for split_name in ("train", "validation"):
            summary = record[split_name]
            lines.append(
                f"| {split_name} | {summary['opportunities']} | "
                f"{summary['resolutions']}/{summary['opportunities']} | "
                f"{summary['source_signature_matches']}/"
                f"{summary['opportunities']} | "
                f"{summary['target_signature_matches']}/"
                f"{summary['opportunities']} | "
                f"{summary['exact_progression_matches']}/"
                f"{summary['opportunities']} | "
                f"{summary['exact_progression_resolutions']}/"
                f"{summary['exact_progression_matches']} vs "
                f"{summary['nonexact_progression_resolutions']}/"
                f"{summary['opportunities'] - summary['exact_progression_matches']} |"
            )
        lines.extend(
            [
                "",
                f"Classification : `{record['classification']}`.",
                (
                    "Fisher unilatéral train, progression exacte contre autres "
                    f"contextes : `p = "
                    f"{record['train']['exact_vs_nonexact_fisher_greater_p']:.6g}`."
                ),
                "",
            ]
        )
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
    parser.add_argument(
        "--calibration-result",
        type=Path,
        default=root / "results/v3_4_tonal_family_calibration.json",
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--results-dir", type=Path, default=root / "results")
    parser.add_argument(
        "--output-stem",
        default="v3_5_selected_tonal_harmonic_audit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
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
    discovery_ids = set(splits["train"] + splits["validation"])
    discovery_pieces = [
        piece for piece in included_pieces if piece["id"] in discovery_ids
    ]
    score_paths = base.materialize_scores(
        archive,
        discovery_pieces,
        root / "work/scores",
    )
    tonic_by_piece, mode_by_piece, tonal_audit = tonal.build_tonal_status_maps(
        score_paths
    )
    all_opportunities = satb.load_satb_opportunities(
        root / "work/satb-opportunities-full.npz"
    )
    train = [
        satb.subset_for_piece_ids(data, splits["train"])
        for data in all_opportunities
    ]
    validation = [
        satb.subset_for_piece_ids(data, splits["validation"])
        for data in all_opportunities
    ]

    calibration_path = args.calibration_result.resolve()
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    retained = [
        record
        for record in calibration["candidate_results"]
        if record["classification"] == "PASSES_EMPIRICAL_FWER_0_05"
    ]
    audits = []
    for candidate in retained:
        hypothesis = HARMONIC_HYPOTHESES.get(candidate["interpretation"])
        if hypothesis is None:
            raise ValueError(
                "No independent harmonic hypothesis for "
                f"{candidate['interpretation']}"
            )
        expected_source = tuple(hypothesis["source_relative_pitch_class_set"])
        expected_target = tuple(hypothesis["target_relative_pitch_class_set"])
        split_summaries = {}
        for split_name, datasets in (
            ("train", train),
            ("validation", validation),
        ):
            data = datasets[candidate["subject_voice_index"]]
            indices = selected_context_indices(
                data,
                candidate,
                tonic_by_piece,
                mode_by_piece,
            )
            rows = signature_rows(
                data,
                indices,
                tonic_by_piece,
                expected_source,
                expected_target,
            )
            split_summaries[split_name] = summarize_rows(rows)
        audits.append(
            {
                "candidate": candidate,
                "harmonic_hypothesis": hypothesis,
                **split_summaries,
                "classification": proxy_classification(
                    split_summaries["train"],
                    split_summaries["validation"],
                ),
            }
        )

    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_5_harmonic_audit",
            "seed": args.seed,
            "test_opened": False,
            "split_strategy": split_metadata["strategy"],
        },
        "source": {
            "archive": str(archive),
            "archive_sha256": actual_hash,
            "manifest": str(args.manifest.resolve()),
            "manifest_schema_version": manifest["schema_version"],
            "calibration_result": str(calibration_path),
            "calibration_result_sha256": base.sha256_file(calibration_path),
        },
        "tonal_status_audit": tonal_audit,
        "corpus": {
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "test_opened": False,
        },
        "audits": audits,
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
