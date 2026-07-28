"""Clean-room K3 representation, rule search primitives, and Gibbs sampling."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
DEFAULT_THRESHOLDS = (1, 2, 4, 7, 12)
ORDER_THRESHOLDS = (-2, -1, 0, 1, 2)
TRIADIC_BASS_PCSET_SIGNATURES = (137, 145, 265, 289, 529, 545)
SHARED_POTENTIAL_KINDS = {
    "central_distinct_pc_count",
    "central_distinct_pc_count_metric",
    "central_tonic_pcset",
    "central_bass_pcset",
    "central_bass_pcset_metric",
    "central_triadic_metric",
    "bass_pcset_transition",
}


@dataclass
class K3Dataset:
    """Masked-note decisions over three consecutive vertical blocks."""

    piece_ids: np.ndarray
    offsets: np.ndarray
    voice_indices: np.ndarray
    blocks: np.ndarray
    attacks: np.ndarray
    candidate_min: int
    candidate_max: int
    tonic_pcs: np.ndarray | None = None
    modes: np.ndarray | None = None
    metric_levels: np.ndarray | None = None

    @property
    def size(self) -> int:
        return int(self.voice_indices.shape[0])

    @property
    def candidate_pitches(self) -> np.ndarray:
        return np.arange(self.candidate_min, self.candidate_max + 1, dtype=np.int16)

    @property
    def chosen_pitches(self) -> np.ndarray:
        rows = np.arange(self.size)
        return self.blocks[rows, 1, self.voice_indices]

    @property
    def chosen_indices(self) -> np.ndarray:
        return (self.chosen_pitches - self.candidate_min).astype(np.int64)

    def take(self, indices: np.ndarray) -> K3Dataset:
        return K3Dataset(
            piece_ids=self.piece_ids[indices],
            offsets=self.offsets[indices],
            voice_indices=self.voice_indices[indices],
            blocks=self.blocks[indices],
            attacks=self.attacks[indices],
            candidate_min=self.candidate_min,
            candidate_max=self.candidate_max,
            tonic_pcs=(None if self.tonic_pcs is None else self.tonic_pcs[indices]),
            modes=None if self.modes is None else self.modes[indices],
            metric_levels=(
                None if self.metric_levels is None else self.metric_levels[indices]
            ),
        )

    def with_domain(self, candidate_min: int, candidate_max: int) -> K3Dataset:
        chosen = self.chosen_pitches
        if chosen.size and (
            int(chosen.min()) < candidate_min or int(chosen.max()) > candidate_max
        ):
            raise ValueError("Chosen pitches fall outside the declared K3 domain")
        return K3Dataset(
            piece_ids=self.piece_ids,
            offsets=self.offsets,
            voice_indices=self.voice_indices,
            blocks=self.blocks,
            attacks=self.attacks,
            candidate_min=candidate_min,
            candidate_max=candidate_max,
            tonic_pcs=self.tonic_pcs,
            modes=self.modes,
            metric_levels=self.metric_levels,
        )


@dataclass(frozen=True)
class RhythmicLattice:
    """Sounding SATB states and per-voice attacks on the union onset grid."""

    piece_id: str
    offsets: np.ndarray
    blocks: np.ndarray
    attacks: np.ndarray
    end_offset: float
    tonic_pc: int
    mode: int
    metric_levels: np.ndarray

    @property
    def size(self) -> int:
        return int(self.offsets.size)


@dataclass(frozen=True)
class FeatureSpec:
    """One generated numeric predicate over a K3 decision."""

    kind: str
    target_voice: int
    other_voice: int | None = None
    value: int | None = None
    second_value: int | None = None
    complexity: int = 1

    @property
    def key(self) -> str:
        fields = (
            self.kind,
            str(self.target_voice),
            "-" if self.other_voice is None else str(self.other_voice),
            "-" if self.value is None else str(self.value),
            "-" if self.second_value is None else str(self.second_value),
        )
        return ":".join(fields)

    @property
    def label(self) -> str:
        voice = "all_voices" if self.target_voice == -1 else f"v{self.target_voice}"
        other = "" if self.other_voice is None else f",v{self.other_voice}"
        values = [
            value for value in (self.value, self.second_value) if value is not None
        ]
        suffix = "" if not values else "=" + ",".join(map(str, values))
        return f"{self.kind}({voice}{other}){suffix}"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["key"] = self.key
        result["label"] = self.label
        return result

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FeatureSpec:
        return cls(
            kind=str(payload["kind"]),
            target_voice=int(payload["target_voice"]),
            other_voice=(
                None
                if payload.get("other_voice") is None
                else int(payload["other_voice"])
            ),
            value=None if payload.get("value") is None else int(payload["value"]),
            second_value=(
                None
                if payload.get("second_value") is None
                else int(payload["second_value"])
            ),
            complexity=int(payload.get("complexity", 1)),
        )


@dataclass(frozen=True)
class ResidualStatistic:
    """Observed-minus-expected evidence for one local predicate."""

    gradient: float
    variance: float
    z_score: float
    approximate_nll_gain: float
    observed_rate: float
    expected_rate: float
    testable_opportunities: int
    piece_support: int
    column_score: float


def _part_events(part: Any) -> list[tuple[float, float, int | None]]:
    events = []
    for element in part.flatten().notesAndRests:
        start = float(element.offset)
        end = start + float(element.duration.quarterLength)
        pitch = int(element.pitch.midi) if element.isNote else None
        events.append((start, end, pitch))
    return sorted(events)


def _sounding_pitch(
    events: Sequence[tuple[float, float, int | None]],
    offset: float,
) -> int | None:
    for start, end, pitch in events:
        if start - 1e-8 <= offset < end - 1e-8:
            return pitch
    return None


def extract_piece_k3(score_path: Path, piece_id: str) -> list[tuple[Any, ...]]:
    """Extract attack-centered decisions on consecutive vertical states."""

    lattice = extract_piece_lattice(score_path, piece_id)
    rows: list[tuple[Any, ...]] = []
    for index in range(1, lattice.size - 1):
        kernel_blocks = lattice.blocks[index - 1 : index + 2]
        kernel_attacks = lattice.attacks[index - 1 : index + 2]
        kernel_offsets = lattice.offsets[index - 1 : index + 2]
        for voice_index, is_attack in enumerate(lattice.attacks[index]):
            if is_attack:
                rows.append(
                    (
                        piece_id,
                        tuple(kernel_offsets),
                        voice_index,
                        tuple(map(tuple, kernel_blocks)),
                        tuple(map(tuple, kernel_attacks)),
                        lattice.tonic_pc,
                        lattice.mode,
                        int(lattice.metric_levels[index]),
                    )
                )
    return rows


def extract_piece_lattice(score_path: Path, piece_id: str) -> RhythmicLattice:
    """Extract every complete vertical state without collapsing held notes."""

    from music21 import converter, key

    score = converter.parse(score_path)
    parts = {part.partName: part for part in score.parts}
    if set(parts) != set(VOICE_NAMES):
        raise ValueError(f"{piece_id}: unexpected parts {tuple(parts)}")
    events = [_part_events(parts[name]) for name in VOICE_NAMES]
    declarations = []
    for name in VOICE_NAMES:
        keys = list(parts[name].recurse().getElementsByClass(key.Key))
        if len(keys) != 1 or keys[0].mode not in {"major", "minor"}:
            raise ValueError(f"{piece_id}: expected one declared major/minor key")
        declarations.append((int(keys[0].tonic.pitchClass), keys[0].mode))
    if len(set(declarations)) != 1:
        raise ValueError(f"{piece_id}: inconsistent keys across parts")
    tonic_pc, mode_name = declarations[0]
    mode = 0 if mode_name == "major" else 1

    strengths: dict[float, float] = {}
    for name in VOICE_NAMES:
        for element in parts[name].flatten().notesAndRests:
            offset = float(element.offset)
            strengths[offset] = max(
                strengths.get(offset, 0.0),
                float(element.beatStrength),
            )
    offsets = sorted({event[0] for voice_events in events for event in voice_events})
    blocks: list[tuple[int, ...]] = []
    attacks: list[tuple[bool, ...]] = []
    valid_offsets: list[float] = []
    metric_levels = []
    for offset in offsets:
        block = tuple(_sounding_pitch(voice_events, offset) for voice_events in events)
        if any(pitch is None for pitch in block):
            continue
        valid_offsets.append(offset)
        strength = strengths[offset]
        metric_levels.append(
            3
            if strength >= 1.0
            else 2
            if strength >= 0.5
            else 1
            if strength >= 0.25
            else 0
        )
        blocks.append(tuple(int(pitch) for pitch in block))
        attacks.append(
            tuple(
                any(abs(start - offset) <= 1e-8 for start, _, _ in voice_events)
                for voice_events in events
            )
        )
    if len(blocks) < 3:
        raise ValueError(f"{piece_id}: fewer than three complete vertical states")
    end_offset = min(max(end for _, end, _ in voice_events) for voice_events in events)
    if end_offset <= valid_offsets[-1]:
        raise ValueError(f"{piece_id}: invalid final sounding span")
    return RhythmicLattice(
        piece_id=piece_id,
        offsets=np.asarray(valid_offsets, dtype=np.float32),
        blocks=np.asarray(blocks, dtype=np.int16),
        attacks=np.asarray(attacks, dtype=bool),
        end_offset=float(end_offset),
        tonic_pc=tonic_pc,
        mode=mode,
        metric_levels=np.asarray(metric_levels, dtype=np.int8),
    )


def build_k3_dataset(
    score_paths: dict[str, Path],
    candidate_min: int = 0,
    candidate_max: int = 127,
) -> K3Dataset:
    rows: list[tuple[Any, ...]] = []
    for index, (piece_id, score_path) in enumerate(
        sorted(score_paths.items()), start=1
    ):
        rows.extend(extract_piece_k3(score_path, piece_id))
        if index % 25 == 0 or index == len(score_paths):
            print(
                f"[k3-corpus] parsed {index}/{len(score_paths)} pieces, "
                f"{len(rows)} decisions",
                flush=True,
            )
    if not rows:
        raise RuntimeError("No K3 decisions were extracted")
    columns = list(zip(*rows, strict=True))
    return K3Dataset(
        piece_ids=np.asarray(columns[0], dtype=str),
        offsets=np.asarray(columns[1], dtype=np.float32),
        voice_indices=np.asarray(columns[2], dtype=np.int8),
        blocks=np.asarray(columns[3], dtype=np.int16),
        attacks=np.asarray(columns[4], dtype=bool),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        tonic_pcs=np.asarray(columns[5], dtype=np.int8),
        modes=np.asarray(columns[6], dtype=np.int8),
        metric_levels=np.asarray(columns[7], dtype=np.int8),
    )


def save_k3_dataset(path: Path, dataset: K3Dataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        piece_ids=dataset.piece_ids,
        offsets=dataset.offsets,
        voice_indices=dataset.voice_indices,
        blocks=dataset.blocks,
        attacks=dataset.attacks,
        **(
            {}
            if dataset.tonic_pcs is None
            else {
                "tonic_pcs": dataset.tonic_pcs,
                "modes": dataset.modes,
                "metric_levels": dataset.metric_levels,
            }
        ),
    )


def load_k3_dataset(path: Path) -> K3Dataset:
    archive = np.load(path)
    blocks = archive["blocks"]
    return K3Dataset(
        piece_ids=archive["piece_ids"],
        offsets=archive["offsets"],
        voice_indices=archive["voice_indices"],
        blocks=blocks,
        attacks=archive["attacks"],
        candidate_min=int(blocks.min()),
        candidate_max=int(blocks.max()),
        tonic_pcs=archive.get("tonic_pcs", None),
        modes=archive.get("modes", None),
        metric_levels=archive.get("metric_levels", None),
    )


def subset_for_piece_ids(dataset: K3Dataset, piece_ids: Iterable[str]) -> K3Dataset:
    selected = np.isin(dataset.piece_ids, np.asarray(tuple(piece_ids)))
    return dataset.take(np.flatnonzero(selected))


def training_domain(dataset: K3Dataset) -> tuple[int, int]:
    """Derive one common domain from train choices only."""

    chosen = dataset.chosen_pitches
    return int(chosen.min()), int(chosen.max())


def filter_to_domain(
    dataset: K3Dataset,
    candidate_min: int,
    candidate_max: int,
) -> tuple[K3Dataset, int]:
    chosen = dataset.chosen_pitches
    keep = (chosen >= candidate_min) & (chosen <= candidate_max)
    removed = int((~keep).sum())
    return dataset.take(np.flatnonzero(keep)).with_domain(
        candidate_min, candidate_max
    ), removed


def shuffle_choices_within_piece_and_voice(
    dataset: K3Dataset,
    seed: int,
) -> K3Dataset:
    """Break K3 relations while preserving piece/voice pitch histograms."""

    shuffled = dataset.take(np.arange(dataset.size))
    shuffled.blocks = shuffled.blocks.copy()
    generator = np.random.default_rng(seed)
    for piece_id in np.unique(shuffled.piece_ids):
        for voice in range(4):
            indices = np.flatnonzero(
                (shuffled.piece_ids == piece_id) & (shuffled.voice_indices == voice)
            )
            if indices.size < 2:
                continue
            pitches = shuffled.blocks[indices, 1, voice].copy()
            shuffled.blocks[indices, 1, voice] = generator.permutation(pitches)
    return shuffled


def feature_catalogue() -> tuple[FeatureSpec, ...]:
    """Generate the frozen, unnamed numeric K3 predicate catalogue."""

    features: list[FeatureSpec] = []
    for interval_class in range(12):
        features.extend(
            (
                FeatureSpec(
                    "any_voice_adjacent_abs_class",
                    -1,
                    value=interval_class,
                ),
                FeatureSpec(
                    "any_pair_central_abs_class",
                    -1,
                    value=interval_class,
                ),
                FeatureSpec(
                    "any_pair_abs_class_preserved_same_sign",
                    -1,
                    value=interval_class,
                    complexity=4,
                ),
                FeatureSpec(
                    "any_pair_arrival_abs_class_same_sign",
                    -1,
                    value=interval_class,
                    complexity=2,
                ),
            )
        )
    for threshold in DEFAULT_THRESHOLDS:
        features.append(FeatureSpec("any_voice_adjacent_step_gt", -1, value=threshold))
    for threshold in ORDER_THRESHOLDS:
        features.append(
            FeatureSpec(
                "any_adjacent_central_ordered_gap_le",
                -1,
                value=threshold,
            )
        )
    for incoming in (-1, 0, 1):
        for outgoing in (-1, 0, 1):
            features.append(
                FeatureSpec(
                    "any_voice_three_block_sign_shape",
                    -1,
                    value=incoming,
                    second_value=outgoing,
                    complexity=2,
                )
            )
    for voice in range(4):
        for interval_class in range(12):
            features.extend(
                (
                    FeatureSpec(
                        "abs_class_from_previous",
                        voice,
                        value=interval_class,
                    ),
                    FeatureSpec(
                        "abs_class_to_next",
                        voice,
                        value=interval_class,
                    ),
                )
            )
        for threshold in DEFAULT_THRESHOLDS:
            features.extend(
                (
                    FeatureSpec("abs_step_from_previous_gt", voice, value=threshold),
                    FeatureSpec("abs_step_to_next_gt", voice, value=threshold),
                )
            )
        for incoming in (-1, 0, 1):
            for outgoing in (-1, 0, 1):
                features.append(
                    FeatureSpec(
                        "three_block_sign_shape",
                        voice,
                        value=incoming,
                        second_value=outgoing,
                        complexity=2,
                    )
                )
        for other in range(4):
            if other == voice:
                continue
            for interval_class in range(12):
                features.extend(
                    (
                        FeatureSpec(
                            "central_pair_abs_class",
                            voice,
                            other,
                            interval_class,
                        ),
                        FeatureSpec(
                            "pair_abs_class_preserved_same_sign",
                            voice,
                            other,
                            interval_class,
                            complexity=4,
                        ),
                        FeatureSpec(
                            "pair_arrival_abs_class_same_sign",
                            voice,
                            other,
                            interval_class,
                            complexity=2,
                        ),
                    )
                )
            for threshold in ORDER_THRESHOLDS:
                features.extend(
                    (
                        FeatureSpec(
                            "central_ordered_gap_le",
                            voice,
                            other,
                            threshold,
                        ),
                        FeatureSpec(
                            "previous_ordered_gap_le",
                            voice,
                            other,
                            threshold,
                        ),
                    )
                )
    unique = {feature.key: feature for feature in features}
    return tuple(unique[key] for key in sorted(unique))


def _sign(values: np.ndarray) -> np.ndarray:
    return np.sign(values).astype(np.int8)


def adjacent_step_sizes(dataset: K3Dataset) -> np.ndarray:
    """Maximum target-voice step to either effective neighboring block."""

    candidates = dataset.candidate_pitches[None, :]
    rows = np.arange(dataset.size)
    voices = dataset.voice_indices
    previous = dataset.blocks[rows, 0, voices, None]
    static_following = dataset.blocks[rows, 2, voices, None]
    following = np.where(
        dataset.attacks[rows, 2, voices, None],
        static_following,
        candidates,
    )
    return np.maximum(
        np.abs(candidates - previous),
        np.abs(following - candidates),
    )


def _context_array(
    values: np.ndarray | None,
    name: str,
) -> np.ndarray:
    if values is None:
        raise ValueError(f"Contextual K3 feature requires {name}")
    return values


def central_tonic_pcset_signatures(dataset: K3Dataset) -> np.ndarray:
    """Return tonic-relative 12-bit pitch-class sets for every candidate."""

    tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")[:, None]
    candidates = dataset.candidate_pitches[None, :]
    voices = dataset.voice_indices
    signatures = np.zeros(
        (dataset.size, dataset.candidate_pitches.size),
        dtype=np.int16,
    )
    for voice in range(4):
        pitches = np.where(
            (voices == voice)[:, None],
            candidates,
            dataset.blocks[:, 1, voice, None],
        )
        relative = (pitches - tonics) % 12
        signatures |= np.left_shift(1, relative).astype(np.int16)
    return signatures


def central_bass_pcset_signatures(dataset: K3Dataset) -> np.ndarray:
    """Return bass-relative 12-bit pitch-class sets for every candidate."""

    return bass_pcset_signatures(dataset, position=1)


def bass_pcset_signatures(
    dataset: K3Dataset,
    *,
    position: int,
) -> np.ndarray:
    """Return candidate-aware bass-relative sets at one K3 position.

    At the central position the candidate replaces the attacked target note.
    At the following position it also replaces that voice when the central
    attack is held. This keeps sonority trajectories consistent with the
    ATTACK/HOLD semantics used by the Gibbs sampler.
    """

    if position not in {0, 1, 2}:
        raise ValueError("A K3 position must be 0, 1, or 2")
    candidates = dataset.candidate_pitches[None, :]
    voices = dataset.voice_indices
    candidate_applies = voices[:, None] == np.arange(4)[None, :]
    if position == 2:
        candidate_applies &= ~dataset.attacks[:, 2, :]
    elif position == 0:
        candidate_applies &= False
    pitches = np.broadcast_to(
        dataset.blocks[:, position, :, None],
        (
            dataset.size,
            4,
            dataset.candidate_pitches.size,
        ),
    )
    pitches = np.where(
        candidate_applies[:, :, None],
        candidates[:, None, :],
        pitches,
    )
    reference = pitches[:, 3, :]
    signatures = np.zeros(
        (dataset.size, dataset.candidate_pitches.size),
        dtype=np.int16,
    )
    for voice in range(4):
        relative = (pitches[:, voice, :] - reference) % 12
        signatures |= np.left_shift(1, relative).astype(np.int16)
    return signatures


def _contextual_feature_mask(
    dataset: K3Dataset,
    feature: FeatureSpec,
    candidates: np.ndarray,
) -> np.ndarray:
    rows = np.arange(dataset.size)
    voices = dataset.voice_indices
    previous = dataset.blocks[rows, 0, voices, None]
    if feature.kind == "attacked_repeat_from_previous":
        applies = (
            np.ones(dataset.size, dtype=bool)
            if feature.target_voice == -1
            else voices == feature.target_voice
        )
        return applies[:, None] & (candidates == previous)
    if feature.kind.startswith("rare_tonal_"):
        if feature.target_voice not in range(4):
            raise ValueError("Rare tonal features require one target voice")
        if feature.value is None or feature.second_value is None:
            raise ValueError("Rare tonal features require a mask and mode")
        if feature.kind == "rare_tonal_bass_pcset":
            feature_mode, vertical_signature = divmod(
                feature.second_value,
                4096,
            )
        else:
            feature_mode = feature.second_value
            vertical_signature = None
        if feature_mode not in {0, 1}:
            raise ValueError("Rare tonal feature has an invalid mode")
        tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")[:, None]
        modes = _context_array(dataset.modes, "modes")
        levels = _context_array(dataset.metric_levels, "metric_levels")
        applies = (voices == feature.target_voice) & (modes == feature_mode)
        relative = (candidates - tonics) % 12
        rare = (
            np.right_shift(int(feature.value), relative).astype(np.int8) & 1
        ).astype(bool)
        following = dataset.blocks[rows, 2, voices, None]
        next_attack = dataset.attacks[rows, 2, voices, None]
        incoming = candidates - previous
        outgoing = following - candidates
        incoming_step = (np.abs(incoming) >= 1) & (np.abs(incoming) <= 2)
        outgoing_step = next_attack & (np.abs(outgoing) >= 1) & (np.abs(outgoing) <= 2)
        if feature.kind == "rare_tonal_class":
            status = np.ones_like(rare)
        elif feature.kind == "rare_tonal_incoming_step":
            status = incoming_step
        elif feature.kind == "rare_tonal_leap_arrival":
            status = ~incoming_step
        elif feature.kind == "rare_tonal_immediate_step_resolution":
            status = outgoing_step
        elif feature.kind == "rare_tonal_short_no_step_resolution":
            status = next_attack & ~outgoing_step
        elif feature.kind == "rare_tonal_immediate_neighbor":
            status = incoming_step & outgoing_step & (following == previous)
        elif feature.kind == "rare_tonal_immediate_passing":
            status = (
                incoming_step & outgoing_step & (np.sign(incoming) == np.sign(outgoing))
            )
        elif feature.kind == "rare_tonal_weak_metric":
            status = levels[:, None] <= 1
        elif feature.kind == "rare_tonal_strong_metric":
            status = levels[:, None] >= 2
        elif feature.kind == "rare_tonal_bass_pcset":
            status = central_bass_pcset_signatures(dataset) == vertical_signature
        else:
            raise ValueError(f"Unknown rare tonal feature: {feature.kind}")
        return applies[:, None] & rare & status
    value = feature.value
    if value is None:
        raise ValueError(f"Feature {feature.key} has no numeric value")
    if feature.kind in {
        "tonic_relative_class",
        "tonic_relative_class_mode",
    }:
        tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")[:, None]
        mask = (candidates - tonics) % 12 == value
        if feature.kind == "tonic_relative_class_mode":
            modes = _context_array(dataset.modes, "modes")
            mask &= modes[:, None] == feature.second_value
        return mask
    if feature.kind in {
        "central_distinct_pc_count",
        "central_distinct_pc_count_metric",
    }:
        signatures = central_tonic_pcset_signatures(dataset)
        lookup = np.asarray([index.bit_count() for index in range(4096)])
        mask = lookup[signatures] == value
        if feature.kind == "central_distinct_pc_count_metric":
            levels = _context_array(dataset.metric_levels, "metric_levels")
            mask &= levels[:, None] == feature.second_value
        return mask
    if feature.kind == "central_tonic_pcset":
        return central_tonic_pcset_signatures(dataset) == value
    if feature.kind == "central_bass_pcset":
        return central_bass_pcset_signatures(dataset) == value
    if feature.kind == "central_bass_pcset_metric":
        levels = _context_array(dataset.metric_levels, "metric_levels")
        return (central_bass_pcset_signatures(dataset) == value) & (
            (levels >= 2)[:, None] == bool(feature.second_value)
        )
    if feature.kind == "central_triadic_metric":
        if feature.second_value not in {0, 1}:
            raise ValueError("Metric triadic features require weak/strong status")
        levels = _context_array(dataset.metric_levels, "metric_levels")
        triadic = np.isin(
            central_bass_pcset_signatures(dataset),
            TRIADIC_BASS_PCSET_SIGNATURES,
        )
        return triadic & (
            (levels >= 2)[:, None] == bool(feature.second_value)
        )
    if feature.kind == "bass_pcset_transition":
        if feature.second_value is None:
            raise ValueError("A sonority transition requires two signatures")
        current = central_bass_pcset_signatures(dataset)
        following = bass_pcset_signatures(dataset, position=2)
        return (current == value) & (following == feature.second_value)
    if feature.kind == "any_pair_central_abs_class_metric":
        if feature.second_value not in {0, 1}:
            raise ValueError("Metric pair features require weak/strong status")
        levels = _context_array(dataset.metric_levels, "metric_levels")
        metric = ((levels >= 2) == bool(feature.second_value))[:, None]
        pair_mask = _universal_feature_mask(
            dataset,
            FeatureSpec(
                "any_pair_central_abs_class",
                -1,
                value=value,
            ),
            candidates,
        )
        return metric & pair_mask
    raise ValueError(f"Unknown contextual K3 feature: {feature.kind}")


def feature_mask(dataset: K3Dataset, feature: FeatureSpec) -> np.ndarray:
    """Evaluate one feature for every candidate in every opportunity."""

    candidates = dataset.candidate_pitches[None, :]
    if feature.kind in {
        "attacked_repeat_from_previous",
        "tonic_relative_class",
        "tonic_relative_class_mode",
        "central_distinct_pc_count",
        "central_distinct_pc_count_metric",
        "central_tonic_pcset",
        "central_bass_pcset",
        "central_bass_pcset_metric",
        "central_triadic_metric",
        "bass_pcset_transition",
        "any_pair_central_abs_class_metric",
    } or feature.kind.startswith("rare_tonal_"):
        return _contextual_feature_mask(dataset, feature, candidates)
    row_voice = dataset.voice_indices
    if feature.target_voice == -1:
        return _universal_feature_mask(dataset, feature, candidates)
    applies = row_voice[:, None] == feature.target_voice
    voice = feature.target_voice
    previous = dataset.blocks[:, 0, voice, None]
    # If the target voice does not attack in the following vertical block,
    # that pitch is the continuation of the central candidate. Counterfactual
    # alternatives must therefore propagate into the held block.
    following = np.where(
        dataset.attacks[:, 2, voice, None],
        dataset.blocks[:, 2, voice, None],
        candidates,
    )
    value = feature.value
    if value is None:
        raise ValueError(f"Feature {feature.key} has no numeric value")

    if feature.kind == "abs_class_from_previous":
        mask = np.abs(candidates - previous) % 12 == value
    elif feature.kind == "abs_class_to_next":
        mask = np.abs(following - candidates) % 12 == value
    elif feature.kind == "abs_step_from_previous_gt":
        mask = np.abs(candidates - previous) > value
    elif feature.kind == "abs_step_to_next_gt":
        mask = np.abs(following - candidates) > value
    elif feature.kind == "three_block_sign_shape":
        mask = (_sign(candidates - previous) == value) & (
            _sign(following - candidates) == feature.second_value
        )
    else:
        other = feature.other_voice
        if other is None:
            raise ValueError(f"Pair feature {feature.key} has no other voice")
        current_other = dataset.blocks[:, 1, other, None]
        previous_other = dataset.blocks[:, 0, other, None]
        target_motion = _sign(candidates - previous)
        other_motion = _sign(current_other - previous_other)
        same_nonzero = (target_motion == other_motion) & (target_motion != 0)
        if feature.kind == "central_pair_abs_class":
            mask = np.abs(candidates - current_other) % 12 == value
        elif feature.kind == "pair_abs_class_preserved_same_sign":
            source_class = (
                np.abs(dataset.blocks[:, 0, voice] - dataset.blocks[:, 0, other]) % 12
            )[:, None]
            target_class = np.abs(candidates - current_other) % 12
            mask = (source_class == value) & (target_class == value) & same_nonzero
        elif feature.kind == "pair_arrival_abs_class_same_sign":
            mask = (np.abs(candidates - current_other) % 12 == value) & same_nonzero
        elif feature.kind in {
            "central_ordered_gap_le",
            "previous_ordered_gap_le",
        }:
            reference = (
                current_other
                if feature.kind == "central_ordered_gap_le"
                else previous_other
            )
            gap = candidates - reference if voice < other else reference - candidates
            mask = gap <= value
        else:
            raise ValueError(f"Unknown K3 feature kind: {feature.kind}")
    return np.broadcast_to(applies, mask.shape) & mask


def _universal_feature_mask(
    dataset: K3Dataset,
    feature: FeatureSpec,
    candidates: np.ndarray,
) -> np.ndarray:
    """Evaluate a voice-invariant predicate before any specialization."""

    rows = np.arange(dataset.size)
    voices = dataset.voice_indices
    previous = dataset.blocks[rows, 0, voices, None]
    static_following = dataset.blocks[rows, 2, voices, None]
    next_attack = dataset.attacks[rows, 2, voices, None]
    following = np.where(next_attack, static_following, candidates)
    value = feature.value
    if value is None:
        raise ValueError(f"Feature {feature.key} has no numeric value")
    if feature.kind == "any_voice_adjacent_abs_class":
        return (np.abs(candidates - previous) % 12 == value) | (
            np.abs(following - candidates) % 12 == value
        )
    if feature.kind == "any_voice_adjacent_step_gt":
        return adjacent_step_sizes(dataset) > value
    if feature.kind == "any_voice_three_block_sign_shape":
        return (_sign(candidates - previous) == value) & (
            _sign(following - candidates) == feature.second_value
        )

    mask = np.zeros((dataset.size, dataset.candidate_pitches.size), dtype=bool)
    for voice in range(4):
        voice_rows = np.flatnonzero(voices == voice)
        if voice_rows.size == 0:
            continue
        voice_previous = dataset.blocks[voice_rows, 0, voice, None]
        for other in range(4):
            if other == voice:
                continue
            if (
                feature.kind == "any_adjacent_central_ordered_gap_le"
                and abs(other - voice) != 1
            ):
                continue
            current_other = dataset.blocks[voice_rows, 1, other, None]
            previous_other = dataset.blocks[voice_rows, 0, other, None]
            if feature.kind == "any_pair_central_abs_class":
                local = np.abs(candidates - current_other) % 12 == value
            elif feature.kind in {
                "any_pair_abs_class_preserved_same_sign",
                "any_pair_arrival_abs_class_same_sign",
            }:
                target_motion = _sign(candidates - voice_previous)
                other_motion = _sign(current_other - previous_other)
                same_nonzero = (target_motion == other_motion) & (target_motion != 0)
                target_class = np.abs(candidates - current_other) % 12
                local = (target_class == value) & same_nonzero
                if feature.kind == "any_pair_abs_class_preserved_same_sign":
                    source_class = (
                        np.abs(
                            dataset.blocks[voice_rows, 0, voice]
                            - dataset.blocks[voice_rows, 0, other]
                        )
                        % 12
                    )[:, None]
                    local &= source_class == value
            elif feature.kind == "any_adjacent_central_ordered_gap_le":
                gap = (
                    candidates - current_other
                    if voice < other
                    else current_other - candidates
                )
                local = gap <= value
            else:
                raise ValueError(f"Unknown universal K3 feature: {feature.kind}")
            mask[voice_rows] |= local
    return mask


def learn_register_logits(dataset: K3Dataset, alpha: float = 0.5) -> np.ndarray:
    """Learn the non-harmonic per-voice pitch baseline from train only."""

    logits = np.empty((4, dataset.candidate_pitches.size), dtype=np.float64)
    for voice in range(4):
        counts = np.full(dataset.candidate_pitches.size, alpha, dtype=np.float64)
        chosen = dataset.chosen_pitches[dataset.voice_indices == voice]
        np.add.at(counts, chosen - dataset.candidate_min, 1.0)
        probabilities = counts / counts.sum()
        logits[voice] = np.log(probabilities)
    return logits


def learn_tonal_logits(dataset: K3Dataset, alpha: float = 0.5) -> np.ndarray:
    """Learn tonic-relative pitch-class priors separately by declared mode."""

    tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")
    modes = _context_array(dataset.modes, "modes")
    relative = (dataset.chosen_pitches - tonics) % 12
    logits = np.empty((2, 12), dtype=np.float64)
    for mode in range(2):
        counts = np.full(12, alpha, dtype=np.float64)
        np.add.at(counts, relative[modes == mode], 1.0)
        logits[mode] = np.log(counts / counts.sum())
    return logits


def learn_voice_tonal_logits(
    dataset: K3Dataset,
    alpha: float = 0.5,
) -> np.ndarray:
    """Learn tonic-relative pitch classes by voice and declared mode."""

    tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")
    modes = _context_array(dataset.modes, "modes")
    relative = (dataset.chosen_pitches - tonics) % 12
    logits = np.empty((4, 2, 12), dtype=np.float64)
    for voice in range(4):
        for mode in range(2):
            counts = np.full(12, alpha, dtype=np.float64)
            rows = (dataset.voice_indices == voice) & (modes == mode)
            np.add.at(counts, relative[rows], 1.0)
            logits[voice, mode] = np.log(counts / counts.sum())
    return logits


def empirical_rare_pc_masks(
    dataset: K3Dataset,
    threshold: float,
) -> np.ndarray:
    """Encode voice/mode pitch classes below a learned marginal threshold."""

    if not 0.0 < threshold < 1.0:
        raise ValueError("Rarity threshold must lie strictly between zero and one")
    rare = np.exp(learn_voice_tonal_logits(dataset)) < threshold
    powers = np.left_shift(1, np.arange(12, dtype=np.int16))
    return np.sum(rare * powers, axis=2, dtype=np.int16)


def rare_tonal_feature_catalogue(
    dataset: K3Dataset,
    threshold: float,
    *,
    voices: Iterable[int] = range(4),
) -> tuple[FeatureSpec, ...]:
    """Generate signed-rule candidates for learned rare-class licences."""

    rare_masks = empirical_rare_pc_masks(dataset, threshold)
    rare_kinds = (
        "rare_tonal_class",
        "rare_tonal_incoming_step",
        "rare_tonal_leap_arrival",
        "rare_tonal_immediate_step_resolution",
        "rare_tonal_short_no_step_resolution",
        "rare_tonal_immediate_neighbor",
        "rare_tonal_immediate_passing",
        "rare_tonal_weak_metric",
        "rare_tonal_strong_metric",
    )
    features = []
    for voice in voices:
        if voice not in range(4):
            raise ValueError(f"Unknown voice index: {voice}")
        for mode in range(2):
            mask = int(rare_masks[voice, mode])
            if not mask:
                continue
            features.extend(
                FeatureSpec(
                    kind,
                    voice,
                    value=mask,
                    second_value=mode,
                    complexity=2 if kind == "rare_tonal_class" else 3,
                )
                for kind in rare_kinds
            )
    return tuple(features)


def rare_tonal_vertical_feature_catalogue(
    dataset: K3Dataset,
    threshold: float,
    *,
    voices: Iterable[int] = range(4),
    minimum_support: int = 20,
    minimum_piece_support: int = 5,
) -> tuple[FeatureSpec, ...]:
    """Enumerate rare choices licensed by observed local vertical signatures."""

    rare_masks = empirical_rare_pc_masks(dataset, threshold)
    signatures = central_bass_pcset_signatures(dataset)
    rows = np.arange(dataset.size)
    chosen_signatures = signatures[rows, dataset.chosen_indices]
    tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")
    modes = _context_array(dataset.modes, "modes")
    relative = (dataset.chosen_pitches - tonics) % 12
    features = []
    for voice in voices:
        if voice not in range(4):
            raise ValueError(f"Unknown voice index: {voice}")
        for mode in range(2):
            rare_mask = int(rare_masks[voice, mode])
            rare_choice = (
                (dataset.voice_indices == voice)
                & (modes == mode)
                & (
                    (np.right_shift(rare_mask, relative).astype(np.int8) & 1).astype(
                        bool
                    )
                )
            )
            for signature in np.unique(chosen_signatures[rare_choice]):
                support = rare_choice & (chosen_signatures == signature)
                if int(support.sum()) < minimum_support:
                    continue
                if (
                    int(np.unique(dataset.piece_ids[support]).size)
                    < minimum_piece_support
                ):
                    continue
                features.append(
                    FeatureSpec(
                        "rare_tonal_bass_pcset",
                        voice,
                        value=rare_mask,
                        second_value=mode * 4096 + int(signature),
                        complexity=4,
                    )
                )
    return tuple(features)


def contextual_base_scores(
    dataset: K3Dataset,
    register_logits: np.ndarray,
    tonal_logits: np.ndarray,
) -> np.ndarray:
    """Combine voice register and declared-key-relative categorical baselines."""

    tonics = _context_array(dataset.tonic_pcs, "tonic_pcs")[:, None]
    modes = _context_array(dataset.modes, "modes")
    relative = (dataset.candidate_pitches[None, :] - tonics) % 12
    if tonal_logits.shape == (2, 12):
        tonal = tonal_logits[
            modes[:, None],
            relative,
        ]
    elif tonal_logits.shape == (4, 2, 12):
        tonal = tonal_logits[
            dataset.voice_indices[:, None],
            modes[:, None],
            relative,
        ]
    else:
        raise ValueError("Tonal logits must have shape (2, 12) or (4, 2, 12)")
    return register_logits[dataset.voice_indices] + tonal


def contextual_feature_catalogue(
    dataset: K3Dataset,
    *,
    minimum_support: int = 100,
    minimum_piece_support: int = 10,
    voice_specific_repeats: bool = False,
    chromatic_rarity_threshold: float | None = None,
) -> tuple[FeatureSpec, ...]:
    """Generate readable context features and observed vertical fingerprints."""

    _context_array(dataset.tonic_pcs, "tonic_pcs")
    _context_array(dataset.modes, "modes")
    _context_array(dataset.metric_levels, "metric_levels")
    features = [FeatureSpec("attacked_repeat_from_previous", -1)]
    if voice_specific_repeats:
        features.extend(
            FeatureSpec("attacked_repeat_from_previous", voice) for voice in range(4)
        )
    if chromatic_rarity_threshold is not None:
        features.extend(
            rare_tonal_feature_catalogue(
                dataset,
                chromatic_rarity_threshold,
            )
        )
    features.extend(
        FeatureSpec("central_distinct_pc_count", -1, value=count)
        for count in range(1, 5)
    )
    features.extend(
        FeatureSpec(
            "central_distinct_pc_count_metric",
            -1,
            value=count,
            second_value=level,
            complexity=2,
        )
        for count in range(1, 5)
        for level in range(4)
    )
    rows = np.arange(dataset.size)
    chosen = dataset.chosen_indices
    signature_families = (
        ("central_tonic_pcset", central_tonic_pcset_signatures(dataset)),
        ("central_bass_pcset", central_bass_pcset_signatures(dataset)),
    )
    for kind, signatures in signature_families:
        observed = signatures[rows, chosen]
        for signature in np.unique(observed):
            support = observed == signature
            if int(support.sum()) < minimum_support:
                continue
            if int(np.unique(dataset.piece_ids[support]).size) < minimum_piece_support:
                continue
            features.append(
                FeatureSpec(
                    kind,
                    -1,
                    value=int(signature),
                    complexity=3,
                )
            )
    unique = {feature.key: feature for feature in features}
    return tuple(unique[key] for key in sorted(unique))


def feature_matrix(
    dataset: K3Dataset,
    features: Sequence[FeatureSpec],
) -> np.ndarray:
    if not features:
        return np.empty(
            (dataset.size, dataset.candidate_pitches.size, 0),
            dtype=np.uint8,
        )
    return np.stack(
        [feature_mask(dataset, feature) for feature in features],
        axis=2,
    ).astype(np.uint8)


def probabilities(
    dataset: K3Dataset,
    register_logits: np.ndarray,
    matrix: np.ndarray | None = None,
    weights: np.ndarray | None = None,
    *,
    base_scores: np.ndarray | None = None,
) -> np.ndarray:
    scores = (
        register_logits[dataset.voice_indices].copy()
        if base_scores is None
        else np.asarray(base_scores, dtype=np.float64).copy()
    )
    if scores.shape != (dataset.size, dataset.candidate_pitches.size):
        raise ValueError("Base scores do not match the K3 decision matrix")
    if matrix is not None and weights is not None and weights.size:
        scores += np.tensordot(matrix, weights, axes=([2], [0]))
    scores -= scores.max(axis=1, keepdims=True)
    exponentials = np.exp(scores)
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def conditional_nll(
    dataset: K3Dataset,
    register_logits: np.ndarray,
    matrix: np.ndarray | None = None,
    weights: np.ndarray | None = None,
    *,
    base_scores: np.ndarray | None = None,
) -> float:
    probs = probabilities(
        dataset,
        register_logits,
        matrix,
        weights,
        base_scores=base_scores,
    )
    chosen = probs[np.arange(dataset.size), dataset.chosen_indices]
    return float(-np.log(np.maximum(chosen, 1e-12)).mean())


def residual_statistic(
    dataset: K3Dataset,
    probs: np.ndarray,
    mask: np.ndarray,
    complexity: int,
    complexity_penalty: float,
) -> ResidualStatistic | None:
    rows = np.arange(dataset.size)
    chosen = mask[rows, dataset.chosen_indices].astype(np.float64)
    expected = np.sum(probs * mask, axis=1)
    testable = mask.any(axis=1) & ~mask.all(axis=1)
    if not np.any(testable):
        return None
    variance = float(np.sum(expected * (1.0 - expected)))
    if variance <= 1e-12:
        return None
    residual_sum = float(np.sum(chosen - expected))
    gradient = residual_sum / dataset.size
    hessian = variance / dataset.size
    approximate_gain = 0.5 * gradient * gradient / hessian
    description_cost = (
        complexity_penalty * complexity * math.log(max(dataset.size, 2)) / dataset.size
    )
    return ResidualStatistic(
        gradient=gradient,
        variance=variance,
        z_score=residual_sum / math.sqrt(variance),
        approximate_nll_gain=approximate_gain,
        observed_rate=float(chosen[testable].mean()),
        expected_rate=float(expected[testable].mean()),
        testable_opportunities=int(testable.sum()),
        piece_support=int(np.unique(dataset.piece_ids[testable]).size),
        column_score=approximate_gain - description_cost,
    )


def fit_weights(
    train: K3Dataset,
    validation: K3Dataset,
    register_logits: np.ndarray,
    train_matrix: np.ndarray,
    validation_matrix: np.ndarray,
    *,
    l1: float,
    max_steps: int,
    learning_rate: float,
    train_base_scores: np.ndarray | None = None,
    validation_base_scores: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fit signed K3 rule weights with Adam and proximal L1 shrinkage."""

    count = train_matrix.shape[2]
    weights = np.zeros(count, dtype=np.float64)
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    best = weights.copy()
    best_validation = math.inf
    history = []
    for step in range(1, max_steps + 1):
        probs = probabilities(
            train,
            register_logits,
            train_matrix,
            weights,
            base_scores=train_base_scores,
        )
        probs[np.arange(train.size), train.chosen_indices] -= 1.0
        gradient = (
            np.einsum("ncr,nc->r", train_matrix, probs, optimize=True) / train.size
        )
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient**2
        corrected_first = first / (1.0 - 0.9**step)
        corrected_second = second / (1.0 - 0.999**step)
        weights -= learning_rate * corrected_first / (np.sqrt(corrected_second) + 1e-8)
        weights = np.sign(weights) * np.maximum(
            np.abs(weights) - learning_rate * l1, 0.0
        )
        if step == 1 or step % 10 == 0 or step == max_steps:
            train_nll = conditional_nll(
                train,
                register_logits,
                train_matrix,
                weights,
                base_scores=train_base_scores,
            )
            validation_nll = conditional_nll(
                validation,
                register_logits,
                validation_matrix,
                weights,
                base_scores=validation_base_scores,
            )
            history.append(
                {
                    "step": step,
                    "train_nll": train_nll,
                    "validation_nll": validation_nll,
                    "active_weights": int((np.abs(weights) >= 0.05).sum()),
                }
            )
            if validation_nll < best_validation:
                best_validation = validation_nll
                best = weights.copy()
    return best, {"best_validation_nll": best_validation, "history": history}


