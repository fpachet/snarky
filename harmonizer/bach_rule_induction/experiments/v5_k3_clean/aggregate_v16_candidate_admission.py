#!/usr/bin/env python3
"""Apply the V16 Pareto admission gate to multiseed candidate sensitivities."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SHORTLIST = FACTOR_BASE / "v16_exact_candidate_shortlist.json"
DEFAULT_CONTROLS = tuple(
    FACTOR_BASE / f"v16_candidate_seed{seed}_control.json"
    for seed in (10103, 20207, 30313)
)
DEFAULT_OUTPUT = FACTOR_BASE / "v16_candidate_admission.json"
DEFAULT_REPORT = FACTOR_BASE / "V16_CANDIDATE_ADMISSION.md"


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator <= 1e-12:
        return 0.0
    return float(left @ right / denominator)


def _conditional_step(
    statistic: dict[str, Any],
    max_abs_step: float,
) -> float:
    gradient = float(statistic["gradient"])
    gain = float(statistic["approximate_nll_gain"])
    if abs(gradient) <= 1e-12 or gain <= 0:
        return 0.0
    newton_step = 2.0 * gain / gradient
    return float(np.clip(newton_step, -max_abs_step, max_abs_step))


def evaluate_candidate(
    *,
    candidate: dict[str, Any],
    sensitivities: np.ndarray,
    residuals: np.ndarray,
    scales: np.ndarray,
    max_abs_step: float,
    minimum_effect_cosine: float,
    maximum_seed_regression: float,
    minimum_ensemble_improvement: float,
) -> dict[str, Any]:
    """Project one conditionally useful candidate through every Gibbs seed."""

    step = _conditional_step(candidate["conditional"], max_abs_step)
    effects = sensitivities * step
    before = np.linalg.norm(residuals / scales, axis=1)
    after = np.linalg.norm((residuals - effects) / scales, axis=1)
    relative_remaining = after / np.maximum(before, 1e-12)
    standardized_effects = effects / scales
    cosines = [
        _cosine(standardized_effects[left], standardized_effects[right])
        for left, right in combinations(range(sensitivities.shape[0]), 2)
    ]
    minimum_cosine = min(cosines)
    ensemble_residual = residuals.mean(axis=0)
    ensemble_scale = scales.mean(axis=0)
    ensemble_effect = effects.mean(axis=0)
    ensemble_before = np.linalg.norm(ensemble_residual / ensemble_scale)
    ensemble_after = np.linalg.norm(
        (ensemble_residual - ensemble_effect) / ensemble_scale
    )
    ensemble_remaining = float(
        ensemble_after / max(ensemble_before, 1e-12)
    )
    stable = bool(minimum_cosine >= minimum_effect_cosine)
    non_regressive = bool(
        np.max(relative_remaining) <= 1.0 + maximum_seed_regression
        and ensemble_remaining <= 1.0 - minimum_ensemble_improvement
    )
    admitted = bool(
        candidate["conditional"]["column_score"] > 0
        and abs(step) > 0
        and stable
        and non_regressive
    )
    return {
        "rank": candidate["rank"],
        "feature": candidate["feature"],
        "family": candidate["family"],
        "conditional_column_score": candidate["conditional"]["column_score"],
        "conditional_approximate_nll_gain": candidate["conditional"][
            "approximate_nll_gain"
        ],
        "proposed_weight_step": step,
        "pairwise_effect_cosines": cosines,
        "minimum_effect_cosine": minimum_cosine,
        "per_seed_relative_remaining": relative_remaining.tolist(),
        "ensemble_relative_remaining": ensemble_remaining,
        "stable_effect": stable,
        "non_regressive_generation_projection": non_regressive,
        "admitted": admitted,
    }


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V16 — admission hybride des candidats",
        "",
        "Chaque colonne du top-K a un poids nul dans les chaînes. Sa covariance",
        "avec les dix diagnostics estime l'effet local qu'aurait le petit pas",
        "conditionnel proposé. Un candidat n'est admissible que si cet effet est",
        "stable entre graines et non régressif pour la distance générative.",
        "",
        f"- Graines indépendantes : `{experiment['seed_count']}`.",
        f"- Pas maximal : `{experiment['max_abs_step']}`.",
        (
            "- Cosinus inter-graines minimal : "
            f"`{experiment['minimum_effect_cosine']}`."
        ),
        (
            "- Régression maximale tolérée par graine : "
            f"`{100 * experiment['maximum_seed_regression']:.1f} %`."
        ),
        (
            "- Amélioration ensemble minimale : "
            f"`{100 * experiment['minimum_ensemble_improvement']:.1f} %`."
        ),
        f"- Candidats admissibles : `{experiment['admitted_count']}`.",
        f"- Candidat proposé : `{experiment['proposed_candidate_rank']}`.",
        "",
        "| Rang | Candidat | Pas | cos min | Résidu ensemble | Admis |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for candidate in result["candidates"]:
        lines.append(
            f"| {candidate['rank']} | `{candidate['feature']['label']}` | "
            f"{candidate['proposed_weight_step']:+.6f} | "
            f"{candidate['minimum_effect_cosine']:+.3f} | "
            f"{candidate['ensemble_relative_remaining']:.3f} | "
            f"{str(candidate['admitted']).lower()} |"
        )
    lines.extend(
        [
            "",
            "L'admission est locale : le candidat proposé doit encore être ajouté,",
            "réajusté conjointement par pseudo-vraisemblance exacte, puis soumis à",
            "un nouvel audit génératif. Le test réservé reste fermé.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shortlist", type=Path, default=DEFAULT_SHORTLIST)
    parser.add_argument(
        "--controls",
        type=Path,
        nargs="+",
        default=DEFAULT_CONTROLS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-abs-step", type=float, default=0.15)
    parser.add_argument("--minimum-effect-cosine", type=float, default=0.5)
    parser.add_argument("--maximum-seed-regression", type=float, default=0.02)
    parser.add_argument(
        "--minimum-ensemble-improvement",
        type=float,
        default=0.0,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.max_abs_step <= 0
        or not -1 <= args.minimum_effect_cosine <= 1
        or args.maximum_seed_regression < 0
        or not 0 <= args.minimum_ensemble_improvement < 1
    ):
        raise ValueError("Invalid V16 admission thresholds")
    shortlist = json.loads(args.shortlist.read_text(encoding="utf-8"))
    controls = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in args.controls
    ]
    if len(controls) < 3:
        raise ValueError("V16 admission requires at least three independent seeds")
    reference = controls[0]["experiment"]
    diagnostics = tuple(reference["diagnostics"])
    piece_ids = tuple(reference["piece_ids"])
    for control in controls:
        experiment = control["experiment"]
        if (
            experiment["test_loaded"]
            or tuple(experiment["diagnostics"]) != diagnostics
            or tuple(experiment["piece_ids"]) != piece_ids
            or experiment["source_model"] != reference["source_model"]
            or experiment["monitor_shortlist"]
            != str(args.shortlist.resolve())
        ):
            raise ValueError("Control runs do not share the V16 train contract")

    records = controls[0]["control"]["factor_records"]
    record_ids = [record["id"] for record in records]
    expected_candidate_ids = [
        f"V16-CANDIDATE-{candidate['rank']:03d}"
        for candidate in shortlist["candidates"]
    ]
    candidate_indices = []
    for candidate_id in expected_candidate_ids:
        if record_ids.count(candidate_id) != 1:
            raise ValueError(f"Missing or duplicate monitored factor {candidate_id}")
        candidate_indices.append(record_ids.index(candidate_id))
    for control in controls[1:]:
        if control["control"]["factor_records"] != records:
            raise ValueError("Monitored factor order differs between seeds")

    residuals = np.asarray(
        [
            [control["diagnostics"][key]["residual"] for key in diagnostics]
            for control in controls
        ],
        dtype=np.float64,
    )
    scales = np.asarray(
        [control["control"]["diagnostic_scales"] for control in controls],
        dtype=np.float64,
    )
    jacobians = np.asarray(
        [control["control"]["jacobian"] for control in controls],
        dtype=np.float64,
    )
    evaluated = [
        evaluate_candidate(
            candidate=candidate,
            sensitivities=jacobians[:, :, index],
            residuals=residuals,
            scales=scales,
            max_abs_step=args.max_abs_step,
            minimum_effect_cosine=args.minimum_effect_cosine,
            maximum_seed_regression=args.maximum_seed_regression,
            minimum_ensemble_improvement=args.minimum_ensemble_improvement,
        )
        for candidate, index in zip(
            shortlist["candidates"],
            candidate_indices,
            strict=True,
        )
    ]
    admitted = [candidate for candidate in evaluated if candidate["admitted"]]
    proposed = (
        None
        if not admitted
        else max(
            admitted,
            key=lambda candidate: (
                candidate["conditional_column_score"],
                -candidate["rank"],
            ),
        )
    )
    result = {
        "experiment": {
            "id": "F-K3-V16-CANDIDATE-ADMISSION",
            "status": (
                "CANDIDATE_PROPOSED_PENDING_EXACT_REFIT"
                if proposed is not None
                else "NO_CANDIDATE_ADMISSIBLE"
            ),
            "shortlist": str(args.shortlist.resolve()),
            "controls": [str(path.resolve()) for path in args.controls],
            "source_model": reference["source_model"],
            "diagnostics": list(diagnostics),
            "piece_ids": list(piece_ids),
            "seed_count": len(controls),
            "max_abs_step": args.max_abs_step,
            "minimum_effect_cosine": args.minimum_effect_cosine,
            "maximum_seed_regression": args.maximum_seed_regression,
            "minimum_ensemble_improvement": (
                args.minimum_ensemble_improvement
            ),
            "admitted_count": len(admitted),
            "proposed_candidate_rank": (
                None if proposed is None else proposed["rank"]
            ),
            "test_loaded": False,
        },
        "candidates": evaluated,
        "proposed_candidate": proposed,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v16-admission] wrote {args.output}", flush=True)
    print(f"[v16-admission] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
