#!/usr/bin/env python3
"""Reinduce a compact K3 factor structure from exact Gibbs conditionals."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import fit_exact_joint_pseudolikelihood as exact
import k3
import numpy as np
import run_generative_moment_calibration as generative
import run_v6_factor_induction as v6
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_GRAMMAR = FACTOR_BASE / "grammar.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v9_exact_reinduced_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V9_EXACT_REINDUCTION_MODEL.md"
DEFAULT_STRUCTURE_CACHE = HERE / "work/k3-exact-catalogue-32x10.npz"
DEFAULT_FULL_CACHE = HERE / "work/k3-exact-v9-selected-full.npz"
DEFAULT_CONTEXT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


@dataclass(frozen=True)
class ExactResidual:
    gradient: float
    variance: float
    z_score: float
    approximate_nll_gain: float
    column_score: float
    observed_mean: float
    expected_mean: float
    testable_opportunities: int
    piece_support: int


@dataclass
class Parameters:
    register: np.ndarray
    tonal: np.ndarray
    factor_weights: np.ndarray

    def copy(self) -> Parameters:
        return Parameters(
            self.register.copy(),
            self.tonal.copy(),
            self.factor_weights.copy(),
        )


def _base_scores(
    voices: np.ndarray,
    modes: np.ndarray,
    tonics: np.ndarray,
    candidate_pitches: np.ndarray,
    register: np.ndarray,
    tonal: np.ndarray,
) -> np.ndarray:
    relative = (candidate_pitches[None, :] - tonics[:, None]) % 12
    return register[voices] + tonal[
        voices[:, None],
        modes[:, None],
        relative,
    ]


def _probabilities(
    voices: np.ndarray,
    modes: np.ndarray,
    tonics: np.ndarray,
    candidate_pitches: np.ndarray,
    factors: np.ndarray,
    parameters: Parameters,
) -> np.ndarray:
    scores = _base_scores(
        voices,
        modes,
        tonics,
        candidate_pitches,
        parameters.register,
        parameters.tonal,
    )
    if factors.shape[2]:
        scores += np.tensordot(
            factors,
            parameters.factor_weights,
            axes=([2], [0]),
        )
    scores -= scores.max(axis=1, keepdims=True)
    probabilities = np.exp(scores)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    return probabilities


def _nll(
    chosen: np.ndarray,
    voices: np.ndarray,
    modes: np.ndarray,
    tonics: np.ndarray,
    candidate_pitches: np.ndarray,
    factors: np.ndarray,
    parameters: Parameters,
) -> float:
    probabilities = _probabilities(
        voices,
        modes,
        tonics,
        candidate_pitches,
        factors,
        parameters,
    )
    selected = probabilities[np.arange(chosen.size), chosen]
    return float(-np.log(np.maximum(selected, 1e-12)).mean())


def _center_nuisance(parameters: Parameters) -> None:
    parameters.register -= parameters.register.mean(axis=1, keepdims=True)
    parameters.tonal -= parameters.tonal.mean(axis=2, keepdims=True)


def _fit(
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    candidate_pitches: np.ndarray,
    initial: Parameters,
    *,
    steps: int,
    learning_rate: float,
    l1: float,
    l2: float,
) -> tuple[Parameters, dict[str, Any]]:
    parameters = initial.copy()
    _center_nuisance(parameters)
    moments = {
        "register": np.zeros_like(parameters.register),
        "tonal": np.zeros_like(parameters.tonal),
        "factor_weights": np.zeros_like(parameters.factor_weights),
    }
    velocities = {key: np.zeros_like(value) for key, value in moments.items()}
    best = parameters.copy()
    best_validation = _nll(
        validation["chosen"],
        validation["voices"],
        validation["modes"],
        validation["tonics"],
        candidate_pitches,
        validation["factors"],
        parameters,
    )
    history = [
        {
            "step": 0,
            "train_nll": _nll(
                train["chosen"],
                train["voices"],
                train["modes"],
                train["tonics"],
                candidate_pitches,
                train["factors"],
                parameters,
            ),
            "validation_nll": best_validation,
        }
    ]
    rows = np.arange(train["chosen"].size)
    relative = (candidate_pitches[None, :] - train["tonics"][:, None]) % 12
    voice_grid = np.broadcast_to(train["voices"][:, None], relative.shape)
    mode_grid = np.broadcast_to(train["modes"][:, None], relative.shape)
    for step in range(1, steps + 1):
        residuals = _probabilities(
            train["voices"],
            train["modes"],
            train["tonics"],
            candidate_pitches,
            train["factors"],
            parameters,
        )
        residuals[rows, train["chosen"]] -= 1.0
        register_gradient = np.zeros_like(parameters.register)
        np.add.at(register_gradient, train["voices"], residuals)
        register_gradient /= train["chosen"].size
        register_gradient += l2 * parameters.register
        tonal_gradient = np.zeros_like(parameters.tonal)
        np.add.at(
            tonal_gradient,
            (voice_grid, mode_grid, relative),
            residuals,
        )
        tonal_gradient /= train["chosen"].size
        tonal_gradient += l2 * parameters.tonal
        if train["factors"].shape[2]:
            factor_gradient = (
                np.einsum(
                    "ncr,nc->r",
                    train["factors"],
                    residuals,
                    optimize=True,
                )
                / train["chosen"].size
            )
            factor_gradient += l2 * parameters.factor_weights
        else:
            factor_gradient = np.empty(0, dtype=np.float64)
        gradients = {
            "register": register_gradient,
            "tonal": tonal_gradient,
            "factor_weights": factor_gradient,
        }
        for name, gradient in gradients.items():
            moments[name] = 0.9 * moments[name] + 0.1 * gradient
            velocities[name] = 0.999 * velocities[name] + 0.001 * gradient**2
            corrected_moment = moments[name] / (1.0 - 0.9**step)
            corrected_velocity = velocities[name] / (1.0 - 0.999**step)
            value = getattr(parameters, name)
            value -= learning_rate * corrected_moment / (
                np.sqrt(corrected_velocity) + 1e-8
            )
        parameters.factor_weights = np.sign(parameters.factor_weights) * np.maximum(
            np.abs(parameters.factor_weights) - learning_rate * l1,
            0.0,
        )
        _center_nuisance(parameters)
        if step == 1 or step % 10 == 0 or step == steps:
            train_nll = _nll(
                train["chosen"],
                train["voices"],
                train["modes"],
                train["tonics"],
                candidate_pitches,
                train["factors"],
                parameters,
            )
            validation_nll = _nll(
                validation["chosen"],
                validation["voices"],
                validation["modes"],
                validation["tonics"],
                candidate_pitches,
                validation["factors"],
                parameters,
            )
            history.append(
                {
                    "step": step,
                    "train_nll": train_nll,
                    "validation_nll": validation_nll,
                }
            )
            if validation_nll < best_validation:
                best_validation = validation_nll
                best = parameters.copy()
    return best, {
        "best_validation_nll": best_validation,
        "history": history,
    }


def _residuals(
    chosen: np.ndarray,
    probabilities: np.ndarray,
    factors: np.ndarray,
    piece_ids: np.ndarray,
    complexities: np.ndarray,
    *,
    complexity_penalty: float,
) -> tuple[ExactResidual | None, ...]:
    rows = np.arange(chosen.size)
    result: list[ExactResidual | None] = [None] * factors.shape[2]
    for start in range(0, factors.shape[2], 32):
        end = min(start + 32, factors.shape[2])
        local = factors[:, :, start:end].astype(np.float64)
        chosen_values = local[rows, chosen, :]
        expected = np.einsum(
            "nc,ncf->nf",
            probabilities,
            local,
            optimize=True,
        )
        expected_squared = np.einsum(
            "nc,ncf->nf",
            probabilities,
            local**2,
            optimize=True,
        )
        residual_sums = (chosen_values - expected).sum(axis=0)
        variances = np.maximum(
            (expected_squared - expected**2).sum(axis=0),
            0.0,
        )
        testable = np.ptp(local, axis=1) > 0
        for local_index, index in enumerate(range(start, end)):
            if (
                variances[local_index] <= 1e-12
                or not testable[:, local_index].any()
            ):
                continue
            opportunities = testable[:, local_index]
            gradient = float(residual_sums[local_index] / chosen.size)
            hessian = float(variances[local_index] / chosen.size)
            gain = 0.5 * gradient * gradient / hessian
            description_cost = (
                complexity_penalty
                * float(complexities[index])
                * math.log(max(chosen.size, 2))
                / chosen.size
            )
            result[index] = ExactResidual(
                gradient=gradient,
                variance=float(variances[local_index]),
                z_score=float(
                    residual_sums[local_index]
                    / math.sqrt(variances[local_index])
                ),
                approximate_nll_gain=gain,
                column_score=gain - description_cost,
                observed_mean=float(
                    chosen_values[opportunities, local_index].mean()
                ),
                expected_mean=float(expected[opportunities, local_index].mean()),
                testable_opportunities=int(opportunities.sum()),
                piece_support=int(np.unique(piece_ids[opportunities]).size),
            )
    return tuple(result)


def _cache_payload(
    path: Path,
    *,
    metadata: dict[str, Any],
    train: tuple[np.ndarray, ...],
    validation: tuple[np.ndarray, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        metadata=json.dumps(metadata, sort_keys=True),
        train_factors=train[1],
        train_chosen=train[2],
        train_piece_ids=train[3],
        train_voices=train[4],
        train_modes=train[5],
        train_tonics=train[6],
        validation_factors=validation[1],
        validation_chosen=validation[2],
        validation_piece_ids=validation[3],
        validation_voices=validation[4],
        validation_modes=validation[5],
        validation_tonics=validation[6],
    )


def _load_or_build(
    path: Path,
    *,
    metadata: dict[str, Any],
    train_ids: list[str],
    validation_ids: list[str],
    scores: Path,
    features: tuple[k3.FeatureSpec, ...],
    register: np.ndarray,
    tonal: np.ndarray,
    candidate_min: int,
    candidate_max: int,
    workers: int,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    if path.exists():
        archive = np.load(path)
        if json.loads(str(archive["metadata"])) != metadata:
            raise ValueError(f"Exact reinduction cache contract changed: {path}")
        print(f"[exact-reinduction] loaded {path}", flush=True)
    else:
        train = exact._build_split(
            train_ids,
            scores=scores,
            features=features,
            register=register,
            tonal=tonal,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            workers=workers,
            label="structure-train",
        )
        validation = exact._build_split(
            validation_ids,
            scores=scores,
            features=features,
            register=register,
            tonal=tonal,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            workers=workers,
            label="structure-validation",
        )
        _cache_payload(
            path,
            metadata=metadata,
            train=train,
            validation=validation,
        )
        print(f"[exact-reinduction] wrote {path}", flush=True)
        archive = np.load(path)

    def split(name: str) -> dict[str, np.ndarray]:
        return {
            "factors": archive[f"{name}_factors"],
            "chosen": archive[f"{name}_chosen"],
            "piece_ids": archive[f"{name}_piece_ids"],
            "voices": archive[f"{name}_voices"],
            "modes": archive[f"{name}_modes"],
            "tonics": archive[f"{name}_tonics"],
        }

    return split("train"), split("validation")


def _select_columns(
    data: dict[str, np.ndarray],
    indices: list[int],
) -> dict[str, np.ndarray]:
    return {
        **data,
        "factors": data["factors"][:, :, indices],
    }


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    model = result["model"]
    lines = [
        "# V9 — réinduction exacte depuis zéro",
        "",
        "La structure est sélectionnée par les gradients résiduels des véritables",
        "conditionnelles Gibbs. Registre, profil tonal et poids factoriels sont",
        "réappris conjointement. Aucun facteur V6/V8 n'est imposé.",
        "",
        "## Résultat",
        "",
        f"- Catalogue exact : `{experiment['catalogue_size']}` facteurs.",
        f"- Facteurs sélectionnés : `{len(model['rules'])}`.",
        f"- NLL validation structure : `{model['structure_validation_nll']:.6f}`.",
        f"- NLL validation complète : `{model['validation_nll']:.6f}`.",
        f"- Test réservé chargé : `{experiment['test_loaded']}`.",
        "",
        "| # | Famille | Facteur | Poids | z de sélection |",
        "|---:|---|---|---:|---:|",
    ]
    for index, rule in enumerate(model["rules"], start=1):
        lines.append(
            f"| {index} | `{rule['family']}` | "
            f"`{rule['feature']['label']}` | {rule['weight']:+.6f} | "
            f"{rule['selection']['z_score']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "La calibration nulle familiale doit encore être répétée avec les",
            "mondes exacts avant toute prétention de règle scientifique finale.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--context-cache", type=Path, default=DEFAULT_CONTEXT_CACHE)
    parser.add_argument(
        "--structure-cache",
        type=Path,
        default=DEFAULT_STRUCTURE_CACHE,
    )
    parser.add_argument("--full-cache", type=Path, default=DEFAULT_FULL_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--structure-train-pieces", type=int, default=32)
    parser.add_argument("--structure-validation-pieces", type=int, default=10)
    parser.add_argument("--maximum-factors", type=int, default=30)
    parser.add_argument("--refit-steps", type=int, default=60)
    parser.add_argument("--full-refit-steps", type=int, default=120)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument("--l1", type=float, default=0.0005)
    parser.add_argument("--l2", type=float, default=0.001)
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grammar = yaml.safe_load(args.grammar.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)
    validation_ids = list(splits["validation"])
    structure_train_ids = train_ids[: args.structure_train_pieces]
    structure_validation_ids = validation_ids[
        : args.structure_validation_pieces
    ]
    context = k3.load_k3_dataset(args.context_cache)
    context_train = k3.subset_for_piece_ids(context, train_ids).with_domain(
        int(source["corpus"]["candidate_min"]),
        int(source["corpus"]["candidate_max"]),
    )
    catalogue = v6._catalogue(context_train, grammar)
    family_by_kind = v6._feature_family_map(grammar)
    candidate_min = int(source["corpus"]["candidate_min"])
    candidate_max = int(source["corpus"]["candidate_max"])
    candidates = np.arange(candidate_min, candidate_max + 1, dtype=np.int16)
    initial_register = np.asarray(
        source["model"]["register_logits"],
        dtype=np.float64,
    )
    initial_tonal = np.asarray(
        source["model"]["tonal_logits"],
        dtype=np.float64,
    )
    structure_metadata = {
        "schema_version": 1,
        "scope": "exact_gibbs_attack_hold_worlds",
        "train_ids": structure_train_ids,
        "validation_ids": structure_validation_ids,
        "feature_keys": [feature.key for feature in catalogue],
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
    }
    train, validation = _load_or_build(
        args.structure_cache,
        metadata=structure_metadata,
        train_ids=structure_train_ids,
        validation_ids=structure_validation_ids,
        scores=args.scores,
        features=catalogue,
        register=initial_register,
        tonal=initial_tonal,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    empty_train = _select_columns(train, [])
    empty_validation = _select_columns(validation, [])
    parameters, baseline_fit = _fit(
        empty_train,
        empty_validation,
        candidates,
        Parameters(
            initial_register,
            initial_tonal,
            np.empty(0, dtype=np.float64),
        ),
        steps=args.refit_steps,
        learning_rate=args.learning_rate,
        l1=args.l1,
        l2=args.l2,
    )
    baseline_validation = baseline_fit["best_validation_nll"]
    selected: list[int] = []
    selections: list[ExactResidual] = []
    history = []
    best = (
        selected.copy(),
        selections.copy(),
        parameters.copy(),
        baseline_validation,
    )
    non_improvements = 0
    complexities = np.asarray(
        [feature.complexity for feature in catalogue],
        dtype=np.float64,
    )
    for iteration in range(1, args.maximum_factors + 1):
        selected_train = _select_columns(train, selected)
        probabilities = _probabilities(
            selected_train["voices"],
            selected_train["modes"],
            selected_train["tonics"],
            candidates,
            selected_train["factors"],
            parameters,
        )
        residuals = _residuals(
            train["chosen"],
            probabilities,
            train["factors"],
            train["piece_ids"],
            complexities,
            complexity_penalty=1.0,
        )
        ranked = [
            (residual.column_score, index, residual)
            for index, residual in enumerate(residuals)
            if index not in selected
            and residual is not None
            and residual.column_score > 0
            and residual.testable_opportunities >= 100
            and residual.piece_support >= 10
        ]
        if not ranked:
            print("[exact-reinduction] no admissible residual", flush=True)
            break
        _, chosen_index, statistic = max(
            ranked,
            key=lambda item: (item[0], catalogue[item[1]].key),
        )
        selected.append(chosen_index)
        selections.append(statistic)
        parameters.factor_weights = np.append(parameters.factor_weights, 0.0)
        selected_train = _select_columns(train, selected)
        selected_validation = _select_columns(validation, selected)
        parameters, fit = _fit(
            selected_train,
            selected_validation,
            candidates,
            parameters,
            steps=args.refit_steps,
            learning_rate=args.learning_rate,
            l1=args.l1,
            l2=args.l2,
        )
        validation_nll = fit["best_validation_nll"]
        history.append(
            {
                "iteration": iteration,
                "feature": catalogue[chosen_index].to_dict(),
                "family": family_by_kind[catalogue[chosen_index].kind],
                "selection": asdict(statistic),
                "validation_nll": validation_nll,
                "fit": fit,
            }
        )
        print(
            f"[exact-reinduction] {iteration}: "
            f"{catalogue[chosen_index].label} "
            f"z={statistic.z_score:+.2f} validation={validation_nll:.6f}",
            flush=True,
        )
        if validation_nll < best[3] - 1e-6:
            best = (
                selected.copy(),
                selections.copy(),
                parameters.copy(),
                validation_nll,
            )
            non_improvements = 0
        else:
            non_improvements += 1
            if non_improvements >= 3:
                print("[exact-reinduction] validation patience reached", flush=True)
                break
    selected, selections, structure_parameters, structure_validation = best
    selected_features = tuple(catalogue[index] for index in selected)

    full_metadata = {
        "schema_version": 1,
        "scope": "exact_gibbs_attack_hold_worlds",
        "train_ids": train_ids,
        "validation_ids": validation_ids,
        "feature_keys": [feature.key for feature in selected_features],
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
    }
    full_train, full_validation = _load_or_build(
        args.full_cache,
        metadata=full_metadata,
        train_ids=train_ids,
        validation_ids=validation_ids,
        scores=args.scores,
        features=selected_features,
        register=initial_register,
        tonal=initial_tonal,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    final_parameters, final_fit = _fit(
        full_train,
        full_validation,
        candidates,
        structure_parameters,
        steps=args.full_refit_steps,
        learning_rate=args.learning_rate,
        l1=args.l1,
        l2=args.l2,
    )
    train_nll = _nll(
        full_train["chosen"],
        full_train["voices"],
        full_train["modes"],
        full_train["tonics"],
        candidates,
        full_train["factors"],
        final_parameters,
    )
    validation_nll = _nll(
        full_validation["chosen"],
        full_validation["voices"],
        full_validation["modes"],
        full_validation["tonics"],
        candidates,
        full_validation["factors"],
        final_parameters,
    )
    result = {
        "experiment": {
            "id": "F-K3-V9-EXACT-REINDUCTION",
            "status": "EXACT_STRUCTURE_CANDIDATE",
            "test_loaded": False,
            "historical_rules_loaded": False,
            "expert_constraints_loaded": False,
            "scope_matches_gibbs": True,
            "nuisance_parameters_jointly_learned": True,
            "catalogue_size": len(catalogue),
            "structure_train_pieces": len(structure_train_ids),
            "structure_validation_pieces": len(structure_validation_ids),
            "full_train_pieces": len(train_ids),
            "full_validation_pieces": len(validation_ids),
            "null_family_calibration": "PENDING_EXACT_REPLICATION",
            "grammar": str(args.grammar.resolve()),
        },
        "corpus": {
            **source["corpus"],
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "train_decisions": int(full_train["chosen"].size),
            "validation_decisions": int(full_validation["chosen"].size),
        },
        "model": {
            "register_logits": final_parameters.register.tolist(),
            "tonal_logits": final_parameters.tonal.tolist(),
            "baseline_structure_validation_nll": baseline_validation,
            "structure_validation_nll": structure_validation,
            "train_nll": train_nll,
            "validation_nll": validation_nll,
            "rules": [
                {
                    "feature": feature.to_dict(),
                    "weight": float(weight),
                    "family": family_by_kind[feature.kind],
                    "selection": asdict(selection),
                }
                for feature, weight, selection in zip(
                    selected_features,
                    final_parameters.factor_weights,
                    selections,
                    strict=True,
                )
            ],
            "structure_history": history,
            "full_fit": final_fit,
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[exact-reinduction] validation={validation_nll:.6f}", flush=True)
    print(f"[exact-reinduction] wrote {args.output}", flush=True)
    print(f"[exact-reinduction] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
