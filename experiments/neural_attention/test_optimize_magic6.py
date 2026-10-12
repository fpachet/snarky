"""Value-order preservation and symmetry orbit coverage, independent of timing."""

from dataclasses import replace
from random import Random

import pytest

from benchmarks.alice_magic import build, validate
from experiments.neural_attention.optimize_magic6 import ordered_model, symmetry_model
from snarky.finite.model import Query, QueryKind
from snarky.finite.search import solve


@pytest.mark.parametrize("order", ["ascending", "middle", "ends", "random"])
def test_value_order_preserves_complete_small_solution_set(order):
    model, _ = build(3)
    changed = ordered_model(model, order, seed=812)
    assert changed.constraints == model.constraints
    assert changed.domains == model.domains
    expected = solve(model, Query(QueryKind.ENUMERATE))
    actual = solve(changed, Query(QueryKind.ENUMERATE))
    assert actual.complete and expected.complete
    assert {tuple(validate(3, s.assignment, model)) for s in actual.solutions} == {
        tuple(validate(3, s.assignment, model)) for s in expected.solutions
    }


def test_symmetry_retains_one_three_by_three_representative():
    model, _ = build(3)
    result = solve(symmetry_model(model, 3), Query(QueryKind.ENUMERATE))
    assert result.complete
    assert len(result.solutions) == 1
    validate(3, result.solutions[0].assignment, model)


def test_corner_canonicalization_covers_every_sampled_symmetry_orbit():
    rng = Random(617)
    for size in (3, 4, 5, 6, 7):
        for _ in range(50):
            board = rng.sample(range(1, size * size + 1), size * size)
            orbit = []
            current = [board[i * size : (i + 1) * size] for i in range(size)]
            for _turn in range(4):
                for transformed in (current, [row[::-1] for row in current]):
                    flat = [v for row in transformed for v in row]
                    orbit += [flat, [size * size + 1 - v for v in flat]]
                current = [list(row) for row in zip(*current[::-1], strict=True)]
            assert any(
                b[0] < min(b[size - 1], b[-size], b[-1])
                and b[size - 1] < b[-size]
                and b[0] <= (size * size + 1) // 2
                for b in orbit
            )


def test_symmetry_rejects_clued_and_other_constrained_models():
    model, _ = build(6)
    clued = replace(
        model,
        variables=(
            replace(model.variables[0], domain=(model.variables[0].domain[0],)),
            *model.variables[1:],
        ),
    )
    with pytest.raises(ValueError, match="blank"):
        symmetry_model(clued, 6)
    with pytest.raises(ValueError, match="blank"):
        symmetry_model(replace(model, constraints=model.constraints[:-1]), 6)
    with pytest.raises(ValueError, match="blank"):
        symmetry_model(replace(model, variables=model.variables[::-1]), 6)
