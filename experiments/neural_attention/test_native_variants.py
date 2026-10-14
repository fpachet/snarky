"""Native filtering variants preserve independent complete assignment oracles."""

from itertools import product
from random import Random
from shutil import which

import pytest

from .model_batch import BatchContext, ModelSpec
from .native_search import solve
from .native_variants import VariantKernel
from .test_native_search import model_for


@pytest.fixture(
    scope="module",
    params=[
        ("bounds", False, False),
        ("staged", False, False),
        ("budget", True, False),
        ("bounds", True, True),
        ("staged", True, True),
        ("budget", True, True),
    ],
)
def variant(request, tmp_path_factory):
    if which("cc") is None:
        pytest.skip("native experiment requires cc")
    mode, delta, shared = request.param
    kernel, _ = VariantKernel.build_variant(
        tmp_path_factory.mktemp(mode) / "search.so", mode, delta=delta, shared=shared
    )
    return mode, kernel


def test_delta_alldiff_preserves_full_fixpoints_and_search(tmp_path):
    from snarky import Atom, Number
    from snarky.finite.constraints import AllDifferentConstraint
    from snarky.finite.model import FiniteModel, FiniteVariable

    reference, _ = VariantKernel.build_variant(tmp_path / "old.so", "exact")
    delta, _ = VariantKernel.build_variant(tmp_path / "delta.so", "exact", delta=True)
    rng = Random(141026)
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, rng.sample(range(130), 130))))
        for i in range(5)
    )
    spec = ModelSpec(
        FiniteModel(
            "wide",
            variables,
            (AllDifferentConstraint(Atom("a"), tuple(v.name for v in variables)),),
        )
    )
    a, b = [BatchContext(spec, k, audit=True) for k in (reference, delta)]
    for trial in range(150):
        masks = (
            spec.full
            if trial % 4 == 0
            else tuple(rng.getrandbits(130) for _ in variables)
        )
        if trial % 5 == 0:
            masks = tuple(1 << rng.randrange(3) for _ in variables)
        assert a.run(masks, reset=trial % 3 == 0) == b.run(masks, reset=trial % 3 == 0)
    for seed in range(20):
        model, _ = model_for(seed)
        spec = ModelSpec(model)
        for policy in ("mrv", "dom_wdeg"):
            left = solve(
                spec, reference, policy=policy, max_solutions=0, collect_limit=256
            )
            right = solve(
                spec, delta, policy=policy, max_solutions=0, collect_limit=256
            )
            for name in left.keys() - {"search_seconds", "setup_and_search_seconds"}:
                assert left[name] == right[name]


def test_shared_exact_engine_matches_existing_controller_and_cutoffs(tmp_path):
    from .test_native_search import (
        test_complete_enumeration_matches_oracle_and_python,
        test_limits_word_boundaries_and_fresh_restarts,
        test_matched_magic_searches,
    )

    kernel, _ = VariantKernel.build_variant(
        tmp_path / "shared.so", "exact", delta=True, shared=True
    )
    for policy in ("mrv", "dom_wdeg"):
        test_complete_enumeration_matches_oracle_and_python(kernel, policy)
    test_limits_word_boundaries_and_fresh_restarts(kernel)
    test_matched_magic_searches(kernel)


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_complete_enumeration_and_limits(variant, policy):
    _, kernel = variant
    for seed in range(50):
        model, valid = model_for(seed)
        spec = ModelSpec(model)
        rng = Random(seed + 1014)
        masks = tuple(rng.randrange(1, 16) for _ in spec.names)
        expected = {
            values
            for values in product(
                *[
                    [v for j, v in enumerate(a) if m & (1 << j)]
                    for a, m in zip(spec.alphabets, masks, strict=True)
                ]
            )
            if valid(values)
        }
        result = solve(
            spec, kernel, masks=masks, policy=policy, max_solutions=0, collect_limit=256
        )
        assert result["termination"] == "exhausted"
        assert set(result["solutions"]) == expected
        assert result["solution_count"] == len(expected)
        assert solve(spec, kernel, seconds=0)["termination"] == "time_limit"


def test_warm_filtering_reconciles_holes_and_widening(variant):
    _, kernel = variant
    for seed in range(20):
        model, valid = model_for(seed)
        spec, rng = ModelSpec(model), Random(seed + 141026)
        context = BatchContext(spec, kernel)
        for trial in range(30):
            masks = (
                spec.full
                if trial % 3 == 0
                else tuple(rng.randrange(16) for _ in spec.names)
            )
            result = context.run(masks, reset=trial % 4 == 0)
            assert all(a & ~b == 0 for a, b in zip(result["masks"], masks, strict=True))
            for selected in product(
                *[[p for p in range(4) if mask & (1 << p)] for mask in masks]
            ):
                values = tuple(spec.alphabets[i][p] for i, p in enumerate(selected))
                if valid(values):
                    assert result["consistent"]
                    assert all(
                        result["masks"][i] & (1 << p) for i, p in enumerate(selected)
                    )


def test_multiword_signed_bounds(variant):
    from snarky import Atom, Number
    from snarky.finite.constraints import ConstraintOperator, LinearSumConstraint
    from snarky.finite.model import FiniteModel, FiniteVariable

    _, kernel = variant
    shift = 10**80
    variables = tuple(
        FiniteVariable(
            Atom(f"x{i}"), tuple(Number(shift + x) for x in reversed(range(130)))
        )
        for i in range(3)
    )
    names = tuple(v.name for v in variables)
    for op in ConstraintOperator:
        model = FiniteModel(
            "wide",
            variables,
            (
                LinearSumConstraint(
                    Atom("s"),
                    ((2, names[0]), (-1, names[1]), (3, names[2])),
                    op,
                    4 * shift + 100,
                ),
            ),
        )
        spec = ModelSpec(model)
        masks = tuple(sum(1 << p for p in (0, 64, 129)) for _ in names)
        expected = set()
        for positions in product((0, 64, 129), repeat=3):
            values = tuple(spec.alphabets[i][p] for i, p in enumerate(positions))
            total = 2 * values[0] - values[1] + 3 * values[2]
            if (
                total == 4 * shift + 100
                if op == ConstraintOperator.EQUAL
                else total <= 4 * shift + 100
                if op == ConstraintOperator.LESS_EQUAL
                else total >= 4 * shift + 100
            ):
                expected.add(values)
        result = solve(spec, kernel, masks=masks, max_solutions=0, collect_limit=27)
        assert result["termination"] == "exhausted"
        assert set(result["solutions"]) == expected
