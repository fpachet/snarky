#!/usr/bin/env python3
"""Learn a sparse, readable K3 rule base by exact pseudolikelihood."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_generative_moment_calibration as generative
import run_v6_factor_induction as v6
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v18_explanatory_sparse_config.yaml"
DEFAULT_SOURCE = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_CACHE = HERE / "work/k3-exact-catalogue-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v18_explanatory_sparse_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V18_EXPLANATORY_SPARSE_MODEL.md"

VOICE_NAMES = ("soprano", "alto", "ténor", "basse")
INTERVAL_NAMES = {
    0: "unisson ou octave modulo l’octave",
    1: "seconde mineure modulo l’octave",
    2: "seconde majeure modulo l’octave",
    3: "tierce mineure modulo l’octave",
    4: "tierce majeure modulo l’octave",
    5: "quarte juste modulo l’octave",
    6: "triton",
    7: "quinte juste modulo l’octave",
    8: "sixte mineure modulo l’octave",
    9: "sixte majeure modulo l’octave",
    10: "septième mineure modulo l’octave",
    11: "septième majeure modulo l’octave",
}
CHORD_QUALITY_NAMES = (
    "triade majeure",
    "triade mineure",
    "triade diminuée",
    "triade augmentée",
    "septième de dominante",
    "septième majeure",
    "septième mineure",
    "septième demi-diminuée",
    "septième diminuée",
    "septième mineure-majeure",
)
INVERSION_NAMES = (
    "à l’état fondamental",
    "au premier renversement",
    "au deuxième renversement",
    "au troisième renversement",
)


def _voice(index: int) -> str:
    return "toutes voix" if index == -1 else VOICE_NAMES[index]


def _human_clause(feature: k3.FeatureSpec) -> str:
    """Render a numeric predicate as a compact, inspectable French clause."""

    voice = _voice(feature.target_voice)
    other = (
        ""
        if feature.other_voice is None
        else VOICE_NAMES[feature.other_voice]
    )
    value = feature.value
    if feature.kind == "any_voice_adjacent_step_gt":
        return f"{voice} : mouvement mélodique supérieur à {value} demi-tons"
    if feature.kind in {"abs_step_from_previous_gt", "abs_step_to_next_gt"}:
        direction = (
            "depuis la note précédente"
            if feature.kind.endswith("previous_gt")
            else "vers la note suivante"
        )
        return f"{voice} : mouvement {direction} supérieur à {value} demi-tons"
    if feature.kind in {
        "any_voice_adjacent_abs_class",
        "abs_class_from_previous",
        "abs_class_to_next",
    }:
        relation = {
            "any_voice_adjacent_abs_class": "mouvement adjacent",
            "abs_class_from_previous": "intervalle depuis la note précédente",
            "abs_class_to_next": "intervalle vers la note suivante",
        }[feature.kind]
        return f"{voice} : {relation} de classe {value} ({INTERVAL_NAMES[value]})"
    if feature.kind in {
        "any_pair_central_abs_class",
        "central_pair_abs_class",
    }:
        subject = (
            "au moins une paire de voix"
            if feature.target_voice == -1
            else f"{voice} avec {other}"
        )
        return (
            f"{subject} : intervalle vertical de classe {value} "
            f"({INTERVAL_NAMES[value]})"
        )
    if feature.kind in {
        "any_pair_abs_class_preserved_same_sign",
        "pair_abs_class_preserved_same_sign",
    }:
        subject = (
            "au moins une paire de voix"
            if feature.target_voice == -1
            else f"{voice} avec {other}"
        )
        return (
            f"{subject} : conserve l’intervalle de classe {value} "
            "par mouvement direct non nul"
        )
    if feature.kind in {
        "any_pair_arrival_abs_class_same_sign",
        "pair_arrival_abs_class_same_sign",
    }:
        subject = (
            "au moins une paire de voix"
            if feature.target_voice == -1
            else f"{voice} avec {other}"
        )
        return (
            f"{subject} : arrive par mouvement direct sur la classe "
            f"d’intervalle {value}"
        )
    if feature.kind in {
        "any_adjacent_central_ordered_gap_le",
        "central_ordered_gap_le",
        "previous_ordered_gap_le",
    }:
        subject = (
            "au moins deux voix adjacentes"
            if feature.target_voice == -1
            else f"{voice} et {other}"
        )
        position = (
            "au bloc précédent"
            if feature.kind == "previous_ordered_gap_le"
            else "au bloc central"
        )
        return f"{subject} : écart ordonné ≤ {value} demi-tons {position}"
    if feature.kind in {
        "any_voice_three_block_sign_shape",
        "three_block_sign_shape",
    }:
        return (
            f"{voice} : directions successives "
            f"({feature.value:+d}, {feature.second_value:+d})"
        )
    if feature.kind == "attacked_repeat_from_previous":
        return f"{voice} : répète par une nouvelle attaque la note précédente"
    if feature.kind == "central_distinct_pc_count":
        return f"bloc central : {value} classes de hauteur distinctes"
    if feature.kind == "central_distinct_pc_count_metric":
        return (
            f"bloc central : {value} classes distinctes au niveau métrique "
            f"{feature.second_value}"
        )
    if feature.kind == "central_triadic_metric":
        strength = "fort" if feature.second_value else "faible"
        return (
            "bloc central : triade majeure ou mineure complète "
            f"sur temps {strength}"
        )
    if feature.kind == "central_named_chord_quality":
        return f"bloc central : {CHORD_QUALITY_NAMES[value]} complète"
    if feature.kind == "central_named_chord_root_degree":
        return (
            "bloc central : fondamentale à "
            f"{value} demi-tons de la tonique déclarée"
        )
    if feature.kind == "central_named_chord_inversion":
        return f"bloc central : accord complet {INVERSION_NAMES[value]}"
    if feature.kind == "central_named_chord_quality_metric":
        strength = "fort" if feature.second_value else "faible"
        return (
            f"bloc central : {CHORD_QUALITY_NAMES[value]} complète "
            f"sur temps {strength}"
        )
    if feature.kind == "central_named_chord_root_degree_metric":
        strength = "fort" if feature.second_value else "faible"
        return (
            "bloc central : fondamentale à "
            f"{value} demi-tons de la tonique sur temps {strength}"
        )
    if feature.kind == "central_named_chord_degree_quality":
        return (
            f"bloc central : {CHORD_QUALITY_NAMES[feature.second_value]} "
            f"sur fondamentale à {value} demi-tons de la tonique"
        )
    if feature.kind == "central_named_chord_quality_inversion":
        return (
            f"bloc central : {CHORD_QUALITY_NAMES[value]} "
            f"{INVERSION_NAMES[feature.second_value]}"
        )
    if feature.kind == "central_named_root_transition_mode":
        previous_degree, current_degree = divmod(value, 12)
        mode = "majeur" if feature.second_value == 0 else "mineur"
        return (
            f"en mode {mode} : fondamentale à {previous_degree} demi-tons "
            f"→ fondamentale à {current_degree} demi-tons de la tonique"
        )
    return feature.label


def _load_catalogue(
    source: dict[str, Any],
    grammar: dict[str, Any],
    context_path: Path,
) -> tuple[k3.FeatureSpec, ...]:
    split_payload = json.loads(
        (
            HERE.parent
            / "differentiable_rules_poc/results/splits.variant-safe.json"
        ).read_text(encoding="utf-8")
    )
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)
    context = k3.load_k3_dataset(context_path)
    context_train = k3.subset_for_piece_ids(context, train_ids).with_domain(
        int(source["corpus"]["candidate_min"]),
        int(source["corpus"]["candidate_max"]),
    )
    return v6._catalogue(context_train, grammar)


def _split_from_archive(
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


def _select(data: dict[str, np.ndarray], indices: list[int]) -> dict[str, np.ndarray]:
    return {
        **data,
        "factors": data["factors"][:, :, indices],
    }


def _piece_nll(
    data: dict[str, np.ndarray],
    candidates: np.ndarray,
    parameters: exact.Parameters,
) -> tuple[float, float, dict[str, float]]:
    probabilities = exact._probabilities(
        data["voices"],
        data["modes"],
        data["tonics"],
        candidates,
        data["factors"],
        parameters,
    )
    chosen_probability = probabilities[
        np.arange(data["chosen"].size),
        data["chosen"],
    ]
    losses = -np.log(np.maximum(chosen_probability, 1e-12))
    per_piece = {
        str(piece): float(losses[data["piece_ids"] == piece].mean())
        for piece in np.unique(data["piece_ids"])
    }
    values = np.asarray(list(per_piece.values()), dtype=np.float64)
    standard_error = (
        0.0
        if values.size < 2
        else float(values.std(ddof=1) / math.sqrt(values.size))
    )
    return float(values.mean()), standard_error, per_piece


def _fit_selected(
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    candidates: np.ndarray,
    initial: exact.Parameters,
    complexities: np.ndarray,
    config: dict[str, Any],
) -> tuple[exact.Parameters, dict[str, Any]]:
    estimation = config["estimation"]
    return exact._fit(
        train,
        validation,
        candidates,
        initial,
        steps=int(estimation["maximum_steps_per_refit"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=float(estimation["l1"]) * complexities,
        l2=float(estimation["l2"]),
    )


def _point(
    iteration: int,
    selected: list[int],
    parameters: exact.Parameters,
    fit: dict[str, Any],
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    candidates: np.ndarray,
    catalogue: tuple[k3.FeatureSpec, ...],
) -> dict[str, Any]:
    train_mean, train_se, _ = _piece_nll(train, candidates, parameters)
    validation_mean, validation_se, per_piece = _piece_nll(
        validation,
        candidates,
        parameters,
    )
    return {
        "iteration": iteration,
        "selected_rule_count": len(selected),
        "active_rule_count_at_0_05": int(
            (np.abs(parameters.factor_weights) >= 0.05).sum()
        ),
        "total_clause_complexity": int(
            sum(catalogue[index].complexity for index in selected)
        ),
        "train_piece_mean_nll": train_mean,
        "train_piece_standard_error": train_se,
        "validation_piece_mean_nll": validation_mean,
        "validation_piece_standard_error": validation_se,
        "validation_decision_mean_nll": exact._nll(
            validation["chosen"],
            validation["voices"],
            validation["modes"],
            validation["tonics"],
            candidates,
            validation["factors"],
            parameters,
        ),
        "validation_piece_nll": per_piece,
        "fit": fit,
    }


def _one_standard_error_index(frontier: list[dict[str, Any]]) -> tuple[int, float]:
    best_index = min(
        range(len(frontier)),
        key=lambda index: frontier[index]["validation_piece_mean_nll"],
    )
    best = frontier[best_index]
    threshold = (
        best["validation_piece_mean_nll"]
        + best["validation_piece_standard_error"]
    )
    chosen_index = next(
        index
        for index, point in enumerate(frontier)
        if point["validation_piece_mean_nll"] <= threshold
    )
    return chosen_index, threshold


def _rule_payload(
    feature: k3.FeatureSpec,
    weight: float,
    family: str,
    selection: exact.ExactResidual,
    index: int,
) -> dict[str, Any]:
    return {
        "id": f"F-K3-V18-{index:03d}",
        "family": family,
        "clause": _human_clause(feature),
        "feature": feature.to_dict(),
        "weight": float(weight),
        "polarity": "preference" if weight > 0 else "avoidance",
        "selection": asdict(selection),
        "origin": "learned_from_bach_corpus",
        "human_authored": False,
        "calls_other_rules": False,
    }


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    selection = result["selection"]
    model = result["model"]
    lines = [
        f"# {experiment['id']} — MaxEnt parcimonieux à règles lisibles",
        "",
        "L'expérience conserve la pseudo-vraisemblance exacte. Chaque colonne est un",
        "prédicat K3 autonome et lisible ; les poids sont réestimés conjointement",
        "après chaque ajout. Aucune statistique de génération n'intervient.",
        "",
        "## Protocole",
        "",
        f"- Catalogue exact initial : `{experiment['source_catalogue_size']}`.",
        f"- Candidats lisibles : `{experiment['readable_catalogue_size']}`.",
        "- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).",
        f"- Pièces structure train/validation : "
        f"`{experiment['train_piece_count']}/{experiment['validation_piece_count']}`.",
        "- Test réservé chargé : `false`.",
        "- Sélection finale : règle d'une erreur standard.",
        "",
        "## Frontière qualité–complexité",
        "",
        "| Règles | Complexité | NLL validation par pièce | Erreur standard |",
        "|---:|---:|---:|---:|",
    ]
    for point in result["frontier"]:
        marker = " **← retenu**" if point["iteration"] == selection["iteration"] else ""
        lines.append(
            f"| {point['selected_rule_count']} | "
            f"{point['total_clause_complexity']} | "
            f"{point['validation_piece_mean_nll']:.6f} | "
            f"{point['validation_piece_standard_error']:.6f} |{marker}"
        )
    lines.extend(
        [
            "",
            "## Base retenue",
            "",
            f"- Règles : `{len(model['rules'])}`.",
            f"- Complexité totale : `{selection['total_clause_complexity']}`.",
            f"- NLL validation par pièce : "
            f"`{selection['validation_piece_mean_nll']:.6f}`.",
            f"- Seuil d'une erreur standard : "
            f"`{selection['one_standard_error_threshold']:.6f}`.",
            "",
            "| # | Interprétation autonome | Poids | Modalité |",
            "|---:|---|---:|---|",
        ]
    )
    for index, rule in enumerate(model["rules"], start=1):
        lines.append(
            f"| {index} | {rule['clause']} | {rule['weight']:+.6f} | "
            f"{rule['polarity']} |"
        )
    lines.extend(
        [
            "",
            "Ces poids sont des estimations conjointes : la table ne prétend pas",
            "encore transformer une forte pénalité en interdiction absolue. La",
            "stabilité inter-échantillons et le test fermé restent requis avant",
            "une RuleCard scientifique finale.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN":
        raise ValueError("V18 configuration must be frozen before induction")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    grammar = exact._load_grammar(
        (FACTOR_BASE / config["source_grammar"]).resolve()
    )
    catalogue = _load_catalogue(source, grammar, args.context)
    family_by_kind = v6._feature_family_map(grammar)
    excluded = set(config["interpretability"]["excluded_families"])
    readable_indices = np.asarray(
        [
            index
            for index, feature in enumerate(catalogue)
            if family_by_kind[feature.kind] not in excluded
        ],
        dtype=np.int64,
    )
    readable = tuple(catalogue[index] for index in readable_indices)

    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    if metadata["feature_keys"] != [feature.key for feature in catalogue]:
        raise ValueError("V18 cache and frozen catalogue disagree")
    train = _split_from_archive(archive, "train", readable_indices)
    validation = _split_from_archive(archive, "validation", readable_indices)
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    register = np.asarray(source["model"]["register_logits"], dtype=np.float64)
    tonal = np.asarray(source["model"]["tonal_logits"], dtype=np.float64)
    empty_train = _select(train, [])
    empty_validation = _select(validation, [])
    parameters, baseline_fit = _fit_selected(
        empty_train,
        empty_validation,
        candidates,
        exact.Parameters(register, tonal, np.empty(0, dtype=np.float64)),
        np.empty(0, dtype=np.float64),
        config,
    )
    frontier_parameters = [parameters.copy()]
    frontier = [
        _point(
            0,
            [],
            parameters,
            baseline_fit,
            empty_train,
            empty_validation,
            candidates,
            readable,
        )
    ]
    selected: list[int] = []
    selections: list[exact.ExactResidual] = []
    maximum = int(config["interpretability"]["maximum_selected_rules"])
    minimum_testable = int(
        config["interpretability"]["minimum_testable_opportunities"]
    )
    minimum_piece_support = int(
        config["interpretability"]["minimum_piece_support"]
    )
    complexity_penalty = float(config["selection"]["description_penalty"])
    complexities = np.asarray(
        [feature.complexity for feature in readable],
        dtype=np.float64,
    )
    stopping = config["selection"]["stopping"]
    patience = int(stopping["consecutive_validation_non_improvements"])
    required_gain = float(stopping["minimum_validation_nll_improvement"])
    best_validation = frontier[0]["validation_piece_mean_nll"]
    non_improvements = 0

    for iteration in range(1, maximum + 1):
        selected_train = _select(train, selected)
        probabilities = exact._probabilities(
            selected_train["voices"],
            selected_train["modes"],
            selected_train["tonics"],
            candidates,
            selected_train["factors"],
            parameters,
        )
        residuals = exact._residuals(
            train["chosen"],
            probabilities,
            train["factors"],
            train["piece_ids"],
            complexities,
            complexity_penalty=complexity_penalty,
        )
        ranked = [
            (statistic.column_score, index, statistic)
            for index, statistic in enumerate(residuals)
            if index not in selected
            and statistic is not None
            and statistic.column_score > 0
            and statistic.testable_opportunities >= minimum_testable
            and statistic.piece_support >= minimum_piece_support
        ]
        if not ranked:
            print("[v18] no admissible readable residual", flush=True)
            break
        _, chosen_index, statistic = max(
            ranked,
            key=lambda item: (item[0], readable[item[1]].key),
        )
        selected.append(chosen_index)
        selections.append(statistic)
        parameters.factor_weights = np.append(parameters.factor_weights, 0.0)
        selected_train = _select(train, selected)
        selected_validation = _select(validation, selected)
        parameters, fit = _fit_selected(
            selected_train,
            selected_validation,
            candidates,
            parameters,
            complexities[selected],
            config,
        )
        point = _point(
            iteration,
            selected,
            parameters,
            fit,
            selected_train,
            selected_validation,
            candidates,
            readable,
        )
        frontier.append(point)
        frontier_parameters.append(parameters.copy())
        print(
            f"[v18] {iteration:02d} {readable[chosen_index].label} "
            f"weight={parameters.factor_weights[-1]:+.4f} "
            f"validation={point['validation_piece_mean_nll']:.6f}",
            flush=True,
        )
        if point["validation_piece_mean_nll"] < best_validation - required_gain:
            best_validation = point["validation_piece_mean_nll"]
            non_improvements = 0
        else:
            non_improvements += 1
            if non_improvements >= patience:
                print("[v18] validation patience reached", flush=True)
                break

    chosen_frontier_index, threshold = _one_standard_error_index(frontier)
    chosen_point = frontier[chosen_frontier_index]
    chosen_parameters = frontier_parameters[chosen_frontier_index]
    chosen_selected = selected[: chosen_point["selected_rule_count"]]
    chosen_selections = selections[: chosen_point["selected_rule_count"]]
    rules = [
        _rule_payload(
            readable[feature_index],
            weight,
            family_by_kind[readable[feature_index].kind],
            statistic,
            index,
        )
        for index, (feature_index, weight, statistic) in enumerate(
            zip(
                chosen_selected,
                chosen_parameters.factor_weights,
                chosen_selections,
                strict=True,
            ),
            start=1,
        )
    ]
    result = {
        "experiment": {
            "id": config["id"],
            "status": "DEVELOPMENT_EXPLANATORY_CANDIDATE",
            "config": str(args.config.resolve()),
            "source_catalogue_size": len(catalogue),
            "readable_catalogue_size": len(readable),
            "excluded_families": sorted(excluded),
            "train_piece_count": int(np.unique(train["piece_ids"]).size),
            "validation_piece_count": int(
                np.unique(validation["piece_ids"]).size
            ),
            "test_loaded": False,
            "historical_rules_loaded": False,
            "expert_constraints_loaded": False,
            "generation_metrics_used_for_weight_learning": False,
            "arbitrary_cross_factor_interactions": False,
        },
        "selection": {
            **{
                key: value
                for key, value in chosen_point.items()
                if key not in {"fit", "validation_piece_nll"}
            },
            "one_standard_error_threshold": threshold,
        },
        "model": {
            "register_logits": chosen_parameters.register.tolist(),
            "tonal_logits": chosen_parameters.tonal.tolist(),
            "rules": rules,
        },
        "frontier": frontier,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v18] selected {len(rules)} rules at "
        f"{chosen_point['validation_piece_mean_nll']:.6f}",
        flush=True,
    )
    print(f"[v18] wrote {args.output}", flush=True)
    print(f"[v18] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
