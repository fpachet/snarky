#!/usr/bin/env python3
"""Build exact conditional worlds for V22 plus the two V23 status groups."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_generative_moment_calibration as generative
import run_v18_explanatory_sparse_induction as sparse
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v23_metric_bass_harmony_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_CACHE = HERE / "work/k3-exact-v23-selected-32x10.npz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--train-pieces", type=int, default=32)
    parser.add_argument("--validation-pieces", type=int, default=10)
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def selected_features(
    *,
    source: dict,
    baseline: dict,
    grammar: dict,
    context: Path,
    groups: list[dict],
) -> tuple[k3.FeatureSpec, ...]:
    """Return the frozen V22 baseline followed by complete V23 groups."""

    catalogue = sparse._load_catalogue(source, grammar, context)
    by_key = {feature.key: feature for feature in catalogue}
    baseline_features = [
        k3.feature_from_model_record(rule)
        for rule in baseline["selected_model"]["baseline_rules"]
    ]
    root_motion = sorted(
        (
            feature
            for feature in catalogue
            if feature.kind == "central_named_root_motion_mode"
        ),
        key=lambda feature: (feature.second_value, feature.value),
    )
    expected_root_motion = len(baseline["selected_group"]["weights"])
    if len(root_motion) != expected_root_motion:
        raise ValueError("V22 root-motion group size disagrees with its model")
    features = [by_key[feature.key] for feature in baseline_features]
    features.extend(root_motion)
    for group in groups:
        block = sorted(
            (
                feature
                for feature in catalogue
                if feature.kind == group["feature_kind"]
            ),
            key=lambda feature: (
                -1 if feature.second_value is None else feature.second_value,
                feature.value,
            ),
        )
        if len(block) != int(group["size"]):
            raise ValueError(
                f"V23 group {group['id']} has {len(block)} rather than "
                f"{group['size']} cells"
            )
        features.extend(block)
    if len({feature.key for feature in features}) != len(features):
        raise ValueError("V23 selected feature list contains duplicate keys")
    return tuple(features)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    baseline_path = FACTOR_BASE / config["baseline_model"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    grammar_path = (FACTOR_BASE / config["source_grammar"]).resolve()
    grammar = exact._load_grammar(grammar_path)
    features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=args.context,
        groups=config["groups"],
    )
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)[
        : args.train_pieces
    ]
    validation_ids = list(splits["validation"])[: args.validation_pieces]
    candidate_min = int(source["corpus"]["candidate_min"])
    candidate_max = int(source["corpus"]["candidate_max"])
    metadata = {
        "schema_version": 1,
        "scope": "exact_gibbs_attack_hold_worlds",
        "experiment": config["id"],
        "train_ids": train_ids,
        "validation_ids": validation_ids,
        "feature_keys": [feature.key for feature in features],
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
    }
    selected_model = baseline["selected_model"]
    train, validation = exact._load_or_build(
        args.cache,
        metadata=metadata,
        train_ids=train_ids,
        validation_ids=validation_ids,
        scores=args.scores,
        features=features,
        register=np.asarray(
            selected_model["register_logits"],
            dtype=np.float64,
        ),
        tonal=np.asarray(
            selected_model["tonal_logits"],
            dtype=np.float64,
        ),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    print(
        f"[v23-cache] features={len(features)} "
        f"train={train['chosen'].size} validation={validation['chosen'].size}",
        flush=True,
    )
    print(f"[v23-cache] wrote {args.cache}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
