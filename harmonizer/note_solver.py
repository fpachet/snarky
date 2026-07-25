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
    VOICE_POOLS,
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

VOICE_NAMES = (
    Atom("soprano"),
    Atom("alto"),
    Atom("tenor"),
    Atom("bass"),
)
VOICE_VARIABLE_RELATIONS = tuple(
    Atom(f"{voice.name}_variable") for voice in VOICE_NAMES
)
type SATBVoice = Literal["soprano", "alto", "tenor", "bass"]


@dataclass(frozen=True, slots=True)
class NoteHarmonizerModel:
    """The two-phase note/voicing model and its stable variable layout."""

    csp: FiniteCSP
    program: RuleProgram
    positions: tuple[Atom, ...]
    variables: tuple[tuple[Atom, Atom, Atom, Atom], ...]
    generated_voicings: tuple[int, ...]
    given_voice: SATBVoice
    preparation_events: tuple[InferenceEvent, ...]


@dataclass(frozen=True, slots=True)
class NoteHarmonization:
    """One result with search and rule-level explanatory traces."""

    voicings: tuple[PitchVoicing, ...]
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
    """Build note domains, then let Snarky generate legal vertical tuples."""

    if len(melody) < 2:
        raise ValueError("the note harmonizer needs at least two positions")
    given_voice_index = _voice_index(given_voice)
    if any(pitch not in VOICE_POOLS[given_voice_index] for pitch in melody):
        raise ValueError(
            f"the given line contains a pitch outside the {given_voice} pool"
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
    facts: list[Fact] = [
        Fact(Triple(PROBLEM, KIND, CSP_PROBLEM)),
        *source_facts,
    ]
    weights: dict[tuple[Term, Term], float] = {}

    for index, (position, position_variables) in enumerate(
        zip(positions, variables, strict=True)
    ):
        facts.append(Fact(Triple(position, KIND, HARMONIC_POSITION)))
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
                else VOICE_POOLS[voice_index]
            )
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
                else VOICE_POOLS[voice_index]
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
            and fact.entity.relation == CANDIDATE
        )
        for position in positions
    )
    if 0 in generated_counts:
        position = generated_counts.index(0)
        raise ValueError(
            f"no legal C-major SATB voicing at position {position} "
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

    priorities: dict[Term, int] = {
        variable: position_index * len(VOICE_NAMES) + voice_index
        for position_index, position_variables in enumerate(model.variables)
        for voice_index, variable in enumerate(position_variables)
    }
    policy = (
        PriorityWeightedRandomChoicePolicy(priorities)
        if weighted_random
        else PriorityMRVChoicePolicy(priorities)
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
    return NoteHarmonization(
        tuple(voicings),
        solution.log_weight,
        solution.decisions,
        result.events,
        (*model.preparation_events, *solution.session.events),
    )


def _integer_value(term: Term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise TypeError("expected an integer note value")
    return term.value


def _static_marginal(
    position: int,
    voice: int,
    pitches: tuple[int, ...],
) -> dict[int, float]:
    if len(pitches) == 1:
        return {pitches[0]: 1.0}
    centers = (
        (67, 67, 72),
        (60, 60, 64),
        (55, 55, 55),
        (36, 43, 48),
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


def _complete_c_major_triad(arguments: tuple[Term, ...]) -> bool:
    if len(arguments) != 4:
        raise ValueError("complete_c_major_triad expects four notes")
    pitches = tuple(_integer_value(argument) for argument in arguments)
    return {pitch % 12 for pitch in pitches} == {0, 4, 7}


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
                "complete_c_major_triad",
                _complete_c_major_triad,
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
    transitions = Path(__file__).with_name("note_transition.rules")
    return (
        *parse_rule_groups(propagation.read_text()),
        *parse_rule_groups(
            transitions.read_text(),
            predicates=transition_registry,
        ),
    )
