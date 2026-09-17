#!/usr/bin/env python3
"""Refitted group ablation for the recovered readable SATB rule catalogue.

Each rule family is removed in turn and every remaining weight is re-estimated
from scratch.  The canonical V2.4 full model supplies the matched reference
loss.  The grouped test split remains sealed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base
import run_satb_ablation as ablation
import run_satb_level_a as satb

RULE_GROUPS = {
    "melody": ("R-MELODY-001", "R-MELODY-002"),
    "overlap": ("R-OVERLAP-001",),
    "parallels": ("R-PARALLEL-001", "R-PARALLEL-002"),
    "direct": ("R-DIRECT-001", "R-DIRECT-002"),
}


def fit_rule_subset(
    train: list[satb.VoiceOpportunities],
    validation: list[satb.VoiceOpportunities],
    included_rule_ids: tuple[str, ...],
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> dict[str, Any]:
    """Fit all nuisance weights and a selected subset of readable rules."""

    voice_records = []
    for train_voice, validation_voice in zip(train, validation, strict=True):
        voice_name = satb.VOICE_NAMES[train_voice.voice_index]
        print(
            f"[group-refit] fitting {voice_name} with "
            f"{len(included_rule_ids)} rules",
            flush=True,
        )
        train_baseline = ablation.nuisance_baseline_matrix(train_voice)
        validation_baseline = ablation.nuisance_baseline_matrix(validation_voice)
        train_masks = ablation.readable_rule_masks(train_voice)
        validation_masks = ablation.readable_rule_masks(validation_voice)
        if included_rule_ids:
            train_rules = np.stack(
                [train_masks[rule_id] for rule_id in included_rule_ids],
                axis=2,
            )
            validation_rules = np.stack(
                [validation_masks[rule_id] for rule_id in included_rule_ids],
                axis=2,
            )
            train_matrix = np.concatenate((train_baseline, train_rules), axis=2)
            validation_matrix = np.concatenate(
                (validation_baseline, validation_rules), axis=2
            )
        else:
            train_matrix = train_baseline
            validation_matrix = validation_baseline
        weights, diagnostics = base.fit_sparse_conditional_model(
            train_matrix,
            train_voice.chosen_indices,
            validation_matrix,
            validation_voice.chosen_indices,
            l1=l1,
            max_steps=max_steps,
            learning_rate=learning_rate,
        )
        rule_weights = (
            weights[-len(included_rule_ids) :]
            if included_rule_ids
            else np.asarray([], dtype=np.float64)
        )
        voice_records.append(
            {
                "voice": voice_name,
                "train_opportunities": train_voice.size,
                "validation_opportunities": validation_voice.size,
                "train_nll": base.conditional_nll(
                    train_matrix, train_voice.chosen_indices, weights
                ),
                "validation_nll": base.conditional_nll(
                    validation_matrix,
                    validation_voice.chosen_indices,
                    weights,
                ),
                "remaining_rule_weights": {
                    rule_id: float(weight)
                    for rule_id, weight in zip(
                        included_rule_ids, rule_weights, strict=True
                    )
                },
                "fit": diagnostics,
            }
        )
    return {
        "train_nll": ablation.combined_nll(
            voice_records, "train_nll", "train_opportunities"
        ),
        "validation_nll": ablation.combined_nll(
            voice_records,
            "validation_nll",
            "validation_opportunities",
        ),
        "voice_models": voice_records,
    }


def validate_reference(
    reference: dict[str, Any],
    *,
    null_shuffle: bool,
    split_strategy: str,
    max_steps: int,
    learning_rate: float,
    l1: float,
) -> None:
    experiment = reference["experiment"]
    if experiment["null_shuffle"] != null_shuffle:
        raise ValueError("V2.4 reference null-control mode does not match")
    if experiment["split_strategy"] != split_strategy:
        raise ValueError("V2.4 reference split does not match")
    first_fit = reference["model"]["voice_models"][0]["full_fit"]
    if first_fit["l1"] != l1:
        raise ValueError("V2.4 reference L1 does not match")
    history = first_fit["history"]
    if history[-1]["step"] != max_steps:
        raise ValueError("V2.4 reference max steps do not match")
    # Learning rate was not serialized in V2.4. Keep the explicit argument in
    # the V2.5 artifact and require its canonical default here.
    if learning_rate != 0.04:
        raise ValueError("Non-canonical learning rate lacks a matched reference")


def markdown_report(result: dict[str, Any]) -> str:
    model = result["model"]
    lines = [
        "# POC V2.5 — ablation par groupe avec réajustement",
        "",
        "## Protocole",
        "",
        "- Chaque groupe est retiré du catalogue de sept règles.",
        "- Tous les poids restants sont réestimés depuis zéro.",
        "- La référence complète est le modèle canonique V2.4.",
        "- Le test final reste scellé.",
        (
            "- Contrôle nul par permutation."
            if result["experiment"]["null_shuffle"]
            else "- Chorals authentiques."
        ),
        "",
        "## Résultats",
        "",
        f"NLL validation du catalogue complet : `{model['full_validation_nll']:.6f}`.",
        "",
        "| Groupe retiré | Règles retirées | NLL train | NLL validation | "
        "Pénalité après réajustement |",
        "|---|---|---:|---:|---:|",
    ]
    for record in model["group_ablations"]:
        rules = ", ".join(f"`{rule}`" for rule in record["removed_rule_ids"])
        lines.append(
            f"| {record['group']} | {rules} | {record['train_nll']:.6f} | "
            f"{record['validation_nll']:.6f} | "
            f"{record['validation_nll_penalty']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "Une pénalité positive signifie que le modèle réajusté ne compense",
            "pas entièrement le retrait du groupe.",
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
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--reference-result", type=Path)
    parser.add_argument("--output-stem", default="v2_5_satb_group_refit")
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

    if args.max_pieces is not None and args.reference_result is None:
        raise ValueError(
            "Smoke runs require --reference-result from a matched V2.4 run"
        )
    reference_path = (
        args.reference_result.resolve()
        if args.reference_result is not None
        else results_dir
        / (
            "v2_4_satb_ablation_null.json"
            if args.null_shuffle
            else "v2_4_satb_ablation.json"
        )
    )
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    validate_reference(
        reference,
        null_shuffle=args.null_shuffle,
        split_strategy=split_metadata["strategy"],
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        l1=args.l1,
    )
    full_validation_nll = reference["model"]["full_validation_nll"]

    group_records = []
    for group, removed_rule_ids in RULE_GROUPS.items():
        included = tuple(
            rule_id
            for rule_id in ablation.RULE_IDS
            if rule_id not in removed_rule_ids
        )
        print(f"[group-refit] removing {group}: {removed_rule_ids}", flush=True)
        fitted = fit_rule_subset(
            train,
            validation,
            included,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
        group_records.append(
            {
                "group": group,
                "removed_rule_ids": list(removed_rule_ids),
                "remaining_rule_ids": list(included),
                "train_nll": fitted["train_nll"],
                "validation_nll": fitted["validation_nll"],
                "validation_nll_penalty": (
                    fitted["validation_nll"] - full_validation_nll
                ),
                "voice_models": fitted["voice_models"],
            }
        )
    group_records.sort(
        key=lambda record: record["validation_nll_penalty"], reverse=True
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v2_5_refitted_group_ablation",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "split_strategy": split_metadata["strategy"],
            "max_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
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
            "reference_result": str(reference_path),
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
            "full_validation_nll": full_validation_nll,
            "group_ablations": group_records,
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
