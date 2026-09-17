#!/usr/bin/env python3
"""Generate a complete SATB choral with learned factors and Snarky search."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_two_loop_score_floor_experiment as score_experiment
import run_v24_snarky_search as search_poc
import v34_harmony
import yaml

from harmonizer.official_manual import (
    DEFAULT_RULEBASE,
    DISSONANT_ABOVE_BASS,
    ParsedSATBScore,
    SATBFrame,
    audit_parsed_satb,
)
from snarky import (
    Atom,
    ChoiceAlternative,
    ChoiceEventKind,
    ChoicePoint,
    ChoiceTraversal,
    Fact,
    FiniteSequence,
    ForwardEngine,
    MRVChoicePolicy,
    Number,
    SessionChoiceSearch,
    Triple,
    parse_factor_groups,
)

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
GENERATED = REPOSITORY / "harmonizer/generated"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_MODEL = FACTOR_BASE / "v23_metric_harmony_full_model.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v23_metric_harmony_full_factors.yaml"
DEFAULT_CACHE = HERE / "work/k3-exact-v24-selected-32x10.npz"
DEFAULT_SEQUENCE_MODEL: Path | None = None
DEFAULT_HARMONIC_BUDGET_MODEL: Path | None = None
DEFAULT_BOUNDARY_MODEL = FACTOR_BASE / "boundary_chord_factors.json"
DEFAULT_OUTPUT = FACTOR_BASE / "two_loop_full_generation.json"
DEFAULT_REPORT = FACTOR_BASE / "TWO_LOOP_FULL_GENERATION.md"
DEFAULT_MUSICXML = GENERATED / "two_loop_full_bwv108_6.musicxml"
DEFAULT_MIDI = GENERATED / "two_loop_full_bwv108_6.mid"

PROBLEM = Atom("full_learned_choral")
KIND = Atom("kind")
FULL_GENERATION = Atom("full_satb_generation")
ASSIGNED_PITCH = Atom("assigned_pitch")
STATE = Atom("state")
CONTRADICTION = Atom("contradiction")
VIOLATED_CONSTRAINT = Atom("violated_constraint")
SCORE_FLOOR = Atom("minimum_learned_sequence_score")
HARD_K3 = Atom("learned_k3_hard_constraint")
HARMONIC_DISSONANCE_BUDGET = Atom("named_dissonance_budget")
HARMONIC_CHAIN_BUDGET = Atom("dissonant_chain_budget")
OFFICIAL_MANUAL_BUDGET = Atom("official_manual_empirical_budget")
HOMORHYTHMIC_CHORD = Atom("homorhythmic_named_chord")
CHOSEN_CHORD = Atom("chosen_reified_chord")
REJECTED_CHORD = Atom("rejected_reified_chord")
REIFIED_CHORD_DOMAIN = Atom("empty_reified_chord_domain")
HOMORHYTHMIC_CHORD_VOCABULARIES = {
    "consonant_triads": frozenset((0, 1)),
    "triads": frozenset((0, 1, 2)),
    "standard": frozenset((0, 1, 2, 4, 5, 6, 7, 8)),
}

type Segment = tuple[int, int, int]
type PitchBlock = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class SegmentEvaluation:
    """Exact conditional score and hard-constraint activations."""

    log_probability: float
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReifiedChordCandidate:
    """One observable SATB value in a position's finite chord domain."""

    time: int
    index: int
    pitches: PitchBlock
    signature: int
    quality: int
    root_degree: int
    inversion_interval: int

    @property
    def lower_pitches(self) -> tuple[int, int, int]:
        return self.pitches[1:]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--calibration-cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--sequence-model",
        type=Path,
        default=DEFAULT_SEQUENCE_MODEL,
        help="Optional independently learned attacked-note sequence factor.",
    )
    parser.add_argument(
        "--official-manual-budgets",
        action="store_true",
        help=(
            "Reject complete branches outside the frozen empirical manual "
            "budget and backtrack."
        ),
    )
    parser.add_argument(
        "--official-manual-profile",
        choices=("bach_empirical", "pedagogical_strict", "diagnostic"),
        default="bach_empirical",
        help=(
            "Use learned Bach budgets, make every declared violation hard, "
            "or retain the manual only as a diagnostic/factor layer."
        ),
    )
    parser.add_argument(
        "--homorhythmic-soprano-grid",
        action="store_true",
        help=(
            "Keep only soprano attacks and make all four voices attack with "
            "the exact soprano rhythm."
        ),
    )
    parser.add_argument(
        "--require-harmonized-blocks",
        action="store_true",
        help=(
            "Require every completed vertical block to be a standard named "
            "chord or an incomplete consonant triad."
        ),
    )
    parser.add_argument(
        "--homorhythmic-chord-vocabulary",
        choices=tuple(HOMORHYTHMIC_CHORD_VOCABULARIES),
        default="standard",
        help=(
            "Use triads only, or the broader standard vocabulary including "
            "seventh chords."
        ),
    )
    parser.add_argument(
        "--score-floor-mode",
        choices=("search", "offline_audit"),
        default="search",
        help=(
            "Enforce the exact MLE score floor inside search, or export a "
            "hard-constraint candidate for a separate compiled score audit."
        ),
    )
    parser.add_argument(
        "--harmonic-budget-model",
        type=Path,
        default=DEFAULT_HARMONIC_BUDGET_MODEL,
        help="Optional next-strong harmonic factor and learned budgets.",
    )
    parser.add_argument(
        "--boundary-model",
        type=Path,
        default=DEFAULT_BOUNDARY_MODEL,
        help="Train-only opening/closing chord factor model.",
    )
    parser.add_argument(
        "--allow-rejected-harmonic-ablation",
        action="store_true",
        help="Allow an explicitly rejected model only for a labelled ablation.",
    )
    parser.add_argument(
        "--constraint-mode",
        choices=("v22", "v33_strict_strong_unlicensed"),
        default="v22",
        help="Hard-constraint ablation applied before each Snarky choice.",
    )
    parser.add_argument(
        "--disable-forward-check",
        action="store_true",
        help=(
            "Disable the one-segment K3 look-ahead without changing the "
            "admissible solutions or learned factors."
        ),
    )
    parser.add_argument(
        "--search-order",
        choices=("chronological", "strong_skeleton"),
        default="chronological",
        help=(
            "Choose lower-voice segments chronologically or assign the three "
            "controllers of every strong block before weak-only segments."
        ),
    )
    parser.add_argument("--max-nodes", type=int, default=20_000)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--musicxml", type=Path, default=DEFAULT_MUSICXML)
    parser.add_argument("--midi", type=Path, default=DEFAULT_MIDI)
    return parser.parse_args()


def _segment_atom(segment: Segment) -> Atom:
    return Atom(f"lower_segment_{segment[0]}_{segment[1]}_{segment[2]}")


def _assignments(session: Any) -> dict[Segment, int]:
    output: dict[Segment, int] = {}
    for fact in session.facts:
        entity = fact.entity
        if (
            not isinstance(entity, Triple)
            or entity.relation != ASSIGNED_PITCH
            or not isinstance(entity.subject, FiniteSequence)
            or not isinstance(entity.object, Number)
            or not isinstance(entity.object.value, int)
        ):
            continue
        fields = entity.subject.elements
        if len(fields) == 3 and all(
            isinstance(field, Number) and isinstance(field.value, int)
            for field in fields
        ):
            output[
                (
                    int(fields[0].value),
                    int(fields[1].value),
                    int(fields[2].value),
                )
            ] = int(entity.object.value)
    return output


def _assignment_fact(segment: Segment, pitch: int) -> Fact:
    return Fact(
        Triple(
            FiniteSequence(tuple(Number(value) for value in segment)),
            ASSIGNED_PITCH,
            Number(pitch),
        )
    )


def _chord_position_atom(time: int) -> Atom:
    return Atom(f"reified_chord_position_{time}")


def _chord_fact(time: int, relation: Atom, candidate_index: int) -> Fact:
    return Fact(
        Triple(
            _chord_position_atom(time),
            relation,
            Number(candidate_index),
        )
    )


def _chord_indices(session: Any, relation: Atom) -> dict[int, set[int]]:
    """Read branch-local reified chord facts grouped by lattice time."""

    output: dict[int, set[int]] = {}
    prefix = "reified_chord_position_"
    for fact in session.facts:
        entity = fact.entity
        if (
            not isinstance(entity, Triple)
            or entity.relation != relation
            or not isinstance(entity.subject, Atom)
            or not entity.subject.name.startswith(prefix)
            or not isinstance(entity.object, Number)
            or not isinstance(entity.object.value, int)
        ):
            continue
        time = int(entity.subject.name.removeprefix(prefix))
        output.setdefault(time, set()).add(int(entity.object.value))
    return output


def _default_blocks(
    lattice: k3.RhythmicLattice,
    program: Any,
) -> np.ndarray:
    """Build a source-independent complete state for dynamic lookahead."""

    blocks = np.empty_like(lattice.blocks)
    blocks[:, 0] = lattice.blocks[:, 0]
    pitches = np.arange(
        program.candidate_min,
        program.candidate_max + 1,
        dtype=np.int16,
    )
    for voice in range(1, 4):
        logits = (
            program.register_logits[voice]
            + program.tonal_logits[
                voice,
                lattice.mode,
                (pitches - lattice.tonic_pc) % 12,
            ]
        )
        default = int(pitches[int(np.argmax(logits))])
        blocks[:, voice] = default
    return blocks


def _homorhythmic_soprano_lattice(
    lattice: k3.RhythmicLattice,
) -> k3.RhythmicLattice:
    indices = np.flatnonzero(lattice.attacks[:, 0])
    if indices.size < 3:
        raise ValueError("Homorhythmic generation requires three soprano attacks")
    return k3.RhythmicLattice(
        piece_id=lattice.piece_id,
        offsets=lattice.offsets[indices].copy(),
        blocks=lattice.blocks[indices].copy(),
        attacks=np.ones((indices.size, 4), dtype=bool),
        end_offset=lattice.end_offset,
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels[indices].copy(),
    )


def _apply_assignments(
    defaults: np.ndarray,
    assignments: dict[Segment, int],
) -> np.ndarray:
    blocks = defaults.copy()
    for (start, end, voice), pitch in assignments.items():
        blocks[start:end, voice] = pitch
    return blocks


def _ordered_lower_segments(attacks: np.ndarray) -> tuple[Segment, ...]:
    voice_order = {3: 0, 2: 1, 1: 2}
    return tuple(
        sorted(
            (segment for segment in k3.attack_segments(attacks) if segment[2] != 0),
            key=lambda segment: (
                segment[0],
                voice_order[segment[2]],
            ),
        )
    )


def _search_ordered_segments(
    attacks: np.ndarray,
    metric_levels: np.ndarray,
    mode: str,
) -> tuple[Segment, ...]:
    chronological = _ordered_lower_segments(attacks)
    if mode == "chronological":
        return chronological
    strong_times = frozenset(int(time) for time in np.flatnonzero(metric_levels >= 2))
    strong_controllers = tuple(
        segment
        for segment in chronological
        if any(time in strong_times for time in range(segment[0], segment[1]))
    )
    weak_only = tuple(
        segment for segment in chronological if segment not in strong_controllers
    )
    return strong_controllers + weak_only


def _learned_voice_ranges(
    cache_path: Path,
    *,
    candidate_min: int,
) -> dict[int, tuple[int, int]]:
    """Return exact lower-voice pitch supports observed in the training split."""

    with np.load(cache_path, allow_pickle=False) as cache:
        chosen = cache["train_chosen"].astype(np.int16) + candidate_min
        voices = cache["train_voices"]
    return {
        voice: (
            int(chosen[voices == voice].min()),
            int(chosen[voices == voice].max()),
        )
        for voice in range(1, 4)
    }


def _constraint_features(
    mode: str,
) -> tuple[tuple[str, k3.FeatureSpec], ...]:
    baseline = search_poc._learned_constraint_features()
    if mode == "v22":
        return baseline
    if mode != "v33_strict_strong_unlicensed":
        raise ValueError(f"Unknown hard-constraint mode: {mode}")
    return (
        *baseline,
        (
            "C-K3-V33-TRIAD-PLUS-UNLICENSED",
            k3.FeatureSpec(
                "central_residual_strong_sonority_status",
                -1,
                value=6,
                complexity=3,
            ),
        ),
        (
            "C-K3-V33-OTHER-UNLICENSED",
            k3.FeatureSpec(
                "central_residual_strong_sonority_status",
                -1,
                value=7,
                complexity=3,
            ),
        ),
    )


