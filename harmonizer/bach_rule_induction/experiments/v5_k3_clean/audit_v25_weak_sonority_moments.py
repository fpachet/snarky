#!/usr/bin/env python3
"""Compare V25 weak-sonority moments in Bach and one generated model."""

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
DEFAULT_CONFIG = FACTOR_BASE / "v25_weak_sonority_config.yaml"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v25_weak_sonority_moment_audit.json"
DEFAULT_REPORT = FACTOR_BASE / "V25_WEAK_SONORITY_MOMENT_AUDIT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--label", default="V24")
    parser.add_argument(
        "--split-role",
        choices=("train", "validation"),
        default="train",
    )
    parser.add_argument("--pieces", type=int)
    parser.add_argument("--seeds")
    parser.add_argument("--sweeps", type=int)
    parser.add_argument("--workers", type=int)
    return parser.parse_args()


def weak_status_counts(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
    *,
    candidate_min: int,
    candidate_max: int,
) -> tuple[np.ndarray, int]:
    times = [
        time
        for time in range(1, lattice.size - 1)
        if lattice.metric_levels[time] < 2
    ]
    if not times:
        return np.zeros(len(k3.RESIDUAL_WEAK_SONORITY_NAMES)), 0
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
    statuses = k3.central_residual_weak_sonority_statuses(
        data,
        data.chosen_pitches[:, None],
    )[:, 0]
    counts = np.bincount(
        statuses[statuses >= 0],
        minlength=len(k3.RESIDUAL_WEAK_SONORITY_NAMES),
    ).astype(np.float64)
    return counts, len(times)


def _sample_piece(
    task: tuple[str, str, dict[str, Any], int, int, str],
) -> tuple[np.ndarray, np.ndarray, int]:
    piece_id, score_path, model, seed, sweeps, update_schedule = task
    lattice = k3.extract_piece_lattice(Path(score_path), piece_id)
    fixed = np.zeros_like(lattice.blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    local_seed = generative._piece_seed(piece_id, seed)
    generated = k3.rhythmic_gibbs_sample(
        lattice.blocks,
        lattice.attacks,
        fixed,
        candidate_min=model["candidate_min"],
        candidate_max=model["candidate_max"],
        register_logits=model["register_logits"],
        features=model["features"],
        weights=model["weights"],
        sweeps=sweeps,
        seed=local_seed,
        tonal_logits=model["tonal_logits"],
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels,
        update_schedule=update_schedule,
    )
    authentic, total = weak_status_counts(
        lattice.blocks,
        lattice,
        candidate_min=model["candidate_min"],
        candidate_max=model["candidate_max"],
    )
    sampled, generated_total = weak_status_counts(
        generated,
        lattice,
        candidate_min=model["candidate_min"],
        candidate_max=model["candidate_max"],
    )
    if generated_total != total:
        raise AssertionError("Authentic and generated weak-block totals differ")
    return authentic, sampled, total


def _markdown(result: dict[str, Any]) -> str:
    label = result["experiment"]["model_label"]
    lines = [
        "# V25 — résidu des moments de sonorité faible",
        "",
        f"Le modèle {label} est figé. Ce diagnostic compare ses générations au "
        "corpus sur les neuf statuts V25, sans modifier aucun poids.",
        "",
        f"| Statut | Bach | {label} | Écart Bach − {label} |",
        "|---|---:|---:|---:|",
    ]
    for row in result["moments"]:
        lines.append(
            f"| `{row['label']}` | {row['bach_rate']:.4f} | "
            f"{row['generated_rate']:.4f} | {row['gradient']:+.4f} |"
        )
    lines.extend(
        [
            "",
            f"- Résiduel total Bach : "
            f"`{result['summary']['bach_residual_rate']:.4f}`.",
            f"- Résiduel total {label} : "
            f"`{result['summary']['generated_residual_rate']:.4f}`.",
            f"- MAE des neuf moments : `{result['summary']['moment_mae']:.5f}`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    model_path = args.model or (FACTOR_BASE / config["baseline_model"])
    baseline = json.loads(model_path.read_text(encoding="utf-8"))
    corpus = baseline["corpus"]
    model_record = baseline["model"]
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
    }
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    sampling = config["sampling"]
    available = (
        sorted(splits["train"], key=generative._stable_order)
        if args.split_role == "train"
        else list(splits["validation"])
    )
    piece_ids = available[: int(args.pieces or sampling["pieces"])]
    seeds = (
        [int(value) for value in args.seeds.split(",") if value]
        if args.seeds
        else [int(value) for value in sampling["seeds"]]
    )
    sweeps = int(args.sweeps or sampling["sweeps"])
    workers = int(args.workers or sampling["workers"])
    tasks = [
        (
            piece_id,
            str(generative._score_path(args.scores, piece_id)),
            prepared,
            int(seed),
            sweeps,
            str(sampling["update_schedule"]),
        )
        for piece_id in piece_ids
        for seed in seeds
    ]
    authentic = np.zeros(len(k3.RESIDUAL_WEAK_SONORITY_NAMES))
    sampled = np.zeros_like(authentic)
    weak_total = 0
    with ProcessPoolExecutor(
        max_workers=workers
    ) as executor:
        for completed, (source, generated, total) in enumerate(
            executor.map(_sample_piece, tasks),
            start=1,
        ):
            authentic += source
            sampled += generated
            weak_total += total
            if completed % 8 == 0 or completed == len(tasks):
                print(
                    f"[v25-moments] pieces={completed}/{len(tasks)}",
                    flush=True,
                )
    authentic_rates = authentic / weak_total
    sampled_rates = sampled / weak_total
    gradients = authentic_rates - sampled_rates
    result = {
        "experiment": {
            "id": "K3-V25-WEAK-SONORITY-MOMENT-AUDIT-1",
            "status": "TRAIN_DIAGNOSTIC",
            "model": str(model_path),
            "model_label": args.label,
            "pieces": len(piece_ids),
            "split_role": args.split_role,
            "seeds": seeds,
            "sweeps": sweeps,
            "weights_updated": False,
            "validation_loaded": args.split_role == "validation",
            "test_loaded": False,
        },
        "summary": {
            "weak_blocks": weak_total,
            "bach_residual_rate": float(authentic_rates.sum()),
            "generated_residual_rate": float(sampled_rates.sum()),
            "moment_mae": float(np.abs(gradients).mean()),
        },
        "moments": [
            {
                "status": index,
                "label": label,
                "bach_count": int(authentic[index]),
                "generated_count": int(sampled[index]),
                "bach_rate": float(authentic_rates[index]),
                "generated_rate": float(sampled_rates[index]),
                "gradient": float(gradients[index]),
            }
            for index, label in enumerate(k3.RESIDUAL_WEAK_SONORITY_NAMES)
        ],
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v25-moments] wrote {args.output}", flush=True)
    print(f"[v25-moments] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
