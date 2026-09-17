"""Unsupervised local-tonic status inferred from adjacent K3 kernels."""

from __future__ import annotations

import math
from dataclasses import dataclass

import k3
import numpy as np


@dataclass(frozen=True)
class LocalTonalSequence:
    piece_id: str
    offsets: np.ndarray
    histograms: np.ndarray
    global_tonic: int
    mode: int


@dataclass(frozen=True)
class LocalTonalInference:
    posterior: np.ndarray
    map_tonics: np.ndarray
    log_evidence: float


def _logsumexp(values: np.ndarray, axis: int | None = None) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    result = maximum + np.log(np.exp(values - maximum).sum(axis=axis, keepdims=True))
    return np.squeeze(result, axis=axis)


def state_sequences(dataset: k3.K3Dataset) -> tuple[LocalTonalSequence, ...]:
    """Collapse simultaneous attack decisions into one K3 tonal observation."""

    if dataset.tonic_pcs is None or dataset.modes is None:
        raise ValueError("Local tonality requires global tonic and mode")
    sequences = []
    for piece_id in np.unique(dataset.piece_ids):
        piece_rows = np.flatnonzero(dataset.piece_ids == piece_id)
        central_offsets = dataset.offsets[piece_rows, 1]
        order = np.argsort(central_offsets, kind="stable")
        ordered_rows = piece_rows[order]
        ordered_offsets = central_offsets[order]
        _, first_positions = np.unique(ordered_offsets, return_index=True)
        rows = ordered_rows[np.sort(first_positions)]
        histograms = np.zeros((rows.size, 12), dtype=np.float64)
        for time, row in enumerate(rows):
            for block_index, weight in enumerate((1.0, 2.0, 1.0)):
                pitch_classes = dataset.blocks[row, block_index] % 12
                np.add.at(histograms[time], pitch_classes, weight)
        sequences.append(
            LocalTonalSequence(
                piece_id=str(piece_id),
                offsets=dataset.offsets[rows, 1].astype(np.float64),
                histograms=histograms,
                global_tonic=int(dataset.tonic_pcs[rows[0]]),
                mode=int(dataset.modes[rows[0]]),
            )
        )
    return tuple(sequences)


def initialize_profiles(
    sequences: tuple[LocalTonalSequence, ...],
    alpha: float = 0.5,
) -> np.ndarray:
    """Initialize transposition-relative emissions at the declared tonic."""

    counts = np.full((2, 12), alpha, dtype=np.float64)
    for sequence in sequences:
        aggregate = sequence.histograms.sum(axis=0)
        for pitch_class, count in enumerate(aggregate):
            counts[sequence.mode, (pitch_class - sequence.global_tonic) % 12] += count
    return counts / counts.sum(axis=1, keepdims=True)


def emission_scores(
    sequence: LocalTonalSequence,
    profiles: np.ndarray,
) -> np.ndarray:
    """Return multinomial log emissions for each local tonic candidate."""

    if profiles.shape != (2, 12):
        raise ValueError("Expected one 12-class profile per declared mode")
    log_profile = np.log(np.maximum(profiles[sequence.mode], 1e-12))
    scores = np.empty((sequence.offsets.size, 12), dtype=np.float64)
    for tonic in range(12):
        relative_indices = (np.arange(12) - tonic) % 12
        scores[:, tonic] = sequence.histograms @ log_profile[relative_indices]
    return scores


def transition_logits(stay_probability: float) -> np.ndarray:
    if not 1.0 / 12.0 < stay_probability < 1.0:
        raise ValueError("Stay probability must exceed chance and remain below one")
    change_probability = (1.0 - stay_probability) / 11.0
    transition = np.full((12, 12), math.log(change_probability))
    np.fill_diagonal(transition, math.log(stay_probability))
    return transition


