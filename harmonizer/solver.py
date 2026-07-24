"""Weighted search over a first finite ROY-style voicing model."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from functools import cache
from itertools import combinations, product
from pathlib import Path

from csp_solver.solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    BinaryCSP,
    assignment_from_solution,
    binary_constraint_facts,
    solve_binary_csp,
)
from snarky import (
    Atom,
    ChoiceSearchResult,
    ChoiceTraversal,
    Fact,
    FiniteSequence,
    Number,
    RuleGroup,
    Term,
    Triple,
    parse_rule_groups,
)

PROBLEM = Atom("roy_harmonization")
HARMONIC_POSITION = Atom("harmonic_position")
TRIAD = frozenset((0, 4, 7))
VOICE_POOLS = (
    (60, 64, 67, 72),
    (55, 60, 64, 67),
    (48, 52, 55, 60),
    (36, 40, 43, 48),
)

type PitchVoicing = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class HarmonizerModel:
    csp: BinaryCSP
    positions: tuple[Atom, ...]
    candidates: tuple[tuple[PitchVoicing, ...], ...]


@dataclass(frozen=True, slots=True)
class Harmonization:
    voicings: tuple[PitchVoicing, ...]
    log_weight: float
    decisions: int


def build_harmonizer_model(
    melody: tuple[int, ...] = (67, 72),
) -> HarmonizerModel:
    """Build the finite hard-constraint model for one C-major phrase."""

    if len(melody) < 2:
        raise ValueError("the first harmonizer needs at least two positions")
    positions = tuple(
        Atom(f"position_{index}") for index in range(len(melody))
    )
    voicings = tuple(_legal_voicings(pitch) for pitch in melody)
    if any(not candidates for candidates in voicings):
        raise ValueError("the melody leaves an empty voicing domain")

    facts: list[Fact] = [Fact(Triple(PROBLEM, KIND, CSP_PROBLEM))]
    weights: dict[tuple[Term, Term], float] = {}
    for index, (position, candidates) in enumerate(
        zip(positions, voicings, strict=True)
    ):
        facts.extend(
            (
                Fact(Triple(PROBLEM, VARIABLE, position)),
                Fact(Triple(position, KIND, CSP_VARIABLE)),
                Fact(Triple(position, KIND, HARMONIC_POSITION)),
            )
        )
        marginals = _pitch_marginals(index, candidates)
        for voicing in candidates:
            value = _voicing_term(voicing)
            facts.append(Fact(Triple(position, CANDIDATE, value)))
            weights[(position, value)] = math.prod(
                marginals[voice][pitch]
                for voice, pitch in enumerate(voicing)
            )

    for index in range(len(positions) - 1):
        left = positions[index]
        right = positions[index + 1]
        pairs = tuple(product(voicings[index], voicings[index + 1]))
        for rule_id, predicate in (
            ("R-MELODY", _melodic_transition),
            ("R-PARALLEL", _no_parallel_perfect_intervals),
            ("R-GLOBAL-MOTION", _global_motion),
        ):
            relation = Atom(f"{rule_id.lower()}_{index}_{index + 1}")
            constraint = Atom(
                f"{rule_id.lower()}_constraint_{index}_{index + 1}"
            )
            allowed = tuple(
                (_voicing_term(source), _voicing_term(target))
                for source, target in pairs
                if predicate(source, target)
            )
            facts.extend(
                binary_constraint_facts(
                    constraint,
                    relation,
                    left,
                    right,
                    allowed,
                )
            )

    return HarmonizerModel(
        BinaryCSP(
            PROBLEM,
            tuple(facts),
            weights,
            _harmonizer_groups(),
        ),
        positions,
        voicings,
    )


def harmonize(
    melody: tuple[int, ...] = (67, 72),
    *,
    max_solutions: int = 3,
) -> tuple[Harmonization, ...]:
    model = build_harmonizer_model(melody)
    result = solve_binary_csp(
        model.csp,
        max_solutions=max_solutions,
        traversal=ChoiceTraversal.BEST_FIRST,
    )
    return tuple(
        _harmonization_from_result(model, result, index)
        for index in range(len(result.solutions))
    )


def _harmonization_from_result(
    model: HarmonizerModel,
    result: ChoiceSearchResult,
    solution_index: int,
) -> Harmonization:
    solution = result.solutions[solution_index]
    assignment = assignment_from_solution(solution, PROBLEM)
    return Harmonization(
        tuple(
            _term_voicing(assignment[position])
            for position in model.positions
        ),
        solution.log_weight,
        len(solution.decisions),
    )


@cache
def _legal_voicings(soprano: int) -> tuple[PitchVoicing, ...]:
    if soprano not in VOICE_POOLS[0]:
        return ()
    output: list[PitchVoicing] = []
    for alto, tenor, bass in product(*VOICE_POOLS[1:]):
        voicing = (soprano, alto, tenor, bass)
        if not soprano >= alto >= tenor >= bass:
            continue
        if soprano - alto > 12 or alto - tenor > 12:
            continue
        if tenor - bass > 19:
            continue
        pitch_classes = tuple(pitch % 12 for pitch in voicing)
        if frozenset(pitch_classes) != TRIAD:
            continue
        if sorted(Counter(pitch_classes).values()) != [1, 1, 2]:
            continue
        output.append(voicing)
    return tuple(output)


def _melodic_transition(
    source: PitchVoicing,
    target: PitchVoicing,
) -> bool:
    movements = tuple(
        target_pitch - source_pitch
        for source_pitch, target_pitch in zip(source, target, strict=True)
    )
    if any(abs(movement) > 12 or abs(movement) == 6 for movement in movements):
        return False
    for upper, lower in ((0, 1), (1, 2), (2, 3)):
        if target[lower] > source[upper]:
            return False
        if target[upper] < source[lower]:
            return False
    return True


def _no_parallel_perfect_intervals(
    source: PitchVoicing,
    target: PitchVoicing,
) -> bool:
    for first, second in combinations(range(4), 2):
        source_interval = abs(source[first] - source[second]) % 12
        target_interval = abs(target[first] - target[second]) % 12
        first_motion = target[first] - source[first]
        second_motion = target[second] - source[second]
        similar_motion = (
            first_motion != 0
            and second_motion != 0
            and (first_motion > 0) == (second_motion > 0)
        )
        if (
            source_interval in {0, 7}
            and target_interval == source_interval
            and similar_motion
        ):
            return False
    return True


def _global_motion(
    source: PitchVoicing,
    target: PitchVoicing,
) -> bool:
    movements = tuple(
        target_pitch - source_pitch
        for source_pitch, target_pitch in zip(source, target, strict=True)
    )
    return not all(movement > 0 for movement in movements) and not all(
        movement < 0 for movement in movements
    )


def _pitch_marginals(
    position: int,
    candidates: tuple[PitchVoicing, ...],
) -> tuple[dict[int, float], ...]:
    centers = (
        0,
        (60, 60, 64)[position % 3],
        (55, 55, 55)[position % 3],
        (36, 43, 48)[position % 3],
    )
    marginals: list[dict[int, float]] = []
    for voice in range(4):
        pitches = tuple(
            dict.fromkeys(voicing[voice] for voicing in candidates)
        )
        if voice == 0:
            marginals.append({pitch: 1.0 for pitch in pitches})
            continue
        raw = {
            pitch: math.exp(-abs(pitch - centers[voice]) / 4)
            for pitch in pitches
        }
        total = sum(raw.values())
        marginals.append(
            {pitch: weight / total for pitch, weight in raw.items()}
        )
    return tuple(marginals)


def _voicing_term(voicing: PitchVoicing) -> FiniteSequence:
    return FiniteSequence(tuple(Number(pitch) for pitch in voicing))


def _term_voicing(term: Term) -> PitchVoicing:
    if not isinstance(term, FiniteSequence) or len(term.elements) != 4:
        raise TypeError("expected a four-note voicing sequence")
    values: list[int] = []
    for element in term.elements:
        if not isinstance(element, Number) or not isinstance(element.value, int):
            raise TypeError("voicing pitches must be integer Numbers")
        values.append(element.value)
    return values[0], values[1], values[2], values[3]


@cache
def _harmonizer_groups() -> tuple[RuleGroup, ...]:
    path = Path(__file__).with_name("rules.rules")
    return parse_rule_groups(path.read_text())


def main() -> None:
    for index, solution in enumerate(harmonize(), start=1):
        probability = math.exp(solution.log_weight)
        print(
            f"{index}: weight={probability:.8f} "
            f"decisions={solution.decisions} {solution.voicings}"
        )


if __name__ == "__main__":
    main()
