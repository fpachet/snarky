#!/usr/bin/env python3
"""Induce the first post-generation family: simultaneous SATB voice order."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
POC = HERE.parent / "differentiable_rules_poc"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

import run_satb_level_a as satb  # noqa: E402

DEFAULT_CACHE = POC / "work" / "satb-opportunities-full.npz"
DEFAULT_SPLITS = POC / "results" / "splits.variant-safe.json"
DEFAULT_OUTPUT = HERE / "results"
THRESHOLDS = (-2, -1, 0, 1, 2)


def simultaneous_order_mask(
    opportunities: satb.VoiceOpportunities,
    threshold: int,
) -> np.ndarray:
    """Candidate leaves at most ``threshold`` semitones to an adjacent voice."""

    voice = opportunities.voice_index
    candidates = opportunities.candidate_pitches[None, :]
    masks = []
    if voice < 3:
        lower = opportunities.current_all[:, voice + 1, None]
        masks.append(candidates - lower <= threshold)
    if voice > 0:
        upper = opportunities.current_all[:, voice - 1, None]
        masks.append(upper - candidates <= threshold)
    if len(masks) == 1:
        return masks[0]
    return masks[0] | masks[1]


def _fit_baselines(
    train: Sequence[satb.VoiceOpportunities],
    validation: Sequence[satb.VoiceOpportunities],
    *,
    max_steps: int,
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    train_probabilities = []
    validation_probabilities = []
    diagnostics = []
    for train_voice, validation_voice in zip(train, validation, strict=True):
        print(
            f"[vertical-order] fitting {satb.VOICE_NAMES[train_voice.voice_index]}",
            flush=True,
        )
        train_probs, validation_probs, fit = satb.fit_voice_baseline(
            train_voice,
            validation_voice,
            0.001,
            max_steps,
            0.04,
        )
        train_probabilities.append(train_probs)
        validation_probabilities.append(validation_probs)
        diagnostics.append(fit)
    return train_probabilities, validation_probabilities, diagnostics


def _candidate(records: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    admissible = [
        record
        for record in records
        if record["train"]["z_score"] <= -3
        and record["validation"]["z_score"] <= -2
        and record["bootstrap_validation"]["negative_fraction"] >= 0.95
        and record["validation"]["local_log_rate_contrast"] is not None
    ]
    if not admissible:
        return None
    return min(
        admissible,
        key=lambda record: record["validation"]["local_log_rate_contrast"],
    )


def _conditional_nll(
    datasets: Sequence[satb.VoiceOpportunities],
    probabilities: Sequence[np.ndarray],
    masks: Sequence[np.ndarray],
    weight: float,
) -> float:
    total = 0.0
    decisions = 0
    for data, baseline, mask in zip(datasets, probabilities, masks, strict=True):
        logits = weight * mask
        scaled = baseline * np.exp(logits - logits.max(axis=1, keepdims=True))
        adjusted = scaled / scaled.sum(axis=1, keepdims=True)
        chosen = adjusted[np.arange(data.size), data.chosen_indices]
        total -= float(np.log(np.maximum(chosen, 1e-300)).sum())
        decisions += data.size
    return total / decisions


def _fit_one_weight(
    datasets: Sequence[satb.VoiceOpportunities],
    probabilities: Sequence[np.ndarray],
    masks: Sequence[np.ndarray],
) -> float:
    weight = 0.0
    for _ in range(40):
        gradient = 0.0
        variance = 0.0
        for data, baseline, mask in zip(datasets, probabilities, masks, strict=True):
            scaled = baseline * np.exp(weight * mask)
            adjusted = scaled / scaled.sum(axis=1, keepdims=True)
            expected = np.sum(adjusted * mask, axis=1)
            observed = mask[np.arange(data.size), data.chosen_indices].astype(
                np.float64
            )
            gradient += float(np.sum(observed - expected))
            variance += float(np.sum(expected * (1 - expected)))
        update = gradient / max(variance, 1e-12)
        weight = max(-20.0, min(20.0, weight + update))
        if abs(update) < 1e-8:
            break
    return weight


def _run_scan(
    train: Sequence[satb.VoiceOpportunities],
    validation: Sequence[satb.VoiceOpportunities],
    train_probabilities: Sequence[np.ndarray],
    validation_probabilities: Sequence[np.ndarray],
    *,
    seed: int,
    bootstrap_replicates: int,
) -> list[dict[str, Any]]:
    records = satb.scan_family(
        "simultaneous_adjacent_gap_le",
        THRESHOLDS,
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        simultaneous_order_mask,
        bootstrap_replicates,
        seed,
    )
    satb.add_local_log_rate_contrasts(records)
    return records


def _selection_payload(
    candidate: dict[str, Any] | None,
    train: Sequence[satb.VoiceOpportunities],
    validation: Sequence[satb.VoiceOpportunities],
    train_probabilities: Sequence[np.ndarray],
    validation_probabilities: Sequence[np.ndarray],
) -> dict[str, Any] | None:
    if candidate is None:
        return None
    threshold = int(candidate["numeric_value"])
    train_masks = [simultaneous_order_mask(data, threshold) for data in train]
    validation_masks = [simultaneous_order_mask(data, threshold) for data in validation]
    weight = _fit_one_weight(train, train_probabilities, train_masks)
    train_baseline = _conditional_nll(train, train_probabilities, train_masks, 0.0)
    validation_baseline = _conditional_nll(
        validation, validation_probabilities, validation_masks, 0.0
    )
    return {
        "threshold": threshold,
        "clause": (
            "candidate_upper - simultaneous_lower <= threshold OR "
            "simultaneous_upper - candidate_lower <= threshold"
        ),
        "fitted_weight": weight,
        "train_nll_gain": train_baseline
        - _conditional_nll(train, train_probabilities, train_masks, weight),
        "validation_nll_gain": validation_baseline
        - _conditional_nll(
            validation,
            validation_probabilities,
            validation_masks,
            weight,
        ),
        "evidence": candidate,
    }


def _report(result: dict[str, Any]) -> str:
    selection = result["authentic"]["selection"]
    null_selection = result["null_control"]["selection"]
    lines = [
        "# V4.2 — Induction de l'ordre simultané des voix",
        "",
        "Cette expérience exploratoire est déclenchée par les croisements et",
        "unissons des générations V4.1. Elle recherche uniformément cinq seuils",
        "numériques autour de la frontière zéro, sans consulter la règle",
        "historique correspondante.",
        "",
        "## Scan authentique",
        "",
        "| Seuil | z train | z validation | contraste local validation |",
        "|---:|---:|---:|---:|",
    ]
    for record in result["authentic"]["scan"]:
        contrast = record["validation"]["local_log_rate_contrast"]
        rendered_contrast = "—" if contrast is None else f"{contrast:.3f}"
        lines.append(
            f"| {record['numeric_value']} | "
            f"{record['train']['z_score']:.3f} | "
            f"{record['validation']['z_score']:.3f} | "
            f"{rendered_contrast} |"
        )
    lines.extend(["", "## Sélection", ""])
    if selection is None:
        lines.append("Aucun seuil n'est retenu.")
    else:
        lines.extend(
            [
                f"- seuil : `{selection['threshold']}` ;",
                f"- poids ajusté : `{selection['fitted_weight']:.6f}` ;",
                f"- gain NLL train : `{selection['train_nll_gain']:.6f}` ;",
                f"- gain NLL validation : `{selection['validation_nll_gain']:.6f}`.",
            ]
        )
    lines.extend(["", "## Contrôle nul", ""])
    if null_selection is None:
        lines.append("Aucun seuil n'est retenu après mélange intra-pièce.")
    else:
        lines.append(
            "Le contrôle retient le seuil "
            f"`{null_selection['threshold']}` : la famille doit rester candidate."
        )
    lines.extend(
        [
            "",
            "## Statut",
            "",
            "`CANDIDATE` : un seul mélange nul ne constitue pas une calibration",
            "familiale suffisante. La règle ne rejoint pas encore `S-LEARNED`.",
            "",
        ]
    )
    return "\n".join(lines)


def run(
    cache: Path,
    splits_path: Path,
    output: Path,
    *,
    seed: int,
    max_steps: int,
    bootstrap_replicates: int,
) -> dict[str, Any]:
    all_opportunities = satb.load_satb_opportunities(cache)
    splits = json.loads(splits_path.read_text(encoding="utf-8"))["grouped_split"]
    train = [
        satb.subset_for_piece_ids(data, splits["train"]) for data in all_opportunities
    ]
    validation = [
        satb.subset_for_piece_ids(data, splits["validation"])
        for data in all_opportunities
    ]
    train_probs, validation_probs, fits = _fit_baselines(
        train, validation, max_steps=max_steps
    )
    authentic_scan = _run_scan(
        train,
        validation,
        train_probs,
        validation_probs,
        seed=seed,
        bootstrap_replicates=bootstrap_replicates,
    )
    authentic_selection = _selection_payload(
        _candidate(authentic_scan),
        train,
        validation,
        train_probs,
        validation_probs,
    )

    shuffled_train = [
        satb.shuffle_choices_within_pieces(data, seed + 101 + voice)
        for voice, data in enumerate(train)
    ]
    shuffled_validation = [
        satb.shuffle_choices_within_pieces(data, seed + 202 + voice)
        for voice, data in enumerate(validation)
    ]
    null_train_probs, null_validation_probs, null_fits = _fit_baselines(
        shuffled_train,
        shuffled_validation,
        max_steps=max_steps,
    )
    null_scan = _run_scan(
        shuffled_train,
        shuffled_validation,
        null_train_probs,
        null_validation_probs,
        seed=seed + 50_000,
        bootstrap_replicates=bootstrap_replicates,
    )
    null_selection = _selection_payload(
        _candidate(null_scan),
        shuffled_train,
        shuffled_validation,
        null_train_probs,
        null_validation_probs,
    )
    result = {
        "schema_version": 1,
        "experiment": "V4.2-simultaneous-voice-order",
        "status": "exploratory",
        "family": {
            "thresholds": list(THRESHOLDS),
            "budget": 1,
            "selection": "most_negative_validation_local_log_rate_contrast",
        },
        "authentic": {
            "baseline_fits": fits,
            "scan": authentic_scan,
            "selection": authentic_selection,
        },
        "null_control": {
            "kind": "one_within_piece_choice_shuffle",
            "baseline_fits": null_fits,
            "scan": null_scan,
            "selection": null_selection,
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "v4_2_vertical_order_induction.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output / "V4_2_VERTICAL_ORDER_INDUCTION_REPORT.md").write_text(
        _report(result),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=4702)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    arguments = parser.parse_args()
    run(
        arguments.cache,
        arguments.splits,
        arguments.output,
        seed=arguments.seed,
        max_steps=arguments.max_steps,
        bootstrap_replicates=arguments.bootstrap_replicates,
    )


if __name__ == "__main__":
    main()
