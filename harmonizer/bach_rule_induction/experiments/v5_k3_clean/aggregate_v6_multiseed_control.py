#!/usr/bin/env python3
"""Aggregate independent V6 control runs into one stable train-only direction."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import run_v6_factor_controllability as control

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v6_train64_multimetric_iteration2_model.json"
DEFAULT_CONTROLS = tuple(
    FACTOR_BASE / f"v6_iteration3_seed{seed}_control.json"
    for seed in (10103, 20207, 30313)
)
DEFAULT_OUTPUT = FACTOR_BASE / "v6_iteration3_multiseed_control.json"
DEFAULT_REPORT = FACTOR_BASE / "V6_ITERATION3_MULTISEED_CONTROL.md"
DEFAULT_RIDGES = (1e-5, 1e-4, 1e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0, 3.0)


def _factor_records(model: dict[str, Any]) -> list[dict[str, Any]]:
    records = model["model"].get("factors")
    if records is not None:
        return records
    return [
        {
            "id": f"LEARNED-{index:03d}",
            "feature": rule["feature"],
        }
        for index, rule in enumerate(model["model"]["rules"], start=1)
    ]


def pairwise_cosines(vectors: np.ndarray) -> list[float]:
    """Return every pairwise cosine, rejecting null directions."""

    values = np.asarray(vectors, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] < 2:
        raise ValueError("At least two direction vectors are required")
    norms = np.linalg.norm(values, axis=1)
    if np.any(norms <= 1e-12):
        raise ValueError("Cannot compare a null control direction")
    return [
        float(values[left] @ values[right] / (norms[left] * norms[right]))
        for left, right in combinations(range(values.shape[0]), 2)
    ]


def _relative_remaining(
    jacobian: np.ndarray,
    residual: np.ndarray,
    delta: np.ndarray,
    scales: np.ndarray,
) -> float:
    before = np.linalg.norm(residual / scales)
    after = np.linalg.norm((residual - jacobian @ delta) / scales)
    return float(after / max(before, 1e-12))


def select_stable_ridge(
    jacobians: np.ndarray,
    residuals: np.ndarray,
    scales: np.ndarray,
    ridges: tuple[float, ...],
    *,
    minimum_cosine: float,
    max_abs_step: float,
) -> tuple[float, np.ndarray, list[dict[str, Any]]]:
    """Choose the least regularization satisfying explicit stability gates."""

    records = []
    chosen: tuple[float, np.ndarray] | None = None
    for ridge in ridges:
        seed_deltas = np.stack(
            [
                control._minimum_norm_delta(jacobian, residual, ridge, scale)[0]
                for jacobian, residual, scale in zip(
                    jacobians,
                    residuals,
                    scales,
                    strict=True,
                )
            ]
        )
        cosines = pairwise_cosines(seed_deltas)
        ensemble_delta = control._minimum_norm_delta(
            jacobians.mean(axis=0),
            residuals.mean(axis=0),
            ridge,
            scales.mean(axis=0),
        )[0]
        remaining = [
            _relative_remaining(jacobian, residual, ensemble_delta, scale)
            for jacobian, residual, scale in zip(
                jacobians,
                residuals,
                scales,
                strict=True,
            )
        ]
        stable = bool(
            min(cosines) >= minimum_cosine
            and max(remaining) < 1.0
            and np.max(np.abs(ensemble_delta)) <= max_abs_step
        )
        records.append(
            {
                "ridge": ridge,
                "pairwise_cosines": cosines,
                "minimum_pairwise_cosine": min(cosines),
                "per_seed_relative_remaining": remaining,
                "max_abs_ensemble_delta": float(
                    np.max(np.abs(ensemble_delta))
                ),
                "passes_stability_gate": stable,
            }
        )
        if stable and chosen is None:
            chosen = ridge, ensemble_delta
    if chosen is None:
        raise ValueError("No ridge value satisfies the multiseed stability gate")
    return chosen[0], chosen[1], records


def _markdown(result: dict[str, Any], model: dict[str, Any]) -> str:
    selected = result["control"]
    lines = [
        "# V6 — correction consensus multigraine, itération 3",
        "",
        "Trois estimations indépendantes utilisent les mêmes 32 chorals de train,",
        "deux chaînes par pièce et un budget fixe. Le test réservé n'est pas",
        "chargé et la structure des 30 facteurs reste gelée.",
        "",
        "## Diagnostic d'instabilité",
        "",
        (
            "- Cosinus des corrections presque non régularisées : "
            f"`{', '.join(f'{value:.3f}' for value in selected['raw_cosines'])}`."
        ),
        (
            "- Signes identiques sur les trois graines : "
            f"`{selected['raw_sign_agreement_count']}/"
            f"{selected['factor_count']}`."
        ),
        "",
        "L'inversion sans régularisation est donc rejetée.",
        "",
        "## Direction retenue",
        "",
        f"- Ridge sélectionné : `{selected['ridge']}`.",
        (
            "- Cosinus inter-graines après régularisation : "
            f"`{', '.join(f'{value:.3f}' for value in selected['pairwise_cosines'])}`."
        ),
        (
            "- Plus grand déplacement proposé : "
            f"`{selected['max_abs_delta']:.6f}`."
        ),
        (
            "- Résidu standardisé restant, ensemble : "
            f"`{selected['ensemble_relative_remaining']:.3f}`."
        ),
        "",
        "| Graine | Résidu restant | Amélioration projetée |",
        "|---:|---:|---:|",
    ]
    for seed_record in selected["per_seed_projection"]:
        lines.append(
            f"| {seed_record['seed']} | "
            f"{seed_record['relative_remaining']:.3f} | "
            f"{100 * seed_record['relative_improvement']:.1f} % |"
        )
    lines.extend(
        [
            "",
            "## Correction par facteur",
            "",
            "| Facteur | Delta consensus |",
            "|---|---:|",
        ]
    )
    for factor, delta in zip(
        _factor_records(model),
        selected["proposed_weight_delta"],
        strict=True,
    ):
        lines.append(f"| `{factor['id']}` | {delta:+.6f} |")
    lines.extend(
        [
            "",
            "Cette direction est apprise exclusivement sur train. Elle doit encore",
            "passer l'audit génératif de développement ; une projection linéaire",
            "positive n'est pas une preuve d'amélioration après rééchantillonnage.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--controls",
        type=Path,
        nargs="+",
        default=DEFAULT_CONTROLS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--ridges",
        default=",".join(str(value) for value in DEFAULT_RIDGES),
    )
    parser.add_argument("--minimum-cosine", type=float, default=0.8)
    parser.add_argument("--max-abs-step", type=float, default=0.05)
    parser.add_argument("--seeds", default="10103,20207,30313")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))
    payloads = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.controls
    ]
    if len(payloads) < 2:
        raise ValueError("Multiseed aggregation requires at least two controls")
    reference = payloads[0]["experiment"]
    diagnostic_keys = tuple(reference["diagnostics"])
    piece_ids = tuple(reference["piece_ids"])
    for payload in payloads:
        experiment = payload["experiment"]
        if (
            experiment["test_loaded"]
            or experiment["factor_structure_changed"]
            or tuple(experiment["diagnostics"]) != diagnostic_keys
            or tuple(experiment["piece_ids"]) != piece_ids
            or experiment["source_model"] != str(args.model.resolve())
        ):
            raise ValueError("Control runs do not share one train-only contract")
    jacobians = np.asarray(
        [payload["control"]["jacobian"] for payload in payloads],
        dtype=np.float64,
    )
    residuals = np.asarray(
        [
            [payload["diagnostics"][key]["residual"] for key in diagnostic_keys]
            for payload in payloads
        ],
        dtype=np.float64,
    )
    scales = np.asarray(
        [payload["control"]["diagnostic_scales"] for payload in payloads],
        dtype=np.float64,
    )
    raw_deltas = np.asarray(
        [payload["control"]["proposed_weight_delta"] for payload in payloads],
        dtype=np.float64,
    )
    ridges = tuple(float(value) for value in args.ridges.split(",") if value)
    if (
        not ridges
        or any(value <= 0 for value in ridges)
        or not 0 < args.minimum_cosine <= 1
        or args.max_abs_step <= 0
    ):
        raise ValueError("Invalid ridge grid or stability threshold")
    ridge, delta, ridge_search = select_stable_ridge(
        jacobians,
        residuals,
        scales,
        ridges,
        minimum_cosine=args.minimum_cosine,
        max_abs_step=args.max_abs_step,
    )
    seed_deltas = np.stack(
        [
            control._minimum_norm_delta(jacobian, residual, ridge, scale)[0]
            for jacobian, residual, scale in zip(
                jacobians,
                residuals,
                scales,
                strict=True,
            )
        ]
    )
    cosines = pairwise_cosines(seed_deltas)
    mean_jacobian = jacobians.mean(axis=0)
    mean_residual = residuals.mean(axis=0)
    mean_scales = scales.mean(axis=0)
    projected = mean_jacobian @ delta
    ensemble_remaining = _relative_remaining(
        mean_jacobian,
        mean_residual,
        delta,
        mean_scales,
    )
    declared_seeds = [int(value) for value in args.seeds.split(",") if value]
    if len(declared_seeds) != len(payloads):
        raise ValueError("One declared seed is required per control input")
    seeds = [
        int(payload["experiment"].get("seed", declared_seed))
        for payload, declared_seed in zip(
            payloads,
            declared_seeds,
            strict=True,
        )
    ]
    per_seed_projection = [
        {
            "seed": seed,
            "relative_remaining": remaining,
            "relative_improvement": 1.0 - remaining,
        }
        for seed, jacobian, residual, scale in zip(
            seeds,
            jacobians,
            residuals,
            scales,
            strict=True,
        )
        if (
            remaining := _relative_remaining(
                jacobian,
                residual,
                delta,
                scale,
            )
        )
        >= 0
    ]
    source_by_seed = np.asarray(
        [
            [payload["diagnostics"][key]["bach"] for key in diagnostic_keys]
            for payload in payloads
        ]
    )
    generated_by_seed = np.asarray(
        [
            [payload["diagnostics"][key]["gibbs"] for key in diagnostic_keys]
            for payload in payloads
        ]
    )
    factors = _factor_records(model)
    result = {
        "experiment": {
            "id": "F-K3-V6-ITERATION3-MULTISEED-CONTROL",
            "status": "TRAIN_ONLY_MULTISEED_CONTROL",
            "source_model": str(args.model.resolve()),
            "control_inputs": [str(path.resolve()) for path in args.controls],
            "seeds": seeds,
            "train_pieces": len(piece_ids),
            "piece_ids": list(piece_ids),
            "chains_per_piece": reference["chains_per_piece"],
            "samples": reference["samples"],
            "burn_in_sweeps": reference["burn_in_sweeps"],
            "sweeps_between": reference["sweeps_between"],
            "diagnostics": list(diagnostic_keys),
            "test_loaded": False,
            "factor_structure_changed": False,
            "weights_changed": False,
        },
        "diagnostics": {
            key: {
                "bach": float(source_by_seed[:, index].mean()),
                "gibbs": float(generated_by_seed[:, index].mean()),
                "residual": float(mean_residual[index]),
                "residual_seed_sd": float(residuals[:, index].std(ddof=1)),
                "projected_metric_change": float(projected[index]),
                "projected_remaining": float(mean_residual[index] - projected[index]),
            }
            for index, key in enumerate(diagnostic_keys)
        },
        "control": {
            "method": "multiseed_ridge_regularized_covariance_projection",
            "ridge": ridge,
            "ridge_search": ridge_search,
            "minimum_cosine_gate": args.minimum_cosine,
            "max_abs_step_gate": args.max_abs_step,
            "jacobian_definition": "mean_seed_Cov(metric, factor_activation_count)",
            "jacobian": mean_jacobian.tolist(),
            "diagnostic_scales": mean_scales.tolist(),
            "rank": int(np.linalg.matrix_rank(mean_jacobian)),
            "proposed_weight_delta": delta.tolist(),
            "projected_metric_change": projected.tolist(),
            "max_abs_delta": float(np.max(np.abs(delta))),
            "ensemble_relative_remaining": ensemble_remaining,
            "pairwise_cosines": cosines,
            "minimum_pairwise_cosine": min(cosines),
            "raw_cosines": pairwise_cosines(raw_deltas),
            "raw_sign_agreement_count": int(
                np.all(np.sign(raw_deltas) == np.sign(raw_deltas[0]), axis=0).sum()
            ),
            "factor_count": len(factors),
            "per_seed_projection": per_seed_projection,
            "stable": True,
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result, model), encoding="utf-8")
    print(f"[v6-multiseed] wrote {args.output}", flush=True)
    print(f"[v6-multiseed] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
