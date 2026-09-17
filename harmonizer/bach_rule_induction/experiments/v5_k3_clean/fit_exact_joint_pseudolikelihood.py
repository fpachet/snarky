#!/usr/bin/env python3
"""Fit K3 weights from the exact conditional worlds used by rhythmic Gibbs."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import fit_joint_pseudolikelihood as central_pl
import k3
import numpy as np
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_STRUCTURE_MODEL = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CENTRAL_MODEL = FACTOR_BASE / "v8_joint_pseudolikelihood_model.json"
DEFAULT_GENERATIVE_REFERENCE = (
    FACTOR_BASE / "v6_train64_multimetric_iteration2_model.json"
)
DEFAULT_RESIDUAL = FACTOR_BASE / "v6_iteration3_residual_feature_diagnostic.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v8_exact_joint_pseudolikelihood_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V8_EXACT_JOINT_PSEUDOLIKELIHOOD_MODEL.md"
DEFAULT_CACHE = HERE / "work/k3-exact-joint-pl-32x10.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


def _eligible_segments(
    lattice: k3.RhythmicLattice,
) -> tuple[tuple[int, int, int], ...]:
    """Mirror the generation task: fixed soprano and fixed boundary states."""

    return tuple(
        segment
        for segment in k3.attack_segments(lattice.attacks)
        if segment[2] != 0
        and segment[0] > 0
        and segment[1] < lattice.size
    )


def _piece_examples(
    task: tuple[
        str,
        Path,
        tuple[k3.FeatureSpec, ...],
        np.ndarray,
        np.ndarray,
        int,
        int,
    ],
) -> tuple[
    str,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    (
        piece_id,
        score_path,
        features,
        register,
        tonal,
        candidate_min,
        candidate_max,
    ) = task
    lattice = k3.extract_piece_lattice(score_path, piece_id)
    candidates = np.arange(candidate_min, candidate_max + 1, dtype=np.int16)
    base_rows = []
    factor_rows = []
    chosen = []
    voices = []
    modes = []
    tonics = []
    for start, end, voice in _eligible_segments(lattice):
        base, totals = k3.candidate_segment_components(
            lattice.blocks,
            lattice.attacks,
            k3.segment_energy_times((start, end, voice), lattice.size),
            start,
            end,
            voice,
            candidates,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            register_logits=register,
            features=features,
            tonal_logits=tonal,
            tonic_pc=lattice.tonic_pc,
            mode=lattice.mode,
            metric_levels=lattice.metric_levels,
        )
        if not np.allclose(totals, np.rint(totals)):
            raise ValueError(f"{piece_id}: non-integral factor grounding count")
        if totals.max(initial=0) > np.iinfo(np.uint8).max:
            raise ValueError(f"{piece_id}: factor grounding count exceeds uint8")
        base_rows.append(base)
        factor_rows.append(totals.astype(np.uint8))
        chosen.append(int(lattice.blocks[start, voice]) - candidate_min)
        voices.append(voice)
        modes.append(lattice.mode)
        tonics.append(lattice.tonic_pc)
    return (
        piece_id,
        np.asarray(base_rows, dtype=np.float64),
        np.asarray(factor_rows, dtype=np.uint8),
        np.asarray(chosen, dtype=np.int16),
        np.asarray(voices, dtype=np.int8),
        np.asarray(modes, dtype=np.int8),
        np.asarray(tonics, dtype=np.int8),
    )


def _build_split(
    piece_ids: list[str],
    *,
    scores: Path,
    features: tuple[k3.FeatureSpec, ...],
    register: np.ndarray,
    tonal: np.ndarray,
    candidate_min: int,
    candidate_max: int,
    workers: int,
    label: str,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    tasks = [
        (
            piece_id,
            generative._score_path(scores, piece_id),
            features,
            register,
            tonal,
            candidate_min,
            candidate_max,
        )
        for piece_id in piece_ids
    ]
    executor = (
        None if workers == 1 else ProcessPoolExecutor(max_workers=workers)
    )
    results = []
    try:
        generated = (
            map(_piece_examples, tasks)
            if executor is None
            else executor.map(_piece_examples, tasks)
        )
        for index, result in enumerate(generated, start=1):
            results.append(result)
            print(
                f"[exact-pl] {label} {index}/{len(tasks)} {result[0]} "
                f"({result[3].size} choices)",
                flush=True,
            )
    finally:
        if executor is not None:
            executor.shutdown()
    return (
        np.concatenate([result[1] for result in results]),
        np.concatenate([result[2] for result in results]),
        np.concatenate([result[3] for result in results]),
        np.concatenate(
            [
                np.full(
                    result[3].size,
                    result[0],
                    dtype=f"<U{max(map(len, piece_ids))}",
                )
                for result in results
            ]
        ),
        np.concatenate([result[4] for result in results]),
        np.concatenate([result[5] for result in results]),
        np.concatenate([result[6] for result in results]),
    )


def _probabilities(
    base_scores: np.ndarray,
    factors: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    scores = base_scores + np.tensordot(factors, weights, axes=([2], [0]))
    scores -= scores.max(axis=1, keepdims=True)
    probabilities = np.exp(scores)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    return probabilities


def _nll(
    base_scores: np.ndarray,
    factors: np.ndarray,
    chosen: np.ndarray,
    weights: np.ndarray,
) -> float:
    probabilities = _probabilities(base_scores, factors, weights)
    selected = probabilities[np.arange(chosen.size), chosen]
    return float(-np.log(np.maximum(selected, 1e-12)).mean())


def _fit(
    train_base: np.ndarray,
    train_factors: np.ndarray,
    train_chosen: np.ndarray,
    validation_base: np.ndarray,
    validation_factors: np.ndarray,
    validation_chosen: np.ndarray,
    initial_weights: np.ndarray,
    *,
    max_steps: int,
    learning_rate: float,
    l1: float,
    l2: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    weights = initial_weights.astype(np.float64, copy=True)
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    best = weights.copy()
    best_validation = _nll(
        validation_base,
        validation_factors,
        validation_chosen,
        weights,
    )
    history = [
        {
            "step": 0,
            "train_nll": _nll(
                train_base,
                train_factors,
                train_chosen,
                weights,
            ),
            "validation_nll": best_validation,
            "active_weights": int((np.abs(weights) >= 0.05).sum()),
        }
    ]
    rows = np.arange(train_chosen.size)
    for step in range(1, max_steps + 1):
        probabilities = _probabilities(train_base, train_factors, weights)
        probabilities[rows, train_chosen] -= 1.0
        gradient = (
            np.einsum(
                "ncr,nc->r",
                train_factors,
                probabilities,
                optimize=True,
            )
            / train_chosen.size
        )
        gradient += l2 * weights
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient**2
        corrected_first = first / (1.0 - 0.9**step)
        corrected_second = second / (1.0 - 0.999**step)
        weights -= learning_rate * corrected_first / (
            np.sqrt(corrected_second) + 1e-8
        )
        weights = np.sign(weights) * np.maximum(
            np.abs(weights) - learning_rate * l1,
            0.0,
        )
        if step == 1 or step % 10 == 0 or step == max_steps:
            train_nll = _nll(
                train_base,
                train_factors,
                train_chosen,
                weights,
            )
            validation_nll = _nll(
                validation_base,
                validation_factors,
                validation_chosen,
                weights,
            )
            history.append(
                {
                    "step": step,
                    "train_nll": train_nll,
                    "validation_nll": validation_nll,
                    "active_weights": int((np.abs(weights) >= 0.05).sum()),
                }
            )
            print(
                f"[exact-pl] step={step} train={train_nll:.6f} "
                f"validation={validation_nll:.6f}",
                flush=True,
            )
            if validation_nll < best_validation:
                best_validation = validation_nll
                best = weights.copy()
    return best, {
        "best_validation_nll": best_validation,
        "history": history,
    }


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    comparison = result["comparison"]
    model = result["model"]
    return "\n".join(
        [
            "# V8 — pseudo-vraisemblance exacte des mondes Gibbs",
            "",
            "Chaque alternative remplace une attaque et toute sa tenue. Son",
            "vecteur factoriel somme exactement tous les noyaux K3 et toutes les",
            "portées que le sampler Gibbs recompte. Le soprano et les états de",
            "bord sont fixes, comme pendant la génération.",
            "",
            "## Corpus de développement",
            "",
            f"- Pièces train : `{experiment['train_pieces']}`.",
            f"- Pièces validation : `{experiment['validation_pieces']}`.",
            f"- Choix train : `{experiment['train_choices']}`.",
            f"- Choix validation : `{experiment['validation_choices']}`.",
            f"- Alternatives par choix : `{experiment['candidate_count']}`.",
            f"- Facteurs appris conjointement : `{experiment['factor_count']}`.",
            "- Test réservé : non chargé.",
            "",
            "## NLL exacte",
            "",
            "| Poids | Validation |",
            "|---|---:|",
            (
                f"| V6 pseudo-vraisemblance centrale | "
                f"{comparison['v6_exact_validation_nll']:.6f} |"
            ),
            (
                f"| Iteration 2 générative | "
                f"{comparison['iteration2_exact_validation_nll']:.6f} |"
            ),
            (
                f"| V8 pseudo-vraisemblance centrale | "
                f"{comparison['central_v8_exact_validation_nll']:.6f} |"
            ),
            f"| V8 exacte | **{model['validation_nll']:.6f}** |",
            "",
            "La promotion dépend des audits génératifs à 6 et 30 sweeps.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure-model", type=Path, default=DEFAULT_STRUCTURE_MODEL)
    parser.add_argument("--central-model", type=Path, default=DEFAULT_CENTRAL_MODEL)
    parser.add_argument(
        "--generative-reference",
        type=Path,
        default=DEFAULT_GENERATIVE_REFERENCE,
    )
    parser.add_argument("--residual", type=Path, default=DEFAULT_RESIDUAL)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--train-pieces", type=int, default=32)
    parser.add_argument("--validation-pieces", type=int, default=10)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument("--l1", type=float, default=0.0005)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    structure_payload = json.loads(args.structure_model.read_text(encoding="utf-8"))
    central_payload = json.loads(args.central_model.read_text(encoding="utf-8"))
    reference_payload = json.loads(
        args.generative_reference.read_text(encoding="utf-8")
    )
    residual_payload = json.loads(args.residual.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)[
        : args.train_pieces
    ]
    validation_ids = list(splits["validation"])[: args.validation_pieces]
    records = central_pl._combined_records(structure_payload, residual_payload)
    features = tuple(record["feature"] for record in records)
    corpus = structure_payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register = np.asarray(
        structure_payload["model"]["register_logits"],
        dtype=np.float64,
    )
    tonal = np.asarray(
        structure_payload["model"]["tonal_logits"],
        dtype=np.float64,
    )
    expected_metadata = {
        "schema_version": 1,
        "train_ids": train_ids,
        "validation_ids": validation_ids,
        "feature_keys": [feature.key for feature in features],
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
        "scope": "all_affected_k3_worlds_fixed_soprano_and_boundaries",
    }
    if args.cache.exists():
        archive = np.load(args.cache)
        metadata = json.loads(str(archive["metadata"]))
        if metadata != expected_metadata:
            raise ValueError("Exact pseudo-likelihood cache contract changed")
        train_base = archive["train_base"]
        train_factors = archive["train_factors"]
        train_chosen = archive["train_chosen"]
        validation_base = archive["validation_base"]
        validation_factors = archive["validation_factors"]
        validation_chosen = archive["validation_chosen"]
        print(f"[exact-pl] loaded {args.cache}", flush=True)
    else:
        train_base, train_factors, train_chosen, _, _, _, _ = _build_split(
            train_ids,
            scores=args.scores,
            features=features,
            register=register,
            tonal=tonal,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            workers=args.workers,
            label="train",
        )
        (
            validation_base,
            validation_factors,
            validation_chosen,
            _,
            _,
            _,
            _,
        ) = _build_split(
            validation_ids,
            scores=args.scores,
            features=features,
            register=register,
            tonal=tonal,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            workers=args.workers,
            label="validation",
        )
        args.cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            args.cache,
            metadata=json.dumps(expected_metadata, sort_keys=True),
            train_base=train_base,
            train_factors=train_factors,
            train_chosen=train_chosen,
            validation_base=validation_base,
            validation_factors=validation_factors,
            validation_chosen=validation_chosen,
        )
        print(f"[exact-pl] wrote {args.cache}", flush=True)

    structure_weight_by_key = {
        k3.feature_from_model_record(rule).key: float(rule["weight"])
        for rule in structure_payload["model"]["rules"]
    }
    initial_weights = np.asarray(
        [structure_weight_by_key.get(feature.key, 0.0) for feature in features],
        dtype=np.float64,
    )
    central_weight_by_key = {
        k3.feature_from_model_record(rule).key: float(rule["weight"])
        for rule in central_payload["model"]["rules"]
    }
    central_weights = np.asarray(
        [central_weight_by_key[feature.key] for feature in features],
        dtype=np.float64,
    )
    reference_weight_by_key = {
        k3.feature_from_model_record(rule).key: float(rule["weight"])
        for rule in reference_payload["model"]["rules"]
    }
    reference_weights = np.asarray(
        [reference_weight_by_key.get(feature.key, 0.0) for feature in features],
        dtype=np.float64,
    )
    weights, diagnostics = _fit(
        train_base,
        train_factors,
        train_chosen,
        validation_base,
        validation_factors,
        validation_chosen,
        initial_weights,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        l1=args.l1,
        l2=args.l2,
    )
    train_nll = _nll(train_base, train_factors, train_chosen, weights)
    validation_nll = _nll(
        validation_base,
        validation_factors,
        validation_chosen,
        weights,
    )
    result = {
        "experiment": {
            "id": "F-K3-V8-EXACT-JOINT-PSEUDOLIKELIHOOD",
            "status": "DEVELOPMENT_CANDIDATE",
            "test_loaded": False,
            "scope_matches_gibbs": True,
            "fixed_soprano": True,
            "fixed_boundary_states": True,
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "train_piece_ids": train_ids,
            "validation_piece_ids": validation_ids,
            "train_choices": int(train_chosen.size),
            "validation_choices": int(validation_chosen.size),
            "candidate_count": candidate_max - candidate_min + 1,
            "factor_count": len(features),
            "maximum_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
            "l2": args.l2,
            "cache": str(args.cache.resolve()),
        },
        "corpus": {
            **corpus,
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "train_decisions": int(train_chosen.size),
            "validation_decisions": int(validation_chosen.size),
        },
        "comparison": {
            "v6_exact_validation_nll": _nll(
                validation_base,
                validation_factors,
                validation_chosen,
                initial_weights,
            ),
            "iteration2_exact_validation_nll": _nll(
                validation_base,
                validation_factors,
                validation_chosen,
                reference_weights,
            ),
            "central_v8_exact_validation_nll": _nll(
                validation_base,
                validation_factors,
                validation_chosen,
                central_weights,
            ),
        },
        "model": {
            "register_logits": register.tolist(),
            "tonal_logits": tonal.tolist(),
            "train_nll": train_nll,
            "validation_nll": validation_nll,
            "rules": [
                {
                    "feature": record["feature"].to_dict(),
                    "weight": float(weight),
                    "origin": record["origin"],
                    "family": record["family"],
                    "description": record["description"],
                    "selection": record["selection"],
                }
                for record, weight in zip(records, weights, strict=True)
            ],
            "fit": diagnostics,
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[exact-pl] validation={validation_nll:.6f}", flush=True)
    print(f"[exact-pl] wrote {args.output}", flush=True)
    print(f"[exact-pl] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
