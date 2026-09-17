#!/usr/bin/env python3
"""Fit and ablate the two compact V23 factor groups on exact conditionals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import grouped_maxent
import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_v18_explanatory_sparse_induction as sparse
import yaml
from build_v23_selected_cache import selected_features
from run_v21_grouped_transition import paired_improvement, select_from_protocol

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v23_metric_bass_harmony_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-v23-selected-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v23_metric_bass_harmony_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V23_METRIC_BASS_HARMONY_MODEL.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _split(archive: Any, name: str, indices: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "factors": archive[f"{name}_factors"][:, :, indices],
        "chosen": archive[f"{name}_chosen"],
        "piece_ids": archive[f"{name}_piece_ids"],
        "voices": archive[f"{name}_voices"],
        "modes": archive[f"{name}_modes"],
        "tonics": archive[f"{name}_tonics"],
    }


def _point(
    *,
    label: str,
    penalty: float | None,
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    candidates: np.ndarray,
    parameters: exact.Parameters,
    group_indices: dict[str, np.ndarray],
    fit: dict[str, Any],
) -> dict[str, Any]:
    train_mean, train_se, _ = sparse._piece_nll(train, candidates, parameters)
    validation_mean, validation_se, validation_pieces = sparse._piece_nll(
        validation,
        candidates,
        parameters,
    )
    return {
        "label": label,
        "group_penalty": penalty,
        "train_piece_mean_nll": train_mean,
        "train_piece_standard_error": train_se,
        "validation_piece_mean_nll": validation_mean,
        "validation_piece_standard_error": validation_se,
        "validation_piece_nll": validation_pieces,
        "group_norms": {
            name: float(np.linalg.norm(parameters.factor_weights[indices]))
            for name, indices in group_indices.items()
        },
        "group_max_abs_weights": {
            name: float(
                np.max(
                    np.abs(parameters.factor_weights[indices]),
                    initial=0.0,
                )
            )
            for name, indices in group_indices.items()
        },
        "terminal_validation_decision_nll": float(
            fit["history"][-1]["validation_nll"]
        ),
        "terminal_train_decision_nll": float(
            fit["history"][-1]["train_nll"]
        ),
        "fit": fit,
        "_parameters": parameters,
    }


def _initial_v22(
    baseline: dict[str, Any],
    features: tuple[k3.FeatureSpec, ...],
    baseline_count: int,
) -> exact.Parameters:
    selected = baseline["selected_model"]
    rules = selected["baseline_rules"]
    rule_weights = [float(rule["weight"]) for rule in rules]
    root_rows = baseline["selected_group"]["weights"]
    root_weights = [float(row["weight"]) for row in root_rows]
    if len(rule_weights) + len(root_weights) != baseline_count:
        raise ValueError("V22 feature count disagrees with V23 cache")
    root_features = features[len(rule_weights):baseline_count]
    for feature, row in zip(root_features, root_rows, strict=True):
        expected_mode = "major" if feature.second_value == 0 else "minor"
        if (
            row["mode"] != expected_mode
            or int(row["root_motion_class"]) != feature.value
        ):
            raise ValueError("V22 root-motion weights are out of feature order")
    return exact.Parameters(
        register=np.asarray(selected["register_logits"], dtype=np.float64),
        tonal=np.asarray(selected["tonal_logits"], dtype=np.float64),
        factor_weights=np.asarray(
            [*rule_weights, *root_weights],
            dtype=np.float64,
        ),
    )


def _group_penalty(
    spec: dict[str, Any],
    indices: np.ndarray,
    strength: float,
) -> grouped_maxent.GroupPenalty:
    identifiability = spec["identifiability"]
    return grouped_maxent.GroupPenalty(
        name=spec["id"],
        indices=indices,
        strength=strength,
        scale_by_sqrt_size=bool(spec["l2_group_scaled_by_sqrt_size"]),
        matrix_shape=tuple(map(int, spec["matrix_shape"])),
        center_last_axis=bool(
            identifiability.get(
                "sum_over_pitch_classes_zero_per_mode",
                False,
            )
        ),
    )


def _feature_payload(
    feature: k3.FeatureSpec,
    weight: float,
) -> dict[str, Any]:
    return {
        "feature": feature.to_dict(),
        "weight": float(weight),
        "sign": "preference" if weight > 0 else "avoidance",
    }


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V23 — basse métrique et harmonie nommée",
        "",
        "Les deux groupes sont appris conjointement avec tous les paramètres V22,",
        "mais évalués aussi séparément. Les poids de basse sont centrés par mode ;",
        "les poids d'accord utilisent comme référence l'absence d'une analyse",
        "nommée unique.",
        "",
        "## Ablations sur le découpage de structure",
        "",
    ]
    for variant_id, variant in result["variants"].items():
        selection = variant["selection"]
        lines.extend(
            [
                f"### `{variant_id}`",
                "",
                "| Candidat | λ | NLL validation/pièce | Gain apparié | "
                "IC bootstrap 95 % | Pièces améliorées |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for index, point in enumerate(variant["path"]):
            marker = " **← retenu**" if index == selection["selected_index"] else ""
            if index == 0:
                gain = interval = pieces = "—"
                penalty = "absent"
            else:
                paired = point["paired_vs_baseline"]
                low, high = paired["bootstrap_95_interval"]
                gain = f"{paired['mean_improvement']:+.6f}"
                interval = f"[{low:+.6f}, {high:+.6f}]"
                pieces = (
                    f"{paired['positive_piece_count']}/"
                    f"{len(paired['piece_ids'])}"
                )
                penalty = f"{point['group_penalty']:.6g}"
            lines.append(
                f"| {point['label']} | {penalty} | "
                f"{point['validation_piece_mean_nll']:.6f} | {gain} | "
                f"{interval} | {pieces} |{marker}"
            )
        lines.extend(
            [
                "",
                f"- Sélection : `{selection['selected_label']}`.",
                f"- Variante retenue sur ce découpage : "
                f"`{str(selection['groups_retained']).lower()}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Portée de la décision",
            "",
            "Ce résultat ne suffit pas encore à adopter V23. Les pénalités et",
            "variantes candidates retenues ici doivent être gelées puis répétées",
            "dans des plis de chorals disjoints avant le réajustement complet.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN":
        raise ValueError("V23 configuration must be frozen before fitting")
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
        groups=config["groups"],
    )
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in features]:
        raise ValueError("V23 cache and frozen feature order disagree")
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    all_indices = np.arange(len(features), dtype=np.int64)
    train_all = _split(archive, "train", all_indices)
    validation_all = _split(archive, "validation", all_indices)
    baseline_count = (
        len(baseline["selected_model"]["baseline_rules"])
        + len(baseline["selected_group"]["weights"])
    )
    group_ranges: dict[str, np.ndarray] = {}
    cursor = baseline_count
    for group in config["groups"]:
        size = int(group["size"])
        group_ranges[group["id"]] = np.arange(cursor, cursor + size)
        cursor += size
    if cursor != len(features):
        raise ValueError("V23 group ranges do not cover selected features")

    baseline_indices = np.arange(baseline_count)
    train_baseline = _split(archive, "train", baseline_indices)
    validation_baseline = _split(archive, "validation", baseline_indices)
    initial = _initial_v22(baseline, features, baseline_count)
    estimation = config["estimation"]
    baseline_l1 = (
        float(estimation["l1_baseline_by_clause_complexity"])
        * np.asarray(
            [feature.complexity for feature in features[:baseline_count]],
            dtype=np.float64,
        )
    )
    prefit, _ = grouped_maxent.fit_grouped(
        train_baseline,
        validation_baseline,
        candidates,
        initial,
        steps=int(estimation["steps_baseline_refit"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=True,
    )
    baseline_parameters, baseline_fit = grouped_maxent.fit_grouped(
        train_baseline,
        validation_baseline,
        candidates,
        prefit,
        steps=int(estimation["steps_per_group_penalty"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=True,
    )
    baseline_point = _point(
        label="socle V22 réajusté",
        penalty=None,
        train=train_baseline,
        validation=validation_baseline,
        candidates=candidates,
        parameters=baseline_parameters,
        group_indices={},
        fit=baseline_fit,
    )

    variants = {
        "bass_only": (config["groups"][0],),
        "harmony_only": (config["groups"][1],),
        "both_groups": tuple(config["groups"]),
    }
    result_variants: dict[str, Any] = {}
    for variant_offset, (variant_id, active_specs) in enumerate(
        variants.items(),
        start=1,
    ):
        selected_indices = [
            *range(baseline_count),
            *(
                int(index)
                for spec in active_specs
                for index in group_ranges[spec["id"]]
            ),
        ]
        selected_array = np.asarray(selected_indices, dtype=np.int64)
        train = _split(archive, "train", selected_array)
        validation = _split(archive, "validation", selected_array)
        local_group_indices: dict[str, np.ndarray] = {}
        local_cursor = baseline_count
        for spec in active_specs:
            size = int(spec["size"])
            local_group_indices[spec["id"]] = np.arange(
                local_cursor,
                local_cursor + size,
            )
            local_cursor += size
        initial_full = exact.Parameters(
            prefit.register.copy(),
            prefit.tonal.copy(),
            np.concatenate(
                (
                    prefit.factor_weights,
                    np.zeros(local_cursor - baseline_count),
                )
            ),
        )
        l1 = np.concatenate(
            (
                baseline_l1,
                *(
                    np.full(
                        int(spec["size"]),
                        float(spec.get("l1_inside_group", 0.0)),
                    )
                    for spec in active_specs
                ),
            )
        )
        path = [{**baseline_point, "_parameters": baseline_parameters.copy()}]
        for penalty_offset, penalty in enumerate(
            map(float, estimation["group_penalty_path"]),
            start=1,
        ):
            penalties = tuple(
                _group_penalty(
                    spec,
                    local_group_indices[spec["id"]],
                    penalty,
                )
                for spec in active_specs
            )
            parameters, fit = grouped_maxent.fit_grouped(
                train,
                validation,
                candidates,
                initial_full,
                steps=int(estimation["steps_per_group_penalty"]),
                learning_rate=float(estimation["learning_rate"]),
                l1=l1,
                l2=float(estimation["l2"]),
                groups=penalties,
                return_best_validation=True,
            )
            point = _point(
                label=f"{variant_id} λ={penalty:g}",
                penalty=penalty,
                train=train,
                validation=validation,
                candidates=candidates,
                parameters=parameters,
                group_indices=local_group_indices,
                fit=fit,
            )
            point["paired_vs_baseline"] = paired_improvement(
                baseline_point["validation_piece_nll"],
                point["validation_piece_nll"],
                seed=(
                    int(config["selection"]["paired_bootstrap_seed"])
                    + variant_offset * 100
                    + penalty_offset
                ),
                resamples=int(
                    config["selection"]["paired_bootstrap_resamples"]
                ),
            )
            path.append(point)
            print(
                f"[v23] {variant_id} lambda={penalty:g} "
                f"validation={point['validation_piece_mean_nll']:.6f} "
                f"gain={point['paired_vs_baseline']['mean_improvement']:+.6f}",
                flush=True,
            )
        selected_index, threshold, best_index = select_from_protocol(
            path,
            config["selection"],
        )
        selected_parameters = path[selected_index]["_parameters"]
        selected_group_payload = {}
        for spec in active_specs:
            indices = local_group_indices[spec["id"]]
            group_weights = (
                selected_parameters.factor_weights[indices]
                if selected_index
                else np.zeros(indices.size, dtype=np.float64)
            )
            selected_group_payload[spec["id"]] = {
                "feature_kind": spec["feature_kind"],
                "matrix_shape": spec["matrix_shape"],
                "weights": [
                    _feature_payload(feature, weight)
                    for feature, weight in zip(
                        (
                            features[index]
                            for index in group_ranges[spec["id"]]
                        ),
                        group_weights,
                        strict=True,
                    )
                ],
            }
        for point in path:
            point.pop("_parameters", None)
        result_variants[variant_id] = {
            "active_group_ids": [spec["id"] for spec in active_specs],
            "path": path,
            "selection": {
                "criterion": config["selection"]["criterion"],
                "selected_index": selected_index,
                "best_index": best_index,
                "threshold": threshold,
                "selected_label": path[selected_index]["label"],
                "best_label": path[best_index]["label"],
                "groups_retained": selected_index != 0,
                "selected_penalty": (
                    None
                    if selected_index == 0
                    else path[selected_index]["group_penalty"]
                ),
            },
            "selected_model": {
                "register_logits": selected_parameters.register.tolist(),
                "tonal_logits": selected_parameters.tonal.tolist(),
                "baseline_rules": [
                    _feature_payload(feature, weight)
                    for feature, weight in zip(
                        features[:baseline_count],
                        selected_parameters.factor_weights[:baseline_count],
                        strict=True,
                    )
                ],
                "groups": selected_group_payload,
            },
        }
        print(
            f"[v23] {variant_id} selected={path[selected_index]['label']}",
            flush=True,
        )

    for point_key in (
        "validation_piece_nll",
        "fit",
        "_parameters",
    ):
        baseline_point.pop(point_key, None)
    result = {
        "experiment": {
            "id": config["id"],
            "status": "STRUCTURE_SPLIT_ONLY",
            "config": str(args.config.resolve()),
            "cache": str(args.cache.resolve()),
            "baseline_feature_count": baseline_count,
            "added_feature_count": len(features) - baseline_count,
            "train_piece_count": int(
                np.unique(train_all["piece_ids"]).size
            ),
            "validation_piece_count": int(
                np.unique(validation_all["piece_ids"]).size
            ),
            "test_loaded": False,
        },
        "baseline": baseline_point,
        "variants": result_variants,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v23] wrote {args.output}", flush=True)
    print(f"[v23] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
