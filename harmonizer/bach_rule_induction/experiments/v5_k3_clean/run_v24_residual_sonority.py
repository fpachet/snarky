#!/usr/bin/env python3
"""Fit one exhaustive residual-sonority RuleGroup above a frozen baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import grouped_maxent
import k3
import numpy as np
import run_exact_factor_reinduction as exact
import yaml
from build_v24_selected_cache import selected_features
from run_v21_grouped_transition import paired_improvement, select_from_protocol
from run_v23_metric_bass_harmony import _point, _split

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v24_residual_sonority_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-v24-selected-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v24_residual_sonority_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V24_RESIDUAL_SONORITY_MODEL.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Return terminal checkpoints for frozen stability runs.",
    )
    parser.add_argument(
        "--penalties",
        help="Comma-separated frozen penalty subset for stability runs.",
    )
    return parser.parse_args()


def _initial(baseline: dict[str, Any]) -> exact.Parameters:
    model = baseline["model"]
    return exact.Parameters(
        register=np.asarray(model["register_logits"], dtype=np.float64),
        tonal=np.asarray(model["tonal_logits"], dtype=np.float64),
        factor_weights=np.asarray(
            [float(rule["weight"]) for rule in model["rules"]],
            dtype=np.float64,
        ),
    )


def _clean_path(path: list[dict[str, Any]]) -> None:
    for point in path:
        point.pop("_parameters", None)


def _status_names(feature_kind: str) -> tuple[str, ...]:
    if feature_kind == "central_residual_strong_sonority_status":
        return k3.RESIDUAL_STRONG_SONORITY_NAMES
    if feature_kind == "central_residual_weak_sonority_status":
        return k3.RESIDUAL_WEAK_SONORITY_NAMES
    if feature_kind == "central_joint_weak_resolution_status":
        return k3.JOINT_WEAK_RESOLUTION_NAMES
    if feature_kind == "central_joint_strong_resolution_status":
        return k3.JOINT_STRONG_RESOLUTION_NAMES
    if feature_kind == "central_bass_trajectory_status":
        return k3.BASS_TRAJECTORY_STATUS_NAMES
    if feature_kind == "central_bass_motion_status":
        return k3.BASS_MOTION_STATUS_NAMES
    if feature_kind == "central_strong_succession_status":
        return k3.STRONG_SUCCESSION_STATUS_NAMES
    raise ValueError(f"Unknown residual-sonority group: {feature_kind}")


def _markdown(result: dict[str, Any]) -> str:
    selection = result["selection"]
    experiment = result["experiment"]
    lines = [
        f"# {experiment['id']} — groupe exhaustif de sonorités résiduelles",
        "",
        f"Les {experiment['group_cell_count']} cellules sont apprises "
        "simultanément au-dessus du socle gelé. Elles ne dupliquent aucun",
        "accord nommé unique et forment une partition mutuellement exclusive.",
        "",
        "| Candidat | λ | NLL validation/pièce | Gain apparié | "
        "IC bootstrap 95 % | Chorals améliorés |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for index, point in enumerate(result["path"]):
        marker = " **← retenu**" if index == selection["selected_index"] else ""
        if index == 0:
            penalty = gain = interval = pieces = "—"
        else:
            paired = point["paired_vs_baseline"]
            low, high = paired["bootstrap_95_interval"]
            penalty = f"{point['group_penalty']:.6g}"
            gain = f"{paired['mean_improvement']:+.6f}"
            interval = f"[{low:+.6f}, {high:+.6f}]"
            pieces = (
                f"{paired['positive_piece_count']}/"
                f"{len(paired['piece_ids'])}"
            )
        lines.append(
            f"| {point['label']} | {penalty} | "
            f"{point['validation_piece_mean_nll']:.6f} | {gain} | "
            f"{interval} | {pieces} |{marker}"
        )
    lines.extend(
        [
            "",
            f"- Sélection : `{selection['selected_label']}`.",
            f"- Groupe retenu sur ce découpage : "
            f"`{str(selection['group_retained']).lower()}`.",
            "",
            "## Poids du candidat retenu",
            "",
            "| Statut | Poids |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{row['status']}` | {row['weight']:+.4f} |"
        for row in result["selected_group"]["weights"]
    )
    lines.extend(
        [
            "",
            "Ces coefficients sont des contributions conjointes. Un statut rare",
            "ou absent n'est pas promu en contrainte dure par cette expérience.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN":
        raise ValueError("Residual-sonority configuration must be frozen")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    baseline = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    grammar = exact._load_grammar(FACTOR_BASE / config["source_grammar"])
    features = selected_features(
        source=source,
        baseline=baseline,
        grammar=grammar,
        context=args.context,
        group=config["group"],
    )
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in features]:
        raise ValueError("Residual cache and frozen features disagree")
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    baseline_count = len(baseline["model"]["rules"])
    group_size = int(config["group"]["size"])
    baseline_indices = np.arange(baseline_count)
    all_indices = np.arange(baseline_count + group_size)
    train_baseline = _split(archive, "train", baseline_indices)
    validation_baseline = _split(archive, "validation", baseline_indices)
    train = _split(archive, "train", all_indices)
    validation = _split(archive, "validation", all_indices)
    estimation = config["estimation"]
    baseline_l1 = (
        float(estimation["l1_baseline_by_clause_complexity"])
        * np.asarray(
            [feature.complexity for feature in features[:baseline_count]],
            dtype=np.float64,
        )
    )
    return_best = not args.terminal
    prefit, _ = grouped_maxent.fit_grouped(
        train_baseline,
        validation_baseline,
        candidates,
        _initial(baseline),
        steps=int(estimation["steps_baseline_prefit"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=return_best,
    )
    baseline_parameters, baseline_fit = grouped_maxent.fit_grouped(
        train_baseline,
        validation_baseline,
        candidates,
        prefit,
        steps=int(estimation["steps_comparison"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=return_best,
    )
    baseline_point = _point(
        label=str(config.get("baseline_label", "socle réajusté")),
        penalty=None,
        train=train_baseline,
        validation=validation_baseline,
        candidates=candidates,
        parameters=baseline_parameters,
        group_indices={},
        fit=baseline_fit,
    )
    group_indices = np.arange(
        baseline_count,
        baseline_count + group_size,
    )
    initial_full = exact.Parameters(
        prefit.register.copy(),
        prefit.tonal.copy(),
        np.concatenate(
            (prefit.factor_weights, np.zeros(group_size))
        ),
    )
    l1 = np.concatenate(
        (
            baseline_l1,
            np.full(
                group_size,
                float(config["group"]["l1_inside_group"]),
            ),
        )
    )
    path = [{**baseline_point, "_parameters": baseline_parameters.copy()}]
    penalty_path = (
        [float(value) for value in args.penalties.split(",")]
        if args.penalties
        else list(map(float, estimation["group_penalty_path"]))
    )
    for index, penalty in enumerate(
        penalty_path,
        start=1,
    ):
        group = grouped_maxent.GroupPenalty(
            name=config["group"]["id"],
            indices=group_indices,
            strength=penalty,
            scale_by_sqrt_size=bool(
                config["group"]["l2_group_scaled_by_sqrt_size"]
            ),
            matrix_shape=tuple(map(int, config["group"]["matrix_shape"])),
        )
        parameters, fit = grouped_maxent.fit_grouped(
            train,
            validation,
            candidates,
            initial_full,
            steps=int(estimation["steps_comparison"]),
            learning_rate=float(estimation["learning_rate"]),
            l1=l1,
            l2=float(estimation["l2"]),
            groups=(group,),
            return_best_validation=return_best,
        )
        point = _point(
            label=f"{config['group'].get('label', config['group']['id'])} "
            f"λ={penalty:g}",
            penalty=penalty,
            train=train,
            validation=validation,
            candidates=candidates,
            parameters=parameters,
            group_indices={config["group"]["id"]: group_indices},
            fit=fit,
        )
        point["paired_vs_baseline"] = paired_improvement(
            baseline_point["validation_piece_nll"],
            point["validation_piece_nll"],
            seed=int(config["selection"]["paired_bootstrap_seed"]) + index,
            resamples=int(config["selection"]["paired_bootstrap_resamples"]),
        )
        path.append(point)
        print(
            f"[residual-group] lambda={penalty:g} "
            f"validation={point['validation_piece_mean_nll']:.6f} "
            f"gain={point['paired_vs_baseline']['mean_improvement']:+.6f}",
            flush=True,
        )
    selected_index, threshold, best_index = select_from_protocol(
        path,
        config["selection"],
    )
    selected_parameters = path[selected_index]["_parameters"]
    candidate_parameters = (
        selected_parameters
        if selected_index
        else path[best_index]["_parameters"]
    )
    group_weights = (
        candidate_parameters.factor_weights[group_indices]
        if candidate_parameters.factor_weights.size > baseline_count
        else np.zeros(group_size)
    )
    result = {
        "experiment": {
            "id": config["id"],
            "status": (
                "FROZEN_STABILITY_FOLD"
                if args.terminal
                else "STRUCTURE_SPLIT_ONLY"
            ),
            "checkpoint": "terminal" if args.terminal else "best_validation",
            "baseline_factor_count": baseline_count,
            "group_cell_count": group_size,
            "train_piece_count": int(
                np.unique(train["piece_ids"]).size
            ),
            "validation_piece_count": int(
                np.unique(validation["piece_ids"]).size
            ),
            "test_loaded": False,
        },
        "path": path,
        "selection": {
            "criterion": config["selection"]["criterion"],
            "selected_index": selected_index,
            "best_index": best_index,
            "threshold": threshold,
            "selected_label": path[selected_index]["label"],
            "best_label": path[best_index]["label"],
            "group_retained": selected_index != 0,
            "selected_penalty": (
                None
                if selected_index == 0
                else path[selected_index]["group_penalty"]
            ),
        },
        "selected_group": {
            "id": config["group"]["id"],
            "uses_best_candidate_when_not_selected": selected_index == 0,
            "path_index": (
                selected_index if selected_index else best_index
            ),
            "weights": [
                {
                    "status": name,
                    "weight": float(weight),
                }
                for name, weight in zip(
                    _status_names(config["group"]["feature_kind"]),
                    group_weights,
                    strict=True,
                )
            ],
        },
        "selected_parameters": {
            "register_logits": selected_parameters.register.tolist(),
            "tonal_logits": selected_parameters.tonal.tolist(),
            "factor_weights": selected_parameters.factor_weights.tolist(),
        },
    }
    _clean_path(path)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[residual-group] selected={result['selection']['selected_label']}",
        flush=True,
    )
    print(f"[residual-group] wrote {args.output}", flush=True)
    print(f"[residual-group] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
