#!/usr/bin/env python3
"""Differentiable, sparse rule induction POC on the historical Bach corpus.

The learner sees numeric pitch relations, not named musicological predicates.
It uses the conditional-likelihood gradient both to guide clause search and to
fit a sparse additive choice model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import tarfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED_ARCHIVE_SHA256 = (
    "73a33407459e59fc5cfa7ea268088e5e10db9354e01ceceb2295d56373b937d2"
)
VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
FAMILY_ORDER = (
    "source_interval_mod12",
    "target_interval_mod12",
    "soprano_direction",
    "bass_direction",
    "soprano_leap_gt",
    "learned_same_nonzero_sign",
)
FAMILY_INDEX = {name: index for index, name in enumerate(FAMILY_ORDER)}


@dataclass(frozen=True, order=True)
class Atom:
    """One generic numeric test."""

    family: str
    value: int

    @property
    def label(self) -> str:
        if self.family == "source_interval_mod12":
            return f"abs(prev_s-prev_b)%12 == {self.value}"
        if self.family == "target_interval_mod12":
            return f"abs(candidate_s-current_b)%12 == {self.value}"
        if self.family == "soprano_direction":
            return f"sign(candidate_s-prev_s) == {direction_name(self.value)}"
        if self.family == "bass_direction":
            return f"sign(current_b-prev_b) == {direction_name(self.value)}"
        if self.family == "soprano_leap_gt":
            return f"abs(candidate_s-prev_s) > {self.value}"
        if self.family == "learned_same_nonzero_sign":
            return "LEARNED_PREDICATE_001 == true"
        raise ValueError(f"Unknown atom family: {self.family}")


@dataclass(frozen=True)
class Clause:
    """A canonical conjunction with at most one atom per family."""

    atoms: tuple[Atom, ...]

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(self.atoms, key=lambda atom: (FAMILY_INDEX[atom.family], atom))
        )
        if ordered != self.atoms:
            raise ValueError("Clause atoms must be in canonical family order")
        families = [atom.family for atom in self.atoms]
        if len(families) != len(set(families)):
            raise ValueError("A clause cannot contain two atoms from one family")

    @property
    def key(self) -> str:
        return " AND ".join(atom.label for atom in self.atoms)

    @property
    def complexity(self) -> int:
        return len(self.atoms)


@dataclass
class Opportunities:
    """Aligned outer-voice transitions and their observed choices."""

    piece_ids: np.ndarray
    offsets_previous: np.ndarray
    offsets_current: np.ndarray
    previous_soprano: np.ndarray
    chosen_soprano: np.ndarray
    previous_bass: np.ndarray
    current_bass: np.ndarray
    candidate_min: int
    candidate_max: int

    @property
    def candidate_pitches(self) -> np.ndarray:
        return np.arange(self.candidate_min, self.candidate_max + 1, dtype=np.int16)

    @property
    def chosen_indices(self) -> np.ndarray:
        return (self.chosen_soprano - self.candidate_min).astype(np.int64)

    @property
    def size(self) -> int:
        return int(self.chosen_soprano.shape[0])

    def take(self, indices: np.ndarray) -> Opportunities:
        return Opportunities(
            piece_ids=self.piece_ids[indices],
            offsets_previous=self.offsets_previous[indices],
            offsets_current=self.offsets_current[indices],
            previous_soprano=self.previous_soprano[indices],
            chosen_soprano=self.chosen_soprano[indices],
            previous_bass=self.previous_bass[indices],
            current_bass=self.current_bass[indices],
            candidate_min=self.candidate_min,
            candidate_max=self.candidate_max,
        )


@dataclass(frozen=True)
class ClauseStatistic:
    clause: Clause
    gradient: float
    z_score: float
    observed_rate: float
    availability_rate: float
    testable_opportunities: int
    candidate_support: int

    @property
    def search_score(self) -> float:
        return abs(self.z_score) - 0.35 * (self.clause.complexity - 1)


def direction_name(value: int) -> str:
    return {-1: "negative", 0: "zero", 1: "positive"}[value]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_archive_path() -> Path:
    return (
        repository_root().parent
        / "deepbach-reference/resources/cache/music21-3.1.0.tar.gz"
    )


def default_manifest_path() -> Path:
    return repository_root() / (
        "harmonizer/bach_rule_induction/corpus/manifest.music21-3.1.0.json"
    )


def experiment_root() -> Path:
    return Path(__file__).resolve().parent


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_included_pieces(
    manifest_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pieces = [piece for piece in manifest["pieces"] if piece["included"]]
    if len(pieces) != 352:
        raise ValueError(f"Expected 352 included pieces, found {len(pieces)}")
    return manifest, pieces


def deterministic_splits(piece_ids: Sequence[str], seed: int) -> dict[str, list[str]]:
    shuffled = sorted(piece_ids)
    random.Random(seed).shuffle(shuffled)
    return {
        "train": shuffled[:246],
        "validation": shuffled[246:299],
        "test": shuffled[299:352],
    }


def materialize_scores(
    archive_path: Path,
    pieces: Sequence[dict[str, Any]],
    destination: Path,
) -> dict[str, Path]:
    """Extract exactly the selected historical score files."""

    destination.mkdir(parents=True, exist_ok=True)
    requested = {
        f"music21-3.1.0/music21/corpus/{piece['source_path']}": piece["id"]
        for piece in pieces
    }
    paths: dict[str, Path] = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers()}
        missing = sorted(set(requested) - set(members))
        if missing:
            raise FileNotFoundError(f"Archive is missing {len(missing)} scores")
        for member_name, piece_id in requested.items():
            output = destination / Path(member_name).name
            expected_hash = next(
                piece["sha256"] for piece in pieces if piece["id"] == piece_id
            )
            if not output.exists() or sha256_file(output) != expected_hash:
                source = archive.extractfile(members[member_name])
                if source is None:
                    raise OSError(f"Cannot extract {member_name}")
                output.write_bytes(source.read())
            paths[piece_id] = output
    return paths


def note_events(part: Any) -> list[tuple[float, float, int | None]]:
    """Return flattened note/rest events as (start, end, midi-or-None)."""

    events: list[tuple[float, float, int | None]] = []
    for element in part.flatten().notesAndRests:
        start = float(element.offset)
        end = start + float(element.duration.quarterLength)
        pitch = int(element.pitch.midi) if element.isNote else None
        events.append((start, end, pitch))
    events.sort(key=lambda event: event[0])
    return events


def sounding_pitch(
    events: Sequence[tuple[float, float, int | None]], offset: float
) -> int | None:
    for start, end, pitch in events:
        if start - 1e-8 <= offset < end - 1e-8:
            return pitch
    return None


def extract_piece_opportunities(
    score_path: Path,
    piece_id: str,
    candidate_min: int,
    candidate_max: int,
) -> list[tuple[str, float, float, int, int, int, int]]:
    from music21 import converter

    score = converter.parse(score_path)
    parts = {part.partName: part for part in score.parts}
    if tuple(parts) != VOICE_NAMES and set(parts) != set(VOICE_NAMES):
        raise ValueError(f"{piece_id}: unexpected parts {tuple(parts)}")
    soprano = note_events(parts["Soprano"])
    bass = note_events(parts["Bass"])
    opportunities: list[tuple[str, float, float, int, int, int, int]] = []

    previous_note: tuple[float, float, int | None] | None = None
    for current in soprano:
        current_start, _, current_pitch = current
        if current_pitch is None:
            previous_note = None
            continue
        if previous_note is None or previous_note[2] is None:
            previous_note = current
            continue
        previous_start, previous_end, previous_pitch_or_none = previous_note
        previous_pitch = int(previous_pitch_or_none)
        # Skip a melodic transition over an explicit rest.
        if abs(previous_end - current_start) > 1e-7:
            previous_note = current
            continue
        previous_bass = sounding_pitch(bass, previous_start)
        current_bass = sounding_pitch(bass, current_start)
        if previous_bass is None or current_bass is None:
            previous_note = current
            continue
        if not candidate_min <= current_pitch <= candidate_max:
            previous_note = current
            continue
        opportunities.append(
            (
                piece_id,
                previous_start,
                current_start,
                previous_pitch,
                current_pitch,
                previous_bass,
                current_bass,
            )
        )
        previous_note = current
    return opportunities


def build_opportunities(
    score_paths: dict[str, Path],
    candidate_min: int,
    candidate_max: int,
) -> Opportunities:
    rows: list[tuple[str, float, float, int, int, int, int]] = []
    for index, (piece_id, score_path) in enumerate(
        sorted(score_paths.items()), start=1
    ):
        rows.extend(
            extract_piece_opportunities(
                score_path, piece_id, candidate_min, candidate_max
            )
        )
        if index % 25 == 0 or index == len(score_paths):
            print(
                f"[corpus] parsed {index}/{len(score_paths)} pieces, "
                f"{len(rows)} opportunities",
                flush=True,
            )
    if not rows:
        raise RuntimeError("No opportunities were extracted")
    columns = list(zip(*rows, strict=True))
    return Opportunities(
        piece_ids=np.asarray(columns[0], dtype=str),
        offsets_previous=np.asarray(columns[1], dtype=np.float32),
        offsets_current=np.asarray(columns[2], dtype=np.float32),
        previous_soprano=np.asarray(columns[3], dtype=np.int16),
        chosen_soprano=np.asarray(columns[4], dtype=np.int16),
        previous_bass=np.asarray(columns[5], dtype=np.int16),
        current_bass=np.asarray(columns[6], dtype=np.int16),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
    )


def save_opportunities(path: Path, opportunities: Opportunities) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        piece_ids=opportunities.piece_ids,
        offsets_previous=opportunities.offsets_previous,
        offsets_current=opportunities.offsets_current,
        previous_soprano=opportunities.previous_soprano,
        chosen_soprano=opportunities.chosen_soprano,
        previous_bass=opportunities.previous_bass,
        current_bass=opportunities.current_bass,
        candidate_min=np.asarray(opportunities.candidate_min),
        candidate_max=np.asarray(opportunities.candidate_max),
    )


def load_opportunities(path: Path) -> Opportunities:
    data = np.load(path)
    return Opportunities(
        piece_ids=data["piece_ids"],
        offsets_previous=data["offsets_previous"],
        offsets_current=data["offsets_current"],
        previous_soprano=data["previous_soprano"],
        chosen_soprano=data["chosen_soprano"],
        previous_bass=data["previous_bass"],
        current_bass=data["current_bass"],
        candidate_min=int(data["candidate_min"]),
        candidate_max=int(data["candidate_max"]),
    )


def subset_for_piece_ids(
    opportunities: Opportunities, piece_ids: Iterable[str]
) -> Opportunities:
    selected = np.isin(opportunities.piece_ids, np.asarray(list(piece_ids)))
    return opportunities.take(np.flatnonzero(selected))


def shuffle_choices_within_pieces(
    opportunities: Opportunities, seed: int
) -> Opportunities:
    """Break local relations while preserving each piece's soprano histogram."""

    shuffled = opportunities.take(np.arange(opportunities.size))
    shuffled.chosen_soprano = shuffled.chosen_soprano.copy()
    generator = np.random.default_rng(seed)
    for piece_id in np.unique(shuffled.piece_ids):
        indices = np.flatnonzero(shuffled.piece_ids == piece_id)
        shuffled.chosen_soprano[indices] = generator.permutation(
            shuffled.chosen_soprano[indices]
        )
    return shuffled