@dataclass(frozen=True, slots=True)
class AttackCycleSequenceFactor:
    """Pure finite-state factor for continuing an attacked-note ABAB cycle."""

    factor_ids: tuple[str, ...]
    voice_log_weights: tuple[float | None, ...]
    source: Path

    @classmethod
    def load(cls, path: Path) -> AttackCycleSequenceFactor:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["experiment"]["status"] != "CONFIRMED":
            raise ValueError("The requested sequence factor is not confirmed")
        factors = payload.get("factors")
        if factors is None:
            factors = [
                {
                    **payload["factor"],
                    "voices": list(k3.VOICE_NAMES[1:]),
                }
            ]
        voice_weights: list[float | None] = [None] * len(k3.VOICE_NAMES)
        for factor in factors:
            for voice_name in factor["voices"]:
                voice_weights[k3.VOICE_NAMES.index(voice_name)] = float(
                    factor["log_weight"]
                )
        return cls(
            factor_ids=tuple(str(factor["id"]) for factor in factors),
            voice_log_weights=tuple(voice_weights),
            source=path.resolve(),
        )

    def candidate_energies(
        self,
        assignments: dict[Segment, int],
        segment: Segment,
        candidates: np.ndarray,
        segments: tuple[Segment, ...],
    ) -> np.ndarray:
        """Return one isolated log-energy contribution per candidate pitch."""

        _, _, voice = segment
        log_weight = self.voice_log_weights[voice]
        history = [
            assignments[previous]
            for previous in segments
            if previous[2] == voice
            and previous[0] < segment[0]
            and previous in assignments
        ]
        output = np.zeros(candidates.shape[0], dtype=np.float64)
        if (
            log_weight is not None
            and len(history) >= 3
            and history[-1] == history[-3]
            and history[-1] != history[-2]
        ):
            output[candidates == history[-2]] = log_weight
        return output


class StrongHarmonyBudget:
    """Next-strong learned factors plus persistent count budgets."""

    def __init__(
        self,
        *,
        source: Path,
        status: str,
        lattice: k3.RhythmicLattice,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        quantile: float,
        dissonant_probability: float,
        chain_probability: float,
        dissonant_log_weight: float,
        outcome_log_weights: dict[str, float],
    ) -> None:
        self.source = source
        self.status = status
        self.lattice = lattice
        self.segments = segments
        self.defaults = defaults
        self.quantile = quantile
        self.dissonant_probability = dissonant_probability
        self.chain_probability = chain_probability
        self.dissonant_log_weight = dissonant_log_weight
        self.outcome_log_weights = outcome_log_weights
        strong = np.flatnonzero(lattice.metric_levels >= 2)
        self.strong_pairs = tuple(
            (int(current), int(following))
            for current, following in zip(strong[:-1], strong[1:], strict=True)
        )
        self.budgeted_strong_times = frozenset(
            current for current, _ in self.strong_pairs
        )
        self.controllers = {
            (time, voice): segment
            for segment in segments
            for time in range(segment[0], segment[1])
            for voice in (segment[2],)
        }
        self.pair_dependencies = tuple(
            frozenset(
                self.controllers[(time, voice)]
                for time in (current, following)
                for voice in range(1, 4)
            )
            for current, following in self.strong_pairs
        )
        self.maximum_dissonant = self._binomial_quantile(
            len(self.strong_pairs),
            dissonant_probability,
            quantile,
        )
        self.maximum_chains = self._binomial_quantile(
            self.maximum_dissonant,
            chain_probability,
            quantile,
        )

    @staticmethod
    def _binomial_quantile(
        trials: int,
        probability: float,
        quantile: float,
    ) -> int:
        if trials <= 0:
            return 0
        cumulative = 0.0
        for successes in range(trials + 1):
            cumulative += (
                math.comb(trials, successes)
                * probability**successes
                * (1.0 - probability) ** (trials - successes)
            )
            if cumulative >= quantile:
                return successes
        return trials

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        lattice: k3.RhythmicLattice,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        allow_rejected_ablation: bool,
    ) -> StrongHarmonyBudget:
        payload = json.loads(path.read_text(encoding="utf-8"))
        status = str(payload["experiment"]["status"])
        if status != "CONFIRMED" and not allow_rejected_ablation:
            raise ValueError(
                "The harmonic budget model is not confirmed; pass the explicit "
                "ablation flag to test it without promotion"
            )
        factors = {factor["outcome"]: factor for factor in payload["factors"]}
        return cls(
            source=path.resolve(),
            status=status,
            lattice=lattice,
            segments=segments,
            defaults=defaults,
            quantile=float(payload["budgets"]["quantile"]),
            dissonant_probability=float(
                payload["budgets"]["dissonant_named_probability"]
            ),
            chain_probability=float(
                payload["budgets"]["chain_given_dissonant_probability"]
            ),
            dissonant_log_weight=float(factors["strong_named_dissonant"]["log_weight"]),
            outcome_log_weights={
                outcome: float(factors[outcome]["log_weight"])
                for outcome in (
                    "next_triad",
                    "next_named_dissonant",
                    "next_residual",
                )
            },
        )

    def _block_complete(
        self,
        assignments: dict[Segment, int],
        time: int,
    ) -> bool:
        return all(
            self.controllers[(time, voice)] in assignments for voice in range(1, 4)
        )

    def _outcome(
        self,
        blocks: np.ndarray,
        current: int,
        following: int,
    ) -> tuple[bool, str | None]:
        current_state = v34_harmony.analyze_block(
            blocks[current],
            self.lattice.tonic_pc,
        )
        if current_state["family"] not in v34_harmony.DISSONANT_FAMILIES:
            return False, None
        following_state = v34_harmony.analyze_block(
            blocks[following],
            self.lattice.tonic_pc,
        )
        raw = v34_harmony.resolution_outcome(current_state, following_state)
        outcome = "next_triad" if raw.startswith("triad_") else raw
        return True, outcome

    def statistics(self, assignments: dict[Segment, int]) -> dict[str, int]:
        blocks = _apply_assignments(self.defaults, assignments)
        completed = 0
        dissonant = 0
        chains = 0
        for current, following in self.strong_pairs:
            if not (
                self._block_complete(assignments, current)
                and self._block_complete(assignments, following)
            ):
                continue
            completed += 1
            is_dissonant, outcome = self._outcome(blocks, current, following)
            dissonant += is_dissonant
            chains += outcome == "next_named_dissonant"
        return {
            "completed_strong_transitions": completed,
            "dissonant_named": dissonant,
            "dissonant_chains": chains,
            "maximum_dissonant_named": self.maximum_dissonant,
            "maximum_dissonant_chains": self.maximum_chains,
        }

    def candidate_is_allowed(
        self,
        assignments: dict[Segment, int],
        segment: Segment,
        pitch: int,
    ) -> bool:
        """Propagate the two monotone learned count budgets immediately."""

        assigned_segments = assignments.keys()
        trial_segments = assigned_segments | {segment}
        newly_completed = tuple(
            index
            for index, dependencies in enumerate(self.pair_dependencies)
            if segment in dependencies
            and dependencies <= trial_segments
            and not dependencies <= assigned_segments
        )
        if not newly_completed:
            return True

        statistics = self.statistics(assignments)
        blocks = _apply_assignments(
            self.defaults,
            {**assignments, segment: pitch},
        )
        dissonant = statistics["dissonant_named"]
        chains = statistics["dissonant_chains"]
        for index in newly_completed:
            current, following = self.strong_pairs[index]
            is_dissonant, outcome = self._outcome(blocks, current, following)
            dissonant += is_dissonant
            chains += outcome == "next_named_dissonant"
        return dissonant <= self.maximum_dissonant and chains <= self.maximum_chains

    def candidate_energies(
        self,
        assignments: dict[Segment, int],
        segment: Segment,
        candidates: np.ndarray,
    ) -> np.ndarray:
        before_complete = {
            time
            for pair in self.strong_pairs
            for time in pair
            if self._block_complete(assignments, time)
        }
        output = np.zeros(candidates.size, dtype=np.float64)
        for index, pitch in enumerate(candidates):
            trial = {**assignments, segment: int(pitch)}
            newly_complete = {
                time
                for pair in self.strong_pairs
                for time in pair
                if time not in before_complete and self._block_complete(trial, time)
            }
            if not newly_complete:
                continue
            blocks = _apply_assignments(self.defaults, trial)
            for time in newly_complete & self.budgeted_strong_times:
                state = v34_harmony.analyze_block(
                    blocks[time],
                    self.lattice.tonic_pc,
                )
                if state["family"] in v34_harmony.DISSONANT_FAMILIES:
                    output[index] += self.dissonant_log_weight
            for current, following in self.strong_pairs:
                if following not in newly_complete:
                    continue
                is_dissonant, outcome = self._outcome(blocks, current, following)
                if is_dissonant and outcome is not None:
                    output[index] += self.outcome_log_weights[outcome]
        return output


class ExactSegmentEvaluator:
    """Cache exact V23 conditionals and V22 pretest violations."""

    def __init__(
        self,
        *,
        lattice: k3.RhythmicLattice,
        program: Any,
        constraint_rows: tuple[tuple[str, k3.FeatureSpec], ...],
    ) -> None:
        self.lattice = lattice
        self.program = program
        self.constraint_rows = constraint_rows
        self.all_features = (
            *program.features,
            *(feature for _, feature in constraint_rows),
        )
        self.candidates = np.arange(
            program.candidate_min,
            program.candidate_max + 1,
            dtype=np.int16,
        )
        self.cache: dict[
            tuple[Segment, tuple[PitchBlock, ...]],
            tuple[np.ndarray, np.ndarray],
        ] = {}
        self.violation_cache: dict[
            tuple[Segment, tuple[PitchBlock, ...]],
            tuple[str, ...],
        ] = {}
        self.evaluation_cache: dict[
            tuple[Segment, tuple[PitchBlock, ...]],
            SegmentEvaluation,
        ] = {}

    def _key(
        self,
        blocks: np.ndarray,
        segment: Segment,
    ) -> tuple[Segment, tuple[PitchBlock, ...]]:
        required = score_experiment._required_times(
            segment,
            blocks.shape[0],
        )
        return (
            segment,
            tuple(tuple(int(value) for value in blocks[time]) for time in required),
        )

    def components(
        self,
        blocks: np.ndarray,
        segment: Segment,
    ) -> tuple[np.ndarray, np.ndarray]:
        key = self._key(blocks, segment)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        start, end, voice = segment
        base, totals = k3.candidate_segment_components(
            blocks,
            self.lattice.attacks,
            k3.segment_energy_times(segment, self.lattice.size),
            start,
            end,
            voice,
            self.candidates,
            candidate_min=self.program.candidate_min,
            candidate_max=self.program.candidate_max,
            register_logits=self.program.register_logits,
            features=self.all_features,
            tonal_logits=self.program.tonal_logits,
            tonic_pc=self.lattice.tonic_pc,
            mode=self.lattice.mode,
            metric_levels=self.lattice.metric_levels,
        )
        self.cache[key] = (base, totals)
        return base, totals

    def candidate_energies(
        self,
        blocks: np.ndarray,
        segment: Segment,
    ) -> np.ndarray:
        base, totals = self.components(blocks, segment)
        factor_count = len(self.program.features)
        return base + totals[:, :factor_count] @ self.program.weights

    def evaluate(
        self,
        blocks: np.ndarray,
        segment: Segment,
    ) -> SegmentEvaluation:
        key = self._key(blocks, segment)
        cached = self.evaluation_cache.get(key)
        if cached is not None:
            return cached
        energies = self.candidate_energies(blocks, segment)
        chosen = int(blocks[segment[0], segment[2]]) - self.program.candidate_min
        maximum = float(np.max(energies))
        log_probability = float(
            energies[chosen] - maximum - np.log(np.exp(energies - maximum).sum())
        )
        _, totals = self.components(blocks, segment)
        factor_count = len(self.program.features)
        active = totals[chosen, factor_count:]
        violations = tuple(
            constraint_id
            for (constraint_id, _), value in zip(
                self.constraint_rows,
                active,
                strict=True,
            )
            if value > 0
        )
        result = SegmentEvaluation(log_probability, violations)
        self.evaluation_cache[key] = result
        return result

    def evaluate_many(
        self,
        block_contexts: np.ndarray,
        segment: Segment,
    ) -> tuple[SegmentEvaluation, ...]:
        """Evaluate one segment exactly in a batch of reified chord contexts."""

        contexts = np.asarray(block_contexts, dtype=np.int16)
        start, end, voice = segment
        base, totals = k3.batch_candidate_segment_components(
            contexts,
            self.lattice.attacks,
            k3.segment_energy_times(segment, self.lattice.size),
            start,
            end,
            voice,
            self.candidates,
            candidate_min=self.program.candidate_min,
            candidate_max=self.program.candidate_max,
            register_logits=self.program.register_logits,
            features=self.all_features,
            tonal_logits=self.program.tonal_logits,
            tonic_pc=self.lattice.tonic_pc,
            mode=self.lattice.mode,
            metric_levels=self.lattice.metric_levels,
        )
        factor_count = len(self.program.features)
        energies = base + totals[:, :, :factor_count] @ self.program.weights
        chosen = contexts[:, start, voice] - self.program.candidate_min
        if np.any(chosen < 0) or np.any(chosen >= self.candidates.size):
            raise ValueError("A chosen pitch falls outside the factor domain")
        rows = np.arange(contexts.shape[0])
        maximum = np.max(energies, axis=1)
        log_probabilities = (
            energies[rows, chosen]
            - maximum
            - np.log(np.exp(energies - maximum[:, None]).sum(axis=1))
        )
        active = totals[rows, chosen, factor_count:]
        results = tuple(
            SegmentEvaluation(
                float(log_probabilities[index]),
                tuple(
                    constraint_id
                    for (constraint_id, _), value in zip(
                        self.constraint_rows,
                        active[index],
                        strict=True,
                    )
                    if value > 0
                ),
            )
            for index in range(contexts.shape[0])
        )
        for context, result in zip(contexts, results, strict=True):
            self.evaluation_cache[self._key(context, segment)] = result
        return results

    def chosen_violations(
        self,
        blocks: np.ndarray,
        segment: Segment,
    ) -> tuple[str, ...]:
        """Evaluate only the selected world and only the hard predicates."""

        key = self._key(blocks, segment)
        cached = self.violation_cache.get(key)
        if cached is not None:
            return cached
        evaluated = self.evaluation_cache.get(key)
        if evaluated is not None:
            self.violation_cache[key] = evaluated.violations
            return evaluated.violations
        start, end, voice = segment
        pitch = np.asarray([blocks[start, voice]], dtype=np.int16)
        _, totals = k3.candidate_segment_components(
            blocks,
            self.lattice.attacks,
            k3.segment_energy_times(segment, self.lattice.size),
            start,
            end,
            voice,
            pitch,
            candidate_min=self.program.candidate_min,
            candidate_max=self.program.candidate_max,
            register_logits=self.program.register_logits,
            features=tuple(feature for _, feature in self.constraint_rows),
            tonal_logits=self.program.tonal_logits,
            tonic_pc=self.lattice.tonic_pc,
            mode=self.lattice.mode,
            metric_levels=self.lattice.metric_levels,
        )
        violations = tuple(
            constraint_id
            for (constraint_id, _), value in zip(
                self.constraint_rows,
                totals[0],
                strict=True,
            )
            if value > 0
        )
        self.violation_cache[key] = violations
        return violations


