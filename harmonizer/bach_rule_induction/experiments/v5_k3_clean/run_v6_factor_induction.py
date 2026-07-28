#!/usr/bin/env python3
"""Induce V6 factor structure and weights from the frozen K3 grammar."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_contextual_induction as contextual
import run_induction as original
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_GRAMMAR = FACTOR_BASE / "grammar.yaml"
DEFAULT_MODEL = FACTOR_BASE / "v6_induced_model.json"
DEFAULT_SELECTED = FACTOR_BASE / "selected_factors.yaml"
DEFAULT_REPORT = FACTOR_BASE / "V6_INDUCTION_REPORT.md"
DEFAULT_MANIFEST = (
    REPOSITORY / "harmonizer/bach_rule_induction/corpus/manifest.music21-3.1.0.json"
)
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_ARCHIVE = (
    REPOSITORY.parent / "deepbach-reference/resources/cache/music21-3.1.0.tar.gz"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _feature_family_map(grammar: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for family in grammar["families"]:
        if family.get("role") == "nuisance_baseline":
            continue
        for kind in family["feature_kinds"]:
            previous = mapping.get(kind)
            if previous is not None and previous != family["id"]:
                raise ValueError(f"feature kind {kind!r} belongs to two families")
            mapping[kind] = str(family["id"])
    return mapping


def _catalogue(
    train: k3.K3Dataset,
    grammar: dict[str, Any],
) -> tuple[k3.FeatureSpec, ...]:
    structure = grammar["structure_learning"]
    contextual_features = k3.contextual_feature_catalogue(
        train,
        minimum_support=int(structure["minimum_testable_opportunities"]),
        minimum_piece_support=int(structure["minimum_piece_support"]),
        voice_specific_repeats=True,
        chromatic_rarity_threshold=None,
    )
    family_by_kind = _feature_family_map(grammar)
    catalogue = {
        feature.key: feature
        for feature in (*k3.feature_catalogue(), *contextual_features)
        if feature.kind in family_by_kind
        and feature.complexity <= int(structure["maximum_clause_complexity"])
    }
    unknown = sorted(
        {
            feature.kind
            for feature in (*k3.feature_catalogue(), *contextual_features)
            if feature.kind not in family_by_kind
        }
    )
    if unknown:
        raise ValueError(
            "frozen grammar does not classify generated feature kinds: "
            + ", ".join(unknown)
        )
    return tuple(catalogue[key] for key in sorted(catalogue))


def _append(matrix: np.ndarray, column: np.ndarray) -> np.ndarray:
    return np.concatenate(
        (matrix, column[:, :, None].astype(np.uint8)),
        axis=2,
    )


def _null_family_maxima(
    data: k3.K3Dataset,
    probabilities: np.ndarray,
    catalogue: tuple[k3.FeatureSpec, ...],
    family_by_kind: dict[str, str],
    selected: set[str],
    *,
    complexity_penalty: float,
    minimum_testable: int,
    minimum_piece_support: int,
) -> dict[str, float]:
    maxima: dict[str, float] = {}
    for feature in catalogue:
        if feature.key in selected:
            continue
        statistic = k3.residual_statistic(
            data,
            probabilities,
            k3.feature_mask(data, feature),
            feature.complexity,
            complexity_penalty,
        )
        if (
            statistic is None
            or statistic.testable_opportunities < minimum_testable
            or statistic.piece_support < minimum_piece_support
        ):
            continue
        family = family_by_kind[feature.kind]
        maxima[family] = max(
            maxima.get(family, 0.0),
            abs(statistic.z_score),
        )
    return maxima


def _best_authentic_column(
    data: k3.K3Dataset,
    probabilities: np.ndarray,
    catalogue: tuple[k3.FeatureSpec, ...],
    family_by_kind: dict[str, str],
    selected: set[str],
    null_maxima: dict[str, float],
    *,
    complexity_penalty: float,
    minimum_testable: int,
    minimum_piece_support: int,
) -> tuple[k3.FeatureSpec, k3.ResidualStatistic, np.ndarray, float] | None:
    ranked: list[
        tuple[
            float,
            k3.FeatureSpec,
            k3.ResidualStatistic,
            np.ndarray,
            float,
        ]
    ] = []
    for feature in catalogue:
        if feature.key in selected:
            continue
        mask = k3.feature_mask(data, feature)
        statistic = k3.residual_statistic(
            data,
            probabilities,
            mask,
            feature.complexity,
            complexity_penalty,
        )
        if (
            statistic is None
            or statistic.testable_opportunities < minimum_testable
            or statistic.piece_support < minimum_piece_support
            or statistic.column_score <= 0
        ):
            continue
        null_max = null_maxima.get(family_by_kind[feature.kind], 0.0)
        if abs(statistic.z_score) <= null_max:
            continue
        ranked.append(
            (
                statistic.column_score,
                feature,
                statistic,
                mask,
                null_max,
            )
        )
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1].key), reverse=True)
    _, feature, statistic, mask, null_max = ranked[0]
    return feature, statistic, mask, null_max


def _factor_payload(
    features: list[k3.FeatureSpec],
    weights: np.ndarray,
    statistics: list[k3.ResidualStatistic],
    family_by_kind: dict[str, str],
    null_maxima: list[float],
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"F-K3-V6-{index:03d}",
            "family": family_by_kind[feature.kind],
            "feature": feature.to_dict(),
            "parameter": {
                "scale": "log_energy_contribution",
                "log_weight": float(weight),
                "sign": "preference" if weight > 0 else "avoidance",
            },
            "selection": {
                **asdict(statistic),
                "null_family_max_abs_z": null_max,
                "exceeds_null_family_max": (abs(statistic.z_score) > null_max),
            },
            "origin": "learned_from_bach_corpus",
            "human_authored": False,
        }
        for index, (feature, weight, statistic, null_max) in enumerate(
            zip(
                features,
                weights,
                statistics,
                null_maxima,
                strict=True,
            ),
            start=1,
        )
    ]


def _markdown(result: dict[str, Any]) -> str:
    model = result["model"]
    lines = [
        "# V6 — induction d'une base factorielle depuis zéro",
        "",
        "## Garanties",
        "",
        "- Grammaire gelée avant cette exécution.",
        "- Aucune règle historique, CHORAL ou contrainte experte chargée.",
        "- Structure et poids appris sur `train`.",
        "- Validation utilisée uniquement pour le réajustement et l'arrêt.",
        "- Chaque sélection dépasse le maximum absolu de sa famille sous",
        "  permutation des choix à l'intérieur de chaque pièce et voix.",
        "- Test de 51 chorals non chargé.",
        "",
        "## Résultat",
        "",
        f"- Catalogue engendré : `{model['catalogue_size']}` facteurs candidats.",
        f"- Facteurs retenus : `{len(model['factors'])}`.",
        (f"- NLL validation baseline : `{model['baseline_validation_nll']:.6f}`."),
        f"- NLL validation finale : `{model['validation_nll']:.6f}`.",
        f"- Gain : `{model['validation_nll_gain']:.6f}`.",
        "",
        "| # | Famille | Prédicat numérique | Poids | z | max |z| nul |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for index, factor in enumerate(model["factors"], start=1):
        lines.append(
            f"| {index} | `{factor['family']}` | "
            f"`{factor['feature']['label']}` | "
            f"{factor['parameter']['log_weight']:+.6f} | "
            f"{factor['selection']['z_score']:+.3f} | "
            f"{factor['selection']['null_family_max_abs_z']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Les noms musicologiques et la comparaison aux traités sont différés",
            "jusqu'après gel de cette liste.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument(
        "--cache",
        type=Path,
        default=HERE / "work/k3-train-validation-context-full.npz",
    )
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--selected-output", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grammar = yaml.safe_load(args.grammar.read_text(encoding="utf-8"))
    if grammar["status"] != "FROZEN":
        raise ValueError("V6 grammar must be frozen before induction")
    if original._sha256(args.archive) != original.EXPECTED_ARCHIVE_SHA256:
        raise ValueError("historical corpus archive hash does not match")
    train, validation, manifest, splits = contextual._load_contextual_data(
        args.archive,
        args.manifest,
        args.splits,
        args.cache,
    )
    null_seed = int(grammar["structure_learning"]["null_control"]["seed"])
    null_train = k3.shuffle_choices_within_piece_and_voice(train, null_seed)
    null_validation = k3.shuffle_choices_within_piece_and_voice(
        validation,
        null_seed + 1,
    )
    catalogue = _catalogue(train, grammar)
    family_by_kind = _feature_family_map(grammar)
    structure = grammar["structure_learning"]
    parameters = grammar["parameter_learning"]
    maximum_factors = int(structure["maximum_factors"])
    minimum_testable = int(structure["minimum_testable_opportunities"])
    minimum_piece_support = int(structure["minimum_piece_support"])
    complexity_penalty = 1.0

    register = k3.learn_register_logits(train)
    tonal = k3.learn_voice_tonal_logits(train)
    train_base = k3.contextual_base_scores(train, register, tonal)
    validation_base = k3.contextual_base_scores(validation, register, tonal)
    null_register = k3.learn_register_logits(null_train)
    null_tonal = k3.learn_voice_tonal_logits(null_train)
    null_train_base = k3.contextual_base_scores(
        null_train,
        null_register,
        null_tonal,
    )
    null_validation_base = k3.contextual_base_scores(
        null_validation,
        null_register,
        null_tonal,
    )
    baseline_validation = k3.conditional_nll(
        validation,
        register,
        base_scores=validation_base,
    )

    features: list[k3.FeatureSpec] = []
    statistics: list[k3.ResidualStatistic] = []
    selection_null_maxima: list[float] = []
    weights = np.asarray([], dtype=np.float64)
    null_weights = np.asarray([], dtype=np.float64)
    train_matrix = k3.feature_matrix(train, ())
    validation_matrix = k3.feature_matrix(validation, ())
    null_train_matrix = k3.feature_matrix(null_train, ())
    null_validation_matrix = k3.feature_matrix(null_validation, ())
    best = (
        list(features),
        list(statistics),
        list(selection_null_maxima),
        weights.copy(),
        train_matrix.copy(),
        validation_matrix.copy(),
        baseline_validation,
    )
    history: list[dict[str, Any]] = []
    non_improvements = 0
    required_gain = float(structure["stopping"]["minimum_validation_nll_improvement"])
    patience = int(structure["stopping"]["consecutive_validation_non_improvements"])

    for iteration in range(1, maximum_factors + 1):
        selected = {feature.key for feature in features}
        null_probabilities = k3.probabilities(
            null_train,
            null_register,
            null_train_matrix,
            null_weights,
            base_scores=null_train_base,
        )
        null_maxima = _null_family_maxima(
            null_train,
            null_probabilities,
            catalogue,
            family_by_kind,
            selected,
            complexity_penalty=complexity_penalty,
            minimum_testable=minimum_testable,
            minimum_piece_support=minimum_piece_support,
        )
        probabilities = k3.probabilities(
            train,
            register,
            train_matrix,
            weights,
            base_scores=train_base,
        )
        chosen = _best_authentic_column(
            train,
            probabilities,
            catalogue,
            family_by_kind,
            selected,
            null_maxima,
            complexity_penalty=complexity_penalty,
            minimum_testable=minimum_testable,
            minimum_piece_support=minimum_piece_support,
        )
        if chosen is None:
            print("[v6] no column exceeds its null-family maximum", flush=True)
            break
        feature, statistic, train_column, null_max = chosen
        features.append(feature)
        statistics.append(statistic)
        selection_null_maxima.append(null_max)
        train_matrix = _append(train_matrix, train_column)
        validation_matrix = _append(
            validation_matrix,
            k3.feature_mask(validation, feature),
        )
        null_train_matrix = _append(
            null_train_matrix,
            k3.feature_mask(null_train, feature),
        )
        null_validation_matrix = _append(
            null_validation_matrix,
            k3.feature_mask(null_validation, feature),
        )
        fit_options = {
            "l1": float(parameters["l1"]),
            "max_steps": int(parameters["maximum_steps_per_refit"]),
            "learning_rate": float(parameters["learning_rate"]),
        }
        weights, fit = k3.fit_weights(
            train,
            validation,
            register,
            train_matrix,
            validation_matrix,
            train_base_scores=train_base,
            validation_base_scores=validation_base,
            **fit_options,
        )
        null_weights, _ = k3.fit_weights(
            null_train,
            null_validation,
            null_register,
            null_train_matrix,
            null_validation_matrix,
            train_base_scores=null_train_base,
            validation_base_scores=null_validation_base,
            **fit_options,
        )
        validation_nll = k3.conditional_nll(
            validation,
            register,
            validation_matrix,
            weights,
            base_scores=validation_base,
        )
        history.append(
            {
                "iteration": iteration,
                "feature": feature.to_dict(),
                "family": family_by_kind[feature.kind],
                "selection": {
                    **asdict(statistic),
                    "null_family_max_abs_z": null_max,
                },
                "weights": weights.tolist(),
                "validation_nll": validation_nll,
                "fit": fit,
            }
        )
        print(
            f"[v6] {iteration}: {feature.label} "
            f"z={statistic.z_score:+.2f} null={null_max:.2f} "
            f"validation={validation_nll:.6f}",
            flush=True,
        )
        if validation_nll < best[-1] - required_gain:
            best = (
                list(features),
                list(statistics),
                list(selection_null_maxima),
                weights.copy(),
                train_matrix.copy(),
                validation_matrix.copy(),
                validation_nll,
            )
            non_improvements = 0
        else:
            non_improvements += 1
            if non_improvements >= patience:
                print(f"[v6] stopping after {patience} non-improvements", flush=True)
                break

    (
        best_features,
        best_statistics,
        best_null_maxima,
        best_weights,
        best_train_matrix,
        _,
        best_validation_nll,
    ) = best
    factors = _factor_payload(
        best_features,
        best_weights,
        best_statistics,
        family_by_kind,
        best_null_maxima,
    )
    train_nll = k3.conditional_nll(
        train,
        register,
        best_train_matrix,
        best_weights,
        base_scores=train_base,
    )
    result = {
        "experiment": {
            "id": "F-K3-V6-INDUCED",
            "status": "STRUCTURE_AND_PARAMETERS_LEARNED",
            "grammar_id": grammar["id"],
            "grammar_sha256": _sha256(args.grammar),
            "test_loaded": False,
            "historical_rules_loaded": False,
            "expert_constraints_loaded": False,
            "null_seed": null_seed,
        },
        "corpus": {
            "manifest_summary": manifest["summary"],
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
            "candidate_min": train.candidate_min,
            "candidate_max": train.candidate_max,
        },
        "model": {
            "catalogue_size": len(catalogue),
            "register_logits": register.tolist(),
            "tonal_logits": tonal.tolist(),
            "baseline_validation_nll": baseline_validation,
            "train_nll": train_nll,
            "validation_nll": best_validation_nll,
            "validation_nll_gain": baseline_validation - best_validation_nll,
            "factors": factors,
            "rules": [
                {
                    "feature": factor["feature"],
                    "weight": factor["parameter"]["log_weight"],
                    "selection": factor["selection"],
                }
                for factor in factors
            ],
        },
        "search_history": history,
    }
    selected = {
        "schema_version": 1,
        "model_id": "F-K3-V6-INDUCED",
        "status": "LEARNED_FROM_CORPUS",
        "grammar": "grammar.yaml",
        "grammar_sha256": _sha256(args.grammar),
        "factors": factors,
        "test_split_loaded": False,
    }
    for path in (args.model_output, args.selected_output, args.report_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.selected_output.write_text(
        yaml.safe_dump(selected, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    args.report_output.write_text(_markdown(result), encoding="utf-8")
    print(f"[v6] wrote {args.model_output}", flush=True)
    print(f"[v6] wrote {args.selected_output}", flush=True)
    print(f"[v6] wrote {args.report_output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
