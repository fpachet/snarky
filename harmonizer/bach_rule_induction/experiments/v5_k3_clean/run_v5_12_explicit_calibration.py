#!/usr/bin/env python3
"""Calibrate explicit bass-motion and sonority-trajectory K3 rules."""

from __future__ import annotations

import argparse
import copy
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import k3
import numpy as np
import run_generative_moment_calibration as generative
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "results/v5_9_generative_model.json"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


def _chosen_values(
    dataset: k3.K3Dataset,
    values: np.ndarray,
) -> np.ndarray:
    return values[np.arange(dataset.size), dataset.chosen_indices]


def _feature_rates(
    chain: generative.Chain,
    blocks: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
    candidate_min: int,
    candidate_max: int,
) -> np.ndarray:
    """Measure chosen predicates per relevant attack decision in one piece."""

    dataset = generative._decision_dataset(
        chain,
        blocks,
        candidate_min,
        candidate_max,
    )
    rows = np.arange(dataset.size)
    chosen = dataset.chosen_indices
    rates = np.zeros(len(features), dtype=np.float64)
    for index, feature in enumerate(features):
        applies = (
            np.ones(dataset.size, dtype=bool)
            if feature.target_voice == -1
            else dataset.voice_indices == feature.target_voice
        )
        if applies.any():
            mask = k3.feature_mask(dataset, feature)
            rates[index] = float(mask[rows, chosen][applies].mean())
    return rates


def _observed_contexts(
    chains: Iterable[generative.Chain],
    *,
    candidate_min: int,
    candidate_max: int,
    generated: bool,
) -> list[tuple[str, int, int, int]]:
    """Return piece, metric, central signature, following signature."""

    contexts = []
    for chain in chains:
        blocks = chain.blocks if generated else chain.lattice.blocks
        dataset = generative._decision_dataset(
            chain,
            blocks,
            candidate_min,
            candidate_max,
        )
        central = _chosen_values(
            dataset,
            k3.central_bass_pcset_signatures(dataset),
        )
        following = _chosen_values(
            dataset,
            k3.bass_pcset_signatures(dataset, position=2),
        )
        for level, current, next_signature in zip(
            dataset.metric_levels,
            central,
            following,
            strict=True,
        ):
            contexts.append(
                (
                    chain.piece_id,
                    int(level >= 2),
                    int(current),
                    int(next_signature),
                )
            )
    return contexts


def _supported_features(
    contexts: list[tuple[str, int, int, int]],
    *,
    minimum_support: int,
    minimum_piece_support: int,
) -> tuple[k3.FeatureSpec, ...]:
    metric_counts = Counter((strong, current) for _, strong, current, _ in contexts)
    transition_counts = Counter((current, following) for _, _, current, following in contexts)
    metric_pieces: dict[tuple[int, int], set[str]] = {}
    transition_pieces: dict[tuple[int, int], set[str]] = {}
    for piece_id, strong, current, following in contexts:
        metric_pieces.setdefault((strong, current), set()).add(piece_id)
        transition_pieces.setdefault((current, following), set()).add(piece_id)

    features: list[k3.FeatureSpec] = []
    features.append(
        k3.FeatureSpec(
            "attacked_repeat_from_previous",
            3,
            complexity=1,
        )
    )
    for (strong, signature), support in metric_counts.items():
        if support < minimum_support:
            continue
        if len(metric_pieces[(strong, signature)]) < minimum_piece_support:
            continue
        features.append(
            k3.FeatureSpec(
                "central_bass_pcset_metric",
                -1,
                value=signature,
                second_value=strong,
                complexity=4,
            )
        )
    for (current, following), support in transition_counts.items():
        if support < minimum_support:
            continue
        if len(transition_pieces[(current, following)]) < minimum_piece_support:
            continue
        features.append(
            k3.FeatureSpec(
                "bass_pcset_transition",
                -1,
                value=current,
                second_value=following,
                complexity=5,
            )
        )
    return tuple(features)


