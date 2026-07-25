from csp_solver.four_queens import (
    PROBLEM,
    n_queens_facts,
    n_queens_intensional_facts,
    solve_four_queens,
    solve_n_queens,
    solve_n_queens_intensional,
)
from csp_solver.latin_square import (
    latin_square_from_solution,
    solve_latin_square,
)
from csp_solver.magic_square import (
    magic_constant,
    magic_square_facts,
    solve_magic_square,
    square_from_solution,
)
from csp_solver.solver import BinaryCSP, FiniteCSP, assignment_from_solution
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


def test_binary_csp_name_remains_a_finite_csp_compatibility_alias() -> None:
    assert BinaryCSP is FiniteCSP


def test_reversible_and_forked_dfs_have_identical_search_semantics() -> None:
    reversible = solve_four_queens(reversible_depth_first=True)
    forked = solve_four_queens(reversible_depth_first=False)

    assert reversible.status is forked.status
    assert reversible.explored_nodes == forked.explored_nodes
    assert reversible.failed_branches == forked.failed_branches
    assert tuple(
        (solution.decisions, solution.log_weight, solution.session.facts)
        for solution in reversible.solutions
    ) == tuple(
        (solution.decisions, solution.log_weight, solution.session.facts)
        for solution in forked.solutions
    )
    assert tuple(event.kind for event in reversible.events) == tuple(
        event.kind for event in forked.events
    )


def test_intensional_queens_matches_extensional_oracle() -> None:
    extensional = solve_n_queens(4, max_solutions=2)
    intensional = solve_n_queens_intensional(4, max_solutions=2)

    assert intensional.status is extensional.status
    assert intensional.explored_nodes == extensional.explored_nodes
    assert intensional.failed_branches == extensional.failed_branches
    assert tuple(
        assignment_from_solution(solution, PROBLEM)
        for solution in intensional.solutions
    ) == tuple(
        assignment_from_solution(solution, PROBLEM)
        for solution in extensional.solutions
    )
    assert len(n_queens_intensional_facts(14).facts) == 253
    assert len(n_queens_facts(14).facts) == 15_513


def test_n_queens_builder_handles_trivial_and_impossible_sizes() -> None:
    one = solve_n_queens(1)
    two = solve_n_queens(2)

    assert one.status is ChoiceSearchStatus.SOLVED
    assert two.status is ChoiceSearchStatus.EXHAUSTED
    assert n_queens_facts(5).problem == Atom("5_queens")


def test_three_by_three_magic_square_is_normal_and_has_magic_lines() -> None:
    result = solve_magic_square(3)

    assert result.status is ChoiceSearchStatus.SOLVED
    square = square_from_solution(result.solutions[0], 3)
    target = magic_constant(3)
    values = [value for row in square for value in row]

    assert sorted(values) == list(range(1, 10))
    assert all(sum(row) == target for row in square)
    assert all(
        sum(square[row][column] for row in range(3)) == target
        for column in range(3)
    )
    assert sum(square[index][index] for index in range(3)) == target
    assert sum(square[index][2 - index] for index in range(3)) == target


def test_magic_square_builder_handles_parameterized_orders() -> None:
    one = solve_magic_square(1)
    two = solve_magic_square(2)

    assert square_from_solution(one.solutions[0], 1) == ((1,),)
    assert two.status is ChoiceSearchStatus.EXHAUSTED
    assert magic_constant(4) == 34
    assert magic_square_facts(4).problem == Atom("magic_square_4")


def test_reduced_latin_square_uses_global_line_constraints() -> None:
    result = solve_latin_square(5)

    assert result.status is ChoiceSearchStatus.SOLVED
    square = latin_square_from_solution(result.solutions[0], 5)
    expected = set(range(1, 6))
    assert all(set(row) == expected for row in square)
    assert all(
        {square[row][column] for row in range(5)} == expected
        for column in range(5)
    )
    assert square[0] == (1, 2, 3, 4, 5)
    assert tuple(row[0] for row in square) == (1, 2, 3, 4, 5)
