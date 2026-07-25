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
PENULTIMATE = Atom("penultimate")
FINAL = Atom("final")
ROOT_INVERSION = Atom("root")
FIRST_INVERSION = Atom("first")

VOICE_NAMES = (
    Atom("soprano"),
    Atom("alto"),
    Atom("tenor"),
    Atom("bass"),
)
VOICE_VARIABLE_RELATIONS = tuple(
    Atom(f"{voice.name}_variable") for voice in VOICE_NAMES
)
CHORDS = (
    Atom("degree_I"),
    Atom("degree_ii"),
    Atom("degree_IV"),
    Atom("degree_V"),
    Atom("degree_vi"),
)
CHORD_PITCH_CLASSES: dict[Atom, tuple[int, int, int]] = {
    CHORDS[0]: (0, 4, 7),
    CHORDS[1]: (2, 5, 9),
    CHORDS[2]: (5, 9, 0),
    CHORDS[3]: (7, 11, 2),
    CHORDS[4]: (9, 0, 4),
}
CHORD_TRANSITIONS: dict[Atom, tuple[Atom, ...]] = {
    CHORDS[0]: (CHORDS[0], CHORDS[2], CHORDS[3], CHORDS[4]),
    CHORDS[1]: (CHORDS[3],),
    CHORDS[2]: (CHORDS[0], CHORDS[1], CHORDS[3]),
    CHORDS[3]: (CHORDS[0], CHORDS[4]),
    CHORDS[4]: (CHORDS[1], CHORDS[2]),
}
DIATONIC_PITCH_CLASSES = frozenset((0, 2, 4, 5, 7, 9, 11))
DIATONIC_VOICE_POOLS = (
    tuple(pitch for pitch in range(60, 77) if pitch % 12 in DIATONIC_PITCH_CLASSES),
    tuple(pitch for pitch in range(55, 70) if pitch % 12 in DIATONIC_PITCH_CLASSES),
    tuple(pitch for pitch in range(48, 65) if pitch % 12 in DIATONIC_PITCH_CLASSES),
    tuple(pitch for pitch in range(36, 53) if pitch % 12 in DIATONIC_PITCH_CLASSES),
)
INVERSION_NAMES = (ROOT_INVERSION, FIRST_INVERSION)
type SATBVoice = Literal["soprano", "alto", "tenor", "bass"]


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
    preparation_events: tuple[InferenceEvent, ...]


@dataclass(frozen=True, slots=True)
class NoteHarmonization:
    """One result with search and rule-level explanatory traces."""

    voicings: tuple[PitchVoicing, ...]
    chords: tuple[str, ...]
    inversions: tuple[str, ...]
    log_weight: float
    decisions: tuple[ChoiceDecision, ...]
    choice_events: tuple[ChoiceEvent, ...]
    inference_events: tuple[InferenceEvent, ...]


