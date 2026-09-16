"""Independent support oracles for both representations of integer equality."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import FiniteModel, FiniteVariable, kernels
from snarky.finite.constraints import (
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.propagation import NativeState


def assert_supports(raw, coefficients, target, *, plain_sum=False):
    names = tuple(Atom(f"x{i}") for i in range(len(raw)))
    domains = {
        name: set(map(Number, values)) for name, values in zip(names, raw, strict=True)
    }
    expected = {name: set() for name in names}
    found = False
    for row in product(*raw):
        if sum(c * x for c, x in zip(coefficients, row, strict=True)) == target:
            found = True
            for name, value in zip(names, row, strict=True):
                expected[name].add(Number(value))
    if plain_sum:
        constraint = SumConstraint(Atom("sum"), names, target)
        valid = kernels._revise_sum(constraint, domains)
    else:
        constraint = LinearSumConstraint(
            Atom("weighted"),
            tuple(zip(coefficients, names, strict=True)),
            ConstraintOperator.EQUAL,
            target,
        )
        valid = kernels._revise_linear_sum(constraint, domains)
    assert valid == found
    if valid:
        assert domains == expected
    return constraint, names, expected


@pytest.mark.parametrize("representation", ["default", "sparse"])
def test_signed_holey_equalities_against_complete_assignment_oracle(
    monkeypatch, representation
):
    if representation == "sparse":
        monkeypatch.setattr(kernels, "_EQUALITY_MAX_BITS", 0)
    rng = Random(93178)
    for _ in range(300):
        arity = rng.randrange(3, 7)
        raw = [rng.sample(range(-8, 10), rng.randrange(1, 4)) for _ in range(arity)]
        coefficients = [rng.choice([-11, -4, -1, 1, 3, 7]) for _ in raw]
        target = sum(c * rng.choice(d) for c, d in zip(coefficients, raw, strict=True))
        if rng.randrange(2):
            target += rng.randrange(-3, 4)
        assert_supports(raw, coefficients, target)
        assert_supports(
            raw, [1] * arity, sum(rng.choice(d) for d in raw), plain_sum=True
        )


def test_large_offsets_large_common_divisors_and_sparse_huge_spans():
    huge = 10**80
    cases = [
        ([[huge, huge + 1, huge + 4]] * 4, [2, -3, 5, 7], 11 * huge + 8),
        ([[0, huge, 3 * huge]] * 4, [2, -3, 5, 7], 9 * huge),
        ([[0, huge, 3 * huge]] * 4, [2, -3, 5, 7], 9 * huge + 1),
        ([[0, huge + 1], [0, huge], [0, huge - 1]], [1, -1, 1], 0),
        ([[-huge, 0, huge], [-huge - 1, 0, huge + 1], [-1, 0, 1]], [1, 1, -1], 0),
    ]
    for raw, coefficients, target in cases:
        assert_supports(raw, coefficients, target)


@pytest.mark.parametrize("target", [-100, -18, -17, 0, 15, 17, 18, 100])
def test_lower_upper_and_infeasible_targets(target):
    assert_supports([[-3, -1, 2], [-2, 0, 3], [-1, 1, 4]], [3, -2, 1], target)
    assert_supports([[4], [-3], [9]], [2, -2, -1], target)


def test_bitset_storage_budget_falls_back_without_changing_supports(monkeypatch):
    monkeypatch.setattr(kernels, "_EQUALITY_TOTAL_BITS", 0)
    assert_supports([[0, 1, 3], [-2, 1, 4], [-1, 0, 5]], [2, -3, 4], 3)


def test_nested_rollback_and_siblings_for_long_weighted_equality():
    raw = [[-3, 0, 4], [-2, 1, 5], [-4, 0, 2], [-2, 0, 3]]
    coefficients = [2, -3, 5, -7]
    constraint, names, _ = assert_supports(raw, coefficients, 0)
    model = FiniteModel(
        "weighted_rollback",
        tuple(
            FiniteVariable(name, tuple(map(Number, values)))
            for name, values in zip(names, raw, strict=True)
        ),
        (constraint,),
    )
    state = NativeState(model)
    original = state.domains.snapshot()
    outer = state.checkpoint()
    for first in raw[0] + raw[0][::-1]:
        state.restrict(names[0], Number(first))
        valid = state.propagate()
        _, _, supported = assert_supports([[first], *raw[1:]], coefficients, 0)
        assert valid == all(supported.values())
        if valid:
            assert state.domains.snapshot() == supported
            inner = state.checkpoint()
            before = state.domains.snapshot()
            for second in tuple(state.domains.values(names[1])):
                state.restrict(names[1], second)
                state.propagate()
                state.rollback(inner)
                assert state.domains.snapshot() == before
            state.release(inner)
        state.rollback(outer)
        assert state.domains.snapshot() == original and not state.domains.removals
    state.release(outer)