def _candidate_catalogue(
    chains: list[generative.Chain],
    *,
    candidate_min: int,
    candidate_max: int,
    selected_keys: set[str],
    minimum_support: int,
    minimum_piece_support: int,
    allow_adjustments: bool,
) -> tuple[k3.FeatureSpec, ...]:
    features: list[k3.FeatureSpec] = []
    features.extend(
        k3.FeatureSpec(
            "abs_class_from_previous",
            3,
            value=interval_class,
            complexity=2,
        )
        for interval_class in range(12)
    )
    features.extend(
        k3.FeatureSpec(
            "abs_step_from_previous_gt",
            3,
            value=threshold,
            complexity=2,
        )
        for threshold in k3.DEFAULT_THRESHOLDS
    )
    features.extend(
        k3.FeatureSpec(
            "three_block_sign_shape",
            3,
            value=incoming,
            second_value=outgoing,
            complexity=3,
        )
        for incoming in (-1, 0, 1)
        for outgoing in (-1, 0, 1)
    )
    features.extend(
        k3.FeatureSpec(
            "any_pair_central_abs_class_metric",
            -1,
            value=interval_class,
            second_value=strong,
            complexity=3,
        )
        for interval_class in range(12)
        for strong in (0, 1)
    )
    features.extend(
        k3.FeatureSpec(
            "central_triadic_metric",
            -1,
            value=1,
            second_value=strong,
            complexity=2,
        )
        for strong in (0, 1)
    )
    contexts = [
        *_observed_contexts(
            chains,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            generated=False,
        ),
        *_observed_contexts(
            chains,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            generated=True,
        ),
    ]
    features.extend(
        _supported_features(
            contexts,
            minimum_support=minimum_support,
            minimum_piece_support=minimum_piece_support,
        )
    )
    unique = {
        feature.key: feature
        for feature in features
        if allow_adjustments
        or feature.key not in selected_keys
        or feature.kind == "attacked_repeat_from_previous"
    }
    return tuple(unique[key] for key in sorted(unique))


def _paired_statistics(
    source_rates: np.ndarray,
    generated_rates: np.ndarray,
    features: tuple[k3.FeatureSpec, ...],
) -> list[dict[str, Any]]:
    differences = source_rates - generated_rates
    records = []
    for index, feature in enumerate(features):
        values = differences[:, index]
        mean = float(values.mean())
        standard_error = (
            0.0
            if values.size < 2
            else float(values.std(ddof=1) / math.sqrt(values.size))
        )
        z_score = mean / max(standard_error, 1e-6)
        records.append(
            {
                "feature": feature.to_dict(),
                "bach_rate": float(source_rates[:, index].mean()),
                "gibbs_rate": float(generated_rates[:, index].mean()),
                "gradient": mean,
                "standard_error": standard_error,
                "z_score": z_score,
                "selection_score": (
                    abs(mean)
                    * max(abs(z_score), 0.25)
                    / max(feature.complexity, 1)
                ),
            }
        )
    return records


def _family(feature: k3.FeatureSpec) -> str:
    if feature.target_voice == 3:
        return "bass_motion"
    if feature.kind == "bass_pcset_transition":
        return "sonority_transition"
    return "vertical_context"


def _select_with_quotas(
    records: list[dict[str, Any]],
    features: tuple[k3.FeatureSpec, ...],
    *,
    per_family: int,
    minimum_rate: float,
    sign_balanced: bool,
    families: tuple[str, ...],
) -> tuple[list[int], list[dict[str, Any]]]:
    selected: list[tuple[float, int, dict[str, Any]]] = []
    for family in families:
        admissible = [
            (record["selection_score"], index, record)
            for index, record in enumerate(records)
            if _family(features[index]) == family
            and max(record["bach_rate"], record["gibbs_rate"]) >= minimum_rate
        ]
        admissible.sort(
            key=lambda item: (item[0], features[item[1]].key),
            reverse=True,
        )
        if not sign_balanced:
            selected.extend(admissible[:per_family])
            continue
        positive = [item for item in admissible if item[2]["gradient"] > 0]
        negative = [item for item in admissible if item[2]["gradient"] < 0]
        positive_budget = per_family // 2
        negative_budget = per_family - positive_budget
        selected.extend(positive[:positive_budget])
        selected.extend(negative[:negative_budget])
    selected.sort(key=lambda item: (item[0], features[item[1]].key), reverse=True)
    return (
        [index for _, index, _ in selected],
        [record for _, _, record in selected],
    )


