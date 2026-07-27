#!/usr/bin/env python3
"""Calibrate the V3.3 tonal search against repeated full-pipeline null runs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import run_poc as base


def experiment_root() -> Path:
    return Path(__file__).resolve().parent


def repository_root() -> Path:
    return experiment_root().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def null_maximum(payload: dict[str, Any]) -> float | None:
    maximum = payload["model"]["family_calibration"]["maximum_supported"]
    return None if maximum is None else float(maximum["joint_min_z"])


def empirical_max_p_value(observed: float, null_maxima: list[float | None]) -> dict:
    exceedances = sum(
        maximum is not None and maximum >= observed for maximum in null_maxima
    )
    return {
        "exceedances": exceedances,
        "replicates": len(null_maxima),
        "p_value": (exceedances + 1) / (len(null_maxima) + 1),
    }


def classify_empirical_p(p_value: float, replicates: int) -> str:
    if replicates < 19:
        return "PILOT_UNDERPOWERED"
    if p_value <= 0.05:
        return "PASSES_EMPIRICAL_FWER_0_05"
    return "DOES_NOT_PASS_EMPIRICAL_FWER_0_05"


def candidate_result(
    record: dict[str, Any],
    null_maxima: list[float | None],
) -> dict[str, Any]:
    observed = min(
        float(record["train"]["z_score"]),
        float(record["validation"]["z_score"]),
    )
    calibration = empirical_max_p_value(observed, null_maxima)
    return {
        "mode": record["mode"],
        "subject_voice": record["subject_voice"],
        "subject_voice_index": record["subject_voice_index"],
        "source_bass_class": record["source_bass_class"],
        "target_bass_class": record["target_bass_class"],
        "interpretation": record["interpretation"],
        "joint_min_z": observed,
        "train_z": record["train"]["z_score"],
        "validation_z": record["validation"]["z_score"],
        "empirical_fwer": calibration,
        "classification": classify_empirical_p(
            calibration["p_value"],
            calibration["replicates"],
        ),
    }


def calibration_quantiles(null_maxima: list[float | None]) -> dict[str, float | None]:
    finite = np.asarray(
        [value for value in null_maxima if value is not None],
        dtype=np.float64,
    )
    if not finite.size:
        return {"q50": None, "q90": None, "q95": None, "maximum": None}
    return {
        "q50": float(np.quantile(finite, 0.50, method="higher")),
        "q90": float(np.quantile(finite, 0.90, method="higher")),
        "q95": float(np.quantile(finite, 0.95, method="higher")),
        "maximum": float(finite.max()),
    }


def build_command(args: argparse.Namespace, seed: int, output_stem: str) -> list[str]:
    return [
        sys.executable,
        str(experiment_root() / "run_leading_tone_refinement.py"),
        "--seed",
        str(seed),
        "--stratify-mode",
        "--min-train-support",
        str(args.min_train_support),
        "--min-validation-support",
        str(args.min_validation_support),
        "--candidate-budget",
        str(args.candidate_budget),
        "--bootstrap-replicates",
        str(args.null_bootstrap_replicates),
        "--max-steps",
        str(args.max_steps),
        "--null-shuffle",
        "--results-dir",
        str(args.work_dir),
        "--output-stem",
        output_stem,
    ]


def run_null_replicate(
    args: argparse.Namespace,
    index: int,
    seed: int,
) -> tuple[int, Path, dict[str, Any]]:
    output_stem = f"null_{index:03d}_seed_{seed}"
    json_path = args.work_dir / f"{output_stem}.json"
    if json_path.exists() and not args.force:
        payload = load_json(json_path)
        experiment = payload["experiment"]
        if (
            experiment["seed"] == seed
            and experiment["null_shuffle"]
            and experiment["mode_stratified"]
        ):
            return seed, json_path, payload

    environment = os.environ.copy()
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        environment[name] = "1"
    completed = subprocess.run(
        build_command(args, seed, output_stem),
        cwd=repository_root(),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"Null replicate seed={seed} failed:\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return seed, json_path, load_json(json_path)


def markdown_report(result: dict[str, Any]) -> str:
    calibration = result["calibration"]
    lines = [
        "# POC V3.4 — calibration familiale des règles tonales",
        "",
        "## Protocole",
        "",
        (
            f"- {calibration['replicates']} permutations indépendantes, avec "
            "réajustement complet de la baseline à chaque réplication."
        ),
        "- Famille : 864 clauses mode × voix × basse source × basse cible.",
        "- Statistique : `min(z train, z validation)`.",
        (
            "- Maximum calculé parmi toutes les clauses qui passent les seuils "
            "de support, avant les seuils de confirmation et de z."
        ),
        "- p empirique corrigé famille : `(1 + dépassements) / (1 + B)`.",
        "- Le test final reste scellé.",
        "",
        "## Distribution du maximum sous le nul",
        "",
        "| Maxima définis | Médiane | q90 | q95 | Maximum observé |",
        "|---:|---:|---:|---:|---:|",
    ]
    quantiles = calibration["null_maximum_quantiles"]

    def number(value: float | None) -> str:
        return "—" if value is None else f"{value:.3f}"

    lines.append(
        f"| {calibration['defined_null_maxima']}/"
        f"{calibration['replicates']} | {number(quantiles['q50'])} | "
        f"{number(quantiles['q90'])} | {number(quantiles['q95'])} | "
        f"{number(quantiles['maximum'])} |"
    )
    lines.extend(
        [
            "",
            "## Candidats authentiques",
            "",
            "| Mode | Voix | Basse | min-z | Dépassements/B | p FWER | Statut |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for record in result["candidate_results"]:
        fwer = record["empirical_fwer"]
        lines.append(
            f"| {record['mode']} | {record['subject_voice']} | "
            f"{record['source_bass_class']}→{record['target_bass_class']} | "
            f"{record['joint_min_z']:.3f} | "
            f"{fwer['exceedances']}/{fwer['replicates']} | "
            f"{fwer['p_value']:.4f} | `{record['classification']}` |"
        )
    lines.extend(["", "## Interprétation", ""])
    if calibration["replicates"] >= 49:
        lines.extend(
            [
                "La résolution empirique minimale est ici de `0,02`. Une seule",
                "clause passe le seuil familial de 5 % ; les autres restent des",
                "hypothèses descriptives, non des règles statistiquement retenues.",
            ]
        )
    else:
        lines.extend(
            [
                "Cette calibration reste pilote : le nombre de permutations ne",
                "donne pas encore une résolution suffisante autour de 5 %.",
            ]
        )
    lines.extend(
        [
            "",
            "Le contrôle porte sur le meilleur résultat recherché dans la famille",
            "entière, et non sur chaque clause considérée isolément.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = experiment_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--authentic-result",
        type=Path,
        default=root / "results/v3_3_mode_stratified_leading_tone.json",
    )
    parser.add_argument("--replicates", type=int, default=49)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--base-seed", type=int, default=1729)
    parser.add_argument("--seed-step", type=int, default=1009)
    parser.add_argument("--min-train-support", type=int, default=20)
    parser.add_argument("--min-validation-support", type=int, default=8)
    parser.add_argument("--candidate-budget", type=int, default=8)
    parser.add_argument("--null-bootstrap-replicates", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=root / "work/tonal-family-calibration",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=root / "results",
    )
    parser.add_argument(
        "--output-stem",
        default="v3_4_tonal_family_calibration",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.replicates < 1:
        parser.error("--replicates must be positive")
    if args.workers < 1:
        parser.error("--workers must be positive")
    args.authentic_result = args.authentic_result.resolve()
    args.work_dir = args.work_dir.resolve()
    args.results_dir = args.results_dir.resolve()
    return args


def main() -> int:
    args = parse_args()
    authentic = load_json(args.authentic_result)
    if not authentic["experiment"].get("mode_stratified"):
        raise ValueError("Authentic result is not mode-stratified V3.3")
    if authentic["experiment"]["test_opened"]:
        raise ValueError("Authentic result unexpectedly opened the final test")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    seeds = [
        args.base_seed + args.seed_step * (index + 1)
        for index in range(args.replicates)
    ]
    null_payloads: dict[int, tuple[Path, dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_null_replicate, args, index, seed): seed
            for index, seed in enumerate(seeds, start=1)
        }
        for completed_index, future in enumerate(as_completed(futures), start=1):
            seed, path, payload = future.result()
            null_payloads[seed] = (path, payload)
            maximum = null_maximum(payload)
            maximum_label = "none" if maximum is None else f"{maximum:.3f}"
            print(
                f"[null-calibration] {completed_index}/{args.replicates} "
                f"seed={seed} max={maximum_label}",
                flush=True,
            )

    ordered = [null_payloads[seed] for seed in seeds]
    null_maxima = [null_maximum(payload) for _, payload in ordered]
    candidate_results = [
        candidate_result(record, null_maxima)
        for record in authentic["model"]["selected_refinements"]
    ]
    candidate_results.sort(key=lambda record: record["joint_min_z"], reverse=True)
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_4_tonal_family_calibration",
            "test_opened": False,
            "authentic_result": str(args.authentic_result),
            "authentic_result_sha256": base.sha256_file(args.authentic_result),
        },
        "calibration": {
            "replicates": args.replicates,
            "workers": args.workers,
            "max_steps": args.max_steps,
            "null_bootstrap_replicates": args.null_bootstrap_replicates,
            "min_train_support": args.min_train_support,
            "min_validation_support": args.min_validation_support,
            "base_seed": args.base_seed,
            "seed_step": args.seed_step,
            "seeds": seeds,
            "statistic": "min(train_residual_z, validation_residual_z)",
            "maximum_scope": "support_gated_864_candidate_family",
            "defined_null_maxima": sum(value is not None for value in null_maxima),
            "null_maxima": null_maxima,
            "null_maximum_quantiles": calibration_quantiles(null_maxima),
            "raw_null_results": [
                {
                    "seed": seed,
                    "path": str(path),
                    "sha256": base.sha256_file(path),
                    "maximum_supported_candidate": payload["model"][
                        "family_calibration"
                    ]["maximum_supported"],
                    "supported_candidate_count": payload["model"][
                        "family_calibration"
                    ]["supported_candidate_count"],
                    "confirmation_gated_candidate_count": payload["model"][
                        "family_calibration"
                    ]["confirmation_gated_candidate_count"],
                    "threshold_passing_candidate_count": payload["model"][
                        "family_calibration"
                    ]["threshold_passing_candidate_count"],
                }
                for seed, (path, payload) in zip(seeds, ordered, strict=True)
            ],
        },
        "candidate_results": candidate_results,
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.results_dir / f"{args.output_stem}.json"
    report_path = args.results_dir / f"{args.output_stem.upper()}_REPORT.md"
    base.json_dump(json_path, result)
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"[done] wrote {json_path}", flush=True)
    print(f"[done] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
