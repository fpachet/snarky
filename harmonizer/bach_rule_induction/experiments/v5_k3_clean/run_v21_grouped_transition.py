#!/usr/bin/env python3
"""Fit V20C root transitions as one identifiable sparse MaxEnt group."""

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

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v21_grouped_transition_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v21_grouped_transition_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V21_GROUPED_TRANSITION_MODEL.md"


def select_one_standard_error(
    candidates: list[dict[str, Any]],
) -> tuple[int, float, int]:
    """Choose the strongest penalty, including the no-group baseline."""

    best_index = min(
        range(len(candidates)),
        key=lambda index: candidates[index]["validation_piece_mean_nll"],
    )
    best = candidates[best_index]
    threshold = (
        best["validation_piece_mean_nll"]
        + best["validation_piece_standard_error"]
    )
    selected_index = next(
        index
        for index, candidate in enumerate(candidates)
        if candidate["validation_piece_mean_nll"] <= threshold
    )
    return selected_index, threshold, best_index


def select_from_protocol(
    candidates: list[dict[str, Any]],
    selection: dict[str, Any],
) -> tuple[int, float | None, int]:
    criterion = str(selection["criterion"])
    if criterion == "strongest_group_penalty_within_one_validation_standard_error":
        return select_one_standard_error(candidates)
    if "paired" not in criterion:
        return select_one_standard_error(candidates)
    best_index = min(
        range(len(candidates)),
        key=lambda index: candidates[index]["validation_piece_mean_nll"],
    )
    minimum_fraction = float(
        selection.get("minimum_positive_piece_fraction", 0.6)
    )
    selected_index = 0
    for index, candidate in enumerate(candidates[1:], start=1):
        paired = candidate["paired_vs_baseline"]
        positive_fraction = (
            paired["positive_piece_count"] / len(paired["piece_ids"])
        )
        if (
            paired["bootstrap_95_interval"][0] > 0
            and positive_fraction >= minimum_fraction
        ):
            selected_index = index
            break
    return selected_index, None, best_index


def paired_improvement(
    baseline: dict[str, float],
    candidate: dict[str, float],
    *,
    seed: int,
    resamples: int,
) -> dict[str, Any]:
    """Compare two models on the same held-out pieces."""

    piece_ids = sorted(baseline)
    if piece_ids != sorted(candidate):
        raise ValueError("Paired comparisons require identical held-out pieces")
    differences = np.asarray(
        [baseline[piece_id] - candidate[piece_id] for piece_id in piece_ids],
        dtype=np.float64,
    )
    standard_error = (
        0.0
        if differences.size < 2
        else float(
            differences.std(ddof=1) / np.sqrt(differences.size)
        )
    )
    rng = np.random.default_rng(seed)
    bootstrap = differences[
        rng.integers(
            0,
            differences.size,
            size=(resamples, differences.size),
        )
    ].mean(axis=1)
    interval = np.quantile(bootstrap, [0.025, 0.975])
    return {
        "piece_ids": piece_ids,
        "differences_baseline_minus_candidate": differences.tolist(),
        "mean_improvement": float(differences.mean()),
        "standard_error": standard_error,
        "positive_piece_count": int((differences > 0).sum()),
        "negative_piece_count": int((differences < 0).sum()),
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "bootstrap_95_interval": list(map(float, interval)),
        "bootstrap_probability_nonpositive": float(
            (bootstrap <= 0).mean()
        ),
    }


def _split(
    archive: Any,
    name: str,
    indices: np.ndarray,
) -> dict[str, np.ndarray]:
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
    group_penalty: float | None,
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    candidates: np.ndarray,
    parameters: exact.Parameters,
    group_indices: np.ndarray,
    group_name: str,
    fit: dict[str, Any],
) -> dict[str, Any]:
    train_mean, train_se, _ = sparse._piece_nll(train, candidates, parameters)
    validation_mean, validation_se, validation_pieces = sparse._piece_nll(
        validation,
        candidates,
        parameters,
    )
    group_weights = parameters.factor_weights[group_indices]
    terminal = fit["history"][-1]
    terminal_group_norm = (
        0.0
        if not group_indices.size
        else float(
            terminal["group_norms"].get(
                group_name,
                0.0,
            )
        )
    )
    return {
        "label": label,
        "group_penalty": group_penalty,
        "train_piece_mean_nll": train_mean,
        "train_piece_standard_error": train_se,
        "validation_piece_mean_nll": validation_mean,
        "validation_piece_standard_error": validation_se,
        "validation_piece_nll": validation_pieces,
        "group_norm": float(np.linalg.norm(group_weights)),
        "group_max_abs_weight": float(np.max(np.abs(group_weights), initial=0.0)),
        "active_group_cells_at_0_05": int(
            (np.abs(group_weights) >= 0.05).sum()
        ),
        "terminal_validation_decision_nll": float(
            terminal["validation_nll"]
        ),
        "terminal_train_decision_nll": float(terminal["train_nll"]),
        "terminal_group_norm": terminal_group_norm,
        "group_weights": group_weights.tolist(),
        "fit": fit,
        "_parameters": parameters,
    }


