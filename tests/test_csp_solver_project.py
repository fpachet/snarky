from csp_solver.four_queens import (
    PROBLEM,
    n_queens_facts,
    solve_four_queens,
    solve_n_queens,
)
from csp_solver.solver import assignment_from_solution
from snarky import Atom, ChoiceSearchStatus


def test_four_queens_finds_the_two_expected_solutions() -> None:
    result = solve_four_queens()
    assignments = {
        tuple(
            assignment_from_solution(solution, PROBLEM)[
                Atom(f"queen_{column}")
            ].value
            for column in range(1, 5)
        )
        for solution in result.solutions
    }

    assert result.status is ChoiceSearchStatus.SOLVED
    assert assignments == {(2, 4, 1, 3), (3, 1, 4, 2)}


def test_n_queens_builder_handles_trivial_and_impossible_sizes() -> None:
    one = solve_n_queens(1)
    two = solve_n_queens(2)

    assert one.status is ChoiceSearchStatus.SOLVED
    assert two.status is ChoiceSearchStatus.EXHAUSTED
    assert n_queens_facts(5).problem == Atom("5_queens")
