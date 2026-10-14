"""Exact support and state-equivalence checks for the opt-in SUM C kernel."""

from collections import Counter
from itertools import product
from random import Random
from shutil import which

import pytest

from snarky import Atom, Number
from snarky.finite.constraints import ConstraintOperator, LinearSumConstraint
from snarky.finite.domains import FiniteDomains
from snarky.finite.model import FiniteModel, FiniteVariable, Query
from snarky.finite.numeric import NumericColumn, NumericPlan
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .sum_kernel import NativeEqualityPlan, SumKernel, enable


@pytest.fixture(scope="module")
def kernel(tmp_path_factory):
    if which("cc") is None:
        pytest.skip("SUM kernel experiment requires cc")
    return SumKernel.build(tmp_path_factory.mktemp("sum_kernel") / "sum.so")[0]


def plans(kernel, values):
    columns = tuple(NumericColumn(Atom(f"x{i}"), v) for i, v in enumerate(values))
    python = NumericPlan(columns, ConstraintOperator.EQUAL)
    native = NativeEqualityPlan(python, kernel, Counter())
    return python, native


def oracle(values, masks, target):
    positions = [
        [j for j in range(len(v)) if mask & (1 << j)]
        for v, mask in zip(values, masks, strict=True)
    ]
    supported = [0] * len(values)
    found = False
    for choices in product(*positions):
        if sum(v[j] for v, j in zip(values, choices, strict=True)) == target:
            found = True
            for i, j in enumerate(choices):
                supported[i] |= 1 << j
    return tuple(supported) if found else None


@pytest.mark.parametrize("seed", [141026, 151026, 161026])
def test_full_supports_against_exhaustive_signed_holey_oracle(kernel, seed):
    rng = Random(seed)
    for trial in range(150):
        columns = []
        for _ in range(rng.randrange(1, 7)):
            coefficient = rng.choice((-3, -1, 1, 2))
            offset = 10**70 * rng.randrange(-2, 3) if trial % 4 == 0 else 0
            columns.append(
                tuple(
                    offset + coefficient * v
                    for v in rng.sample(range(-8, 12), rng.randrange(1, 5))
                )
            )
        values = tuple(columns)
        python, native = plans(kernel, values)
        for _ in range(4):
            masks = tuple(rng.randrange(1, 1 << len(v)) for v in values)
            target = sum(
                v[(m & -m).bit_length() - 1] for v, m in zip(values, masks, strict=True)
            ) + rng.randrange(-5, 6)
            expected = oracle(values, masks, target)
            assert python._equality_supports(masks, target) == expected
            assert native._equality_supports(masks, target) == expected


@pytest.mark.parametrize("target", [8191, 8192, 8193, 16384, -1, 16385])
def test_maximum_span_reflection_and_word_edges(kernel, target):
    values = ((0, 8192), (4096, 0), (0, 4096))
    python, native = plans(kernel, values)
    assert (
        native._equality_supports((3, 3, 3), target)
        == python._equality_supports((3, 3, 3), target)
        == oracle(values, (3, 3, 3), target)
    )


def test_large_candidate_masks_and_repeated_restores(kernel):
    values = tuple(tuple(range(4096)) for _ in range(3))
    python, native = plans(kernel, values)
    masks = tuple(
        sum(1 << p for p in positions)
        for positions in ((0, 63, 64, 4095), (1, 65, 127, 128), (2, 66, 129, 4094))
    )
    for target in (65, 130, 192, 4097, 8190, 12285):
        for current in (masks, tuple((m & -m) for m in masks), masks):
            assert (
                native._equality_supports(current, target)
                == python._equality_supports(current, target)
                == oracle(values, current, target)
            )


