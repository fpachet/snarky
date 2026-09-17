"""The optional native-global CLAIRE comparison keeps the queens problem exact."""

from itertools import permutations

import pytest

from benchmarks.claire_n_queens import validate_solution
from benchmarks.claire_refresh import native_queens_model
from snarky.finite import Query, QueryKind, solve


@pytest.mark.parametrize("size", [1, 2, 3, 4, 5])
def test_global_queens_has_exactly_the_independent_board_solutions(size):
    expected = set()
    for row in permutations(range(1, size + 1)):
        try:
            validate_solution(size, row)
        except ValueError:
            continue
        expected.add(row)
    model, names = native_queens_model(size)
    result = solve(model, Query(QueryKind.ENUMERATE), policy="mrv")
    assert result.complete
    actual = [tuple(s.assignment[v].value for v in names) for s in result.solutions]
    assert len(actual) == len(set(actual))
    assert set(actual) == expected


def test_nonpositive_queens_size_rejected():
    with pytest.raises(ValueError, match="positive"):
        native_queens_model(0)