def feature_from_model_record(record: dict[str, Any]) -> FeatureSpec:
    payload = record.get("feature", record)
    return FeatureSpec.from_dict(payload)


def shared_potential_rows(
    dataset: K3Dataset,
    group_ids: np.ndarray | None = None,
) -> np.ndarray:
    """Select one representative per joint world and central K3 block.

    A chord or sonority-transition potential belongs to the vertical block,
    not to every voice attacking in that block. Conditional note prediction
    legitimately exposes the potential in each voice's conditional, whereas
    a joint-state energy must count it exactly once.
    """

    central = dataset.offsets[:, 1]
    groups = (
        np.zeros(dataset.size, dtype=np.int64)
        if group_ids is None
        else np.asarray(group_ids, dtype=np.int64)
    )
    if groups.shape != (dataset.size,):
        raise ValueError("Joint-world group ids must match the K3 dataset")
    keys = np.rec.fromarrays((groups, central), names=("group", "central"))
    _, indices = np.unique(keys, return_index=True)
    mask = np.zeros(dataset.size, dtype=bool)
    mask[indices] = True
    return mask


def gibbs_sample(
    initial_blocks: np.ndarray,
    fixed: np.ndarray,
    *,
    candidate_min: int,
    candidate_max: int,
    register_logits: np.ndarray,
    features: Sequence[FeatureSpec],
    weights: np.ndarray,
    sweeps: int,
    seed: int,
    temperature: float = 1.0,
) -> np.ndarray:
    """Sample a dense block lattice using the same K3 feature evaluator."""

    blocks = np.asarray(initial_blocks, dtype=np.int16).copy()
    fixed_mask = np.asarray(fixed, dtype=bool)
    if blocks.ndim != 2 or blocks.shape[1] != 4 or fixed_mask.shape != blocks.shape:
        raise ValueError("Expected blocks and fixed masks with shape (time, 4)")
    if blocks.shape[0] < 3:
        raise ValueError("K3 Gibbs sampling requires at least three blocks")
    mutable = [
        (time, voice)
        for time in range(1, blocks.shape[0] - 1)
        for voice in range(4)
        if not fixed_mask[time, voice]
    ]
    if not mutable:
        return blocks
    generator = np.random.default_rng(seed)
    candidate_pitches = np.arange(candidate_min, candidate_max + 1)
    for _ in range(sweeps):
        generator.shuffle(mutable)
        for time, voice in mutable:
            kernel = blocks[time - 1 : time + 2][None, :, :]
            dataset = K3Dataset(
                piece_ids=np.asarray(["generation"]),
                offsets=np.asarray([[time - 1, time, time + 1]], dtype=np.float32),
                voice_indices=np.asarray([voice], dtype=np.int8),
                blocks=kernel,
                attacks=np.ones((1, 3, 4), dtype=bool),
                candidate_min=candidate_min,
                candidate_max=candidate_max,
            )
            matrix = feature_matrix(dataset, features)
            scores = register_logits[voice] + np.tensordot(
                matrix[0], weights, axes=([1], [0])
            )
            scores = scores / max(temperature, 1e-6)
            scores -= scores.max()
            probs = np.exp(scores)
            probs /= probs.sum()
            blocks[time, voice] = generator.choice(candidate_pitches, p=probs)
    return blocks


