from csp_solver.solver import solve_binary_csp
from harmonizer import (
    build_note_harmonizer_model,
    harmonize_notes,
    sample_harmonization,
)
from harmonizer.solver import build_harmonizer_model, harmonize
from snarky import ChoiceTraversal


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

    assert model.generated_voicings == (26, 30, 7, 26)
    assert model.program.manifest() == (
        ("preparation", ("generate_candidate_voicings",)),
        ("choice", ("apply_csp_choices",)),
        (
            "propagation",
            (
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
        solution.chords == ("degree_I", "degree_IV", "degree_V", "degree_I")
        for solution in solutions
    )
    assert solutions[0].voicings == (
        (72, 64, 55, 48),
        (69, 60, 57, 41),
        (71, 59, 50, 43),
        (72, 64, 55, 36),
    )
    assert all(
        decision.point.startswith("apply_csp_choices:choose_csp_value:")
        for solution in solutions
        for decision in solution.decisions
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
        event.rule_group == "enforce_tonal_form"
        for event in solutions[0].inference_events
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
    melody = (72, 72, 67, 67, 72)
    solution = harmonize_notes(melody, max_solutions=1)[0]

    assert solution.chords == (
        "degree_I",
        "degree_IV",
        "degree_I",
        "degree_V",
        "degree_I",
    )
    assert solution.inversions == (
        "root",
        "root",
        "first",
        "root",
        "root",
    )
    assert any(
        "variable=harmony_1_chord]" in decision.point for decision in solution.decisions
    )
    chord_pitch_classes = {
        "degree_I": {0, 4, 7},
        "degree_ii": {2, 5, 9},
        "degree_IV": {0, 5, 9},
        "degree_V": {2, 7, 11},
        "degree_vi": {0, 4, 9},
    }
    for chord, voicing in zip(
        solution.chords,
        solution.voicings,
        strict=True,
    ):
        assert {pitch % 12 for pitch in voicing} == chord_pitch_classes[chord]
    first_inversion_index = solution.inversions.index("first")
    assert solution.voicings[first_inversion_index][3] % 12 == 4
