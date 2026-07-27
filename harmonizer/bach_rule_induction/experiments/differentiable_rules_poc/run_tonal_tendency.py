#!/usr/bin/env python3
"""Discover an upward-semitone obligation from primitive global-key status.

The learner scans all twelve tonic-relative source classes uniformly.  It asks
where an exact upward semitone is unexpectedly preferred under the existing
four-voice conditional baseline.  The name ``leading tone`` is assigned only
after numeric selection.  The grouped test split remains sealed.
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


def extract_declared_global_key(score_path: Path) -> tuple[int, str]:
    """Return the one key declared consistently in all four score parts."""

    from music21 import converter, key

    score = converter.parse(score_path)
    declarations: list[list[tuple[float, int, str]]] = []
    for part in score.parts:
        events = []
        for signature in part.flatten().getElementsByClass(key.KeySignature):
            tonic = getattr(signature, "tonic", None)
            mode = getattr(signature, "mode", None)
            if tonic is None or mode not in {"major", "minor"}:
                raise ValueError(
                    f"{score_path.name}: key lacks explicit tonic/mode"
                )
            event = (float(signature.offset), int(tonic.pitchClass), mode)
            if not events or event[1:] != events[-1][1:]:
                events.append(event)
        declarations.append(events)
    if any(len(events) != 1 for events in declarations):
        raise ValueError(
            f"{score_path.name}: expected one declared key per part, "
            f"found {[len(events) for events in declarations]}"
        )
    values = {(events[0][1], events[0][2]) for events in declarations}
    if len(values) != 1:
        raise ValueError(f"{score_path.name}: inconsistent part keys {values}")
    return next(iter(values))


def build_tonal_status_maps(
    score_paths: dict[str, Path],
) -> tuple[dict[str, int], dict[str, str], dict[str, Any]]:
    tonic_by_piece = {}
    mode_by_piece = {}
    modes = Counter()
    for index, (piece_id, score_path) in enumerate(
        sorted(score_paths.items()), start=1
    ):
        tonic_pc, mode = extract_declared_global_key(score_path)
        tonic_by_piece[piece_id] = tonic_pc
        mode_by_piece[piece_id] = mode
        modes[mode] += 1
        if index % 50 == 0 or index == len(score_paths):
            print(f"[tonal-status] audited {index}/{len(score_paths)}", flush=True)
    return tonic_by_piece, mode_by_piece, {
        "pieces_audited": len(score_paths),
        "pieces_with_one_consistent_key": len(tonic_by_piece),
        "mode_counts": dict(sorted(modes.items())),
        "key_changes_detected": 0,
    }


def build_key_map(
    score_paths: dict[str, Path],
) -> tuple[dict[str, int], dict[str, Any]]:
    tonic_by_piece, _, audit = build_tonal_status_maps(score_paths)
    return tonic_by_piece, audit


def tonic_relative_source_classes(
    opportunities: satb.VoiceOpportunities,
    tonic_by_piece: dict[str, int],
) -> np.ndarray:
    tonics = np.asarray(
        [tonic_by_piece[piece_id] for piece_id in opportunities.piece_ids],
        dtype=np.int16,
    )
    return (opportunities.previous_pitch - tonics) % 12


def upward_semitone_mask(
    opportunities: satb.VoiceOpportunities,
    source_class: int,
    tonic_by_piece: dict[str, int],
) -> np.ndarray:
    """Candidate rises exactly one semitone in one tonic-relative context."""

    context = (
        tonic_relative_source_classes(opportunities, tonic_by_piece)
        == source_class
    )
    candidates = opportunities.candidate_pitches[None, :]
    conclusion = candidates == opportunities.previous_pitch[:, None] + 1
    return context[:, None] & conclusion


def select_top_obligations(
    records: list[dict[str, Any]],
    train_z_min: float,
    validation_z_min: float,
    bootstrap_positive_fraction_min: float,
    train_local_peak_min: float,
    validation_local_peak_min: float,
    budget: int,
) -> list[int]:
    admissible = [
        record
        for record in records
        if record["train"]["z_score"] >= train_z_min
        and record["validation"]["z_score"] >= validation_z_min
        and record["bootstrap_validation"]["positive_fraction"]
        >= bootstrap_positive_fraction_min
        and record["train"]["local_log_rate_contrast"]
        >= train_local_peak_min
        and record["validation"]["local_log_rate_contrast"]
        >= validation_local_peak_min
    ]
    admissible.sort(
        key=lambda record: (
            record["train"]["z_score"] ** 2
            + record["validation"]["z_score"] ** 2
        ),
        reverse=True,
    )
    return [int(record["numeric_value"]) for record in admissible[:budget]]


def per_voice_evidence(
    source_class: int,
    datasets: list[satb.VoiceOpportunities],
    probabilities: list[np.ndarray],
    tonic_by_piece: dict[str, int],
) -> list[dict[str, Any]]:
    records = []
    for data, probs in zip(datasets, probabilities, strict=True):
        mask = upward_semitone_mask(data, source_class, tonic_by_piece)
        evidence = satb.aggregate_evidence([data], [probs], [mask])
        rows = tonic_relative_source_classes(data, tonic_by_piece) == source_class
        available = rows & (data.previous_pitch < data.candidate_max)
        resolves = data.chosen_pitch == data.previous_pitch + 1
        records.append(
            {
                "voice": satb.VOICE_NAMES[data.voice_index],
                **satb.serialize_evidence(evidence),
                "source_occurrences": int(rows.sum()),
                "testable_occurrences": int(available.sum()),
                "observed_resolutions": int((available & resolves).sum()),
                "observed_exceptions": int((available & ~resolves).sum()),
            }
        )
    return records


def markdown_report(result: dict[str, Any]) -> str:
    model = result["model"]
    audit = result["tonal_status_audit"]
    lines = [
        "# POC V3.1 — première obligation tonale",
        "",
        "## Audit des statuts",
        "",
        (
            f"- {audit['pieces_with_one_consistent_key']}/"
            f"{audit['pieces_audited']} chorals ont une tonalité unique et "
            "cohérente dans les quatre voix."
        ),
        f"- Modes : `{audit['mode_counts']}`.",
        "- Aucun changement de signature détecté.",
        "- La tonalité locale est provisoirement la tonalité globale notée.",
        "- Le test final reste scellé.",
        (
            "- Contrôle nul par permutation."
            if result["experiment"]["null_shuffle"]
            else "- Chorals authentiques."
        ),
        "",
        "## Scan des douze classes relatives à la tonique",
        "",
        "Conclusion testée uniformément : `candidate == previous + 1`.",
        "",
        "| Classe source | z train | z validation | Pic local train/val. | "
        "Taux observé/attendu val. | Bootstrap val. médian [95 %] | "
        "P(z val. > 0) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for record in model["source_class_scan"]:
        validation = record["validation"]
        bootstrap = record["bootstrap_validation"]
        lines.append(
            f"| {record['numeric_value']} | {record['train']['z_score']:.3f} | "
            f"{validation['z_score']:.3f} | "
            f"{record['train']['local_log_rate_contrast']:.3f} / "
            f"{validation['local_log_rate_contrast']:.3f} | "
            f"{validation['observed_rate']:.4f} / "
            f"{validation['expected_rate']:.4f} | "
            f"{bootstrap['z_median']:.3f} "
            f"[{bootstrap['z_p025']:.3f} ; {bootstrap['z_p975']:.3f}] | "
            f"{bootstrap['positive_fraction']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Sélection",
            "",
            f"- Classes retenues : `{model['selected_source_classes']}`.",
        ]
    )
    if model["selected_source_classes"]:
        lines.extend(
            [
                "- Interprétation postérieure de `11` : sensible globale.",
                "",
                "## Détail par voix sur validation",
                "",
                "| Voix | Occurrences testables | Résolutions | Exceptions | "
                "Taux observé | Taux attendu | z |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for record in model["selected_validation_by_voice"]:
            lines.append(
                f"| {record['voice']} | {record['testable_occurrences']} | "
                f"{record['observed_resolutions']} | "
                f"{record['observed_exceptions']} | "
                f"{record['observed_rate']:.4f} | "
                f"{record['expected_rate']:.4f} | "
                f"{record['z_score']:.3f} |"
            )
    lines.extend(
        [
            "",
            "## Statut sémantique",
            "",
            "`MISSING_CONTEXT_FOR_EQUIVALENCE` : la classe numérique peut être",
            "comparée à la sensible, mais le modèle ne possède pas encore le rôle",
            "harmonique de l'accord source ni les exceptions cadentielles de",
            "`R-LEADING-001`.",
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
    parser.add_argument("--train-z-min", type=float, default=3.0)
    parser.add_argument("--validation-z-min", type=float, default=2.0)
    parser.add_argument(
        "--bootstrap-positive-fraction-min", type=float, default=0.95
    )
    parser.add_argument("--train-local-peak-min", type=float, default=1.4)
    parser.add_argument("--validation-local-peak-min", type=float, default=1.5)
    parser.add_argument("--family-budget", type=int, default=1)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--output-stem", default="v3_1_global_tonal_tendency")
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
    if cache_path.exists():
        print(f"[satb-corpus] loading cache {cache_path}", flush=True)
        all_opportunities = satb.load_satb_opportunities(cache_path)
    else:
        all_opportunities = satb.build_satb_opportunities(score_paths)
        satb.save_satb_opportunities(cache_path, all_opportunities)
    tonic_by_piece, tonal_audit = build_key_map(score_paths)

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

    def mask_builder(
        data: satb.VoiceOpportunities, value: int
    ) -> np.ndarray:
        return upward_semitone_mask(data, value, tonic_by_piece)
    source_scan = satb.scan_family(
        "tonic_relative_source_class_requires_upward_semitone",
        range(12),
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        mask_builder,
        args.bootstrap_replicates,
        args.seed + 50_000,
    )
    satb.add_local_log_rate_contrasts(source_scan, circular=True)
    selected = select_top_obligations(
        source_scan,
        args.train_z_min,
        args.validation_z_min,
        args.bootstrap_positive_fraction_min,
        args.train_local_peak_min,
        args.validation_local_peak_min,
        args.family_budget,
    )
    selected_validation_by_voice = (
        per_voice_evidence(
            selected[0],
            validation,
            validation_probabilities,
            tonic_by_piece,
        )
        if selected
        else []
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_1_global_tonal_tendency",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "split_strategy": split_metadata["strategy"],
            "selection": {
                "train_z_min": args.train_z_min,
                "validation_z_min": args.validation_z_min,
                "bootstrap_validation_positive_fraction_min": (
                    args.bootstrap_positive_fraction_min
                ),
                "train_local_log_rate_peak_min": args.train_local_peak_min,
                "validation_local_log_rate_peak_min": (
                    args.validation_local_peak_min
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
        "tonal_status_audit": tonal_audit,
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
            "source_class_scan": source_scan,
            "selected_source_classes": selected,
            "selected_validation_by_voice": selected_validation_by_voice,
            "semantic_status": "MISSING_CONTEXT_FOR_EQUIVALENCE",
            "reference_rule_id": "R-LEADING-001",
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