class DynamicSegmentChoiceProvider:
    """Choose every lower-voice attack span from learned conditionals."""

    def __init__(
        self,
        *,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        evaluator: ExactSegmentEvaluator,
        voice_ranges: dict[int, tuple[int, int]],
        sequence_factor: AttackCycleSequenceFactor | None = None,
        harmonic_budget: StrongHarmonyBudget | None = None,
        quality: FullQualityPropagator | None = None,
        forward_check: bool = False,
    ) -> None:
        self.segments = segments
        self.defaults = defaults
        self.evaluator = evaluator
        self.voice_ranges = voice_ranges
        self.sequence_factor = sequence_factor
        self.harmonic_budget = harmonic_budget
        self.quality = quality
        self.forward_check = forward_check
        self.calls = 0
        self.prefiltered_alternatives = 0
        self.harmonic_budget_prefiltered = 0
        self.forward_check_rejections = 0
        self.empty_domains = 0

    def __call__(self, session: Any) -> tuple[ChoicePoint, ...]:
        assigned = _assignments(session)
        segment = next(
            (item for item in self.segments if item not in assigned),
            None,
        )
        if segment is None:
            return ()
        self.calls += 1
        blocks = _apply_assignments(self.defaults, assigned)
        energies = self.evaluator.candidate_energies(blocks, segment)
        if self.sequence_factor is not None:
            energies = energies + self.sequence_factor.candidate_energies(
                assigned,
                segment,
                self.evaluator.candidates,
                self.segments,
            )
        if self.harmonic_budget is not None:
            energies = energies + self.harmonic_budget.candidate_energies(
                assigned,
                segment,
                self.evaluator.candidates,
            )
        maximum = float(np.max(energies))
        lower, upper = self.voice_ranges[segment[2]]
        allowed = []
        for index, pitch in enumerate(self.evaluator.candidates):
            if not lower <= int(pitch) <= upper:
                continue
            if self.quality is not None and not self.quality.candidate_is_allowed(
                assigned,
                segment,
                int(pitch),
            ):
                self.prefiltered_alternatives += 1
                continue
            if (
                self.harmonic_budget is not None
                and not self.harmonic_budget.candidate_is_allowed(
                    assigned,
                    segment,
                    int(pitch),
                )
            ):
                self.harmonic_budget_prefiltered += 1
                continue
            if self.forward_check and self.quality is not None:
                trial = {**assigned, segment: int(pitch)}
                following = next(
                    (item for item in self.segments if item not in trial),
                    None,
                )
                if following is not None:
                    following_lower, following_upper = self.voice_ranges[following[2]]
                    has_support = any(
                        following_lower <= int(candidate) <= following_upper
                        and self.quality.candidate_is_allowed(
                            trial,
                            following,
                            int(candidate),
                        )
                        and (
                            self.harmonic_budget is None
                            or self.harmonic_budget.candidate_is_allowed(
                                trial,
                                following,
                                int(candidate),
                            )
                        )
                        for candidate in self.evaluator.candidates
                    )
                    if not has_support:
                        self.forward_check_rejections += 1
                        continue
            allowed.append(index)
        order = sorted(
            allowed,
            key=lambda index: (
                -float(energies[index]),
                int(self.evaluator.candidates[index]),
            ),
        )
        if not order:
            self.empty_domains += 1
            return ()
        alternatives = tuple(
            ChoiceAlternative(
                name=f"pitch_{int(self.evaluator.candidates[index])}",
                facts=(
                    _assignment_fact(
                        segment,
                        int(self.evaluator.candidates[index]),
                    ),
                ),
                value=Number(int(self.evaluator.candidates[index])),
                weight=math.exp(max(float(energies[index] - maximum), -700.0)),
                metadata={
                    "segment": segment,
                    "conditional_energy": float(energies[index]),
                },
            )
            for index in order
        )
        return (
            ChoicePoint(
                f"assign_{segment[0]}_{segment[1]}_{segment[2]}",
                alternatives,
                variable=_segment_atom(segment),
            ),
        )


class JointHomorhythmicChoiceProvider:
    """Choose one complete lower-voice voicing per soprano attack."""

    def __init__(
        self,
        *,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        evaluator: ExactSegmentEvaluator,
        voice_ranges: dict[int, tuple[int, int]],
        quality: FullQualityPropagator,
        allowed_qualities: frozenset[int],
    ) -> None:
        self.segments = segments
        self.defaults = defaults
        self.evaluator = evaluator
        self.voice_ranges = voice_ranges
        self.quality = quality
        grouped: dict[int, dict[int, Segment]] = {}
        for segment in segments:
            grouped.setdefault(segment[0], {})[segment[2]] = segment
        if any(set(voices) != {1, 2, 3} for voices in grouped.values()):
            raise ValueError("Joint homorhythmic choices require three voices per time")
        self.groups = tuple(
            (time, tuple(voices[voice] for voice in range(1, 4)))
            for time, voices in sorted(grouped.items())
        )
        self.allowed_signatures = _allowed_homorhythmic_signatures(allowed_qualities)
        self.calls = 0
        self.prefiltered_alternatives = 0
        self.harmonic_budget_prefiltered = 0
        self.forward_check_rejections = 0
        self.empty_domains = 0
        self.forward_check = False
        self._voicing_cache: dict[int, tuple[tuple[int, int, int], ...]] = {}

    def _voicings(
        self, soprano: int, tonic_pc: int
    ) -> tuple[tuple[int, int, int], ...]:
        cached = self._voicing_cache.get(soprano)
        if cached is not None:
            return cached
        ranges = tuple(self.voice_ranges[voice] for voice in range(1, 4))
        output = []
        for alto in range(ranges[0][0], min(ranges[0][1], soprano) + 1):
            if soprano - alto > 12:
                continue
            for tenor in range(ranges[1][0], min(ranges[1][1], alto) + 1):
                if alto - tenor > 12:
                    continue
                for bass in range(ranges[2][0], min(ranges[2][1], tenor) + 1):
                    if tenor - bass > 19:
                        continue
                    block = np.asarray((soprano, alto, tenor, bass), dtype=np.int16)
                    signature = _tonic_relative_signature(block, tonic_pc)
                    if signature in self.allowed_signatures:
                        output.append((alto, tenor, bass))
        result = tuple(output)
        self._voicing_cache[soprano] = result
        return result

    def _prior_energy(self, voicing: tuple[int, int, int]) -> float:
        return float(
            sum(
                self.evaluator.program.register_logits[
                    voice,
                    pitch - self.evaluator.program.candidate_min,
                ]
                + self.evaluator.program.tonal_logits[
                    voice,
                    self.evaluator.lattice.mode,
                    (pitch - self.evaluator.lattice.tonic_pc) % 12,
                ]
                for voice, pitch in enumerate(voicing, start=1)
            )
        )

    @staticmethod
    def _violates_pairwise_voice_leading(
        previous: tuple[int, int, int, int],
        current: tuple[int, int, int, int],
    ) -> bool:
        """Apply the local two-position rules before opening a branch."""

        for upper in range(4):
            for lower in range(upper + 1, 4):
                source_interval = (previous[upper] - previous[lower]) % 12
                target_interval = (current[upper] - current[lower]) % 12
                upper_motion = current[upper] - previous[upper]
                lower_motion = current[lower] - previous[lower]
                similar_nonzero = (
                    upper_motion != 0
                    and lower_motion != 0
                    and (upper_motion > 0) == (lower_motion > 0)
                )
                if (
                    similar_nonzero
                    and source_interval == target_interval
                    and target_interval in {0, 7}
                ):
                    return True
        for upper, lower in ((0, 1), (1, 2), (2, 3)):
            if current[lower] > previous[upper]:
                return True
            if current[upper] < previous[lower]:
                return True
        soprano_motion = current[0] - previous[0]
        bass_motion = current[3] - previous[3]
        return bool(
            abs(soprano_motion) > 2
            and bass_motion != 0
            and (soprano_motion > 0) == (bass_motion > 0)
            and (current[0] - current[3]) % 12 == 7
        )

    def _bass_repeat_run(
        self,
        assignments: dict[Segment, int],
        candidate_bass: int,
    ) -> int:
        run = 1
        for _, segments in reversed(self.groups):
            bass_segment = segments[2]
            pitch = assignments.get(bass_segment)
            if pitch is None:
                continue
            if pitch != candidate_bass:
                break
            run += 1
        return run

    def _search_energy(
        self,
        previous: tuple[int, int, int, int] | None,
        current: tuple[int, int, int, int],
    ) -> float:
        energy = self._prior_energy(current[1:])
        if previous is None:
            return energy
        motions = tuple(current[voice] - previous[voice] for voice in range(1, 4))
        steps = sum(0 < abs(motion) <= 2 for motion in motions)
        common_tones = sum(motion == 0 for motion in motions)
        total_motion = sum(abs(motion) for motion in motions)
        bass_step = 0 < abs(motions[2]) <= 2
        bass_repeat = motions[2] == 0
        # This only orders branches; it is not a probability or an additional
        # admissibility condition.  Learned factors remain conceptually separate.
        return (
            energy
            + 4.0 * steps
            + 1.0 * common_tones
            - 0.15 * total_motion
            + (3.0 if bass_step else 0.0)
            - (3.0 if bass_repeat else 0.0)
        )

    def __call__(self, session: Any) -> tuple[ChoicePoint, ...]:
        assigned = _assignments(session)
        pending = next(
            (
                (time, segments)
                for time, segments in self.groups
                if any(segment not in assigned for segment in segments)
            ),
            None,
        )
        if pending is None:
            return ()
        self.calls += 1
        time, segments = pending
        soprano = int(self.defaults[time, 0])
        previous = None
        previous_group = next(
            (
                group_segments
                for group_time, group_segments in reversed(self.groups)
                if group_time < time
            ),
            None,
        )
        if previous_group is not None and all(
            segment in assigned for segment in previous_group
        ):
            previous_time = previous_group[0][0]
            previous = (
                int(self.defaults[previous_time, 0]),
                *(int(assigned[segment]) for segment in previous_group),
            )
        allowed = []
        for voicing in self._voicings(soprano, self.evaluator.lattice.tonic_pc):
            current = (soprano, *voicing)
            if previous is not None and self._violates_pairwise_voice_leading(
                previous, current
            ):
                self.prefiltered_alternatives += 1
                continue
            if self._bass_repeat_run(assigned, voicing[2]) > 3:
                self.prefiltered_alternatives += 1
                continue
            allowed.append((voicing, self._search_energy(previous, current)))
        allowed.sort(key=lambda row: (-row[1], row[0]))
        if not allowed:
            self.empty_domains += 1
            return ()
        maximum = allowed[0][1]
        alternatives = tuple(
            ChoiceAlternative(
                name=f"voicing_{alto}_{tenor}_{bass}",
                facts=tuple(
                    _assignment_fact(segment, pitch)
                    for segment, pitch in zip(
                        segments,
                        (alto, tenor, bass),
                        strict=True,
                    )
                ),
                value=FiniteSequence((Number(alto), Number(tenor), Number(bass))),
                weight=math.exp(max(energy - maximum, -700.0)),
                metadata={
                    "time": time,
                    "voicing": (alto, tenor, bass),
                    "learned_register_tonal_energy": energy,
                },
            )
            for (alto, tenor, bass), energy in allowed
        )
        return (
            ChoicePoint(
                f"harmonize_soprano_note_{time}",
                alternatives,
                variable=Atom(f"soprano_note_{time}_voicing"),
            ),
        )


