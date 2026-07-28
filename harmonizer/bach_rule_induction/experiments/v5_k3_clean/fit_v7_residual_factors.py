#!/usr/bin/env python3
"""Fit a six-factor V7 extension while freezing all V6 parameters."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import k3
import numpy as np
import refit_v6_generative_weights as refit
import run_generative_moment_calibration as generative
import run_v6_factor_controllability as control

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v6_train64_multimetric_iteration2_model.json"
DEFAULT_DIAGNOSTIC = FACTOR_BASE / "v6_iteration3_residual_feature_diagnostic.json"
DEFAULT_CHAIN_CACHE = HERE / "work/v6_iteration3_seed10103_chains.npz"
DEFAULT_CONTEXT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v7_residual_six_factor_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V7_RESIDUAL_SIX_FACTOR_MODEL.md"
DEFAULT_FINAL_CACHE = HERE / "work/v7_residual_six_factor_chains.npz"


def _choose_two_per_family(
    records: list[dict[str, Any]],
    families: tuple[str, ...] = (
        "bass_motion",
        "vertical_context",
        "sonority_transition",
    ),
) -> list[dict[str, Any]]:
    """Choose the strongest positive and negative residual in each family."""

    chosen = []
    for family in families:
        local = [record for record in records if record["family"] == family]
        positive = [record for record in local if record["gradient"] > 0]
        negative = [record for record in local if record["gradient"] < 0]
        if not positive or not negative:
            raise ValueError(f"Family {family} lacks one residual sign")
        chosen.append(max(positive, key=lambda record: record["selection_score"]))
        chosen.append(max(negative, key=lambda record: record["selection_score"]))
    return chosen


def _markdown(result: dict[str, Any]) -> str:
    learning = result["model"]["v7_residual_learning"]
    lines = [
        (
            f"# V7 — {len(learning['factors'])} facteurs résiduels, "
            "socle V6 gelé"
        ),
        "",
        "V7 ajoute deux facteurs par famille résiduelle retenue : un gradient",
        "positif et un gradient négatif. Les 30 facteurs V6, leurs poids, les",
        "baselines de registre et de tonalité restent inchangés.",
        "",
        "## Facteurs ajoutés",
        "",
        "| Facteur | Famille | Description | Poids appris |",
        "|---|---|---|---:|",
    ]
    for record in learning["factors"]:
        lines.append(
            f"| `{record['id']}` | `{record['family']}` | "
            f"{record['description']} | {record['weight']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## Apprentissage train",
            "",
            (
                f"- MAE des six moments : "
                f"`{learning['initial_moment_mae']:.6f}` → "
                f"`{learning['best_moment_mae']:.6f}`."
            ),
            (
                f"- NLL conditionnelle validation : "
                f"`{learning['source_validation_nll']:.6f}` → "
                f"`{learning['validation_nll']:.6f}`."
            ),
            f"- Époque retenue : `{learning['best_epoch']}`.",
            "",
            "Le modèle reste candidat jusqu'aux audits génératifs appariés à 6 et",
            "30 sweeps. Le test réservé n'est pas chargé.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--diagnostic", type=Path, default=DEFAULT_DIAGNOSTIC)
    parser.add_argument("--chain-cache", type=Path, default=DEFAULT_CHAIN_CACHE)
    parser.add_argument("--context-cache", type=Path, default=DEFAULT_CONTEXT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--sweeps-per-epoch", type=int, default=2)
    parser.add_argument("--final-sweeps", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--anchor", type=float, default=0.05)
    parser.add_argument("--max-abs-weight", type=float, default=0.5)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=47017)
    parser.add_argument(
        "--families",
        default="bass_motion,vertical_context,sonority_transition",
    )
    parser.add_argument(
        "--experiment-id",
        default="F-K3-V7-RESIDUAL-SIX-FACTOR",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--final-chain-cache", type=Path, default=DEFAULT_FINAL_CACHE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.epochs <= 0
        or args.sweeps_per_epoch <= 0
        or args.final_sweeps <= 0
        or args.workers <= 0
    ):
        raise ValueError("Epochs, sweeps and workers must be positive")
    source = json.loads(args.model.read_text(encoding="utf-8"))
    diagnostic = json.loads(args.diagnostic.read_text(encoding="utf-8"))
    if (
        diagnostic["experiment"]["test_loaded"]
        or diagnostic["experiment"]["source_model"] != str(args.model.resolve())
    ):
        raise ValueError("Residual diagnostic does not match the train-only model")
    families = tuple(value for value in args.families.split(",") if value)
    if not families or len(set(families)) != len(families):
        raise ValueError("At least one unique residual family is required")
    chosen_records = _choose_two_per_family(
        diagnostic["selected"],
        families,
    )
    new_features = tuple(
        k3.FeatureSpec.from_dict(record["feature"]) for record in chosen_records
    )
    base_model = source["model"]
    base_features = tuple(
        k3.feature_from_model_record(rule) for rule in base_model["rules"]
    )
    if {feature.key for feature in new_features} & {
        feature.key for feature in base_features
    }:
        raise ValueError("V7 residual factors must be structurally new")
    base_weights = np.asarray(
        [rule["weight"] for rule in base_model["rules"]],
        dtype=np.float64,
    )
    corpus = source["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(base_model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(base_model["tonal_logits"], dtype=np.float64)

    cached_states, cache_metadata = control._load_chain_cache(args.chain_cache)
    expected_hash = hashlib.sha256(base_weights.tobytes()).hexdigest()
    if cache_metadata["weights_sha256"] != expected_hash:
        raise ValueError("V7 initial chains do not match the frozen V6 weights")
    piece_ids = tuple(diagnostic["experiment"]["piece_ids"])
    chains = []
    for piece_id in piece_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        for replica in range(2):
            chain_id = f"{piece_id}#replica={replica}"
            blocks = cached_states[chain_id].copy()
            chains.append(generative.Chain(chain_id, lattice, blocks, fixed))

    empirical = np.stack(
        [
            refit.factor_rates(
                chain,
                chain.lattice.blocks,
                new_features,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    ).mean(axis=0)
    weights = np.zeros(len(new_features), dtype=np.float64)
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    best_weights = weights.copy()
    best_mae = float("inf")
    best_epoch = 0
    initial_mae = float("nan")
    history = []
    executor = ProcessPoolExecutor(max_workers=args.workers)
    try:
        for epoch in range(1, args.epochs + 1):
            generated = np.stack(
                [
                    refit.factor_rates(
                        chain,
                        chain.blocks,
                        new_features,
                        candidate_min,
                        candidate_max,
                    )
                    for chain in chains
                ]
            ).mean(axis=0)
            error = empirical - generated
            mae = float(np.abs(error).mean())
            if epoch == 1:
                initial_mae = mae
            if mae < best_mae:
                best_mae = mae
                best_weights = weights.copy()
                best_epoch = epoch
            gradient = error - args.anchor * weights
            first = 0.9 * first + 0.1 * gradient
            second = 0.999 * second + 0.001 * gradient**2
            corrected_first = first / (1.0 - 0.9**epoch)
            corrected_second = second / (1.0 - 0.999**epoch)
            weights += (
                args.learning_rate
                * corrected_first
                / (np.sqrt(corrected_second) + 1e-8)
            )
            weights = np.clip(
                weights,
                -args.max_abs_weight,
                args.max_abs_weight,
            )
            history.append(
                {
                    "epoch": epoch,
                    "moment_mae": mae,
                    "bach_moments": empirical.tolist(),
                    "gibbs_moments": generated.tolist(),
                    "gradient": gradient.tolist(),
                    "weights_after_update": weights.tolist(),
                }
            )
            print(
                f"[v7-fit] epoch {epoch}/{args.epochs}: "
                f"moment_mae={mae:.6f}",
                flush=True,
            )
            refit._sample(
                chains,
                (*base_features, *new_features),
                np.concatenate((base_weights, weights)),
                candidate_min=candidate_min,
                candidate_max=candidate_max,
                register_logits=register_logits,
                tonal_logits=tonal_logits,
                sweeps=args.sweeps_per_epoch,
                seed=args.seed + epoch,
                executor=executor,
            )
    finally:
        executor.shutdown()

    final_executor = ProcessPoolExecutor(max_workers=args.workers)
    try:
        refit._sample(
            chains,
            (*base_features, *new_features),
            np.concatenate((base_weights, best_weights)),
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            register_logits=register_logits,
            tonal_logits=tonal_logits,
            sweeps=args.final_sweeps,
            seed=args.seed + 10_000,
            executor=final_executor,
        )
    finally:
        final_executor.shutdown()

    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    full = k3.load_k3_dataset(args.context_cache)
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, removed = k3.filter_to_domain(
        validation,
        candidate_min,
        candidate_max,
    )
    if removed:
        raise ValueError("Validation choices fall outside the train domain")
    combined_features = (*base_features, *new_features)
    combined_weights = np.concatenate((base_weights, best_weights))
    validation_nll = generative._conditional_validation_nll(
        validation,
        register_logits,
        tonal_logits,
        combined_features,
        combined_weights,
    )

    output = copy.deepcopy(source)
    output["experiment"] = {
        **source["experiment"],
        "id": args.experiment_id,
        "status": "PENDING_GENERATIVE_AUDIT",
        "source_model": str(args.model.resolve()),
        "residual_diagnostic": str(args.diagnostic.resolve()),
        "base_factor_count": len(base_features),
        "new_factor_count": len(new_features),
        "factor_structure_frozen_during_weight_fit": True,
        "test_loaded": False,
    }
    for index, (feature, record, weight) in enumerate(
        zip(new_features, chosen_records, best_weights, strict=True),
        start=1,
    ):
        selection = {
            key: value
            for key, value in record.items()
            if key
            not in {
                "description",
                "family",
                "feature",
            }
        }
        output["model"]["rules"].append(
            {
                "feature": feature.to_dict(),
                "selection": selection,
                "weight": float(weight),
            }
        )
        output["model"]["factors"].append(
            {
                "id": f"F-K3-V7-{index:03d}",
                "family": record["family"],
                "feature": feature.to_dict(),
                "human_authored": False,
                "origin": "learned_from_multiseed_v6_residual",
                "parameter": {
                    "scale": "log_energy_contribution",
                    "log_weight": float(weight),
                    "sign": "preference" if weight > 0 else "avoidance",
                },
                "selection": selection,
            }
        )
    output["model"]["validation_nll"] = validation_nll
    output["model"]["v7_residual_learning"] = {
        "method": "persistent_chain_bach_minus_gibbs_adam",
        "base_weights_changed": False,
        "initial_chain_cache": str(args.chain_cache.resolve()),
        "train_pieces": len(piece_ids),
        "chains": len(chains),
        "epochs": args.epochs,
        "sweeps_per_epoch": args.sweeps_per_epoch,
        "final_sweeps": args.final_sweeps,
        "learning_rate": args.learning_rate,
        "anchor": args.anchor,
        "initial_moment_mae": initial_mae,
        "best_moment_mae": best_mae,
        "best_epoch": best_epoch,
        "source_validation_nll": float(base_model["validation_nll"]),
        "validation_nll": validation_nll,
        "history": history,
        "factors": [
            {
                "id": f"F-K3-V7-{index:03d}",
                "family": record["family"],
                "description": record["description"],
                "feature": feature.to_dict(),
                "weight": float(weight),
            }
            for index, (feature, record, weight) in enumerate(
                zip(new_features, chosen_records, best_weights, strict=True),
                start=1,
            )
        ],
        "test_loaded": False,
    }
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(output), encoding="utf-8")
    control._write_chain_cache(
        args.final_chain_cache,
        chain_ids=[chain.piece_id for chain in chains],
        states={chain.piece_id: chain.blocks for chain in chains},
        source_model=args.output,
        weights=combined_weights,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        seed=args.seed,
    )
    print(f"[v7-fit] wrote {args.output}", flush=True)
    print(f"[v7-fit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
