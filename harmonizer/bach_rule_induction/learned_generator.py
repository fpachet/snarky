"""Diagnostic SATB generation using only induced Snarky rule activations."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from functools import cache
from itertools import combinations, product
from typing import cast

import yaml

from csp_solver import (
    FiniteCSP,
    assignment_from_solution,
    finite_csp_rule_library,
    solve_finite_csp,
)
from csp_solver.solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
)
from snarky import (
    Atom,
    ChoiceTraversal,
    Fact,
    FiniteSequence,
    InferenceSession,
    Number,
    PriorityWeightedRandomChoicePolicy,
    RuleGroup,
    Term,
    Triple,
    parse_rule_groups,
)

from .rule_profiles import RuleBaseManifest, load_rule_base

PROBLEM = Atom("learned_bach_harmonization")
POSITION_KIND = Atom("learned_satb_position")
TRANSITION_KIND = Atom("learned_satb_transition")
PREDECESSOR = Atom("predecessor")
SUCCESSOR = Atom("successor")
LEARNED_CONDITIONAL_WEIGHT = Atom("learned_conditional_weight")
LEARNED_RULE_ACTIVATION = Atom("learned_rule_activation")
LEARNED_TONAL_STRENGTH = Atom("learned_tonal_resolution_strength")
VOICE_PATH = Atom("voice_path")
VOICE_PAIR = Atom("voice_pair")
ADJACENT_VOICE_PAIR = Atom("adjacent_voice_pair")
OUTER_VOICE_PAIR = Atom("outer_voice_pair")
GLOBAL_KEY_MODE = Atom("global_key_mode")
SUBJECT_VOICE = Atom("subject_voice")
SOURCE_RELATIVE_CLASS = Atom("source_relative_class")
SOURCE_BASS_RELATIVE_CLASS = Atom("source_bass_relative_class")
TARGET_BASS_RELATIVE_CLASS = Atom("target_bass_relative_class")
MOTION_INTERVAL = Atom("motion_interval")
SOURCE_HARMONIC_STATUS = Atom("source_harmonic_status")
TARGET_HARMONIC_STATUS = Atom("target_harmonic_status")

VOICE_NAMES = tuple(map(Atom, ("soprano", "alto", "tenor", "bass")))
VOICE_PAIRS = tuple(combinations(range(4), 2))
ADJACENT_PAIRS = ((0, 1), (1, 2), (2, 3))

type PitchVoicing = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class LearnedRuleActivation:
    """One selected transition's traceable learned score contribution."""

    position: int
    rule_id: str
    context: tuple[str, ...]
    strength: int
    log_contribution: float


@dataclass(frozen=True, slots=True)
class LearnedGeneration:
    """One exploratory generation and its learned-rule trace."""

    profile_id: str
    seed: int
    tonic_pc: int
    mode: str
    soprano: tuple[int, ...]
    voicings: tuple[PitchVoicing, ...]
    activations: tuple[LearnedRuleActivation, ...]
    search_log_weight: float
    decisions: int

    @property
    def diagnostic_counts(self) -> dict[str, int]:
        crossings = 0
        unisons = 0
        for voicing in self.voicings:
            crossings += sum(
                voicing[upper] < voicing[lower] for upper, lower in ADJACENT_PAIRS
            )
            unisons += sum(
                voicing[upper] == voicing[lower] for upper, lower in ADJACENT_PAIRS
            )
        upper_spacing = sum(
            (voicing[0] - voicing[1] > 12) + (voicing[1] - voicing[2] > 12)
            for voicing in self.voicings
        )
        bass_spacing = sum(voicing[2] - voicing[3] > 19 for voicing in self.voicings)
        low_cardinality = sum(
            len({pitch % 12 for pitch in voicing}) < 3 for voicing in self.voicings
        )
        return {
            "vertical_crossings": crossings,
            "adjacent_unisons": unisons,
            "upper_spacing_over_octave": upper_spacing,
            "tenor_bass_spacing_over_19": bass_spacing,
            "pitch_class_cardinality_lt3": low_cardinality,
            "learned_rule_activations": len(self.activations),
        }