def atoms(*, include_derived: bool = False) -> list[Atom]:
    result = [Atom("source_interval_mod12", value) for value in range(12)]
    result.extend(Atom("target_interval_mod12", value) for value in range(12))
    result.extend(Atom("soprano_direction", value) for value in (-1, 0, 1))
    result.extend(Atom("bass_direction", value) for value in (-1, 0, 1))
    result.extend(Atom("soprano_leap_gt", value) for value in (1, 2, 4, 7, 12))
    if include_derived:
        result.append(Atom("learned_same_nonzero_sign", 1))
    return result


def sign(values: np.ndarray) -> np.ndarray:
    return np.sign(values).astype(np.int8)


def atom_masks(
    opportunities: Opportunities, atom_list: Sequence[Atom]
) -> dict[Atom, np.ndarray]:
    candidates = opportunities.candidate_pitches[None, :]
    previous_soprano = opportunities.previous_soprano[:, None]
    previous_bass = opportunities.previous_bass[:, None]
    current_bass = opportunities.current_bass[:, None]
    source_interval = np.abs(previous_soprano - previous_bass) % 12
    target_interval = np.abs(candidates - current_bass) % 12
    soprano_delta = candidates - previous_soprano
    bass_delta = current_bass - previous_bass

    masks: dict[Atom, np.ndarray] = {}
    shape = target_interval.shape
    for atom in atom_list:
        if atom.family == "source_interval_mod12":
            mask = np.broadcast_to(source_interval == atom.value, shape)
        elif atom.family == "target_interval_mod12":
            mask = target_interval == atom.value
        elif atom.family == "soprano_direction":
            mask = sign(soprano_delta) == atom.value
        elif atom.family == "bass_direction":
            mask = np.broadcast_to(sign(bass_delta) == atom.value, shape)
        elif atom.family == "soprano_leap_gt":
            mask = np.abs(soprano_delta) > atom.value
        elif atom.family == "learned_same_nonzero_sign":
            mask = ((sign(soprano_delta) == 1) & (sign(bass_delta) == 1)) | (
                (sign(soprano_delta) == -1) & (sign(bass_delta) == -1)
            )
        else:
            raise ValueError(atom.family)
        masks[atom] = np.asarray(mask, dtype=np.bool_)
    return masks


