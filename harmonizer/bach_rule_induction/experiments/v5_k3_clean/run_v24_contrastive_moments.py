#!/usr/bin/env python3
"""Learn V24 weights from Bach-minus-generated MaxEnt moments."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v24c_contrastive_moment_config.yaml"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v24c_contrastive_moment_fit.json"
DEFAULT_MODEL = FACTOR_BASE / "v24_contrastive_moment_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V24C_CONTRASTIVE_MOMENT_FIT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _status_counts(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
    *,
    candidate_min: int,
    candidate_max: int,
) -> tuple[np.ndarray, int]:
    times = [
        time
        for time in range(1, lattice.size - 1)
        if lattice.metric_levels[time] >= 2
    ]
    if not times:
        return np.zeros(len(k3.RESIDUAL_STRONG_SONORITY_NAMES)), 0
    data = k3.K3Dataset(
        piece_ids=np.full(len(times), lattice.piece_id),
        offsets=np.asarray(
            [[time - 1, time, time + 1] for time in times],
            dtype=np.float32,
        ),
        voice_indices=np.zeros(len(times), dtype=np.int8),
        blocks=np.asarray(
            [blocks[time - 1 : time + 2] for time in times],
            dtype=np.int16,
        ),
        attacks=np.asarray(
            [lattice.attacks[time - 1 : time + 2] for time in times],
            dtype=bool,
        ),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        tonic_pcs=np.full(len(times), lattice.tonic_pc, dtype=np.int8),
        modes=np.full(len(times), lattice.mode, dtype=np.int8),
        metric_levels=np.asarray(
            [lattice.metric_levels[time] for time in times],
            dtype=np.int8,
        ),
    )
    statuses = k3.central_residual_strong_sonority_statuses(
        data,
        data.chosen_pitches[:, None],
    )[:, 0]
    counts = np.bincount(
        statuses[statuses >= 0],
        minlength=len(k3.RESIDUAL_STRONG_SONORITY_NAMES),
    ).astype(np.float64)
    return counts, len(times)


def _sample_piece(
    task: tuple[
        str,
        str,
        dict[str, Any],
        np.ndarray,
        int,
        int,
        str,
    ],
) -> tuple[str, np.ndarray, np.ndarray, int]:
    (
        piece_id,
        score_path,
        model,
        residual_weights,
        seed,
        sweeps,
        update_schedule,
    ) = task
    lattice = k3.extract_piece_lattice(Path(score_path), piece_id)
    candidate_min = int(model["candidate_min"])
    candidate_max = int(model["candidate_max"])
    fixed = np.zeros_like(lattice.blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    local_seed = generative._piece_seed(piece_id, seed)
    features = (*model["features"], *model["residual_features"])
    weights = np.concatenate((model["weights"], residual_weights))
    generated = k3.rhythmic_gibbs_sample(
        lattice.blocks,
        lattice.attacks,
        fixed,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        register_logits=model["register_logits"],
        features=features,
        weights=weights,
        sweeps=sweeps,
        seed=local_seed,
        tonal_logits=model["tonal_logits"],
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels,
        update_schedule=update_schedule,
    )
    authentic, total = _status_counts(
        lattice.blocks,
        lattice,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )
    sampled, sampled_total = _status_counts(
        generated,
        lattice,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )
    if total != sampled_total:
        raise AssertionError("Authentic and sampled strong-block totals differ")
    return piece_id, authentic, sampled, total


def _rates(counts: np.ndarray, total: int) -> list[float]:
    return (counts / max(total, 1)).tolist()


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V24C — apprentissage par moments contrastifs",
        "",
        "Le vocabulaire V24 reste gelé. À chaque itération, le gradient compare",
        "la fréquence des huit statuts chez Bach à leur fréquence dans les",
        "générations du modèle courant. Les paramètres V23 sont fixes.",
        "",
        "| Itération | Résiduel Bach | Résiduel généré | MAE moments | "
        "Norme des poids |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in result["history"]:
        lines.append(
            f"| {row['iteration']} | {row['authentic_residual_rate']:.4f} | "
            f"{row['generated_residual_rate']:.4f} | "
            f"{row['moment_mae']:.5f} | {row['weight_norm']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Poids finaux",
            "",
            "| Statut | Bach | Généré final | Poids |",
            "|---|---:|---:|---:|",
        ]
    )
    final = result["history"][-1]
    for index, status in enumerate(k3.RESIDUAL_STRONG_SONORITY_NAMES):
        lines.append(
            f"| `{status}` | {final['authentic_rates'][index]:.4f} | "
            f"{final['generated_rates'][index]:.4f} | "
            f"{result['weights'][index]:+.4f} |"
        )
    lines.extend(
        [
            "",
            "Cette calibration est une approximation Monte-Carlo du gradient",
            "MaxEnt génératif. Elle ne transforme aucune cellule en contrainte",
            "dure et n'utilise pas la validation pour modifier les poids.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    baseline_path = FACTOR_BASE / config["baseline_model"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    corpus = baseline["corpus"]
    model_record = baseline["model"]
    residual_features = k3.residual_strong_sonority_feature_catalogue()
    prepared = {
        "candidate_min": int(corpus["candidate_min"]),
        "candidate_max": int(corpus["candidate_max"]),
        "register_logits": np.asarray(
            model_record["register_logits"],
            dtype=np.float64,
        ),
        "tonal_logits": np.asarray(
            model_record["tonal_logits"],
            dtype=np.float64,
        ),
        "features": tuple(
            k3.feature_from_model_record(rule)
            for rule in model_record["rules"]
        ),
        "weights": np.asarray(
            [float(rule["weight"]) for rule in model_record["rules"]],
            dtype=np.float64,
        ),
        "residual_features": residual_features,
    }
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    sampling = config["sampling"]
    piece_ids = sorted(
        splits["train"],
        key=generative._stable_order,
    )[: int(sampling["pieces"])]
    score_paths = {
        piece_id: str(generative._score_path(args.scores, piece_id))
        for piece_id in piece_ids
    }
    optimization = config["optimization"]
    weights = np.zeros(len(residual_features), dtype=np.float64)
    history = []
    iterations = int(optimization["iterations"])
    for iteration in range(iterations + 1):
        tasks = [
            (
                piece_id,
                score_paths[piece_id],
                prepared,
                weights,
                int(seed),
                int(sampling["sweeps"]),
                str(sampling["update_schedule"]),
            )
            for piece_id in piece_ids
            for seed in sampling["seeds"]
        ]
        authentic = np.zeros_like(weights)
        generated = np.zeros_like(weights)
        strong_total = 0
        with ProcessPoolExecutor(
            max_workers=int(sampling["workers"])
        ) as executor:
            for completed, (_, source, sampled, total) in enumerate(
                executor.map(_sample_piece, tasks),
                start=1,
            ):
                authentic += source
                generated += sampled
                strong_total += total
                if completed % 8 == 0 or completed == len(tasks):
                    print(
                        f"[v24c] iteration={iteration} "
                        f"pieces={completed}/{len(tasks)}",
                        flush=True,
                    )
        authentic_rates = authentic / strong_total
        generated_rates = generated / strong_total
        gradient = authentic_rates - generated_rates
        history.append(
            {
                "iteration": iteration,
                "strong_blocks": strong_total,
                "authentic_rates": authentic_rates.tolist(),
                "generated_rates": generated_rates.tolist(),
                "authentic_residual_rate": float(authentic_rates.sum()),
                "generated_residual_rate": float(generated_rates.sum()),
                "moment_mae": float(np.abs(gradient).mean()),
                "gradient": gradient.tolist(),
                "weights_before_update": weights.tolist(),
                "weight_norm": float(np.linalg.norm(weights)),
            }
        )
        print(
            f"[v24c] iteration={iteration} "
            f"residual={generated_rates.sum():.4f} "
            f"target={authentic_rates.sum():.4f} "
            f"mae={np.abs(gradient).mean():.5f}",
            flush=True,
        )
        if iteration == iterations:
            break
        weights += float(optimization["learning_rate"]) * (
            gradient - float(optimization["l2"]) * weights
        )
        weights = np.clip(
            weights,
            -float(optimization["weight_clip"]),
            float(optimization["weight_clip"]),
        )
    result = {
        "experiment": {
            "id": config["id"],
            "status": "STRUCTURE_TRAIN_CONTRASTIVE_CANDIDATE",
            "piece_count": len(piece_ids),
            "piece_ids": piece_ids,
            "iterations": iterations,
            "validation_used_during_updates": False,
            "test_loaded": False,
        },
        "history": history,
        "weights": weights.tolist(),
        "features": [feature.to_dict() for feature in residual_features],
    }
    candidate = json.loads(json.dumps(baseline))
    candidate["experiment"] = {
        **baseline["experiment"],
        "id": "K3-V24-CONTRASTIVE-MOMENT-MODEL-1",
        "status": "GENERATIVE_CALIBRATION_CANDIDATE",
        "source_fit": config["id"],
        "learned_factor_count": len(model_record["rules"]) + len(weights),
        "new_residual_sonority_factor_count": len(weights),
        "rule_group_count": int(baseline["experiment"]["rule_group_count"]) + 1,
        "test_loaded": False,
    }
    candidate["model"]["rules"].extend(
        {
            "id": f"F-K3-V24-{index:03d}",
            "family": "residual_strong_sonority_status",
            "clause": feature.label,
            "feature": feature.to_dict(),
            "weight": float(weight),
            "origin": "learned_from_bach_minus_generated_moments",
            "human_authored": False,
            "calls_other_rules": False,
            "rule_group": "RG-LEARNED-V24-001",
        }
        for index, (feature, weight) in enumerate(
            zip(residual_features, weights, strict=True),
            start=1,
        )
    )
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.model.write_text(
        json.dumps(candidate, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v24c] wrote {args.output}", flush=True)
    print(f"[v24c] wrote {args.model}", flush=True)
    print(f"[v24c] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
