#!/usr/bin/env python3
"""Probe DeepBach's alto probabilities in the frozen Bach test contexts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_harmonic_feature_compression as compression
import run_poc as base
import run_satb_level_a as satb
import run_tonal_rule_ablation as ablation
import run_tonal_tendency as tonal

TIMESTEPS = 16
SUBDIVISION = 4


def load_deepbach_runtime(deepbach_root: Path) -> tuple[Any, Any, Any]:
    compat_root = deepbach_root / "compat/keras3"
    sys.path.insert(0, str(compat_root))
    from deepbach_compat import (
        load_historical_dataset,
        load_models,
    )
    from deepbach_compat.artifacts import snapshot_data_utils

    return load_historical_dataset(), load_models(), snapshot_data_utils()


def encode_score(
    score_path: Path,
    dataset: Any,
    data_utils: Any,
) -> tuple[np.ndarray, list[np.ndarray]]:
    from music21 import converter

    score = converter.parse(score_path)
    index2notes = [dict(mapping) for mapping in dataset.index2notes]
    note2indexes = [dict(mapping) for mapping in dataset.note2indexes]
    voice_major = data_utils.chorale_to_inputs(
        score,
        dataset.voice_ids,
        index2notes,
        note2indexes,
    )
    if [len(mapping) for mapping in index2notes] != dataset.num_pitches:
        raise ValueError(f"{score_path}: score introduced an unseen pitch")
    time_major = np.asarray(voice_major, dtype=np.int64).T
    start = np.asarray(
        [mapping["START"] for mapping in dataset.note2indexes],
        dtype=np.int64,
    )
    end = np.asarray(
        [mapping["END"] for mapping in dataset.note2indexes],
        dtype=np.int64,
    )
    extended = np.concatenate(
        (
            np.broadcast_to(start, (TIMESTEPS, 4)),
            time_major,
            np.broadcast_to(end, (TIMESTEPS, 4)),
        ),
        axis=0,
    )
    metadata_values = [
        np.asarray(metadata.evaluate(score), dtype=np.int64)
        for metadata in dataset.metadatas
    ]
    extended_metadata = [
        np.concatenate(
            (
                np.zeros(TIMESTEPS, dtype=np.int64),
                values,
                np.zeros(TIMESTEPS, dtype=np.int64),
            )
        )
        for values in metadata_values
    ]
    return extended, extended_metadata


def midi_to_note_name(midi: int) -> str:
    from music21 import pitch

    value = pitch.Pitch()
    value.midi = midi
    return value.nameWithOctave


def make_probe_example(
    extended: np.ndarray,
    extended_metadata: list[np.ndarray],
    time_index: int,
    data_utils: Any,
    dataset: Any,
) -> dict[str, np.ndarray]:
    left, center, right, _ = data_utils.all_features(
        extended,
        voice_index=1,
        time_index=time_index + TIMESTEPS,
        timesteps=TIMESTEPS,
        num_pitches=dataset.num_pitches,
        num_voices=4,
    )
    left_meta, center_meta, right_meta = data_utils.all_metadatas(
        chorale_metadatas=extended_metadata,
        metadatas=dataset.metadatas,
        time_index=time_index + TIMESTEPS,
        timesteps=TIMESTEPS,
    )
    return {
        "left_features": left,
        "central_features": center,
        "right_features": right,
        "left_metas": left_meta,
        "central_metas": center_meta,
        "right_metas": right_meta,
    }


def probe_contexts(
    model: Any,
    dataset: Any,
    data_utils: Any,
    score_paths: dict[str, Path],
    opportunities: satb.VoiceOpportunities,
    masks: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    proxy_rows = np.flatnonzero(
        masks[ablation.PROXY_RULE_ID].any(axis=1)
    )
    encoded: dict[str, tuple[np.ndarray, list[np.ndarray]]] = {}
    examples = []
    row_metadata = []
    for row_index in proxy_rows:
        piece_id = str(opportunities.piece_ids[row_index])
        if piece_id not in encoded:
            encoded[piece_id] = encode_score(
                score_paths[piece_id],
                dataset,
                data_utils,
            )
        sequence, metadata = encoded[piece_id]
        time_index = int(
            round(opportunities.offsets_current[row_index] * SUBDIVISION)
        )
        examples.append(
            make_probe_example(
                sequence,
                metadata,
                time_index,
                data_utils,
                dataset,
            )
        )
        resolution_pitch = int(
            opportunities.previous_pitch[row_index] + 1
        )
        resolution_name = midi_to_note_name(resolution_pitch)
        actual_name = midi_to_note_name(
            int(opportunities.chosen_pitch[row_index])
        )
        row_metadata.append(
            {
                "row_index": int(row_index),
                "piece_id": piece_id,
                "offset_current": float(
                    opportunities.offsets_current[row_index]
                ),
                "resolution_pitch": resolution_pitch,
                "resolution_index": dataset.note2indexes[1][resolution_name],
                "actual_pitch": int(
                    opportunities.chosen_pitch[row_index]
                ),
                "actual_index": dataset.note2indexes[1][actual_name],
                "bach_resolved": bool(
                    opportunities.chosen_pitch[row_index]
                    == resolution_pitch
                ),
                "exact_candidate_context": bool(
                    masks[compression.EXACT_STATUS_ID][row_index].any()
                ),
            }
        )
    batch = {
        key: np.asarray([example[key] for example in examples])
        for key in examples[0]
    }
    probabilities = model.predict(
        batch,
        batch_size=len(examples),
        verbose=0,
    )
    records = []
    for metadata, distribution in zip(
        row_metadata,
        probabilities,
        strict=True,
    ):
        resolution_index = metadata.pop("resolution_index")
        actual_index = metadata.pop("actual_index")
        resolution_probability = float(distribution[resolution_index])
        actual_probability = float(distribution[actual_index])
        rank = int(
            1
            + np.sum(
                distribution > distribution[resolution_index]
            )
        )
        records.append(
            {
                **metadata,
                "deepbach_resolution_probability": resolution_probability,
                "deepbach_actual_probability": actual_probability,
                "deepbach_resolution_rank": rank,
                "deepbach_top_choice_is_resolution": bool(
                    int(np.argmax(distribution)) == resolution_index
                ),
            }
        )
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    exact = [record for record in records if record["exact_candidate_context"]]
    nonexact = [
        record for record in records if not record["exact_candidate_context"]
    ]

    def group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "opportunities": len(rows),
            "bach_resolutions": sum(row["bach_resolved"] for row in rows),
            "mean_deepbach_resolution_probability": float(
                np.mean(
                    [
                        row["deepbach_resolution_probability"]
                        for row in rows
                    ]
                )
            ),
            "median_deepbach_resolution_probability": float(
                np.median(
                    [
                        row["deepbach_resolution_probability"]
                        for row in rows
                    ]
                )
            ),
            "deepbach_top_choice_is_resolution": sum(
                row["deepbach_top_choice_is_resolution"] for row in rows
            ),
            "mean_resolution_rank": float(
                np.mean(
                    [row["deepbach_resolution_rank"] for row in rows]
                )
            ),
        }

    return {
        "all": group_summary(records),
        "exact": group_summary(exact),
        "nonexact": group_summary(nonexact),
    }


def markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# POC V3.9 — sonde conditionnelle DeepBach",
        "",
        "## Protocole",
        "",
        "- Les 12 contextes proviennent du test Bach gelé.",
        "- Le réseau d'alto reçoit les 16 pas gauche/droite et les autres voix.",
        "- Aucune sortie DeepBach n'est utilisée pour modifier la règle.",
        "- Les poids historiques ont vu le corpus : audit, pas test indépendant.",
        "- Port Keras 3 opérationnel ; certification TensorFlow 1.1 en attente.",
        "",
        "## Résultats",
        "",
        "| Sous-ensemble | N | Résolutions Bach | Probabilité DeepBach moyenne | "
        "Résolution top-1 | Rang moyen |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in ("all", "exact", "nonexact"):
        record = summary[name]
        lines.append(
            f"| {name} | {record['opportunities']} | "
            f"{record['bach_resolutions']} | "
            f"{record['mean_deepbach_resolution_probability']:.4f} | "
            f"{record['deepbach_top_choice_is_resolution']} | "
            f"{record['mean_resolution_rank']:.2f} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = base.experiment_root()
    project_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deepbach-root",
        type=Path,
        default=project_root.parent / "deepbach-reference",
    )
    parser.add_argument("--archive", type=Path, default=base.default_archive_path())
    parser.add_argument("--manifest", type=Path, default=base.default_manifest_path())
    parser.add_argument(
        "--splits",
        type=Path,
        default=column.default_variant_safe_splits_path(),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--results-dir", type=Path, default=root / "results")
    parser.add_argument(
        "--output-stem",
        default="v3_9_deepbach_conditional_probe",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
    deepbach_root = args.deepbach_root.resolve()
    dataset, models, data_utils = load_deepbach_runtime(deepbach_root)
    archive = args.archive.resolve()
    if base.sha256_file(archive) != base.EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Unexpected corpus archive")
    manifest, included_pieces = base.load_included_pieces(args.manifest.resolve())
    splits, split_metadata = column.load_experiment_splits(
        [piece["id"] for piece in included_pieces],
        args.seed,
        args.splits.resolve(),
    )
    test_ids = set(splits["test"])
    score_paths = base.materialize_scores(
        archive,
        [piece for piece in included_pieces if piece["id"] in test_ids],
        root / "work/scores",
    )
    tonic_by_piece, mode_by_piece, tonal_audit = tonal.build_tonal_status_maps(
        score_paths
    )
    alto = satb.load_satb_opportunities(
        root / "work/satb-opportunities-full.npz"
    )[1]
    test = satb.subset_for_piece_ids(alto, splits["test"])
    masks = compression.feature_masks(
        test,
        tonic_by_piece,
        mode_by_piece,
    )
    records = probe_contexts(
        models[1],
        dataset,
        data_utils,
        score_paths,
        test,
        masks,
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_9_deepbach_conditional_probe",
            "test_contexts_reused_after_frozen_evaluation": True,
            "rule_retuning_allowed": False,
            "deepbach_training_leakage": (
                "historical weights were trained on augmented versions of "
                "the full Bach corpus"
            ),
        },
        "source": {
            "deepbach_root": str(deepbach_root),
            "upstream_manifest": str(deepbach_root / "UPSTREAM.json"),
            "upstream_manifest_sha256": base.sha256_file(
                deepbach_root / "UPSTREAM.json"
            ),
            "archive": str(archive),
            "archive_sha256": base.sha256_file(archive),
            "manifest": str(args.manifest.resolve()),
            "manifest_schema_version": manifest["schema_version"],
            "split": split_metadata["source"],
        },
        "tonal_status_audit": tonal_audit,
        "records": records,
        "summary": summarize(records),
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