ROOT_MOTION_NAMES = (
    "maintien",
    "seconde mineure ascendante",
    "seconde majeure ascendante",
    "tierce mineure ascendante",
    "tierce majeure ascendante",
    "quarte ascendante / quinte descendante",
    "triton",
    "quinte ascendante / quarte descendante",
    "tierce majeure descendante",
    "tierce mineure descendante",
    "seconde majeure descendante",
    "seconde mineure descendante",
)


def _group_payload(
    features: list[k3.FeatureSpec],
    weights: np.ndarray,
) -> list[dict[str, Any]]:
    rows = []
    for feature, weight in zip(features, weights, strict=True):
        row = {
            "mode": "major" if feature.second_value == 0 else "minor",
            "weight": float(weight),
        }
        if feature.kind == "central_named_root_transition_mode":
            previous, current = divmod(int(feature.value), 12)
            row.update(
                {
                    "case": f"{previous} → {current}",
                    "previous_root_degree": previous,
                    "current_root_degree": current,
                }
            )
        elif feature.kind == "central_named_root_motion_mode":
            motion = int(feature.value)
            row.update(
                {
                    "case": ROOT_MOTION_NAMES[motion],
                    "root_motion_class": motion,
                }
            )
        else:
            raise ValueError(f"Unsupported grouped feature: {feature.kind}")
        rows.append(row)
    return rows


