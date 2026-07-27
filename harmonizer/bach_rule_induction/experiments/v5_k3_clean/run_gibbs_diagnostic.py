#!/usr/bin/env python3
"""Generate dense SATB blocks from a learned V5 K3 model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import k3
import numpy as np

HERE = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        type=Path,
        default=HERE / "results/v5_1_k3_compact_model.json",
    )
    parser.add_argument("--length", type=int, default=12)
    parser.add_argument("--sweeps", type=int, default=40)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE / "results/v5_1_k3_compact_gibbs_diagnostic.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    model = payload["model"]
    corpus = payload["corpus"]
    minimum = int(corpus["candidate_min"])
    maximum = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    features = [k3.feature_from_model_record(rule) for rule in model["rules"]]
    weights = np.asarray([rule["weight"] for rule in model["rules"]], dtype=np.float64)
    generator = np.random.default_rng(args.seed)
    probabilities = np.exp(register_logits)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    candidates = np.arange(minimum, maximum + 1)
    blocks = np.stack(
        [
            [generator.choice(candidates, p=probabilities[voice]) for voice in range(4)]
            for _ in range(args.length)
        ]
    ).astype(np.int16)
    # A neutral, reproducible soprano contour is fixed; the three lower voices
    # are resampled. Boundary blocks stay fixed because they lack a full K3.
    soprano_pool = candidates[
        np.argsort(register_logits[0])[-max(4, min(8, candidates.size)) :]
    ]
    blocks[:, 0] = generator.choice(soprano_pool, size=args.length)
    fixed = np.zeros_like(blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    generated = k3.gibbs_sample(
        blocks,
        fixed,
        candidate_min=minimum,
        candidate_max=maximum,
        register_logits=register_logits,
        features=features,
        weights=weights,
        sweeps=args.sweeps,
        seed=args.seed,
        temperature=args.temperature,
    )
    result = {
        "experiment": "V5-K3-CLEAN-GIBBS-DIAGNOSTIC",
        "model": str(args.model.resolve()),
        "seed": args.seed,
        "temperature": args.temperature,
        "sweeps": args.sweeps,
        "dense_attack_grid": True,
        "initial_blocks": blocks.tolist(),
        "generated_blocks": generated.tolist(),
        "fixed_soprano": generated[:, 0].tolist(),
        "learned_rule_count": len(features),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[k3-gibbs] wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
