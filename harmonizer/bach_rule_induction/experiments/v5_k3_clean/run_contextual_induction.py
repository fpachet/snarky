#!/usr/bin/env python3
"""Reinduce K3 rules with key, metre, attack and vertical-set context."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_induction as original

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = (
    REPOSITORY / "harmonizer/bach_rule_induction/corpus/manifest.music21-3.1.0.json"
)
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_ARCHIVE = (
    REPOSITORY.parent / "deepbach-reference/resources/cache/music21-3.1.0.tar.gz"
)


def _load_contextual_data(
    archive: Path,
    manifest_path: Path,
    splits_path: Path,
    cache: Path,
) -> tuple[
    k3.K3Dataset,
    k3.K3Dataset,
    dict[str, Any],
    dict[str, list[str]],
]:
    manifest, included, splits = original._load_inputs(manifest_path, splits_path)
    permitted = set(splits["train"] + splits["validation"])
    selected = [piece for piece in included if piece["id"] in permitted]
    if cache.exists():
        data = k3.load_k3_dataset(cache)
        if data.tonic_pcs is None:
            raise ValueError("Contextual cache lacks declared-key metadata")
    else:
        paths = original._materialize_scores(archive, selected, HERE / "work/scores")
        data = k3.build_k3_dataset(paths)
        k3.save_k3_dataset(cache, data)
    train = k3.subset_for_piece_ids(data, splits["train"])
    validation = k3.subset_for_piece_ids(data, splits["validation"])
    minimum, maximum = k3.training_domain(train)
    train, train_removed = k3.filter_to_domain(train, minimum, maximum)
    validation, validation_removed = k3.filter_to_domain(
        validation,
        minimum,
        maximum,
    )
    if train_removed or validation_removed:
        raise ValueError("Contextual domain unexpectedly removed observed choices")
    return train, validation, manifest, splits


def _append_feature(matrix: np.ndarray, column: np.ndarray) -> np.ndarray:
    return np.concatenate((matrix, column[:, :, None].astype(np.uint8)), axis=2)


def _pcset(signature: int) -> list[int]:
    return [pitch_class for pitch_class in range(12) if signature & (1 << pitch_class)]


def _rule_explanation(feature: k3.FeatureSpec) -> str:
    if feature.kind == "attacked_repeat_from_previous":
        scope = (
            "toutes voix"
            if feature.target_voice == -1
            else k3.VOICE_NAMES[feature.target_voice]
        )
        return f"attaque répétant exactement la hauteur précédente ({scope})"
    if feature.kind == "central_tonic_pcset":
        return f"ensemble vertical relatif à la tonique {_pcset(int(feature.value))}"
    if feature.kind == "central_bass_pcset":
        return f"ensemble vertical relatif à la basse {_pcset(int(feature.value))}"
    if feature.kind == "central_distinct_pc_count":
        return f"bloc central avec {feature.value} classes distinctes"
    if feature.kind == "central_distinct_pc_count_metric":
        return (
            f"bloc central avec {feature.value} classes distinctes "
            f"au niveau métrique {feature.second_value}"
        )
    return feature.label


def _markdown(result: dict[str, Any]) -> str:
    model = result["model"]
    baseline = result["baseline"]
    display_id = result["experiment"]["id"].replace("V5_7", "V5.7")
    lines = [
        f"# {display_id} — réinduction contextuelle K3",
        "",
        "## Ajouts",
        "",
        "- Tonique et mode globaux déclarés dans le MusicXML.",
        (
            "- Distribution catégorielle apprise des classes relatives par voix "
            "et mode."
            if result["experiment"]["voice_specific_tonal_baseline"]
            else "- Distribution catégorielle apprise des classes relatives par mode."
        ),
        "- Répétition attaquée distincte d'une tenue.",
        "- Nombre de classes distinctes, éventuellement conditionné par la métrique.",
        "- Fingerprints verticaux mécaniquement énumérés relativement à la tonique",
        "  ou à la basse.",
        "- Aucune règle historique ni étiquette d'accord chargée.",
        "- Test fermé non chargé.",
        "",
        "## Baselines",
        "",
        (
            f"- NLL validation registre absolu : "
            f"`{baseline['register_validation_nll']:.6f}`."
        ),
        (
            f"- NLL validation registre + tonalité : "
            f"`{baseline['tonal_validation_nll']:.6f}`."
        ),
        f"- Gain tonal seul : `{baseline['tonal_gain']:.6f}`.",
        "",
        "## Modèle réinduit",
        "",
        f"- Catalogue total : `{model['catalogue_size']}` prédicats.",
        f"- Règles retenues : `{len(model['rules'])}`.",
        f"- NLL validation finale : `{model['validation_nll']:.6f}`.",
        f"- Gain total : `{model['validation_nll_gain']:.6f}`.",
        "",
        "| # | Lecture numérique | Poids | z de sélection |",
        "|---:|---|---:|---:|",
    ]
    for index, rule in enumerate(model["rules"], start=1):
        lines.append(
            f"| {index} | {_rule_explanation(k3.feature_from_model_record(rule))} | "
            f"{rule['weight']:+.6f} | {rule['selection']['z_score']:+.3f} |"
        )
    lines.extend(
        [
            "",
            "Les fingerprints restent des ensembles numériques. Les noms d'accords",
            "ne seront attribués qu'après gel et comparaison musicologique.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument(
        "--cache",
        type=Path,
        default=HERE / "work/k3-train-validation-context-full.npz",
    )
    parser.add_argument("--max-rules", type=int, default=18)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--complexity-penalty", type=float, default=1.0)
    parser.add_argument("--min-testable", type=int, default=100)
    parser.add_argument("--min-piece-support", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    parser.add_argument("--version", default="v5_6")
    parser.add_argument("--voice-specific-tonal", action="store_true")
    parser.add_argument("--voice-specific-repeats", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if original._sha256(args.archive) != original.EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Historical corpus archive hash does not match")
    train, validation, manifest, splits = _load_contextual_data(
        args.archive,
        args.manifest,
        args.splits,
        args.cache,
    )
    register_logits = k3.learn_register_logits(train)
    tonal_logits = (
        k3.learn_voice_tonal_logits(train)
        if args.voice_specific_tonal
        else k3.learn_tonal_logits(train)
    )
    train_base = k3.contextual_base_scores(train, register_logits, tonal_logits)
    validation_base = k3.contextual_base_scores(
        validation,
        register_logits,
        tonal_logits,
    )
    register_validation_nll = k3.conditional_nll(validation, register_logits)
    tonal_validation_nll = k3.conditional_nll(
        validation,
        register_logits,
        base_scores=validation_base,
    )
    contextual = k3.contextual_feature_catalogue(
        train,
        minimum_support=args.min_testable,
        minimum_piece_support=args.min_piece_support,
        voice_specific_repeats=args.voice_specific_repeats,
    )
    catalogue_map = {
        feature.key: feature for feature in (*k3.feature_catalogue(), *contextual)
    }
    catalogue = tuple(catalogue_map[key] for key in sorted(catalogue_map))
    selected_features: list[k3.FeatureSpec] = []
    selected_statistics: list[k3.ResidualStatistic] = []
    weights = np.asarray([], dtype=np.float64)
    train_matrix = k3.feature_matrix(train, ())
    validation_matrix = k3.feature_matrix(validation, ())
    best_snapshot = (
        selected_features.copy(),
        selected_statistics.copy(),
        weights.copy(),
        train_matrix,
        validation_matrix,
        tonal_validation_nll,
    )
    iterations = []
    for iteration in range(1, args.max_rules + 1):
        probabilities = k3.probabilities(
            train,
            register_logits,
            train_matrix,
            weights,
            base_scores=train_base,
        )
        selected_keys = {feature.key for feature in selected_features}
        ranked = []
        for feature_index, feature in enumerate(catalogue, start=1):
            if feature.key in selected_keys:
                continue
            mask = k3.feature_mask(train, feature)
            statistic = k3.residual_statistic(
                train,
                probabilities,
                mask,
                feature.complexity,
                args.complexity_penalty,
            )
            if (
                statistic is None
                or statistic.testable_opportunities < args.min_testable
                or statistic.piece_support < args.min_piece_support
                or statistic.column_score <= 0
            ):
                continue
            ranked.append((statistic.column_score, feature, statistic, mask))
            if feature_index % 250 == 0:
                print(
                    f"[k3-context] iteration {iteration}: "
                    f"{feature_index}/{len(catalogue)}",
                    flush=True,
                )
        if not ranked:
            break
        ranked.sort(key=lambda item: (item[0], item[1].key), reverse=True)
        _, feature, statistic, train_column = ranked[0]
        validation_column = k3.feature_mask(validation, feature)
        selected_features.append(feature)
        selected_statistics.append(statistic)
        train_matrix = _append_feature(train_matrix, train_column)
        validation_matrix = _append_feature(
            validation_matrix,
            validation_column,
        )
        weights, fit = k3.fit_weights(
            train,
            validation,
            register_logits,
            train_matrix,
            validation_matrix,
            l1=args.l1,
            max_steps=args.max_steps,
            learning_rate=args.learning_rate,
            train_base_scores=train_base,
            validation_base_scores=validation_base,
        )
        validation_nll = k3.conditional_nll(
            validation,
            register_logits,
            validation_matrix,
            weights,
            base_scores=validation_base,
        )
        print(
            f"[k3-context] {iteration}: {feature.label} "
            f"z={statistic.z_score:+.3f} validation={validation_nll:.6f}",
            flush=True,
        )
        iterations.append(
            {
                "iteration": iteration,
                "selected": feature.to_dict(),
                "selection": asdict(statistic),
                "fit": fit,
                "validation_nll": validation_nll,
            }
        )
        if validation_nll < best_snapshot[5]:
            best_snapshot = (
                selected_features.copy(),
                selected_statistics.copy(),
                weights.copy(),
                train_matrix.copy(),
                validation_matrix.copy(),
                validation_nll,
            )
    (
        selected_features,
        selected_statistics,
        weights,
        train_matrix,
        validation_matrix,
        best_validation,
    ) = best_snapshot
    train_nll = k3.conditional_nll(
        train,
        register_logits,
        train_matrix,
        weights,
        base_scores=train_base,
    )
    result = {
        "experiment": {
            "id": f"{args.version.upper()}-K3-CONTEXTUAL-REINDUCTION",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "initial_musical_rules": 0,
            "locality_blocks": 3,
            "manifest_summary": manifest["summary"],
            "voice_specific_tonal_baseline": args.voice_specific_tonal,
            "voice_specific_repeats": args.voice_specific_repeats,
        },
        "corpus": {
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
            "candidate_min": train.candidate_min,
            "candidate_max": train.candidate_max,
        },
        "baseline": {
            "register_validation_nll": register_validation_nll,
            "tonal_validation_nll": tonal_validation_nll,
            "tonal_gain": register_validation_nll - tonal_validation_nll,
            "tonal_logits": tonal_logits.tolist(),
        },
        "model": {
            "register_logits": register_logits.tolist(),
            "tonal_logits": tonal_logits.tolist(),
            "catalogue_size": len(catalogue),
            "contextual_catalogue_size": len(contextual),
            "train_nll": train_nll,
            "validation_nll": best_validation,
            "validation_nll_gain": register_validation_nll - best_validation,
            "rules": [
                {
                    "feature": feature.to_dict(),
                    "weight": float(weight),
                    "selection": asdict(statistic),
                }
                for feature, weight, statistic in zip(
                    selected_features,
                    weights,
                    selected_statistics,
                    strict=True,
                )
            ],
            "iterations": iterations,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.version}_k3_contextual_model.json"
    report_path = (
        args.output_dir / f"{args.version.upper()}_K3_CONTEXTUAL_REINDUCTION.md"
    )
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-context] wrote {json_path}", flush=True)
    print(f"[k3-context] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
