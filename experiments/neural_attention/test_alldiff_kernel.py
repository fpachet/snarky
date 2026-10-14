"""Exact support, matching-hint and rollback equivalence for native ALLDIFF."""

from collections import Counter
from dataclasses import replace
from itertools import product
from random import Random
from shutil import which

import pytest

from snarky import Atom, Number
from snarky.finite.alldifferent import AllDifferentPlan, MaskColumn
from snarky.finite.constraints import AllDifferentConstraint
from snarky.finite.model import FiniteModel, FiniteVariable, Query, QueryKind
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .alldiff_kernel import AllDiffKernel, NativeAllDifferentPlan, enable


@pytest.fixture(scope="module")
def kernel(tmp_path_factory):
    if which("cc") is None:
        pytest.skip("ALLDIFF experiment requires cc")
    return AllDiffKernel.build(tmp_path_factory.mktemp("alldiff") / "alldiff.so")[0]


class Masks:
    def __init__(self, masks):
        self.masks = masks

    def mask(self, variable):
        return self.masks[int(variable.name)]


def plan(kernel, positions, count=None):
    original = AllDifferentPlan(
        tuple(Atom(str(i)) for i in range(len(positions))),
        tuple(MaskColumn(tuple(p)) for p in positions),
        count or 1 + max(max(p) for p in positions),
    )
    return NativeAllDifferentPlan(original, kernel, Counter(), audit=True)


def oracle(positions, masks):
    choices = [
        [j for j in range(len(p)) if m & (1 << j)]
        for p, m in zip(positions, masks, strict=True)
    ]
    result = [0] * len(positions)
    found = False
    for selected in product(*choices):
        if len({p[j] for p, j in zip(positions, selected, strict=True)}) == len(
            positions
        ):
            found = True
            for i, j in enumerate(selected):
                result[i] |= 1 << j
    return tuple(result) if found else None


@pytest.mark.parametrize("seed", [141026, 151026, 161026])
def test_random_holes_widening_empty_and_cached_against_exhaustive_oracle(kernel, seed):
    rng = Random(seed)
    for _ in range(180):
        count = rng.randrange(2, 10)
        positions = [
            rng.sample(range(count), rng.randrange(1, min(count, 4) + 1))
            for _ in range(rng.randrange(1, 7))
        ]
        native = plan(kernel, positions, count)
        for _trial in range(12):
            masks = tuple(rng.randrange(1 << len(p)) for p in positions)
            for current in (masks, tuple((1 << len(p)) - 1 for p in positions), masks):
                expected = oracle(positions, current)
                assert native.supports(Masks(current)) == expected
                if expected:
                    assert native.supports(Masks(expected)) == expected
        assert native.stats["audited_calls"] == native.stats["calls"]


@pytest.mark.parametrize("count", [63, 64, 65, 127, 128, 129, 2048])
def test_word_boundaries_sparse_large_alphabets_and_restores(kernel, count):
    positions = [
        tuple(range(count)),
        tuple(reversed(range(count))),
        tuple(range(count - 1, -1, -1)),
    ]
    native = plan(kernel, positions, count)
    for active in ((0, count - 1), (0, 1, count - 1), (0,), (count - 2, count - 1)):
        masks = tuple(sum(1 << p.index(v) for v in active) for p in positions)
        assert native.supports(Masks(masks)) == oracle(positions, masks)
        native.supports(Masks(tuple((1 << count) - 1 for _ in positions)))


def test_sparse_chain_dense_graph_and_hall_failure(kernel):
    positions = [(i, i + 1) for i in range(130)]
    native = plan(kernel, positions, 131)
    for masks in ((3,) * 130, (1,) + (3,) * 129, (3,) * 129 + (2,), (3,) * 130):
        native.supports(Masks(masks))  # Audit checks Python's sparse SCC path.
    native = plan(kernel, [tuple(range(130))] * 130)
    native.supports(Masks(((1 << 130) - 1,) * 130))
    # Adequate universe, but a Hall-deficient subset forces an augment failure.
    native = plan(kernel, [(0, 1), (0, 1), (0, 1), (2, 3, 4)])
    assert native.supports(Masks((3, 3, 3, 7))) is None
    assert native.supports(Masks((1, 2, 3, 7))) is None


def test_symbolic_values_propagation_causes_rollback_and_complete_search(kernel):
    rng = Random(171026)
    for _ in range(60):
        values = [Atom("a"), Atom("b"), Number(10**80), Number(-(10**90)), Atom("c")]
        variables = tuple(
            FiniteVariable(Atom(f"x{i}"), tuple(rng.sample(values, 3)))
            for i in range(4)
        )
        constraints = (
            AllDifferentConstraint(Atom("distinct"), tuple(v.name for v in variables)),
        )
        model = FiniteModel("symbolic", variables, constraints)
        python, native = (
            NativeState(model),
            enable(NativeState(model), kernel, audit=True),
        )
        for i in range(3):
            points = python.checkpoint(), native.checkpoint()
            if i:
                v = variables[i - 1]
                for state in (python, native):
                    state.restrict(v.name, v.domain[0])
            assert python.propagate() == native.propagate()
            assert python.domains.snapshot() == native.domains.snapshot()
            assert python.failure == native.failure
            assert python.domains.removals == native.domains.removals
            for state, point in zip((python, native), points, strict=True):
                state.rollback(point)
                state.release(point)
            assert (
                python.domains.snapshot() == native.domains.snapshot() == model.domains
            )
        a = search(
            NativeState(model), Query(kind=QueryKind.ENUMERATE, max_solutions=None)
        )
        b = search(
            enable(NativeState(model), kernel, audit=True),
            Query(kind=QueryKind.ENUMERATE, max_solutions=None),
        )
        assert replace(a, elapsed_seconds=0) == replace(b, elapsed_seconds=0)
    with pytest.raises(ValueError, match="before propagation"):
        state = enable(NativeState(model), kernel)
        state.propagate()
        enable(state, kernel)


def test_creation_guards_and_empty_scope_fallback(kernel):
    import ctypes as ct

    starts = (ct.c_int * 2)(0, 2)
    for positions in ((0, 0), (0, 2), (-1, 1)):
        assert not kernel.create(1, 2, starts, (ct.c_int * 2)(*positions))
    assert not kernel.create(0, 2, starts, (ct.c_int * 2)(0, 1))
    original = AllDifferentPlan((), (), 0)
    with pytest.raises(ValueError):
        NativeAllDifferentPlan(original, kernel, Counter())


def test_maximum_workspace_dimensions_and_entry_budget(kernel):
    native = plan(kernel, [(i,) for i in range(2048)], 2048)
    assert native.supports(Masks((1,) * 2048)) == (1,) * 2048
    native = plan(kernel, [tuple(range(2048))] * 128, 2048)
    masks = ((1 << 2048) - 1,) * 128
    assert native.supports(Masks(masks)) == masks
