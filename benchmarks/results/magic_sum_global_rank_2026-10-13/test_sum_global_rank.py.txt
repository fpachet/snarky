"""Whole-system exact rank and partial deductions against rational elimination."""

from fractions import Fraction
from random import Random

import pytest

from benchmarks.alice_magic import build
from snarky import Number

from .sum_global_rank import assess, eliminate, extract
from .sum_systems import Equation, factor


def equation(coefficients, target):
    return Equation(
        tuple((c, i) for i, c in enumerate(coefficients) if c),
        target,
        sum(1 << i for i, c in enumerate(coefficients) if c),
    )


@pytest.mark.parametrize("size", [3, 4, 8, 16])
def test_initial_magic_rank_and_freedom(size):
    model, _ = build(size)
    report = assess(
        extract(model),
        tuple(v.domain for v in model.variables),
        tuple((1 << len(v.domain)) - 1 for v in model.variables),
    )
    assert report["rank"] == 2 * size + 1
    assert report["freedom"] == size * size - 2 * size - 1
    if size == 3:
        assert [(r["variable"], r["value"]) for r in report["forced"]] == [(4, "5")]
    else:
        assert not report["forced"]


def test_underdetermined_system_can_force_one_variable():
    equations = (equation([1, 1, 0], 10), equation([1, 1, 1], 13))
    report = assess(equations, (tuple(map(Number, range(21))),) * 3, (2**21 - 1,) * 3)
    assert report["rank"] == 2 and report["freedom"] == 1
    assert not report["fully_determined"]
    assert [(r["variable"], r["value"]) for r in report["forced"]] == [(2, "3")]


def test_nine_variables_can_be_uniquely_determined():
    equations = []
    for i in range(8):
        coefficients = [0] * 9
        coefficients[i], coefficients[i + 1] = 1, -1
        equations.append(equation(coefficients, -1))
    equations.append(equation([1] * 9, 45))
    report = assess(equations, (tuple(map(Number, range(21))),) * 9, (2**21 - 1,) * 9)
    assert report["fully_determined"] and report["rank"] == 9
    assert {r["variable"]: r["value"] for r in report["forced"]} == {
        i: str(i + 1) for i in range(9)
    }


def test_rational_and_integer_inconsistency_are_distinguished():
    alphabets = (tuple(map(Number, range(5))),) * 2
    report = assess((equation([1, 1], 2), equation([2, 2], 5)), alphabets, (31, 31))
    assert report["rational_inconsistent"]
    report = assess((equation([1, 1], 1), equation([1, -1], 0)), alphabets, (31, 31))
    assert not report["rational_inconsistent"] and report["integer_contradiction"]
    assert all(r["value"] == "1/2" for r in report["forced"])


def test_same_structural_plan_uses_current_singleton_values():
    equations = (equation([1, 1, -1], 0), equation([1, 1, 0], 10))
    alphabets = (tuple(map(Number, range(21))),) * 3
    plan = eliminate(equations, 3)
    assert not assess(equations, alphabets, (2**21 - 1, 2**21 - 1, 1 << 10), plan)[
        "rational_inconsistent"
    ]
    assert assess(equations, alphabets, (2**21 - 1, 2**21 - 1, 1 << 11), plan)[
        "rational_inconsistent"
    ]


def test_unconstrained_variables_are_counted_as_free():
    report = assess(
        (equation([1, 0], 2),), (tuple(map(Number, range(5))),) * 2, (31, 31)
    )
    assert report["rank"] == 1 and report["freedom"] == 1
    assert not report["fully_determined"]


def test_sparse_integer_elimination_matches_independent_rational_rref():
    rng = Random(131031)
    for case in range(400):
        count, equations_count = rng.randrange(1, 8), rng.randrange(1, 11)
        equations = []
        for _ in range(equations_count):
            coefficients = [
                rng.choice([-3, -2, -1, 0, 0, 1, 2, 3]) for _ in range(count)
            ]
            if case % 7 == 0:
                coefficients[0] *= 10**20
            equations.append(equation(coefficients, rng.randrange(-10, 11)))
        unresolved = rng.randrange(1 << count)
        rows, proofs, rank = eliminate(equations, unresolved)
        reference = factor(equations, (1 << equations_count) - 1, unresolved)
        assert rank == len(reference.pivots)
        for row, proof in zip(rows, proofs, strict=True):
            expected = {
                v: sum(
                    multiplier * dict((v, c) for c, v in equations[i].terms).get(v, 0)
                    for i, multiplier in proof.items()
                )
                for v in range(count)
                if unresolved & (1 << v)
            }
            assert row == {v: c for v, c in expected.items() if c}
        alphabets = (tuple(map(Number, range(-3, 4))),) * count
        masks = tuple(
            127 if unresolved & (1 << v) else 1 << rng.randrange(7)
            for v in range(count)
        )
        report = assess(equations, alphabets, masks, (rows, proofs, rank))
        targets = [
            e.target
            - sum(
                c * alphabets[v][masks[v].bit_length() - 1].value
                for c, v in e.terms
                if not unresolved & (1 << v)
            )
            for e in equations
        ]
        expected_forced = {}
        inconsistent = False
        for row, proof in zip(reference.reduced, reference.transform, strict=True):
            rhs = sum(c * t for c, t in zip(proof, targets, strict=True))
            nonzero = [
                (v, c) for v, c in zip(reference.variables, row, strict=True) if c
            ]
            if not nonzero:
                inconsistent |= bool(rhs)
            if len(nonzero) == 1:
                v, c = nonzero[0]
                expected_forced[v] = Fraction(rhs, c)
        assert report["rational_inconsistent"] == inconsistent
        if not inconsistent:
            assert {
                r["variable"]: Fraction(r["value"]) for r in report["forced"]
            } == expected_forced
