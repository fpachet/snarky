"""Note-variable harmonizer driven by Snarky propagation and CHOICE."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

from csp_solver.solver import (
    CANDIDATE,
    CHOICE_WEIGHT,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    FiniteCSP,
    assignment_from_solution,
    finite_csp_rule_library,
    solve_finite_csp,
)
from snarky import (
    Atom,
    ChoiceDecision,
    ChoiceEvent,
    ChoiceSearchResult,
    ChoiceTraversal,
    ComputedPredicate,
    Fact,
    FiniteSequence,
    InferenceEvent,
    InferenceSession,
    Number,
    PredicateRegistry,
    PriorityMRVChoicePolicy,
    PriorityWeightedRandomChoicePolicy,
    RuleGroup,
    RuleProgram,
    SemiNaiveInstantiationStrategy,
    Term,
    Triple,
    parse_rule_groups,
)

from .solver import (
    PitchVoicing,
    _global_motion,
    _melodic_transition,
    _no_parallel_perfect_intervals,
    _term_voicing,
)

PROBLEM = Atom("roy_note_harmonization")
VOICE_NOTE = Atom("voice_note")
HARMONIC_POSITION = Atom("harmonic_position")
POSITION = Atom("position")
VOICE = Atom("voice")
PREDECESSOR = Atom("predecessor")
CONDITIONAL_WEIGHT = Atom("conditional_weight")
SUCCESSOR = Atom("successor")
SOURCE_VARIABLE = Atom("harmonizer_variable")
CHORD_NOTE = Atom("chord_note")
CHORD_VARIABLE = Atom("chord_variable")
INVERSION_VARIABLE = Atom("inversion_variable")
HARMONIC_CHORD = Atom("harmonic_chord")
HARMONIC_INVERSION = Atom("harmonic_inversion")
VOICE_PITCH = Atom("voice_pitch")
INVERSION_BASS_PITCH = Atom("inversion_bass_pitch")
ALLOWS_INVERSION = Atom("allows_inversion")
ALLOWS_SUCCESSOR = Atom("allows_successor")
VOICING_CANDIDATE = Atom("voicing_candidate")
PHRASE_ROLE = Atom("phrase_role")
INITIAL = Atom("initial")
PRECADENTIAL = Atom("precadential")
PENULTIMATE = Atom("penultimate")
FINAL = Atom("final")
RESTRICT_CHORD = Atom("restrict_chord")
ALLOWED_FORM_CHORD = Atom("allowed_form_chord")
RESTRICT_INVERSION = Atom("restrict_inversion")
ALLOWED_FORM_INVERSION = Atom("allowed_form_inversion")
ROOT_INVERSION = Atom("root")
FIRST_INVERSION = Atom("first")
SECOND_INVERSION = Atom("second")

VOICE_NAMES = (
    Atom("soprano"),
    Atom("alto"),
    Atom("tenor"),
    Atom("bass"),
)
VOICE_VARIABLE_RELATIONS = tuple(
    Atom(f"{voice.name}_variable") for voice in VOICE_NAMES
)
DEGREE_I = Atom("degree_I")
DEGREE_II = Atom("degree_ii")
DEGREE_IV = Atom("degree_IV")
DEGREE_V = Atom("degree_V")
DEGREE_V7 = Atom("degree_V7")
DEGREE_VI = Atom("degree_vi")
DEGREE_VII = Atom("degree_vii")
CHORDS = (
    DEGREE_I,
    DEGREE_II,
    DEGREE_IV,
    DEGREE_V,
    DEGREE_V7,
    DEGREE_VI,
    DEGREE_VII,
)
CHORD_PITCH_CLASSES: dict[Atom, tuple[int, ...]] = {
    DEGREE_I: (0, 4, 7),
    DEGREE_II: (2, 5, 9),
    DEGREE_IV: (5, 9, 0),
    DEGREE_V: (7, 11, 2),
    DEGREE_V7: (7, 11, 2, 5),
    DEGREE_VI: (9, 0, 4),
    DEGREE_VII: (11, 2, 5),
}
CHORD_TRANSITIONS: dict[Atom, tuple[Atom, ...]] = {
    DEGREE_I: (
        DEGREE_I,
        DEGREE_II,
        DEGREE_IV,
        DEGREE_V,
        DEGREE_V7,
        DEGREE_VI,
        DEGREE_VII,
    ),
    DEGREE_II: (DEGREE_II, DEGREE_V, DEGREE_V7),
    DEGREE_IV: (DEGREE_IV, DEGREE_I, DEGREE_II, DEGREE_V, DEGREE_V7),
    DEGREE_V: (DEGREE_V, DEGREE_V7, DEGREE_I, DEGREE_VI),
    DEGREE_V7: (DEGREE_V7, DEGREE_I, DEGREE_VI),
    DEGREE_VI: (DEGREE_VI, DEGREE_II, DEGREE_IV),
    DEGREE_VII: (DEGREE_VII, DEGREE_I),
}
CHORD_INVERSIONS: dict[Atom, tuple[Atom, ...]] = {
    DEGREE_I: (ROOT_INVERSION, FIRST_INVERSION, SECOND_INVERSION),
    DEGREE_II: (ROOT_INVERSION, FIRST_INVERSION),
    DEGREE_IV: (ROOT_INVERSION, FIRST_INVERSION),
    DEGREE_V: (ROOT_INVERSION, FIRST_INVERSION),
    DEGREE_V7: (ROOT_INVERSION,),
    DEGREE_VI: (ROOT_INVERSION, FIRST_INVERSION),
    DEGREE_VII: (FIRST_INVERSION,),
}
DIATONIC_PITCH_CLASSES = frozenset((0, 2, 4, 5, 7, 9, 11))
DIATONIC_VOICE_POOLS = (
    tuple(pitch for pitch in range(60, 77) if pitch % 12 in DIATONIC_PITCH_CLASSES),
    tuple(pitch for pitch in range(55, 70) if pitch % 12 in DIATONIC_PITCH_CLASSES),
    tuple(pitch for pitch in range(48, 65) if pitch % 12 in DIATONIC_PITCH_CLASSES),
    tuple(pitch for pitch in range(36, 53) if pitch % 12 in DIATONIC_PITCH_CLASSES),
)
INVERSION_NAMES = (ROOT_INVERSION, FIRST_INVERSION, SECOND_INVERSION)
type SATBVoice = Literal["soprano", "alto", "tenor", "bass"]
type Cadence = Literal["perfect", "plagal", "deceptive", "half"]


@dataclass(frozen=True, slots=True)
class NoteHarmonizerModel:
    """The two-phase note/voicing model and its stable variable layout."""

    csp: FiniteCSP
    program: RuleProgram
    positions: tuple[Atom, ...]
    variables: tuple[tuple[Atom, Atom, Atom, Atom], ...]
    harmonic_variables: tuple[tuple[Atom, Atom], ...]
    choice_priorities: dict[Term, int]
    generated_voicings: tuple[int, ...]
    given_voice: SATBVoice
    cadence: Cadence
    harmonic_rhythm: tuple[int, ...]
    preparation_events: tuple[InferenceEvent, ...]


@dataclass(frozen=True, slots=True)
class NoteHarmonization:
    """One result with search and rule-level explanatory traces."""

    voicings: tuple[PitchVoicing, ...]
    chords: tuple[str, ...]
    inversions: tuple[str, ...]
    cadence: Cadence
    harmonic_rhythm: tuple[int, ...]
    log_weight: float
    decisions: tuple[ChoiceDecision, ...]
    choice_events: tuple[ChoiceEvent, ...]
    inference_events: tuple[InferenceEvent, ...]


def build_note_harmonizer_model(
    melody: tuple[int, ...] = (71, 72),
    *,
    given_voice: SATBVoice = "soprano",
    cadence: Cadence = "perfect",
    harmonic_rhythm: tuple[int, ...] | None = None,
    source_facts: tuple[Fact, ...] = (),
    source_notes: tuple[Atom, ...] = (),
) -> NoteHarmonizerModel:
    """Build a tonal SATB CSP, then generate supported chord voicings."""

    if len(melody) < 2:
        raise ValueError("the note harmonizer needs at least two positions")
    given_voice_index = _voice_index(given_voice)
    if any(pitch not in DIATONIC_VOICE_POOLS[given_voice_index] for pitch in melody):
        raise ValueError(
            f"the given line contains a non-diatonic pitch or one outside "
            f"the {given_voice} range"
        )
    if source_notes and not source_facts:
        raise ValueError("source note identities require their encoded facts")
    if source_notes and len(source_notes) != len(melody):
        raise ValueError("source notes must match the given line length")
    if len(set(source_notes)) != len(source_notes):
        raise ValueError("source note identities must be unique")
    imported_line = bool(source_notes)
    rhythm = _normalized_harmonic_rhythm(len(melody), harmonic_rhythm)
    harmonic_positions = tuple(rhythm.index(slot) for slot in range(max(rhythm) + 1))

    positions = tuple(Atom(f"note_position_{index}") for index in range(len(melody)))
    variables = tuple(
        (
            Atom(f"note_{index}_soprano"),
            Atom(f"note_{index}_alto"),
            Atom(f"note_{index}_tenor"),
            Atom(f"note_{index}_bass"),
        )
        for index in range(len(melody))
    )
    slot_harmonic_variables = tuple(
        (
            Atom(f"harmony_{slot}_chord"),
            Atom(f"harmony_{slot}_inversion"),
        )
        for slot in range(len(harmonic_positions))
    )
    harmonic_variables = tuple(
        slot_harmonic_variables[slot] for slot in rhythm
    )
    facts: list[Fact] = [
        Fact(Triple(PROBLEM, KIND, CSP_PROBLEM)),
        *source_facts,
        *_harmonic_vocabulary_facts(),
    ]
    weights: dict[tuple[Term, Term], float] = {}
    choice_priorities: dict[Term, int] = {}

    for slot, (
        first_position,
        harmonic_pair,
    ) in enumerate(
        zip(
            harmonic_positions,
            slot_harmonic_variables,
            strict=True,
        )
    ):
        position = positions[first_position]
        chord_variable, inversion_variable = harmonic_pair
        facts.extend(
            (
                Fact(Triple(PROBLEM, VARIABLE, chord_variable)),
                Fact(Triple(chord_variable, KIND, CSP_VARIABLE)),
                Fact(Triple(chord_variable, KIND, HARMONIC_CHORD)),
                Fact(Triple(chord_variable, POSITION, position)),
                Fact(Triple(PROBLEM, VARIABLE, inversion_variable)),
                Fact(Triple(inversion_variable, KIND, CSP_VARIABLE)),
                Fact(Triple(inversion_variable, KIND, HARMONIC_INVERSION)),
                Fact(Triple(inversion_variable, POSITION, position)),
            )
        )
        choice_priorities[chord_variable] = first_position * 6
        choice_priorities[inversion_variable] = first_position * 6 + 1

        chord_weights = _static_chord_weights(first_position)
        for chord in CHORDS:
            weight = chord_weights[chord]
            facts.extend(
                (
                    Fact(Triple(chord_variable, CANDIDATE, chord)),
                    Fact(
                        Triple(
                            chord_variable,
                            CHOICE_WEIGHT,
                            FiniteSequence((chord, Number(weight))),
                        )
                    ),
                )
            )
            weights[(chord_variable, chord)] = weight

        inversion_weights = {
            ROOT_INVERSION: 0.72,
            FIRST_INVERSION: 0.23,
            SECOND_INVERSION: 0.05,
        }
        for inversion in INVERSION_NAMES:
            weight = inversion_weights[inversion]
            facts.extend(
                (
                    Fact(Triple(inversion_variable, CANDIDATE, inversion)),
                    Fact(
                        Triple(
                            inversion_variable,
                            CHOICE_WEIGHT,
                            FiniteSequence((inversion, Number(weight))),
                        )
                    ),
                )
            )
            weights[(inversion_variable, inversion)] = weight

        if slot == 0:
            continue
        previous_chord = slot_harmonic_variables[slot - 1][0]
        facts.append(Fact(Triple(chord_variable, PREDECESSOR, previous_chord)))
        for previous in CHORDS:
            conditional = _chord_transition_weights(previous)
            facts.extend(
                Fact(
                    Triple(
                        chord_variable,
                        CONDITIONAL_WEIGHT,
                        FiniteSequence(
                            (
                                previous,
                                chord,
                                Number(conditional[chord]),
                            )
                        ),
                    )
                )
                for chord in CHORDS
            )

    for index, (position, position_variables, harmonic_pair) in enumerate(
        zip(positions, variables, harmonic_variables, strict=True)
    ):
        chord_variable, inversion_variable = harmonic_pair
        facts.extend(
            (
                Fact(Triple(position, KIND, HARMONIC_POSITION)),
                Fact(Triple(position, CHORD_VARIABLE, chord_variable)),
                Fact(Triple(position, INVERSION_VARIABLE, inversion_variable)),
            )
        )

        for voice_index, (voice, relation, variable) in enumerate(
            zip(
                VOICE_NAMES,
                VOICE_VARIABLE_RELATIONS,
                position_variables,
                strict=True,
            )
        ):
            candidates = (
                (melody[index],)
                if voice_index == given_voice_index
                else DIATONIC_VOICE_POOLS[voice_index]
            )
            choice_priorities[variable] = index * 6 + voice_index + 2
            facts.extend(
                (
                    Fact(Triple(PROBLEM, VARIABLE, variable)),
                    Fact(Triple(variable, KIND, CSP_VARIABLE)),
                    Fact(Triple(variable, KIND, VOICE_NOTE)),
                    Fact(Triple(variable, POSITION, position)),
                    Fact(Triple(variable, VOICE, voice)),
                    Fact(Triple(position, relation, variable)),
                )
            )
            static_weights = _static_marginal(
                index,
                voice_index,
                candidates,
            )
            for pitch in candidates:
                pitch_term = Number(pitch)
                weight = static_weights[pitch]
                if not (imported_line and voice_index == given_voice_index):
                    facts.append(Fact(Triple(variable, CANDIDATE, pitch_term)))
                facts.append(
                    Fact(
                        Triple(
                            variable,
                            CHOICE_WEIGHT,
                            FiniteSequence((pitch_term, Number(weight))),
                        )
                    )
                )
                weights[(variable, pitch_term)] = weight

            if imported_line and voice_index == given_voice_index:
                facts.append(
                    Fact(
                        Triple(
                            source_notes[index],
                            SOURCE_VARIABLE,
                            variable,
                        )
                    )
                )

            if index == 0:
                continue
            previous = variables[index - 1][voice_index]
            previous_candidates = (
                (melody[index - 1],)
                if voice_index == given_voice_index
                else DIATONIC_VOICE_POOLS[voice_index]
            )
            facts.append(Fact(Triple(variable, PREDECESSOR, previous)))
            for previous_pitch in previous_candidates:
                note_conditional = _conditional_marginal(
                    previous_pitch,
                    candidates,
                )
                facts.extend(
                    Fact(
                        Triple(
                            variable,
                            CONDITIONAL_WEIGHT,
                            FiniteSequence(
                                (
                                    Number(previous_pitch),
                                    Number(pitch),
                                    Number(note_conditional[pitch]),
                                )
                            ),
                        )
                    )
                    for pitch in candidates
                )

    _add_form_facts(
        facts,
        positions,
        harmonic_positions,
        cadence,
    )
    facts.extend(
        Fact(Triple(left, SUCCESSOR, right))
        for left, right in zip(
            positions[:-1],
            positions[1:],
            strict=True,
        )
    )

    program = _note_harmonizer_program(import_muses=imported_line)
    generated_facts, preparation_events = _prepare_model_facts(
        tuple(facts),
        program,
    )
    generated_counts = tuple(
        sum(
            1
            for fact in generated_facts
            if isinstance(fact.entity, Triple)
            and fact.entity.subject == position
            and fact.entity.relation == VOICING_CANDIDATE
        )
        for position in positions
    )
    if 0 in generated_counts:
        empty_position = generated_counts.index(0)
        raise ValueError(
            f"no legal tonal SATB voicing at position {empty_position} "
            f"for {given_voice} pitch {melody[empty_position]}"
        )
    return NoteHarmonizerModel(
        FiniteCSP(
            PROBLEM,
            generated_facts,
            weights,
            _note_harmonizer_groups(),
        ),
        program,
        positions,
        variables,
        harmonic_variables,
        choice_priorities,
        generated_counts,
        given_voice,
        cadence,
        rhythm,
        preparation_events,
    )


def _normalized_harmonic_rhythm(
    note_count: int,
    harmonic_rhythm: tuple[int, ...] | None,
) -> tuple[int, ...]:
    rhythm = tuple(range(note_count)) if harmonic_rhythm is None else harmonic_rhythm
    if len(rhythm) != note_count:
        raise ValueError("harmonic_rhythm must contain one slot number per note")
    if not rhythm or rhythm[0] != 0:
        raise ValueError("harmonic_rhythm must start at slot 0")
    if any(
        not isinstance(slot, int) or isinstance(slot, bool) or slot < 0
        for slot in rhythm
    ):
        raise ValueError("harmonic_rhythm slots must be non-negative integers")
    if any(
        right not in (left, left + 1)
        for left, right in zip(rhythm, rhythm[1:], strict=False)
    ):
        raise ValueError("harmonic_rhythm slots must be contiguous and non-decreasing")
    if rhythm[-1] < 1:
        raise ValueError("the harmonizer needs at least two harmonic slots")
    return rhythm


def _add_form_facts(
    facts: list[Fact],
    positions: tuple[Atom, ...],
    harmonic_positions: tuple[int, ...],
    cadence: Cadence,
) -> None:
    try:
        penultimate_chords, final_chords = {
            "perfect": ((DEGREE_V, DEGREE_V7), (DEGREE_I,)),
            "plagal": ((DEGREE_IV,), (DEGREE_I,)),
            "deceptive": ((DEGREE_V, DEGREE_V7), (DEGREE_VI,)),
            "half": ((), (DEGREE_V, DEGREE_V7)),
        }[cadence]
    except KeyError as error:
        raise ValueError(
            "cadence must be perfect, plagal, deceptive, or half"
        ) from error

    def restrict_chord(position: Atom, allowed: tuple[Atom, ...]) -> None:
        facts.append(Fact(Triple(position, RESTRICT_CHORD, Atom("true"))))
        facts.extend(
            Fact(Triple(position, ALLOWED_FORM_CHORD, chord)) for chord in allowed
        )

    def restrict_inversion(position: Atom, allowed: tuple[Atom, ...]) -> None:
        facts.append(Fact(Triple(position, RESTRICT_INVERSION, Atom("true"))))
        facts.extend(
            Fact(Triple(position, ALLOWED_FORM_INVERSION, inversion))
            for inversion in allowed
        )

    representative_positions = tuple(
        positions[index] for index in harmonic_positions
    )
    if len(representative_positions) >= 3:
        initial = representative_positions[0]
        facts.append(Fact(Triple(initial, PHRASE_ROLE, INITIAL)))
        restrict_chord(initial, (DEGREE_I,))
        restrict_inversion(initial, (ROOT_INVERSION,))

    if penultimate_chords:
        penultimate = representative_positions[-2]
        facts.append(Fact(Triple(penultimate, PHRASE_ROLE, PENULTIMATE)))
        restrict_chord(penultimate, penultimate_chords)
        restrict_inversion(penultimate, (ROOT_INVERSION,))

    final = representative_positions[-1]
    facts.append(Fact(Triple(final, PHRASE_ROLE, FINAL)))
    restrict_chord(final, final_chords)
    restrict_inversion(final, (ROOT_INVERSION,))

    if cadence == "perfect" and len(representative_positions) >= 4:
        precadential_start = harmonic_positions[-3]
        precadential_end = harmonic_positions[-2]
        facts.extend(
            Fact(Triple(position, PHRASE_ROLE, PRECADENTIAL))
            for position in positions[precadential_start:precadential_end]
        )


def harmonize_notes(
    melody: tuple[int, ...] = (71, 72),
    *,
    given_voice: SATBVoice = "soprano",
    cadence: Cadence = "perfect",
    harmonic_rhythm: tuple[int, ...] | None = None,
    max_solutions: int = 3,
    seed: int = 0,
) -> tuple[NoteHarmonization, ...]:
    """Return best-first harmonizations chosen one note variable at a time."""

    model = build_note_harmonizer_model(
        melody,
        given_voice=given_voice,
        cadence=cadence,
        harmonic_rhythm=harmonic_rhythm,
    )
    result = solve_note_harmonizer(
        model,
        max_solutions=max_solutions,
        seed=seed,
    )
    return tuple(
        _note_harmonization(model, result, index)
        for index in range(len(result.solutions))
    )


def sample_harmonization(
    melody: tuple[int, ...] = (71, 72),
    *,
    given_voice: SATBVoice = "soprano",
    cadence: Cadence = "perfect",
    harmonic_rhythm: tuple[int, ...] | None = None,
    seed: int = 0,
) -> NoteHarmonization:
    """Sample one feasible harmonization from contextual note marginals."""

    model = build_note_harmonizer_model(
        melody,
        given_voice=given_voice,
        cadence=cadence,
        harmonic_rhythm=harmonic_rhythm,
    )
    result = solve_note_harmonizer(
        model,
        max_solutions=1,
        traversal=ChoiceTraversal.DEPTH_FIRST,
        weighted_random=True,
        seed=seed,
    )
    if not result.solutions:
        raise ValueError("the melody has no feasible harmonization")
    return _note_harmonization(model, result, 0)


def solve_note_harmonizer(
    model: NoteHarmonizerModel,
    *,
    max_solutions: int = 3,
    traversal: ChoiceTraversal = ChoiceTraversal.BEST_FIRST,
    weighted_random: bool = False,
    seed: int = 0,
) -> ChoiceSearchResult:
    """Expose the generic search result for benchmarks and diagnostics."""

    policy = (
        PriorityWeightedRandomChoicePolicy(model.choice_priorities)
        if weighted_random
        else PriorityMRVChoicePolicy(model.choice_priorities)
    )
    return solve_finite_csp(
        model.csp,
        max_solutions=max_solutions,
        traversal=traversal,
        policy=policy,
        seed=seed,
        rule_groups=model.program.search_groups,
    )


def _note_harmonization(
    model: NoteHarmonizerModel,
    result: ChoiceSearchResult,
    solution_index: int,
) -> NoteHarmonization:
    solution = result.solutions[solution_index]
    assignment = assignment_from_solution(solution, PROBLEM)
    voicings: list[PitchVoicing] = []
    for position_variables in model.variables:
        pitches = tuple(_integer_value(assignment[item]) for item in position_variables)
        voicings.append((pitches[0], pitches[1], pitches[2], pitches[3]))
    chords = tuple(
        _atom_name(assignment[chord]) for chord, _ in model.harmonic_variables
    )
    inversions = tuple(
        _atom_name(assignment[inversion]) for _, inversion in model.harmonic_variables
    )
    return NoteHarmonization(
        tuple(voicings),
        chords,
        inversions,
        model.cadence,
        model.harmonic_rhythm,
        solution.log_weight,
        solution.decisions,
        result.events,
        (*model.preparation_events, *solution.session.events),
    )


def _integer_value(term: Term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise TypeError("expected an integer note value")
    return term.value


def _atom_name(term: Term) -> str:
    if not isinstance(term, Atom):
        raise TypeError("expected an atom value")
    return term.name


def _static_marginal(
    position: int,
    voice: int,
    pitches: tuple[int, ...],
) -> dict[int, float]:
    if len(pitches) == 1:
        return {pitches[0]: 1.0}
    centers = (
        (67, 69, 72),
        (60, 62, 64),
        (55, 57, 59),
        (43, 45, 48),
    )
    raw = {
        pitch: math.exp(-abs(pitch - centers[voice][position % 3]) / 4)
        for pitch in pitches
    }
    total = sum(raw.values())
    return {pitch: value / total for pitch, value in raw.items()}


def _conditional_marginal(
    previous_pitch: int,
    pitches: tuple[int, ...],
) -> dict[int, float]:
    raw = {pitch: math.exp(-abs(pitch - previous_pitch) / 3) for pitch in pitches}
    total = sum(raw.values())
    return {pitch: value / total for pitch, value in raw.items()}


def _static_chord_weights(position: int) -> dict[Atom, float]:
    del position
    raw = {
        DEGREE_I: 0.20,
        DEGREE_II: 0.05,
        DEGREE_IV: 0.31,
        DEGREE_V: 0.20,
        DEGREE_V7: 0.06,
        DEGREE_VI: 0.14,
        DEGREE_VII: 0.04,
    }
    total = sum(raw.values())
    return {chord: value / total for chord, value in raw.items()}


def _chord_transition_weights(previous: Atom) -> dict[Atom, float]:
    preferred = {
        DEGREE_I: {
            DEGREE_I: 0.08,
            DEGREE_II: 0.05,
            DEGREE_IV: 0.35,
            DEGREE_V: 0.20,
            DEGREE_V7: 0.08,
            DEGREE_VI: 0.17,
            DEGREE_VII: 0.07,
        },
        DEGREE_II: {
            DEGREE_II: 0.05,
            DEGREE_V: 0.65,
            DEGREE_V7: 0.30,
        },
        DEGREE_IV: {
            DEGREE_IV: 0.08,
            DEGREE_I: 0.12,
            DEGREE_II: 0.10,
            DEGREE_V: 0.48,
            DEGREE_V7: 0.22,
        },
        DEGREE_V: {
            DEGREE_V: 0.05,
            DEGREE_V7: 0.10,
            DEGREE_I: 0.75,
            DEGREE_VI: 0.10,
        },
        DEGREE_V7: {
            DEGREE_V7: 0.05,
            DEGREE_I: 0.85,
            DEGREE_VI: 0.10,
        },
        DEGREE_VI: {
            DEGREE_VI: 0.08,
            DEGREE_II: 0.37,
            DEGREE_IV: 0.55,
        },
        DEGREE_VII: {
            DEGREE_VII: 0.05,
            DEGREE_I: 0.95,
        },
    }[previous]
    return {chord: preferred.get(chord, 0.001) for chord in CHORDS}


def _harmonic_vocabulary_facts() -> tuple[Fact, ...]:
    facts: list[Fact] = []
    for chord, pitch_classes in CHORD_PITCH_CLASSES.items():
        facts.append(
            Fact(Triple(chord, KIND, HARMONIC_CHORD))
        )
        facts.extend(
            Fact(Triple(chord, ALLOWS_INVERSION, inversion))
            for inversion in CHORD_INVERSIONS[chord]
        )
        for voice, pool in zip(
            VOICE_NAMES,
            DIATONIC_VOICE_POOLS,
            strict=True,
        ):
            facts.extend(
                Fact(
                    Triple(
                        chord,
                        VOICE_PITCH,
                        FiniteSequence((voice, Number(pitch))),
                    )
                )
                for pitch in pool
                if pitch % 12 in pitch_classes
            )
        bass_pool = DIATONIC_VOICE_POOLS[3]
        inversion_indexes = {
            ROOT_INVERSION: 0,
            FIRST_INVERSION: 1,
            SECOND_INVERSION: 2,
        }
        for inversion in CHORD_INVERSIONS[chord]:
            bass_pitch_class = pitch_classes[inversion_indexes[inversion]]
            facts.extend(
                Fact(
                    Triple(
                        chord,
                        INVERSION_BASS_PITCH,
                        FiniteSequence((inversion, Number(pitch))),
                    )
                )
                for pitch in bass_pool
                if pitch % 12 == bass_pitch_class
            )
    for source, targets in CHORD_TRANSITIONS.items():
        facts.extend(
            Fact(Triple(source, ALLOWS_SUCCESSOR, target)) for target in targets
        )
    return tuple(facts)


def _prepare_model_facts(
    facts: tuple[Fact, ...],
    program: RuleProgram,
) -> tuple[tuple[Fact, ...], tuple[InferenceEvent, ...]]:
    session = InferenceSession(
        facts,
        strategy=SemiNaiveInstantiationStrategy(),
    )
    for group in program.preparation_groups:
        session.run_group(group)
    return session.facts, session.events


def _complete_chord(arguments: tuple[Term, ...]) -> bool:
    if len(arguments) != 5 or not isinstance(arguments[0], Atom):
        raise ValueError("complete_chord expects a chord and four notes")
    chord = arguments[0]
    try:
        required = set(CHORD_PITCH_CLASSES[chord])
    except KeyError as error:
        raise ValueError(f"unknown tonal chord {chord.name}") from error
    pitches = tuple(_integer_value(argument) for argument in arguments[1:])
    return {pitch % 12 for pitch in pitches} == required


def _legal_doubling(arguments: tuple[Term, ...]) -> bool:
    if (
        len(arguments) != 6
        or not isinstance(arguments[0], Atom)
        or not isinstance(arguments[1], Atom)
    ):
        raise ValueError(
            "legal_doubling expects chord, inversion, and four notes"
        )
    chord = arguments[0]
    inversion = arguments[1]
    pitches = tuple(_integer_value(argument) for argument in arguments[2:])
    pitch_classes = tuple(pitch % 12 for pitch in pitches)
    counts = {
        pitch_class: pitch_classes.count(pitch_class)
        for pitch_class in set(pitch_classes)
    }

    # R-DOUBLING-002 and R-EXT-7CHORD-003.
    if counts.get(11, 0) > 1:
        return False
    if chord == DEGREE_V7:
        return all(count == 1 for count in counts.values())

    # R-DOUBLING-004/005: the third of root-position I/IV is exceptional
    # only when soprano and alto carry it together.
    if chord in (DEGREE_I, DEGREE_IV) and inversion == ROOT_INVERSION:
        third = CHORD_PITCH_CLASSES[chord][1]
        if counts.get(third, 0) > 1 and pitch_classes[:2] != (third, third):
            return False

    # R-DOUBLING-006/007.
    if inversion == FIRST_INVERSION:
        if pitch_classes[1] == pitch_classes[3]:
            return False
        if (
            chord in (DEGREE_I, DEGREE_IV, DEGREE_VI, DEGREE_VII)
            and counts[pitch_classes[3]] != 1
        ):
            return False

    # The delivered six-four is cadential: double its dominant bass.
    if inversion == SECOND_INVERSION:
        return chord == DEGREE_I and counts[pitch_classes[3]] == 2

    # For vii° in first inversion, R-DOUBLING-002 and R-DOUBLING-007 leave
    # only the fifth available for doubling in the four-part triad.
    return True


def _voicing_predicate(
    predicate: object,
    arguments: tuple[Term, ...],
) -> bool:
    if len(arguments) != 2:
        raise ValueError("transition predicates expect two voicings")
    source = _term_voicing(arguments[0])
    target = _term_voicing(arguments[1])
    if predicate is _melodic_transition:
        return _melodic_transition(source, target)
    if predicate is _no_parallel_perfect_intervals:
        return _no_parallel_perfect_intervals(source, target)
    if predicate is _global_motion:
        return _global_motion(source, target)
    raise AssertionError("unknown transition predicate")


def _melodic_transition_predicate(arguments: tuple[Term, ...]) -> bool:
    return _voicing_predicate(_melodic_transition, arguments)


def _parallel_transition_predicate(arguments: tuple[Term, ...]) -> bool:
    return _voicing_predicate(_no_parallel_perfect_intervals, arguments)


def _global_motion_predicate(arguments: tuple[Term, ...]) -> bool:
    return _voicing_predicate(_global_motion, arguments)


def _resolves_tendency_tones(arguments: tuple[Term, ...]) -> bool:
    if (
        len(arguments) != 6
        or not isinstance(arguments[0], Atom)
        or not isinstance(arguments[1], Atom)
        or not isinstance(arguments[2], Atom)
        or not isinstance(arguments[3], Atom)
    ):
        raise ValueError(
            "resolves_tendency_tones expects two chords, two inversions, "
            "and two voicings"
        )
    source_chord, source_inversion, target_chord, target_inversion = arguments[:4]
    source = _term_voicing(arguments[4])
    target = _term_voicing(arguments[5])

    if source_chord == DEGREE_I and source_inversion == SECOND_INVERSION:
        if target_chord not in (DEGREE_V, DEGREE_V7):
            return False
        if target_inversion != ROOT_INVERSION or source[3] != target[3]:
            return False
        for source_pitch, target_pitch in zip(source[:3], target[:3], strict=True):
            if source_pitch % 12 == 0 and target_pitch != source_pitch - 1:
                return False
            if source_pitch % 12 == 4 and target_pitch != source_pitch - 2:
                return False

    if source_chord in (DEGREE_V, DEGREE_V7, DEGREE_VII):
        for voice, (source_pitch, target_pitch) in enumerate(
            zip(source, target, strict=True)
        ):
            if source_pitch % 12 == 11:
                deceptive_inner_voice_exception = (
                    target_chord == DEGREE_VI
                    and voice in (1, 2)
                    and target[voice - 1] % 12 == 0
                )
                if (
                    not deceptive_inner_voice_exception
                    and target_pitch != source_pitch + 1
                ):
                    return False
            if (
                source_chord in (DEGREE_V7, DEGREE_VII)
                and source_pitch % 12 == 5
                and target_pitch != source_pitch - 1
            ):
                return False
    return True


def _voice_index(voice: SATBVoice) -> int:
    try:
        return tuple(item.name for item in VOICE_NAMES).index(voice)
    except ValueError as error:
        raise ValueError("given_voice must be soprano, alto, tenor, or bass") from error


@cache
def _note_generation_groups() -> tuple[RuleGroup, ...]:
    registry = PredicateRegistry(
        (
            ComputedPredicate(
                "complete_chord",
                _complete_chord,
            ),
            ComputedPredicate(
                "legal_doubling",
                _legal_doubling,
            ),
        )
    )
    path = Path(__file__).with_name("note_generation.rules")
    return parse_rule_groups(path.read_text(), predicates=registry)


@cache
def _muses_input_groups() -> tuple[RuleGroup, ...]:
    path = Path(__file__).with_name("muses_input.rules")
    return parse_rule_groups(path.read_text())


@cache
def _note_harmonizer_program(*, import_muses: bool) -> RuleProgram:
    csp = finite_csp_rule_library()
    musical = {group.name: group for group in _note_harmonizer_groups()}
    preparation = (
        (*_muses_input_groups(), *_note_generation_groups())
        if import_muses
        else _note_generation_groups()
    )
    return RuleProgram(
        name="muses_note_harmonizer" if import_muses else "note_harmonizer",
        preparation_groups=preparation,
        choice_groups=(csp.choices,),
        propagation_groups=(
            csp.domains,
            musical["enforce_tonal_form"],
            musical["maintain_note_voicing_channel"],
            musical["update_contextual_note_weights"],
            musical["propagate_note_harmonic_transitions"],
            csp.problems,
        ),
        interpretation_groups=(musical["interpret_note_harmonization"],),
    )


@cache
def _note_harmonizer_groups() -> tuple[RuleGroup, ...]:
    transition_registry = PredicateRegistry(
        (
            ComputedPredicate(
                "melodic_transition",
                _melodic_transition_predicate,
            ),
            ComputedPredicate(
                "no_parallel_perfects",
                _parallel_transition_predicate,
            ),
            ComputedPredicate(
                "legal_global_motion",
                _global_motion_predicate,
            ),
            ComputedPredicate(
                "resolves_tendency_tones",
                _resolves_tendency_tones,
            ),
        )
    )
    propagation = Path(__file__).with_name("note_propagation.rules")
    form = Path(__file__).with_name("harmonic_form.rules")
    transitions = Path(__file__).with_name("note_transition.rules")
    return (
        *parse_rule_groups(form.read_text()),
        *parse_rule_groups(propagation.read_text()),
        *parse_rule_groups(
            transitions.read_text(),
            predicates=transition_registry,
        ),
    )
