#!/usr/bin/env python3
"""Fit one frozen V23 stability fold with terminal checkpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import grouped_maxent
import numpy as np
import run_exact_factor_reinduction as exact
import yaml
from build_v23_selected_cache import selected_features
from run_v21_grouped_transition import paired_improvement
from run_v23_metric_bass_harmony import (
    _group_penalty,
    _initial_v22,
    _point,
    _split,
)

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v23b_metric_bass_harmony_stability_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold", type=int, required=True, choices=range(5))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--variant",
        choices=("harmony_only", "both_groups"),
        help="Fit only one frozen variant (useful for the retained full model).",
    )
    return parser.parse_args()


def _clean_point(point: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in point.items()
        if key not in {"_parameters", "fit", "validation_piece_nll"}
    }


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    baseline = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    grammar = exact._load_grammar(FACTOR_BASE / config["source_grammar"])
    features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=args.context,
        groups=config["groups"],
    )
    if args.fold == 0 and args.cache is None:
        raise ValueError("Full validation mode requires an explicit cache")
    cache = args.cache or (
        FACTOR_BASE
        / config["source_cache_directory"]
        / f"fold{args.fold}.npz"
    ).resolve()
    output = args.output or (
        FACTOR_BASE
        / (
            "v23c_metric_bass_harmony_full_model.json"
            if args.fold == 0
            else f"v23b_metric_bass_harmony_fold{args.fold}.json"
        )
    )
    archive = np.load(cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in features]:
        raise ValueError("V23 stability cache and feature order disagree")
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    baseline_count = (
        len(baseline["selected_model"]["baseline_rules"])
        + len(baseline["selected_group"]["weights"])
    )
    group_specs = {group["id"]: group for group in config["groups"]}
    group_ranges: dict[str, np.ndarray] = {}
    cursor = baseline_count
    for group in config["groups"]:
        size = int(group["size"])
        group_ranges[group["id"]] = np.arange(cursor, cursor + size)
        cursor += size
    baseline_indices = np.arange(baseline_count)
    train_baseline = _split(archive, "train", baseline_indices)
    validation_baseline = _split(archive, "validation", baseline_indices)
    estimation = config["estimation"]
    initial = _initial_v22(baseline, features, baseline_count)
    baseline_l1 = (
        float(estimation["l1_baseline_by_clause_complexity"])
        * np.asarray(
            [feature.complexity for feature in features[:baseline_count]],
            dtype=np.float64,
        )
    )
    prefit, _ = grouped_maxent.fit_grouped(
        train_baseline,
        validation_baseline,
        candidates,
        initial,
        steps=int(estimation["steps_baseline_prefit"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=False,
    )
    baseline_parameters, baseline_fit = grouped_maxent.fit_grouped(
        train_baseline,
        validation_baseline,
        candidates,
        prefit,
        steps=int(estimation["steps_comparison"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=False,
    )
    baseline_point = _point(
        label="socle V22",
        penalty=None,
        train=train_baseline,
        validation=validation_baseline,
        candidates=candidates,
        parameters=baseline_parameters,
        group_indices={},
        fit=baseline_fit,
    )
    variants = {}
    active_variants = [
        variant
        for variant in config["variants"]
        if args.variant is None or variant["id"] == args.variant
    ]
    for variant_offset, variant in enumerate(active_variants, start=1):
        active_specs = [
            group_specs[group_id]
            for group_id in variant["active_groups"]
        ]
        selected_indices = [
            *range(baseline_count),
            *(
                int(index)
                for spec in active_specs
                for index in group_ranges[spec["id"]]
            ),
        ]
        selected_array = np.asarray(selected_indices, dtype=np.int64)
        train = _split(archive, "train", selected_array)
        validation = _split(archive, "validation", selected_array)
        local_ranges: dict[str, np.ndarray] = {}
        local_cursor = baseline_count
        for spec in active_specs:
            size = int(spec["size"])
            local_ranges[spec["id"]] = np.arange(
                local_cursor,
                local_cursor + size,
            )
            local_cursor += size
        initial_full = exact.Parameters(
            prefit.register.copy(),
            prefit.tonal.copy(),
            np.concatenate(
                (
                    prefit.factor_weights,
                    np.zeros(local_cursor - baseline_count),
                )
            ),
        )
        l1 = np.concatenate(
            (
                baseline_l1,
                *(
                    np.full(
                        int(spec["size"]),
                        float(spec["l1_inside_group"]),
                    )
                    for spec in active_specs
                ),
            )
        )
        penalty = float(variant["frozen_group_penalty"])
        penalties = tuple(
            _group_penalty(
                spec,
                local_ranges[spec["id"]],
                penalty,
            )
            for spec in active_specs
        )
        parameters, fit = grouped_maxent.fit_grouped(
            train,
            validation,
            candidates,
            initial_full,
            steps=int(estimation["steps_comparison"]),
            learning_rate=float(estimation["learning_rate"]),
            l1=l1,
            l2=float(estimation["l2"]),
            groups=penalties,
            return_best_validation=False,
        )
        point = _point(
            label=variant["id"],
            penalty=penalty,
            train=train,
            validation=validation,
            candidates=candidates,
            parameters=parameters,
            group_indices=local_ranges,
            fit=fit,
        )
        paired = paired_improvement(
            baseline_point["validation_piece_nll"],
            point["validation_piece_nll"],
            seed=(
                int(config["selection"]["paired_bootstrap_seed"])
                + args.fold * 10
                + variant_offset
            ),
            resamples=int(config["selection"]["paired_bootstrap_resamples"]),
        )
        variants[variant["id"]] = {
            "active_group_ids": variant["active_groups"],
            "frozen_group_penalty": penalty,
            "point": _clean_point(point),
            "paired_vs_baseline": paired,
            "group_weights": {
                spec["id"]: parameters.factor_weights[
                    local_ranges[spec["id"]]
                ].tolist()
                for spec in active_specs
            },
            "model_parameters": {
                "register_logits": parameters.register.tolist(),
                "tonal_logits": parameters.tonal.tolist(),
                "factor_weights": parameters.factor_weights.tolist(),
                "feature_keys": [
                    features[index].key for index in selected_indices
                ],
            },
        }
        print(
            f"[v23-{'full' if args.fold == 0 else f'fold{args.fold}'}] "
            f"{variant['id']} "
            f"gain={paired['mean_improvement']:+.6f} "
            f"positive={paired['positive_piece_count']}/"
            f"{len(paired['piece_ids'])}",
            flush=True,
        )
    result = {
        "experiment": {
            "id": config["id"],
            "fold": None if args.fold == 0 else args.fold,
            "full_validation": args.fold == 0,
            "cache": str(cache),
            "train_piece_count": int(
                np.unique(train_baseline["piece_ids"]).size
            ),
            "validation_piece_count": int(
                np.unique(validation_baseline["piece_ids"]).size
            ),
            "checkpoint": "terminal",
            "test_loaded": False,
        },
        "baseline": _clean_point(baseline_point),
        "variants": variants,
    }
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    label = "full" if args.fold == 0 else f"fold{args.fold}"
    print(f"[v23-{label}] wrote {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
