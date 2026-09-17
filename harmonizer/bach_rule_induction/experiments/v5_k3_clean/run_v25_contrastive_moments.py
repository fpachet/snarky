#!/usr/bin/env python3
"""Learn V25 weak-sonority weights from Bach-minus-generated moments."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import yaml
from audit_v25_weak_sonority_moments import weak_status_counts

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v25_weak_sonority_config.yaml"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v25_contrastive_moment_fit.json"
DEFAULT_MODEL = FACTOR_BASE / "v25_contrastive_moment_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V25_CONTRASTIVE_MOMENT_FIT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--reuse-existing-history",
        action="store_true",
        help="Rematerialize the selected checkpoint without resampling.",
    )
    return parser.parse_args()


def _sample_piece(
    task: tuple[
        str,
        str,
        dict[str, Any],
        np.ndarray,
        int,
        int,
        str,
    ],
) -> tuple[np.ndarray, np.ndarray, int]:
    (
        piece_id,
        score_path,
        model,
        residual_weights,
        seed,
        sweeps,
        update_schedule,
    ) = task
    lattice = k3.extract_piece_lattice(Path(score_path), piece_id)
    fixed = np.zeros_like(lattice.blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    local_seed = generative._piece_seed(piece_id, seed)
    generated = k3.rhythmic_gibbs_sample(
        lattice.blocks,
        lattice.attacks,
        fixed,
        candidate_min=model["candidate_min"],
        candidate_max=model["candidate_max"],
        register_logits=model["register_logits"],
        features=(*model["features"], *model["residual_features"]),
        weights=np.concatenate((model["weights"], residual_weights)),
        sweeps=sweeps,
        seed=local_seed,
        tonal_logits=model["tonal_logits"],
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels,
        update_schedule=update_schedule,
    )
    authentic, total = weak_status_counts(
        lattice.blocks,
        lattice,
        candidate_min=model["candidate_min"],
        candidate_max=model["candidate_max"],
    )
    sampled, generated_total = weak_status_counts(
        generated,
        lattice,
        candidate_min=model["candidate_min"],
        candidate_max=model["candidate_max"],
    )
    if generated_total != total:
        raise AssertionError("Authentic and generated weak-block totals differ")
    return authentic, sampled, total


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V25 — apprentissage génératif des licences faibles",
        "",
        "Le vocabulaire V25 et les 65 poids V24 restent gelés. Seuls les neuf",
        "poids faibles sont mis à jour par les moments `Bach − générateur`.",
        "",
        "| Itération | Résiduel Bach | Résiduel généré | MAE | Norme poids |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in result["history"]:
        lines.append(
            f"| {row['iteration']} | {row['authentic_residual_rate']:.4f} | "
            f"{row['generated_residual_rate']:.4f} | "
            f"{row['moment_mae']:.5f} | {row['weight_norm']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Point d'arrêt sélectionné",
            "",
            f"L'itération `{result['selection']['iteration']}` minimise la MAE "
            "des neuf moments sur l'échantillon d'apprentissage. Ses poids, plus "
            "modérés que ceux de la dernière itération, sont exportés.",
            "",
            "| Statut | Bach | Généré au point d'arrêt | Poids |",
            "|---|---:|---:|---:|",
        ]
    )
    selected = result["history"][result["selection"]["iteration"]]
    for index, status in enumerate(k3.RESIDUAL_WEAK_SONORITY_NAMES):
        lines.append(
            f"| `{status}` | {selected['authentic_rates'][index]:.4f} | "
            f"{selected['generated_rates'][index]:.4f} | "
            f"{result['weights'][index]:+.4f} |"
        )
    lines.extend(
        [
            "",
            "La validation n'est jamais consultée pendant ces mises à jour.",
            "Aucun statut n'est converti en contrainte dure.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    baseline = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    corpus = baseline["corpus"]
    model_record = baseline["model"]
    residual_features = k3.residual_weak_sonority_feature_catalogue()
    prepared = {
        "candidate_min": int(corpus["candidate_min"]),
        "candidate_max": int(corpus["candidate_max"]),
        "register_logits": np.asarray(
            model_record["register_logits"],
            dtype=np.float64,
        ),
        "tonal_logits": np.asarray(
            model_record["tonal_logits"],
            dtype=np.float64,
        ),
        "features": tuple(
            k3.feature_from_model_record(rule)
            for rule in model_record["rules"]
        ),
        "weights": np.asarray(
            [float(rule["weight"]) for rule in model_record["rules"]],
            dtype=np.float64,
        ),
        "residual_features": residual_features,
    }
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    sampling = config["sampling"]
    piece_ids = sorted(
        splits["train"],
        key=generative._stable_order,
    )[: int(sampling["pieces"])]
    score_paths = {
        piece_id: str(generative._score_path(args.scores, piece_id))
        for piece_id in piece_ids
    }
    optimization = config["optimization"]
    iterations = int(optimization["iterations"])
    if args.reuse_existing_history:
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        history = previous["history"]
        weights = np.asarray(
            previous.get("final_iteration_weights", previous["weights"]),
            dtype=np.float64,
        )
    else:
        weights = np.zeros(len(residual_features), dtype=np.float64)
        history = []
        for iteration in range(iterations + 1):
            tasks = [
                (
                    piece_id,
                    score_paths[piece_id],
                    prepared,
                    weights,
                    int(seed),
                    int(sampling["sweeps"]),
                    str(sampling["update_schedule"]),
                )
                for piece_id in piece_ids
                for seed in sampling["seeds"]
            ]
            authentic = np.zeros_like(weights)
            generated = np.zeros_like(weights)
            weak_total = 0
            with ProcessPoolExecutor(
                max_workers=int(sampling["workers"])
            ) as executor:
                for completed, (source, sampled, total) in enumerate(
                    executor.map(_sample_piece, tasks),
                    start=1,
                ):
                    authentic += source
                    generated += sampled
                    weak_total += total
                    if completed % 8 == 0 or completed == len(tasks):
                        print(
                            f"[v25] iteration={iteration} "
                            f"pieces={completed}/{len(tasks)}",
                            flush=True,
                        )
            authentic_rates = authentic / weak_total
            generated_rates = generated / weak_total
            gradient = authentic_rates - generated_rates
            history.append(
                {
                    "iteration": iteration,
                    "weak_blocks": weak_total,
                    "authentic_rates": authentic_rates.tolist(),
                    "generated_rates": generated_rates.tolist(),
                    "authentic_residual_rate": float(authentic_rates.sum()),
                    "generated_residual_rate": float(generated_rates.sum()),
                    "moment_mae": float(np.abs(gradient).mean()),
                    "gradient": gradient.tolist(),
                    "weights_before_update": weights.tolist(),
                    "weight_norm": float(np.linalg.norm(weights)),
                }
            )
            print(
                f"[v25] iteration={iteration} "
                f"residual={generated_rates.sum():.4f} "
                f"target={authentic_rates.sum():.4f} "
                f"mae={np.abs(gradient).mean():.5f}",
                flush=True,
            )
            if iteration == iterations:
                break
            weights += float(optimization["learning_rate"]) * (
                gradient - float(optimization["l2"]) * weights
            )
            weights = np.clip(
                weights,
                -float(optimization["weight_clip"]),
                float(optimization["weight_clip"]),
            )
    selected = min(history, key=lambda row: row["moment_mae"])
    selected_weights = np.asarray(
        selected["weights_before_update"],
        dtype=np.float64,
    )
    result = {
        "experiment": {
            "id": "K3-V25-CONTRASTIVE-MOMENT-1",
            "status": "STRUCTURE_TRAIN_CONTRASTIVE_CANDIDATE",
            "piece_count": len(piece_ids),
            "piece_ids": piece_ids,
            "iterations": iterations,
            "validation_used_during_updates": False,
            "test_loaded": False,
        },
        "history": history,
        "selection": {
            "criterion": "minimum_train_moment_mae",
            "iteration": int(selected["iteration"]),
            "moment_mae": float(selected["moment_mae"]),
            "validation_used": False,
        },
        "weights": selected_weights.tolist(),
        "final_iteration_weights": weights.tolist(),
        "features": [feature.to_dict() for feature in residual_features],
    }
    candidate = json.loads(json.dumps(baseline))
    candidate["experiment"] = {
        **baseline["experiment"],
        "id": "K3-V25-CONTRASTIVE-MOMENT-MODEL-1",
        "status": "GENERATIVE_CALIBRATION_CANDIDATE",
        "source_fit": result["experiment"]["id"],
        "selected_iteration": int(selected["iteration"]),
        "selection_criterion": result["selection"]["criterion"],
        "learned_factor_count": len(model_record["rules"]) + len(weights),
        "new_weak_sonority_factor_count": len(weights),
        "rule_group_count": int(baseline["experiment"]["rule_group_count"]) + 1,
        "test_loaded": False,
    }
    candidate["model"]["rules"].extend(
        {
            "id": f"F-K3-V25-{index:03d}",
            "family": "residual_weak_sonority_status",
            "clause": feature.label,
            "feature": feature.to_dict(),
            "weight": float(weight),
            "origin": "learned_from_bach_minus_generated_moments",
            "human_authored": False,
            "calls_other_rules": False,
            "rule_group": "RG-LEARNED-V25-001",
        }
        for index, (feature, weight) in enumerate(
            zip(residual_features, selected_weights, strict=True),
            start=1,
        )
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.model.write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v25] wrote {args.output}", flush=True)
    print(f"[v25] wrote {args.model}", flush=True)
    print(f"[v25] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
