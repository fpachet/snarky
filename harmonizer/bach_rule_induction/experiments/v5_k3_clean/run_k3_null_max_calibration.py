#!/usr/bin/env python3
"""Calibrate the first K3 column against catalogue-wide shuffled maxima."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE / "work/k3-train-validation-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def _load_train(
    cache_path: Path,
    splits_path: Path,
) -> tuple[k3.K3Dataset, dict[str, list[str]]]:
    data = k3.load_k3_dataset(cache_path)
    payload = json.loads(splits_path.read_text(encoding="utf-8"))
    source = payload.get("grouped_split", payload)
    splits = {name: list(source[name]) for name in ("train", "validation", "test")}
    train = k3.subset_for_piece_ids(data, splits["train"])
    minimum, maximum = k3.training_domain(train)
    train, removed = k3.filter_to_domain(train, minimum, maximum)
    if removed:
        raise ValueError("Train-derived domain removed train decisions")
    return train, splits


def shuffled_choice_indices(
    dataset: k3.K3Dataset,
    replicates: int,
    seed: int,
) -> np.ndarray:
    """Return within-piece/voice label permutations without copying K3 blocks."""

    base = dataset.chosen_pitches
    result = np.broadcast_to(base, (replicates, dataset.size)).copy()
    groups = [
        np.flatnonzero(
            (dataset.piece_ids == piece_id) & (dataset.voice_indices == voice)
        )
        for piece_id in np.unique(dataset.piece_ids)
        for voice in range(4)
    ]
    generator = np.random.default_rng(seed)
    for replicate in range(replicates):
        for indices in groups:
            if indices.size >= 2:
                result[replicate, indices] = generator.permutation(base[indices])
    return (result - dataset.candidate_min).astype(np.int16)


def _feature_z_scores(
    dataset: k3.K3Dataset,
    probabilities: np.ndarray,
    feature: k3.FeatureSpec,
    shuffled_indices: np.ndarray,
) -> tuple[float, np.ndarray, dict[str, Any]] | None:
    mask = k3.feature_mask(dataset, feature)
    any_candidate = mask.any(axis=1)
    all_candidates = mask.all(axis=1)
    testable = any_candidate & ~all_candidates
    if not np.any(testable):
        return None
    expected = np.sum(probabilities * mask, axis=1)
    variance = float(np.sum(expected * (1.0 - expected)))
    if variance <= 1e-12:
        return None
    rows = np.arange(dataset.size)
    chosen = mask[rows, dataset.chosen_indices]
    authentic_residual = float(np.sum(chosen - expected))
    null_chosen = mask[rows[None, :], shuffled_indices]
    null_residuals = np.sum(null_chosen, axis=1) - float(np.sum(expected))
    scale = math.sqrt(variance)
    return (
        authentic_residual / scale,
        null_residuals / scale,
        {
            "testable_opportunities": int(testable.sum()),
            "piece_support": int(np.unique(dataset.piece_ids[testable]).size),
            "observed_rate": float(chosen[testable].mean()),
            "expected_rate": float(expected[testable].mean()),
        },
    )


def calibrate(
    dataset: k3.K3Dataset,
    *,
    replicates: int,
    seed: int,
    min_testable: int,
    min_piece_support: int,
) -> dict[str, Any]:
    register_logits = k3.learn_register_logits(dataset)
    probabilities = k3.probabilities(dataset, register_logits)
    shuffled = shuffled_choice_indices(dataset, replicates, seed)
    maxima = np.zeros(replicates, dtype=np.float64)
    authentic_records = []
    catalogue = k3.feature_catalogue()
    for index, feature in enumerate(catalogue, start=1):
        scored = _feature_z_scores(dataset, probabilities, feature, shuffled)
        if scored is None:
            continue
        authentic_z, null_z, metadata = scored
        if (
            metadata["testable_opportunities"] < min_testable
            or metadata["piece_support"] < min_piece_support
        ):
            continue
        maxima = np.maximum(maxima, np.abs(null_z))
        authentic_records.append(
            {
                "feature": feature.to_dict(),
                "authentic_z_score": authentic_z,
                **metadata,
            }
        )
        if index % 100 == 0 or index == len(catalogue):
            print(
                f"[k3-null-max] scanned {index}/{len(catalogue)} features",
                flush=True,
            )
    authentic_records.sort(
        key=lambda record: abs(record["authentic_z_score"]),
        reverse=True,
    )
    for record in authentic_records:
        absolute_z = abs(record["authentic_z_score"])
        record["familywise_p"] = float(
            (1 + np.sum(maxima >= absolute_z)) / (replicates + 1)
        )
        record["exceeds_all_null_maxima"] = bool(absolute_z > maxima.max())
    first_rule_key = k3.FeatureSpec("any_voice_adjacent_step_gt", -1, value=2).key
    first_rule = next(
        record
        for record in authentic_records
        if record["feature"]["key"] == first_rule_key
    )
    quantiles = np.quantile(maxima, [0.5, 0.9, 0.95, 1.0])
    return {
        "catalogue_size": len(catalogue),
        "admissible_features": len(authentic_records),
        "replicates": replicates,
        "seed": seed,
        "null_maxima": maxima.tolist(),
        "null_maximum_summary": {
            "median": float(quantiles[0]),
            "p90": float(quantiles[1]),
            "p95": float(quantiles[2]),
            "maximum": float(quantiles[3]),
        },
        "first_rule": first_rule,
        "top_authentic_features": authentic_records[:25],
    }


def _markdown(result: dict[str, Any]) -> str:
    calibration = result["calibration"]
    summary = calibration["null_maximum_summary"]
    first = calibration["first_rule"]
    lines = [
        "# V5.4 — calibration du maximum familial K3",
        "",
        "## Protocole",
        "",
        (
            f"- `{calibration['replicates']}` permutations des choix au sein de "
            "chaque pièce et voix."
        ),
        (
            f"- `{calibration['catalogue_size']}` prédicats scannés, dont "
            f"`{calibration['admissible_features']}` testables après filtrage."
        ),
        "- Maximum absolu calculé sur tous les prédicats testables.",
        "- Distribution de registre réestimée sur le train authentique.",
        "- Cette calibration porte sur la première étape de génération de colonne.",
        "- Le test de 51 chorals reste fermé.",
        "",
        "## Maximum nul",
        "",
        f"- médiane : `{summary['median']:.3f}` ;",
        f"- percentile 90 : `{summary['p90']:.3f}` ;",
        f"- percentile 95 : `{summary['p95']:.3f}` ;",
        f"- maximum observé : `{summary['maximum']:.3f}`.",
        "",
        "## Première règle authentique",
        "",
        f"- clause : `{first['feature']['label']}` ;",
        f"- z authentique : `{first['authentic_z_score']:+.3f}` ;",
        f"- p familial empirique : `{first['familywise_p']:.3f}` ;",
        (
            "- dépasse les 49 maxima nuls : "
            f"`{str(first['exceeds_all_null_maxima']).lower()}`."
        ),
        (
            "- `0,020 = 1/50` est la résolution minimale avec 49 permutations : "
            "aucun maximum nul n'atteint le signal authentique."
        ),
        "",
        "## Principaux signaux authentiques avant réajustement",
        "",
        "| Rang | Prédicat | z | p familial |",
        "|---:|---|---:|---:|",
    ]
    for index, record in enumerate(calibration["top_authentic_features"][:12], start=1):
        lines.append(
            f"| {index} | `{record['feature']['label']}` | "
            f"{record['authentic_z_score']:+.3f} | "
            f"{record['familywise_p']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Portée",
            "",
            "Le p familial protège la sélection de la première colonne contre les",
            f"{calibration['catalogue_size']} essais numériques du catalogue, dont",
            f"{calibration['admissible_features']} sont testables. Il ne valide pas",
            "automatiquement les onze colonnes suivantes, qui sont recherchées sur",
            "des résidus successivement réajustés. Leur calibration complète exigera",
            "de répéter toute la génération de colonnes sous chaque permutation.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--replicates", type=int, default=49)
    parser.add_argument("--seed", type=int, default=5309)
    parser.add_argument("--min-testable", type=int, default=100)
    parser.add_argument("--min-piece-support", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    train, splits = _load_train(args.cache, args.splits)
    result = {
        "experiment": {
            "id": "V5.4-K3-FIRST-COLUMN-NULL-MAX",
            "test_loaded": False,
        },
        "corpus": {
            "train_pieces": len(splits["train"]),
            "validation_pieces_reserved": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
        },
        "calibration": calibrate(
            train,
            replicates=args.replicates,
            seed=args.seed,
            min_testable=args.min_testable,
            min_piece_support=args.min_piece_support,
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_4_k3_first_column_null_max.json"
    report_path = args.output_dir / "V5_4_K3_FIRST_COLUMN_NULL_MAX.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-null-max] wrote {json_path}", flush=True)
    print(f"[k3-null-max] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