@dataclass(frozen=True, slots=True)
class LearnedTransitionEvaluation:
    """Public evaluation of one local SATB transition."""

    source: PitchVoicing
    target: PitchVoicing
    log_score: float
    activations: tuple[LearnedRuleActivation, ...]


@dataclass(frozen=True, slots=True)
class _TransitionScore:
    log_score: float
    activations: tuple[tuple[str, tuple[str, ...], int, float], ...]


@dataclass(frozen=True, slots=True)
class _LearnedModel:
    csp: FiniteCSP
    positions: tuple[Atom, ...]
    candidates: tuple[tuple[PitchVoicing, ...], ...]
    transition_scores: dict[tuple[PitchVoicing, PitchVoicing], _TransitionScore]
    profile: RuleBaseManifest


def _atom_text(term: Term) -> str:
    if isinstance(term, Atom):
        return term.name
    if isinstance(term, Number):
        return str(term.value)
    return str(term)


def _voicing_term(voicing: PitchVoicing) -> FiniteSequence:
    return FiniteSequence(tuple(Number(pitch) for pitch in voicing))


def _term_voicing(term: Term) -> PitchVoicing:
    if not isinstance(term, FiniteSequence) or len(term.elements) != 4:
        raise TypeError("expected a four-pitch finite sequence")
    pitches = tuple(
        int(element.value)
        for element in term.elements
        if isinstance(element, Number) and isinstance(element.value, int)
    )
    if len(pitches) != 4:
        raise TypeError("voicing pitches must be integer numbers")
    return cast(PitchVoicing, pitches)


def _transition_term(source: PitchVoicing, target: PitchVoicing) -> FiniteSequence:
    return FiniteSequence((_voicing_term(source), _voicing_term(target)))


def _relative_class(pitch: int, tonic_pc: int) -> int:
    return (pitch - tonic_pc) % 12


def _is_exact_harmony(
    voicing: PitchVoicing,
    tonic_pc: int,
    *,
    classes: frozenset[int],
    bass_class: int,
) -> bool:
    relative = frozenset(_relative_class(pitch, tonic_pc) for pitch in voicing)
    return relative == classes and _relative_class(voicing[3], tonic_pc) == bass_class


def _transition_facts(
    source: PitchVoicing,
    target: PitchVoicing,
    *,
    tonic_pc: int,
    mode: str,
) -> tuple[Fact, ...]:
    transition = _transition_term(source, target)
    facts: list[Fact] = [
        Fact(Triple(transition, KIND, TRANSITION_KIND)),
        Fact(Triple(transition, GLOBAL_KEY_MODE, Atom(mode))),
        Fact(Triple(transition, SUBJECT_VOICE, Atom("alto"))),
        Fact(
            Triple(
                transition,
                SOURCE_RELATIVE_CLASS,
                Number(_relative_class(source[1], tonic_pc)),
            )
        ),
        Fact(
            Triple(
                transition,
                SOURCE_BASS_RELATIVE_CLASS,
                Number(_relative_class(source[3], tonic_pc)),
            )
        ),
        Fact(
            Triple(
                transition,
                TARGET_BASS_RELATIVE_CLASS,
                Number(_relative_class(target[3], tonic_pc)),
            )
        ),
        Fact(Triple(transition, MOTION_INTERVAL, Number(target[1] - source[1]))),
        Fact(
            Triple(
                transition,
                OUTER_VOICE_PAIR,
                FiniteSequence(
                    tuple(
                        Number(pitch)
                        for pitch in (
                            source[0],
                            source[3],
                            target[0],
                            target[3],
                        )
                    )
                ),
            )
        ),
    ]
    for voice, source_pitch, target_pitch in zip(
        VOICE_NAMES, source, target, strict=True
    ):
        facts.append(
            Fact(
                Triple(
                    transition,
                    VOICE_PATH,
                    FiniteSequence((voice, Number(source_pitch), Number(target_pitch))),
                )
            )
        )
    for upper, lower in VOICE_PAIRS:
        relation = (
            ADJACENT_VOICE_PAIR if (upper, lower) in ADJACENT_PAIRS else VOICE_PAIR
        )
        payload = FiniteSequence(
            (
                VOICE_NAMES[upper],
                VOICE_NAMES[lower],
                Number(source[upper]),
                Number(source[lower]),
                Number(target[upper]),
                Number(target[lower]),
            )
        )
        facts.append(Fact(Triple(transition, VOICE_PAIR, payload)))
        if relation == ADJACENT_VOICE_PAIR:
            facts.append(Fact(Triple(transition, ADJACENT_VOICE_PAIR, payload)))
    if _is_exact_harmony(
        source,
        tonic_pc,
        classes=frozenset((11, 2, 5)),
        bass_class=2,
    ):
        facts.append(
            Fact(
                Triple(
                    transition,
                    SOURCE_HARMONIC_STATUS,
                    Atom("exact_vii6"),
                )
            )
        )
    if _is_exact_harmony(
        target,
        tonic_pc,
        classes=frozenset((0, 4, 7)),
        bass_class=4,
    ):
        facts.append(
            Fact(
                Triple(
                    transition,
                    TARGET_HARMONIC_STATUS,
                    Atom("exact_I6"),
                )
            )
        )
    return tuple(facts)