def clause_mask(clause: Clause, masks: dict[Atom, np.ndarray]) -> np.ndarray:
    result = masks[clause.atoms[0]].copy()
    for atom in clause.atoms[1:]:
        result &= masks[atom]
    return result


def uniform_residual(opportunities: Opportunities) -> np.ndarray:
    candidate_count = opportunities.candidate_pitches.shape[0]
    residual = np.full(
        (opportunities.size, candidate_count),
        -1.0 / candidate_count,
        dtype=np.float32,
    )
    residual[np.arange(opportunities.size), opportunities.chosen_indices] += 1.0
    return residual


def statistic_for_clause(
    clause: Clause,
    masks: dict[Atom, np.ndarray],
    residual: np.ndarray,
    chosen_indices: np.ndarray,
) -> ClauseStatistic | None:
    mask = clause_mask(clause, masks)
    any_candidate = mask.any(axis=1)
    all_candidates = mask.all(axis=1)
    testable = any_candidate & ~all_candidates
    testable_count = int(testable.sum())
    candidate_support = int(mask.sum())
    if testable_count == 0 or candidate_support == 0:
        return None

    rows = np.arange(mask.shape[0])
    chosen = mask[rows, chosen_indices]
    availability_by_opportunity = mask.mean(axis=1)
    observed = float(chosen[testable].mean())
    availability = float(availability_by_opportunity[testable].mean())
    centered = chosen.astype(np.float64) - availability_by_opportunity
    variance = float(
        np.sum(availability_by_opportunity * (1.0 - availability_by_opportunity))
    )
    z_score = float(centered.sum() / math.sqrt(max(variance, 1e-9)))
    gradient = float(np.sum(mask * residual) / mask.shape[0])
    return ClauseStatistic(
        clause=clause,
        gradient=gradient,
        z_score=z_score,
        observed_rate=observed,
        availability_rate=availability,
        testable_opportunities=testable_count,
        candidate_support=candidate_support,
    )