def _markdown(result: dict[str, Any]) -> str:
    selection = result["selection"]
    experiment = result["experiment"]
    lines = [
        f"# {experiment['id']} — apprentissage conjoint d'un RuleGroup",
        "",
        f"Les {experiment['group_cell_count']} cellules du groupe",
        f"`{experiment['group_id']}` sont apprises simultanément plutôt que",
        "mises en concurrence comme des règles indépendantes. La projection",
        "d'identifiabilité est appliquée après chaque pas proximal.",
        "",
        "## Trajectoire de régularisation",
        "",
        "| Candidat | λ groupe | NLL validation/pièce | e.s. | "
        "norme retenue | norme terminale | cellules |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for index, point in enumerate(result["path"]):
        marker = " **← retenu**" if index == selection["selected_index"] else ""
        penalty = "groupe absent" if point["group_penalty"] is None else (
            f"{point['group_penalty']:.6g}"
        )
        lines.append(
            f"| {point['label']} | {penalty} | "
            f"{point['validation_piece_mean_nll']:.6f} | "
            f"{point['validation_piece_standard_error']:.6f} | "
            f"{point['group_norm']:.6f} | "
            f"{point['terminal_group_norm']:.6f} | "
            f"{point['active_group_cells_at_0_05']} |{marker}"
        )
    lines.extend(
        [
            "",
            "## Comparaisons appariées au socle",
            "",
            "| Candidat | Gain moyen | e.s. appariée | "
            "IC bootstrap 95 % | Pièces améliorées |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for point in result["path"][1:]:
        paired = point["paired_vs_baseline"]
        low, high = paired["bootstrap_95_interval"]
        lines.append(
            f"| {point['label']} | {paired['mean_improvement']:+.6f} | "
            f"{paired['standard_error']:.6f} | "
            f"[{low:+.6f}, {high:+.6f}] | "
            f"{paired['positive_piece_count']}/"
            f"{len(paired['piece_ids'])} |"
        )
    lines.extend(
        [
            "",
            "## Décision",
            "",
            f"- Meilleur candidat brut : `{selection['best_label']}`.",
            (
                "- Seuil à une erreur standard : "
                f"`{selection['threshold']:.6f}`."
                if selection["threshold"] is not None
                else "- Sélection : IC bootstrap apparié strictement positif."
            ),
            f"- Candidat retenu : `{selection['selected_label']}`.",
            f"- Groupe retenu : `{str(selection['group_retained']).lower()}`.",
            "",
        ]
    )
    if selection["group_retained"]:
        lines.extend(
            [
                "Le groupe apporte collectivement assez d'information pour",
                "survivre au critère à une erreur standard. Les coefficients",
                "extrêmes ci-dessous restent des cellules d'une même règle",
                "structurée, et non 288 règles autonomes.",
                "",
                "### Interactions positives les plus fortes",
                "",
                "| Mode | Cas partagé | Poids |",
                "|---|---:|---:|",
            ]
        )
        for row in result["selected_group"]["top_positive"]:
            lines.append(
                f"| {row['mode']} | {row['case']} | "
                f"{row['weight']:+.6f} |"
            )
        lines.extend(
            [
                "",
                "### Interactions négatives les plus fortes",
                "",
                "| Mode | Cas partagé | Poids |",
                "|---|---:|---:|",
            ]
        )
        for row in result["selected_group"]["top_negative"]:
            lines.append(
                f"| {row['mode']} | {row['case']} | "
                f"{row['weight']:+.6f} |"
            )
    else:
        lines.extend(
            [
                "Le modèle sans table de transitions reste dans l'intervalle",
                "à une erreur standard du meilleur candidat. La sélection",
                "groupée rejette donc la famille entière ; elle ne transforme",
                "pas artificiellement les grands marginaux en règles.",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN":
        raise ValueError("V21 configuration must be frozen before fitting")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    grammar = exact._load_grammar(
        (FACTOR_BASE / config["source_grammar"]).resolve()
    )
    catalogue = sparse._load_catalogue(source, grammar, args.context)
    key_to_index = {feature.key: index for index, feature in enumerate(catalogue)}
    baseline_model = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    baseline_features = [
        k3.feature_from_model_record(rule)
        for rule in baseline_model["model"]["rules"]
    ]
    baseline_indices = [key_to_index[feature.key] for feature in baseline_features]
    transition_pairs = sorted(
        (
            (index, feature)
            for index, feature in enumerate(catalogue)
            if feature.kind == config["group"]["feature_kind"]
        ),
        key=lambda pair: (pair[1].second_value, pair[1].value),
    )
    transition_catalogue_indices = [index for index, _ in transition_pairs]
    transition_features = [feature for _, feature in transition_pairs]
    expected_size = int(config["group"]["size"])
    if len(transition_features) != expected_size:
        raise ValueError("Frozen V21 transition group has the wrong size")
    selected_catalogue_indices = np.asarray(
        [*baseline_indices, *transition_catalogue_indices],
        dtype=np.int64,
    )
    cache = args.cache or (
        FACTOR_BASE / config["source_exact_cache"]
    ).resolve()
    archive = np.load(cache)
    metadata = json.loads(str(archive["metadata"]))
    full_catalogue_keys = [feature.key for feature in catalogue]
    selected_feature_keys = [
        catalogue[index].key for index in selected_catalogue_indices
    ]
    if metadata["feature_keys"] == full_catalogue_keys:
        cache_indices = selected_catalogue_indices
    elif metadata["feature_keys"] == selected_feature_keys:
        cache_indices = np.arange(
            selected_catalogue_indices.size,
            dtype=np.int64,
        )
    else:
        raise ValueError("V21 cache and frozen catalogue disagree")
    train = _split(archive, "train", cache_indices)
    validation = _split(archive, "validation", cache_indices)
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    baseline_count = len(baseline_features)
    group_indices = np.arange(
        baseline_count,
        baseline_count + expected_size,
        dtype=np.int64,
    )
    baseline_initial = exact.Parameters(
        register=np.asarray(
            baseline_model["model"]["register_logits"],
            dtype=np.float64,
        ),
        tonal=np.asarray(
            baseline_model["model"]["tonal_logits"],
            dtype=np.float64,
        ),
        factor_weights=np.asarray(
            [rule["weight"] for rule in baseline_model["model"]["rules"]],
            dtype=np.float64,
        ),
    )
    estimation = config["estimation"]
    baseline_train = {
        **train,
        "factors": train["factors"][:, :, :baseline_count],
    }
    baseline_validation = {
        **validation,
        "factors": validation["factors"][:, :, :baseline_count],
    }
    baseline_complexities = np.asarray(
        [feature.complexity for feature in baseline_features],
        dtype=np.float64,
    )
    baseline_parameters, baseline_fit = grouped_maxent.fit_grouped(
        baseline_train,
        baseline_validation,
        candidates,
        baseline_initial,
        steps=int(estimation["steps_baseline_refit"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=(
            float(estimation["l1_baseline_by_clause_complexity"])
            * baseline_complexities
        ),
        l2=float(estimation["l2"]),
        groups=(),
        return_best_validation=(
            estimation.get("return_checkpoint", "best_validation")
            == "best_validation"
        ),
    )
    baseline_full_parameters = exact.Parameters(
        baseline_parameters.register.copy(),
        baseline_parameters.tonal.copy(),
        np.concatenate(
            (
                baseline_parameters.factor_weights,
                np.zeros(expected_size, dtype=np.float64),
            )
        ),
    )
    path = [
        _point(
            label="socle V20B réajusté",
            group_penalty=None,
            train=baseline_train,
            validation=baseline_validation,
            candidates=candidates,
            parameters=baseline_parameters,
            group_indices=np.empty(0, dtype=np.int64),
            group_name=config["group"]["id"],
            fit=baseline_fit,
        )
    ]
    full_l1 = np.concatenate(
        (
            float(estimation["l1_baseline_by_clause_complexity"])
            * baseline_complexities,
            np.full(
                expected_size,
                float(config["group"].get("l1_inside_group", 0.0)),
                dtype=np.float64,
            ),
        )
    )
    matrix_shape = tuple(map(int, config["group"]["matrix_shape"]))
    identifiability = config["group"]["identifiability"]
    for penalty in map(float, estimation["group_penalty_path"]):
        group = grouped_maxent.GroupPenalty(
            name=config["group"]["id"],
            indices=group_indices,
            strength=penalty,
            scale_by_sqrt_size=bool(
                config["group"]["l2_group_scaled_by_sqrt_size"]
            ),
            matrix_shape=matrix_shape,
            double_center_last_two_axes=bool(
                identifiability.get("row_sums_zero", False)
                and identifiability.get("column_sums_zero", False)
            ),
            center_last_axis=bool(
                identifiability.get(
                    "sum_over_motion_classes_zero_per_mode",
                    False,
                )
            ),
        )
        parameters, fit = grouped_maxent.fit_grouped(
            train,
            validation,
            candidates,
            baseline_full_parameters,
            steps=int(estimation["steps_per_group_penalty"]),
            learning_rate=float(estimation["learning_rate"]),
            l1=full_l1,
            l2=float(estimation["l2"]),
            groups=(group,),
            return_best_validation=(
                estimation.get("return_checkpoint", "best_validation")
                == "best_validation"
            ),
        )
        point = _point(
            label=f"groupe λ={penalty:g}",
            group_penalty=penalty,
            train=train,
            validation=validation,
            candidates=candidates,
            parameters=parameters,
            group_indices=group_indices,
            group_name=config["group"]["id"],
            fit=fit,
        )
        path.append(point)
        print(
            f"[v21] lambda={penalty:g} "
            f"validation={point['validation_piece_mean_nll']:.6f} "
            f"norm={point['group_norm']:.6f}",
            flush=True,
        )
    bootstrap_resamples = int(
        config["selection"].get("paired_bootstrap_resamples", 100_000)
    )
    bootstrap_seed = int(
        config["selection"].get("paired_bootstrap_seed", 21_029)
    )
    baseline_piece_nll = path[0]["validation_piece_nll"]
    for index, point in enumerate(path[1:], start=1):
        point["paired_vs_baseline"] = paired_improvement(
            baseline_piece_nll,
            point["validation_piece_nll"],
            seed=bootstrap_seed + index,
            resamples=bootstrap_resamples,
        )
    selected_index, threshold, best_index = select_from_protocol(
        path,
        config["selection"],
    )
    selected = path[selected_index]
    best_parameters = path[best_index]["_parameters"]
    selected_parameters = selected.pop("_parameters")
    for point in path:
        point.pop("_parameters", None)
    transition_rows = _group_payload(
        transition_features,
        selected_parameters.factor_weights[group_indices]
        if selected_index
        else np.zeros(expected_size),
    )
    top_positive = sorted(
        transition_rows,
        key=lambda row: row["weight"],
        reverse=True,
    )[:12]
    top_negative = sorted(transition_rows, key=lambda row: row["weight"])[:12]
    best_transition_rows = _group_payload(
        transition_features,
        best_parameters.factor_weights[group_indices]
        if best_index
        else np.zeros(expected_size),
    )
    result = {
        "experiment": {
            "id": config["id"],
            "status": "STRUCTURE_SPLIT_ONLY",
            "config": str(args.config.resolve()),
            "cache": str(cache),
            "baseline_rule_count": baseline_count,
            "group_cell_count": expected_size,
            "group_id": config["group"]["id"],
            "group_feature_kind": config["group"]["feature_kind"],
            "train_piece_count": int(np.unique(train["piece_ids"]).size),
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
        },
        "selected_model": {
            "register_logits": selected_parameters.register.tolist(),
            "tonal_logits": selected_parameters.tonal.tolist(),
            "baseline_rules": [
                {
                    "feature": feature.to_dict(),
                    "weight": float(weight),
                }
                for feature, weight in zip(
                    baseline_features,
                    selected_parameters.factor_weights[:baseline_count],
                    strict=True,
                )
            ],
        },
        "selected_group": {
            "id": config["group"]["id"],
            "matrix_shape": list(matrix_shape),
            "weights": transition_rows,
            "top_positive": top_positive,
            "top_negative": top_negative,
        },
        "best_group": {
            "path_index": best_index,
            "label": path[best_index]["label"],
            "matrix_shape": list(matrix_shape),
            "weights": best_transition_rows,
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v21] selected={path[selected_index]['label']} "
        f"group_retained={selected_index != 0}",
        flush=True,
    )
    print(f"[v21] wrote {args.output}", flush=True)
    print(f"[v21] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