@cache
def _learned_rule_groups() -> tuple[RuleGroup, ...]:
    profile = load_rule_base("learned")
    groups: list[RuleGroup] = []
    for path in profile.rule_files:
        groups.extend(parse_rule_groups(path.read_text(encoding="utf-8")))
    return tuple(
        group for group in groups if group.name != "update_learned_contextual_weights"
    )


@cache
def _learned_weight_group() -> RuleGroup:
    groups: list[RuleGroup] = []
    for path in load_rule_base("learned").rule_files:
        groups.extend(parse_rule_groups(path.read_text(encoding="utf-8")))
    return next(
        group for group in groups if group.name == "update_learned_contextual_weights"
    )


def _score_transitions(
    sources: tuple[PitchVoicing, ...],
    targets: tuple[PitchVoicing, ...],
    *,
    tonic_pc: int,
    mode: str,
    profile: RuleBaseManifest,
) -> dict[tuple[PitchVoicing, PitchVoicing], _TransitionScore]:
    facts = tuple(
        fact
        for source, target in product(sources, targets)
        for fact in _transition_facts(
            source,
            target,
            tonic_pc=tonic_pc,
            mode=mode,
        )
    )
    session = InferenceSession(facts)
    for group in _learned_rule_groups():
        session.run_group(group)

    activations: dict[
        tuple[PitchVoicing, PitchVoicing],
        list[tuple[str, tuple[str, ...], int, float]],
    ] = {(source, target): [] for source, target in product(sources, targets)}
    weights = profile.weight_by_rule
    for fact in session.facts:
        entity = fact.entity
        if not isinstance(entity, Triple):
            continue
        if not (
            isinstance(entity.subject, FiniteSequence)
            and len(entity.subject.elements) == 2
        ):
            continue
        source = _term_voicing(entity.subject.elements[0])
        target = _term_voicing(entity.subject.elements[1])
        key = (source, target)
        if entity.relation == LEARNED_RULE_ACTIVATION:
            payload = entity.object
            if not isinstance(payload, FiniteSequence) or not payload.elements:
                continue
            rule_id = _atom_text(payload.elements[0])
            weight = weights[rule_id]
            if weight.log_contribution is None:
                raise ValueError(f"{rule_id} needs a direct diagnostic weight")
            context = tuple(_atom_text(item) for item in payload.elements[1:])
            activations[key].append((rule_id, context, 1, weight.log_contribution))
        elif (
            entity.relation == LEARNED_TONAL_STRENGTH
            and isinstance(entity.object, Number)
            and isinstance(entity.object.value, int)
        ):
            rule_id = "R-LEARNED-LEADING-001"
            weight = weights[rule_id]
            if weight.log_contribution_per_strength is None:
                raise ValueError(f"{rule_id} needs a strength weight")
            strength = entity.object.value
            activations[key].append(
                (
                    rule_id,
                    ("alto",),
                    strength,
                    strength * weight.log_contribution_per_strength,
                )
            )
    return {
        key: _TransitionScore(
            sum(item[3] for item in values),
            tuple(sorted(values)),
        )
        for key, values in activations.items()
    }