def search_clauses(
    opportunities: Opportunities,
    masks: dict[Atom, np.ndarray],
    residual: np.ndarray,
    max_depth: int,
    beam_size: int,
    min_testable: int,
) -> list[ClauseStatistic]:
    """Beam search ranked by the conditional-likelihood gradient tail."""

    atom_list = list(masks)
    chosen_indices = opportunities.chosen_indices
    beam = [Clause((atom,)) for atom in atom_list]
    all_statistics: dict[str, ClauseStatistic] = {}

    for depth in range(1, max_depth + 1):
        statistics: list[ClauseStatistic] = []
        for clause in beam:
            statistic = statistic_for_clause(clause, masks, residual, chosen_indices)
            if (
                statistic is not None
                and statistic.testable_opportunities >= min_testable
            ):
                statistics.append(statistic)
                previous = all_statistics.get(clause.key)
                if previous is None or statistic.search_score > previous.search_score:
                    all_statistics[clause.key] = statistic
        statistics.sort(key=lambda item: item.search_score, reverse=True)
        kept = statistics[:beam_size]
        print(
            f"[search] depth={depth} evaluated={len(beam)} "
            f"admissible={len(statistics)} kept={len(kept)}",
            flush=True,
        )
        if depth == max_depth:
            break
        extensions: dict[str, Clause] = {}
        # A context-only singleton has no within-opportunity marginal and thus
        # no gradient by itself. Keep it as a depth-one prefix so that clauses
        # such as source-class AND target-class remain discoverable.
        extension_clauses = (
            beam if depth == 1 else [statistic.clause for statistic in kept]
        )
        for clause in extension_clauses:
            last_family_index = FAMILY_INDEX[clause.atoms[-1].family]
            used = {atom.family for atom in clause.atoms}
            for atom in atom_list:
                if atom.family in used:
                    continue
                if FAMILY_INDEX[atom.family] <= last_family_index:
                    continue
                extended = Clause(clause.atoms + (atom,))
                extensions[extended.key] = extended
        beam = list(extensions.values())
        if not beam:
            break

    return sorted(
        all_statistics.values(), key=lambda item: item.search_score, reverse=True
    )


def feature_matrix(
    clauses: Sequence[Clause], masks: dict[Atom, np.ndarray]
) -> np.ndarray:
    if not clauses:
        raise ValueError("At least one clause is required")
    first_shape = next(iter(masks.values())).shape
    matrix = np.empty((*first_shape, len(clauses)), dtype=np.uint8)
    for index, clause in enumerate(clauses):
        matrix[:, :, index] = clause_mask(clause, masks)
    return matrix