def build_note_harmonizer_model(
    melody: tuple[int, ...] = (67, 72),
    *,
    given_voice: SATBVoice = "soprano",
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
    harmonic_variables = tuple(
        (
            Atom(f"harmony_{index}_chord"),
            Atom(f"harmony_{index}_inversion"),
        )
        for index in range(len(melody))
    )
    facts: list[Fact] = [
        Fact(Triple(PROBLEM, KIND, CSP_PROBLEM)),
        *source_facts,
        *_harmonic_vocabulary_facts(),
    ]
    weights: dict[tuple[Term, Term], float] = {}
    choice_priorities: dict[Term, int] = {}

    for index, (position, position_variables, harmonic_pair) in enumerate(
        zip(positions, variables, harmonic_variables, strict=True)
    ):
        chord_variable, inversion_variable = harmonic_pair
        facts.append(Fact(Triple(position, KIND, HARMONIC_POSITION)))
        facts.extend(
            (
                Fact(Triple(PROBLEM, VARIABLE, chord_variable)),
                Fact(Triple(chord_variable, KIND, CSP_VARIABLE)),
                Fact(Triple(chord_variable, KIND, HARMONIC_CHORD)),
                Fact(Triple(chord_variable, POSITION, position)),
                Fact(Triple(position, CHORD_VARIABLE, chord_variable)),
                Fact(Triple(PROBLEM, VARIABLE, inversion_variable)),
                Fact(Triple(inversion_variable, KIND, CSP_VARIABLE)),
                Fact(Triple(inversion_variable, KIND, HARMONIC_INVERSION)),
                Fact(Triple(inversion_variable, POSITION, position)),
                Fact(
                    Triple(
                        position,
                        INVERSION_VARIABLE,
                        inversion_variable,
                    )
                ),
            )
        )
        choice_priorities[chord_variable] = index * 6
        choice_priorities[inversion_variable] = index * 6 + 1

        chord_weights = _static_chord_weights(index)
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
            ROOT_INVERSION: 0.8,
            FIRST_INVERSION: 0.2,
        }
        for inversion in INVERSION_NAMES:
            weight = inversion_weights[inversion]
            facts.extend(
                (
                    Fact(
                        Triple(
                            inversion_variable,
                            CANDIDATE,
                            inversion,
                        )
                    ),
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

        if index > 0:
            previous_chord = harmonic_variables[index - 1][0]
            facts.append(
                Fact(
                    Triple(
                        chord_variable,
                        PREDECESSOR,
                        previous_chord,
                    )
                )
            )
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
                conditional = _conditional_marginal(
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
                                    Number(conditional[pitch]),
                                )
                            ),
                        )
                    )
                    for pitch in candidates
                )

    if len(positions) >= 3:
        facts.append(Fact(Triple(positions[0], PHRASE_ROLE, INITIAL)))
    facts.extend(
        (
            Fact(Triple(positions[-2], PHRASE_ROLE, PENULTIMATE)),
            Fact(Triple(positions[-1], PHRASE_ROLE, FINAL)),
        )
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
        position = generated_counts.index(0)
        raise ValueError(
            f"no legal tonal SATB voicing at position {position} "
            f"for {given_voice} pitch {melody[position]}"
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
        preparation_events,
    )


def harmonize_notes(
    melody: tuple[int, ...] = (67, 72),
    *,
    given_voice: SATBVoice = "soprano",
    max_solutions: int = 3,
    seed: int = 0,
) -> tuple[NoteHarmonization, ...]:
    """Return best-first harmonizations chosen one note variable at a time."""

    model = build_note_harmonizer_model(
        melody,
        given_voice=given_voice,
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
    melody: tuple[int, ...] = (67, 72),
    *,
    given_voice: SATBVoice = "soprano",
    seed: int = 0,
) -> NoteHarmonization:
    """Sample one feasible harmonization from contextual note marginals."""

    model = build_note_harmonizer_model(
        melody,
        given_voice=given_voice,
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
        CHORDS[0]: 0.20,
        CHORDS[1]: 0.05,
        CHORDS[2]: 0.35,
        CHORDS[3]: 0.25,
        CHORDS[4]: 0.15,
    }
    total = sum(raw.values())
    return {chord: value / total for chord, value in raw.items()}


def _chord_transition_weights(previous: Atom) -> dict[Atom, float]:
    preferred = {
        CHORDS[0]: {
            CHORDS[0]: 0.10,
            CHORDS[2]: 0.45,
            CHORDS[3]: 0.25,
            CHORDS[4]: 0.20,
        },
        CHORDS[1]: {CHORDS[3]: 1.0},
        CHORDS[2]: {
            CHORDS[0]: 0.15,
            CHORDS[1]: 0.15,
            CHORDS[3]: 0.70,
        },
        CHORDS[3]: {CHORDS[0]: 0.85, CHORDS[4]: 0.15},
        CHORDS[4]: {CHORDS[1]: 0.40, CHORDS[2]: 0.60},
    }[previous]
    return {chord: preferred.get(chord, 0.001) for chord in CHORDS}


def _harmonic_vocabulary_facts() -> tuple[Fact, ...]:
    facts: list[Fact] = []
    for chord, pitch_classes in CHORD_PITCH_CLASSES.items():
        facts.extend(
            (
                Fact(Triple(chord, KIND, HARMONIC_CHORD)),
                Fact(Triple(chord, ALLOWS_INVERSION, ROOT_INVERSION)),
                Fact(Triple(chord, ALLOWS_INVERSION, FIRST_INVERSION)),
            )
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
        root_pitch_class, third_pitch_class, _ = pitch_classes
        bass_pool = DIATONIC_VOICE_POOLS[3]
        facts.extend(
            Fact(
                Triple(
                    chord,
                    INVERSION_BASS_PITCH,
                    FiniteSequence((ROOT_INVERSION, Number(pitch))),
                )
            )
            for pitch in bass_pool
            if pitch % 12 == root_pitch_class
        )
        facts.extend(
            Fact(
                Triple(
                    chord,
                    INVERSION_BASS_PITCH,
                    FiniteSequence((FIRST_INVERSION, Number(pitch))),
                )
            )
            for pitch in bass_pool
            if pitch % 12 == third_pitch_class
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
