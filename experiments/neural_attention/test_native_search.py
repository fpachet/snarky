"""Independent assignment oracles and matched Python/native DFS checks."""

from itertools import product
from random import Random
from shutil import which

import pytest

from snarky import Atom, Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.model import FiniteModel, FiniteVariable, Query, QueryKind
from snarky.finite.search import search

from .model_batch import BatchContext, BatchNative, ModelSpec
from .native_search import SearchKernel, solve


@pytest.fixture(scope="module")
def kernel(tmp_path_factory):
    if which("cc") is None:
        pytest.skip("native search experiment requires cc")
    return SearchKernel.build_search(tmp_path_factory.mktemp("search") / "search.so")[0]


def model_for(seed, *, width=4):
    rng = Random(seed)
    variables = tuple(
        FiniteVariable(
            Atom(f"x{i}"), tuple(map(Number, rng.sample(range(-4, 8), width)))
        )
        for i in range(4)
    )
    names = tuple(v.name for v in variables)
    coefficients = [rng.choice([-3, -1, 0, 1, 2]) for _ in names]
    coefficients = [c or 1 for c in coefficients]
    target = sum(
        c * v.domain[0].value for c, v in zip(coefficients, variables, strict=True)
    )
    op = rng.choice(list(ConstraintOperator))
    model = FiniteModel(
        "oracle",
        variables,
        (
            AllDifferentConstraint(Atom("a"), names),
            LinearSumConstraint(
                Atom("s"), tuple(zip(coefficients, names, strict=True)), op, target
            ),
        ),
    )

    def valid(values):
        total = sum(c * v for c, v in zip(coefficients, values, strict=True))
        return len(set(values)) == len(values) and (
            total == target
            if op == ConstraintOperator.EQUAL
            else total <= target
            if op == ConstraintOperator.LESS_EQUAL
            else total >= target
        )

    return model, valid


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_complete_enumeration_matches_oracle_and_python(kernel, policy):
    for seed in range(30):
        model, valid = model_for(seed)
        spec = ModelSpec(model)
        masks = tuple(Random(seed + v + 100).randrange(1, 16) for v in range(4))
        expected = {
            values
            for values in product(
                *[
                    [x for p, x in enumerate(a) if m & (1 << p)]
                    for a, m in zip(spec.alphabets, masks, strict=True)
                ]
            )
            if valid(values)
        }
        state = BatchNative(model, spec, kernel)
        for name, mask in zip(spec.names, masks, strict=True):
            state.domains.retain_mask(name, mask, Atom("initial"))
        python = search(
            state, Query(kind=QueryKind.ENUMERATE, max_solutions=None), policy=policy
        )
        native = solve(
            spec, kernel, masks=masks, policy=policy, max_solutions=0, collect_limit=256
        )
        assert native["termination"] == "exhausted"
        assert set(native["solutions"]) == expected
        assert native["solution_count"] == len(expected)
        assert native["solutions"] == [
            tuple(s.assignment[n].value for n in spec.names) for s in python.solutions
        ]
        assert (native["nodes"], native["failures"], native["revisions"]) == (
            python.explored_nodes,
            python.failed_branches,
            python.constraint_revisions,
        )
        for name in ("support_calls", "cache_hits", "reductions"):
            assert native[name] == state.batch_totals[name]


def test_limits_word_boundaries_and_fresh_restarts(kernel):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, range(130)))) for i in range(3)
    )
    model = FiniteModel(
        "words",
        variables,
        (AllDifferentConstraint(Atom("a"), tuple(v.name for v in variables)),),
    )
    spec = ModelSpec(model)
    masks = ((1 << 0) | (1 << 64), (1 << 64) | (1 << 129), (1 << 0) | (1 << 129))
    a = solve(spec, kernel, masks=masks, max_solutions=0, collect_limit=10)
    assert set(a["solutions"]) == {(0, 64, 129), (64, 129, 0)}
    assert solve(spec, kernel, max_nodes=1)["termination"] == "node_limit"
    assert solve(spec, kernel, seconds=0)["termination"] == "time_limit"
    assert solve(spec, kernel, masks=(0, *masks[1:]))["termination"] == "exhausted"
    assert solve(spec, kernel, masks=masks)["solutions"] == a["solutions"][:1]
    # Reuse one native Batch workspace after timeout, failure and early success.
    import ctypes as ct

    context = BatchContext(spec, kernel)
    stats, output = (ct.c_uint64 * 10)(), (ct.c_int * 30)()
    for budget, initial in [
        (0, spec.full),
        (5, (0, *masks[1:])),
        (5, masks),
        (5, masks),
    ]:
        status = kernel.search(
            context.handle, spec.encode(initial), 0, 0, 0, budget, output, 10, stats
        )
        assert status == (3 if budget == 0 else 0)
        assert stats[6] == (2 if initial == masks else 0)
    with pytest.raises(ValueError):
        solve(spec, kernel, max_nodes=-1)
    with pytest.raises(ValueError):
        solve(spec, kernel, seconds=float("nan"))


def test_matched_magic_searches(kernel):
    from .magic_search_tuning import prepare

    for n, policy in [(3, "mrv"), (4, "dom_wdeg"), (8, "mrv")]:
        _, model = prepare(n, "middle", "row_major", True)
        spec = ModelSpec(model)
        state = BatchNative(model, spec, kernel)
        python = search(
            state, Query(max_nodes=10000, time_limit_seconds=20), policy=policy
        )
        native = solve(spec, kernel, policy=policy, max_nodes=10000, seconds=20)
        assert native["termination"] == python.termination.value
        assert (native["nodes"], native["failures"], native["revisions"]) == (
            python.explored_nodes,
            python.failed_branches,
            python.constraint_revisions,
        )
        assert native["solutions"] == [
            tuple(s.assignment[n].value for n in spec.names) for s in python.solutions
        ]