def infer_sequence(
    sequence: LocalTonalSequence,
    profiles: np.ndarray,
    *,
    stay_probability: float,
    global_start_probability: float,
) -> LocalTonalInference:
    """Run exact forward-backward inference over twelve local tonic states."""

    if not 1.0 / 12.0 < global_start_probability < 1.0:
        raise ValueError("Global start probability must exceed chance")
    emissions = emission_scores(sequence, profiles)
    transition = transition_logits(stay_probability)
    initial = np.full(
        12,
        math.log((1.0 - global_start_probability) / 11.0),
    )
    initial[sequence.global_tonic] = math.log(global_start_probability)
    length = sequence.offsets.size
    forward = np.empty((length, 12), dtype=np.float64)
    forward[0] = initial + emissions[0]
    for time in range(1, length):
        forward[time] = emissions[time] + _logsumexp(
            forward[time - 1][:, None] + transition,
            axis=0,
        )
    log_evidence = float(_logsumexp(forward[-1]))
    backward = np.zeros((length, 12), dtype=np.float64)
    for time in range(length - 2, -1, -1):
        backward[time] = _logsumexp(
            transition + emissions[time + 1][None, :] + backward[time + 1][None, :],
            axis=1,
        )
    log_posterior = forward + backward - log_evidence
    posterior = np.exp(log_posterior)
    posterior /= posterior.sum(axis=1, keepdims=True)
    return LocalTonalInference(
        posterior=posterior,
        map_tonics=posterior.argmax(axis=1).astype(np.int8),
        log_evidence=log_evidence,
    )


def fit_profiles(
    sequences: tuple[LocalTonalSequence, ...],
    *,
    iterations: int = 20,
    alpha: float = 0.5,
    stay_probability: float = 0.92,
    global_start_probability: float = 0.8,
) -> tuple[np.ndarray, dict[str, LocalTonalInference], list[dict[str, float]]]:
    """Fit transposition-relative profiles with exact EM."""

    profiles = initialize_profiles(sequences, alpha)
    history = []
    inferences: dict[str, LocalTonalInference] = {}
    for iteration in range(1, iterations + 1):
        counts = np.full((2, 12), alpha, dtype=np.float64)
        evidence = 0.0
        entropy_sum = 0.0
        state_count = 0
        inferences = {}
        for sequence in sequences:
            inference = infer_sequence(
                sequence,
                profiles,
                stay_probability=stay_probability,
                global_start_probability=global_start_probability,
            )
            inferences[sequence.piece_id] = inference
            evidence += inference.log_evidence
            entropy_sum += float(
                -np.sum(
                    inference.posterior * np.log(np.maximum(inference.posterior, 1e-12))
                )
            )
            state_count += sequence.offsets.size
            for tonic in range(12):
                weighted = (
                    inference.posterior[:, tonic, None] * sequence.histograms
                ).sum(axis=0)
                for pitch_class, count in enumerate(weighted):
                    counts[
                        sequence.mode,
                        (pitch_class - tonic) % 12,
                    ] += count
        profiles = counts / counts.sum(axis=1, keepdims=True)
        history.append(
            {
                "iteration": iteration,
                "log_evidence_per_state": evidence / state_count,
                "posterior_entropy_normalized": entropy_sum
                / (state_count * math.log(12)),
            }
        )
    return profiles, inferences, history


def infer_corpus(
    sequences: tuple[LocalTonalSequence, ...],
    profiles: np.ndarray,
    *,
    stay_probability: float,
    global_start_probability: float,
) -> dict[str, LocalTonalInference]:
    return {
        sequence.piece_id: infer_sequence(
            sequence,
            profiles,
            stay_probability=stay_probability,
            global_start_probability=global_start_probability,
        )
        for sequence in sequences
    }


def inference_lookup(
    sequences: tuple[LocalTonalSequence, ...],
    inferences: dict[str, LocalTonalInference],
) -> dict[tuple[str, float], tuple[np.ndarray, int]]:
    lookup = {}
    for sequence in sequences:
        inference = inferences[sequence.piece_id]
        for index, offset in enumerate(sequence.offsets):
            lookup[(sequence.piece_id, round(float(offset), 6))] = (
                inference.posterior[index],
                int(inference.map_tonics[index]),
            )
    return lookup


def learn_local_voice_logits(
    dataset: k3.K3Dataset,
    lookup: dict[tuple[str, float], tuple[np.ndarray, int]],
    alpha: float = 0.5,
) -> np.ndarray:
    """Learn voice/mode degree marginals under posterior local tonic status."""

    if dataset.modes is None:
        raise ValueError("Local voice profiles require declared mode")
    counts = np.full((4, 2, 12), alpha, dtype=np.float64)
    for row in range(dataset.size):
        key = (
            str(dataset.piece_ids[row]),
            round(float(dataset.offsets[row, 1]), 6),
        )
        posterior, _ = lookup[key]
        pitch_class = int(dataset.chosen_pitches[row]) % 12
        voice = int(dataset.voice_indices[row])
        mode = int(dataset.modes[row])
        for tonic, probability in enumerate(posterior):
            counts[voice, mode, (pitch_class - tonic) % 12] += probability
    return np.log(counts / counts.sum(axis=2, keepdims=True))