def _pitch_classes(signature: int) -> str:
    values = [
        str(pitch_class)
        for pitch_class in range(12)
        if signature & (1 << pitch_class)
    ]
    return "{" + ", ".join(values) + "}"


def _description(feature: k3.FeatureSpec) -> str:
    if feature.kind == "attacked_repeat_from_previous":
        return "répétition attaquée de basse (correction additive)"
    if feature.kind == "abs_class_from_previous":
        return f"basse : classe d'intervalle entrant {feature.value}"
    if feature.kind == "abs_step_from_previous_gt":
        return f"basse : saut entrant supérieur à {feature.value} demi-tons"
    if feature.kind == "three_block_sign_shape":
        return (
            "basse : directions K3 "
            f"({feature.value:+d}, {feature.second_value:+d})"
        )
    if feature.kind == "any_pair_central_abs_class_metric":
        metric = "fort" if feature.second_value else "faible"
        return (
            f"intervalle vertical {feature.value} présent sur bloc métrique {metric}"
        )
    if feature.kind == "central_bass_pcset_metric":
        metric = "fort" if feature.second_value else "faible"
        return (
            f"sonorité {_pitch_classes(int(feature.value))} "
            f"relative à la basse, bloc {metric}"
        )
    if feature.kind == "central_triadic_metric":
        metric = "fort" if feature.second_value else "faible"
        return f"sonorité triadique (six renversements), bloc {metric}"
    if feature.kind == "bass_pcset_transition":
        return (
            f"transition {_pitch_classes(int(feature.value))} → "
            f"{_pitch_classes(int(feature.second_value))}"
        )
    return feature.label


