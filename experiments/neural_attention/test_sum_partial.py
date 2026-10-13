"""Opt-in partial-sum prototypes preserve exact supports and sibling rollback."""

import importlib.util
from pathlib import Path
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import numeric
from snarky.finite.constraints import ConstraintOperator, LinearSumConstraint
from snarky.finite.model import FiniteModel, FiniteVariable
from snarky.finite.propagation import NativeState


@pytest.fixture(params=["baseline", "partial_edges"], autouse=True)
def experimental_kernel(request, monkeypatch):
    if request.param == "baseline":
        return
    source = (
        Path(__file__).resolve().parents[2]
        / "benchmarks/results/magic_sum_partial_2026-10-13/candidate_edges.py"
    )
    spec = importlib.util.spec_from_file_location(
        "snarky.finite._partial_candidate_test", source
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        numeric.NumericPlan, "_equality_supports", module.NumericPlan._equality_supports
    )


def make_model(values, coefficients, target):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, v)))
        for i, v in enumerate(values)
    )
    constraint = LinearSumConstraint(
        Atom("sum"),
        tuple(zip(coefficients, (v.name for v in variables), strict=True)),
        ConstraintOperator.EQUAL,
        target,
    )
    return FiniteModel("partial_sum", variables, (constraint,))


@pytest.mark.parametrize("missing,target,unsupported", [(1, 20, 19), (19, 60, 1)])
@pytest.mark.parametrize("coefficients", [[1] * 4, [-1, 1, -1, 1]])
def test_partially_certified_values_still_support_other_variables(
    missing, target, unsupported, coefficients
):
    rng = Random(131027)
    contributions = [v for v in range(21) if v != missing]
    values = []
    for i, coefficient in enumerate(coefficients):
        alphabet = [
            coefficient * (v + (10**40 if i == 0 else 0)) for v in contributions
        ]
        rng.shuffle(alphabet)
        values.append(alphabet)
    model = make_model(values, coefficients, target + 10**40)
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    roots = [s.checkpoint() for s in (fast, slow)]
    for visit in range(3):
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            if visit == 1:
                state.restrict(model.variables[0].name, Number(values[0][0]))
        assert fast.propagate() == slow.propagate()
        assert fast.domains.snapshot() == slow.domains.snapshot()
        assert fast.domains.removals == slow.domains.removals
        assert fast.revisions == slow.revisions
        if visit != 1:
            for i, variable in enumerate(model.variables):
                live = {
                    coefficients[i] * v.value - (10**40 if i == 0 else 0)
                    for v in fast.domains.values(variable.name)
                }
                assert live == set(contributions) - {unsupported}
                # These boundary values need the certified interior candidates
                # of other variables to remain in backward reachability.
                assert 0 in live and 20 in live
    for state, root in zip((fast, slow), roots, strict=True):
        state.rollback(root)
        state.release(root)
        assert state.domains.snapshot() == model.domains


def test_partial_certification_with_zero_margin_matches_reference_bounds():
    model = make_model([list(range(31))] * 4 + [[0, 50]], [1] * 5, 29)
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    assert fast.propagate() == slow.propagate()
    assert fast.domains.snapshot() == slow.domains.snapshot()
    assert fast.domains.removals == slow.domains.removals
    assert fast.domains.values(model.variables[-1].name) == (Number(0),)


def test_partial_edge_reachability_matches_independent_set_sum_oracle():
    rng = Random(131028)
    for case in range(120):
        count = rng.randrange(4, 8)
        alphabets = []
        for _ in range(count):
            width = rng.randrange(20, 33)
            alphabet = list(range(width + 1))
            for value in rng.sample(range(1, width), rng.randrange(1, 3)):
                alphabet.remove(value)
            rng.shuffle(alphabet)
            alphabets.append(alphabet)
        widths = [max(a) for a in alphabets]
        target = max(widths) + rng.randrange(-3, 3)
        if case % 2:
            target = sum(widths) - target
        coefficients = [rng.choice((-1, 1)) for _ in alphabets]
        values = [
            [c * (v + (10**40 if i == 0 else 0)) for v in alphabet]
            for i, (c, alphabet) in enumerate(zip(coefficients, alphabets, strict=True))
        ]
        model = make_model(values, coefficients, target + 10**40)
        state = NativeState(model)
        plan = state._numeric.get(0, model.constraints[0])
        assert plan is not None
        expected = []
        for i, alphabet in enumerate(alphabets):
            sums = {0}
            for j, other in enumerate(alphabets):
                if j != i:
                    sums = {a + b for a in sums for b in other}
            expected.append(
                sum(
                    1 << k for k, value in enumerate(alphabet) if target - value in sums
                )
            )
        assert plan.supports(state.domains, target + 10**40) == tuple(expected)
