from csp_solver.balanced_curriculum import (
    CURRICULUM_PREREQUISITE,
    DEFAULT_INSTANCE,
    schedule_from_solution,
    solve_balanced_curriculum,
    validate_schedule,
)
from csp_solver.balanced_graph_coloring import (
    COLORING_EDGE,
    TRIANGULAR_PRISM,
    coloring_from_solution,
    solve_balanced_graph_coloring,
    validate_coloring,
)
from csp_solver.car_sequencing import (
    sequence_from_solution,
    solve_car_sequencing,
    validate_sequence,
)
from csp_solver.golomb_ruler import (
    marks_from_solution,
    solve_golomb_ruler,
    validate_ruler,
)
from csp_solver.send_more_money import (
    solve_send_more_money,
    words_from_solution,
)
from snarky import Atom, ChoiceSearchStatus, Fact, Triple

KIND = Atom("kind")
STATE = Atom("state")
SATISFIED = Atom("satisfied")


def test_send_more_money_uses_the_unique_classical_solution() -> None:
    result = solve_send_more_money()

    assert result.status is ChoiceSearchStatus.SOLVED
    assert result.explored_nodes == 1
    assert words_from_solution(result.solutions[0]) == (9567, 1085, 10652)


def test_bounded_golomb_ruler_has_distinct_distances() -> None:
    result = solve_golomb_ruler(5, 11)

    assert result.status is ChoiceSearchStatus.SOLVED
    marks = marks_from_solution(result.solutions[0], 5, 11)
    assert marks[-1] <= 11
    assert validate_ruler(marks)


def test_classic_car_sequence_respects_demands_and_option_windows() -> None:
    result = solve_car_sequencing()

    assert result.status is ChoiceSearchStatus.SOLVED
    sequence = sequence_from_solution(result.solutions[0])
    assert validate_sequence(sequence)


def test_curriculum_constraints_and_rules_produce_a_valid_report() -> None:
    result = solve_balanced_curriculum()

    assert result.status is ChoiceSearchStatus.SOLVED
    solution = result.solutions[0]
    schedule = schedule_from_solution(solution)
    assert validate_schedule(schedule)
    prerequisites = {
        fact.entity.subject
        for fact in solution.session.facts
        if isinstance(fact.entity, Triple)
        and fact.entity.relation == KIND
        and fact.entity.object == CURRICULUM_PREREQUISITE
    }
    assert len(prerequisites) == len(DEFAULT_INSTANCE.prerequisites)
    assert all(
        Fact(Triple(prerequisite, STATE, SATISFIED))
        in solution.session.facts
        for prerequisite in prerequisites
    )


def test_balanced_coloring_constraints_and_rules_cover_every_edge() -> None:
    result = solve_balanced_graph_coloring()

    assert result.status is ChoiceSearchStatus.SOLVED
    solution = result.solutions[0]
    coloring = coloring_from_solution(solution)
    assert validate_coloring(coloring)
    edges = {
        fact.entity.subject
        for fact in solution.session.facts
        if isinstance(fact.entity, Triple)
        and fact.entity.relation == KIND
        and fact.entity.object == COLORING_EDGE
    }
    assert len(edges) == len(TRIANGULAR_PRISM.edges)
    assert all(
        Fact(Triple(edge, STATE, SATISFIED)) in solution.session.facts
        for edge in edges
    )