@dataclass(frozen=True, slots=True)
class BoundaryChordFactor:
    """Leave-one-piece-out categorical factors for opening and closing chords."""

    source: Path
    alpha: float
    excluded_piece_id: str
    records: tuple[dict[str, Any], ...]

    @classmethod
    def load(cls, path: Path, *, excluded_piece_id: str) -> BoundaryChordFactor:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != "TRAIN_ONLY_FROZEN_COUNTS":
            raise ValueError("Boundary model is not a frozen train-only model")
        if payload.get("test_loaded") or payload.get("validation_loaded"):
            raise ValueError("Boundary factor fitting must not load validation or test")
        records = tuple(
            row
            for row in payload["records"]
            if str(row["piece_id"]) != excluded_piece_id
        )
        return cls(
            source=path.resolve(),
            alpha=float(payload["alpha"]),
            excluded_piece_id=excluded_piece_id,
            records=records,
        )

    @staticmethod
    def _state(candidate: ReifiedChordCandidate) -> tuple[int, int, int]:
        return (
            candidate.quality,
            candidate.root_degree,
            candidate.inversion_interval,
        )

    @staticmethod
    def _record_state(record: dict[str, Any]) -> tuple[int, int, int]:
        return (
            int(record["quality"]),
            int(record["root_degree"]),
            int(record["inversion_interval"]),
        )

    def energies(
        self,
        candidates: tuple[ReifiedChordCandidate, ...],
        *,
        boundary: str,
        mode: str,
        soprano_degree: int,
    ) -> np.ndarray:
        """Return smoothed corpus log-probabilities for candidate chord states."""

        backoff_rows = tuple(
            row
            for row in self.records
            if row["boundary"] == boundary and row["mode"] == mode
        )
        conditional_rows = tuple(
            row for row in backoff_rows if int(row["soprano_degree"]) == soprano_degree
        )
        selected = conditional_rows or backoff_rows
        if not selected:
            raise ValueError(f"No boundary training rows for {boundary}/{mode}")
        counts: dict[tuple[int, int, int], int] = {}
        interval_counts: tuple[dict[int, int], ...] = ({}, {}, {})
        for row in selected:
            state = self._record_state(row)
            counts[state] = counts.get(state, 0) + 1
            for voice, interval in enumerate(row["lower_intervals_from_soprano"]):
                value = int(interval)
                interval_counts[voice][value] = interval_counts[voice].get(value, 0) + 1
        states = frozenset((*counts, *(self._state(row) for row in candidates)))
        denominator = len(selected) + self.alpha * len(states)
        output = np.asarray(
            [
                math.log((counts.get(self._state(row), 0) + self.alpha) / denominator)
                for row in candidates
            ],
            dtype=np.float64,
        )
        for voice in range(3):
            candidate_intervals = tuple(
                row.pitches[0] - row.lower_pitches[voice] for row in candidates
            )
            interval_values = frozenset((*interval_counts[voice], *candidate_intervals))
            interval_denominator = len(selected) + self.alpha * len(interval_values)
            output += np.asarray(
                [
                    math.log(
                        (interval_counts[voice].get(interval, 0) + self.alpha)
                        / interval_denominator
                    )
                    for interval in candidate_intervals
                ],
                dtype=np.float64,
            )
        return output


class OfficialManualTransitionScorer:
    """Pure additive score for the five frozen transition factors."""

    def __init__(self, rulebase: Path = DEFAULT_RULEBASE) -> None:
        groups = parse_factor_groups(
            (rulebase / "official_manual.factors").read_text(encoding="utf-8")
        )
        self.weights = {
            factor.name: float(factor.parameter.log_weight)
            for group in groups
            for factor in group.factors
        }
        expected = {
            "manual_parallel_fifth",
            "manual_parallel_octave",
            "manual_direct_fifth",
            "manual_voice_overlap",
            "manual_leading_tone_resolution",
        }
        if set(self.weights) != expected:
            raise ValueError("The official manual transition factors changed")

    @staticmethod
    def activations(
        previous: PitchBlock,
        current: PitchBlock,
        tonic_pc: int,
    ) -> frozenset[str]:
        output: set[str] = set()
        for upper in range(4):
            for lower in range(upper + 1, 4):
                source_interval = (previous[upper] - previous[lower]) % 12
                target_interval = (current[upper] - current[lower]) % 12
                upper_motion = current[upper] - previous[upper]
                lower_motion = current[lower] - previous[lower]
                similar_nonzero = (
                    upper_motion != 0
                    and lower_motion != 0
                    and (upper_motion > 0) == (lower_motion > 0)
                )
                if similar_nonzero and source_interval == target_interval == 7:
                    output.add("manual_parallel_fifth")
                if similar_nonzero and source_interval == target_interval == 0:
                    output.add("manual_parallel_octave")
        soprano_motion = current[0] - previous[0]
        bass_motion = current[3] - previous[3]
        if (
            abs(soprano_motion) > 2
            and bass_motion != 0
            and (soprano_motion > 0) == (bass_motion > 0)
            and (current[0] - current[3]) % 12 == 7
        ):
            output.add("manual_direct_fifth")
        if any(
            current[lower] > previous[upper] or current[upper] < previous[lower]
            for upper, lower in ((0, 1), (1, 2), (2, 3))
        ):
            output.add("manual_voice_overlap")
        leading_pc = (tonic_pc - 1) % 12
        if any(
            source % 12 == leading_pc and target == source + 1
            for source, target in zip(previous, current, strict=True)
        ):
            output.add("manual_leading_tone_resolution")
        return frozenset(output)

    def energy(
        self,
        previous: PitchBlock,
        current: PitchBlock,
        tonic_pc: int,
    ) -> float:
        return sum(
            self.weights[name] for name in self.activations(previous, current, tonic_pc)
        )


class ReifiedChordSpace:
    """Finite observable chord domains and compiled binary rule supports.

    A candidate is a complete SATB verticality at one soprano attack.  It is
    not a hidden harmonic state: pitch content, root, quality and inversion
    are all deterministic attributes of the four notes.  The support matrices
    compile the local two-position rules once, before search.
    """

    def __init__(
        self,
        *,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        lattice: k3.RhythmicLattice,
        voice_ranges: dict[int, tuple[int, int]],
        allowed_qualities: frozenset[int],
        manual_profile: str,
    ) -> None:
        grouped: dict[int, dict[int, Segment]] = {}
        for segment in segments:
            grouped.setdefault(segment[0], {})[segment[2]] = segment
        if any(set(voices) != {1, 2, 3} for voices in grouped.values()):
            raise ValueError("Reified chord choices require three voices per time")
        self.groups = tuple(
            (time, tuple(voices[voice] for voice in range(1, 4)))
            for time, voices in sorted(grouped.items())
        )
        self.time_to_position = {
            time: position for position, (time, _) in enumerate(self.groups)
        }
        allowed_signatures = _allowed_homorhythmic_signatures(allowed_qualities)
        domains = []
        for time, _ in self.groups:
            soprano = int(defaults[time, 0])
            rows = []
            for alto, tenor, bass in self._voicings(
                soprano,
                lattice.tonic_pc,
                voice_ranges,
                allowed_signatures,
            ):
                pitches = (soprano, alto, tenor, bass)
                block = np.asarray(pitches, dtype=np.int16)
                analysis = v34_harmony.analyze_block(block, lattice.tonic_pc)
                if (
                    int(analysis["analysis_count"]) != 1
                    or int(analysis["quality"]) not in allowed_qualities
                    or len(set(int(pitch) % 12 for pitch in pitches)) < 3
                ):
                    raise AssertionError(
                        "A reified chord candidate must have one named analysis"
                    )
                rows.append(
                    ReifiedChordCandidate(
                        time=time,
                        index=len(rows),
                        pitches=pitches,
                        signature=int(analysis["signature"]),
                        quality=int(analysis["quality"]),
                        root_degree=int(analysis["root_degree"]),
                        inversion_interval=int(analysis["inversion_interval"]),
                    )
                )
            if not rows:
                raise ValueError(f"Empty static chord domain at time {time}")
            domains.append(tuple(rows))
        self.domains = tuple(domains)
        self.supports = tuple(
            self._pair_support(
                left,
                right,
                tonic_pc=lattice.tonic_pc,
                strict_manual=manual_profile == "pedagogical_strict",
            )
            for left, right in zip(self.domains[:-1], self.domains[1:], strict=True)
        )

    @staticmethod
    def _voicings(
        soprano: int,
        tonic_pc: int,
        voice_ranges: dict[int, tuple[int, int]],
        allowed_signatures: frozenset[int],
    ) -> tuple[tuple[int, int, int], ...]:
        output = []
        alto_range, tenor_range, bass_range = (
            voice_ranges[voice] for voice in range(1, 4)
        )
        for alto in range(alto_range[0], min(alto_range[1], soprano) + 1):
            if soprano - alto > 12:
                continue
            for tenor in range(tenor_range[0], min(tenor_range[1], alto) + 1):
                if alto - tenor > 12:
                    continue
                for bass in range(bass_range[0], min(bass_range[1], tenor) + 1):
                    if tenor - bass > 19:
                        continue
                    block = np.asarray((soprano, alto, tenor, bass), dtype=np.int16)
                    signature = _tonic_relative_signature(block, tonic_pc)
                    if signature in allowed_signatures:
                        output.append((alto, tenor, bass))
        return tuple(output)

    @staticmethod
    def violates_pairwise_rules(
        previous: PitchBlock,
        current: PitchBlock,
    ) -> bool:
        """Compiled execution form of the local manual voice-leading rules."""

        return JointHomorhythmicChoiceProvider._violates_pairwise_voice_leading(
            previous,
            current,
        )

    @classmethod
    def _pair_support(
        cls,
        left: tuple[ReifiedChordCandidate, ...],
        right: tuple[ReifiedChordCandidate, ...],
        *,
        tonic_pc: int = 0,
        strict_manual: bool = False,
    ) -> np.ndarray:
        """Compile all admissible adjacent chord pairs into one boolean matrix."""

        left_blocks = np.asarray([row.pitches for row in left], dtype=np.int16)
        right_blocks = np.asarray([row.pitches for row in right], dtype=np.int16)
        support = np.ones((len(left), len(right)), dtype=bool)
        if not strict_manual:
            return support
        motions = right_blocks[None, :, :] - left_blocks[:, None, :]
        support &= np.all(np.abs(motions) <= 7, axis=2)
        for upper in range(4):
            for lower in range(upper + 1, 4):
                source = (left_blocks[:, upper] - left_blocks[:, lower]) % 12
                target = (right_blocks[:, upper] - right_blocks[:, lower]) % 12
                upper_motion = motions[:, :, upper]
                lower_motion = motions[:, :, lower]
                similar_nonzero = (
                    (upper_motion != 0)
                    & (lower_motion != 0)
                    & ((upper_motion > 0) == (lower_motion > 0))
                )
                parallel_perfect = (
                    similar_nonzero
                    & (source[:, None] == target[None, :])
                    & np.isin(target[None, :], (0, 7))
                )
                support &= ~parallel_perfect
        for upper, lower in ((0, 1), (1, 2), (2, 3)):
            support &= ~(right_blocks[None, :, lower] > left_blocks[:, None, upper])
            support &= ~(right_blocks[None, :, upper] < left_blocks[:, None, lower])
        soprano_motion = motions[:, :, 0]
        bass_motion = motions[:, :, 3]
        direct_fifth = (
            (np.abs(soprano_motion) > 2)
            & (bass_motion != 0)
            & ((soprano_motion > 0) == (bass_motion > 0))
            & ((right_blocks[None, :, 0] - right_blocks[None, :, 3]) % 12 == 7)
        )
        support &= ~direct_fifth
        leading_pc = (tonic_pc - 1) % 12
        for voice in range(4):
            source_is_leading = left_blocks[:, voice] % 12 == leading_pc
            resolves = motions[:, :, voice] == 1
            support &= ~(source_is_leading[:, None] & ~resolves)
        return support

    def masks(self, session: Any) -> list[np.ndarray]:
        """Return current finite domains encoded by branch-local facts."""

        chosen = _chord_indices(session, CHOSEN_CHORD)
        rejected = _chord_indices(session, REJECTED_CHORD)
        output = []
        for position, (time, _) in enumerate(self.groups):
            mask = np.ones(len(self.domains[position]), dtype=bool)
            for index in rejected.get(time, ()):
                if 0 <= index < mask.size:
                    mask[index] = False
            selected = chosen.get(time, set())
            if len(selected) > 1:
                mask[:] = False
            elif selected:
                selected_index = next(iter(selected))
                was_available = 0 <= selected_index < mask.size and bool(
                    mask[selected_index]
                )
                mask[:] = False
                if was_available:
                    mask[selected_index] = True
            output.append(mask)
        return output


