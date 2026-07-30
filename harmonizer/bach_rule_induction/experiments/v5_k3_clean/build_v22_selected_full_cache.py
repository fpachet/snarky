#!/usr/bin/env python3
"""Build full train/validation exact worlds for V20B plus one V22 RuleGroup."""

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
DEFAULT_CONFIG = FACTOR_BASE / "v22b_shared_root_motion_stability_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_CACHE = HERE / "work/k3-exact-v22-selected-full.npz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    grammar = exact._load_grammar(
        (FACTOR_BASE / config["source_grammar"]).resolve()
    )
    catalogue = sparse._load_catalogue(source, grammar, args.context)
    by_key = {feature.key: feature for feature in catalogue}
    baseline = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    baseline_features = [
        k3.feature_from_model_record(rule)
        for rule in baseline["model"]["rules"]
    ]
    group_features = sorted(
        (
            feature
            for feature in catalogue
            if feature.kind == config["group"]["feature_kind"]
        ),
        key=lambda feature: (feature.second_value, feature.value),
    )
    features = tuple(
        [by_key[feature.key] for feature in baseline_features]
        + group_features
    )
    expected = len(baseline_features) + int(config["group"]["size"])
    if len(features) != expected:
        raise ValueError("V22 selected full feature count disagrees with config")
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)
    validation_ids = list(splits["validation"])
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
    train, validation = exact._load_or_build(
        args.cache,
        metadata=metadata,
        train_ids=train_ids,
        validation_ids=validation_ids,
        scores=args.scores,
        features=features,
        register=np.asarray(
            source["model"]["register_logits"],
            dtype=np.float64,
        ),
        tonal=np.asarray(
            source["model"]["tonal_logits"],
            dtype=np.float64,
        ),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    print(
        f"[v22-full-cache] features={len(features)} "
        f"train={train['chosen'].size} validation={validation['chosen'].size}",
        flush=True,
    )
    print(f"[v22-full-cache] wrote {args.cache}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
