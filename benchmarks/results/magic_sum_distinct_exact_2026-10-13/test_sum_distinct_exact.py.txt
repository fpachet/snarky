"""Exact three-variable joint filtering against independent enumeration."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from benchmarks.alice_magic import build, validate
from snarky import Atom, Number, Triple
from snarky.finite.constraints import (
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.model import GuardedConstraint, Query, QueryKind
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .sum_distinct import (
    DistinctSumState,
    exact_three_supports,
    three_distinct_supports,
)
from .test_sum_distinct import make_model

SETTINGS = dict(max_active=3, max_candidates=24, pair_fast=True, exact_three=True)


def oracle_supports(alphabets, masks, target):
    domains = [
        [(1 << j, v) for j, v in enumerate(a) if m & (1 << j)]
        for a, m in zip(alphabets, masks, strict=True)
    ]
    result = [0] * len(masks)
    for choices in product(*domains):
        values = [v for _, v in choices]
        if len(set(values)) == len(values) and sum(values) == target:
            for i, (bit, _) in enumerate(choices):
                result[i] |= bit
    return tuple(result) if all(result) else None


def test_exact_masks_match_5000_exhaustive_cases():
    rng = Random(131037)
    for case in range(5000):
        shift = rng.choice([0, 10**40, -(10**40)])
        pairs = []
        for _ in range(rng.randrange(5)):
            pairs.append(((rng.randrange(-4, 9) + shift,), 1))
        for _ in range(3):
            values = rng.sample(range(-4, 9), rng.randrange(2, 8))
            if case % 7 == 0:
                values = [v * 10**40 for v in values]
            live = rng.sample(range(len(values)), rng.randrange(2, len(values) + 1))
            pairs.append((tuple(v + shift for v in values), sum(1 << j for j in live)))
        rng.shuffle(pairs)
        alphabets = tuple(a for a, _ in pairs)
        masks = tuple(m for _, m in pairs)
        active = [i for i, m in enumerate(masks) if m & (m - 1)]
        target = sum(
            rng.choice([v for j, v in enumerate(a) if m & (1 << j)]) for a, m in pairs
        ) + rng.choice([-1, 0, 0, 1])
        observed, counts = exact_three_supports(alphabets, masks, target, active)
        assert observed == oracle_supports(alphabets, masks, target)
        sizes = sorted(masks[i].bit_count() for i in active)
        assert counts["pair_checks"] <= sizes[0] * sizes[1] <= 64


def test_exact_removes_a_hole_supported_by_union_bounds():
    alphabets = ((4, 6, 3, 7), (9, 3, 2, 5), (3, 1, 6, 8))
    masks = (15, 15, 15)
    assert three_distinct_supports(alphabets, masks, 9, [0, 1, 2])[0] == (7, 14, 3)
    supported, counts = exact_three_supports(alphabets, masks, 9, [0, 1, 2])
    assert supported == (7, 12, 3)
    assert counts["pair_checks"] == 16


def test_24_candidate_boundary_checks_at_most_64_pairs():
    alphabets = (tuple(range(8)),) * 3
    supported, counts = exact_three_supports(alphabets, (255,) * 3, 10, [0, 1, 2])
    assert supported == oracle_supports(alphabets, (255,) * 3, 10)
    assert counts["pair_checks"] == 64


@pytest.mark.parametrize(
    "alphabets,masks,target,active",
    [
        (((1, 2),) * 3, (3, 3, 3), 4, [0, 1, 2]),
        (((1,), (1,), (2, 3), (3, 4), (4, 5)), (1, 1, 3, 3, 3), 12, [2, 3, 4]),
        (((1, 2),) * 3, (0, 3, 3), 4, [0, 1, 2]),
        (((1,), (1, 2), (1, 3), (1, 4)), (1, 3, 3, 3), 10, [1, 2, 3]),
    ],
)
def test_empty_domains_fixed_exclusions_and_duplicate_values(
    alphabets, masks, target, active
):
    assert exact_three_supports(alphabets, masks, target, active)[0] == oracle_supports(
        alphabets, masks, target
    )


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_full_search_preserves_all_solutions_with_overlapping_scopes(policy):
    rng = Random(131038)
    for case in range(150):
        count = rng.randrange(3, 7)
        domains = [rng.sample(range(-3, 6), rng.randrange(2, 5)) for _ in range(count)]
        scope = sorted(rng.sample(range(count), rng.randrange(3, count + 1)))
        target = sum(rng.choice(domains[i]) for i in scope)
        model = make_model(domains, target, scope)
        if case % 3 == 0:
            line = LinearSumConstraint(
                Atom("unit_linear"),
                tuple((1, model.variables[i].name) for i in scope),
                ConstraintOperator.EQUAL,
                target,
            )
            model = replace(model, constraints=(model.constraints[0], line))
        extra_scope = sorted(rng.sample(range(count), 3))
        extra_target = sum(rng.choice(domains[i]) for i in extra_scope)
        if case % 2 == 0:
            model = replace(
                model,
                constraints=(
                    *model.constraints,
                    SumConstraint(
                        Atom("overlap"),
                        tuple(model.variables[i].name for i in extra_scope),
                        extra_target,
                    ),
                ),
            )
        oracle = {
            values
            for values in product(*domains)
            if len(set(values)) == count
            and sum(values[i] for i in scope) == target
            and (case % 2 or sum(values[i] for i in extra_scope) == extra_target)
        }
        state = DistinctSumState(model, **SETTINGS)
        result = search(state, Query(kind=QueryKind.ENUMERATE), policy=policy)
        observed = {
            tuple(s.assignment[v.name].value for v in model.variables)
            for s in result.solutions
        }
        assert observed == oracle


def test_sibling_rollback_restores_masks_and_recomputes_supports():
    model = make_model([range(1, 8)] * 4, 16)
    state = DistinctSumState(model, **SETTINGS)
    root = state.checkpoint()
    for first in [1, 7, 3, 1]:
        state.rollback(root)
        state.restrict(model.variables[0].name, Number(first))
        state.propagate()
        # Enumerating children exercises further propagation and rollback.
        result = search(state, Query(kind=QueryKind.ENUMERATE), policy="mrv")
        oracle = {
            values
            for values in product(range(1, 8), repeat=4)
            if values[0] == first and len(set(values)) == 4 and sum(values) == 16
        }
        assert {
            tuple(s.assignment[v.name].value for v in model.variables)
            for s in result.solutions
        } == oracle
    assert state.stats["exact_calls"] > 0
    state.rollback(root)
    state.release(root)
    assert state.domains.snapshot() == model.domains


def test_more_than_24_candidates_falls_back_to_bounds():
    model = make_model([range(1, 11)] * 3, 15)
    state = DistinctSumState(model, exact_three=True)
    bounds = DistinctSumState(model)
    assert state.propagate()
    assert bounds.propagate()
    assert state.stats["exact_calls"] == 0
    assert state.stats["calls"] > 0
    assert state.domains.snapshot() == bounds.domains.snapshot()


def test_partial_and_guarded_alldiff_do_not_enable_exact_filtering():
    model = make_model([range(1, 5)] * 3, 6)
    different, total = model.constraints
    guard = Triple(Atom("g"), Atom("is"), Atom("true"))
    for constraint in [
        replace(different, variables=different.variables[:2]),
        GuardedConstraint(Atom("guarded"), guard, different),
    ]:
        state = DistinctSumState(
            replace(model, constraints=(constraint, total)), **SETTINGS
        )
        assert not state.coupled
        assert state.propagate()
        assert state.stats["exact_calls"] == 0


@pytest.mark.parametrize(
    "coefficients,operator",
    [
        ((1, -1, 1), ConstraintOperator.EQUAL),
        ((1, 2, 1), ConstraintOperator.EQUAL),
        ((1, 1, 1), ConstraintOperator.LESS_EQUAL),
    ],
)
def test_signed_weighted_and_inequality_sums_do_not_qualify(coefficients, operator):
    model = make_model([range(-2, 4)] * 3, 3)
    line = LinearSumConstraint(
        Atom("linear"),
        tuple(zip(coefficients, (v.name for v in model.variables), strict=True)),
        operator,
        3,
    )
    model = replace(model, constraints=(model.constraints[0], line))
    state = DistinctSumState(model, **SETTINGS)
    assert not state.coupled
    baseline = NativeState(model)
    assert state.propagate() == baseline.propagate()
    assert state.domains.snapshot() == baseline.domains.snapshot()
    assert state.stats["exact_calls"] == 0


def test_all_eight_three_by_three_magic_squares_are_preserved():
    model, _ = build(3)
    observed = []
    for state in [NativeState(model), DistinctSumState(model, **SETTINGS)]:
        result = search(state, Query(kind=QueryKind.ENUMERATE), policy="mrv")
        observed.append(
            {tuple(validate(3, s.assignment, model)) for s in result.solutions}
        )
    assert len(observed[0]) == 8 and observed[0] == observed[1]


def test_deadline_is_respected():
    with pytest.raises(TimeoutError):
        DistinctSumState(make_model([range(1, 5)] * 3, 6), **SETTINGS).propagate(
            deadline=0
        )