def _markdown(result: dict[str, Any]) -> str:
    model = result["model"]
    version = result["experiment"]["version"]
    key = result["experiment"]["model_key"]
    lines = [
        f"# {version} — calibration K3 explicite de la basse et des sonorités",
        "",
        "V5.11 n'est pas utilisée. Toutes les variables sont directement",
        "observables dans trois blocs : mouvement de basse, niveau métrique,",
        "intervalles verticaux et empreintes de sonorité relatives à la basse.",
        "",
        "Le gradient reste :",
        "",
        "`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.",
        "",
        f"Calibration sur `{result['corpus']['calibration_train_pieces']}` chorals",
        "du train. Validation utilisée seulement pour la NLL finale ; test fermé.",
        "",
        "## Règles retenues",
        "",
        "| Règle observable | Famille | Bach | Gibbs initial | Gradient | Poids |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for rule in model[f"{key}_rules"]:
        feature = k3.feature_from_model_record(rule)
        selection = rule["selection"]
        lines.append(
            f"| {_description(feature)} | `{_family(feature)}` | "
            f"{100 * selection['bach_rate']:.2f} % | "
            f"{100 * selection['gibbs_rate']:.2f} % | "
            f"{100 * selection['gradient']:+.2f} pp | "
            f"{rule['weight']:+.4f} |"
        )
    lines.extend(
        [
            "",
            "## Critères internes",
            "",
            f"- candidats explicites : `{model[f'{key}_candidate_count']}` ;",
            f"- règles ajoutées : `{model[f'{key}_rule_count']}` ;",
            (
                "- erreur absolue moyenne des moments sélectionnés : "
                f"`{model[f'{key}_initial_moment_mae']:.6f}` → "
                f"`{model[f'{key}_final_moment_mae']:.6f}` ;"
            ),
            (
                f"- NLL validation avant : "
                f"`{model[f'{key}_base_validation_nll']:.6f}` ;"
            ),
            f"- NLL validation après : `{model['validation_nll']:.6f}`.",
            "",
            "Ces nombres ne suffisent pas à promouvoir le modèle. La décision",
            "dépend de générations contrôlées multi-chorals et d'un retour",
            "spécifique sur BWV 108.6.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=16)
    parser.add_argument("--burn-in-sweeps", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--sweeps-per-epoch", type=int, default=2)
    parser.add_argument("--per-family", type=int, default=4)
    parser.add_argument("--sign-balanced", action="store_true")
    parser.add_argument("--minimum-rate", type=float, default=0.003)
    parser.add_argument("--minimum-support", type=int, default=20)
    parser.add_argument("--minimum-piece-support", type=int, default=3)
    parser.add_argument(
        "--families",
        default="bass_motion,vertical_context,sonority_transition",
    )
    parser.add_argument("--allow-adjustments", action="store_true")
    parser.add_argument("--learning-rate", type=float, default=0.10)
    parser.add_argument("--l1", type=float, default=0.002)
    parser.add_argument("--anchor", type=float, default=0.02)
    parser.add_argument("--max-abs-weight", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=5912)
    parser.add_argument("--version", default="V5_12")
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_payload = json.loads(args.model.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(
        splits["train"],
        key=generative._stable_order,
    )[: args.train_pieces]
    model = base_payload["model"]
    corpus = base_payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    base_features = tuple(
        k3.feature_from_model_record(rule) for rule in model["rules"]
    )
    base_weights = np.asarray([rule["weight"] for rule in model["rules"]])
    selected_keys = {feature.key for feature in base_features}
    full = k3.load_k3_dataset(args.cache)
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, removed = k3.filter_to_domain(
        validation,
        candidate_min,
        candidate_max,
    )
    if removed:
        raise ValueError("Validation choices unexpectedly fall outside train domain")

    chains = []
    for piece_id in train_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        initial = rhythmic._randomize_mutable_segments(
            lattice.blocks,
            lattice.attacks,
            fixed,
            register_logits,
            candidate_min,
            generative._piece_seed(piece_id, args.seed),
            tonal_logits,
            lattice.tonic_pc,
            lattice.mode,
        )
        chains.append(generative.Chain(piece_id, lattice, initial, fixed))

    generative._sample_chains(
        chains,
        base_features,
        base_weights,
        (),
        np.asarray([], dtype=np.float64),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        register_logits=register_logits,
        tonal_logits=tonal_logits,
        sweeps=args.burn_in_sweeps,
        seed=args.seed + 1,
    )
    candidates = _candidate_catalogue(
        chains,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        selected_keys=selected_keys,
        minimum_support=args.minimum_support,
        minimum_piece_support=args.minimum_piece_support,
        allow_adjustments=args.allow_adjustments,
    )
    source_rates = np.stack(
        [
            _feature_rates(
                chain,
                chain.lattice.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )
    initial_generated_rates = np.stack(
        [
            _feature_rates(
                chain,
                chain.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )
    statistics = _paired_statistics(
        source_rates,
        initial_generated_rates,
        candidates,
    )
    selected_indices, selection_metadata = _select_with_quotas(
        statistics,
        candidates,
        per_family=args.per_family,
        minimum_rate=args.minimum_rate,
        sign_balanced=args.sign_balanced,
        families=tuple(
            family.strip()
            for family in args.families.split(",")
            if family.strip()
        ),
    )
    selected_features = tuple(candidates[index] for index in selected_indices)
    empirical = source_rates[:, selected_indices].mean(axis=0)
    initial_generated = initial_generated_rates[:, selected_indices].mean(axis=0)

    weights = np.zeros(len(selected_features), dtype=np.float64)
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    history = []
    for epoch in range(1, args.epochs + 1):
        generative._sample_chains(
            chains,
            base_features,
            base_weights,
            selected_features,
            weights,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            register_logits=register_logits,
            tonal_logits=tonal_logits,
            sweeps=args.sweeps_per_epoch,
            seed=args.seed + 1 + epoch,
        )
        generated_rates = np.stack(
            [
                _feature_rates(
                    chain,
                    chain.blocks,
                    selected_features,
                    candidate_min,
                    candidate_max,
                )
                for chain in chains
            ]
        )
        generated = generated_rates.mean(axis=0)
        gradient = empirical - generated - args.anchor * weights
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient**2
        corrected_first = first / (1.0 - 0.9**epoch)
        corrected_second = second / (1.0 - 0.999**epoch)
        weights += (
            args.learning_rate
            * corrected_first
            / (np.sqrt(corrected_second) + 1e-8)
        )
        weights = np.sign(weights) * np.maximum(
            np.abs(weights) - args.learning_rate * args.l1,
            0.0,
        )
        weights = np.clip(weights, -args.max_abs_weight, args.max_abs_weight)
        history.append(
            {
                "epoch": epoch,
                "weights": weights.tolist(),
                "bach_moments": empirical.tolist(),
                "gibbs_moments": generated.tolist(),
                "gradient": gradient.tolist(),
                "moment_mae": float(np.abs(empirical - generated).mean()),
            }
        )
        print(
            f"[k3-{args.version.lower().replace('_', '.')}] "
            f"epoch {epoch}/{args.epochs}: "
            f"moment_mae={history[-1]['moment_mae']:.6f}",
            flush=True,
        )

    final_generated = np.asarray(history[-1]["gibbs_moments"])
    all_features = (*base_features, *selected_features)
    all_weights = np.concatenate((base_weights, weights))
    validation_nll = generative._conditional_validation_nll(
        validation,
        register_logits,
        tonal_logits,
        all_features,
        all_weights,
    )
    output = copy.deepcopy(base_payload)
    version_key = args.version.lower()
    output["experiment"] = {
        "id": f"{args.version}-K3-EXPLICIT-GENERATIVE-CALIBRATION",
        "version": args.version.replace("_", "."),
        "model_key": version_key,
        "status": "EXPLORATORY_FROZEN_FOR_VALIDATION",
        "test_loaded": False,
        "source_model": str(args.model.resolve()),
        "latent_states": False,
        "gradient": "E_Bach[f] - E_Gibbs[f]",
    }
    output["corpus"]["calibration_train_pieces"] = len(train_ids)
    output["corpus"]["calibration_piece_ids"] = train_ids
    output["model"][f"{version_key}_base_validation_nll"] = float(
        model["validation_nll"]
    )
    output["model"]["validation_nll"] = validation_nll
    output["model"][f"{version_key}_candidate_count"] = len(candidates)
    output["model"][f"{version_key}_rule_count"] = len(selected_features)
    output["model"][f"{version_key}_initial_moment_mae"] = float(
        np.abs(empirical - initial_generated).mean()
    )
    output["model"][f"{version_key}_final_moment_mae"] = float(
        np.abs(empirical - final_generated).mean()
    )
    output["model"][f"{version_key}_rules"] = [
        {
            "feature": feature.to_dict(),
            "weight": float(weight),
            "selection": selection,
        }
        for feature, weight, selection in zip(
            selected_features,
            weights,
            selection_metadata,
            strict=True,
        )
    ]
    output["model"]["rules"].extend(output["model"][f"{version_key}_rules"])
    output["model"][f"{version_key}_history"] = history
    output["model"][f"{version_key}_calibration"] = {
        "burn_in_sweeps": args.burn_in_sweeps,
        "epochs": args.epochs,
        "sweeps_per_epoch": args.sweeps_per_epoch,
        "per_family": args.per_family,
        "sign_balanced": args.sign_balanced,
        "families": [
            family.strip()
            for family in args.families.split(",")
            if family.strip()
        ],
        "allow_adjustments": args.allow_adjustments,
        "learning_rate": args.learning_rate,
        "l1": args.l1,
        "anchor": args.anchor,
        "max_abs_weight": args.max_abs_weight,
        "seed": args.seed,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{version_key}_explicit_generative_model.json"
    report_path = (
        args.output_dir / f"{args.version}_EXPLICIT_GENERATIVE_CALIBRATION.md"
    )
    json_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(output), encoding="utf-8")
    print(f"[k3-{version_key}] wrote {json_path}", flush=True)
    print(f"[k3-{version_key}] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
