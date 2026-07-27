#!/usr/bin/env python3
"""Evaluate the frozen V3.7 harmonic compression once on the sealed test."""

from __future__ import annotations

import argparse
import json
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


def verify_frozen_protocol(
    protocol: dict[str, Any],
    compression_path: Path,
    authentic_result: Path,
    null_result: Path,
) -> None:
    if protocol["status"] != "FROZEN_BEFORE_TEST":
        raise ValueError("Protocol was not frozen before test")
    if protocol["frozen_model"] != "graded_exact":
        raise ValueError("Unexpected frozen model")
    expected = protocol["source_hashes"]
    actual = {
        "compression_implementation_sha256": base.sha256_file(
            compression_path
        ),
        "authentic_v3_7_sha256": base.sha256_file(authentic_result),
        "null_v3_7_sha256": base.sha256_file(null_result),
    }
    if actual != expected:
        raise ValueError(
            f"Frozen source hash mismatch: expected={expected}, actual={actual}"
        )


def model_matrix(
    model_name: str,
    baseline: np.ndarray,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, list[str]]:
    columns, rule_ids = compression.model_rule_columns(model_name, masks)
    return compression.append_columns(baseline, columns), rule_ids


def evaluate_frozen_models(
    discovery: satb.VoiceOpportunities,
    test: satb.VoiceOpportunities,
    discovery_masks: dict[str, np.ndarray],
    test_masks: dict[str, np.ndarray],
    model_names: list[str],
    max_steps: int,
    learning_rate: float,
    l1: float,
    bootstrap_replicates: int,
    seed: int,
) -> dict[str, Any]:
    discovery_baseline = satb.baseline_matrix(discovery)
    test_baseline = satb.baseline_matrix(test)
    records = {}
    losses = {}
    for model_name in model_names:
        print(f"[frozen-test] fitting {model_name}", flush=True)
        discovery_matrix, rule_ids = model_matrix(
            model_name,
            discovery_baseline,
            discovery_masks,
        )
        test_matrix, _ = model_matrix(
            model_name,
            test_baseline,
            test_masks,
        )
        weights, diagnostics = compression.fit_without_holdout_selection(
            discovery_matrix,
            discovery.chosen_indices,
            l1,
            max_steps,
            learning_rate,
        )
        test_losses = ablation.row_nll(
            test_matrix,
            test.chosen_indices,
            weights,
        )
        losses[model_name] = test_losses
        records[model_name] = {
            "rule_ids": rule_ids,
            "discovery_nll": base.conditional_nll(
                discovery_matrix,
                discovery.chosen_indices,
                weights,
            ),
            "test_nll": float(test_losses.mean()),
            "rule_weights": [
                float(weight)
                for weight in (
                    weights[-len(rule_ids) :]
                    if rule_ids
                    else np.asarray([], dtype=np.float64)
                )
            ],
            "fit": diagnostics,
        }
    baseline_losses = losses["baseline"]
    for index, model_name in enumerate(model_names):
        if model_name == "baseline":
            continue
        records[model_name]["test_gain_vs_baseline"] = float(
            baseline_losses.mean() - losses[model_name].mean()
        )
        records[model_name]["bootstrap_vs_baseline"] = (
            ablation.bootstrap_nll_gain_by_piece(
                baseline_losses,
                losses[model_name],
                test.piece_ids,
                bootstrap_replicates,
                seed + index,
            )
        )
    return records


