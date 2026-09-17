"""Sparse compilation remains an admissible bound under changing domains."""

from dataclasses import replace
from fractions import Fraction
from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    RationalProductObjective,
    TableFactor,
    WeightTable,
)
from snarky.finite.bounds import NoObjectiveCompletion, compile_objective_bound
from snarky.finite.constraints import TableConstraint
from snarky.finite.product_objective import ProductChainBound, supports_product_chain
from snarky.finite.sparse_chain import SparseSumChainBound, supports_sparse_sum


@pytest.mark.parametrize("seed", range(8))
def test_sparse_sum_bounds_match_direct_paths_including_negative_scores(seed):
    rng = Random(seed)
    x, y, z = map(Atom, ("x", "y", "z"))
    values = tuple(map(Number, range(4)))
    rows = tuple(row for row in product(values, repeat=2) if rng.random() < 0.4)
    model = FiniteModel(
        "sparse",
        tuple(FiniteVariable(v, values) for v in (x, y, z)),
        (TableConstraint(Atom("reversed"), (y, x), rows),),
        objective=FactorObjective(
            (
                TableFactor(
                    "xy",
                    (x, y),
                    {row: rng.randrange(-10, 10) for row in product(values, repeat=2)},
                    default=-3,
                ),
                TableFactor("z", (z,), {(v,): rng.randrange(-10, 10) for v in values}),
                TableFactor("constant", (), {(): -7}),
            ),
            offset=9,
        ),
    )
    bound = SparseSumChainBound(model)
    assert supports_sparse_sum(model, 100)
    assert not supports_sparse_sum(model, 1)
    for xs in (values, values[::2], values[1::2]):
        for ys in (values, values[:1], values[-1:]):
            domains = {x: frozenset(xs), y: frozenset(ys), z: frozenset(values[1:])}
            feasible = [
                model.objective.evaluate(dict(zip((x, y, z), row, strict=True)))
                for row in product(xs, ys, values[1:])
                if (row[1], row[0]) in rows
            ]
            if feasible:
                assert bound(domains) == (min(feasible), max(feasible))
            else:
                with pytest.raises(NoObjectiveCompletion):
                    bound(domains)
    with pytest.raises(TimeoutError):
        SparseSumChainBound(model, deadline=0)
    bound.deadline = 0
    with pytest.raises(TimeoutError):
        bound({v: frozenset(values) for v in (x, y, z)})


def test_sparse_product_support_reversed_scope_and_zero_defaults():
    values = tuple(map(Number, range(400)))
    x, y = Atom("x"), Atom("y")
    sparse = WeightTable(
        "sparse", (y, x), {(v, v): Fraction(i, 400) for i, v in enumerate(values)}
    )
    multiplier = WeightTable(
        "multiply", (x,), {(v,): 2 for v in values[::2]}, default=1
    )
    model = FiniteModel(
        "large sparse",
        tuple(FiniteVariable(v, values) for v in (x, y)),
        objective=RationalProductObjective((sparse, multiplier)),
    )
    assert supports_product_chain(model, 1000)
    assert not supports_product_chain(model, 1)
    assert isinstance(compile_objective_bound(model, max_edges=1000), ProductChainBound)
    bound = compile_objective_bound(model, max_edges=1000)
    domains = {x: frozenset(values[:100]), y: frozenset(values[::3])}
    expected = max(
        Fraction(i, 400) * (2 if i % 2 == 0 else 1) for i in range(100) if i % 3 == 0
    )
    assert bound(domains) == (0, expected)
    assert bound({x: frozenset(values[:1]), y: frozenset(values[:1])}) == (0, 0)
    assert not supports_product_chain(
        replace(
            model, objective=RationalProductObjective((replace(sparse, default=1),))
        ),
        1000,
    )
    with pytest.raises(TimeoutError):
        ProductChainBound(model, deadline=0)
