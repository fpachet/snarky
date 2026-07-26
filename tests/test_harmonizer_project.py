import pytest

from csp_solver.solver import solve_binary_csp
from harmonizer import (
    build_note_harmonizer_model,
    harmonize_notes,
    sample_harmonization,
)
from harmonizer.solver import build_harmonizer_model, harmonize
from snarky import (
    Atom,
    ChoiceEventKind,
    ChoiceTraversal,
    FiniteSequence,
    Number,
    Triple,
)


def test_first_harmonizer_returns_legal_weighted_satb_solutions() -> None:
    model = build_harmonizer_model()
    solutions = harmonize(max_solutions=1)

    assert tuple(len(domain) for domain in model.candidates) == (15, 9)
    assert len(solutions) == 1
    solution = solutions[0]
    assert solution.decisions == 2
    assert solution.log_weight < 0
    assert tuple(voicing[0] for voicing in solution.voicings) == (67, 72)
    for voicing in solution.voicings:
        soprano, alto, tenor, bass = voicing
        assert soprano >= alto >= tenor >= bass
        assert soprano - alto <= 12
        assert alto - tenor <= 12
        assert tenor - bass <= 19


def test_lazy_and_eager_best_first_frontiers_are_equivalent() -> None:
    model = build_harmonizer_model()
    lazy = solve_binary_csp(
        model.csp,
        max_solutions=3,
        traversal=ChoiceTraversal.BEST_FIRST,
        lazy_frontier=True,
    )
    eager = solve_binary_csp(
        model.csp,
        max_solutions=3,
        traversal=ChoiceTraversal.BEST_FIRST,
        lazy_frontier=False,
    )

    assert lazy.status is eager.status
    assert lazy.explored_nodes == eager.explored_nodes
    assert lazy.failed_branches == eager.failed_branches
    assert tuple(
        (solution.decisions, solution.log_weight, solution.session.facts)
        for solution in lazy.solutions
    ) == tuple(
        (solution.decisions, solution.log_weight, solution.session.facts)
        for solution in eager.solutions
    )
    assert lazy.events == eager.events


def test_intensional_transitions_match_extensional_oracle() -> None:
    extensional = harmonize(
        max_solutions=3,
        intensional_transitions=False,
    )
    intensional = harmonize(
        max_solutions=3,
        intensional_transitions=True,
    )

    assert intensional == extensional
    assert len(build_harmonizer_model(intensional_transitions=False).csp.facts) == 401
    assert len(build_harmonizer_model(intensional_transitions=True).csp.facts) == 32


def test_note_harmonizer_generates_and_chooses_individual_notes() -> None:
    melody = (72, 69, 71, 72)
    model = build_note_harmonizer_model(melody)
    solutions = harmonize_notes(melody, max_solutions=3)

    assert model.generated_voicings == (3, 24, 5, 3)
    assert model.program.manifest() == (
        (
            "preparation",
                (
                    "derive_melodic_roles",
                    "derive_harmonic_plan",
                "prepare_harmonic_domains",
                "generate_candidate_voicings",
                "describe_candidate_voicings",
                "enforce_vertical_conformance",
                "prepare_tonal_form",
                "prepare_note_voicing_channel",
                "describe_satb_transitions",
                "derive_satb_resolution_exceptions",
                "detect_satb_transition_violations",
                "classify_legal_satb_transitions",
            ),
        ),
        ("step:harmonic_plan", ("choose_harmonic_plan",)),
        ("step:satb_realization", ("choose_satb_realization",)),
        (
            "propagation",
            (
                "apply_harmonizer_decisions",
                "classify_csp_domains",
                "enforce_tonal_form",
                "maintain_note_voicing_channel",
                "update_contextual_note_weights",
                "propagate_note_harmonic_transitions",
                "classify_csp_problems",
            ),
        ),
        ("interpretation", ("interpret_note_harmonization",)),
    )
    assert "propagate_binary_constraints" not in tuple(
        group.name for group in model.program.all_groups
    )
    assert len(solutions) == 3
    assert all(
        tuple(voicing[0] for voicing in solution.voicings) == melody
        for solution in solutions
    )
    assert all(
        set(solution.melodic_roles) == {"chord_tone"}
        for solution in solutions
    )
    assert all(
        solution.chords[0] == "degree_I"
        and solution.chords[-2] in {"degree_V", "degree_V7"}
        and solution.chords[-1] == "degree_I"
        for solution in solutions
    )
    assert solutions[0].chords == (
        "degree_I",
        "degree_IV",
        "degree_V",
        "degree_I",
    )
    assert solutions[0].voicings == (
        (72, 64, 55, 48),
        (69, 65, 60, 41),
        (71, 62, 50, 43),
        (72, 64, 55, 36),
    )
    assert all(
        decision.point.startswith(
            (
                "choose_harmonic_plan:choose_harmonic_chord:",
                "choose_satb_realization:",
            )
        )
        for solution in solutions
        for decision in solution.decisions
    )
    assert all(
        any(event.kind is ChoiceEventKind.STEP for event in solution.choice_events)
        for solution in solutions
    )
    assert any(
        event.rule_group == "update_contextual_note_weights"
        for event in solutions[0].inference_events
    )
    assert any(
        event.rule_group == "maintain_note_voicing_channel"
        for event in solutions[0].inference_events
    )
    assert any(
        event.rule_group == "prepare_harmonic_domains"
        for event in model.preparation_events
    )
    assert any(
        event.rule_group == "propagate_note_harmonic_transitions"
        for event in solutions[0].inference_events
    )


