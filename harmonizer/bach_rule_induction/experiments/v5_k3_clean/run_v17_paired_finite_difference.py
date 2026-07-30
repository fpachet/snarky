#!/usr/bin/env python3
"""Screen exact candidates by paired finite differences of the real sampler."""

from __future__ import annotations

import argparse
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_explicit_generation_audit as audit
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v13_exact_directed_metric_model.json"
DEFAULT_SHORTLIST = FACTOR_BASE / "v16_exact_candidate_shortlist.json"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v17_paired_fd_screen.json"
DEFAULT_REPORT = FACTOR_BASE / "V17_PAIRED_FD_SCREEN.md"
GUARDED_METRICS = (
    "bass_large_leap_rate",
    "strong_nontriadic_rate",
    "strong_pair_dissonances_per_block",
)


def _conditional_step(candidate: dict[str, Any], max_abs_step: float) -> float:
    statistic = candidate["conditional"]
    gradient = float(statistic["gradient"])
    gain = float(statistic["approximate_nll_gain"])
    if abs(gradient) <= 1e-12 or gain <= 0:
        return 0.0
    return float(np.clip(2.0 * gain / gradient, -max_abs_step, max_abs_step))


def _mean_interval(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    standard_error = (
        0.0
        if values.size < 2
        else float(values.std(ddof=1) / math.sqrt(values.size))
    )
    return {
        "mean": mean,
        "ci95_low": mean - 1.96 * standard_error,
        "ci95_high": mean + 1.96 * standard_error,
    }


def _distance(
    generated: np.ndarray,
    bach: np.ndarray,
    scales: np.ndarray,
) -> float:
    return float(np.abs((generated - bach) / scales).sum())


def evaluate_paired_candidate(
    *,
    baseline: np.ndarray,
    candidate: np.ndarray,
    bach: np.ndarray,
    scales: np.ndarray,
    metric_keys: tuple[str, ...],
) -> dict[str, Any]:
    """Summarize one paired perturbation across pieces and seeds."""

    baseline_mean = baseline.mean(axis=(0, 1))
    candidate_mean = candidate.mean(axis=(0, 1))
    bach_mean = bach.mean(axis=0)
    baseline_distance = _distance(baseline_mean, bach_mean, scales)
    candidate_distance = _distance(candidate_mean, bach_mean, scales)
    per_seed_remaining = []
    for seed_index in range(baseline.shape[1]):
        before = _distance(
            baseline[:, seed_index].mean(axis=0),
            bach_mean,
            scales,
        )
        after = _distance(
            candidate[:, seed_index].mean(axis=0),
            bach_mean,
            scales,
        )
        per_seed_remaining.append(after / max(before, 1e-12))
    per_piece_delta = []
    for piece_index in range(baseline.shape[0]):
        before = np.mean(
            [
                _distance(row, bach[piece_index], scales)
                for row in baseline[piece_index]
            ]
        )
        after = np.mean(
            [
                _distance(row, bach[piece_index], scales)
                for row in candidate[piece_index]
            ]
        )
        per_piece_delta.append(after - before)
    guard_deltas = {
        key: float(
            abs(candidate_mean[index] - bach_mean[index])
            - abs(baseline_mean[index] - bach_mean[index])
        )
        for index, key in enumerate(metric_keys)
        if key in GUARDED_METRICS
    }
    relative_remaining = candidate_distance / max(baseline_distance, 1e-12)
    return {
        "baseline_standardized_l1": baseline_distance,
        "candidate_standardized_l1": candidate_distance,
        "ensemble_relative_remaining": relative_remaining,
        "per_seed_relative_remaining": per_seed_remaining,
        "per_piece_standardized_l1_delta": _mean_interval(
            np.asarray(per_piece_delta)
        ),
        "guarded_absolute_error_deltas": guard_deltas,
        "improves_ensemble": relative_remaining < 1.0,
        "improves_every_seed": max(per_seed_remaining) < 1.0,
        "passes_guarded_metrics": all(
            value <= 0 for value in guard_deltas.values()
        ),
    }


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V17 — différences finies appariées du sampler",
        "",
        "Chaque candidat est réellement ajouté au modèle avec un petit poids.",
        "V13 et sa perturbation utilisent la même pièce, le même état initial et",
        "le même flux pseudo-aléatoire. Aucun gradient d'équilibre n'est supposé.",
        "",
        f"- Split : `{experiment['split_role']}`.",
        f"- Pièces : `{experiment['pieces']}`.",
        f"- Graines : `{experiment['seeds']}`.",
        f"- Horizon : `{experiment['sweeps']}` balayages.",
        f"- Candidats : `{experiment['candidate_count']}`.",
        f"- Test réservé chargé : `{str(experiment['test_loaded']).lower()}`.",
        "",
        "| Rang | Candidat | Pas | Résidu relatif | Toutes graines | Gardes |",
        "|---:|---|---:|---:|---|---|",
    ]
    for candidate in result["candidates"]:
        paired = candidate["paired"]
        lines.append(
            f"| {candidate['rank']} | `{candidate['feature']['label']}` | "
            f"{candidate['weight_step']:+.6f} | "
            f"{paired['ensemble_relative_remaining']:.3f} | "
            f"{str(paired['improves_every_seed']).lower()} | "
            f"{str(paired['passes_guarded_metrics']).lower()} |"
        )
    lines.extend(
        [
            "",
            "Une amélioration sur ce petit écran train n'admet pas encore le",
            "facteur. Les survivants doivent être répliqués sur 32 pièces, trois",
            "graines et aux horizons 6 et 30 avant tout refit exact borné.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--shortlist", type=Path, default=DEFAULT_SHORTLIST)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument(
        "--split-role",
        choices=("train", "validation"),
        default="train",
    )
    parser.add_argument("--pieces", type=int, default=8)
    parser.add_argument("--piece-offset", type=int, default=0)
    parser.add_argument("--seeds", default="10103,20207")
    parser.add_argument("--sweeps", type=int, default=6)
    parser.add_argument("--candidate-ranks", default="all")
    parser.add_argument("--max-abs-step", type=float, default=0.15)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.pieces <= 0
        or args.piece_offset < 0
        or args.sweeps <= 0
        or args.max_abs_step <= 0
        or args.workers <= 0
    ):
        raise ValueError("Invalid finite-difference screen parameters")
    source = json.loads(args.model.read_text(encoding="utf-8"))
    shortlist = json.loads(args.shortlist.read_text(encoding="utf-8"))
    requested_ranks = (
        {candidate["rank"] for candidate in shortlist["candidates"]}
        if args.candidate_ranks == "all"
        else {
            int(value)
            for value in args.candidate_ranks.split(",")
            if value
        }
    )
    candidates = [
        candidate
        for candidate in shortlist["candidates"]
        if candidate["rank"] in requested_ranks
    ]
    found_ranks = {candidate["rank"] for candidate in candidates}
    if not candidates or found_ranks != requested_ranks:
        raise ValueError("Requested candidate ranks are absent from the shortlist")
    seeds = tuple(int(value) for value in args.seeds.split(",") if value)
    if not seeds:
        raise ValueError("At least one seed is required")

    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    available_ids = (
        sorted(splits["train"], key=generative._stable_order)
        if args.split_role == "train"
        else list(splits["validation"])
    )
    piece_ids = available_ids[
        args.piece_offset : args.piece_offset + args.pieces
    ]
    if len(piece_ids) != args.pieces:
        raise ValueError("Requested finite-difference piece slice is incomplete")
    lattices = {
        piece_id: k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        for piece_id in piece_ids
    }
    model = source["model"]
    base_model = {
        "register_logits": np.asarray(model["register_logits"], dtype=np.float64),
        "tonal_logits": np.asarray(model["tonal_logits"], dtype=np.float64),
        "features": tuple(
            k3.feature_from_model_record(rule) for rule in model["rules"]
        ),
        "weights": np.asarray(
            [float(rule["weight"]) for rule in model["rules"]],
            dtype=np.float64,
        ),
    }
    prepared = {"V13": base_model}
    candidate_steps = {}
    for candidate in candidates:
        step = _conditional_step(candidate, args.max_abs_step)
        candidate_steps[candidate["rank"]] = step
        prepared[f"candidate-{candidate['rank']}"] = {
            **base_model,
            "features": (
                *base_model["features"],
                k3.feature_from_model_record(candidate["feature"]),
            ),
            "weights": np.append(base_model["weights"], step),
        }
    corpus = source["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    tasks = [
        (
            label,
            lattices[piece_id],
            prepared_model,
            candidate_min,
            candidate_max,
            seed,
            args.sweeps,
        )
        for piece_id in piece_ids
        for seed in seeds
        for label, prepared_model in prepared.items()
    ]
    executor = (
        None if args.workers == 1 else ProcessPoolExecutor(max_workers=args.workers)
    )
    try:
        generated = (
            map(audit._generation_metrics, tasks)
            if executor is None
            else executor.map(audit._generation_metrics, tasks)
        )
        rows = list(generated)
    finally:
        if executor is not None:
            executor.shutdown()

    first_lattice = next(iter(lattices.values()))
    metric_keys = tuple(audit._metrics(first_lattice.blocks, first_lattice))
    bach = np.asarray(
        [
            [
                audit._metrics(
                    lattices[piece_id].blocks,
                    lattices[piece_id],
                )[key]
                for key in metric_keys
            ]
            for piece_id in piece_ids
        ],
        dtype=np.float64,
    )
    values: dict[tuple[str, str], list[np.ndarray]] = {}
    for piece_id in piece_ids:
        for label in prepared:
            values[(piece_id, label)] = []
    for piece_id, label, metrics in rows:
        values[(piece_id, label)].append(
            np.asarray([metrics[key] for key in metric_keys], dtype=np.float64)
        )
    generated_by_label = {
        label: np.stack(
            [
                np.stack(values[(piece_id, label)])
                for piece_id in piece_ids
            ]
        )
        for label in prepared
    }
    scales = np.maximum(bach.std(axis=0, ddof=1), 0.01)
    baseline = generated_by_label["V13"]
    evaluated = []
    for candidate in candidates:
        paired = evaluate_paired_candidate(
            baseline=baseline,
            candidate=generated_by_label[f"candidate-{candidate['rank']}"],
            bach=bach,
            scales=scales,
            metric_keys=metric_keys,
        )
        evaluated.append(
            {
                "rank": candidate["rank"],
                "family": candidate["family"],
                "feature": candidate["feature"],
                "conditional": candidate["conditional"],
                "weight_step": candidate_steps[candidate["rank"]],
                "paired": paired,
            }
        )
    evaluated.sort(
        key=lambda candidate: (
            candidate["paired"]["ensemble_relative_remaining"],
            candidate["rank"],
        )
    )
    result = {
        "experiment": {
            "id": "F-K3-V17-PAIRED-FINITE-DIFFERENCE-SCREEN",
            "status": "TRAIN_SCREEN_PENDING_REPLICATION",
            "source_model": str(args.model.resolve()),
            "shortlist": str(args.shortlist.resolve()),
            "split_role": args.split_role,
            "pieces": len(piece_ids),
            "piece_ids": piece_ids,
            "seeds": list(seeds),
            "sweeps": args.sweeps,
            "candidate_count": len(candidates),
            "candidate_ranks": sorted(requested_ranks),
            "max_abs_step": args.max_abs_step,
            "paired_initialization": True,
            "paired_random_stream": True,
            "test_loaded": False,
        },
        "metric_keys": list(metric_keys),
        "diagnostic_scales": scales.tolist(),
        "candidates": evaluated,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v17-paired-fd] wrote {args.output}", flush=True)
    print(f"[v17-paired-fd] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