class ReifiedChordDomainPropagator:
    """Maintain arc-consistent persistent chord domains inside Snarky search."""

    watched_relations = frozenset((ASSIGNED_PITCH, CHOSEN_CHORD, REJECTED_CHORD))

    def __init__(self, space: ReifiedChordSpace) -> None:
        self.space = space
        self.calls = 0
        self.domain_removals = 0
        self.singleton_assignments = 0
        self.empty_domains = 0
        self.minimum_live_domain = min(len(domain) for domain in space.domains)

    def _revise(self, masks: list[np.ndarray]) -> None:
        """Reach arc consistency on the complete adjacent-position chain."""

        changed = True
        while changed:
            changed = False
            for position, support in enumerate(self.space.supports):
                left = masks[position]
                right = masks[position + 1]
                left_supported = (
                    np.any(support[:, right], axis=1)
                    if np.any(right)
                    else np.zeros_like(left)
                )
                revised_left = left & left_supported
                right_supported = (
                    np.any(support[left, :], axis=0)
                    if np.any(left)
                    else np.zeros_like(right)
                )
                revised_right = right & right_supported
                if not np.array_equal(revised_left, left):
                    masks[position] = revised_left
                    changed = True
                if not np.array_equal(revised_right, right):
                    masks[position + 1] = revised_right
                    changed = True

    def _propagate_bass_runs(self, masks: list[np.ndarray]) -> None:
        """Remove a fourth identical bass once three predecessors are fixed."""

        for position in range(3, len(masks)):
            fixed = []
            for previous in range(position - 3, position):
                live = np.flatnonzero(masks[previous])
                if live.size != 1:
                    fixed = []
                    break
                fixed.append(self.space.domains[previous][int(live[0])].pitches[3])
            if fixed and len(set(fixed)) == 1:
                repeated = fixed[0]
                masks[position] &= np.asarray(
                    [
                        candidate.pitches[3] != repeated
                        for candidate in self.space.domains[position]
                    ],
                    dtype=bool,
                )

    def __call__(self, session: Any) -> None:
        contradiction = Fact(Triple(PROBLEM, STATE, CONTRADICTION))
        if contradiction in session.facts:
            return
        self.calls += 1
        before = self.space.masks(session)
        masks = [mask.copy() for mask in before]
        self._revise(masks)
        self._propagate_bass_runs(masks)
        self._revise(masks)
        for position, mask in enumerate(masks):
            time, segments = self.space.groups[position]
            live = np.flatnonzero(mask)
            if live.size == 0:
                self.empty_domains += 1
                session.assume(
                    contradiction,
                    Fact(Triple(PROBLEM, VIOLATED_CONSTRAINT, REIFIED_CHORD_DOMAIN)),
                    label=f"constraint:{REIFIED_CHORD_DOMAIN.name}:{time}",
                )
                return
            self.minimum_live_domain = min(self.minimum_live_domain, int(live.size))
            removed = np.flatnonzero(before[position] & ~mask)
            if removed.size:
                self.domain_removals += int(removed.size)
                session.assume(
                    *(
                        _chord_fact(time, REJECTED_CHORD, int(index))
                        for index in removed
                    ),
                    label=f"propagate:reified_chord_domain:{time}",
                )
            if live.size != 1:
                continue
            index = int(live[0])
            chosen_fact = _chord_fact(time, CHOSEN_CHORD, index)
            if chosen_fact in session.facts:
                continue
            candidate = self.space.domains[position][index]
            self.singleton_assignments += 1
            session.assume(
                chosen_fact,
                *(
                    _assignment_fact(segment, pitch)
                    for segment, pitch in zip(
                        segments,
                        candidate.lower_pitches,
                        strict=True,
                    )
                ),
                label=f"propagate:singleton_reified_chord:{time}",
            )


class ReifiedChordChoiceProvider:
    """Choose propagated chord-domain values using exact learned factors."""

    def __init__(
        self,
        *,
        space: ReifiedChordSpace,
        defaults: np.ndarray,
        evaluator: ExactSegmentEvaluator,
        quality: FullQualityPropagator,
        choice_order: str,
        manual_budget: OfficialManualBudgetPropagator | None = None,
        manual_factors: OfficialManualTransitionScorer | None = None,
        boundary_factor: BoundaryChordFactor | None = None,
    ) -> None:
        self.space = space
        self.defaults = defaults
        self.evaluator = evaluator
        self.quality = quality
        self.choice_order = choice_order
        self.manual_budget = manual_budget
        self.manual_factors = manual_factors
        self.boundary_factor = boundary_factor
        self.calls = 0
        self.prefiltered_alternatives = 0
        self.harmonic_budget_prefiltered = 0
        self.manual_budget_prefiltered = 0
        self.forward_check_rejections = 0
        self.empty_domains = 0
        self.forward_check = True
        self.batch_factor_evaluations = 0
        self.factor_weighted_choices = 0
        self.manual_factor_weighted_choices = 0
        self.boundary_factor_weighted_choices = 0
        self.boundary_energy_spreads: dict[str, float] = {}

    def _boundary_factor_energies(
        self,
        position: int,
        candidates: tuple[ReifiedChordCandidate, ...],
    ) -> np.ndarray:
        last_position = len(self.space.groups) - 1
        if position not in {0, last_position}:
            return np.zeros(len(candidates), dtype=np.float64)
        if self.boundary_factor is None:
            raise ValueError("Reified chord search requires a boundary factor model")
        boundary = "opening" if position == 0 else "closing"
        time = self.space.groups[position][0]
        soprano_degree = (
            int(self.defaults[time, 0]) - self.evaluator.lattice.tonic_pc
        ) % 12
        output = self.boundary_factor.energies(
            candidates,
            boundary=boundary,
            mode=self.evaluator.lattice.mode,
            soprano_degree=soprano_degree,
        )
        for index, candidate in enumerate(candidates):
            output[index] += sum(
                self.evaluator.program.register_logits[
                    voice,
                    pitch - self.evaluator.program.candidate_min,
                ]
                + self.evaluator.program.tonal_logits[
                    voice,
                    self.evaluator.lattice.mode,
                    (pitch - self.evaluator.lattice.tonic_pc) % 12,
                ]
                for voice, pitch in enumerate(candidate.lower_pitches, start=1)
            )
        spread = float(np.ptp(output))
        if spread <= 1e-12:
            raise RuntimeError(f"The {boundary} CHOICE has no learned discrimination")
        self.boundary_factor_weighted_choices += 1
        self.boundary_energy_spreads[boundary] = spread
        return output

    def _manual_factor_energies(
        self,
        assignments: dict[Segment, int],
        position: int,
        candidates: tuple[ReifiedChordCandidate, ...],
    ) -> np.ndarray:
        if self.manual_factors is None:
            return np.zeros(len(candidates), dtype=np.float64)
        blocks = _apply_assignments(self.defaults, assignments)
        output = np.zeros(len(candidates), dtype=np.float64)
        for row, candidate in enumerate(candidates):
            if position > 0 and all(
                segment in assignments for segment in self.space.groups[position - 1][1]
            ):
                previous = tuple(
                    int(value) for value in blocks[self.space.groups[position - 1][0]]
                )
                output[row] += self.manual_factors.energy(
                    previous,
                    candidate.pitches,
                    self.evaluator.lattice.tonic_pc,
                )
            if position + 1 < len(self.space.groups) and all(
                segment in assignments for segment in self.space.groups[position + 1][1]
            ):
                following = tuple(
                    int(value) for value in blocks[self.space.groups[position + 1][0]]
                )
                output[row] += self.manual_factors.energy(
                    candidate.pitches,
                    following,
                    self.evaluator.lattice.tonic_pc,
                )
        return output

    def _creates_four_bass_repetitions(
        self,
        assignments: dict[Segment, int],
        position: int,
        candidate: ReifiedChordCandidate,
    ) -> bool:
        bass_by_position: dict[int, int] = {}
        for index, (_, segments) in enumerate(self.space.groups):
            bass = assignments.get(segments[2])
            if bass is not None:
                bass_by_position[index] = bass
        bass_by_position[position] = candidate.pitches[3]
        for start in range(
            max(0, position - 3),
            min(position + 1, len(self.space.groups) - 3),
        ):
            values = [bass_by_position.get(index) for index in range(start, start + 4)]
            if None not in values and len(set(values)) == 1:
                return True
        return False

    def _violates_strict_window_rules(
        self,
        assignments: dict[Segment, int],
        position: int,
        candidate: ReifiedChordCandidate,
    ) -> bool:
        if (
            self.manual_budget is None
            or self.manual_budget.profile != "pedagogical_strict"
        ):
            return False
        _, segments = self.space.groups[position]
        trial = {
            **assignments,
            **dict(zip(segments, candidate.lower_pitches, strict=True)),
        }
        blocks = _apply_assignments(self.defaults, trial)
        assigned_positions = {
            index
            for index, (_, group_segments) in enumerate(self.space.groups)
            if all(segment in trial for segment in group_segments)
        }
        for start in range(
            max(0, position - 2),
            min(position + 1, len(self.space.groups) - 2),
        ):
            if not all(
                index in assigned_positions for index in range(start, start + 3)
            ):
                continue
            times = tuple(
                self.space.groups[index][0] for index in range(start, start + 3)
            )
            first, middle, last = (blocks[time] for time in times)
            if int(first[3]) == int(middle[3]):
                continue
            for voice in range(3):
                prepared = int(first[voice]) == int(middle[voice])
                dissonant = int(middle[voice] - middle[3]) % 12 in DISSONANT_ABOVE_BASS
                resolution = int(middle[voice] - last[voice])
                if prepared and dissonant and resolution not in {1, 2}:
                    return True
        return False

    def _incremental_evaluations(
        self,
        assignments: dict[Segment, int],
        position: int,
        candidates: tuple[ReifiedChordCandidate, ...],
    ) -> tuple[np.ndarray, list[set[str]], int]:
        """Return exact newly-decided log scores and hard activations."""

        _, segments = self.space.groups[position]
        assigned_keys = frozenset(assignments)
        trial_keys = assigned_keys | frozenset(segments)
        newly_decidable = tuple(
            target
            for target in self.quality.segments
            if self.quality.dependencies[target].issubset(trial_keys)
            and not self.quality.dependencies[target].issubset(assigned_keys)
        )
        energies = np.zeros(len(candidates), dtype=np.float64)
        violations = [set() for _ in candidates]
        if not newly_decidable:
            return energies, violations, 0
        base = _apply_assignments(self.defaults, assignments)
        contexts = np.repeat(base[None, :, :], len(candidates), axis=0)
        for row, candidate in enumerate(candidates):
            for segment, pitch in zip(segments, candidate.lower_pitches, strict=True):
                start, end, voice = segment
                contexts[row, start:end, voice] = pitch
        scored = frozenset(self.quality.scored_segments)
        scored_count = 0
        for target in newly_decidable:
            rows = self.evaluator.evaluate_many(contexts, target)
            self.batch_factor_evaluations += 1
            if target in scored:
                energies += np.asarray(
                    [row.log_probability for row in rows],
                    dtype=np.float64,
                )
                scored_count += 1
            for index, row in enumerate(rows):
                violations[index].update(row.violations)
        return energies, violations, scored_count

    def __call__(self, session: Any) -> tuple[ChoicePoint, ...]:
        chosen = _chord_indices(session, CHOSEN_CHORD)
        masks = self.space.masks(session)
        pending = [
            position
            for position, (time, _) in enumerate(self.space.groups)
            if time not in chosen
        ]
        if not pending:
            return ()
        self.calls += 1
        position = (
            pending[0]
            if self.choice_order == "chronological"
            else min(
                pending,
                key=lambda index: (int(np.count_nonzero(masks[index])), index),
            )
        )
        time, segments = self.space.groups[position]
        live_indices = tuple(int(index) for index in np.flatnonzero(masks[position]))
        if not live_indices:
            self.empty_domains += 1
            return ()
        candidates = tuple(
            self.space.domains[position][index] for index in live_indices
        )
        assignments = _assignments(session)
        k3_energies, violations, scored_count = self._incremental_evaluations(
            assignments,
            position,
            candidates,
        )
        manual_energies = self._manual_factor_energies(
            assignments,
            position,
            candidates,
        )
        boundary_energies = self._boundary_factor_energies(position, candidates)
        energies = k3_energies + manual_energies + boundary_energies
        allowed = []
        for row, candidate in enumerate(candidates):
            if (
                violations[row]
                or self._creates_four_bass_repetitions(
                    assignments,
                    position,
                    candidate,
                )
                or self._violates_strict_window_rules(
                    assignments,
                    position,
                    candidate,
                )
            ):
                self.prefiltered_alternatives += 1
                continue
            trial = {
                **assignments,
                **dict(zip(segments, candidate.lower_pitches, strict=True)),
            }
            if (
                self.manual_budget is not None
                and not self.manual_budget.candidate_is_allowed(trial)
            ):
                self.manual_budget_prefiltered += 1
                continue
            allowed.append((row, candidate))
        if not allowed:
            self.empty_domains += 1
            return ()
        if scored_count:
            self.factor_weighted_choices += 1
        if np.any(manual_energies):
            self.manual_factor_weighted_choices += 1
        maximum = max(float(energies[row]) for row, _ in allowed)
        allowed.sort(key=lambda item: (-float(energies[item[0]]), item[1].pitches))
        alternatives = tuple(
            ChoiceAlternative(
                name=(
                    f"chord_{candidate.index}_"
                    f"{candidate.pitches[1]}_{candidate.pitches[2]}_{candidate.pitches[3]}"
                ),
                facts=(
                    _chord_fact(time, CHOSEN_CHORD, candidate.index),
                    *(
                        _assignment_fact(segment, pitch)
                        for segment, pitch in zip(
                            segments,
                            candidate.lower_pitches,
                            strict=True,
                        )
                    ),
                ),
                value=FiniteSequence(
                    tuple(Number(value) for value in candidate.lower_pitches)
                ),
                weight=math.exp(max(float(energies[row]) - maximum, -700.0)),
                metadata={
                    "time": time,
                    "candidate_index": candidate.index,
                    "pitches": candidate.pitches,
                    "quality": candidate.quality,
                    "root_degree": candidate.root_degree,
                    "inversion_interval": candidate.inversion_interval,
                    "incremental_pseudolikelihood": float(k3_energies[row]),
                    "official_manual_factor_energy": float(manual_energies[row]),
                    "boundary_factor_energy": float(boundary_energies[row]),
                    "total_choice_energy": float(energies[row]),
                    "newly_decidable_factor_conditionals": scored_count,
                },
            )
            for row, candidate in allowed
        )
        return (
            ChoicePoint(
                f"choose_reified_chord_{time}",
                alternatives,
                variable=_chord_position_atom(time),
            ),
        )