def test_interval_certificate_dense_holes_and_dp_paths(kernel):
    cases = (
        ((tuple(range(8)),) * 4, 14),
        (((0, 1, 2, 4, 5, 6, 7),) * 4, 14),
        (((0, 3, 7), (1, 5, 9), (2, 6, 8)), 13),
    )
    seen = set()
    for values, target in cases:
        _, native = plans(kernel, values)
        masks = tuple((1 << len(v)) - 1 for v in values)
        assert native._equality_supports(masks, target) == oracle(values, masks, target)
        seen.update(k for k in native.stats if k.startswith("path_"))
    assert {"path_4", "path_5", "path_6"} <= seen


def test_rejected_representation_and_python_fallback(kernel):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), (Number(0), Number(1))) for i in range(65)
    )
    names = tuple(v.name for v in variables)
    c = LinearSumConstraint(
        Atom("sum"), tuple((1, name) for name in names), ConstraintOperator.EQUAL, 32
    )
    model = FiniteModel("large_scope", variables, (c,))
    state = enable(NativeState(model), kernel)
    assert state.propagate()
    assert state._numeric.stats["fallback_plans"] == 1
    assert not state._numeric.stats["compiled_plans"]
    with pytest.raises(ValueError, match="before propagation"):
        enable(state, kernel)
    for values in (((0, 16385), (0, 1), (0, 1)), ((0, 0), (1, 2), (2, 3))):
        python = NumericPlan(
            tuple(NumericColumn(Atom(str(i)), v) for i, v in enumerate(values)),
            ConstraintOperator.EQUAL,
        )
        with pytest.raises(ValueError):
            NativeEqualityPlan(python, kernel, Counter())


def test_native_propagation_solutions_causes_and_rollback(kernel):
    rng = Random(171026)
    for _ in range(80):
        variables = tuple(
            FiniteVariable(
                Atom(f"x{i}"), tuple(map(Number, rng.sample(range(-5, 9), 4)))
            )
            for i in range(4)
        )
        constraints = tuple(
            LinearSumConstraint(
                Atom(f"sum{q}"),
                tuple((rng.choice((-2, -1, 1, 3)), v.name) for v in variables),
                ConstraintOperator.EQUAL,
                rng.randrange(-12, 30),
            )
            for q in range(2)
        )
        model = FiniteModel("state", variables, constraints)
        python, native = (
            NativeState(model),
            enable(NativeState(model), kernel, audit=True),
        )
        for i in range(3):
            checkpoints = python.checkpoint(), native.checkpoint()
            if i:
                v = variables[i - 1]
                python.restrict(v.name, v.domain[0])
                native.restrict(v.name, v.domain[0])
            assert python.propagate() == native.propagate()
            assert python.domains.snapshot() == native.domains.snapshot()
            assert python.failure == native.failure
            assert python.domains.removals == native.domains.removals
            for state, point in zip((python, native), checkpoints, strict=True):
                state.rollback(point)
                state.release(point)
            assert (
                python.domains.snapshot() == native.domains.snapshot() == model.domains
            )
        results = search(python, Query()), search(native, Query())
        a, b = results
        assert (
            a.solutions,
            a.explored_nodes,
            a.failed_branches,
            a.constraint_revisions,
            a.termination,
        ) == (
            b.solutions,
            b.explored_nodes,
            b.failed_branches,
            b.constraint_revisions,
            b.termination,
        )


def test_empty_domain_and_cache_fixpoint(kernel):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, range(4)))) for i in range(3)
    )
    domains = FiniteDomains(variables)
    original = NumericPlan(
        tuple(NumericColumn(v.name, tuple(range(4))) for v in variables),
        ConstraintOperator.EQUAL,
        domains,
    )
    plan = NativeEqualityPlan(original, kernel, Counter())
    answer = plan.supports(domains, 1)
    assert answer == (3, 3, 3)
    for v, mask in zip(variables, answer, strict=True):
        domains.retain_mask(v.name, mask, Atom("sum"))
    calls = plan.stats["calls"]
    assert plan.supports(domains, 1) == answer and plan.stats["calls"] == calls
    domains.retain_mask(variables[0].name, 0, Atom("empty"))
    assert plan.supports(domains, 1) is None
