import pytest

from sudoku import (
    SudokuValidationError,
    candidates_from_facts,
    initial_facts,
    load_puzzle,
    validate_complete_grid,
)


@pytest.mark.parametrize("level", range(1, 7))
def test_native_fixtures_match_their_clips_sources(level: int) -> None:
    puzzle = load_puzzle(level)

    validate_complete_grid(puzzle.solution, clues=puzzle.grid)
    candidates = candidates_from_facts(initial_facts(puzzle))

    assert len(candidates) == 81
    for row in range(1, 10):
        for column in range(1, 10):
            clue = puzzle.grid[row - 1][column - 1]
            expected = {clue} if clue else set(range(1, 10))
            assert candidates[(row, column)] == expected


def test_independent_validator_rejects_a_corrupted_solution() -> None:
    puzzle = load_puzzle(1)
    corrupted = list(puzzle.solution)
    corrupted[0] = (corrupted[0][1], *corrupted[0][1:])

    with pytest.raises(SudokuValidationError):
        validate_complete_grid(tuple(corrupted), clues=puzzle.grid)