class FullQualityPropagator:
    """Propagate hard constraints and the learned full-sequence score floor."""

    watched_relations = frozenset((ASSIGNED_PITCH,))

    def __init__(
        self,
        *,
        segments: tuple[Segment, ...],
        scored_segments: tuple[Segment, ...],
        defaults: np.ndarray,
        evaluator: ExactSegmentEvaluator,
        threshold: float,
        harmonic_budget: StrongHarmonyBudget | None = None,
        defer_score_until_complete: bool = False,
        enforce_score_floor: bool = True,
    ) -> None:
        self.segments = segments
        self.scored_segments = scored_segments
        self.defaults = defaults
        self.evaluator = evaluator
        self.threshold = threshold
        self.harmonic_budget = harmonic_budget
        self.defer_score_until_complete = defer_score_until_complete
        self.enforce_score_floor = enforce_score_floor
        self.controllers = self._controllers()
        self.dependencies = {
            segment: self._dependencies(segment) for segment in segments
        }
        self.dependents = {
            controller: tuple(
                segment
                for segment in segments
                if controller in self.dependencies[segment]
            )
            for controller in segments
        }
        self.rejections: list[dict[str, Any]] = []

    def _controllers(self) -> dict[tuple[int, int], Segment]:
        output: dict[tuple[int, int], Segment] = {}
        for segment in self.segments:
            start, end, voice = segment
            for time in range(start, end):
                output[(time, voice)] = segment
        return output

    def _dependencies(self, segment: Segment) -> frozenset[Segment]:
        required_times = score_experiment._required_times(
            segment,
            self.defaults.shape[0],
        )
        return frozenset(
            self.controllers[(time, voice)]
            for time in required_times
            for voice in range(1, 4)
        )

    def evaluate(
        self,
        assignments: dict[Segment, int],
    ) -> tuple[
        float,
        int,
        tuple[tuple[Segment, SegmentEvaluation], ...],
        tuple[str, ...],
    ]:
        blocks = _apply_assignments(self.defaults, assignments)
        rows = tuple(
            (segment, self.evaluator.evaluate(blocks, segment))
            for segment in self.scored_segments
            if self.dependencies[segment].issubset(assignments)
        )
        scored_by_segment = dict(rows)
        decidable_segments = tuple(
            segment
            for segment in self.segments
            if self.dependencies[segment].issubset(assignments)
        )
        violations = {
            violation
            for row in scored_by_segment.values()
            for violation in row.violations
        }
        for segment in decidable_segments:
            if segment not in scored_by_segment:
                violations.update(self.evaluator.chosen_violations(blocks, segment))
        return (
            float(sum(row.log_probability for _, row in rows)),
            len(rows),
            rows,
            tuple(sorted(violations)),
        )

    def complete_score(
        self,
        assignments: dict[Segment, int],
    ) -> score_experiment.SequenceScore:
        total, count, rows, _ = self.evaluate(assignments)
        if count != len(self.scored_segments):
            raise ValueError("Cannot score an incomplete full generation")
        return score_experiment.SequenceScore(
            total=total,
            mean=total / count,
            contributions=tuple(
                (segment, row.log_probability) for segment, row in rows
            ),
        )

    def candidate_is_allowed(
        self,
        assignments: dict[Segment, int],
        segment: Segment,
        pitch: int,
    ) -> bool:
        """Apply every hard K3 predicate that this assignment makes decidable."""

        trial = {**assignments, segment: pitch}
        blocks = _apply_assignments(self.defaults, trial)
        for target in self.dependents[segment]:
            if not self.dependencies[target].issubset(trial):
                continue
            if self.evaluator.chosen_violations(blocks, target):
                return False
        return True

    def __call__(self, session: Any) -> None:
        contradiction = Fact(Triple(PROBLEM, STATE, CONTRADICTION))
        if contradiction in session.facts:
            return
        assigned = _assignments(session)
        complete = len(assigned) == len(self.segments)
        if not self.enforce_score_floor or (
            self.defer_score_until_complete and not complete
        ):
            blocks = _apply_assignments(self.defaults, assigned)
            decidable = tuple(
                segment
                for segment in self.segments
                if self.dependencies[segment].issubset(assigned)
            )
            violations = tuple(
                sorted(
                    {
                        violation
                        for segment in decidable
                        for violation in self.evaluator.chosen_violations(
                            blocks, segment
                        )
                    }
                )
            )
            fixed_total = 0.0
            scored = 0
        else:
            fixed_total, scored, _, violations = self.evaluate(assigned)
        cause = None
        if violations:
            cause = HARD_K3
        harmonic_statistics = (
            None
            if self.harmonic_budget is None
            else self.harmonic_budget.statistics(assigned)
        )
        if (
            cause is None
            and harmonic_statistics is not None
            and harmonic_statistics["dissonant_named"]
            > harmonic_statistics["maximum_dissonant_named"]
        ):
            cause = HARMONIC_DISSONANCE_BUDGET
        if (
            cause is None
            and harmonic_statistics is not None
            and harmonic_statistics["dissonant_chains"]
            > harmonic_statistics["maximum_dissonant_chains"]
        ):
            cause = HARMONIC_CHAIN_BUDGET
        required_total = self.threshold * len(self.scored_segments)
        if (
            cause is None
            and self.enforce_score_floor
            and (not self.defer_score_until_complete or complete)
            and fixed_total + 1e-12 < required_total
        ):
            cause = SCORE_FLOOR
        if cause is None:
            return
        self.rejections.append(
            {
                "cause": cause.name,
                "assigned_segments": len(assigned),
                "scored_segments": scored,
                "segment_count": len(self.scored_segments),
                "optimistic_total": fixed_total,
                "required_total": required_total,
                "violations": list(violations),
                "harmonic_budget": harmonic_statistics,
            }
        )
        session.assume(
            contradiction,
            Fact(Triple(PROBLEM, VIOLATED_CONSTRAINT, cause)),
            label=f"constraint:{cause.name}",
        )


def _parsed_score_from_blocks(
    lattice: k3.RhythmicLattice,
    blocks: np.ndarray,
    source: Path,
) -> ParsedSATBScore:
    frames = tuple(
        SATBFrame(
            offset=Fraction(str(float(lattice.offsets[index]))),
            pitches=tuple(int(value) for value in blocks[index]),
            attacks=tuple(bool(value) for value in lattice.attacks[index]),
        )
        for index in range(lattice.size)
    )
    lines = tuple(
        tuple(
            int(blocks[index, voice])
            for index in range(lattice.size)
            if bool(lattice.attacks[index, voice])
        )
        for voice in range(4)
    )
    return ParsedSATBScore(
        source=source,
        tonic_pc=lattice.tonic_pc,
        frames=frames,
        attacked_lines=lines,
    )


def _tonic_relative_signature(block: np.ndarray, tonic_pc: int) -> int:
    signature = 0
    for pitch in block:
        signature |= 1 << ((int(pitch) - tonic_pc) % 12)
    return signature


def _allowed_homorhythmic_signatures(
    allowed_qualities: frozenset[int],
) -> frozenset[int]:
    return frozenset(
        sum(1 << ((root + interval) % 12) for interval in intervals)
        for quality, (_, intervals) in enumerate(k3.NAMED_CHORD_QUALITIES)
        if quality in allowed_qualities
        for root in range(12)
    )


class HomorhythmicChordPropagator:
    """Require a recognizable chord whenever one vertical block is complete."""

    watched_relations = frozenset((ASSIGNED_PITCH,))

    def __init__(
        self,
        *,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        lattice: k3.RhythmicLattice,
        allowed_qualities: frozenset[int],
    ) -> None:
        self.defaults = defaults
        self.lattice = lattice
        self.controllers = {
            (time, voice): segment
            for segment in segments
            for voice in (segment[2],)
            for time in range(segment[0], segment[1])
        }
        self.allowed_signatures = _allowed_homorhythmic_signatures(allowed_qualities)
        self.rejections: list[dict[str, Any]] = []

    def __call__(self, session: Any) -> None:
        contradiction = Fact(Triple(PROBLEM, STATE, CONTRADICTION))
        if contradiction in session.facts:
            return
        assignments = _assignments(session)
        for time in range(self.lattice.size):
            controllers = tuple(
                self.controllers[(time, voice)] for voice in range(1, 4)
            )
            if not all(segment in assignments for segment in controllers):
                continue
            block = self.defaults[time].copy()
            for voice, segment in enumerate(controllers, start=1):
                block[voice] = assignments[segment]
            signature = _tonic_relative_signature(block, self.lattice.tonic_pc)
            if signature in self.allowed_signatures:
                continue
            analysis = v34_harmony.analyze_block(block, self.lattice.tonic_pc)
            self.rejections.append(
                {
                    "time": time,
                    "offset": float(self.lattice.offsets[time]),
                    "pitches": [int(value) for value in block],
                    "analysis": analysis,
                }
            )
            session.assume(
                contradiction,
                Fact(Triple(PROBLEM, VIOLATED_CONSTRAINT, HOMORHYTHMIC_CHORD)),
                label=f"constraint:{HOMORHYTHMIC_CHORD.name}",
            )
            return


