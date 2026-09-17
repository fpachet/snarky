"""Check benchmark transformations against complete small solution sets."""

from benchmarks.alice_magic import VARIANTS, derive, prepare, validate
from snarky.finite.model import Query, QueryKind
from snarky.finite.search import solve


def test_all_variants_preserve_all_eight_three_by_three_squares():
    solution_sets = []
    for variant in VARIANTS:
        model, _ = prepare(3, variant)
        result = solve(model, Query(kind=QueryKind.ENUMERATE))
        assert result.complete
        squares = {
            tuple(validate(3, solution.assignment, model))
            for solution in result.solutions
        }
        assert len(squares) == 8
        solution_sets.append(squares)
    assert solution_sets[0] == solution_sets[1] == solution_sets[2]


def test_cancellation_derives_singleton_with_checkable_proof():
    originals = [(1, 1, 1, 10), (1, 1, 0, 7)]
    for variant in VARIANTS[1:]:
        results = dict(derive(originals, variant))
        assert (0, 0, 1, 3) in results
        assert tuple(results[(0, 0, 1, 3)]) == (1, -1)