def test_contextual_weighted_sampling_is_seed_reproducible() -> None:
    first = sample_harmonization(seed=7)
    second = sample_harmonization(seed=7)
    other = sample_harmonization(seed=0)

    assert first.voicings == second.voicings
    assert first.decisions == second.decisions
    assert first.voicings != other.voicings


def test_chord_choice_and_first_inversion_are_exposed_declaratively() -> None:
    melody = (72, 71)
    solutions = harmonize_notes(melody, cadence="half", max_solutions=10)
    solution = next(
        item
        for item in solutions
        if item.inversions[0] == "first"
        and item.chords[-1] == "degree_V"
    )

    assert solution.chords == (
        "degree_IV",
        "degree_V",
    )
    assert solution.inversions == (
        "first",
        "root",
    )
    assert any(
        "variable=harmony_0_chord]" in decision.point for decision in solution.decisions
    )
    chord_pitch_classes = {
        "degree_I": {0, 4, 7},
        "degree_ii": {2, 5, 9},
        "degree_IV": {0, 5, 9},
        "degree_V": {2, 7, 11},
        "degree_V7": {2, 5, 7, 11},
        "degree_vi": {0, 4, 9},
        "degree_vii": {2, 5, 11},
    }
    for chord, voicing in zip(
        solution.chords,
        solution.voicings,
        strict=True,
    ):
        assert {pitch % 12 for pitch in voicing} == chord_pitch_classes[chord]
    first_inversion_index = solution.inversions.index("first")
    assert solution.voicings[first_inversion_index][3] % 12 == 9


def test_dominant_seventh_and_tendency_tones_resolve() -> None:
    solution = harmonize_notes(
        (72, 69, 71, 72),
        harmonic_plan=("I", "ii", "V7", "I"),
        max_solutions=1,
    )[0]

    assert solution.chords[-2:] == ("degree_V7", "degree_I")
    dominant, tonic = solution.voicings[-2:]
    assert {pitch % 12 for pitch in dominant} == {2, 5, 7, 11}
    for source, target in zip(dominant, tonic, strict=True):
        if source % 12 == 11:
            assert target == source + 1
        if source % 12 == 5:
            assert target == source - 1


def test_diminished_leading_tone_chord_has_legal_first_inversion_voicings() -> None:
    model = build_note_harmonizer_model((71, 71), cadence="half")
    generated = set()
    removed_by_vertical_rules = set()
    for event in model.preparation_events:
        entity = event.fact.entity
        if (
            isinstance(entity, Triple)
            and entity.subject == model.positions[0]
            and entity.relation == Atom("voicing_candidate")
            and isinstance(entity.object, FiniteSequence)
            and entity.object.elements[0] == Atom("degree_vii")
        ):
            if event.rule_group == "generate_candidate_voicings":
                generated.add(entity.object.elements)
            if (
                event.rule_group == "enforce_vertical_conformance"
                and event.kind.value == "remove"
            ):
                removed_by_vertical_rules.add(entity.object.elements)
    candidates = generated - removed_by_vertical_rules

    assert candidates
    for chord, inversion, *notes in candidates:
        assert chord == Atom("degree_vii")
        assert inversion == Atom("first")
        assert all(isinstance(note, Number) for note in notes)
        pitch_classes = [
            int(note.value) % 12 for note in notes if isinstance(note, Number)
        ]
        assert pitch_classes[3] == 2
        assert pitch_classes.count(11) == 1
        assert pitch_classes.count(2) == 1
        assert pitch_classes.count(5) == 2