class OfficialManualBudgetPropagator:
    """Reject complete branches outside the frozen Bach empirical envelope."""

    watched_relations = frozenset((ASSIGNED_PITCH,))

    def __init__(
        self,
        *,
        segments: tuple[Segment, ...],
        defaults: np.ndarray,
        lattice: k3.RhythmicLattice,
        source: Path,
        profile: str = "bach_empirical",
    ) -> None:
        self.segments = segments
        self.defaults = defaults
        self.lattice = lattice
        self.source = source
        self.profile = profile
        self.rejections: list[dict[str, Any]] = []
        self._cache: dict[tuple[tuple[Segment, int], ...], Any] = {}
        self.transition_scorer = OfficialManualTransitionScorer()
        payload = yaml.safe_load(
            (DEFAULT_RULEBASE / "empirical_budgets.yaml").read_text(encoding="utf-8")
        )
        self.thresholds = {
            str(row["metric_id"]): float(row["threshold"])
            for row in payload["promoted_budgets"]
        }
        self.maximum_exceeded_budgets = int(payload["maximum_exceeded_budgets"])
        self.group_budgets = {
            str(row["group_id"]): (
                frozenset(str(value) for value in row["metric_ids"]),
                int(row["maximum_exceeded_budgets"]),
                str(row["rule_id"]),
            )
            for row in payload["group_budgets"]
        }
        self.controllers = {
            (time, voice): segment
            for segment in segments
            for voice in (segment[2],)
            for time in range(segment[0], segment[1])
        }

    def _known_attack_line(
        self,
        assignments: dict[Segment, int],
        voice: int,
    ) -> tuple[int | None, ...]:
        output = []
        for time in range(self.lattice.size):
            if not bool(self.lattice.attacks[time, voice]):
                continue
            if voice == 0:
                output.append(int(self.defaults[time, voice]))
                continue
            segment = self.controllers[(time, voice)]
            output.append(assignments.get(segment))
        return tuple(output)

    def _irreversible_exceedances(
        self,
        assignments: dict[Segment, int],
    ) -> tuple[dict[str, Any], ...]:
        voice_names = ("soprano", "alto", "tenor", "bass")
        metrics: dict[str, float] = {}
        for voice, name in enumerate(voice_names):
            line = self._known_attack_line(assignments, voice)
            maximum_leap = max(
                (
                    abs(right - left)
                    for left, right in zip(line[:-1], line[1:], strict=True)
                    if left is not None and right is not None
                ),
                default=0,
            )
            metrics[f"{name}_maximum_leap"] = float(maximum_leap)
            if voice == 0:
                continue
            longest = 0
            current = 0
            previous: int | None = None
            for pitch in line:
                if pitch is None:
                    current = 0
                    previous = None
                elif pitch == previous:
                    current += 1
                else:
                    current = 1
                    previous = pitch
                longest = max(longest, current)
            metrics[f"{name}_longest_repeat_run"] = float(longest)
        blocks = _apply_assignments(self.defaults, assignments)
        factor_counts: dict[str, int] = {
            "manual_parallel_fifth": 0,
            "manual_parallel_octave": 0,
            "manual_direct_fifth": 0,
            "manual_voice_overlap": 0,
        }
        for time in range(self.lattice.size - 1):
            controllers = tuple(
                self.controllers[(position, voice)]
                for position in (time, time + 1)
                for voice in range(1, 4)
            )
            if not all(segment in assignments for segment in controllers):
                continue
            activations = self.transition_scorer.activations(
                tuple(int(value) for value in blocks[time]),
                tuple(int(value) for value in blocks[time + 1]),
                self.lattice.tonic_pc,
            )
            for factor_name in factor_counts:
                factor_counts[factor_name] += factor_name in activations
        transitions = max(self.lattice.size - 1, 1)
        metrics.update(
            {
                "parallel_fifth_rate": (
                    factor_counts["manual_parallel_fifth"] / transitions
                ),
                "parallel_octave_rate": (
                    factor_counts["manual_parallel_octave"] / transitions
                ),
                "direct_fifth_rate": (
                    factor_counts["manual_direct_fifth"] / transitions
                ),
                "voice_overlap_rate": (
                    factor_counts["manual_voice_overlap"] / transitions
                ),
                "voice_crossing_rate": 0.0,
            }
        )
        return tuple(
            {
                "metric_id": metric_id,
                "value": value,
                "threshold": self.thresholds[metric_id],
            }
            for metric_id, value in metrics.items()
            if value > self.thresholds[metric_id]
        )

    def _violated_irreversible_groups(
        self,
        exceedances: tuple[dict[str, Any], ...],
    ) -> tuple[str, ...]:
        exceeded = {str(row["metric_id"]) for row in exceedances}
        groups = tuple(
            rule_id
            for metric_ids, maximum, rule_id in self.group_budgets.values()
            if len(exceeded & metric_ids) > maximum
        )
        if len(exceeded) > self.maximum_exceeded_budgets:
            return (*groups, "EMPIRICAL-JOINT-BUDGET")
        return groups

    def _irrecoverable_step_deficits(
        self,
        assignments: dict[Segment, int],
    ) -> tuple[str, ...]:
        """Find lines that cannot reach the empirical step rate any more.

        Every still unknown adjacent transition is optimistically counted as
        a conjunct non-repeated motion.  Failing under this best case is a
        monotone fact, so it is safe to use during backtracking.
        """

        output = []
        for voice, name in enumerate(("soprano", "alto", "tenor", "bass")):
            if voice == 0:
                continue
            line = self._known_attack_line(assignments, voice)
            known_edges = tuple(
                (left, right)
                for left, right in zip(line[:-1], line[1:], strict=True)
                if left is not None and right is not None
            )
            steps = sum(0 < abs(right - left) <= 2 for left, right in known_edges)
            motions = sum(right != left for left, right in known_edges)
            remaining_edges = len(line) - 1 - len(known_edges)
            best_steps = steps + remaining_edges
            best_motions = motions + remaining_edges
            best_rate = 0.0 if best_motions == 0 else best_steps / best_motions
            maximum_deficit = self.thresholds[f"{name}_step_deficit"]
            if 1.0 - best_rate > maximum_deficit + 1e-12:
                output.append(f"{name}_step_deficit")
        return tuple(output)

    def candidate_is_allowed(self, assignments: dict[Segment, int]) -> bool:
        """Check all presently monotone manual-budget bounds."""

        if self.profile == "diagnostic":
            return True
        if self.profile == "pedagogical_strict":
            for voice in (1, 2):
                line = self._known_attack_line(assignments, voice)
                if None not in line and len(set(line)) <= 1:
                    return False
            return True
        irreversible = self._irreversible_exceedances(assignments)
        if self._violated_irreversible_groups(irreversible):
            return False
        irrecoverable_steps = frozenset(self._irrecoverable_step_deficits(assignments))
        exceeded = {str(row["metric_id"]) for row in irreversible} | set(
            irrecoverable_steps
        )
        if len(exceeded) > self.maximum_exceeded_budgets:
            return False
        metric_ids, maximum, _ = self.group_budgets["conjunct_motion"]
        return len(irrecoverable_steps & metric_ids) <= maximum

    def diagnostic(self, assignments: dict[Segment, int]) -> Any:
        key = tuple(sorted(assignments.items()))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        blocks = _apply_assignments(self.defaults, assignments)
        parsed = _parsed_score_from_blocks(self.lattice, blocks, self.source)
        diagnostic = audit_parsed_satb(parsed, profile=self.profile)
        self._cache[key] = diagnostic
        return diagnostic

    def __call__(self, session: Any) -> None:
        contradiction = Fact(Triple(PROBLEM, STATE, CONTRADICTION))
        if contradiction in session.facts:
            return
        assignments = _assignments(session)
        if self.profile == "diagnostic":
            return
        if self.profile == "pedagogical_strict":
            if len(assignments) != len(self.segments):
                return
            diagnostic = self.diagnostic(assignments)
            if not diagnostic.contradiction:
                return
            self.rejections.append(
                {
                    "cause": OFFICIAL_MANUAL_BUDGET.name,
                    "phase": "complete_snarky_strict_audit",
                    "hard_violations": list(diagnostic.hard_violations),
                }
            )
            session.assume(
                contradiction,
                Fact(Triple(PROBLEM, VIOLATED_CONSTRAINT, OFFICIAL_MANUAL_BUDGET)),
                label=f"constraint:{OFFICIAL_MANUAL_BUDGET.name}",
            )
            return
        irreversible = self._irreversible_exceedances(assignments)
        irreversible_groups = self._violated_irreversible_groups(irreversible)
        irrecoverable_steps = self._irrecoverable_step_deficits(assignments)
        conjunct_metrics, conjunct_maximum, conjunct_rule = self.group_budgets[
            "conjunct_motion"
        ]
        conjunct_impossible = (
            len(frozenset(irrecoverable_steps) & conjunct_metrics) > conjunct_maximum
        )
        jointly_impossible = (
            len(
                {str(row["metric_id"]) for row in irreversible}
                | set(irrecoverable_steps)
            )
            > self.maximum_exceeded_budgets
        )
        if irreversible_groups or conjunct_impossible or jointly_impossible:
            self.rejections.append(
                {
                    "cause": OFFICIAL_MANUAL_BUDGET.name,
                    "phase": "monotone_partial_propagation",
                    "assigned_segments": len(assignments),
                    "exceedances": list(irreversible),
                    "irrecoverable_step_deficits": list(irrecoverable_steps),
                    "hard_violations": [
                        *irreversible_groups,
                        *([conjunct_rule] if conjunct_impossible else []),
                        *(["EMPIRICAL-JOINT-BUDGET"] if jointly_impossible else []),
                    ],
                }
            )
            session.assume(
                contradiction,
                Fact(
                    Triple(
                        PROBLEM,
                        VIOLATED_CONSTRAINT,
                        OFFICIAL_MANUAL_BUDGET,
                    )
                ),
                label=f"constraint:{OFFICIAL_MANUAL_BUDGET.name}",
            )
            return
        if len(assignments) != len(self.segments):
            return
        diagnostic = self.diagnostic(assignments)
        if not diagnostic.contradiction:
            return
        self.rejections.append(
            {
                "cause": OFFICIAL_MANUAL_BUDGET.name,
                "phase": "complete_snarky_audit",
                "exceedances": list(diagnostic.empirical_budget_exceedances),
                "hard_violations": list(diagnostic.hard_violations),
            }
        )
        session.assume(
            contradiction,
            Fact(
                Triple(
                    PROBLEM,
                    VIOLATED_CONSTRAINT,
                    OFFICIAL_MANUAL_BUDGET,
                )
            ),
            label=f"constraint:{OFFICIAL_MANUAL_BUDGET.name}",
        )


