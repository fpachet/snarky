#!/usr/bin/env python3
"""Refit the unanimous readable V18 core on the full train/validation split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_generative_moment_calibration as generative
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v18_explanatory_sparse_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_STABILITY = FACTOR_BASE / "v18_structure_stability.json"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_CACHE = HERE / "work/k3-exact-v18-unanimous-full.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v18_unanimous_full_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V18_UNANIMOUS_FULL_MODEL.md"


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    model = result["model"]
    lines = [
        f"# {experiment['title']}",
        "",
        f"Les {len(model['rules'])} prédicats présents dans les cinq "
        "réinductions de structure sont gelés. Seuls les profils auxiliaires "
        "et leurs poids sont réappris sur les 251 chorals de train, avec "
        "arrêt sur les 50 de validation.",
        "",
        "## Résultat",
        "",
        f"- Train : `{experiment['train_pieces']}` chorals, "
        f"`{experiment['train_decisions']}` décisions.",
        f"- Validation : `{experiment['validation_pieces']}` chorals, "
        f"`{experiment['validation_decisions']}` décisions.",
        f"- Règles : `{len(model['rules'])}`.",
        f"- NLL validation sans règles : "
        f"`{model['baseline_validation_nll']:.6f}`.",
        f"- NLL validation avec noyau unanime : "
        f"`{model['validation_nll']:.6f}`.",
        f"- Gain : `{model['validation_nll_gain']:.6f}`.",
        "- Test réservé chargé : `false`.",
        "",
        "| # | Règle | Poids complet |",
        "|---:|---|---:|",
    ]
    for index, rule in enumerate(model["rules"], start=1):
        lines.append(
            f"| {index} | {rule['clause']} | {rule['weight']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "Cette étape gèle le modèle explicatif destiné aux RuleCards et à la",
            "compilation Snarky. La génération reste un audit externe.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--stability", type=Path, default=DEFAULT_STABILITY)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--steps", type=int, default=160)
    parser.add_argument(
        "--experiment-id",
        default="K3-V18-UNANIMOUS-FULL-1",
    )
    parser.add_argument(
        "--title",
        default="V18 — noyau unanime réappris sur le corpus complet",
    )
    parser.add_argument("--rule-prefix", default="F-K3-V18-CORE")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    stability = json.loads(args.stability.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)
    validation_ids = list(splits["validation"])
    core = stability["summary"]["unanimous_core"]
    features = tuple(k3.FeatureSpec.from_dict(row["feature"]) for row in core)
    candidate_min = int(source["corpus"]["candidate_min"])
    candidate_max = int(source["corpus"]["candidate_max"])
    candidates = np.arange(candidate_min, candidate_max + 1, dtype=np.int16)
    source_register = np.asarray(
        source["model"]["register_logits"],
        dtype=np.float64,
    )
    source_tonal = np.asarray(
        source["model"]["tonal_logits"],
        dtype=np.float64,
    )
    metadata = {
        "schema_version": 1,
        "scope": "exact_gibbs_attack_hold_worlds",
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
        register=source_register,
        tonal=source_tonal,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    empty_train = exact._select_columns(train, [])
    empty_validation = exact._select_columns(validation, [])
    estimation = config["estimation"]
    baseline, baseline_fit = exact._fit(
        empty_train,
        empty_validation,
        candidates,
        exact.Parameters(
            source_register,
            source_tonal,
            np.empty(0, dtype=np.float64),
        ),
        steps=args.steps,
        learning_rate=float(estimation["learning_rate"]),
        l1=np.empty(0, dtype=np.float64),
        l2=float(estimation["l2"]),
    )
    complexities = np.asarray(
        [feature.complexity for feature in features],
        dtype=np.float64,
    )
    fitted, fit = exact._fit(
        train,
        validation,
        candidates,
        exact.Parameters(
            source_register,
            source_tonal,
            np.zeros(len(features), dtype=np.float64),
        ),
        steps=args.steps,
        learning_rate=float(estimation["learning_rate"]),
        l1=float(estimation["l1"]) * complexities,
        l2=float(estimation["l2"]),
    )
    baseline_validation = exact._nll(
        empty_validation["chosen"],
        empty_validation["voices"],
        empty_validation["modes"],
        empty_validation["tonics"],
        candidates,
        empty_validation["factors"],
        baseline,
    )
    train_nll = exact._nll(
        train["chosen"],
        train["voices"],
        train["modes"],
        train["tonics"],
        candidates,
        train["factors"],
        fitted,
    )
    validation_nll = exact._nll(
        validation["chosen"],
        validation["voices"],
        validation["modes"],
        validation["tonics"],
        candidates,
        validation["factors"],
        fitted,
    )
    rules = [
        {
            "id": f"{args.rule_prefix}-{index:03d}",
            "family": row["family"],
            "clause": row["clause"],
            "feature": feature.to_dict(),
            "weight": float(weight),
            "polarity": "preference" if weight > 0 else "avoidance",
            "structure_selection_count": int(row["selection_count"]),
            "structure_selection_total": 5,
            "origin": "learned_from_bach_corpus",
            "human_authored": False,
            "preference_human_authored": False,
            "feature_definition_human_authored": (
                feature.kind == "central_triadic_metric"
            ),
            "calls_other_rules": False,
        }
        for index, (row, feature, weight) in enumerate(
            zip(core, features, fitted.factor_weights, strict=True),
            start=1,
        )
    ]
    result = {
        "experiment": {
            "id": args.experiment_id,
            "title": args.title,
            "status": "FROZEN_EXPLANATORY_PRETEST",
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "train_decisions": int(train["chosen"].size),
            "validation_decisions": int(validation["chosen"].size),
            "structure_reinduction_count": 5,
            "unanimous_structure_threshold": 5,
            "test_loaded": False,
            "historical_rules_loaded": False,
            "expert_constraints_loaded": False,
            "generation_metrics_used_for_weight_learning": False,
        },
        "corpus": {
            **source["corpus"],
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
        },
        "model": {
            "register_logits": fitted.register.tolist(),
            "tonal_logits": fitted.tonal.tolist(),
            "baseline_validation_nll": baseline_validation,
            "train_nll": train_nll,
            "validation_nll": validation_nll,
            "validation_nll_gain": baseline_validation - validation_nll,
            "rules": rules,
            "baseline_fit": baseline_fit,
            "fit": fit,
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v18-full] baseline={baseline_validation:.6f} "
        f"model={validation_nll:.6f}",
        flush=True,
    )
    print(f"[v18-full] wrote {args.output}", flush=True)
    print(f"[v18-full] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
