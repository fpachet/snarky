#!/usr/bin/env python3
"""Estimate whether frozen V6 factors can control explicit generation defects."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import k3
import numpy as np
import refit_v6_generative_weights as refit
import run_explicit_generation_audit as audit
import run_generative_moment_calibration as generative
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v6_train64_generative_refit_model.json"
DEFAULT_OUTPUT = FACTOR_BASE / "v6_train64_controllability.json"
DEFAULT_REPORT = FACTOR_BASE / "V6_TRAIN64_CONTROLLABILITY.md"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_DIAGNOSTICS = (
    "bass_repeat_rate",
    "strong_pair_dissonances_per_block",
)
DIAGNOSTIC_METADATA = {
    "bass_semitone_rate": ("Demi-tons à la basse", 100.0, " pp"),
    "bass_repeat_rate": ("Répétitions de basse", 100.0, " pp"),
    "bass_large_leap_rate": ("Sauts de basse > 4 demi-tons", 100.0, " pp"),
    "bass_outside_natural_scale_rate": (
        "Basse hors gamme naturelle globale",
        100.0,
        " pp",
    ),
    "triadic_block_rate": ("Blocs triadiques", 100.0, " pp"),
    "strong_nontriadic_rate": ("Blocs forts non triadiques", 100.0, " pp"),
    "weak_pair_dissonances_per_block": (
        "Dissonances par bloc faible",
        1.0,
        "",
    ),
    "strong_pair_dissonances_per_block": (
        "Dissonances par bloc fort",
        1.0,
        "",
    ),
    "dominant_65_strong_rate": ("{0,3,6,8} sur bloc fort", 100.0, " pp"),
    "dominant_65_weak_rate": ("{0,3,6,8} sur bloc faible", 100.0, " pp"),
}


@dataclass(frozen=True)
class TrajectoryTask:
    actual_piece_id: str
    chain: generative.Chain
    features: tuple[k3.FeatureSpec, ...]
    monitored_features: tuple[k3.FeatureSpec, ...]
    weights: np.ndarray
    candidate_min: int
    candidate_max: int
    register_logits: np.ndarray
    tonal_logits: np.ndarray
    diagnostic_keys: tuple[str, ...]
    burn_in_sweeps: int
    samples: int
    adaptive_sampling: bool
    max_samples: int
    convergence_window: int
    ess_target: float
    stability_tolerance: float
    sweeps_between: int
    update_schedule: str
    seed: int


@dataclass(frozen=True)
class TrajectoryResult:
    actual_piece_id: str
    chain_id: str
    diagnostics: np.ndarray
    factor_counts: np.ndarray
    final_blocks: np.ndarray
    effective_sample_size_q05: float
    standardized_drift_q95: float
    converged: bool


def _lag1_effective_sample_sizes(values: np.ndarray) -> np.ndarray:
    """Conservative, cheap ESS approximation for many monitored moments."""

    observations = np.asarray(values, dtype=np.float64)
    if observations.ndim != 2 or observations.shape[0] < 2:
        raise ValueError("ESS requires a matrix with at least two observations")
    centered = observations - observations.mean(axis=0, keepdims=True)
    variance = np.sum(centered * centered, axis=0)
    covariance = np.sum(centered[:-1] * centered[1:], axis=0)
    rho = np.divide(
        covariance,
        variance,
        out=np.zeros_like(covariance),
        where=variance > 1e-12,
    )
    rho = np.clip(rho, -0.99, 0.99)
    size = observations.shape[0]
    ess = size * (1.0 - rho) / (1.0 + rho)
    return np.clip(ess, 1.0, float(size))


def _convergence_moments(
    diagnostics: np.ndarray,
    factor_counts: np.ndarray,
) -> np.ndarray:
    """Moments needed by means and Cov(diagnostic, factor activation)."""

    products = np.einsum("si,sj->sij", diagnostics, factor_counts)
    return np.concatenate(
        (
            diagnostics,
            factor_counts,
            products.reshape((diagnostics.shape[0], -1)),
        ),
        axis=1,
    )


def _convergence_summary(
    diagnostics: np.ndarray,
    factor_counts: np.ndarray,
    *,
    window: int,
) -> tuple[float, float]:
    """Return robust ESS and recent standardized drift summaries."""

    moments = _convergence_moments(diagnostics, factor_counts)
    if moments.shape[0] < 2 * window:
        return 0.0, float("inf")
    ess_q05 = float(np.quantile(_lag1_effective_sample_sizes(moments), 0.05))
    previous = moments[-2 * window : -window]
    recent = moments[-window:]
    scale = np.std(moments, axis=0, ddof=1)
    drift = np.abs(recent.mean(axis=0) - previous.mean(axis=0))
    standardized = np.divide(
        drift,
        np.maximum(scale, 1e-6),
    )
    return ess_q05, float(np.quantile(standardized, 0.95))


def _factor_counts(
    chain: generative.Chain,
    blocks: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    candidate_min: int,
    candidate_max: int,
) -> np.ndarray:
    dataset = generative._decision_dataset(
        chain,
        blocks,
        candidate_min,
        candidate_max,
    )
    counts = np.zeros(len(features), dtype=np.float64)
    for index, feature in enumerate(features):
        applies = refit._grounding_rows(dataset, feature)
        if applies.any():
            active = k3.chosen_feature_values(dataset, feature)
            counts[index] = float(active[applies].sum())
    return counts


def _diagnostics(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
    keys: tuple[str, ...],
) -> np.ndarray:
    values = audit._metrics(blocks, lattice)
    return np.asarray([values[key] for key in keys], dtype=np.float64)


def _sample_trajectory(task: TrajectoryTask) -> TrajectoryResult:
    """Run one complete chain trajectory without inter-process round trips."""

    chain = task.chain
    if task.burn_in_sweeps:
        chain.blocks = refit._sample_one(
            (
                chain,
                task.features,
                task.weights,
                task.candidate_min,
                task.candidate_max,
                task.register_logits,
                task.tonal_logits,
                task.burn_in_sweeps,
                task.seed + 1,
                task.update_schedule,
            )
        )
    diagnostics = []
    factor_counts = []
    ess_q05 = 0.0
    drift_q95 = float("inf")
    converged = False
    retained_limit = task.max_samples if task.adaptive_sampling else task.samples
    for sample in range(retained_limit):
        chain.blocks = refit._sample_one(
            (
                chain,
                task.features,
                task.weights,
                task.candidate_min,
                task.candidate_max,
                task.register_logits,
                task.tonal_logits,
                task.sweeps_between,
                task.seed + 2 + sample,
                task.update_schedule,
            )
        )
        diagnostics.append(
            _diagnostics(
                chain.blocks,
                chain.lattice,
                task.diagnostic_keys,
            )
        )
        factor_counts.append(
            _factor_counts(
                chain,
                chain.blocks,
                task.monitored_features,
                task.candidate_min,
                task.candidate_max,
            )
        )
        retained = sample + 1
        if task.adaptive_sampling and retained >= task.samples:
            ess_q05, drift_q95 = _convergence_summary(
                np.stack(diagnostics),
                np.stack(factor_counts),
                window=task.convergence_window,
            )
            converged = bool(
                ess_q05 >= task.ess_target
                and drift_q95 <= task.stability_tolerance
            )
            if converged:
                break
    if not task.adaptive_sampling:
        ess_q05, drift_q95 = _convergence_summary(
            np.stack(diagnostics),
            np.stack(factor_counts),
            window=min(task.convergence_window, task.samples // 2),
        )
    return TrajectoryResult(
        actual_piece_id=task.actual_piece_id,
        chain_id=chain.piece_id,
        diagnostics=np.stack(diagnostics),
        factor_counts=np.stack(factor_counts),
        final_blocks=chain.blocks,
        effective_sample_size_q05=ess_q05,
        standardized_drift_q95=drift_q95,
        converged=converged,
    )


def _load_chain_cache(path: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    with np.load(path, allow_pickle=False) as payload:
        metadata = json.loads(str(payload["metadata"].item()))
        chain_ids = [str(value) for value in payload["chain_ids"]]
        states = {
            chain_id: np.asarray(payload[f"blocks_{index:05d}"], dtype=np.int16)
            for index, chain_id in enumerate(chain_ids)
        }
    if metadata.get("schema_version") != 1:
        raise ValueError(f"{path}: unsupported chain-cache schema")
    return states, metadata


def _write_chain_cache(
    path: Path,
    *,
    chain_ids: list[str],
    states: dict[str, np.ndarray],
    source_model: Path,
    weights: np.ndarray,
    candidate_min: int,
    candidate_max: int,
    seed: int,
) -> None:
    if set(chain_ids) != set(states):
        raise ValueError("Final chain states do not match the requested cache")
    metadata = {
        "schema_version": 1,
        "source_model": str(source_model.resolve()),
        "weights_sha256": hashlib.sha256(weights.tobytes()).hexdigest(),
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
        "seed": seed,
        "chains": len(chain_ids),
    }
    arrays = {
        f"blocks_{index:05d}": np.asarray(states[chain_id], dtype=np.int16)
        for index, chain_id in enumerate(chain_ids)
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
        chain_ids=np.asarray(chain_ids),
        **arrays,
    )


def _piece_covariance(
    diagnostics: np.ndarray,
    factor_counts: np.ndarray,
) -> np.ndarray:
    if diagnostics.shape[0] < 2:
        raise ValueError("At least two samples are required per piece")
    centered_diagnostics = diagnostics - diagnostics.mean(axis=0, keepdims=True)
    centered_counts = factor_counts - factor_counts.mean(axis=0, keepdims=True)
    return centered_diagnostics.T @ centered_counts / (diagnostics.shape[0] - 1)


def _minimum_norm_delta(
    jacobian: np.ndarray,
    residual: np.ndarray,
    ridge: float,
    diagnostic_scales: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    scaled_jacobian = jacobian / diagnostic_scales[:, None]
    scaled_residual = residual / diagnostic_scales
    gram = scaled_jacobian @ scaled_jacobian.T
    scale = max(float(np.trace(gram) / gram.shape[0]), 1e-12)
    delta = scaled_jacobian.T @ np.linalg.solve(
        gram + ridge * scale * np.eye(gram.shape[0]),
        scaled_residual,
    )
    return delta, jacobian @ delta


def _bootstrap_intervals(
    per_piece_jacobian: np.ndarray,
    source: np.ndarray,
    generated: np.ndarray,
    *,
    samples: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    generator = np.random.default_rng(seed)
    jacobians = np.empty(
        (samples, *per_piece_jacobian.shape[1:]),
        dtype=np.float64,
    )
    residuals = np.empty((samples, source.shape[1]), dtype=np.float64)
    for sample in range(samples):
        indices = generator.integers(0, source.shape[0], source.shape[0])
        jacobians[sample] = per_piece_jacobian[indices].mean(axis=0)
        residuals[sample] = (source[indices] - generated[indices]).mean(axis=0)
    jacobian_interval = np.quantile(jacobians, (0.025, 0.975), axis=0)
    residual_interval = np.quantile(residuals, (0.025, 0.975), axis=0)
    return jacobian_interval, residual_interval


def _markdown(result: dict[str, Any]) -> str:
    diagnostics = result["diagnostics"]
    diagnostic_keys = result["experiment"]["diagnostics"]
    lines = [
        "# V6 — contrôlabilité des résidus par les 30 facteurs gelés",
        "",
        "Cette analyse utilise uniquement des chorals du train. Pour une métrique",
        "`g` et un facteur `f`, la sensibilité locale est estimée par :",
        "",
        "```text",
        "∂ E[g] / ∂ poids(f) = Cov(g, nombre_d_activations(f))",
        "```",
        "",
        "Aucun facteur ni poids n'est modifié par cette expérience. Le test",
        "réservé n'est pas chargé.",
        "",
        "## Échantillonnage",
        "",
        f"- Pièces : `{result['experiment']['train_pieces']}`.",
        f"- Chaînes par pièce : `{result['experiment']['chains_per_piece']}`.",
        (
            "- États conservés par chaîne (min/moy/max) : "
            f"`{result['experiment']['retained_samples_min']}/"
            f"{result['experiment']['retained_samples_mean']:.1f}/"
            f"{result['experiment']['retained_samples_max']}`."
        ),
        (
            "- Arrêt adaptatif : "
            f"`{str(result['experiment']['adaptive_sampling']).lower()}` ; "
            f"chaînes convergées : "
            f"`{result['experiment']['converged_chains']}/"
            f"{result['experiment']['chains']}`."
        ),
        f"- Mode d'exécution : `{result['experiment']['execution_mode']}`.",
        (
            f"- Chaînes restaurées : "
            f"`{result['experiment']['warm_started_chains']}/"
            f"{result['experiment']['chains']}`."
        ),
        (
            f"- Cache issu des mêmes poids : "
            f"`{result['experiment']['initial_cache_weights_match']}`."
        ),
        (
            f"- Temps d'échantillonnage : "
            f"`{result['experiment']['sampling_seconds']:.3f}` secondes."
        ),
        (
            f"- Rang de la matrice de sensibilité : "
            f"`{result['control']['rank']}/{len(diagnostic_keys)}`."
        ),
        (
            f"- Métriques standardisées : "
            f"`{str(result['control']['standardized']).lower()}`."
        ),
        "",
        "## Résidus train",
        "",
        "| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in diagnostic_keys:
        label, scale, suffix = DIAGNOSTIC_METADATA[key]
        row = diagnostics[key]
        lines.append(
            f"| {label} | {scale * row['bach']:.3f} | "
            f"{scale * row['gibbs']:.3f} | "
            f"{scale * row['residual']:+.3f}{suffix} | "
            f"`{scale * row['residual_ci95_low']:+.3f}` à "
            f"`{scale * row['residual_ci95_high']:+.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Correction linéaire minimale",
            "",
            (
                f"- Erreur relative projetée : "
                f"`{result['control']['relative_projection_error']:.6f}`."
            ),
            (
                f"- Plus grand déplacement proposé : "
                f"`{result['control']['max_abs_delta']:.6f}`."
            ),
            (
                f"- Structure localement contrôlable : "
                f"`{str(result['control']['controllable']).lower()}`."
            ),
            "",
            "Cette projection est un diagnostic local, pas encore un nouveau",
            "jeu de poids. Elle doit être confirmée par génération.",
            "",
            "## Facteurs les plus sensibles",
            "",
        ]
    )
    for key in diagnostic_keys:
        label, _, _ = DIAGNOSTIC_METADATA[key]
        lines.extend(
            [
                f"### {label}",
                "",
                "| Facteur | Prédicat | Sensibilité | IC95 |",
                "|---|---|---:|---:|",
            ]
        )
        for record in result["top_sensitivities"][key]:
            lines.append(
                f"| `{record['factor_id']}` | `{record['feature_label']}` | "
                f"{record['sensitivity']:+.6f} | "
                f"`{record['ci95_low']:+.6f}` à "
                f"`{record['ci95_high']:+.6f}` |"
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=64)
    parser.add_argument("--chains-per-piece", type=int, default=2)
    parser.add_argument("--burn-in-sweeps", type=int, default=6)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument(
        "--adaptive-sampling",
        action="store_true",
        help=(
            "Treat --samples as a minimum and stop each trajectory once the "
            "diagnostic/factor moments are stable, up to --max-samples."
        ),
    )
    parser.add_argument("--max-samples", type=int, default=24)
    parser.add_argument("--convergence-window", type=int, default=3)
    parser.add_argument("--ess-target", type=float, default=4.0)
    parser.add_argument("--stability-tolerance", type=float, default=1.5)
    parser.add_argument("--sweeps-between", type=int, default=2)
    parser.add_argument(
        "--update-schedule",
        choices=("sequential", "colored"),
        default="sequential",
        help=(
            "Sequential random scan, or exact simultaneous updates of spans "
            "whose K3 factor scopes are disjoint."
        ),
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--execution-mode",
        choices=("trajectory", "staged"),
        default="trajectory",
        help=(
            "Run each complete trajectory inside one worker, or use the former "
            "stage-by-stage process-pool dispatch as a parity oracle."
        ),
    )
    parser.add_argument(
        "--initial-chain-cache",
        type=Path,
        help="Optional NPZ states from a previous nearby weight checkpoint.",
    )
    parser.add_argument(
        "--final-chain-cache",
        type=Path,
        help="Optional NPZ destination for the final persistent chain states.",
    )
    parser.add_argument(
        "--warm-start-burn-in-sweeps",
        type=int,
        default=1,
        help="Burn-in used only for chains restored from an explicit cache.",
    )
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--ridge", type=float, default=1e-5)
    parser.add_argument(
        "--diagnostics",
        default=",".join(DEFAULT_DIAGNOSTICS),
        help="Comma-separated explicit metric keys, or 'all'",
    )
    parser.add_argument(
        "--monitor-shortlist",
        type=Path,
        help=(
            "Optional V16 shortlist whose zero-weight candidate activations "
            "are monitored without changing the sampled model."
        ),
    )
    parser.add_argument("--standardize", action="store_true")
    parser.add_argument("--max-controllable-delta", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=7613)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.train_pieces <= 0 or args.chains_per_piece <= 0:
        raise ValueError("Train pieces and chains per piece must be positive")
    if args.samples < 2:
        raise ValueError("At least two retained samples are required")
    if (
        args.max_samples < args.samples
        or args.convergence_window <= 0
        or args.ess_target <= 0
        or args.stability_tolerance < 0
        or (
            args.adaptive_sampling
            and args.samples < 2 * args.convergence_window
        )
    ):
        raise ValueError(
            "Adaptive sampling requires max >= samples >= 2 * window, "
            "ESS > 0 and tolerance >= 0"
        )
    if (
        args.burn_in_sweeps < 0
        or args.sweeps_between <= 0
        or args.warm_start_burn_in_sweeps < 0
    ):
        raise ValueError("Sweep counts must satisfy burn-in >= 0 and between > 0")
    if args.workers <= 0:
        raise ValueError("Workers must be positive")
    if args.adaptive_sampling and args.execution_mode != "trajectory":
        raise ValueError("Adaptive sampling requires trajectory execution mode")
    diagnostic_keys = (
        tuple(DIAGNOSTIC_METADATA)
        if args.diagnostics == "all"
        else tuple(key for key in args.diagnostics.split(",") if key)
    )
    if (
        not diagnostic_keys
        or len(set(diagnostic_keys)) != len(diagnostic_keys)
        or any(key not in DIAGNOSTIC_METADATA for key in diagnostic_keys)
    ):
        raise ValueError("Diagnostics must be unique known explicit metric keys")
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    model = payload["model"]
    calibration_ids = model.get("generative_weight_refit", {}).get("piece_ids", [])
    if len(calibration_ids) >= args.train_pieces:
        train_ids = list(calibration_ids[: args.train_pieces])
    else:
        train_ids = sorted(splits["train"], key=generative._stable_order)[
            : args.train_pieces
        ]
    corpus = payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    features = tuple(k3.feature_from_model_record(rule) for rule in model["rules"])
    weights = np.asarray(
        [float(rule["weight"]) for rule in model["rules"]],
        dtype=np.float64,
    )
    factor_records = model.get("factors")
    if factor_records is None:
        factor_records = [
            {
                "id": f"LEARNED-{index:03d}",
                "feature": rule["feature"],
            }
            for index, rule in enumerate(model["rules"], start=1)
        ]
    monitored_features = features
    monitored_candidate_count = 0
    if args.monitor_shortlist is not None:
        shortlist = json.loads(
            args.monitor_shortlist.read_text(encoding="utf-8")
        )
        candidates_to_monitor = shortlist["candidates"]
        candidate_features = tuple(
            k3.feature_from_model_record(candidate["feature"])
            for candidate in candidates_to_monitor
        )
        existing_keys = {feature.key for feature in features}
        duplicate_keys = [
            feature.key
            for feature in candidate_features
            if feature.key in existing_keys
        ]
        if duplicate_keys:
            raise ValueError(
                "Monitor shortlist contains factors already in the model: "
                + ", ".join(duplicate_keys)
            )
        if len({feature.key for feature in candidate_features}) != len(
            candidate_features
        ):
            raise ValueError("Monitor shortlist contains duplicate factors")
        monitored_features = (*features, *candidate_features)
        monitored_candidate_count = len(candidate_features)
        factor_records = [
            *factor_records,
            *[
                {
                    "id": f"V16-CANDIDATE-{candidate['rank']:03d}",
                    "feature": candidate["feature"],
                }
                for candidate in candidates_to_monitor
            ],
        ]

    cached_states: dict[str, np.ndarray] = {}
    cache_metadata: dict[str, Any] | None = None
    cache_weights_match: bool | None = None
    if args.initial_chain_cache is not None:
        cached_states, cache_metadata = _load_chain_cache(args.initial_chain_cache)
        if (
            int(cache_metadata["candidate_min"]) != candidate_min
            or int(cache_metadata["candidate_max"]) != candidate_max
        ):
            raise ValueError("Chain cache and model use different pitch domains")
        cache_weights_match = bool(
            cache_metadata["weights_sha256"]
            == hashlib.sha256(weights.tobytes()).hexdigest()
        )

    chains: list[generative.Chain] = []
    actual_piece_ids: list[str] = []
    warm_started_chain_ids: set[str] = set()
    source_by_piece: dict[str, np.ndarray] = {}
    for piece_id in train_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        source_by_piece[piece_id] = _diagnostics(
            lattice.blocks,
            lattice,
            diagnostic_keys,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        for replica in range(args.chains_per_piece):
            chain_id = f"{piece_id}#replica={replica}"
            cached = cached_states.get(chain_id)
            if cached is None:
                initial = rhythmic._randomize_mutable_segments(
                    lattice.blocks,
                    lattice.attacks,
                    fixed,
                    register_logits,
                    candidate_min,
                    generative._piece_seed(chain_id, args.seed),
                    tonal_logits,
                    lattice.tonic_pc,
                    lattice.mode,
                )
            else:
                if cached.shape != lattice.blocks.shape:
                    raise ValueError(
                        f"{chain_id}: cached shape {cached.shape} differs from "
                        f"lattice shape {lattice.blocks.shape}"
                    )
                if not np.array_equal(cached[fixed], lattice.blocks[fixed]):
                    raise ValueError(f"{chain_id}: cache changes fixed boundary notes")
                k3.validated_attack_segments(cached, lattice.attacks)
                initial = cached.copy()
                warm_started_chain_ids.add(chain_id)
            chains.append(generative.Chain(chain_id, lattice, initial, fixed))
            actual_piece_ids.append(piece_id)

    sampled_diagnostics: dict[str, list[np.ndarray]] = defaultdict(list)
    sampled_counts: dict[str, list[np.ndarray]] = defaultdict(list)
    final_states: dict[str, np.ndarray] = {}
    trajectory_results: list[TrajectoryResult] = []
    sampling_started = time.perf_counter()
    if args.execution_mode == "trajectory":
        tasks = [
            TrajectoryTask(
                actual_piece_id=piece_id,
                chain=chain,
                features=features,
                monitored_features=monitored_features,
                weights=weights,
                candidate_min=candidate_min,
                candidate_max=candidate_max,
                register_logits=register_logits,
                tonal_logits=tonal_logits,
                diagnostic_keys=diagnostic_keys,
                burn_in_sweeps=(
                    args.warm_start_burn_in_sweeps
                    if chain.piece_id in warm_started_chain_ids
                    else args.burn_in_sweeps
                ),
                samples=args.samples,
                adaptive_sampling=args.adaptive_sampling,
                max_samples=args.max_samples,
                convergence_window=args.convergence_window,
                ess_target=args.ess_target,
                stability_tolerance=args.stability_tolerance,
                sweeps_between=args.sweeps_between,
                update_schedule=args.update_schedule,
                seed=args.seed,
            )
            for piece_id, chain in zip(actual_piece_ids, chains, strict=True)
        ]
        executor = (
            None if args.workers == 1 else ProcessPoolExecutor(max_workers=args.workers)
        )
        try:
            trajectories = (
                map(_sample_trajectory, tasks)
                if executor is None
                else executor.map(_sample_trajectory, tasks)
            )
            for completed, trajectory in enumerate(trajectories, start=1):
                trajectory_results.append(trajectory)
                final_states[trajectory.chain_id] = trajectory.final_blocks
                print(
                    f"[v6-control] trajectory {completed}/{len(tasks)}",
                    flush=True,
                )
        finally:
            if executor is not None:
                executor.shutdown()
        if args.adaptive_sampling:
            for trajectory in trajectory_results:
                sampled_diagnostics[trajectory.actual_piece_id].extend(
                    trajectory.diagnostics
                )
                sampled_counts[trajectory.actual_piece_id].extend(
                    trajectory.factor_counts
                )
        else:
            for sample in range(args.samples):
                for trajectory in trajectory_results:
                    sampled_diagnostics[trajectory.actual_piece_id].append(
                        trajectory.diagnostics[sample]
                    )
                    sampled_counts[trajectory.actual_piece_id].append(
                        trajectory.factor_counts[sample]
                    )
    else:
        executor = (
            None if args.workers == 1 else ProcessPoolExecutor(max_workers=args.workers)
        )
        try:
            cold_chains = [
                chain
                for chain in chains
                if chain.piece_id not in warm_started_chain_ids
            ]
            warm_chains = [
                chain for chain in chains if chain.piece_id in warm_started_chain_ids
            ]
            if cold_chains and args.burn_in_sweeps:
                refit._sample(
                    cold_chains,
                    features,
                    weights,
                    candidate_min=candidate_min,
                    candidate_max=candidate_max,
                    register_logits=register_logits,
                    tonal_logits=tonal_logits,
                    sweeps=args.burn_in_sweeps,
                    seed=args.seed + 1,
                    update_schedule=args.update_schedule,
                    executor=executor,
                )
            if warm_chains and args.warm_start_burn_in_sweeps:
                refit._sample(
                    warm_chains,
                    features,
                    weights,
                    candidate_min=candidate_min,
                    candidate_max=candidate_max,
                    register_logits=register_logits,
                    tonal_logits=tonal_logits,
                    sweeps=args.warm_start_burn_in_sweeps,
                    seed=args.seed + 1,
                    update_schedule=args.update_schedule,
                    executor=executor,
                )
            for sample in range(args.samples):
                refit._sample(
                    chains,
                    features,
                    weights,
                    candidate_min=candidate_min,
                    candidate_max=candidate_max,
                    register_logits=register_logits,
                    tonal_logits=tonal_logits,
                    sweeps=args.sweeps_between,
                    seed=args.seed + 2 + sample,
                    update_schedule=args.update_schedule,
                    executor=executor,
                )
                for piece_id, chain in zip(actual_piece_ids, chains, strict=True):
                    sampled_diagnostics[piece_id].append(
                        _diagnostics(
                            chain.blocks,
                            chain.lattice,
                            diagnostic_keys,
                        )
                    )
                    sampled_counts[piece_id].append(
                        _factor_counts(
                            chain,
                            chain.blocks,
                            monitored_features,
                            candidate_min,
                            candidate_max,
                        )
                    )
                print(
                    f"[v6-control] sample {sample + 1}/{args.samples}",
                    flush=True,
                )
            final_states = {chain.piece_id: chain.blocks for chain in chains}
        finally:
            if executor is not None:
                executor.shutdown()
    sampling_seconds = time.perf_counter() - sampling_started
    retained_counts = (
        [int(result.diagnostics.shape[0]) for result in trajectory_results]
        if trajectory_results
        else [args.samples] * len(chains)
    )
    convergence_ess = (
        [result.effective_sample_size_q05 for result in trajectory_results]
        if trajectory_results
        else []
    )
    convergence_drift = (
        [result.standardized_drift_q95 for result in trajectory_results]
        if trajectory_results
        else []
    )
    chain_ids = [chain.piece_id for chain in chains]
    if args.final_chain_cache is not None:
        _write_chain_cache(
            args.final_chain_cache,
            chain_ids=chain_ids,
            states=final_states,
            source_model=args.model,
            weights=weights,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            seed=args.seed,
        )

    source = np.stack([source_by_piece[piece_id] for piece_id in train_ids])
    generated = np.stack(
        [np.stack(sampled_diagnostics[piece_id]).mean(axis=0) for piece_id in train_ids]
    )
    per_piece_jacobian = np.stack(
        [
            _piece_covariance(
                np.stack(sampled_diagnostics[piece_id]),
                np.stack(sampled_counts[piece_id]),
            )
            for piece_id in train_ids
        ]
    )
    jacobian = per_piece_jacobian.mean(axis=0)
    residual = (source - generated).mean(axis=0)
    diagnostic_scales = (
        np.maximum(source.std(axis=0, ddof=1), 1e-3)
        if args.standardize
        else np.ones(len(diagnostic_keys), dtype=np.float64)
    )
    delta, projected = _minimum_norm_delta(
        jacobian,
        residual,
        args.ridge,
        diagnostic_scales,
    )
    relative_error = float(
        np.linalg.norm((projected - residual) / diagnostic_scales)
        / max(np.linalg.norm(residual / diagnostic_scales), 1e-12)
    )
    jacobian_interval, residual_interval = _bootstrap_intervals(
        per_piece_jacobian,
        source,
        generated,
        samples=args.bootstrap_samples,
        seed=args.seed + 10_000,
    )
    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    rank = int(np.linalg.matrix_rank(jacobian))
    robust_counts = [
        int(
            np.count_nonzero(
                (jacobian_interval[0, diagnostic] > 0)
                | (jacobian_interval[1, diagnostic] < 0)
            )
        )
        for diagnostic in range(len(diagnostic_keys))
    ]
    max_abs_delta = float(np.max(np.abs(delta)))
    controllable = bool(
        rank == len(diagnostic_keys)
        and relative_error <= 0.1
        and max_abs_delta <= args.max_controllable_delta
        and all(count > 0 for count in robust_counts)
    )
    top_sensitivities = {}
    for diagnostic, key in enumerate(diagnostic_keys):
        indices = np.argsort(np.abs(jacobian[diagnostic]))[::-1][:8]
        top_sensitivities[key] = [
            {
                "factor_id": factor_records[index]["id"],
                "feature_key": factor_records[index]["feature"]["key"],
                "feature_label": factor_records[index]["feature"]["label"],
                "sensitivity": float(jacobian[diagnostic, index]),
                "ci95_low": float(jacobian_interval[0, diagnostic, index]),
                "ci95_high": float(jacobian_interval[1, diagnostic, index]),
                "proposed_weight_delta": float(delta[index]),
            }
            for index in indices
        ]
    result = {
        "experiment": {
            "id": "F-K3-V6-TRAIN64-CONTROLLABILITY",
            "status": "TRAIN_ONLY_DIAGNOSTIC",
            "source_model": str(args.model.resolve()),
            "train_pieces": len(train_ids),
            "piece_ids": train_ids,
            "chains_per_piece": args.chains_per_piece,
            "samples": args.samples,
            "adaptive_sampling": args.adaptive_sampling,
            "max_samples": args.max_samples,
            "retained_samples_min": min(retained_counts),
            "retained_samples_mean": float(np.mean(retained_counts)),
            "retained_samples_max": max(retained_counts),
            "convergence_window": args.convergence_window,
            "ess_target": args.ess_target,
            "stability_tolerance": args.stability_tolerance,
            "converged_chains": sum(
                result.converged for result in trajectory_results
            ),
            "effective_sample_size_q05_min": (
                None if not convergence_ess else min(convergence_ess)
            ),
            "standardized_drift_q95_max": (
                None if not convergence_drift else max(convergence_drift)
            ),
            "trajectory_convergence": [
                {
                    "chain_id": trajectory.chain_id,
                    "retained_samples": int(trajectory.diagnostics.shape[0]),
                    "effective_sample_size_q05": (
                        trajectory.effective_sample_size_q05
                    ),
                    "standardized_drift_q95": (
                        trajectory.standardized_drift_q95
                    ),
                    "converged": trajectory.converged,
                }
                for trajectory in trajectory_results
            ],
            "burn_in_sweeps": args.burn_in_sweeps,
            "sweeps_between": args.sweeps_between,
            "update_schedule": args.update_schedule,
            "workers": args.workers,
            "execution_mode": args.execution_mode,
            "chains": len(chains),
            "warm_started_chains": len(warm_started_chain_ids),
            "warm_start_burn_in_sweeps": args.warm_start_burn_in_sweeps,
            "sampling_seconds": sampling_seconds,
            "seed": args.seed,
            "initial_chain_cache": (
                None
                if args.initial_chain_cache is None
                else str(args.initial_chain_cache.resolve())
            ),
            "initial_chain_cache_metadata": cache_metadata,
            "initial_cache_weights_match": cache_weights_match,
            "final_chain_cache": (
                None
                if args.final_chain_cache is None
                else str(args.final_chain_cache.resolve())
            ),
            "diagnostics": list(diagnostic_keys),
            "monitor_shortlist": (
                None
                if args.monitor_shortlist is None
                else str(args.monitor_shortlist.resolve())
            ),
            "monitored_existing_factor_count": len(features),
            "monitored_candidate_count": monitored_candidate_count,
            "test_loaded": False,
            "factor_structure_changed": False,
            "weights_changed": False,
        },
        "diagnostics": {
            key: {
                "bach": float(source[:, index].mean()),
                "gibbs": float(generated[:, index].mean()),
                "residual": float(residual[index]),
                "residual_ci95_low": float(residual_interval[0, index]),
                "residual_ci95_high": float(residual_interval[1, index]),
            }
            for index, key in enumerate(diagnostic_keys)
        },
        "control": {
            "jacobian_definition": "Cov(metric, factor_activation_count)",
            "factor_records": factor_records,
            "jacobian": jacobian.tolist(),
            "singular_values": singular_values.tolist(),
            "rank": rank,
            "ridge": args.ridge,
            "standardized": args.standardize,
            "diagnostic_scales": diagnostic_scales.tolist(),
            "proposed_weight_delta": delta.tolist(),
            "projected_metric_change": projected.tolist(),
            "relative_projection_error": relative_error,
            "max_abs_delta": max_abs_delta,
            "max_controllable_delta": args.max_controllable_delta,
            "robust_sensitivity_counts": robust_counts,
            "controllable": controllable,
        },
        "top_sensitivities": top_sensitivities,
        "per_piece": [
            {
                "piece_id": piece_id,
                "bach": source[index].tolist(),
                "gibbs": generated[index].tolist(),
                "jacobian": per_piece_jacobian[index].tolist(),
            }
            for index, piece_id in enumerate(train_ids)
        ],
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v6-control] wrote {args.output}", flush=True)
    print(f"[v6-control] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
