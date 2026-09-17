"""Exact assignment bounds checked against independent permutation enumeration."""

from dataclasses import replace
from fractions import Fraction
from itertools import permutations, product
from math import prod
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    RationalProductObjective,
    ResultStatus,
    WeightTable,
    enumerate_model,
    solve,
)
from snarky.finite.bounds import compile_objective_bound
from snarky.finite.constraints import AllDifferentConstraint
from snarky.finite.product_assignment import (
    ProductPermutationBound,
    maximum_product_assignment,
    supports_product_permutation,
)


@pytest.mark.parametrize("seed", range(16))
def test_multiplicative_matching_equals_exhaustive_assignment(seed):
    rng = Random(seed)
    for n in range(7):
        weights = [
            [Fraction(rng.randrange(6), rng.randrange(1, 8)) for _ in range(n)]
            for _ in range(n)
        ]
        expected = max(
            (
                prod((weights[i][j] for i, j in enumerate(p)), start=Fraction(1))
                for p in permutations(range(n))
            ),
            default=Fraction(1),
        )
        assert maximum_product_assignment(weights) == expected


def test_assignment_handles_hall_failure_zero_rows_near_ties_and_timeout():
    assert maximum_product_assignment([[1, 0, 0], [1, 0, 0], [0, 1, 1]]) == 0
    assert maximum_product_assignment([[1, 1], [0, 0]]) == 0
    epsilon = Fraction(1, 10**50)
    assert maximum_product_assignment([[1, 1 + epsilon], [1, 1]]) == 1 + epsilon
    with pytest.raises(ValueError, match="square"):
        maximum_product_assignment([[1, 2]])
    with pytest.raises(ValueError, match="nonnegative"):
        maximum_product_assignment([[-1]])
    with pytest.raises(TimeoutError):
        maximum_product_assignment([[1]], deadline=0)


def permutation_model(seed):
    rng = Random(seed)
    names = tuple(Atom(f"x{i}") for i in range(6))
    values = tuple(map(Number, range(6)))
    factors = [WeightTable("constant", (), {(): Fraction(seed % 3, 2)})]
    # Position-dependent edges, defaults, zeros, >1 weights and multiple factors
    # per layer prevent assumptions about a stationary stochastic matrix.
    for i in range(5):
        factors.append(
            WeightTable(
                str(i),
                names[i : i + 2],
                {
                    row: Fraction(rng.randrange(5), rng.randrange(1, 6))
                    for row in product(values, repeat=2)
                    if rng.random() < 0.7
                },
                default=Fraction(seed % 2, 3),
            )
        )
    for i in range(6):
        factors.append(
            WeightTable(
                f"unary{i}",
                names[i : i + 1],
                {(value,): Fraction(rng.randrange(1, 5), 3) for value in values},
            )
        )
    return FiniteModel(
        "permutation",
        tuple(
            FiniteVariable(
                v, values[:1] if i == 0 else values[-1:] if i == 5 else values
            )
            for i, v in enumerate(names)
        ),
        (AllDifferentConstraint(Atom("distinct"), names),),
        objective=RationalProductObjective(tuple(factors)),
    )


@pytest.mark.parametrize("seed", range(12))
def test_residual_bounds_and_search_equal_independent_permutation_scores(seed):
    model = permutation_model(seed)
    bound = compile_objective_bound(model)
    assert isinstance(bound, ProductPermutationBound)
    names = tuple(v.name for v in model.variables)
    values = tuple(map(Number, range(6)))

    def direct(row):
        assignment = dict(zip(names, row, strict=True))
        return prod(
            (
                factor.values.get(
                    tuple(assignment[v] for v in factor.variables), factor.default
                )
                for factor in model.objective.factors
            ),
            start=Fraction(1),
        )

    # Includes empty domains, duplicate singleton assignments, holes and branches
    # revisited in a different order. Only all-different feasible rows count.
    for domain in ((), values[:1], values[1:3], values[3:5], values[-1:]):
        domains = dict(model.domains)
        domains[names[2]] = frozenset(domain)
        candidates = [
            direct(row)
            for row in permutations(values)
            if all(x in domains[v] for v, x in zip(names, row, strict=True))
        ]
        low, high = bound(domains)
        assert low == 0 and high >= max(candidates, default=Fraction(0))
    for row in permutations(values[1:5]):
        row = (values[0], *row, values[-1])
        domains = {v: frozenset((x,)) for v, x in zip(names, row, strict=True)}
        assert bound(domains)[1] == direct(row)
    expected = [direct((values[0], *p, values[-1])) for p in permutations(values[1:5])]
    for kind, choose in ((QueryKind.MINIMIZE, min), (QueryKind.MAXIMIZE, max)):
        for ordering in (None, names[::-1]):
            result = solve(
                model, Query(kind), variable_order=ordering, value_policy="objective"
            )
            assert result.status is ResultStatus.OPTIMAL
            assert (
                result.incumbent.objective_value
                == result.objective_bound
                == choose(expected)
            )
        assert enumerate_model(model, Query(kind)).incumbent.objective_value == choose(
            expected
        )


def test_permutation_recognition_requires_whole_alphabet_and_hard_distinctness():
    model = permutation_model(1)
    assert supports_product_permutation(model)
    assert not supports_product_permutation(model, max_symbols=5)
    assert not supports_product_permutation(replace(model, constraints=()))
    assert not supports_product_permutation(
        replace(
            model,
            variables=(
                replace(model.variables[0], domain=model.variables[1].domain),
                *model.variables[1:],
            ),
        )
    )
    assert not supports_product_permutation(
        replace(
            model,
            variables=(
                *model.variables[:-1],
                replace(model.variables[-1], domain=model.variables[0].domain),
            ),
        )
    )
    extra = Number(99)
    assert not supports_product_permutation(
        replace(
            model,
            variables=(
                model.variables[0],
                replace(model.variables[1], domain=(*model.variables[1].domain, extra)),
                *model.variables[2:],
            ),
        )
    )
    assert not isinstance(
        compile_objective_bound(model, max_window=0), ProductPermutationBound
    )
