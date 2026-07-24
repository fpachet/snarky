from csp_solver.solver import solve_binary_csp
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
    assert len(
        build_harmonizer_model(
            intensional_transitions=False
        ).csp.facts
    ) == 401
    assert len(
        build_harmonizer_model(
            intensional_transitions=True
        ).csp.facts
    ) == 32
