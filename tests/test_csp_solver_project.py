from csp_solver.four_queens import PROBLEM, solve_four_queens
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
