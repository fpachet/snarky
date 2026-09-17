#!/usr/bin/env python3
"""Blind recovery of simple melodic and voice-order constraints in all SATB voices.

The learner is deliberately given only numeric MIDI relations.  Four sparse
conditional choice models absorb register and generic melodic motion.  Their
likelihood residuals then rank two uniformly enumerated numeric families:

* absolute melodic interval sizes;
* signed depths relative to the preceding note of an adjacent voice.

Musicological names and reference rules are consulted only after selection.
The grouped test split is never loaded or evaluated.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import run_column_generation as column
import run_poc as base

VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
VOICE_RANGES = ((60, 81), (55, 74), (48, 69), (36, 60))


@dataclass
class VoiceOpportunities:
    """Contiguous melodic choices for one voice with the surrounding SATB state."""

    piece_ids: np.ndarray
    offsets_previous: np.ndarray
    offsets_current: np.ndarray
    previous_pitch: np.ndarray
    chosen_pitch: np.ndarray
    previous_all: np.ndarray
    current_all: np.ndarray
    voice_index: int
    candidate_min: int
    candidate_max: int

    @property
    def candidate_pitches(self) -> np.ndarray:
        return np.arange(self.candidate_min, self.candidate_max + 1, dtype=np.int16)

    @property
    def chosen_indices(self) -> np.ndarray:
        return (self.chosen_pitch - self.candidate_min).astype(np.int64)

    @property
    def size(self) -> int:
        return int(self.chosen_pitch.shape[0])

    def take(self, indices: np.ndarray) -> VoiceOpportunities:
        return VoiceOpportunities(
            piece_ids=self.piece_ids[indices],
            offsets_previous=self.offsets_previous[indices],
            offsets_current=self.offsets_current[indices],
            previous_pitch=self.previous_pitch[indices],
            chosen_pitch=self.chosen_pitch[indices],
            previous_all=self.previous_all[indices],
            current_all=self.current_all[indices],
            voice_index=self.voice_index,
            candidate_min=self.candidate_min,
            candidate_max=self.candidate_max,
        )


@dataclass(frozen=True)
class ResidualEvidence:
    """Observed-minus-expected evidence for one Boolean candidate column."""

    residual_sum: float
    variance: float
    z_score: float
    observed_rate: float
    expected_rate: float
    testable_opportunities: int
    piece_support: int


def _rows_to_opportunities(
    rows: list[tuple[str, float, float, int, int, tuple[int, ...], tuple[int, ...]]],
    voice_index: int,
) -> VoiceOpportunities:
    candidate_min, candidate_max = VOICE_RANGES[voice_index]
    columns = list(zip(*rows, strict=True))
    return VoiceOpportunities(
        piece_ids=np.asarray(columns[0], dtype=str),
        offsets_previous=np.asarray(columns[1], dtype=np.float32),
        offsets_current=np.asarray(columns[2], dtype=np.float32),
        previous_pitch=np.asarray(columns[3], dtype=np.int16),
        chosen_pitch=np.asarray(columns[4], dtype=np.int16),
        previous_all=np.asarray(columns[5], dtype=np.int16),
        current_all=np.asarray(columns[6], dtype=np.int16),
        voice_index=voice_index,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )


def extract_piece_satb(
    score_path: Path,
    piece_id: str,
) -> list[list[tuple[str, float, float, int, int, tuple[int, ...], tuple[int, ...]]]]:
    """Extract note-to-note decisions for every voice in one score."""

    from music21 import converter

    score = converter.parse(score_path)
    parts = {part.partName: part for part in score.parts}
    if set(parts) != set(VOICE_NAMES):
        raise ValueError(f"{piece_id}: unexpected parts {tuple(parts)}")
    events = [base.note_events(parts[name]) for name in VOICE_NAMES]
    by_voice: list[
        list[tuple[str, float, float, int, int, tuple[int, ...], tuple[int, ...]]]
    ] = [[] for _ in VOICE_NAMES]

    for voice_index, voice_events in enumerate(events):
        candidate_min, candidate_max = VOICE_RANGES[voice_index]
        previous_note: tuple[float, float, int | None] | None = None
        for current in voice_events:
            current_start, _, current_pitch = current
            if current_pitch is None:
                previous_note = None
                continue
            if previous_note is None or previous_note[2] is None:
                previous_note = current
                continue
            previous_start, previous_end, previous_pitch_or_none = previous_note
            if abs(previous_end - current_start) > 1e-7:
                previous_note = current
                continue
            previous_pitch = int(previous_pitch_or_none)
            previous_state = tuple(
                base.sounding_pitch(other_events, previous_start)
                for other_events in events
            )
            current_state = tuple(
                base.sounding_pitch(other_events, current_start)
                for other_events in events
            )
            if any(pitch is None for pitch in (*previous_state, *current_state)):
                previous_note = current
                continue
            if not candidate_min <= current_pitch <= candidate_max:
                previous_note = current
                continue
            by_voice[voice_index].append(
                (
                    piece_id,
                    previous_start,
                    current_start,
                    previous_pitch,
                    current_pitch,
                    tuple(int(pitch) for pitch in previous_state),
                    tuple(int(pitch) for pitch in current_state),
                )
            )
            previous_note = current
    return by_voice


def build_satb_opportunities(
    score_paths: dict[str, Path],
) -> list[VoiceOpportunities]:
    """Parse the corpus once and construct four aligned choice datasets."""

    rows: list[
        list[tuple[str, float, float, int, int, tuple[int, ...], tuple[int, ...]]]
    ] = [[] for _ in VOICE_NAMES]
    for index, (piece_id, score_path) in enumerate(
        sorted(score_paths.items()), start=1
    ):
        piece_rows = extract_piece_satb(score_path, piece_id)
        for voice_index in range(4):
            rows[voice_index].extend(piece_rows[voice_index])
        if index % 25 == 0 or index == len(score_paths):
            counts = ", ".join(
                f"{VOICE_NAMES[voice][0]}={len(rows[voice])}" for voice in range(4)
            )
            print(
                f"[satb-corpus] parsed {index}/{len(score_paths)} pieces ({counts})",
                flush=True,
            )
    if any(not voice_rows for voice_rows in rows):
        raise RuntimeError("At least one SATB voice has no extracted opportunities")
    return [
        _rows_to_opportunities(voice_rows, voice_index)
        for voice_index, voice_rows in enumerate(rows)
    ]


def save_satb_opportunities(
    path: Path,
    opportunities: Sequence[VoiceOpportunities],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays: dict[str, np.ndarray] = {}
    for voice, data in enumerate(opportunities):
        prefix = f"v{voice}_"
        arrays.update(
            {
                prefix + "piece_ids": data.piece_ids,
                prefix + "offsets_previous": data.offsets_previous,
                prefix + "offsets_current": data.offsets_current,
                prefix + "previous_pitch": data.previous_pitch,
                prefix + "chosen_pitch": data.chosen_pitch,
                prefix + "previous_all": data.previous_all,
                prefix + "current_all": data.current_all,
            }
        )
    np.savez_compressed(path, **arrays)


def load_satb_opportunities(path: Path) -> list[VoiceOpportunities]:
    archive = np.load(path)
    result = []
    for voice_index, (candidate_min, candidate_max) in enumerate(VOICE_RANGES):
        prefix = f"v{voice_index}_"
        result.append(
            VoiceOpportunities(
                piece_ids=archive[prefix + "piece_ids"],
                offsets_previous=archive[prefix + "offsets_previous"],
                offsets_current=archive[prefix + "offsets_current"],
                previous_pitch=archive[prefix + "previous_pitch"],
                chosen_pitch=archive[prefix + "chosen_pitch"],
                previous_all=archive[prefix + "previous_all"],
                current_all=archive[prefix + "current_all"],
                voice_index=voice_index,
                candidate_min=candidate_min,
                candidate_max=candidate_max,
            )
        )
    return result


def subset_for_piece_ids(
    opportunities: VoiceOpportunities,
    piece_ids: Iterable[str],
) -> VoiceOpportunities:
    selected = np.isin(opportunities.piece_ids, np.asarray(list(piece_ids)))
    return opportunities.take(np.flatnonzero(selected))


def shuffle_choices_within_pieces(
    opportunities: VoiceOpportunities,
    seed: int,
) -> VoiceOpportunities:
    """Break local relations while preserving each piece/voice pitch histogram."""

    shuffled = opportunities.take(np.arange(opportunities.size))
    shuffled.chosen_pitch = shuffled.chosen_pitch.copy()
    generator = np.random.default_rng(seed)
    for piece_id in np.unique(shuffled.piece_ids):
        indices = np.flatnonzero(shuffled.piece_ids == piece_id)
        shuffled.chosen_pitch[indices] = generator.permutation(
            shuffled.chosen_pitch[indices]
        )
    return shuffled


def baseline_matrix(opportunities: VoiceOpportunities) -> np.ndarray:
    """Generic nuisance model without either searched Boolean predicate.

    Simultaneous interval classes absorb local key/harmony.  Linear and
    quadratic oriented separations absorb smooth voice-spacing effects but do
    not expose the zero crossing boundary used by the overlap scan.
    """

    candidates = opportunities.candidate_pitches[None, :]
    previous = opportunities.previous_pitch[:, None]
    delta = candidates - previous
    features = [candidates == pitch for pitch in opportunities.candidate_pitches]
    features.extend(np.sign(delta) == direction for direction in (-1, 0, 1))
    features.extend(np.abs(delta) > threshold for threshold in (1, 2, 4, 7, 12))
    for other_voice in range(4):
        if other_voice == opportunities.voice_index:
            continue
        harmonic_class = (
            np.abs(candidates - opportunities.current_all[:, other_voice, None]) % 12
        )
        features.extend(
            harmonic_class == interval_class for interval_class in range(12)
        )
    if opportunities.voice_index < 3:
        separation = (
            candidates
            - opportunities.previous_all[:, opportunities.voice_index + 1, None]
        ) / 12.0
        features.extend((separation, separation**2))
    if opportunities.voice_index > 0:
        separation = (
            opportunities.previous_all[:, opportunities.voice_index - 1, None]
            - candidates
        ) / 12.0
        features.extend((separation, separation**2))
    shape = delta.shape
    return np.stack(
        [np.broadcast_to(feature, shape) for feature in features],
        axis=2,
    ).astype(np.float32)


def fit_voice_baseline(
    train: VoiceOpportunities,
    validation: VoiceOpportunities,
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    train_matrix = baseline_matrix(train)
    validation_matrix = baseline_matrix(validation)
    weights, diagnostics = base.fit_sparse_conditional_model(
        train_matrix,
        train.chosen_indices,
        validation_matrix,
        validation.chosen_indices,
        l1=l1,
        max_steps=max_steps,
        learning_rate=learning_rate,
    )
    return (
        base.probabilities(train_matrix, weights),
        base.probabilities(validation_matrix, weights),
        {
            "voice": VOICE_NAMES[train.voice_index],
            "feature_count": int(train_matrix.shape[2]),
            "train_nll": base.conditional_nll(
                train_matrix, train.chosen_indices, weights
            ),
            "validation_nll": base.conditional_nll(
                validation_matrix, validation.chosen_indices, weights
            ),
            "active_weights": int((np.abs(weights) >= 0.05).sum()),
            "fit": diagnostics,
        },
    )


def melodic_interval_mask(
    opportunities: VoiceOpportunities,
    interval_class: int,
) -> np.ndarray:
    candidates = opportunities.candidate_pitches[None, :]
    return (
        np.abs(candidates - opportunities.previous_pitch[:, None]) % 12
        == interval_class
    )


def overlap_depth_mask(
    opportunities: VoiceOpportunities,
    threshold: int,
) -> np.ndarray | None:
    """Candidate crosses the preceding adjacent voice by more than threshold."""

    voice = opportunities.voice_index
    candidates = opportunities.candidate_pitches[None, :]
    if voice < 3:
        depth = opportunities.previous_all[:, voice + 1, None] - candidates
        return depth > threshold
    return None


def reverse_overlap_depth_mask(
    opportunities: VoiceOpportunities,
    threshold: int,
) -> np.ndarray | None:
    """Lower candidate crosses the preceding upper voice by more than threshold."""

    voice = opportunities.voice_index
    candidates = opportunities.candidate_pitches[None, :]
    if voice > 0:
        depth = candidates - opportunities.previous_all[:, voice - 1, None]
        return depth > threshold
    return None


def any_overlap_depth_mask(
    opportunities: VoiceOpportunities,
    threshold: int,
) -> np.ndarray:
    """Candidate overlaps either preceding adjacent voice beyond a threshold."""

    upper = overlap_depth_mask(opportunities, threshold)
    lower = reverse_overlap_depth_mask(opportunities, threshold)
    if upper is None:
        assert lower is not None
        return lower
    if lower is None:
        return upper
    return upper | lower


def residual_components(
    opportunities: VoiceOpportunities,
    probabilities: np.ndarray,
    mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rows = np.arange(opportunities.size)
    chosen = mask[rows, opportunities.chosen_indices].astype(np.float64)
    expected = np.sum(probabilities * mask, axis=1)
    testable = mask.any(axis=1) & ~mask.all(axis=1)
    return chosen, expected, expected * (1.0 - expected), testable


def aggregate_evidence(
    datasets: Sequence[VoiceOpportunities],
    probabilities: Sequence[np.ndarray],
    masks: Sequence[np.ndarray | None],
) -> ResidualEvidence:
    residual_sum = 0.0
    variance_sum = 0.0
    observed_sum = 0.0
    expected_sum = 0.0
    testable_count = 0
    supported_pieces: set[str] = set()
    for data, probs, mask in zip(datasets, probabilities, masks, strict=True):
        if mask is None:
            continue
        chosen, expected, variance, testable = residual_components(data, probs, mask)
        residual_sum += float(np.sum(chosen - expected))
        variance_sum += float(variance.sum())
        observed_sum += float(chosen[testable].sum())
        expected_sum += float(expected[testable].sum())
        testable_count += int(testable.sum())
        supported_pieces.update(data.piece_ids[testable].tolist())
    return ResidualEvidence(
        residual_sum=residual_sum,
        variance=variance_sum,
        z_score=residual_sum / math.sqrt(max(variance_sum, 1e-12)),
        observed_rate=observed_sum / max(testable_count, 1),
        expected_rate=expected_sum / max(testable_count, 1),
        testable_opportunities=testable_count,
        piece_support=len(supported_pieces),
    )


def serialize_evidence(evidence: ResidualEvidence) -> dict[str, Any]:
    return {
        "residual_sum": evidence.residual_sum,
        "variance": evidence.variance,
        "z_score": evidence.z_score,
        "observed_rate": evidence.observed_rate,
        "expected_rate": evidence.expected_rate,
        "testable_opportunities": evidence.testable_opportunities,
        "piece_support": evidence.piece_support,
    }


def bootstrap_by_piece(
    datasets: Sequence[VoiceOpportunities],
    probabilities: Sequence[np.ndarray],
    masks: Sequence[np.ndarray | None],
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    """Cluster-bootstrap an aggregate SATB residual by whole chorals."""

    pieces = np.unique(np.concatenate([data.piece_ids for data in datasets]))
    residual_by_piece = np.zeros(pieces.shape[0], dtype=np.float64)
    variance_by_piece = np.zeros(pieces.shape[0], dtype=np.float64)
    piece_index = {piece: index for index, piece in enumerate(pieces)}
    for data, probs, mask in zip(datasets, probabilities, masks, strict=True):
        if mask is None:
            continue
        chosen, expected, variance, _ = residual_components(data, probs, mask)
        residual = chosen - expected
        for piece in np.unique(data.piece_ids):
            rows = data.piece_ids == piece
            index = piece_index[piece]
            residual_by_piece[index] += float(residual[rows].sum())
            variance_by_piece[index] += float(variance[rows].sum())
    generator = np.random.default_rng(seed)
    sampled = generator.integers(0, len(pieces), size=(replicates, len(pieces)))
    z_scores = residual_by_piece[sampled].sum(axis=1) / np.sqrt(
        np.maximum(variance_by_piece[sampled].sum(axis=1), 1e-12)
    )
    quantiles = np.quantile(z_scores, [0.025, 0.5, 0.975])
    return {
        "replicates": replicates,
        "piece_count": int(len(pieces)),
        "z_p025": float(quantiles[0]),
        "z_median": float(quantiles[1]),
        "z_p975": float(quantiles[2]),
        "negative_fraction": float(np.mean(z_scores < 0)),
        "positive_fraction": float(np.mean(z_scores > 0)),
        "below_minus_two_fraction": float(np.mean(z_scores <= -2)),
        "above_two_fraction": float(np.mean(z_scores >= 2)),
    }


def scan_family(
    family: str,
    values: Sequence[int],
    train: Sequence[VoiceOpportunities],
    validation: Sequence[VoiceOpportunities],
    train_probabilities: Sequence[np.ndarray],
    validation_probabilities: Sequence[np.ndarray],
    mask_builder: Any,
    bootstrap_replicates: int,
    seed: int,
) -> list[dict[str, Any]]:
    records = []
    for index, value in enumerate(values):
        train_masks = [mask_builder(data, value) for data in train]
        validation_masks = [mask_builder(data, value) for data in validation]
        records.append(
            {
                "family": family,
                "numeric_value": value,
                "train": serialize_evidence(
                    aggregate_evidence(train, train_probabilities, train_masks)
                ),
                "validation": serialize_evidence(
                    aggregate_evidence(
                        validation, validation_probabilities, validation_masks
                    )
                ),
                "bootstrap_train": bootstrap_by_piece(
                    train,
                    train_probabilities,
                    train_masks,
                    bootstrap_replicates,
                    seed + 2 * index,
                ),
                "bootstrap_validation": bootstrap_by_piece(
                    validation,
                    validation_probabilities,
                    validation_masks,
                    bootstrap_replicates,
                    seed + 2 * index + 1,
                ),
            }
        )
    return records


def select_avoidances(
    records: Sequence[dict[str, Any]],
    train_z: float,
    validation_z: float,
    bootstrap_negative_fraction: float,
) -> list[int]:
    return [
        int(record["numeric_value"])
        for record in records
        if record["train"]["z_score"] <= train_z
        and record["validation"]["z_score"] <= validation_z
        and record["bootstrap_validation"]["negative_fraction"]
        >= bootstrap_negative_fraction
    ]


def select_top_avoidances(
    records: Sequence[dict[str, Any]],
    train_z: float,
    validation_z: float,
    bootstrap_negative_fraction: float,
    budget: int,
) -> list[int]:
    """Apply stability gates, then spend a small intelligibility budget."""

    admissible = [
        record
        for record in records
        if record["train"]["z_score"] <= train_z
        and record["validation"]["z_score"] <= validation_z
        and record["bootstrap_validation"]["negative_fraction"]
        >= bootstrap_negative_fraction
    ]
    admissible.sort(
        key=lambda record: (
            record["train"]["z_score"] ** 2
            + record["validation"]["z_score"] ** 2
        ),
        reverse=True,
    )
    return [int(record["numeric_value"]) for record in admissible[:budget]]


def add_local_log_rate_contrasts(
    records: list[dict[str, Any]],
    *,
    circular: bool = False,
) -> None:
    """Annotate isolated notches relative to adjacent numeric hypotheses."""

    for split in ("train", "validation"):
        log_rates = [
            math.log(
                (record[split]["observed_rate"] + 1e-9)
                / (record[split]["expected_rate"] + 1e-9)
            )
            for record in records
        ]
        for index, record in enumerate(records):
            contrast = None
            if circular or 0 < index < len(records) - 1:
                contrast = log_rates[index] - 0.5 * (
                    log_rates[index - 1]
                    + log_rates[(index + 1) % len(records)]
                )
            record[split]["local_log_rate_contrast"] = contrast


def select_local_notches(
    records: Sequence[dict[str, Any]],
    train_z: float,
    validation_z: float,
    bootstrap_negative_fraction: float,
    maximum_local_contrast: float,
    budget: int,
) -> list[int]:
    """Select stable, isolated dips rather than broad low-frequency regions."""

    admissible = [
        record
        for record in records
        if record["train"]["z_score"] <= train_z
        and record["validation"]["z_score"] <= validation_z
        and record["bootstrap_validation"]["negative_fraction"]
        >= bootstrap_negative_fraction
        and record["train"]["local_log_rate_contrast"] is not None
        and record["validation"]["local_log_rate_contrast"] is not None
        and record["train"]["local_log_rate_contrast"] <= maximum_local_contrast
        and record["validation"]["local_log_rate_contrast"]
        <= maximum_local_contrast
    ]
    admissible.sort(
        key=lambda record: (
            record["train"]["local_log_rate_contrast"]
            + record["validation"]["local_log_rate_contrast"]
        )
    )
    return [int(record["numeric_value"]) for record in admissible[:budget]]


def compare_melodic_class_to_reference(interval_class: int) -> dict[str, Any]:
    """Post-hoc finite-domain comparison with the hidden Snarky melody rule."""

    tested = 0
    mismatches = 0
    for candidate_min, candidate_max in VOICE_RANGES:
        for source in range(candidate_min, candidate_max + 1):
            for target in range(candidate_min, candidate_max + 1):
                learned = abs(target - source) % 12 == interval_class
                reference = (target - source) % 12 == 6
                tested += 1
                mismatches += int(learned != reference)
    return {
        "numeric_class": interval_class,
        "reference_rule_id": "R-MELODY-002",
        "tested_voice_range_states": tested,
        "mismatches": mismatches,
        "classification": (
            "RECOVERED_EQUIVALENT" if mismatches == 0 else "NOT_EQUIVALENT"
        ),
    }


def compare_overlap_threshold_to_reference(threshold: int) -> dict[str, Any]:
    """Post-hoc finite-domain comparison with the hidden adjacent-overlap rule."""

    tested = 0
    mismatches = 0
    for upper_voice in range(3):
        upper_min, upper_max = VOICE_RANGES[upper_voice]
        lower_min, lower_max = VOICE_RANGES[upper_voice + 1]
        for source_upper in range(upper_min, upper_max + 1):
            for source_lower in range(lower_min, lower_max + 1):
                if source_upper <= source_lower:
                    continue
                for target_upper in range(upper_min, upper_max + 1):
                    for target_lower in range(lower_min, lower_max + 1):
                        learned = (
                            source_lower - target_upper > threshold
                            or target_lower - source_upper > threshold
                        )
                        reference = (
                            target_upper < source_lower
                            or target_lower > source_upper
                        )
                        tested += 1
                        mismatches += int(learned != reference)
    return {
        "numeric_threshold": threshold,
        "reference_rule_id": "R-OVERLAP-001",
        "tested_valid_adjacent_voice_states": tested,
        "mismatches": mismatches,
        "classification": (
            "RECOVERED_EQUIVALENT" if mismatches == 0 else "NOT_EQUIVALENT"
        ),
    }


def markdown_report(result: dict[str, Any]) -> str:
    corpus = result["corpus"]
    lines = [
        "# POC V2.2 — contraintes locales SATB",
        "",
        "## Protocole",
        "",
        (
            f"- Train groupé : {corpus['train_pieces']} chorals / "
            f"{corpus['train_opportunities']} décisions SATB."
        ),
        (
            f"- Validation groupée : {corpus['validation_pieces']} chorals / "
            f"{corpus['validation_opportunities']} décisions SATB."
        ),
        f"- Test réservé : {corpus['test_pieces_reserved']} chorals, non ouvert.",
        (
            "- Contrôle nul : choix mélangés par choral et par voix."
            if result["experiment"]["null_shuffle"]
            else "- Données authentiques."
        ),
        (
            "- Socle conditionnel par voix : hauteur absolue, direction, "
            "seuils génériques de saut, harmonie locale et espacement lisse."
        ),
        "",
        "## Ajustement des quatre modèles",
        "",
        "| Voix | Train NLL | Validation NLL | Poids actifs |",
        "|---|---:|---:|---:|",
    ]
    for fit in result["model"]["voice_baselines"]:
        lines.append(
            f"| {fit['voice']} | {fit['train_nll']:.6f} | "
            f"{fit['validation_nll']:.6f} | {fit['active_weights']} |"
        )
    for title, key in (
        ("Classes d'intervalle mélodique modulo 12", "melodic_interval_scan"),
        ("Overlap adjacent symétrique", "overlap_scan"),
        ("Profondeur sous la voix inférieure précédente", "upper_overlap_scan"),
        ("Profondeur au-dessus de la voix supérieure précédente", "lower_overlap_scan"),
    ):
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                "| Valeur | z train | z validation | Contraste local train/val. | "
                "Bootstrap val. médian [2,5 % ; 97,5 %] | P(z val. < 0) |",
                "|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for record in result["model"][key]:
            bootstrap = record["bootstrap_validation"]
            lines.append(
                f"| {record['numeric_value']} | {record['train']['z_score']:.3f} | "
                f"{record['validation']['z_score']:.3f} | "
                f"{record['train']['local_log_rate_contrast'] or math.nan:.3f} / "
                f"{record['validation']['local_log_rate_contrast'] or math.nan:.3f} | "
                f"{bootstrap['z_median']:.3f} "
                f"[{bootstrap['z_p025']:.3f} ; {bootstrap['z_p975']:.3f}] | "
                f"{bootstrap['negative_fraction']:.3f} |"
            )
    lines.extend(
        [
            "",
            "## Sélections automatiques",
            "",
            (
                "- Tailles mélodiques évitées : "
                f"`{result['model']['selected_melodic_intervals']}`."
            ),
            (
                "- Seuil d'overlap adjacent retenu : "
                f"`{result['model']['selected_overlap_thresholds']}`."
            ),
            "",
            "Les noms musicologiques ne sont attribués qu'après cette sélection.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=base.default_archive_path())
    parser.add_argument("--manifest", type=Path, default=base.default_manifest_path())
    parser.add_argument(
        "--splits",
        type=Path,
        default=column.default_variant_safe_splits_path(),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--train-z", type=float, default=-3.0)
    parser.add_argument("--validation-z", type=float, default=-2.0)
    parser.add_argument("--bootstrap-negative-fraction", type=float, default=0.95)
    parser.add_argument(
        "--family-budget",
        type=int,
        default=1,
        help="maximum number of readable rules retained from each numeric family",
    )
    parser.add_argument("--melodic-notch-max", type=float, default=-0.75)
    parser.add_argument("--overlap-notch-max", type=float, default=-0.20)
    parser.add_argument("--null-shuffle", action="store_true")
    parser.add_argument("--output-stem", default="v2_2_satb_level_a")
    parser.add_argument("--results-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = base.experiment_root()
    work = root / "work"
    results_dir = (
        args.results_dir.resolve() if args.results_dir is not None else root / "results"
    )
    archive = args.archive.resolve()
    actual_hash = base.sha256_file(archive)
    if actual_hash != base.EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"Unexpected archive hash {actual_hash}")
    manifest, included_pieces = base.load_included_pieces(args.manifest.resolve())
    splits, split_metadata = column.load_experiment_splits(
        [piece["id"] for piece in included_pieces],
        args.seed,
        args.splits.resolve(),
    )

    selected_pieces = included_pieces
    cache_suffix = "full"
    if args.max_pieces is not None:
        selected_ids = set((splits["train"] + splits["validation"])[: args.max_pieces])
        selected_pieces = [
            piece for piece in included_pieces if piece["id"] in selected_ids
        ]
        cache_suffix = f"smoke-{args.max_pieces}"
    cache_path = work / f"satb-opportunities-{cache_suffix}.npz"
    if cache_path.exists():
        print(f"[satb-corpus] loading cache {cache_path}", flush=True)
        all_opportunities = load_satb_opportunities(cache_path)
    else:
        score_paths = base.materialize_scores(archive, selected_pieces, work / "scores")
        all_opportunities = build_satb_opportunities(score_paths)
        save_satb_opportunities(cache_path, all_opportunities)

    available = set(np.concatenate([data.piece_ids for data in all_opportunities]))
    train_ids = [piece for piece in splits["train"] if piece in available]
    validation_ids = [piece for piece in splits["validation"] if piece in available]
    if args.max_pieces is not None and not validation_ids:
        smoke_ids = sorted(available)
        split_at = max(1, int(0.8 * len(smoke_ids)))
        train_ids, validation_ids = smoke_ids[:split_at], smoke_ids[split_at:]
    train = [subset_for_piece_ids(data, train_ids) for data in all_opportunities]
    validation = [
        subset_for_piece_ids(data, validation_ids) for data in all_opportunities
    ]
    if any(data.size == 0 for data in (*train, *validation)):
        raise RuntimeError("At least one train/validation voice split is empty")
    if args.null_shuffle:
        train = [
            shuffle_choices_within_pieces(data, args.seed + 101 + voice)
            for voice, data in enumerate(train)
        ]
        validation = [
            shuffle_choices_within_pieces(data, args.seed + 202 + voice)
            for voice, data in enumerate(validation)
        ]

    train_probabilities = []
    validation_probabilities = []
    voice_baselines = []
    for train_voice, validation_voice in zip(train, validation, strict=True):
        print(f"[baseline] fitting {VOICE_NAMES[train_voice.voice_index]}", flush=True)
        train_probs, validation_probs, diagnostics = fit_voice_baseline(
            train_voice,
            validation_voice,
            args.l1,
            args.max_steps,
            args.learning_rate,
        )
        train_probabilities.append(train_probs)
        validation_probabilities.append(validation_probs)
        voice_baselines.append(diagnostics)

    melodic_scan = scan_family(
        "absolute_melodic_interval_mod12",
        range(12),
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        melodic_interval_mask,
        args.bootstrap_replicates,
        args.seed + 10_000,
    )
    upper_overlap_scan = scan_family(
        "upper_voice_overlap_depth_gt",
        range(-4, 5),
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        overlap_depth_mask,
        args.bootstrap_replicates,
        args.seed + 20_000,
    )
    overlap_scan = scan_family(
        "adjacent_voice_overlap_depth_gt",
        range(-4, 5),
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        any_overlap_depth_mask,
        args.bootstrap_replicates,
        args.seed + 25_000,
    )
    lower_overlap_scan = scan_family(
        "lower_voice_overlap_depth_gt",
        range(-4, 5),
        train,
        validation,
        train_probabilities,
        validation_probabilities,
        reverse_overlap_depth_mask,
        args.bootstrap_replicates,
        args.seed + 30_000,
    )
    add_local_log_rate_contrasts(melodic_scan, circular=True)
    for scan in (overlap_scan, upper_overlap_scan, lower_overlap_scan):
        add_local_log_rate_contrasts(scan)
    selected_melodic = select_local_notches(
        melodic_scan,
        args.train_z,
        args.validation_z,
        args.bootstrap_negative_fraction,
        args.melodic_notch_max,
        args.family_budget,
    )
    selected_overlap = select_local_notches(
        overlap_scan,
        args.train_z,
        args.validation_z,
        args.bootstrap_negative_fraction,
        args.overlap_notch_max,
        args.family_budget,
    )

    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v2_2_satb_level_a",
            "seed": args.seed,
            "null_shuffle": args.null_shuffle,
            "test_opened": False,
            "voice_ranges": [list(bounds) for bounds in VOICE_RANGES],
            "split_strategy": split_metadata["strategy"],
            "selection": {
                "train_z_max": args.train_z,
                "validation_z_max": args.validation_z,
                "bootstrap_validation_negative_fraction_min": (
                    args.bootstrap_negative_fraction
                ),
                "family_rule_budget": args.family_budget,
                "melodic_local_log_rate_contrast_max": args.melodic_notch_max,
                "overlap_local_log_rate_contrast_max": args.overlap_notch_max,
            },
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "music21": __import__("music21").__version__,
        },
        "source": {
            "archive": str(archive),
            "archive_sha256": actual_hash,
            "manifest": str(args.manifest.resolve()),
            "manifest_schema_version": manifest["schema_version"],
            "split": split_metadata["source"],
        },
        "corpus": {
            "pieces_total": len(available),
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "opportunities_by_voice": {
                VOICE_NAMES[data.voice_index]: data.size for data in all_opportunities
            },
            "train_opportunities": sum(data.size for data in train),
            "validation_opportunities": sum(data.size for data in validation),
            "test_opened": False,
        },
        "model": {
            "voice_baselines": voice_baselines,
            "melodic_interval_scan": melodic_scan,
            "overlap_scan": overlap_scan,
            "upper_overlap_scan": upper_overlap_scan,
            "lower_overlap_scan": lower_overlap_scan,
            "selected_melodic_intervals": selected_melodic,
            "selected_overlap_thresholds": selected_overlap,
            "semantic_comparison": {
                "melodic": [
                    compare_melodic_class_to_reference(value)
                    for value in selected_melodic
                ],
                "overlap": [
                    compare_overlap_threshold_to_reference(value)
                    for value in selected_overlap
                ],
            },
        },
    }
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