def attack_segments(attacks: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    """Return ``(start, end, voice)`` spans controlled by each attack."""

    attack_grid = np.asarray(attacks, dtype=bool)
    if attack_grid.ndim != 2 or attack_grid.shape[1] != 4:
        raise ValueError("Expected attacks with shape (time, 4)")
    if attack_grid.shape[0] < 3:
        raise ValueError("K3 rhythmic sampling requires at least three blocks")
    if not attack_grid[0].all():
        raise ValueError("Every voice must attack in the first lattice block")
    segments = []
    for voice in range(4):
        starts = np.flatnonzero(attack_grid[:, voice])
        ends = np.concatenate((starts[1:], np.asarray([attack_grid.shape[0]])))
        segments.extend(
            (int(start), int(end), voice)
            for start, end in zip(starts, ends, strict=True)
        )
    return tuple(sorted(segments))


def _decision_dataset(
    blocks: np.ndarray,
    attacks: np.ndarray,
    central_times: Sequence[int],
    candidate_min: int,
    candidate_max: int,
    tonic_pc: int | None = None,
    mode: int | None = None,
    metric_levels: np.ndarray | None = None,
) -> K3Dataset | None:
    decisions = [
        (time, voice)
        for time in central_times
        if 0 < time < blocks.shape[0] - 1
        for voice in range(4)
        if attacks[time, voice]
    ]
    if not decisions:
        return None
    return K3Dataset(
        piece_ids=np.full(len(decisions), "generation"),
        offsets=np.asarray(
            [[time - 1, time, time + 1] for time, _ in decisions],
            dtype=np.float32,
        ),
        voice_indices=np.asarray([voice for _, voice in decisions], dtype=np.int8),
        blocks=np.asarray(
            [blocks[time - 1 : time + 2] for time, _ in decisions],
            dtype=np.int16,
        ),
        attacks=np.asarray(
            [attacks[time - 1 : time + 2] for time, _ in decisions],
            dtype=bool,
        ),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        tonic_pcs=(
            None
            if tonic_pc is None
            else np.full(len(decisions), tonic_pc, dtype=np.int8)
        ),
        modes=(None if mode is None else np.full(len(decisions), mode, dtype=np.int8)),
        metric_levels=(
            None
            if metric_levels is None
            else np.asarray(
                [metric_levels[time] for time, _ in decisions],
                dtype=np.int8,
            )
        ),
    )


def _state_energy(
    blocks: np.ndarray,
    attacks: np.ndarray,
    central_times: Sequence[int],
    *,
    candidate_min: int,
    candidate_max: int,
    register_logits: np.ndarray,
    features: Sequence[FeatureSpec],
    weights: np.ndarray,
    tonal_logits: np.ndarray | None = None,
    tonic_pc: int | None = None,
    mode: int | None = None,
    metric_levels: np.ndarray | None = None,
) -> float:
    dataset = _decision_dataset(
        blocks,
        attacks,
        central_times,
        candidate_min,
        candidate_max,
        tonic_pc,
        mode,
        metric_levels,
    )
    if dataset is None:
        return 0.0
    if np.any(dataset.chosen_indices < 0) or np.any(
        dataset.chosen_indices >= dataset.candidate_pitches.size
    ):
        return -math.inf
    rows = np.arange(dataset.size)
    if tonal_logits is None:
        score = register_logits[dataset.voice_indices, dataset.chosen_indices]
    else:
        base_scores = contextual_base_scores(
            dataset,
            register_logits,
            tonal_logits,
        )
        score = base_scores[rows, dataset.chosen_indices]
    if features:
        matrix = feature_matrix(dataset, features)
        chosen_features = matrix[rows, dataset.chosen_indices]
        representatives = shared_potential_rows(dataset)
        for index, (feature, weight) in enumerate(
            zip(features, weights, strict=True)
        ):
            applies = (
                representatives
                if feature.kind in SHARED_POTENTIAL_KINDS
                else np.ones(dataset.size, dtype=bool)
            )
            score[applies] += weight * chosen_features[applies, index]
    return float(score.sum())


def _candidate_state_energies(
    blocks: np.ndarray,
    attacks: np.ndarray,
    central_times: Sequence[int],
    start: int,
    end: int,
    voice: int,
    candidates: np.ndarray,
    *,
    candidate_min: int,
    candidate_max: int,
    register_logits: np.ndarray,
    features: Sequence[FeatureSpec],
    weights: np.ndarray,
    tonal_logits: np.ndarray | None = None,
    tonic_pc: int | None = None,
    mode: int | None = None,
    metric_levels: np.ndarray | None = None,
) -> np.ndarray:
    """Score every proposed segment pitch in one vectorized feature pass."""

    previous = blocks[start:end, voice].copy()
    worlds = []
    group_ids = []
    try:
        for group, candidate in enumerate(candidates):
            blocks[start:end, voice] = candidate
            dataset = _decision_dataset(
                blocks,
                attacks,
                central_times,
                candidate_min,
                candidate_max,
                tonic_pc,
                mode,
                metric_levels,
            )
            if dataset is not None:
                worlds.append(dataset)
                group_ids.append(np.full(dataset.size, group, dtype=np.int16))
    finally:
        blocks[start:end, voice] = previous
    if not worlds:
        return np.zeros(candidates.size, dtype=np.float64)
    dataset = K3Dataset(
        piece_ids=np.concatenate([world.piece_ids for world in worlds]),
        offsets=np.concatenate([world.offsets for world in worlds]),
        voice_indices=np.concatenate([world.voice_indices for world in worlds]),
        blocks=np.concatenate([world.blocks for world in worlds]),
        attacks=np.concatenate([world.attacks for world in worlds]),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        tonic_pcs=(
            None
            if tonic_pc is None
            else np.concatenate([world.tonic_pcs for world in worlds])
        ),
        modes=(
            None if mode is None else np.concatenate([world.modes for world in worlds])
        ),
        metric_levels=(
            None
            if metric_levels is None
            else np.concatenate([world.metric_levels for world in worlds])
        ),
    )
    rows = np.arange(dataset.size)
    chosen = dataset.chosen_indices
    if np.any(chosen < 0) or np.any(chosen >= candidates.size):
        return np.full(candidates.size, -math.inf, dtype=np.float64)
    if tonal_logits is None:
        row_scores = register_logits[dataset.voice_indices, chosen].copy()
    else:
        base_scores = contextual_base_scores(
            dataset,
            register_logits,
            tonal_logits,
        )
        row_scores = base_scores[rows, chosen]
    joint_groups = np.concatenate(group_ids)
    representatives = shared_potential_rows(dataset, joint_groups)
    for feature, weight in zip(features, weights, strict=True):
        mask = feature_mask(dataset, feature)
        contribution = mask[rows, chosen]
        if feature.kind in SHARED_POTENTIAL_KINDS:
            contribution &= representatives
        row_scores += weight * contribution
    return np.bincount(
        joint_groups,
        weights=row_scores,
        minlength=candidates.size,
    )


def rhythmic_gibbs_sample(
    initial_blocks: np.ndarray,
    attacks: np.ndarray,
    fixed: np.ndarray,
    *,
    candidate_min: int,
    candidate_max: int,
    register_logits: np.ndarray,
    features: Sequence[FeatureSpec],
    weights: np.ndarray,
    sweeps: int,
    seed: int,
    temperature: float = 1.0,
    tonal_logits: np.ndarray | None = None,
    tonic_pc: int | None = None,
    mode: int | None = None,
    metric_levels: np.ndarray | None = None,
) -> np.ndarray:
    """Sample attack pitches while preserving every per-voice hold span.

    A sampled attack controls its pitch until the next attack in that voice.
    Candidate scores sum every attack-centred K3 energy whose kernel intersects
    the changed span.
    """

    blocks = np.asarray(initial_blocks, dtype=np.int16).copy()
    attack_grid = np.asarray(attacks, dtype=bool)
    fixed_mask = np.asarray(fixed, dtype=bool)
    if (
        blocks.ndim != 2
        or blocks.shape[1] != 4
        or attack_grid.shape != blocks.shape
        or fixed_mask.shape != blocks.shape
    ):
        raise ValueError("Expected blocks, attacks and fixed with shape (time, 4)")
    if register_logits.shape != (4, candidate_max - candidate_min + 1):
        raise ValueError("Register logits do not match the declared pitch domain")
    if len(features) != weights.size:
        raise ValueError("One learned weight is required per K3 feature")
    if tonal_logits is not None and (
        tonal_logits.shape not in {(2, 12), (4, 2, 12)}
        or tonic_pc is None
        or mode is None
        or metric_levels is None
    ):
        raise ValueError("Tonal sampling requires key, mode and metric context")
    segments = attack_segments(attack_grid)
    for start, end, voice in segments:
        if not np.all(blocks[start:end, voice] == blocks[start, voice]):
            raise ValueError("A held span changes pitch before its next attack")
    mutable = [
        segment
        for segment in segments
        if not fixed_mask[segment[0] : segment[1], segment[2]].any()
    ]
    if not mutable:
        return blocks
    generator = np.random.default_rng(seed)
    candidates = np.arange(candidate_min, candidate_max + 1, dtype=np.int16)
    scale = max(temperature, 1e-6)
    for _ in range(sweeps):
        generator.shuffle(mutable)
        for start, end, voice in mutable:
            affected_times = range(
                max(1, start - 1),
                min(blocks.shape[0] - 2, end) + 1,
            )
            scores = _candidate_state_energies(
                blocks,
                attack_grid,
                affected_times,
                start,
                end,
                voice,
                candidates,
                candidate_min=candidate_min,
                candidate_max=candidate_max,
                register_logits=register_logits,
                features=features,
                weights=weights,
                tonal_logits=tonal_logits,
                tonic_pc=tonic_pc,
                mode=mode,
                metric_levels=metric_levels,
            )
            scores /= scale
            scores -= scores.max()
            probabilities = np.exp(scores)
            probabilities /= probabilities.sum()
            selected = generator.choice(candidates, p=probabilities)
            blocks[start:end, voice] = selected
    return blocks