def probabilities(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    scores = np.tensordot(matrix, weights, axes=([2], [0])).astype(np.float64)
    scores -= scores.max(axis=1, keepdims=True)
    exponentials = np.exp(scores)
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def conditional_nll(
    matrix: np.ndarray, chosen_indices: np.ndarray, weights: np.ndarray
) -> float:
    probs = probabilities(matrix, weights)
    chosen = probs[np.arange(probs.shape[0]), chosen_indices]
    return float(-np.log(np.maximum(chosen, 1e-12)).mean())


def fit_sparse_conditional_model(
    train_matrix: np.ndarray,
    train_chosen: np.ndarray,
    validation_matrix: np.ndarray,
    validation_chosen: np.ndarray,
    l1: float,
    max_steps: int,
    learning_rate: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fit signed rule weights with Adam and proximal L1 shrinkage."""

    feature_count = train_matrix.shape[2]
    weights = np.zeros(feature_count, dtype=np.float64)
    first_moment = np.zeros_like(weights)
    second_moment = np.zeros_like(weights)
    best_weights = weights.copy()
    best_validation = math.inf
    history: list[dict[str, float | int]] = []
    beta1 = 0.9
    beta2 = 0.999

    for step in range(1, max_steps + 1):
        probs = probabilities(train_matrix, weights)
        probs[np.arange(probs.shape[0]), train_chosen] -= 1.0
        gradient = (
            np.einsum("ncr,nc->r", train_matrix, probs, optimize=True)
            / train_matrix.shape[0]
        )
        first_moment = beta1 * first_moment + (1.0 - beta1) * gradient
        second_moment = beta2 * second_moment + (1.0 - beta2) * gradient**2
        corrected_first = first_moment / (1.0 - beta1**step)
        corrected_second = second_moment / (1.0 - beta2**step)
        weights -= learning_rate * corrected_first / (np.sqrt(corrected_second) + 1e-8)
        weights = np.sign(weights) * np.maximum(
            np.abs(weights) - learning_rate * l1, 0.0
        )

        if step == 1 or step % 10 == 0 or step == max_steps:
            train_nll = conditional_nll(train_matrix, train_chosen, weights)
            validation_nll = conditional_nll(
                validation_matrix, validation_chosen, weights
            )
            active = int((np.abs(weights) >= 0.05).sum())
            history.append(
                {
                    "step": step,
                    "train_nll": train_nll,
                    "validation_nll": validation_nll,
                    "active_weights": active,
                }
            )
            if validation_nll < best_validation:
                best_validation = validation_nll
                best_weights = weights.copy()
    return best_weights, {
        "l1": l1,
        "best_validation_nll": best_validation,
        "history": history,
    }


def residual_from_model(
    matrix: np.ndarray, chosen_indices: np.ndarray, weights: np.ndarray
) -> np.ndarray:
    residual = -probabilities(matrix, weights).astype(np.float32)
    residual[np.arange(residual.shape[0]), chosen_indices] += 1.0
    return residual


def modality(weight: float, statistic: ClauseStatistic) -> str:
    if (
        statistic.testable_opportunities >= 200
        and statistic.observed_rate <= 0.01
        and weight < 0
    ):
        return "FORBID_CANDIDATE"
    if (
        statistic.testable_opportunities >= 200
        and statistic.observed_rate >= 0.99
        and weight > 0
    ):
        return "REQUIRE_CANDIDATE"
    return "AVOID" if weight < 0 else "PREFER"


def piece_support(
    clause: Clause,
    masks: dict[Atom, np.ndarray],
    opportunities: Opportunities,
) -> int:
    mask = clause_mask(clause, masks)
    testable = mask.any(axis=1) & ~mask.all(axis=1)
    return int(np.unique(opportunities.piece_ids[testable]).shape[0])


def rule_records(
    clauses: Sequence[Clause],
    weights: np.ndarray,
    train_statistics: dict[str, ClauseStatistic],
    validation_opportunities: Opportunities,
    validation_masks: dict[Atom, np.ndarray],
) -> list[dict[str, Any]]:
    uniform_validation = uniform_residual(validation_opportunities)
    records: list[dict[str, Any]] = []
    for clause, weight in zip(clauses, weights, strict=True):
        if abs(float(weight)) < 0.05:
            continue
        train_statistic = train_statistics[clause.key]
        validation_statistic = statistic_for_clause(
            clause,
            validation_masks,
            uniform_validation,
            validation_opportunities.chosen_indices,
        )
        if validation_statistic is None:
            continue
        records.append(
            {
                "clause": clause.key,
                "atoms": [
                    {"family": atom.family, "value": atom.value, "label": atom.label}
                    for atom in clause.atoms
                ],
                "complexity": clause.complexity,
                "weight": float(weight),
                "modality": modality(float(weight), train_statistic),
                "train": {
                    "observed_rate": train_statistic.observed_rate,
                    "availability_rate": train_statistic.availability_rate,
                    "z_score": train_statistic.z_score,
                    "testable_opportunities": train_statistic.testable_opportunities,
                },
                "validation": {
                    "observed_rate": validation_statistic.observed_rate,
                    "availability_rate": validation_statistic.availability_rate,
                    "z_score": validation_statistic.z_score,
                    "testable_opportunities": (
                        validation_statistic.testable_opportunities
                    ),
                    "piece_support": piece_support(
                        clause, validation_masks, validation_opportunities
                    ),
                },
            }
        )
    records.sort(key=lambda record: abs(record["weight"]), reverse=True)
    return records


def common_atoms_without_directions(clause: Clause) -> tuple[Atom, ...]:
    return tuple(
        atom
        for atom in clause.atoms
        if atom.family not in {"soprano_direction", "bass_direction"}
    )


def direction_pair(clause: Clause) -> tuple[int | None, int | None]:
    soprano = next(
        (atom.value for atom in clause.atoms if atom.family == "soprano_direction"),
        None,
    )
    bass = next(
        (atom.value for atom in clause.atoms if atom.family == "bass_direction"),
        None,
    )
    return soprano, bass


def mirror_abstractions(
    statistics: Sequence[ClauseStatistic],
    minimum_abs_z: float = 2.0,
) -> list[dict[str, Any]]:
    """Factor mirrored up/up and down/down clauses after blind search."""

    indexed: dict[
        tuple[tuple[Atom, ...], tuple[int | None, int | None]], ClauseStatistic
    ] = {}
    for statistic in statistics:
        directions = direction_pair(statistic.clause)
        if directions not in {(1, 1), (-1, -1)}:
            continue
        common = common_atoms_without_directions(statistic.clause)
        indexed[(common, directions)] = statistic

    abstractions: list[dict[str, Any]] = []
    seen: set[tuple[Atom, ...]] = set()
    for (common, directions), upward in indexed.items():
        if directions != (1, 1) or common in seen:
            continue
        downward = indexed.get((common, (-1, -1)))
        if downward is None:
            continue
        if (
            abs(upward.z_score) < minimum_abs_z
            or abs(downward.z_score) < minimum_abs_z
            or upward.z_score * downward.z_score <= 0
        ):
            continue
        seen.add(common)
        abstractions.append(
            {
                "provisional_predicate": (
                    "(delta_soprano > 0 AND delta_bass > 0) OR "
                    "(delta_soprano < 0 AND delta_bass < 0)"
                ),
                "common_conditions": [atom.label for atom in common],
                "direction": "selected_more_than_available"
                if upward.z_score > 0
                else "selected_less_than_available",
                "upward_z": upward.z_score,
                "downward_z": downward.z_score,
                "upward_clause": upward.clause.key,
                "downward_clause": downward.clause.key,
                "description_length_saved_literals": 2 * len(common),
            }
        )
    abstractions.sort(
        key=lambda item: min(abs(item["upward_z"]), abs(item["downward_z"])),
        reverse=True,
    )
    return abstractions


def admits_same_sign_predicate(
    abstractions: Sequence[dict[str, Any]],
) -> bool:
    """Require the parameter-free mirrored pair before inventing the atom."""

    return any(
        not abstraction["common_conditions"]
        and min(
            abs(abstraction["upward_z"]),
            abs(abstraction["downward_z"]),
        )
        >= 2.0
        for abstraction in abstractions
    )


def clauses_using_learned_same_sign() -> list[Clause]:
    """Generate every numeric class uniformly after predicate invention."""

    learned = Atom("learned_same_nonzero_sign", 1)
    clauses: list[Clause] = []
    for interval_class in range(12):
        clauses.append(
            Clause(
                (
                    Atom("source_interval_mod12", interval_class),
                    Atom("target_interval_mod12", interval_class),
                    learned,
                )
            )
        )
        clauses.append(
            Clause(
                (
                    Atom("target_interval_mod12", interval_class),
                    Atom("soprano_leap_gt", 2),
                    learned,
                )
            )
        )
    return clauses


def statistic_for_custom_mask(
    mask: np.ndarray, opportunities: Opportunities
) -> dict[str, float | int]:
    """Compute the opportunity-normalized tail for a DNF mask."""

    testable = mask.any(axis=1) & ~mask.all(axis=1)
    rows = np.arange(opportunities.size)
    chosen = mask[rows, opportunities.chosen_indices]
    availability_by_opportunity = mask.mean(axis=1)
    centered = chosen.astype(np.float64) - availability_by_opportunity
    variance = float(
        np.sum(availability_by_opportunity * (1.0 - availability_by_opportunity))
    )
    return {
        "observed_rate": float(chosen[testable].mean()),
        "availability_rate": float(availability_by_opportunity[testable].mean()),
        "z_score": float(centered.sum() / math.sqrt(max(variance, 1e-9))),
        "testable_opportunities": int(testable.sum()),
        "piece_support": int(np.unique(opportunities.piece_ids[testable]).shape[0]),
    }


def learned_symmetry_scan(
    opportunities: Opportunities, masks: dict[Atom, np.ndarray]
) -> list[dict[str, Any]]:
    """Scan all numeric classes after factoring the learned sign symmetry."""

    same_nonzero_sign = (
        masks[Atom("soprano_direction", 1)] & masks[Atom("bass_direction", 1)]
    ) | (masks[Atom("soprano_direction", -1)] & masks[Atom("bass_direction", -1)])
    leap = masks[Atom("soprano_leap_gt", 2)]
    records: list[dict[str, Any]] = []
    for interval_class in range(12):
        source = masks[Atom("source_interval_mod12", interval_class)]
        target = masks[Atom("target_interval_mod12", interval_class)]
        repeated_class = same_nonzero_sign & source & target
        arrival_after_leap = same_nonzero_sign & leap & target
        records.append(
            {
                "numeric_class": interval_class,
                "same_sign_repeated_class": statistic_for_custom_mask(
                    repeated_class, opportunities
                ),
                "same_sign_arrival_after_leap_gt_2": (
                    statistic_for_custom_mask(arrival_after_leap, opportunities)
                ),
            }
        )
    return records


def markdown_report(result: dict[str, Any]) -> str:
    corpus = result["corpus"]
    model = result["model"]
    rules = result["rules"]
    abstractions = result["mirror_abstractions"]
    symmetry_scan = result["learned_symmetry_scan"]
    lines = [
        "# Résultats du POC différentiable",
        "",
        "## Périmètre",
        "",
        (
            f"- {corpus['pieces_total']} chorals historiques analysés, "
            f"{corpus['opportunities_total']} décisions de soprano."
        ),
        (
            f"- Train : {corpus['train_pieces']} pièces / "
            f"{corpus['train_opportunities']} décisions."
        ),
        (
            f"- Validation : {corpus['validation_pieces']} pièces / "
            f"{corpus['validation_opportunities']} décisions."
        ),
        "- Le test final n'a pas été ouvert."
        if not corpus["test_opened"]
        else ("- ATTENTION : le test final a été explicitement ouvert."),
        (
            "- Contrôle nul : les choix de soprano ont été mélangés dans chaque pièce."
            if result["experiment"]["null_shuffle"]
            else "- Données authentiques, sans mélange des choix."
        ),
        "",
        "## Modèle",
        "",
        f"- Clauses ajustées conjointement : {model['candidate_clause_count']}.",
        f"- Clauses actives (`|poids| >= 0.05`) : {model['active_rule_count']}.",
        f"- L1 choisie sur validation : `{model['selected_l1']}`.",
        f"- NLL uniforme : `{model['uniform_nll']:.6f}`.",
        f"- NLL train : `{model['train_nll']:.6f}`.",
        f"- NLL validation : `{model['validation_nll']:.6f}`.",
        (
            "- `LEARNED_PREDICATE_001` a été admis après détection des deux "
            "branches symétriques."
            if result["experiment"]["derived_predicate_admitted"]
            else "- Aucun prédicat de signe commun n'a été admis."
        ),
        "",
        "## Règles actives les plus fortes",
        "",
        "| # | Modalité | Poids | Train obs./disp. | Validation obs./disp. | Clause |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for index, rule in enumerate(rules[:30], start=1):
        lines.append(
            f"| {index} | {rule['modality']} | {rule['weight']:.3f} | "
            f"{rule['train']['observed_rate']:.3f} / "
            f"{rule['train']['availability_rate']:.3f} | "
            f"{rule['validation']['observed_rate']:.3f} / "
            f"{rule['validation']['availability_rate']:.3f} | "
            f"`{rule['clause']}` |"
        )
    lines.extend(
        [
            "",
            "Les deux taux sont calculés seulement dans les opportunités où la",
            "propriété et son complément sont tous deux disponibles.",
            "",
            "## Abstractions symétriques proposées après apprentissage",
            "",
        ]
    )
    if not abstractions:
        lines.append(
            "Aucune paire montée/montée – descente/descente suffisamment stable "
            "n'a été trouvée avec le seuil courant."
        )
    else:
        for index, abstraction in enumerate(abstractions[:20], start=1):
            common = " AND ".join(abstraction["common_conditions"]) or "(aucune)"
            lines.extend(
                [
                    f"### Abstraction {index}",
                    "",
                    f"- Conditions communes : `{common}`",
                    (
                        f"- z montée/montée : `{abstraction['upward_z']:.3f}` ; "
                        f"z descente/descente : "
                        f"`{abstraction['downward_z']:.3f}`."
                    ),
                    f"- Direction statistique : `{abstraction['direction']}`.",
                    "- Prédicat dérivé proposé :",
                    "",
                    "```text",
                    abstraction["provisional_predicate"],
                    "```",
                    "",
                ]
            )
    lines.extend(
        [
            "## Scan aveugle des douze classes numériques",
            "",
            "Ce scan est effectué seulement après que les deux branches de signe",
            "commun ont suggéré une abstraction symétrique. Les classes restent",
            "désignées par les nombres `0..11`.",
            "",
            "| Classe | Répétition même signe z train | z validation | "
            "Arrivée après saut z train | z validation |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for record in symmetry_scan:
        repeated = record["same_sign_repeated_class"]
        arrival = record["same_sign_arrival_after_leap_gt_2"]
        lines.append(
            f"| {record['numeric_class']} | "
            f"{repeated['train']['z_score']:.3f} | "
            f"{repeated['validation']['z_score']:.3f} | "
            f"{arrival['train']['z_score']:.3f} | "
            f"{arrival['validation']['z_score']:.3f} |"
        )
    lines.extend(
        [
            "## Limites",
            "",
            "- Cette première expérience ne modélise que les choix de soprano avec",
            "  le mouvement de basse comme contexte.",
            "- Les candidates sont équiprobables avant application des règles ;",
            "  l'ambitus est la seule faisabilité préimposée.",
            "- Une clause extrême est une hypothèse empirique, pas encore une règle",
            "  normative.",
            "- La compression symétrique est postérieure au gradient et doit être",
            "  confirmée par stabilité et par comparaison à des contrôles nuls.",
            "- Le test scellé ne sera ouvert qu'après gel du vocabulaire et des",
            "  hyperparamètres.",
            "",
        ]
    )
    return "\n".join(lines)


def serialize_statistic(statistic: ClauseStatistic) -> dict[str, Any]:
    return {
        "clause": statistic.clause.key,
        "atoms": [
            {"family": atom.family, "value": atom.value, "label": atom.label}
            for atom in statistic.clause.atoms
        ],
        "complexity": statistic.clause.complexity,
        "gradient": statistic.gradient,
        "z_score": statistic.z_score,
        "observed_rate": statistic.observed_rate,
        "availability_rate": statistic.availability_rate,
        "testable_opportunities": statistic.testable_opportunities,
        "candidate_support": statistic.candidate_support,
        "search_score": statistic.search_score,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=default_archive_path())
    parser.add_argument("--manifest", type=Path, default=default_manifest_path())
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--candidate-min", type=int, default=60)
    parser.add_argument("--candidate-max", type=int, default=81)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--beam-size", type=int, default=512)
    parser.add_argument("--min-testable", type=int, default=150)
    parser.add_argument("--candidate-clauses", type=int, default=32)
    parser.add_argument("--max-steps", type=int, default=140)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument(
        "--l1-grid",
        type=float,
        nargs="+",
        default=(0.001, 0.01, 0.03, 0.1),
    )
    parser.add_argument("--rebuild-corpus", action="store_true")
    parser.add_argument("--open-test", action="store_true")
    parser.add_argument(
        "--null-shuffle",
        action="store_true",
        help="shuffle chosen soprano pitches within each piece",
    )
    parser.add_argument(
        "--output-stem",
        default="result",
        help="JSON basename; the default also writes REPORT.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = experiment_root()
    work = root / "work"
    results_dir = root / "results"
    work.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    archive = args.archive.resolve()
    manifest_path = args.manifest.resolve()
    actual_hash = sha256_file(archive)
    if actual_hash != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(
            f"Unexpected archive hash {actual_hash}; expected {EXPECTED_ARCHIVE_SHA256}"
        )
    manifest, included_pieces = load_included_pieces(manifest_path)
    splits = deterministic_splits([piece["id"] for piece in included_pieces], args.seed)
    json_dump(
        results_dir / "splits.json",
        {
            "seed": args.seed,
            "split_before_events": True,
            "train": splits["train"],
            "validation": splits["validation"],
            "test": splits["test"],
        },
    )

    selected_pieces = included_pieces
    cache_suffix = "full"
    if args.max_pieces is not None:
        selected_ids = set((splits["train"] + splits["validation"])[: args.max_pieces])
        selected_pieces = [
            piece for piece in included_pieces if piece["id"] in selected_ids
        ]
        cache_suffix = f"smoke-{args.max_pieces}"

    cache_path = work / f"opportunities-{cache_suffix}.npz"
    if args.rebuild_corpus and cache_path.exists():
        cache_path.unlink()
    if cache_path.exists():
        print(f"[corpus] loading cache {cache_path}", flush=True)
        all_opportunities = load_opportunities(cache_path)
    else:
        score_paths = materialize_scores(archive, selected_pieces, work / "scores")
        all_opportunities = build_opportunities(
            score_paths, args.candidate_min, args.candidate_max
        )
        save_opportunities(cache_path, all_opportunities)

    available_piece_ids = set(all_opportunities.piece_ids.tolist())
    train_ids = [piece for piece in splits["train"] if piece in available_piece_ids]
    validation_ids = [
        piece for piece in splits["validation"] if piece in available_piece_ids
    ]
    if args.max_pieces is not None and not validation_ids:
        smoke_ids = sorted(available_piece_ids)
        split_at = max(1, int(0.8 * len(smoke_ids)))
        train_ids = smoke_ids[:split_at]
        validation_ids = smoke_ids[split_at:]
    train = subset_for_piece_ids(all_opportunities, train_ids)
    validation = subset_for_piece_ids(all_opportunities, validation_ids)
    if train.size == 0 or validation.size == 0:
        raise RuntimeError(
            f"Empty split: train={train.size}, validation={validation.size}"
        )
    if args.null_shuffle:
        train = shuffle_choices_within_pieces(train, args.seed + 101)
        validation = shuffle_choices_within_pieces(validation, args.seed + 202)
    print(
        f"[corpus] train={train.size} validation={validation.size} "
        f"candidates={train.candidate_pitches.shape[0]}",
        flush=True,
    )

    atom_list = atoms()
    train_masks = atom_masks(train, atom_list)
    validation_masks = atom_masks(validation, atom_list)
    initial_residual = uniform_residual(train)
    searched = search_clauses(
        train,
        train_masks,
        initial_residual,
        max_depth=args.max_depth,
        beam_size=args.beam_size,
        min_testable=min(args.min_testable, max(10, train.size // 4)),
    )
    if not searched:
        raise RuntimeError("Clause search returned no candidates")
    abstractions = mirror_abstractions(searched)
    selected_statistics = searched[: args.candidate_clauses]
    derived_predicate_admitted = admits_same_sign_predicate(abstractions)
    if derived_predicate_admitted:
        learned_atom = Atom("learned_same_nonzero_sign", 1)
        train_masks.update(atom_masks(train, [learned_atom]))
        validation_masks.update(atom_masks(validation, [learned_atom]))
        for clause in clauses_using_learned_same_sign():
            statistic = statistic_for_clause(
                clause,
                train_masks,
                initial_residual,
                train.chosen_indices,
            )
            if statistic is not None:
                selected_statistics.append(statistic)
    selected_clauses = [statistic.clause for statistic in selected_statistics]
    train_statistics = {
        statistic.clause.key: statistic
        for statistic in [*searched, *selected_statistics]
    }

    print(
        f"[fit] building matrices for {len(selected_clauses)} clauses",
        flush=True,
    )
    train_matrix = feature_matrix(selected_clauses, train_masks)
    validation_matrix = feature_matrix(selected_clauses, validation_masks)

    fits: list[tuple[np.ndarray, dict[str, Any]]] = []
    for l1 in args.l1_grid:
        print(f"[fit] l1={l1}", flush=True)
        weights, diagnostics = fit_sparse_conditional_model(
            train_matrix,
            train.chosen_indices,
            validation_matrix,
            validation.chosen_indices,
            l1=l1,
            max_steps=args.max_steps,
            learning_rate=args.learning_rate,
        )
        fits.append((weights, diagnostics))
        print(
            f"[fit] l1={l1} best_validation_nll="
            f"{diagnostics['best_validation_nll']:.6f}",
            flush=True,
        )
    weights, fit_diagnostics = min(
        fits, key=lambda item: item[1]["best_validation_nll"]
    )

    records = rule_records(
        selected_clauses,
        weights,
        train_statistics,
        validation,
        validation_masks,
    )
    train_symmetry_scan = learned_symmetry_scan(train, train_masks)
    validation_symmetry_scan = learned_symmetry_scan(validation, validation_masks)
    symmetry_scan = []
    for train_record, validation_record in zip(
        train_symmetry_scan, validation_symmetry_scan, strict=True
    ):
        symmetry_scan.append(
            {
                "numeric_class": train_record["numeric_class"],
                "same_sign_repeated_class": {
                    "train": train_record["same_sign_repeated_class"],
                    "validation": validation_record["same_sign_repeated_class"],
                },
                "same_sign_arrival_after_leap_gt_2": {
                    "train": train_record["same_sign_arrival_after_leap_gt_2"],
                    "validation": validation_record[
                        "same_sign_arrival_after_leap_gt_2"
                    ],
                },
            }
        )
    uniform_nll = math.log(train.candidate_pitches.shape[0])
    train_nll = conditional_nll(train_matrix, train.chosen_indices, weights)
    validation_nll = conditional_nll(
        validation_matrix, validation.chosen_indices, weights
    )

    result: dict[str, Any] = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc",
            "seed": args.seed,
            "candidate_pitch_range": [
                args.candidate_min,
                args.candidate_max,
            ],
            "max_clause_depth": args.max_depth,
            "beam_size": args.beam_size,
            "test_opened": args.open_test,
            "null_shuffle": args.null_shuffle,
            "derived_predicate_admitted": derived_predicate_admitted,
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "music21": __import__("music21").__version__,
        },
        "source": {
            "archive": str(archive),
            "archive_sha256": actual_hash,
            "manifest": str(manifest_path),
            "manifest_schema_version": manifest["schema_version"],
        },
        "corpus": {
            "pieces_total": len(available_piece_ids),
            "opportunities_total": all_opportunities.size,
            "train_pieces": len(train_ids),
            "validation_pieces": len(validation_ids),
            "test_pieces_reserved": len(splits["test"]),
            "train_opportunities": train.size,
            "validation_opportunities": validation.size,
            "test_opened": args.open_test,
        },
        "search": {
            "atom_count": len(atom_list),
            "admissible_clause_count": len(searched),
            "top_marginal_clauses": [
                serialize_statistic(statistic) for statistic in searched[:100]
            ],
        },
        "model": {
            "candidate_clause_count": len(selected_clauses),
            "active_rule_count": len(records),
            "selected_l1": fit_diagnostics["l1"],
            "uniform_nll": uniform_nll,
            "train_nll": train_nll,
            "validation_nll": validation_nll,
            "all_l1_fits": [diagnostics for _, diagnostics in fits],
        },
        "rules": records,
        "mirror_abstractions": abstractions[:100],
        "learned_symmetry_scan": symmetry_scan,
    }
    if args.open_test:
        test = subset_for_piece_ids(all_opportunities, splits["test"])
        if test.size:
            test_masks = atom_masks(test, atom_list)
            test_matrix = feature_matrix(selected_clauses, test_masks)
            result["corpus"]["test_opportunities"] = test.size
            result["model"]["test_nll"] = conditional_nll(
                test_matrix, test.chosen_indices, weights
            )

    json_path = results_dir / f"{args.output_stem}.json"
    report_name = (
        "REPORT.md"
        if args.output_stem == "result"
        else f"{args.output_stem.upper()}_REPORT.md"
    )
    report_path = results_dir / report_name
    json_dump(json_path, result)
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"[done] wrote {json_path}", flush=True)
    print(f"[done] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