def acceptance_decision(
    records: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    selected = records[protocol["frozen_model"]]
    both = records["both"]
    selected_gain = selected["test_gain_vs_baseline"]
    both_gain = both["test_gain_vs_baseline"]
    retention = selected_gain / both_gain if both_gain > 0 else 0.0
    criteria = {
        "selected_nll_below_baseline": (
            selected["test_nll"] < records["baseline"]["test_nll"]
        ),
        "bootstrap_gain_p025_above_zero": (
            selected["bootstrap_vs_baseline"]["gain_p025"] > 0
        ),
        "minimum_gain_retention_vs_both": (
            retention
            >= protocol["acceptance"]["minimum_gain_retention_vs_both"]
        ),
    }
    return {
        "criteria": criteria,
        "gain_retention_vs_both": retention,
        "accepted": all(criteria.values()),
        "no_retuning_after_test": protocol["acceptance"][
            "no_retuning_after_test"
        ],
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# POC V3.8 — test final gelé",
        "",
        "## Protocole",
        "",
        "- Feature et seuils gelés avant l'ouverture.",
        "- Ajustement sur 301 chorals de développement.",
        "- Évaluation unique sur 51 chorals de test.",
        "- Aucun réajustement autorisé après lecture.",
        "",
        "## Résultats",
        "",
        "| Modèle | NLL test | Gain contre baseline | Poids |",
        "|---|---:|---:|---:|",
    ]
    for model_name, record in result["models"].items():
        gain = record.get("test_gain_vs_baseline")
        if gain is None:
            lines.append(
                f"| {model_name} | {record['test_nll']:.6f} | — | — |"
            )
            continue
        weight_label = ", ".join(
            f"{weight:.3f}" for weight in record["rule_weights"]
        )
        lines.append(
            f"| {model_name} | {record['test_nll']:.6f} | "
            f"{gain:+.8f} | {weight_label or '—'} |"
        )
    decision = result["acceptance"]
    lines.extend(
        [
            "",
            "## Décision",
            "",
            f"Accepté : `{decision['accepted']}`.",
            (
                "Gain conservé face aux deux poids : "
                f"`{decision['gain_retention_vs_both']:.3f}`."
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
        "--protocol",
        type=Path,
        default=root / "FROZEN_V3_8_TEST_PROTOCOL.json",
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--results-dir", type=Path, default=root / "results")
    parser.add_argument("--output-stem", default="v3_8_frozen_harmonic_test")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
    protocol_path = args.protocol.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    compression_path = Path(compression.__file__).resolve()
    authentic_result = root / "results/v3_7_harmonic_feature_compression.json"
    null_result = (
        root / "results/v3_7_harmonic_feature_compression_null.json"
    )
    verify_frozen_protocol(
        protocol,
        compression_path,
        authentic_result,
        null_result,
    )
    archive = args.archive.resolve()
    if base.sha256_file(archive) != base.EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Unexpected corpus archive")
    manifest, included_pieces = base.load_included_pieces(args.manifest.resolve())
    splits, split_metadata = column.load_experiment_splits(
        [piece["id"] for piece in included_pieces],
        args.seed,
        args.splits.resolve(),
    )
    score_paths = base.materialize_scores(
        archive,
        included_pieces,
        root / "work/scores",
    )
    tonic_by_piece, mode_by_piece, tonal_audit = tonal.build_tonal_status_maps(
        score_paths
    )
    alto = satb.load_satb_opportunities(
        root / "work/satb-opportunities-full.npz"
    )[1]
    discovery_ids = splits["train"] + splits["validation"]
    discovery = satb.subset_for_piece_ids(alto, discovery_ids)
    test = satb.subset_for_piece_ids(alto, splits["test"])
    discovery_masks = compression.feature_masks(
        discovery,
        tonic_by_piece,
        mode_by_piece,
    )
    test_masks = compression.feature_masks(
        test,
        tonic_by_piece,
        mode_by_piece,
    )
    training = protocol["training"]
    model_names = ["baseline", "both", protocol["frozen_model"]]
    records = evaluate_frozen_models(
        discovery,
        test,
        discovery_masks,
        test_masks,
        model_names,
        training["max_steps"],
        training["learning_rate"],
        training["l1"],
        protocol["evaluation"]["bootstrap_replicates"],
        args.seed + 809,
    )
    decision = acceptance_decision(records, protocol)
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_8_frozen_test",
            "seed": args.seed,
            "test_opened": True,
            "test_opening": "single_frozen_evaluation",
            "split_strategy": split_metadata["strategy"],
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "music21": __import__("music21").__version__,
        },
        "source": {
            "protocol": str(protocol_path),
            "protocol_sha256": base.sha256_file(protocol_path),
            "archive": str(archive),
            "archive_sha256": base.sha256_file(archive),
            "manifest": str(args.manifest.resolve()),
            "manifest_schema_version": manifest["schema_version"],
            "split": split_metadata["source"],
        },
        "tonal_status_audit": tonal_audit,
        "corpus": {
            "discovery_pieces": len(discovery_ids),
            "test_pieces": len(splits["test"]),
            "discovery_alto_opportunities": discovery.size,
            "test_alto_opportunities": test.size,
        },
        "coverage": {
            "discovery": compression.coverage(
                discovery,
                discovery_masks,
            ),
            "test": compression.coverage(test, test_masks),
        },
        "models": records,
        "acceptance": decision,
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