def test_cadential_six_four_is_generated_and_resolved() -> None:
    solution = harmonize_notes(
        (48, 43, 43, 48),
        given_voice="bass",
        max_solutions=1,
    )[0]

    assert solution.chords == (
        "degree_I",
        "degree_I",
        "degree_V",
        "degree_I",
    )
    assert solution.inversions == ("root", "second", "root", "root")
    six_four, dominant = solution.voicings[1:3]
    assert six_four[3] == dominant[3]
    for source, target in zip(six_four[:3], dominant[:3], strict=True):
        if source % 12 == 0:
            assert target == source - 1
        if source % 12 == 4:
            assert target == source - 2


def test_cadence_profiles_and_harmonic_rhythm_are_explicit() -> None:
    plagal = harmonize_notes((69, 72), cadence="plagal", max_solutions=1)[0]
    deceptive = harmonize_notes(
        (71, 72),
        cadence="deceptive",
        max_solutions=1,
    )[0]
    half = harmonize_notes((72, 71), cadence="half", max_solutions=1)[0]
    held = harmonize_notes(
        (72, 72, 71, 72),
        harmonic_rhythm=(0, 0, 1, 2),
        max_solutions=1,
    )[0]

    assert plagal.chords == ("degree_IV", "degree_I")
    assert deceptive.chords == ("degree_V", "degree_vi")
    assert half.chords[-1] == "degree_V"
    assert held.harmonic_rhythm == (0, 0, 1, 2)
    assert held.chords[0] == held.chords[1]
    assert held.inversions[0] == held.inversions[1]


def test_long_form_harmonization_uses_a_prolonged_predominant() -> None:
    solution = harmonize_notes(
        (72, 74, 76, 72, 65, 69, 71, 72),
        harmonic_rhythm=(0, 1, 2, 3, 4, 4, 5, 6),
        max_solutions=1,
    )[0]

    assert solution.chords == (
        "degree_I",
        "degree_V",
        "degree_I",
        "degree_IV",
        "degree_ii",
        "degree_ii",
        "degree_V7",
        "degree_I",
    )
    assert solution.harmonic_rhythm == (0, 1, 2, 3, 4, 4, 5, 6)
    assert solution.inversions == (
        "root",
        "root",
        "root",
        "first",
        "root",
        "root",
        "root",
        "root",
    )
    assert solution.voicings == (
        (72, 67, 64, 48),
        (74, 67, 59, 43),
        (76, 67, 60, 48),
        (72, 65, 60, 45),
        (65, 62, 57, 50),
        (69, 62, 53, 50),
        (71, 65, 62, 43),
        (72, 64, 55, 48),
    )


def test_eight_bar_form_derives_a_plan_from_the_soprano_in_two_steps() -> None:
    solution = harmonize_notes(
        (67, 76, 69, 72, 72, 76, 65, 69, 67, 64, 69, 72, 74, 69, 71, 72),
        harmonic_rhythm=(
            0,
            0,
            1,
            1,
            2,
            2,
            3,
            3,
            4,
            4,
            5,
            5,
            6,
            6,
            7,
            8,
        ),
        traversal=ChoiceTraversal.DEPTH_FIRST,
        max_solutions=1,
    )[0]

    assert solution.chords == (
        "degree_I",
        "degree_I",
        "degree_IV",
        "degree_IV",
        "degree_I",
        "degree_I",
        "degree_IV",
        "degree_IV",
        "degree_I",
        "degree_I",
        "degree_IV",
        "degree_IV",
        "degree_ii",
        "degree_ii",
        "degree_V",
        "degree_I",
    )
    assert solution.voicings == (
        (67, 60, 52, 48),
        (76, 64, 55, 48),
        (69, 65, 60, 41),
        (72, 65, 57, 41),
        (72, 64, 55, 36),
        (76, 64, 55, 36),
        (65, 60, 57, 41),
        (69, 60, 53, 41),
        (67, 60, 52, 36),
        (64, 60, 55, 36),
        (69, 60, 53, 41),
        (72, 60, 57, 41),
        (74, 65, 57, 38),
        (69, 65, 57, 38),
        (71, 62, 55, 43),
        (72, 64, 55, 48),
    )
    assert any(
        event.rule_group == "derive_harmonic_plan"
        and event.rule_name == "constrain_perfect_cadence_penultimate"
        for event in solution.inference_events
    )
    assert any(
        event.kind is ChoiceEventKind.STEP
        and event.detail == "harmonic_plan -> satb_realization"
        for event in solution.choice_events
    )
    assert {
        event.fact.entity.object
        for event in solution.inference_events
        if isinstance(event.fact.entity, Triple)
        and event.fact.entity.relation == Atom("harmonic_function")
    } == {Atom("tonic"), Atom("predominant"), Atom("dominant")}


