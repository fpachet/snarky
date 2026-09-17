#!/usr/bin/env python3
"""Compress the tonal proxy hierarchy into interpretable harmonic statuses."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base
import run_satb_level_a as satb
import run_tonal_rule_ablation as ablation
import run_tonal_tendency as tonal

EXACT_STATUS_ID = ablation.HARMONIC_RULE_ID
VII_CORE_STATUS_ID = "TONAL_VII_CORE_TO_TONIC_CORE"
DOMINANT_CORE_STATUS_ID = "TONAL_DOMINANT_CORE_TO_TONIC_CORE"


@dataclass(frozen=True)
class StatusSpec:
    rule_id: str
    source_kind: str
    target_kind: str
    label: str
    predicate_atoms: int


STATUS_SPECS = (
    StatusSpec(
        EXACT_STATUS_ID,
        "exact_vii6",
        "exact_i6",
        "vii°6 exact vers I6 exact",
        7,
    ),
    StatusSpec(
        VII_CORE_STATUS_ID,
        "contains_vii_core",
        "contains_tonic_core",
        "noyau vii° avec ornements vers noyau tonique",
        7,
    ),
    StatusSpec(
        DOMINANT_CORE_STATUS_ID,
        "dominant_function_core",
        "contains_tonic_core",
        "fonction dominante locale vers noyau tonique",
        7,
    ),
)

MODEL_METADATA = {
    "baseline": {"parameter_count": 0, "predicate_atoms": 0, "rule_count": 0},
    "proxy": {"parameter_count": 1, "predicate_atoms": 5, "rule_count": 1},
    "exact": {"parameter_count": 1, "predicate_atoms": 7, "rule_count": 1},
    "both": {"parameter_count": 2, "predicate_atoms": 12, "rule_count": 2},
    "vii_core": {"parameter_count": 1, "predicate_atoms": 7, "rule_count": 1},
    "dominant_core": {
        "parameter_count": 1,
        "predicate_atoms": 7,
        "rule_count": 1,
    },
    "graded_exact": {
        "parameter_count": 1,
        "predicate_atoms": 8,
        "rule_count": 1,
    },
    "graded_vii_core": {
        "parameter_count": 1,
        "predicate_atoms": 8,
        "rule_count": 1,
    },
    "graded_dominant_core": {
        "parameter_count": 1,
        "predicate_atoms": 8,
        "rule_count": 1,
    },
}

CROSSFIT_MODELS = (
    "baseline",
    "proxy",
    "both",
    "graded_exact",
    "graded_vii_core",
    "graded_dominant_core",
)


def contains_signature_rows(
    states: np.ndarray,
    tonics: np.ndarray,
    required_classes: tuple[int, ...],
) -> np.ndarray:
    relative = (states - tonics[:, None]) % 12
    return np.stack(
        [(relative == value).any(axis=1) for value in required_classes],
        axis=1,
    ).all(axis=1)


def dominant_function_rows(states: np.ndarray, tonics: np.ndarray) -> np.ndarray:
    """Recognize a minimal leading-tone or dominant core above bass degree 2."""

    relative = (states - tonics[:, None]) % 12
    has_leading_tone = (relative == 11).any(axis=1)
    has_bass_degree = (relative == 2).any(axis=1)
    has_dominant_colour = (relative == 5).any(axis=1) | (
        relative == 7
    ).any(axis=1)
    return has_leading_tone & has_bass_degree & has_dominant_colour


def candidate_target_contains_mask(
    opportunities: satb.VoiceOpportunities,
    tonics: np.ndarray,
    required_classes: tuple[int, ...],
) -> np.ndarray:
    candidates = opportunities.candidate_pitches
    other_indices = [
        voice for voice in range(4) if voice != opportunities.voice_index
    ]
    other = (
        opportunities.current_all[:, other_indices] - tonics[:, None]
    ) % 12
    candidate_relative = (candidates[None, :] - tonics[:, None]) % 12
    present = np.ones(candidate_relative.shape, dtype=np.bool_)
    for value in required_classes:
        present &= (other == value).any(axis=1)[:, None] | (
            candidate_relative == value
        )
    return present


def status_rule_mask(
    opportunities: satb.VoiceOpportunities,
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
    spec: StatusSpec,
) -> np.ndarray:
    shape = (opportunities.size, opportunities.candidate_pitches.size)
    if opportunities.voice_index != 1:
        return np.zeros(shape, dtype=np.bool_)
    tonics = np.asarray(
        [tonic_by_piece[piece_id] for piece_id in opportunities.piece_ids],
        dtype=np.int16,
    )
    proxy = ablation.proxy_rule_mask(
        opportunities,
        tonic_by_piece,
        mode_by_piece,
    )
    if spec.source_kind == "exact_vii6":
        source = ablation.exact_signature_rows(
            opportunities.previous_all,
            tonics,
            (2, 5, 11),
        )
    elif spec.source_kind == "contains_vii_core":
        source = contains_signature_rows(
            opportunities.previous_all,
            tonics,
            (2, 5, 11),
        )
    elif spec.source_kind == "dominant_function_core":
        source = dominant_function_rows(opportunities.previous_all, tonics)
    else:
        raise ValueError(spec.source_kind)

    if spec.target_kind == "exact_i6":
        target = ablation.candidate_target_signature_mask(
            opportunities,
            tonics,
            (0, 4, 7),
        )
    elif spec.target_kind == "contains_tonic_core":
        target = candidate_target_contains_mask(
            opportunities,
            tonics,
            (0, 4, 7),
        )
    else:
        raise ValueError(spec.target_kind)
    return proxy & source[:, None] & target


def feature_masks(
    opportunities: satb.VoiceOpportunities,
    tonic_by_piece: dict[str, int],
    mode_by_piece: dict[str, str],
) -> dict[str, np.ndarray]:
    masks = {
        ablation.PROXY_RULE_ID: ablation.proxy_rule_mask(
            opportunities,
            tonic_by_piece,
            mode_by_piece,
        )
    }
    for spec in STATUS_SPECS:
        masks[spec.rule_id] = status_rule_mask(
            opportunities,
            tonic_by_piece,
            mode_by_piece,
            spec,
        )
        if not np.all(masks[spec.rule_id] <= masks[ablation.PROXY_RULE_ID]):
            raise AssertionError(f"{spec.rule_id} must be nested in proxy")
    return masks


def model_rule_columns(
    model_name: str,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray | None, list[str]]:
    proxy = masks[ablation.PROXY_RULE_ID].astype(np.float32)
    exact = masks[EXACT_STATUS_ID].astype(np.float32)
    vii_core = masks[VII_CORE_STATUS_ID].astype(np.float32)
    dominant_core = masks[DOMINANT_CORE_STATUS_ID].astype(np.float32)
    if model_name == "baseline":
        return None, []
    if model_name == "proxy":
        return proxy[:, :, None], [ablation.PROXY_RULE_ID]
    if model_name == "exact":
        return exact[:, :, None], [EXACT_STATUS_ID]
    if model_name == "both":
        return np.stack((proxy, exact), axis=2), [
            ablation.PROXY_RULE_ID,
            EXACT_STATUS_ID,
        ]
    if model_name == "vii_core":
        return vii_core[:, :, None], [VII_CORE_STATUS_ID]
    if model_name == "dominant_core":
        return dominant_core[:, :, None], [DOMINANT_CORE_STATUS_ID]
    if model_name == "graded_exact":
        return (proxy + exact)[:, :, None], [
            f"GRADED({ablation.PROXY_RULE_ID}+{EXACT_STATUS_ID})"
        ]
    if model_name == "graded_vii_core":
        return (proxy + vii_core)[:, :, None], [
            f"GRADED({ablation.PROXY_RULE_ID}+{VII_CORE_STATUS_ID})"
        ]
    if model_name == "graded_dominant_core":
        return (proxy + dominant_core)[:, :, None], [
            f"GRADED({ablation.PROXY_RULE_ID}+{DOMINANT_CORE_STATUS_ID})"
        ]
    raise ValueError(model_name)


def description_bits(model_name: str) -> int:
    metadata = MODEL_METADATA[model_name]
    return int(
        32 * metadata["parameter_count"]
        + 12 * metadata["predicate_atoms"]
        + 16 * metadata["rule_count"]
    )


def duplicate_components(
    piece_ids: list[str],
    split_payload: dict[str, Any],
) -> list[list[str]]:
    parent = {piece_id: piece_id for piece_id in piece_ids}

    def find(piece_id: str) -> str:
        while parent[piece_id] != piece_id:
            parent[piece_id] = parent[parent[piece_id]]
            piece_id = parent[piece_id]
        return piece_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    allowed = set(piece_ids)
    for record in split_payload["audit"]["soprano_duplicate_groups"]:
        members = [piece for piece in record["members"] if piece in allowed]
        for member in members[1:]:
            union(members[0], member)
    components: dict[str, list[str]] = {}
    for piece_id in piece_ids:
        components.setdefault(find(piece_id), []).append(piece_id)
    return [sorted(members) for members in components.values()]


def grouped_piece_folds(
    opportunities: satb.VoiceOpportunities,
    piece_ids: list[str],
    split_payload: dict[str, Any],
    fold_count: int,
    seed: int,
) -> list[list[str]]:
    components = duplicate_components(piece_ids, split_payload)
    row_counts = {
        piece_id: int(np.sum(opportunities.piece_ids == piece_id))
        for piece_id in piece_ids
    }
    generator = np.random.default_rng(seed)
    tie_breakers = generator.random(len(components))
    ordered = sorted(
        zip(components, tie_breakers, strict=True),
        key=lambda item: (
            -sum(row_counts[piece] for piece in item[0]),
            item[1],
        ),
    )
    folds: list[list[str]] = [[] for _ in range(fold_count)]
    fold_loads = np.zeros(fold_count, dtype=np.int64)
    for component, _ in ordered:
        fold_index = int(np.argmin(fold_loads))
        folds[fold_index].extend(component)
        fold_loads[fold_index] += sum(row_counts[piece] for piece in component)
    return [sorted(fold) for fold in folds]


def append_columns(
    baseline: np.ndarray,
    columns: np.ndarray | None,
) -> np.ndarray:
    if columns is None:
        return baseline
    return np.concatenate((baseline, columns), axis=2)


def fit_without_holdout_selection(
    train_matrix: np.ndarray,
    chosen_indices: np.ndarray,
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    return base.fit_sparse_conditional_model(
        train_matrix,
        chosen_indices,
        train_matrix,
        chosen_indices,
        l1=l1,
        max_steps=max_steps,
        learning_rate=learning_rate,
    )


def evaluate_models(
    train: satb.VoiceOpportunities,
    validation: satb.VoiceOpportunities,
    train_masks: dict[str, np.ndarray],
    validation_masks: dict[str, np.ndarray],
    folds: list[list[str]],
    l1: float,
    max_steps: int,
    learning_rate: float,
    bootstrap_replicates: int,
    seed: int,
) -> dict[str, Any]:
    train_baseline = satb.baseline_matrix(train)
    validation_baseline = satb.baseline_matrix(validation)
    records: dict[str, Any] = {}
    crossfit_losses: dict[str, np.ndarray] = {}
    for model_name in MODEL_METADATA:
        print(f"[harmonic-compression] fitting {model_name}", flush=True)
        train_columns, rule_ids = model_rule_columns(model_name, train_masks)
        validation_columns, _ = model_rule_columns(
            model_name,
            validation_masks,
        )
        train_matrix = append_columns(train_baseline, train_columns)
        validation_matrix = append_columns(
            validation_baseline,
            validation_columns,
        )
        weights, diagnostics = fit_without_holdout_selection(
            train_matrix,
            train.chosen_indices,
            l1,
            max_steps,
            learning_rate,
        )
        validation_losses = ablation.row_nll(
            validation_matrix,
            validation.chosen_indices,
            weights,
        )
        record = {
            **MODEL_METADATA[model_name],
            "description_bits": description_bits(model_name),
            "rule_ids": rule_ids,
            "train_nll": base.conditional_nll(
                train_matrix,
                train.chosen_indices,
                weights,
            ),
            "validation_nll": float(validation_losses.mean()),
            "rule_weights": [
                float(weight)
                for weight in (
                    weights[-len(rule_ids) :]
                    if rule_ids
                    else np.asarray([], dtype=np.float64)
                )
            ],
            "fit": diagnostics,
        }
        if model_name in CROSSFIT_MODELS:
            pooled = np.full(train.size, np.nan, dtype=np.float64)
            fold_records = []
            for fold_index, heldout_pieces in enumerate(folds):
                heldout = np.isin(train.piece_ids, heldout_pieces)
                fitted = ~heldout
                fold_weights, _ = fit_without_holdout_selection(
                    train_matrix[fitted],
                    train.chosen_indices[fitted],
                    l1,
                    max_steps,
                    learning_rate,
                )
                fold_losses = ablation.row_nll(
                    train_matrix[heldout],
                    train.chosen_indices[heldout],
                    fold_weights,
                )
                pooled[heldout] = fold_losses
                fold_records.append(
                    {
                        "fold": fold_index,
                        "fit_pieces": int(
                            np.unique(train.piece_ids[fitted]).size
                        ),
                        "heldout_pieces": int(
                            np.unique(train.piece_ids[heldout]).size
                        ),
                        "heldout_opportunities": int(heldout.sum()),
                        "heldout_nll": float(fold_losses.mean()),
                    }
                )
            if np.isnan(pooled).any():
                raise AssertionError("Cross-fitting left rows unevaluated")
            crossfit_losses[model_name] = pooled
            record["crossfit_nll"] = float(pooled.mean())
            record["crossfit_folds"] = fold_records
        records[model_name] = record

    baseline_losses = crossfit_losses["baseline"]
    both_gain = float(
        baseline_losses.mean() - crossfit_losses["both"].mean()
    )
    for model_index, model_name in enumerate(CROSSFIT_MODELS):
        losses = crossfit_losses[model_name]
        gain = float(baseline_losses.mean() - losses.mean())
        records[model_name]["crossfit_gain_vs_baseline"] = gain
        records[model_name]["crossfit_gain_retention_vs_both"] = (
            gain / both_gain if both_gain > 0 else 0.0
        )
        records[model_name]["bootstrap_vs_baseline"] = (
            ablation.bootstrap_nll_gain_by_piece(
                baseline_losses,
                losses,
                train.piece_ids,
                bootstrap_replicates,
                seed + model_index,
            )
        )
    return {
        "records": records,
        "crossfit_losses": crossfit_losses,
    }


def select_compressed_model(
    records: dict[str, Any],
    minimum_gain_retention: float,
) -> dict[str, Any]:
    candidates = []
    for model_name in CROSSFIT_MODELS:
        if model_name in {"baseline", "both"}:
            continue
        record = records[model_name]
        bootstrap = record["bootstrap_vs_baseline"]
        eligible = (
            record["parameter_count"] == 1
            and record["crossfit_gain_retention_vs_both"]
            >= minimum_gain_retention
            and bootstrap["gain_p025"] > 0
        )
        candidates.append(
            {
                "model": model_name,
                "eligible": eligible,
                "crossfit_nll": record["crossfit_nll"],
                "gain_retention": record[
                    "crossfit_gain_retention_vs_both"
                ],
                "description_bits": record["description_bits"],
                "bootstrap_gain_p025": bootstrap["gain_p025"],
            }
        )
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    selected = (
        min(
            eligible,
            key=lambda candidate: (
                candidate["description_bits"],
                candidate["crossfit_nll"],
            ),
        )["model"]
        if eligible
        else None
    )
    return {
        "minimum_gain_retention": minimum_gain_retention,
        "selected_model": selected,
        "candidates": candidates,
    }


def relative_signature(pitches: np.ndarray, tonic: int) -> list[int]:
    return sorted({int((pitch - tonic) % 12) for pitch in pitches})


def audit_atypical_rows(
    data: satb.VoiceOpportunities,
    masks: dict[str, np.ndarray],
    tonic_by_piece: dict[str, int],
) -> dict[str, Any]:
    proxy_rows = masks[ablation.PROXY_RULE_ID].any(axis=1)
    exact_rows = masks[EXACT_STATUS_ID].any(axis=1)
    chosen_exact = masks[EXACT_STATUS_ID][
        np.arange(data.size),
        data.chosen_indices,
    ]
    exact_exceptions = exact_rows & ~chosen_exact
    proxy_only = proxy_rows & ~exact_rows
    atypical = proxy_only | exact_exceptions
    rows = []
    for index in np.flatnonzero(atypical):
        piece_id = str(data.piece_ids[index])
        tonic = tonic_by_piece[piece_id]
        resolved_target = data.current_all[index].copy()
        resolved_target[data.voice_index] = data.previous_pitch[index] + 1
        rows.append(
            {
                "piece_id": piece_id,
                "offset_previous": float(data.offsets_previous[index]),
                "offset_current": float(data.offsets_current[index]),
                "category": (
                    "exact_context_exception"
                    if exact_exceptions[index]
                    else "proxy_only"
                ),
                "resolved": bool(
                    data.chosen_pitch[index]
                    == data.previous_pitch[index] + 1
                ),
                "source_signature": relative_signature(
                    data.previous_all[index],
                    tonic,
                ),
                "observed_target_signature": relative_signature(
                    data.current_all[index],
                    tonic,
                ),
                "resolved_candidate_target_signature": relative_signature(
                    resolved_target,
                    tonic,
                ),
                "status_membership": {
                    spec.rule_id: bool(masks[spec.rule_id][index].any())
                    for spec in STATUS_SPECS
                },
            }
        )
    return {
        "proxy_opportunities": int(proxy_rows.sum()),
        "exact_status_opportunities": int(exact_rows.sum()),
        "proxy_only_count": int(proxy_only.sum()),
        "exact_context_exception_count": int(exact_exceptions.sum()),
        "atypical_count": int(atypical.sum()),
        "rows": rows,
    }


def coverage(
    data: satb.VoiceOpportunities,
    masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    return {
        rule_id: ablation.selected_rate(data, mask)
        for rule_id, mask in masks.items()
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# POC V3.7 — compression des statuts harmoniques",
        "",
        "## Protocole",
        "",
        f"- Contrôle nul : `{result['experiment']['null_shuffle']}`.",
        "- Cinq plis par groupes de chorals, sans sélection sur le pli tenu à part.",
        "- Les groupes de sopranos dupliqués restent dans le même pli.",
        "- Gradient conditionnel Adam avec parcimonie L1.",
        "- Bootstrap par chorals entiers à pertes cross-fittées fixes.",
        "- Test final non ouvert.",
        "",
        "## Audit des cas atypiques",
        "",
    ]
    for split_name in ("train", "validation"):
        audit = result["atypical_audit"][split_name]
        lines.append(
            f"- {split_name} : {audit['proxy_only_count']} cas proxy seuls, "
            f"{audit['exact_context_exception_count']} exceptions du contexte "
            f"exact, soit {audit['atypical_count']} cas atypiques."
        )
    lines.extend(
        [
            "",
            "## Modèles",
            "",
            "| Modèle | Paramètres | Bits descriptifs | NLL cross-fit | "
            "Gain conservé | NLL validation |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    records = result["models"]
    for model_name in MODEL_METADATA:
        record = records[model_name]
        crossfit = (
            f"{record['crossfit_nll']:.6f}"
            if "crossfit_nll" in record
            else "—"
        )
        retention = (
            f"{record['crossfit_gain_retention_vs_both']:.3f}"
            if "crossfit_gain_retention_vs_both" in record
            else "—"
        )
        lines.append(
            f"| {model_name} | {record['parameter_count']} | "
            f"{record['description_bits']} | {crossfit} | {retention} | "
            f"{record['validation_nll']:.6f} |"
        )
    selection = result["selection"]
    lines.extend(
        [
            "",
            "## Sélection gelable",
            "",
            f"Modèle retenu : `{selection['selected_model']}`.",
            (
                "Seuil de conservation du gain cross-fitté : "
                f"`{selection['minimum_gain_retention']:.3f}`."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = base.experiment_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=base.default_archive_path())
    parser.add_argument("--manifest", type=Path, default=base.default_manifest_path())
    parser.add_argument(
        "--splits",
        type=Path,
        default=column.default_variant_safe_splits_path(),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--minimum-gain-retention", type=float, default=0.95)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--results-dir", type=Path, default=root / "results")
    parser.add_argument(
        "--output-stem",
        default="v3_7_harmonic_feature_compression",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
    archive = args.archive.resolve()
    if base.sha256_file(archive) != base.EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Unexpected corpus archive")
    manifest, included_pieces = base.load_included_pieces(args.manifest.resolve())
    split_path = args.splits.resolve()
    split_payload = json.loads(split_path.read_text(encoding="utf-8"))
    splits, split_metadata = column.load_experiment_splits(
        [piece["id"] for piece in included_pieces],
        args.seed,
        split_path,
    )
    discovery_ids = set(splits["train"] + splits["validation"])
    score_paths = base.materialize_scores(
        archive,
        [piece for piece in included_pieces if piece["id"] in discovery_ids],
        root / "work/scores",
    )
    tonic_by_piece, mode_by_piece, tonal_audit = tonal.build_tonal_status_maps(
        score_paths
    )
    alto = satb.load_satb_opportunities(
        root / "work/satb-opportunities-full.npz"
    )[1]
    train = satb.subset_for_piece_ids(alto, splits["train"])
    validation = satb.subset_for_piece_ids(alto, splits["validation"])
    if args.null_shuffle:
        train = satb.shuffle_choices_within_pieces(train, args.seed + 307)
        validation = satb.shuffle_choices_within_pieces(
            validation,
            args.seed + 401,
        )
    train_masks = feature_masks(train, tonic_by_piece, mode_by_piece)
    validation_masks = feature_masks(
        validation,
        tonic_by_piece,
        mode_by_piece,
    )
    folds = grouped_piece_folds(
        train,
        splits["train"],
        split_payload,
        args.fold_count,
        args.seed + 503,
    )
    evaluation = evaluate_models(
        train,
        validation,
        train_masks,
        validation_masks,
        folds,
        args.l1,
        args.max_steps,
        args.learning_rate,
        args.bootstrap_replicates,
        args.seed + 601,
    )
    records = evaluation["records"]
    selection = select_compressed_model(
        records,
        args.minimum_gain_retention,
    )
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_7_harmonic_compression",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "fold_count": args.fold_count,
            "max_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
            "bootstrap_replicates": args.bootstrap_replicates,
            "split_strategy": split_metadata["strategy"],
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "music21": __import__("music21").__version__,
        },
        "source": {
            "archive": str(archive),
            "archive_sha256": base.sha256_file(archive),
            "manifest": str(args.manifest.resolve()),
            "manifest_schema_version": manifest["schema_version"],
            "split": str(split_path),
            "split_sha256": base.sha256_file(split_path),
            "v3_6": str(
                root / "results/v3_6_tonal_rule_ablation.json"
            ),
            "v3_6_sha256": base.sha256_file(
                root / "results/v3_6_tonal_rule_ablation.json"
            ),
        },
        "tonal_status_audit": tonal_audit,
        "corpus": {
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_alto_opportunities": train.size,
            "validation_alto_opportunities": validation.size,
            "test_opened": False,
        },
        "folds": [
            {
                "fold": index,
                "piece_count": len(piece_ids),
                "piece_ids": piece_ids,
            }
            for index, piece_ids in enumerate(folds)
        ],
        "status_specs": [
            {
                "rule_id": spec.rule_id,
                "source_kind": spec.source_kind,
                "target_kind": spec.target_kind,
                "label": spec.label,
                "predicate_atoms": spec.predicate_atoms,
            }
            for spec in STATUS_SPECS
        ],
        "coverage": {
            "train": coverage(train, train_masks),
            "validation": coverage(validation, validation_masks),
        },
        "atypical_audit": {
            "train": audit_atypical_rows(
                train,
                train_masks,
                tonic_by_piece,
            ),
            "validation": audit_atypical_rows(
                validation,
                validation_masks,
                tonic_by_piece,
            ),
        },
        "models": records,
        "selection": selection,
    }
    results_dir = args.results_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / f"{args.output_stem}.json"
    report_path = results_dir / f"{args.output_stem.upper()}_REPORT.md"
    base.json_dump(json_path, result)
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"[done] wrote {json_path}", flush=True)
    print(f"[done] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
