#!/usr/bin/env python3
"""Build an exact conditional cache for a frozen readable K3 grammar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import run_exact_factor_reinduction as exact
import run_generative_moment_calibration as generative
import run_v6_factor_induction as v6

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_GRAMMAR = FACTOR_BASE / "grammar_v19_vertical_status.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-v19-catalogue-32x10.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=32)
    parser.add_argument("--validation-pieces", type=int, default=10)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--label", default="v19")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grammar = exact._load_grammar(args.grammar)
    source = json.loads(args.source.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)[
        : args.train_pieces
    ]
    validation_ids = list(splits["validation"])[: args.validation_pieces]
    context = exact.k3.load_k3_dataset(args.context)
    context_train = exact.k3.subset_for_piece_ids(context, list(splits["train"]))
    context_train = context_train.with_domain(
        int(source["corpus"]["candidate_min"]),
        int(source["corpus"]["candidate_max"]),
    )
    catalogue = v6._catalogue(context_train, grammar)
    candidate_min = int(source["corpus"]["candidate_min"])
    candidate_max = int(source["corpus"]["candidate_max"])
    metadata = {
        "schema_version": 1,
        "scope": "exact_gibbs_attack_hold_worlds",
        "train_ids": train_ids,
        "validation_ids": validation_ids,
        "feature_keys": [feature.key for feature in catalogue],
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
    }
    register = np.asarray(source["model"]["register_logits"], dtype=np.float64)
    tonal = np.asarray(source["model"]["tonal_logits"], dtype=np.float64)
    train, validation = exact._load_or_build(
        args.cache,
        metadata=metadata,
        train_ids=train_ids,
        validation_ids=validation_ids,
        scores=args.scores,
        features=catalogue,
        register=register,
        tonal=tonal,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    print(
        f"[{args.label}-cache] factors={len(catalogue)} "
        f"train={train['chosen'].size} validation={validation['chosen'].size}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
