"""Exact support oracles for fast arithmetic, including holes and huge integers."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import FiniteModel, FiniteVariable
from snarky.finite.constraints import (
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.kernels import _revise_binary_comparison, _revise_linear_sum
from snarky.finite.propagation import NativeState


def check_linear(domains, coefficients, target, operator):
    names = tuple(Atom(f"x{i}") for i in range(len(domains)))
    original = {v: set(map(Number, d)) for v, d in zip(names, domains, strict=True)}
    expected = {v: set() for v in names}
    for row in product(*domains):
        total = sum(c * x for c, x in zip(coefficients, row, strict=True))
        if {
            ConstraintOperator.EQUAL: total == target,
            ConstraintOperator.LESS_EQUAL: total <= target,
            ConstraintOperator.GREATER_EQUAL: total >= target,
        }[operator]:
            for v, x in zip(names, row, strict=True):
                expected[v].add(Number(x))
    constraint = LinearSumConstraint(
        Atom("linear"), tuple(zip(coefficients, names, strict=True)), operator, target
    )
    actual = {v: set(d) for v, d in original.items()}
    valid = _revise_linear_sum(constraint, actual)
    assert valid == all(expected.values())
    if valid:
        assert actual == expected
    return names, original, constraint


@pytest.mark.parametrize("operator", list(ConstraintOperator))
def test_linear_supported_values_match_exhaustive_signed_holey_oracle(operator):
    rng = Random(2138)
    for _ in range(350):
        arity = rng.randrange(1, 5)
        domains = [rng.sample(range(-5, 7), rng.randrange(1, 5)) for _ in range(arity)]
        coefficients = [rng.choice((-7, -3, -1, 1, 2, 5)) for _ in range(arity)]
        check_linear(domains, coefficients, rng.randrange(-25, 26), operator)


@pytest.mark.parametrize("operator", list(ConstraintOperator))
def test_large_integer_arithmetic_and_empty_domains(operator):
    huge = 10**60
    for target in (-huge, 0, huge, huge + 1):
        check_linear([[-huge, -1, huge], [0, 2, huge]], [-3, 7], target, operator)
        check_linear([[-huge, huge]], [-huge], target, operator)
    check_linear([[], [0, 1]], [1, -1], 0, operator)


@pytest.mark.parametrize("operator", list(BinaryComparisonOperator))
def test_binary_supported_values_match_cartesian_oracle(operator):
    x, y = Atom("x"), Atom("y")
    # Disequality also permits symbolic values; ordered comparisons permit floats.
    alphabet = (
        [Atom("a"), Atom("b"), Number(0), Number(2)]
        if operator is BinaryComparisonOperator.NOT_EQUAL
        else list(map(Number, [-(10**20), -0.25, 0, 0.5, 10**20]))
    )
    subsets = [
        {v for i, v in enumerate(alphabet) if mask & (1 << i)}
        for mask in range(1 << len(alphabet))
    ]
    for left, right in product(subsets, repeat=2):
        supported = [
            (a, b)
            for a, b in product(left, right)
            if (
                a != b
                if operator is BinaryComparisonOperator.NOT_EQUAL
                else a.value <= b.value
                if operator is BinaryComparisonOperator.LESS_EQUAL
                else a.value < b.value
            )
        ]
        domains = {x: set(left), y: set(right)}
        c = BinaryComparisonConstraint(Atom("binary"), x, y, operator)
        assert _revise_binary_comparison(c, domains) == bool(supported)
        if supported:
            assert domains == {
                x: {a for a, b in supported},
                y: {b for a, b in supported},
            }


@pytest.mark.parametrize("operator", list(ConstraintOperator))
def test_arithmetic_repeated_sibling_rollback(operator):
    names, original, constraint = check_linear(
        [[-3, 0, 4], [-2, 1, 5]], [2, -3], 3, operator
    )
    model = FiniteModel(
        "rollback",
        tuple(FiniteVariable(v, tuple(original[v])) for v in names),
        (constraint,),
    )
    state = NativeState(model)
    root = state.checkpoint()
    for value in (-3, 4, 0, -3):
        state.restrict(names[0], Number(value))
        state.propagate()
        state.rollback(root)
        assert state.domains.snapshot() == original and state.domains.removals == ()
    state.release(root)
