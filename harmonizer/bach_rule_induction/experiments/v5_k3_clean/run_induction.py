#!/usr/bin/env python3
"""Run clean-room residual rule induction on K3 Bach decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import k3
import numpy as np

EXPECTED_ARCHIVE_SHA256 = (
    "73a33407459e59fc5cfa7ea268088e5e10db9354e01ceceb2295d56373b937d2"
)
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_inputs(
    manifest_path: Path,
    splits_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[str]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pieces = [piece for piece in manifest["pieces"] if piece["included"]]
    split_payload = json.loads(splits_path.read_text(encoding="utf-8"))
    split_source = split_payload.get("grouped_split", split_payload)
    splits = {
        name: list(split_source[name]) for name in ("train", "validation", "test")
    }
    ids = {piece["id"] for piece in pieces}
    flattened = [piece for values in splits.values() for piece in values]
    if len(flattened) != len(set(flattened)) or set(flattened) != ids:
        raise ValueError("Variant-safe split does not partition the corpus")
    return manifest, pieces, splits


def _materialize_scores(
    archive_path: Path,
    pieces: list[dict[str, Any]],
    destination: Path,
) -> dict[str, Path]:
    destination.mkdir(parents=True, exist_ok=True)
    requested = {
        f"music21-3.1.0/music21/corpus/{piece['source_path']}": piece
        for piece in pieces
    }
    result: dict[str, Path] = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers()}
        missing = sorted(set(requested) - set(members))
        if missing:
            raise FileNotFoundError(f"Archive lacks {len(missing)} requested scores")
        for member_name, piece in requested.items():
            output = destination / Path(member_name).name
            if not output.exists() or _sha256(output) != piece["sha256"]:
                source = archive.extractfile(members[member_name])
                if source is None:
                    raise OSError(f"Cannot extract {member_name}")
                output.write_bytes(source.read())
            result[piece["id"]] = output
    return result


def _append_feature(
    matrix: np.ndarray,
    column: np.ndarray,
) -> np.ndarray:
    return np.concatenate((matrix, column[:, :, None].astype(np.uint8)), axis=2)


def _statistic_payload(statistic: k3.ResidualStatistic) -> dict[str, Any]:
    return asdict(statistic)


def _posthoc_benchmark(features: list[k3.FeatureSpec]) -> dict[str, Any]:
    """Apply musicological names only after the selected catalogue is frozen."""

    selected = {(feature.kind, feature.value) for feature in features}
    return {
        "melodic_class_6": (
            ("abs_class_from_previous", 6) in selected
            or ("abs_class_to_next", 6) in selected
            or ("any_voice_adjacent_abs_class", 6) in selected
        ),
        "preserved_pair_class_0": (
            "pair_abs_class_preserved_same_sign",
            0,
        )
        in selected
        or ("any_pair_abs_class_preserved_same_sign", 0) in selected,
        "preserved_pair_class_7": (
            "pair_abs_class_preserved_same_sign",
            7,
        )
        in selected
        or ("any_pair_abs_class_preserved_same_sign", 7) in selected,
        "arrival_pair_class_0": (
            "pair_arrival_abs_class_same_sign",
            0,
        )
        in selected
        or ("any_pair_arrival_abs_class_same_sign", 0) in selected,
        "arrival_pair_class_7": (
            "pair_arrival_abs_class_same_sign",
            7,
        )
        in selected
        or ("any_pair_arrival_abs_class_same_sign", 7) in selected,
        "previous_or_central_order_boundary": any(
            feature.kind
            in {
                "central_ordered_gap_le",
                "previous_ordered_gap_le",
                "any_adjacent_central_ordered_gap_le",
            }
            and feature.value in {-1, 0}
            for feature in features
        ),
    }


def _markdown_report(result: dict[str, Any]) -> str:
    corpus = result["corpus"]
    model = result["model"]
    lines = [
        "# V5-K3-CLEAN — premier cycle d'induction",
        "",
        "## Protocole",
        "",
        "- Base musicale initiale vide.",
        "- Une note masquée et trois blocs verticaux consécutifs.",
        "- Domaine commun de hauteurs dérivé du seul train.",
        "- Aucun manifeste ni fichier de règles V1–V4 chargé.",
        "- Sélection des colonnes sur le gradient résiduel du train.",
        "- Les noms musicologiques ne sont appliqués qu'après sélection.",
        (
            "- Contrôle nul : choix permutés au sein de chaque pièce et voix."
            if result["experiment"]["null_shuffle"]
            else "- Données authentiques, sans permutation."
        ),
        "",
        "## Corpus",
        "",
        (
            f"- Train : `{corpus['train_pieces']}` chorals, "
            f"`{corpus['train_decisions']}` décisions."
        ),
        (
            f"- Validation : `{corpus['validation_pieces']}` chorals, "
            f"`{corpus['validation_decisions']}` décisions."
        ),
        f"- Ancien test : `{corpus['test_pieces_reserved']}` chorals non chargés.",
        (
            f"- Domaine commun train : MIDI `{corpus['candidate_min']}` à "
            f"`{corpus['candidate_max']}`."
        ),
        (
            "- Choix validation hors domaine : "
            f"`{corpus['validation_choices_outside_train_domain']}`."
        ),
        "",
        "## Modèle",
        "",
        f"- NLL validation registre seul : `{model['baseline_validation_nll']:.6f}`.",
        f"- Meilleure NLL validation : `{model['validation_nll']:.6f}`.",
        f"- Gain : `{model['validation_nll_gain']:.6f}`.",
        f"- Règles locales retenues : `{len(model['rules'])}`.",
        "",
        "| # | Clause numérique | Poids | z au moment de la sélection | Modalité |",
        "|---:|---|---:|---:|---|",
    ]
    for index, rule in enumerate(model["rules"], start=1):
        modality = "préférence" if rule["weight"] > 0 else "évitement"
        lines.append(
            f"| {index} | `{rule['feature']['label']}` | "
            f"{rule['weight']:+.6f} | {rule['selection']['z_score']:+.3f} | "
            f"{modality} |"
        )
    lines.extend(
        [
            "",
            "## Benchmark externe après gel",
            "",
        ]
    )
    for name, recovered in result["posthoc_known_rule_benchmark"].items():
        lines.append(f"- `{name}` : `{'retrouvé' if recovered else 'non retrouvé'}`")
    lines.extend(
        [
            "",
            "Ce benchmark ne change ni les colonnes ni les poids. Les absences sont",
            "des résultats négatifs du premier budget, pas des motifs d'ajustement",
            "manuel.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--max-rules", type=int, default=12)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--complexity-penalty", type=float, default=1.0)
    parser.add_argument("--min-testable", type=int, default=100)
    parser.add_argument("--min-piece-support", type=int, default=10)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if _sha256(args.archive) != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Historical corpus archive hash does not match")
    manifest, included, splits = _load_inputs(args.manifest, args.splits)
    train_ids = list(splits["train"])
    validation_ids = list(splits["validation"])
    if args.max_pieces is not None:
        train_count = max(2, int(args.max_pieces * 0.8))
        validation_count = max(1, args.max_pieces - train_count)
        train_ids = train_ids[:train_count]
        validation_ids = validation_ids[:validation_count]
    permitted = set(train_ids + validation_ids)
    selected_pieces = [piece for piece in included if piece["id"] in permitted]
    suffix = "full" if args.max_pieces is None else f"smoke-{args.max_pieces}"
    work = HERE / "work"
    cache = work / f"k3-train-validation-{suffix}.npz"
    if cache.exists():
        print(f"[k3-corpus] loading {cache}", flush=True)
        all_data = k3.load_k3_dataset(cache)
    else:
        score_paths = _materialize_scores(
            args.archive, selected_pieces, work / "scores"
        )
        all_data = k3.build_k3_dataset(score_paths)
        k3.save_k3_dataset(cache, all_data)

    train = k3.subset_for_piece_ids(all_data, train_ids)
    validation = k3.subset_for_piece_ids(all_data, validation_ids)
    candidate_min, candidate_max = k3.training_domain(train)
    train, train_removed = k3.filter_to_domain(train, candidate_min, candidate_max)
    validation, validation_removed = k3.filter_to_domain(
        validation, candidate_min, candidate_max
    )
    if train_removed:
        raise AssertionError("A train-derived domain removed train choices")
    if args.null_shuffle:
        train = k3.shuffle_choices_within_piece_and_voice(train, args.seed)
        validation = k3.shuffle_choices_within_piece_and_voice(
            validation, args.seed + 1
        )

    register_logits = k3.learn_register_logits(train)
    baseline_train = k3.conditional_nll(train, register_logits)
    baseline_validation = k3.conditional_nll(validation, register_logits)
    catalogue = k3.feature_catalogue()
    selected_features: list[k3.FeatureSpec] = []
    selected_statistics: list[k3.ResidualStatistic] = []
    weights = np.asarray([], dtype=np.float64)
    train_matrix = k3.feature_matrix(train, ())
    validation_matrix = k3.feature_matrix(validation, ())
    best_snapshot: tuple[
        list[k3.FeatureSpec],
        list[k3.ResidualStatistic],
        np.ndarray,
        np.ndarray,
        np.ndarray,
        float,
    ] = ([], [], weights, train_matrix, validation_matrix, baseline_validation)
    iterations = []

    for iteration in range(1, args.max_rules + 1):
        probs = k3.probabilities(train, register_logits, train_matrix, weights)
        selected_keys = {feature.key for feature in selected_features}
        ranked: list[
            tuple[float, k3.FeatureSpec, k3.ResidualStatistic, np.ndarray]
        ] = []
        for feature in catalogue:
            if feature.key in selected_keys:
                continue
            mask = k3.feature_mask(train, feature)
            statistic = k3.residual_statistic(
                train,
                probs,
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
        if not ranked:
            print("[k3-search] no admissible residual column", flush=True)
            break
        ranked.sort(key=lambda item: (item[0], item[1].key), reverse=True)
        _, feature, statistic, train_column = ranked[0]
        validation_column = k3.feature_mask(validation, feature)
        selected_features.append(feature)
        selected_statistics.append(statistic)
        train_matrix = _append_feature(train_matrix, train_column)
        validation_matrix = _append_feature(validation_matrix, validation_column)
        weights, fit = k3.fit_weights(
            train,
            validation,
            register_logits,
            train_matrix,
            validation_matrix,
            l1=args.l1,
            max_steps=args.max_steps,
            learning_rate=args.learning_rate,
        )
        train_nll = k3.conditional_nll(train, register_logits, train_matrix, weights)
        validation_nll = k3.conditional_nll(
            validation, register_logits, validation_matrix, weights
        )
        iterations.append(
            {
                "iteration": iteration,
                "feature": feature.to_dict(),
                "selection": _statistic_payload(statistic),
                "weights": weights.tolist(),
                "train_nll": train_nll,
                "validation_nll": validation_nll,
                "fit": fit,
            }
        )
        print(
            f"[k3-search] {iteration}/{args.max_rules} {feature.label} "
            f"z={statistic.z_score:+.2f} w={weights[-1]:+.3f} "
            f"val={validation_nll:.6f}",
            flush=True,
        )
        if validation_nll < best_snapshot[-1] - 1e-9:
            best_snapshot = (
                list(selected_features),
                list(selected_statistics),
                weights.copy(),
                train_matrix.copy(),
                validation_matrix.copy(),
                validation_nll,
            )

    (
        best_features,
        best_statistics,
        best_weights,
        best_train_matrix,
        best_validation_matrix,
        best_validation_nll,
    ) = best_snapshot
    best_train_nll = k3.conditional_nll(
        train, register_logits, best_train_matrix, best_weights
    )
    rules = [
        {
            "feature": feature.to_dict(),
            "weight": float(weight),
            "selection": _statistic_payload(statistic),
        }
        for feature, weight, statistic in zip(
            best_features, best_weights, best_statistics, strict=True
        )
    ]
    result = {
        "experiment": {
            "id": "V5-K3-CLEAN",
            "status": "EXPLORATORY",
            "initial_musical_rules": 0,
            "locality_blocks": 3,
            "old_test_loaded": False,
            "null_shuffle": args.null_shuffle,
            "seed": args.seed,
            "manifest_sha256": _sha256(args.manifest),
            "split_sha256": _sha256(args.splits),
            "archive_sha256": _sha256(args.archive),
            "catalogue_size": len(catalogue),
            "max_rules": args.max_rules,
            "max_steps": args.max_steps,
            "l1": args.l1,
            "learning_rate": args.learning_rate,
            "complexity_penalty": args.complexity_penalty,
        },
        "corpus": {
            "source_summary": manifest["summary"],
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
            "candidate_min": candidate_min,
            "candidate_max": candidate_max,
            "validation_choices_outside_train_domain": validation_removed,
        },
        "model": {
            "register_logits": register_logits.tolist(),
            "baseline_train_nll": baseline_train,
            "baseline_validation_nll": baseline_validation,
            "train_nll": best_train_nll,
            "validation_nll": best_validation_nll,
            "validation_nll_gain": baseline_validation - best_validation_nll,
            "rules": rules,
        },
        "search_iterations": iterations,
        "posthoc_known_rule_benchmark": _posthoc_benchmark(best_features),
    }
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    suffix = "_null" if args.null_shuffle else ""
    model_path = output / f"v5_1_k3_compact{suffix}_model.json"
    report_path = output / f"V5_1_K3_COMPACT{suffix.upper()}_REPORT.md"
    model_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown_report(result), encoding="utf-8")
    print(f"[k3-result] wrote {model_path}", flush=True)
    print(f"[k3-result] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
