#!/usr/bin/env python3
"""Calibrate readable K3 rules with a Bach-minus-Gibbs moment gradient."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "results/v5_7_k3_contextual_model.json"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


@dataclass
class Chain:
    piece_id: str
    lattice: k3.RhythmicLattice
    blocks: np.ndarray
    fixed: np.ndarray


def _score_path(directory: Path, piece_id: str) -> Path:
    stem = piece_id.split("/", 1)[-1]
    matches = [
        path
        for suffix in (".mxl", ".xml")
        if (path := directory / f"{stem}{suffix}").exists()
    ]
    if len(matches) != 1:
        raise FileNotFoundError(f"{piece_id}: expected one materialized score")
    return matches[0]


def _stable_order(piece_id: str) -> str:
    return hashlib.sha256(piece_id.encode()).hexdigest()


def _piece_seed(piece_id: str, seed: int) -> int:
    digest = hashlib.sha256(f"{piece_id}:{seed}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _decision_dataset(
    chain: Chain,
    blocks: np.ndarray,
    candidate_min: int,
    candidate_max: int,
) -> k3.K3Dataset:
    dataset = k3._decision_dataset(
        blocks,
        chain.lattice.attacks,
        range(1, chain.lattice.size - 1),
        candidate_min,
        candidate_max,
        chain.lattice.tonic_pc,
        chain.lattice.mode,
        chain.lattice.metric_levels,
    )
    if dataset is None:
        raise ValueError(f"{chain.piece_id}: no internal attack decision")
    return dataset


def _feature_rates(
    chain: Chain,
    blocks: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    candidate_min: int,
    candidate_max: int,
) -> np.ndarray:
    dataset = _decision_dataset(chain, blocks, candidate_min, candidate_max)
    rows = np.arange(dataset.size)
    chosen = dataset.chosen_indices
    rates = np.zeros(len(features), dtype=np.float64)
    for index, feature in enumerate(features):
        applies = dataset.voice_indices == feature.target_voice
        if not applies.any():
            continue
        mask = k3.feature_mask(dataset, feature)
        rates[index] = mask[rows, chosen][applies].mean()
    return rates


def _paired_statistics(
    source_rates: np.ndarray,
    generated_rates: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
) -> list[dict[str, Any]]:
    differences = source_rates - generated_rates
    records = []
    for index, feature in enumerate(features):
        values = differences[:, index]
        mean = float(values.mean())
        standard_error = (
            0.0
            if values.size < 2
            else float(values.std(ddof=1) / math.sqrt(values.size))
        )
        z_score = mean / max(standard_error, 1e-6)
        records.append(
            {
                "feature": feature.to_dict(),
                "bach_rate": float(source_rates[:, index].mean()),
                "gibbs_rate": float(generated_rates[:, index].mean()),
                "gradient": mean,
                "standard_error": standard_error,
                "z_score": z_score,
                "selection_score": abs(z_score)
                * abs(mean)
                / max(feature.complexity, 1),
            }
        )
    return records


def _sample_chains(
    chains: list[Chain],
    base_features: tuple[k3.FeatureSpec, ...],
    base_weights: np.ndarray,
    calibration_features: tuple[k3.FeatureSpec, ...],
    calibration_weights: np.ndarray,
    *,
    candidate_min: int,
    candidate_max: int,
    register_logits: np.ndarray,
    tonal_logits: np.ndarray,
    sweeps: int,
    seed: int,
) -> None:
    features = (*base_features, *calibration_features)
    weights = np.concatenate((base_weights, calibration_weights))
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
            seed=_piece_seed(chain.piece_id, seed),
            tonal_logits=tonal_logits,
            tonic_pc=chain.lattice.tonic_pc,
            mode=chain.lattice.mode,
            metric_levels=chain.lattice.metric_levels,
        )


def _conditional_validation_nll(
    validation: k3.K3Dataset,
    register_logits: np.ndarray,
    tonal_logits: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    weights: np.ndarray,
) -> float:
    matrix = k3.feature_matrix(validation, features)
    base_scores = k3.contextual_base_scores(
        validation,
        register_logits,
        tonal_logits,
    )
    return k3.conditional_nll(
        validation,
        register_logits,
        matrix,
        weights,
        base_scores=base_scores,
    )


def _feature_description(feature: k3.FeatureSpec) -> str:
    status = {
        "rare_tonal_class": "classe rare",
        "rare_tonal_incoming_step": "classe rare approchée par pas",
        "rare_tonal_leap_arrival": "classe rare atteinte sans pas",
        "rare_tonal_immediate_step_resolution": (
            "classe rare immédiatement résolue par pas"
        ),
        "rare_tonal_short_no_step_resolution": (
            "classe rare courte sans résolution par pas"
        ),
        "rare_tonal_immediate_neighbor": "classe rare en broderie",
        "rare_tonal_immediate_passing": "classe rare en passage",
        "rare_tonal_weak_metric": "classe rare sur temps faible",
        "rare_tonal_strong_metric": "classe rare sur temps fort",
    }[feature.kind]
    mode = "mineur" if feature.second_value else "majeur"
    pitch_classes = [
        pitch_class
        for pitch_class in range(12)
        if int(feature.value) & (1 << pitch_class)
    ]
    return (
        f"{status}, {k3.VOICE_NAMES[feature.target_voice]}, {mode}, "
        f"classes {pitch_classes}"
    )


def _markdown(result: dict[str, Any]) -> str:
    model = result["model"]
    lines = [
        "# V5.9 — calibration générative par contraste de moments",
        "",
        "Le socle V5.7 est gelé. Un petit budget de statuts chromatiques reçoit",
        "des poids supplémentaires par le gradient :",
        "",
        "`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.",
        "",
        f"Calibration sur `{result['corpus']['calibration_train_pieces']}` chorals",
        "du train choisis par hash, sans consulter validation pour les poids.",
        "Le test scellé n'est pas chargé.",
        "",
        "## Règles génératives retenues",
        "",
        "| # | Règle lisible | Bach initial | Gibbs initial | Gradient initial | "
        "Poids final |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for index, rule in enumerate(model["calibration_rules"], start=1):
        feature = k3.feature_from_model_record(rule)
        selection = rule["selection"]
        lines.append(
            f"| {index} | {_feature_description(feature)} | "
            f"{100 * selection['bach_rate']:.3f} % | "
            f"{100 * selection['gibbs_rate']:.3f} % | "
            f"{100 * selection['gradient']:+.3f} pp | "
            f"{rule['weight']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## Critères après gel",
            "",
            f"- NLL conditionnelle V5.7 : `{model['base_validation_nll']:.6f}`.",
            f"- NLL conditionnelle V5.9 : `{model['validation_nll']:.6f}`.",
            (
                "- Distance moyenne absolue des moments sélectionnés : "
                f"`{model['initial_moment_mae']:.6f}` → "
                f"`{model['final_moment_mae']:.6f}` sur le sous-ensemble train."
            ),
            "",
            "La promotion générative dépend d'une campagne séparée sur validation",
            "avec exactement les mêmes pièces, graines et balayages que V5.7.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=16)
    parser.add_argument("--max-features", type=int, default=8)
    parser.add_argument("--rarity-threshold", type=float, default=0.02)
    parser.add_argument("--burn-in-sweeps", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--sweeps-per-epoch", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.12)
    parser.add_argument("--l1", type=float, default=0.002)
    parser.add_argument("--anchor", type=float, default=0.02)
    parser.add_argument("--max-abs-weight", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=5909)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_payload = json.loads(args.model.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=_stable_order)[: args.train_pieces]
    model = base_payload["model"]
    corpus = base_payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    base_features = tuple(k3.feature_from_model_record(rule) for rule in model["rules"])
    base_weights = np.asarray([rule["weight"] for rule in model["rules"]])
    full = k3.load_k3_dataset(args.cache)
    train = k3.subset_for_piece_ids(full, splits["train"])
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    train, train_removed = k3.filter_to_domain(
        train,
        candidate_min,
        candidate_max,
    )
    validation, validation_removed = k3.filter_to_domain(
        validation,
        candidate_min,
        candidate_max,
    )
    if train_removed or validation_removed:
        raise ValueError("Observed choices unexpectedly fall outside train domain")
    candidates = k3.rare_tonal_feature_catalogue(
        train,
        args.rarity_threshold,
        voices=(1, 2, 3),
    )
    chains = []
    for piece_id in train_ids:
        lattice = k3.extract_piece_lattice(
            _score_path(args.scores, piece_id),
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
            _piece_seed(piece_id, args.seed),
            tonal_logits,
            lattice.tonic_pc,
            lattice.mode,
        )
        chains.append(Chain(piece_id, lattice, initial, fixed))
    source_rates = np.stack(
        [
            _feature_rates(
                chain,
                chain.lattice.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )
    _sample_chains(
        chains,
        base_features,
        base_weights,
        (),
        np.asarray([], dtype=np.float64),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        register_logits=register_logits,
        tonal_logits=tonal_logits,
        sweeps=args.burn_in_sweeps,
        seed=args.seed + 1,
    )
    initial_generated_rates = np.stack(
        [
            _feature_rates(
                chain,
                chain.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )
    statistics = _paired_statistics(
        source_rates,
        initial_generated_rates,
        candidates,
    )
    admissible = [
        (record["selection_score"], index, record)
        for index, record in enumerate(statistics)
        if max(record["bach_rate"], record["gibbs_rate"]) >= 0.002
    ]
    admissible.sort(key=lambda item: (item[0], candidates[item[1]].key), reverse=True)
    selected_records = admissible[: args.max_features]
    selected_indices = [index for _, index, _ in selected_records]
    selected_features = tuple(candidates[index] for index in selected_indices)
    selection_metadata = [record for _, _, record in selected_records]
    empirical = source_rates[:, selected_indices].mean(axis=0)
    initial_generated = initial_generated_rates[:, selected_indices].mean(axis=0)
    weights = np.zeros(len(selected_features), dtype=np.float64)
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    history = []
    for epoch in range(1, args.epochs + 1):
        _sample_chains(
            chains,
            base_features,
            base_weights,
            selected_features,
            weights,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            register_logits=register_logits,
            tonal_logits=tonal_logits,
            sweeps=args.sweeps_per_epoch,
            seed=args.seed + 1 + epoch,
        )
        generated_rates = np.stack(
            [
                _feature_rates(
                    chain,
                    chain.blocks,
                    selected_features,
                    candidate_min,
                    candidate_max,
                )
                for chain in chains
            ]
        )
        generated = generated_rates.mean(axis=0)
        gradient = empirical - generated - args.anchor * weights
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient**2
        corrected_first = first / (1.0 - 0.9**epoch)
        corrected_second = second / (1.0 - 0.999**epoch)
        weights += (
            args.learning_rate * corrected_first / (np.sqrt(corrected_second) + 1e-8)
        )
        weights = np.sign(weights) * np.maximum(
            np.abs(weights) - args.learning_rate * args.l1,
            0.0,
        )
        weights = np.clip(weights, -args.max_abs_weight, args.max_abs_weight)
        history.append(
            {
                "epoch": epoch,
                "weights": weights.tolist(),
                "bach_moments": empirical.tolist(),
                "gibbs_moments": generated.tolist(),
                "gradient": gradient.tolist(),
                "moment_mae": float(np.abs(empirical - generated).mean()),
            }
        )
        print(
            f"[k3-generative] epoch {epoch}/{args.epochs}: "
            f"moment_mae={history[-1]['moment_mae']:.6f} "
            f"max|w|={np.abs(weights).max():.4f}",
            flush=True,
        )
    final_generated = np.asarray(history[-1]["gibbs_moments"])
    all_features = (*base_features, *selected_features)
    all_weights = np.concatenate((base_weights, weights))
    validation_nll = _conditional_validation_nll(
        validation,
        register_logits,
        tonal_logits,
        all_features,
        all_weights,
    )
    output = copy.deepcopy(base_payload)
    output["experiment"] = {
        "id": "V5_9-K3-GENERATIVE-MOMENT-CALIBRATION",
        "status": "EXPLORATORY_FROZEN_FOR_VALIDATION",
        "test_loaded": False,
        "source_model": str(args.model.resolve()),
        "conditional_base_frozen": True,
        "gradient": "E_Bach[f] - E_Gibbs[f]",
        "rarity_threshold": args.rarity_threshold,
    }
    output["corpus"]["calibration_train_pieces"] = len(train_ids)
    output["corpus"]["calibration_piece_ids"] = train_ids
    output["model"]["base_validation_nll"] = float(model["validation_nll"])
    output["model"]["validation_nll"] = validation_nll
    output["model"]["base_rule_count"] = len(base_features)
    output["model"]["calibration_rule_count"] = len(selected_features)
    output["model"]["initial_moment_mae"] = float(
        np.abs(empirical - initial_generated).mean()
    )
    output["model"]["final_moment_mae"] = float(
        np.abs(empirical - final_generated).mean()
    )
    output["model"]["calibration_rules"] = [
        {
            "feature": feature.to_dict(),
            "weight": float(weight),
            "selection": selection,
        }
        for feature, weight, selection in zip(
            selected_features,
            weights,
            selection_metadata,
            strict=True,
        )
    ]
    output["model"]["rules"].extend(output["model"]["calibration_rules"])
    output["model"]["generative_history"] = history
    output["model"]["generative_calibration"] = {
        "burn_in_sweeps": args.burn_in_sweeps,
        "epochs": args.epochs,
        "sweeps_per_epoch": args.sweeps_per_epoch,
        "learning_rate": args.learning_rate,
        "l1": args.l1,
        "anchor": args.anchor,
        "max_abs_weight": args.max_abs_weight,
        "seed": args.seed,
        "candidate_features": len(candidates),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_9_generative_model.json"
    report_path = args.output_dir / "V5_9_GENERATIVE_CALIBRATION.md"
    json_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(output), encoding="utf-8")
    print(f"[k3-generative] wrote {json_path}", flush=True)
    print(f"[k3-generative] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