def _scaffolding_pools(profile: RuleBaseManifest) -> tuple[tuple[int, ...], ...]:
    if profile.scaffolding_path is None:
        raise ValueError(f"{profile.id} has no diagnostic scaffolding")
    raw = yaml.safe_load(profile.scaffolding_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("scaffolding must be a mapping")
    voice_pools = raw.get("voice_pitch_pools")
    if not isinstance(voice_pools, dict):
        raise ValueError("scaffolding needs voice_pitch_pools")
    output: list[tuple[int, ...]] = []
    for voice in ("alto", "tenor", "bass"):
        payload = voice_pools.get(voice)
        if not isinstance(payload, dict):
            raise ValueError(f"missing {voice} pitch pool")
        pitches = payload.get("pitches")
        if not isinstance(pitches, list) or not all(
            isinstance(pitch, int) and not isinstance(pitch, bool) for pitch in pitches
        ):
            raise ValueError(f"invalid {voice} pitch pool")
        output.append(tuple(sorted(set(pitches))))
    return tuple(output)


def build_learned_generator_model(
    soprano: tuple[int, ...],
    *,
    tonic_pc: int = 0,
    mode: str = "major",
) -> _LearnedModel:
    """Build a complete-voicing diagnostic model with no historical rules."""

    if len(soprano) < 2:
        raise ValueError("learned generation needs at least two positions")
    if not 0 <= tonic_pc <= 11:
        raise ValueError("tonic_pc must be between 0 and 11")
    if mode not in {"major", "minor"}:
        raise ValueError("mode must be major or minor")
    profile = load_rule_base("learned")
    lower_pools = _scaffolding_pools(profile)
    candidates = tuple(
        tuple((pitch, alto, tenor, bass) for alto, tenor, bass in product(*lower_pools))
        for pitch in soprano
    )
    positions = tuple(
        Atom(f"learned_position_{index}") for index in range(len(soprano))
    )
    score_tables = tuple(
        _score_transitions(
            candidates[index - 1],
            candidates[index],
            tonic_pc=tonic_pc,
            mode=mode,
            profile=profile,
        )
        for index in range(1, len(candidates))
    )
    transition_scores = {
        key: value for table in score_tables for key, value in table.items()
    }

    facts: list[Fact] = [Fact(Triple(PROBLEM, KIND, CSP_PROBLEM))]
    weights: dict[tuple[Term, Term], float] = {}
    for index, (position, domain) in enumerate(zip(positions, candidates, strict=True)):
        facts.extend(
            (
                Fact(Triple(PROBLEM, VARIABLE, position)),
                Fact(Triple(position, KIND, CSP_VARIABLE)),
                Fact(Triple(position, KIND, POSITION_KIND)),
            )
        )
        neutral = 1.0 / len(domain)
        for voicing in domain:
            term = _voicing_term(voicing)
            facts.append(Fact(Triple(position, CANDIDATE, term)))
            weights[(position, term)] = neutral
        if index == 0:
            continue
        previous = positions[index - 1]
        facts.append(Fact(Triple(position, PREDECESSOR, previous)))
        facts.append(Fact(Triple(previous, SUCCESSOR, position)))
        for source in candidates[index - 1]:
            row = score_tables[index - 1]
            raw = {
                target: math.exp(row[(source, target)].log_score) for target in domain
            }
            total = sum(raw.values())
            for target, value in raw.items():
                facts.append(
                    Fact(
                        Triple(
                            position,
                            LEARNED_CONDITIONAL_WEIGHT,
                            FiniteSequence(
                                (
                                    _voicing_term(source),
                                    _voicing_term(target),
                                    Number(value / total),
                                )
                            ),
                        )
                    )
                )

    library = finite_csp_rule_library()
    return _LearnedModel(
        FiniteCSP(
            PROBLEM,
            tuple(facts),
            weights,
            (*library.groups, _learned_weight_group()),
        ),
        positions,
        candidates,
        transition_scores,
        profile,
    )


def evaluate_learned_transition(
    source: PitchVoicing,
    target: PitchVoicing,
    *,
    tonic_pc: int = 0,
    mode: str = "major",
) -> LearnedTransitionEvaluation:
    """Evaluate one pair through the autonomous learned Snarky files."""

    if mode not in {"major", "minor"}:
        raise ValueError("mode must be major or minor")
    if not 0 <= tonic_pc <= 11:
        raise ValueError("tonic_pc must be between 0 and 11")
    score = _score_transitions(
        (source,),
        (target,),
        tonic_pc=tonic_pc,
        mode=mode,
        profile=load_rule_base("learned"),
    )[(source, target)]
    return LearnedTransitionEvaluation(
        source,
        target,
        score.log_score,
        tuple(
            LearnedRuleActivation(1, rule_id, context, strength, contribution)
            for rule_id, context, strength, contribution in score.activations
        ),
    )


def _solve_learned_model(
    model: _LearnedModel,
    soprano: tuple[int, ...],
    *,
    tonic_pc: int,
    mode: str,
    seed: int,
) -> LearnedGeneration:
    result = solve_finite_csp(
        model.csp,
        max_solutions=1,
        traversal=ChoiceTraversal.DEPTH_FIRST,
        policy=PriorityWeightedRandomChoicePolicy(
            {position: index for index, position in enumerate(model.positions)}
        ),
        seed=seed,
    )
    if not result.solutions:
        raise ValueError("the learned-only diagnostic model has no solution")
    solution = result.solutions[0]
    assignment = assignment_from_solution(solution, PROBLEM)
    voicings = tuple(
        _term_voicing(assignment[position]) for position in model.positions
    )
    selected_activations: list[LearnedRuleActivation] = []
    for index, (source, target) in enumerate(
        zip(voicings[:-1], voicings[1:], strict=True), start=1
    ):
        for rule_id, context, strength, contribution in model.transition_scores[
            (source, target)
        ].activations:
            selected_activations.append(
                LearnedRuleActivation(
                    index,
                    rule_id,
                    context,
                    strength,
                    contribution,
                )
            )
    return LearnedGeneration(
        model.profile.id,
        seed,
        tonic_pc,
        mode,
        soprano,
        voicings,
        tuple(selected_activations),
        solution.log_weight,
        len(solution.decisions),
    )


def generate_with_learned_rules(
    soprano: tuple[int, ...],
    *,
    tonic_pc: int = 0,
    mode: str = "major",
    seed: int = 0,
) -> LearnedGeneration:
    """Generate one diagnostic SATB path from the learned-only profile."""

    model = build_learned_generator_model(
        soprano,
        tonic_pc=tonic_pc,
        mode=mode,
    )
    return _solve_learned_model(
        model,
        soprano,
        tonic_pc=tonic_pc,
        mode=mode,
        seed=seed,
    )


def generate_many_with_learned_rules(
    soprano: tuple[int, ...],
    *,
    tonic_pc: int = 0,
    mode: str = "major",
    seeds: tuple[int, ...] = (0,),
) -> tuple[LearnedGeneration, ...]:
    """Reuse one learned score table for several registered random seeds."""

    if not seeds:
        raise ValueError("at least one seed is required")
    model = build_learned_generator_model(
        soprano,
        tonic_pc=tonic_pc,
        mode=mode,
    )
    return tuple(
        _solve_learned_model(
            model,
            soprano,
            tonic_pc=tonic_pc,
            mode=mode,
            seed=seed,
        )
        for seed in seeds
    )


def activation_histogram(
    generations: tuple[LearnedGeneration, ...],
) -> dict[str, int]:
    """Aggregate selected learned-rule activations for a diagnostic report."""

    counts = Counter(
        activation.rule_id
        for generation in generations
        for activation in generation.activations
    )
    return dict(sorted(counts.items()))
