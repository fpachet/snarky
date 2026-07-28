#!/usr/bin/env python3
"""Refit only V6 weights with Bach-minus-Gibbs moment gradients."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v6_generative_refit_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V6_GENERATIVE_WEIGHT_REFIT.md"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


def _grounding_rows(
    dataset: k3.K3Dataset,
    feature: k3.FeatureSpec,
) -> np.ndarray:
    if feature.kind in k3.SHARED_POTENTIAL_KINDS:
        return k3.shared_potential_rows(dataset)
    if feature.target_voice in range(4):
        return dataset.voice_indices == feature.target_voice
    return np.ones(dataset.size, dtype=bool)


def factor_rates(
    chain: generative.Chain,
    blocks: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    candidate_min: int,
    candidate_max: int,
) -> np.ndarray:
    """Measure each selected factor with its declared grounding semantics."""

    dataset = generative._decision_dataset(
        chain,
        blocks,
        candidate_min,
        candidate_max,
    )
    rows = np.arange(dataset.size)
    chosen = dataset.chosen_indices
    rates = np.zeros(len(features), dtype=np.float64)
    for index, feature in enumerate(features):
        applies = _grounding_rows(dataset, feature)
        if not applies.any():
            continue
        active = k3.feature_mask(dataset, feature)[rows, chosen]
        rates[index] = float(active[applies].mean())
    return rates


def _sample(
    chains: list[generative.Chain],
    features: tuple[k3.FeatureSpec, ...],
    weights: np.ndarray,
    *,
    candidate_min: int,
    candidate_max: int,
    register_logits: np.ndarray,
    tonal_logits: np.ndarray,
    sweeps: int,
    seed: int,
) -> None:
    for chain in chains:
        chain.blocks = k3.rhythmic_gibbs_sample(
            chain.blocks,
            chain.lattice.attacks,
            chain.fixed,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            register_logits=register_logits,
            features=features,
            weights=weights,
            sweeps=sweeps,
            seed=generative._piece_seed(chain.piece_id, seed),
            tonal_logits=tonal_logits,
            tonic_pc=chain.lattice.tonic_pc,
            mode=chain.lattice.mode,
            metric_levels=chain.lattice.metric_levels,
        )


def _rates(
    chains: list[generative.Chain],
    *,
    source: bool,
    features: tuple[k3.FeatureSpec, ...],
    candidate_min: int,
    candidate_max: int,
) -> np.ndarray:
    return np.stack(
        [
            factor_rates(
                chain,
                chain.lattice.blocks if source else chain.blocks,
                features,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )


def _markdown(result: dict[str, Any]) -> str:
    calibration = result["model"]["generative_weight_refit"]
    lines = [
        "# V6 — réajustement génératif des poids",
        "",
        "La structure des 30 facteurs est strictement gelée. Seuls leurs poids",
        "sont ajustés par `E_Bach[f] - E_Gibbs[f]` sur un sous-ensemble de train.",
        "Aucune nouvelle feature, règle historique ou contrainte experte n'est",
        "introduite. Le test reste fermé.",
        "",
        "## Résultat d'apprentissage",
        "",
        f"- Pièces train : `{calibration['train_pieces']}`.",
        f"- Époques : `{calibration['epochs']}`.",
        (
            f"- MAE des moments : `{calibration['initial_moment_mae']:.6f}` → "
            f"`{calibration['best_moment_mae']:.6f}`."
        ),
        (
            f"- NLL conditionnelle validation : "
            f"`{calibration['base_validation_nll']:.6f}` → "
            f"`{calibration['validation_nll']:.6f}`."
        ),
        f"- Plus grand déplacement de poids : `{calibration['max_abs_delta']:.6f}`.",
        "",
        "La décision de promotion dépend d'un audit génératif séparé sur les",
        "mêmes pièces et graines que V5.16.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=16)
    parser.add_argument("--burn-in-sweeps", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--sweeps-per-epoch", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--anchor", type=float, default=0.03)
    parser.add_argument("--l1-delta", type=float, default=0.001)
    parser.add_argument("--max-abs-delta", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=6601)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(
        splits["train"],
        key=generative._stable_order,
    )[: args.train_pieces]
    model = payload["model"]
    corpus = payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    features = tuple(k3.feature_from_model_record(rule) for rule in model["rules"])
    initial_weights = np.asarray(
        [float(rule["weight"]) for rule in model["rules"]],
        dtype=np.float64,
    )
    chains: list[generative.Chain] = []
    for piece_id in train_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        initial = rhythmic._randomize_mutable_segments(
            lattice.blocks,
            lattice.attacks,
            fixed,
            register_logits,
            candidate_min,
            generative._piece_seed(piece_id, args.seed),
            tonal_logits,
            lattice.tonic_pc,
            lattice.mode,
        )
        chains.append(generative.Chain(piece_id, lattice, initial, fixed))
    empirical_by_piece = _rates(
        chains,
        source=True,
        features=features,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )
    empirical = empirical_by_piece.mean(axis=0)
    weights = initial_weights.copy()
    _sample(
        chains,
        features,
        weights,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        register_logits=register_logits,
        tonal_logits=tonal_logits,
        sweeps=args.burn_in_sweeps,
        seed=args.seed + 1,
    )
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    best_weights = weights.copy()
    best_mae = float("inf")
    initial_mae = float("nan")
    history: list[dict[str, Any]] = []
    for epoch in range(1, args.epochs + 1):
        generated = _rates(
            chains,
            source=False,
            features=features,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
        ).mean(axis=0)
        moment_error = empirical - generated
        mae = float(np.abs(moment_error).mean())
        if epoch == 1:
            initial_mae = mae
        if mae < best_mae:
            best_mae = mae
            best_weights = weights.copy()
        weights_before_update = weights.copy()
        delta = weights - initial_weights
        gradient = moment_error - args.anchor * delta
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient**2
        corrected_first = first / (1.0 - 0.9**epoch)
        corrected_second = second / (1.0 - 0.999**epoch)
        delta += (
            args.learning_rate * corrected_first / (np.sqrt(corrected_second) + 1e-8)
        )
        delta = np.sign(delta) * np.maximum(
            np.abs(delta) - args.learning_rate * args.l1_delta,
            0.0,
        )
        delta = np.clip(delta, -args.max_abs_delta, args.max_abs_delta)
        weights = initial_weights + delta
        history.append(
            {
                "epoch": epoch,
                "moment_mae": mae,
                "weights_before_update": weights_before_update.tolist(),
                "weights_after_update": weights.tolist(),
                "bach_moments": empirical.tolist(),
                "gibbs_moments": generated.tolist(),
                "gradient": gradient.tolist(),
            }
        )
        print(
            f"[v6-refit] epoch {epoch}/{args.epochs}: "
            f"moment_mae={mae:.6f} max|delta|={np.abs(delta).max():.4f}",
            flush=True,
        )
        _sample(
            chains,
            features,
            weights,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            register_logits=register_logits,
            tonal_logits=tonal_logits,
            sweeps=args.sweeps_per_epoch,
            seed=args.seed + 1 + epoch,
        )
    final_generated = _rates(
        chains,
        source=False,
        features=features,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    ).mean(axis=0)
    final_mae = float(np.abs(empirical - final_generated).mean())
    if final_mae < best_mae:
        best_mae = final_mae
        best_weights = weights.copy()

    full = k3.load_k3_dataset(args.cache)
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, removed = k3.filter_to_domain(
        validation,
        candidate_min,
        candidate_max,
    )
    if removed:
        raise ValueError("validation choices fall outside the train domain")
    validation_nll = generative._conditional_validation_nll(
        validation,
        register_logits,
        tonal_logits,
        features,
        best_weights,
    )
    output = copy.deepcopy(payload)
    output["experiment"] = {
        **payload["experiment"],
        "id": "F-K3-V6-GENERATIVE-WEIGHT-REFIT",
        "status": "WEIGHTS_REFIT_STRUCTURE_FROZEN",
        "source_model": str(args.model.resolve()),
        "test_loaded": False,
        "factor_structure_frozen": True,
        "new_factor_count": 0,
    }
    for rule, weight in zip(
        output["model"]["rules"],
        best_weights,
        strict=True,
    ):
        rule["weight"] = float(weight)
    for factor, weight in zip(
        output["model"]["factors"],
        best_weights,
        strict=True,
    ):
        factor["parameter"]["log_weight"] = float(weight)
        factor["parameter"]["sign"] = "preference" if weight > 0 else "avoidance"
    output["model"]["validation_nll"] = validation_nll
    output["model"]["generative_weight_refit"] = {
        "train_pieces": len(train_ids),
        "piece_ids": train_ids,
        "epochs": args.epochs,
        "burn_in_sweeps": args.burn_in_sweeps,
        "sweeps_per_epoch": args.sweeps_per_epoch,
        "learning_rate": args.learning_rate,
        "anchor_to_conditional_weights": args.anchor,
        "l1_delta": args.l1_delta,
        "max_abs_delta_allowed": args.max_abs_delta,
        "max_abs_delta": float(np.max(np.abs(best_weights - initial_weights))),
        "initial_moment_mae": initial_mae,
        "best_moment_mae": best_mae,
        "base_validation_nll": float(model["validation_nll"]),
        "validation_nll": validation_nll,
        "gradient": "E_Bach[f] - E_Gibbs[f]",
        "history": history,
        "test_loaded": False,
        "factor_structure_changed": False,
    }
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(output), encoding="utf-8")
    print(f"[v6-refit] wrote {args.output}", flush=True)
    print(f"[v6-refit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