def _markdown(payload: dict[str, Any]) -> str:
    search = payload["search"]
    solution = payload.get("solution")
    manual = None if solution is None else solution.get("official_manual")
    manual_passes = None if manual is None else manual["passes_profile"]
    lines = [
        "# Génération complète à soprano imposé",
        "",
        "Toutes les attaques des voix d'alto, ténor et basse sont choisies",
        "par Snarky. Le soprano, le rythme et la métrique sont imposés ;",
        "aucune hauteur intérieure de Bach n'est utilisée par la recherche.",
        "",
        f"- Blocs : `{payload['fragment']['blocks']}`.",
        f"- Segments générés : `{payload['fragment']['generated_segments']}`.",
        f"- Facteurs MLE : `{payload['model']['factor_count']}`.",
        f"- Supports de registre appris : `{payload['model']['voice_ranges']}`.",
        f"- Threshold : `{payload['model']['threshold']:.6f}`.",
        f"- Statut : `{search['status']}`.",
        f"- Nœuds : `{search['explored_nodes']}`.",
        f"- Backtracks : `{search['backtracks']}`.",
        f"- Rejets de score : `{search['score_rejections']}`.",
        f"- Rejets de contraintes : `{search['hard_constraint_rejections']}`.",
        "- Valeurs retirées par propagation des domaines : "
        f"`{(search['reified_domain_propagation'] or {}).get('domain_removals', 0)}`.",
        "- CHOICE pondérés par les facteurs K3 : "
        f"`{search['factor_weighted_choices']}`.",
        "- CHOICE pondérés par les facteurs du manuel : "
        f"`{search['manual_factor_weighted_choices']}`.",
        "- Rejets du budget empirique du manuel : "
        f"`{search['official_manual_budget_rejections']}`.",
        "- Rejets de blocs verticaux non harmonisés : "
        f"`{search['homorhythmic_chord_rejections']}`.",
    ]
    if solution:
        score = solution["score"]
        lines.extend(
            [
                (
                    "- Score généré : audit compilé différé."
                    if score is None
                    else f"- Score généré : `{score['mean']:.6f}`."
                ),
                f"- Blocs avec croisement adjacent : "
                f"`{solution['adjacent_crossed_blocks']}`.",
                (
                    "- Profil empirique du manuel : audit externe séparé."
                    if manual_passes is None
                    else f"- Profil du manuel satisfait : `{manual_passes}`."
                ),
                f"- MusicXML : `{solution['exports']['musicxml']}`.",
                f"- MIDI : `{solution['exports']['midi']}`.",
                "",
                "La partition générée couvre le choral entier. Les différences",
                "musicales restantes doivent être traitées dans la prochaine",
                "boucle d'induction, sans ajuster ce résultat après écoute.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    program = score_experiment._model_program(args.model, args.catalogue)
    sequence_factor = (
        None
        if args.sequence_model is None
        else AttackCycleSequenceFactor.load(args.sequence_model)
    )
    calibration = score_experiment.calibrate_threshold(
        args.calibration_cache,
        program,
        split="validation",
        policy="strict_minimum",
        override=None,
    )
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    if args.homorhythmic_soprano_grid:
        lattice = _homorhythmic_soprano_lattice(lattice)
    if args.require_harmonized_blocks and not args.homorhythmic_soprano_grid:
        raise ValueError(
            "--require-harmonized-blocks requires --homorhythmic-soprano-grid"
        )
    defaults = _default_blocks(lattice, program)
    segments = _search_ordered_segments(
        lattice.attacks,
        lattice.metric_levels,
        args.search_order,
    )
    harmonic_budget = (
        None
        if args.harmonic_budget_model is None
        else StrongHarmonyBudget.load(
            args.harmonic_budget_model,
            lattice=lattice,
            segments=segments,
            defaults=defaults,
            allow_rejected_ablation=args.allow_rejected_harmonic_ablation,
        )
    )
    scored_segments = tuple(
        segment for segment in segments if segment[0] > 0 and segment[1] < lattice.size
    )
    constraints = _constraint_features(args.constraint_mode)
    voice_ranges = _learned_voice_ranges(
        args.calibration_cache,
        candidate_min=program.candidate_min,
    )
    evaluator = ExactSegmentEvaluator(
        lattice=lattice,
        program=program,
        constraint_rows=constraints,
    )
    quality = FullQualityPropagator(
        segments=segments,
        scored_segments=scored_segments,
        defaults=defaults,
        evaluator=evaluator,
        threshold=calibration.threshold,
        harmonic_budget=harmonic_budget,
        # A missing conditional can contribute at most zero log-probability.
        # The partial total is therefore a sound optimistic score bound and
        # may reject a branch as soon as it falls below the complete threshold.
        defer_score_until_complete=False,
        enforce_score_floor=args.score_floor_mode == "search",
    )
    official_manual = (
        OfficialManualBudgetPropagator(
            segments=segments,
            defaults=defaults,
            lattice=lattice,
            source=args.musicxml,
            profile=args.official_manual_profile,
        )
        # The note-by-note experiment is specifically a validation of the
        # manual rule base, so its frozen Bach envelope is part of that mode.
        if args.official_manual_budgets or args.homorhythmic_soprano_grid
        else None
    )
    homorhythmic_chords = (
        HomorhythmicChordPropagator(
            segments=segments,
            defaults=defaults,
            lattice=lattice,
            allowed_qualities=HOMORHYTHMIC_CHORD_VOCABULARIES[
                args.homorhythmic_chord_vocabulary
            ],
        )
        if args.require_harmonized_blocks
        else None
    )
    reified_space = (
        ReifiedChordSpace(
            segments=segments,
            defaults=defaults,
            lattice=lattice,
            voice_ranges=voice_ranges,
            allowed_qualities=HOMORHYTHMIC_CHORD_VOCABULARIES[
                args.homorhythmic_chord_vocabulary
            ],
            manual_profile=args.official_manual_profile,
        )
        if args.homorhythmic_soprano_grid
        else None
    )
    reified_domains = (
        None if reified_space is None else ReifiedChordDomainPropagator(reified_space)
    )
    manual_transition_factors = (
        OfficialManualTransitionScorer() if reified_space is not None else None
    )
    boundary_factor = (
        BoundaryChordFactor.load(
            args.boundary_model,
            excluded_piece_id=args.piece_id,
        )
        if reified_space is not None
        else None
    )
    provider = (
        ReifiedChordChoiceProvider(
            space=reified_space,
            defaults=defaults,
            evaluator=evaluator,
            quality=quality,
            choice_order=args.search_order,
            manual_budget=official_manual,
            manual_factors=manual_transition_factors,
            boundary_factor=boundary_factor,
        )
        if reified_space is not None
        else DynamicSegmentChoiceProvider(
            segments=segments,
            defaults=defaults,
            evaluator=evaluator,
            voice_ranges=voice_ranges,
            sequence_factor=sequence_factor,
            harmonic_budget=harmonic_budget,
            quality=quality,
            forward_check=(
                args.constraint_mode == "v33_strict_strong_unlicensed"
                and not args.disable_forward_check
            ),
        )
    )
    initial = (Fact(Triple(PROBLEM, KIND, FULL_GENERATION)),)
    session = ForwardEngine(()).create_session(initial)

    def goal(current: Any) -> bool:
        return len(_assignments(current)) == len(segments)

    contradiction = Fact(Triple(PROBLEM, STATE, CONTRADICTION))
    engine = SessionChoiceSearch(
        (),
        provider,
        goal,
        lambda current: contradiction in current.facts,
        policy=MRVChoicePolicy(prefer_high_weight=True),
        traversal=ChoiceTraversal.DEPTH_FIRST,
        max_nodes=args.max_nodes,
        max_solutions=1,
        propagators=tuple(
            propagator
            for propagator in (
                reified_domains,
                quality,
                homorhythmic_chords,
                official_manual,
            )
            if propagator is not None
        ),
        reversible_depth_first=True,
    )
    result = engine.solve(session)
    payload: dict[str, Any] = {
        "experiment": {
            "id": "K3-TWO-LOOP-FULL-SNARKY-GENERATION-1",
            "status": "FULL_GENERATION",
            "gibbs_used_for_generation": False,
            "lower_voice_source_used_for_search": False,
            "test_loaded": False,
        },
        "fragment": {
            "piece_id": args.piece_id,
            "blocks": lattice.size,
            "end_offset": lattice.end_offset,
            "generated_segments": len(segments),
            "scored_segments": len(scored_segments),
            "soprano_imposed": True,
            "rhythm_imposed": True,
            "homorhythmic_soprano_grid": args.homorhythmic_soprano_grid,
            "all_voices_share_soprano_attacks": bool(
                np.all(lattice.attacks == lattice.attacks[:, :1])
            ),
            "choice_unit": (
                "propagated_reified_chord_domain"
                if args.homorhythmic_soprano_grid
                else "single_voice_segment"
            ),
        },
        "model": {
            "source": str(args.model.resolve()),
            "factor_count": len(program.features),
            "weight_estimator": "joint_conditional_mle",
            "constraint_count": len(constraints),
            "constraint_status": (
                "EMPIRICAL_PRETEST_FILTER"
                if args.constraint_mode == "v22"
                else "STRICT_GENERATIVE_ABLATION_NOT_PROMOTED"
            ),
            "constraint_mode": args.constraint_mode,
            "forward_check": provider.forward_check,
            "factor_choice_semantics": (
                "exact_incremental_conditional_pseudolikelihood"
                if reified_space is not None
                else "single_segment_conditional_energy"
            ),
            "boundary_factor": (
                None
                if boundary_factor is None
                else {
                    "source": str(boundary_factor.source),
                    "estimator": "leave_one_piece_out_smoothed_categorical",
                    "excluded_piece_id": boundary_factor.excluded_piece_id,
                    "training_records_after_exclusion": len(boundary_factor.records),
                    "state": ["quality", "root_degree", "inversion_interval"],
                    "global_unary_factors": ["register", "tonal_pitch_class"],
                }
            ),
            "search_order": args.search_order,
            "voice_ranges": {
                str(voice): list(bounds) for voice, bounds in voice_ranges.items()
            },
            "voice_range_status": "EXACT_TRAIN_SUPPORT",
            "threshold": calibration.threshold,
            "threshold_policy": calibration.policy,
            "score_floor_mode": args.score_floor_mode,
            "score_floor_enforced": args.score_floor_mode == "search",
            "sequence_factor": (
                None
                if sequence_factor is None
                else {
                    "ids": list(sequence_factor.factor_ids),
                    "source": str(sequence_factor.source),
                    "voice_log_weights": list(sequence_factor.voice_log_weights),
                    "activation": "continued_attacked_two_note_cycle",
                }
            ),
            "harmonic_budget": (
                None
                if harmonic_budget is None
                else {
                    "source": str(harmonic_budget.source),
                    "source_status": harmonic_budget.status,
                    "ablation_only": harmonic_budget.status != "CONFIRMED",
                    "quantile": harmonic_budget.quantile,
                    "maximum_dissonant_named": (harmonic_budget.maximum_dissonant),
                    "maximum_dissonant_chains": harmonic_budget.maximum_chains,
                }
            ),
            "official_manual_budgets": (
                None
                if official_manual is None
                else {
                    "profile": args.official_manual_profile,
                    "status": "FROZEN_AFTER_TEST_REPORT",
                    "activation": "complete_branch_constraint",
                }
            ),
            "vertical_harmonization": (
                None
                if homorhythmic_chords is None
                else {
                    "every_block_checked": True,
                    "allowed_named_quality_indices": sorted(
                        HOMORHYTHMIC_CHORD_VOCABULARIES[
                            args.homorhythmic_chord_vocabulary
                        ]
                    ),
                    "vocabulary": args.homorhythmic_chord_vocabulary,
                    "incomplete_major_minor_triads_allowed": True,
                    "harmonic_skeleton_imposed": False,
                }
            ),
        },
        "search": {
            "status": result.status.value,
            "explored_nodes": result.explored_nodes,
            "failed_branches": result.failed_branches,
            "backtracks": sum(
                event.kind is ChoiceEventKind.BACKTRACK for event in result.events
            ),
            "score_rejections": sum(
                row["cause"] == SCORE_FLOOR.name for row in quality.rejections
            ),
            "hard_constraint_rejections": sum(
                row["cause"] == HARD_K3.name for row in quality.rejections
            ),
            "harmonic_dissonance_budget_rejections": sum(
                row["cause"] == HARMONIC_DISSONANCE_BUDGET.name
                for row in quality.rejections
            ),
            "harmonic_chain_budget_rejections": sum(
                row["cause"] == HARMONIC_CHAIN_BUDGET.name for row in quality.rejections
            ),
            "official_manual_budget_rejections": (
                0 if official_manual is None else len(official_manual.rejections)
            ),
            "official_manual_partial_rejections": (
                0
                if official_manual is None
                else sum(
                    row.get("phase") == "monotone_partial_propagation"
                    for row in official_manual.rejections
                )
            ),
            "official_manual_complete_rejections": (
                0
                if official_manual is None
                else sum(
                    row.get("phase") == "complete_snarky_audit"
                    for row in official_manual.rejections
                )
            ),
            "official_manual_rejection_examples": (
                [] if official_manual is None else official_manual.rejections[:10]
            ),
            "homorhythmic_chord_rejections": (
                0
                if homorhythmic_chords is None
                else len(homorhythmic_chords.rejections)
            ),
            "homorhythmic_chord_rejection_examples": (
                []
                if homorhythmic_chords is None
                else homorhythmic_chords.rejections[:10]
            ),
            "provider_calls": provider.calls,
            "prefiltered_alternatives": provider.prefiltered_alternatives,
            "harmonic_budget_prefiltered": (provider.harmonic_budget_prefiltered),
            "manual_budget_prefiltered": getattr(
                provider, "manual_budget_prefiltered", 0
            ),
            "forward_check_rejections": provider.forward_check_rejections,
            "empty_domains": provider.empty_domains,
            "component_cache_entries": len(evaluator.cache),
            "hard_prefilter_cache_entries": len(evaluator.violation_cache),
            "batched_evaluation_cache_entries": len(evaluator.evaluation_cache),
            "reified_domain_propagation": (
                None
                if reified_domains is None
                else {
                    "calls": reified_domains.calls,
                    "domain_removals": reified_domains.domain_removals,
                    "singleton_assignments": reified_domains.singleton_assignments,
                    "empty_domains": reified_domains.empty_domains,
                    "minimum_live_domain": reified_domains.minimum_live_domain,
                    "static_domain_sizes": [
                        len(domain) for domain in reified_space.domains
                    ],
                    "compiled_pair_supports": len(reified_space.supports),
                }
            ),
            "batch_factor_evaluations": getattr(
                provider, "batch_factor_evaluations", 0
            ),
            "factor_weighted_choices": getattr(provider, "factor_weighted_choices", 0),
            "manual_factor_weighted_choices": getattr(
                provider, "manual_factor_weighted_choices", 0
            ),
            "boundary_factor_weighted_choices": getattr(
                provider, "boundary_factor_weighted_choices", 0
            ),
            "boundary_energy_spreads": getattr(provider, "boundary_energy_spreads", {}),
            "rejection_examples": quality.rejections[:20],
        },
    }
    if result.solutions:
        assignments = _assignments(result.solutions[0].session)
        generated = _apply_assignments(defaults, assignments)
        score = (
            quality.complete_score(assignments)
            if args.score_floor_mode == "search"
            else None
        )
        score_experiment._export_solution(
            source_path=args.score,
            lattice=lattice,
            blocks=generated,
            start=0,
            musicxml_path=args.musicxml,
            midi_path=args.midi,
        )
        payload["solution"] = {
            "blocks": generated.tolist(),
            "score": (
                None if score is None else score_experiment._score_payload(score)
            ),
            "score_audit_status": (
                "PENDING_COMPILED_OFFLINE_AUDIT"
                if score is None
                else "EVALUATED_IN_SEARCH"
            ),
            "satisfies_threshold": (
                None if score is None else score.mean >= calibration.threshold - 1e-12
            ),
            "adjacent_crossed_blocks": int(
                (
                    (generated[:, 1] < generated[:, 2])
                    | (generated[:, 2] < generated[:, 3])
                ).sum()
            ),
            "exports": {
                "musicxml": str(args.musicxml.resolve()),
                "midi": str(args.midi.resolve()),
                "exporter": "MuSES",
            },
            "harmonic_budget": (
                None
                if harmonic_budget is None
                else harmonic_budget.statistics(assignments)
            ),
            "official_manual": (
                None
                if official_manual is None
                else official_manual.diagnostic(assignments).to_dict()
            ),
        }
        payload["diagnostic"] = {"bach_used_for_search": False}
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    print(
        f"[full-score-floor] status={result.status.value} "
        f"nodes={result.explored_nodes} failed={result.failed_branches} "
        f"backtracks={payload['search']['backtracks']}",
        flush=True,
    )
    if payload.get("solution") and payload["solution"]["score"] is not None:
        print(
            f"[full-score-floor] score="
            f"{payload['solution']['score']['mean']:.6f} "
            f"threshold={calibration.threshold:.6f}",
            flush=True,
        )
    print(f"[full-score-floor] wrote {args.output}", flush=True)
    print(f"[full-score-floor] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
