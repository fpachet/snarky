"""Deterministic strong-beat harmonic states for the V34 experiment."""

from __future__ import annotations

from typing import Any

import k3
import numpy as np

DISSONANT_FAMILIES = (
    "dominant_seventh",
    "common_seventh",
    "diminished_family",
    "altered_named",
    "ambiguous_named",
)
RESOLUTION_OUTCOMES = (
    "triad_descending_fifth",
    "triad_step_root",
    "triad_repeated_root",
    "triad_other_root_motion",
    "triad_after_ambiguous_root",
    "next_named_dissonant",
    "next_residual",
)
SEVENTH_INTERVAL_BY_QUALITY = {
    4: 10,
    5: 11,
    6: 10,
    7: 10,
    8: 9,
    9: 11,
}


def _signature(block: np.ndarray, tonic_pc: int) -> int:
    signature = 0
    for value in block:
        signature |= 1 << ((int(value) - tonic_pc) % 12)
    return signature


def analyze_block(block: np.ndarray, tonic_pc: int) -> dict[str, Any]:
    """Return an observable chord analysis, never a latent state."""

    signature = _signature(block, tonic_pc)
    analysis_count = int(k3.NAMED_CHORD_ANALYSIS_COUNT_BY_SIGNATURE[signature])
    quality = (
        int(k3.NAMED_CHORD_UNIQUE_QUALITY_BY_SIGNATURE[signature])
        if analysis_count == 1
        else -1
    )
    root_degree = (
        int(k3.NAMED_CHORD_STRICT_UNIQUE_ROOT_BY_SIGNATURE[signature])
        if analysis_count == 1
        else -1
    )
    if analysis_count > 1:
        family = "ambiguous_named"
    elif analysis_count == 0:
        family = "residual"
    elif quality in {0, 1}:
        family = "consonant_triad"
    elif quality == 4:
        family = "dominant_seventh"
    elif quality in {5, 6}:
        family = "common_seventh"
    elif quality in {2, 7, 8}:
        family = "diminished_family"
    else:
        family = "altered_named"
    root_pc = -1 if root_degree < 0 else (tonic_pc + root_degree) % 12
    inversion_interval = (
        -1 if root_pc < 0 else (int(block[3]) - root_pc) % 12
    )
    return {
        "signature": signature,
        "analysis_count": analysis_count,
        "quality": quality,
        "quality_name": (
            None if quality < 0 else k3.NAMED_CHORD_QUALITIES[quality][0]
        ),
        "root_degree": root_degree,
        "root_pc": root_pc,
        "inversion_interval": inversion_interval,
        "family": family,
    }


def resolution_outcome(
    current: dict[str, Any],
    following: dict[str, Any],
) -> str:
    """Classify the next strong harmony relative to the current root."""

    if following["family"] == "consonant_triad":
        if current["root_degree"] < 0:
            return "triad_after_ambiguous_root"
        motion = (following["root_degree"] - current["root_degree"]) % 12
        if motion == 5:
            return "triad_descending_fifth"
        if motion in {1, 2, 10, 11}:
            return "triad_step_root"
        if motion == 0:
            return "triad_repeated_root"
        return "triad_other_root_motion"
    if following["analysis_count"] > 0:
        return "next_named_dissonant"
    return "next_residual"


def seventh_resolution_status(
    current_block: np.ndarray,
    following_block: np.ndarray,
    current: dict[str, Any],
) -> str:
    interval = SEVENTH_INTERVAL_BY_QUALITY.get(int(current["quality"]))
    if interval is None or current["root_pc"] < 0:
        return "not_applicable"
    seventh_pc = (current["root_pc"] + interval) % 12
    voices = [
        voice
        for voice, pitch in enumerate(current_block)
        if int(pitch) % 12 == seventh_pc
    ]
    if not voices:
        return "not_applicable"
    return (
        "resolved_down"
        if all(
            int(following_block[voice]) - int(current_block[voice]) in {-2, -1}
            for voice in voices
        )
        else "not_resolved_down"
    )


def leading_tone_resolution_status(
    current_block: np.ndarray,
    following_block: np.ndarray,
    tonic_pc: int,
) -> str:
    leading_pc = (tonic_pc - 1) % 12
    voices = [
        voice
        for voice, pitch in enumerate(current_block)
        if int(pitch) % 12 == leading_pc
    ]
    if not voices:
        return "not_applicable"
    return (
        "resolved_to_tonic"
        if all(
            int(following_block[voice]) % 12 == tonic_pc
            and 0 < int(following_block[voice]) - int(current_block[voice]) <= 2
            for voice in voices
        )
        else "not_resolved_to_tonic"
    )


def tritone_resolution_status(
    current_block: np.ndarray,
    following_block: np.ndarray,
) -> str:
    pairs = [
        (left, right)
        for left in range(4)
        for right in range(left + 1, 4)
        if abs(int(current_block[left]) - int(current_block[right])) % 12 == 6
    ]
    if not pairs:
        return "not_applicable"
    for left, right in pairs:
        left_motion = int(following_block[left]) - int(current_block[left])
        right_motion = int(following_block[right]) - int(current_block[right])
        if (
            0 < abs(left_motion) <= 2
            and 0 < abs(right_motion) <= 2
            and np.sign(left_motion) != np.sign(right_motion)
        ):
            return "resolved_by_contrary_steps"
    return "not_resolved_by_contrary_steps"


def strong_transition_rows(
    lattice: k3.RhythmicLattice,
    blocks: np.ndarray,
) -> list[dict[str, Any]]:
    """Return one row for every dissonant named strong chord with a successor."""

    strong = np.flatnonzero(lattice.metric_levels >= 2)
    rows = []
    for current_time, following_time in zip(strong[:-1], strong[1:], strict=True):
        current = analyze_block(blocks[current_time], lattice.tonic_pc)
        if current["family"] not in DISSONANT_FAMILIES:
            continue
        following = analyze_block(blocks[following_time], lattice.tonic_pc)
        rows.append(
            {
                "current_time": int(current_time),
                "following_time": int(following_time),
                "current_offset": float(lattice.offsets[current_time]),
                "following_offset": float(lattice.offsets[following_time]),
                "family": current["family"],
                "quality": current["quality"],
                "quality_name": current["quality_name"],
                "root_degree": current["root_degree"],
                "inversion_interval": current["inversion_interval"],
                "resolution_outcome": resolution_outcome(current, following),
                "seventh_resolution": seventh_resolution_status(
                    blocks[current_time],
                    blocks[following_time],
                    current,
                ),
                "leading_tone_resolution": leading_tone_resolution_status(
                    blocks[current_time],
                    blocks[following_time],
                    lattice.tonic_pc,
                ),
                "tritone_resolution": tritone_resolution_status(
                    blocks[current_time],
                    blocks[following_time],
                ),
            }
        )
    return rows