def test_each_diatonic_note_receives_an_independent_harmonic_decision() -> None:
    melody = (72, 74, 76, 67, 65, 69, 71, 72)
    solution = harmonize_notes(
        melody,
        traversal=ChoiceTraversal.DEPTH_FIRST,
        max_solutions=1,
    )[0]

    assert solution.chords[:3] == ("degree_I", "degree_V", "degree_I")
    assert solution.melodic_roles[:3] == (
        "chord_tone",
        "chord_tone",
        "chord_tone",
    )
    d_voicing = solution.voicings[1]
    assert d_voicing[0] % 12 == 2
    assert {pitch % 12 for pitch in d_voicing} == {2, 7, 11}


def test_passing_tone_is_inferred_when_the_harmony_is_explicitly_held() -> None:
    melody = (72, 74, 76, 67, 65, 69, 71, 72)
    solution = harmonize_notes(
        melody,
        harmonic_rhythm=(0, 0, 1, 1, 2, 2, 3, 4),
        traversal=ChoiceTraversal.DEPTH_FIRST,
        max_solutions=1,
    )[0]

    assert solution.chords == (
        "degree_I",
        "degree_I",
        "degree_I",
        "degree_I",
        "degree_IV",
        "degree_IV",
        "degree_V",
        "degree_I",
    )
    assert solution.melodic_roles == (
        "chord_tone",
        "passing_tone",
        "chord_tone",
        "chord_tone",
        "chord_tone",
        "chord_tone",
        "chord_tone",
        "chord_tone",
    )
    passing_voicing = solution.voicings[1]
    assert passing_voicing[0] % 12 == 2
    assert {pitch % 12 for pitch in passing_voicing[1:]} == {0, 4, 7}
    assert any(
        event.rule_group == "derive_melodic_roles"
        and event.rule_name == "derive_ascending_passing_tone"
        for event in solution.inference_events
    )


@pytest.mark.parametrize(
    ("melody", "expected_role"),
    (
        ((72, 74, 72, 76, 65, 69, 71, 72), "upper_neighbor"),
        ((76, 74, 76, 67, 65, 69, 71, 72), "lower_neighbor"),
    ),
)
def test_neighbor_tone_candidates_are_generated_declaratively(
    melody: tuple[int, ...],
    expected_role: str,
) -> None:
    model = build_note_harmonizer_model(
        melody,
        harmonic_rhythm=(0, 0, 1, 1, 2, 2, 3, 4),
    )

    assert any(
        isinstance(fact.entity, Triple)
        and fact.entity.subject == model.positions[1]
        and fact.entity.relation == Atom("voicing_melodic_role")
        and isinstance(fact.entity.object, FiniteSequence)
        and fact.entity.object.elements[-1] == Atom(expected_role)
        for fact in model.csp.facts
    )


def test_harmonic_rhythm_and_cadence_are_validated() -> None:
    with pytest.raises(ValueError, match="one slot number per note"):
        build_note_harmonizer_model((71, 72), harmonic_rhythm=(0,))
    with pytest.raises(ValueError, match="contiguous"):
        build_note_harmonizer_model((72, 71, 72), harmonic_rhythm=(0, 2, 2))
    with pytest.raises(ValueError, match="at least two harmonic slots"):
        build_note_harmonizer_model((71, 72), harmonic_rhythm=(0, 0))
    with pytest.raises(ValueError, match="cadence must be"):
        build_note_harmonizer_model(
            (71, 72),
            cadence="unknown",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="one chord label per harmonic slot"):
        build_note_harmonizer_model(
            (71, 72),
            harmonic_plan=("V",),
        )
    with pytest.raises(ValueError, match="labels must be"):
        build_note_harmonizer_model(
            (71, 72),
            harmonic_plan=("V", "unknown"),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="mutually exclusive"):
        build_note_harmonizer_model(
            (71, 72),
            harmonic_plan=("V", "I"),
            harmonic_plan_profile="extended_tonal_arc",
        )
    with pytest.raises(ValueError, match="profile must be"):
        build_note_harmonizer_model(
            (71, 72),
            harmonic_plan_profile="unknown",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="no legal tonal SATB voicing"):
        build_note_harmonizer_model(
            (71, 72),
            harmonic_plan_profile="extended_tonal_arc",
        )
