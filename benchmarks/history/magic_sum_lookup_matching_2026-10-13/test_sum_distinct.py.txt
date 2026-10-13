"""Soundness of opt-in distinct-sum bounds against exhaustive joint supports."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from benchmarks.alice_magic import build, validate
from snarky import Atom, Number, Triple
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.model import (
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    Query,
    QueryKind,
)
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .sum_distinct import DistinctSumState, distinct_supports


def make_model(domains, target, scope=None):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, d)))
        for i, d in enumerate(domains)
    )
    names = tuple(v.name for v in variables)
    scope = names if scope is None else tuple(names[i] for i in scope)
    return FiniteModel(
        "distinct_sum_test",
        variables,
        (
            AllDifferentConstraint(Atom("all"), names),
            SumConstraint(Atom("sum"), scope, target),
        ),
    )


def test_distinct_bounds_remove_values_missed_by_separate_propagators():
    model = make_model([range(1, 5)] * 3, 6)
    baseline, coupled = NativeState(model), DistinctSumState(model)
    assert baseline.propagate() and coupled.propagate()
    assert all(baseline.domains.size(v.name) == 4 for v in model.variables)
    assert all(
        {x.value for x in coupled.domains.values(v.name)} == {1, 2, 3}
        for v in model.variables
    )
    assert coupled.stats["bound_removals"] == 3


def test_two_variable_rule_excludes_a_value_supported_only_by_itself():
    model = make_model([range(1, 4)] * 2, 4)
    baseline, coupled = NativeState(model), DistinctSumState(model, max_active=2)
    assert baseline.propagate() and coupled.propagate()
    assert all(baseline.domains.size(v.name) == 3 for v in model.variables)
    assert all(
        {x.value for x in coupled.domains.values(v.name)} == {1, 3}
        for v in model.variables
    )
    assert coupled.stats["pair_removals"] == 2


@pytest.mark.parametrize("shift", [0, 10**40, -(10**40)])
def test_fast_pair_uses_current_fixed_sum_and_declared_value_positions(shift):
    model = make_model(
        [[shift + 100], [shift - 2, shift, shift - 4], [shift - 4, shift - 2, shift]],
        3 * shift + 96,
    )
    state = DistinctSumState(model, max_active=2, pair_fast=True)
    assert state.propagate()
    for v in model.variables[1:]:
        assert {x.value for x in state.domains.values(v.name)} == {shift - 4, shift}
    assert state.stats["pair_removals"] == 2


def test_unit_linear_sum_qualifies_but_signed_linear_sum_does_not():
    model = make_model([range(1, 5)] * 3, 6)
    line = LinearSumConstraint(
        Atom("linear"),
        tuple((1, v.name) for v in model.variables),
        ConstraintOperator.EQUAL,
        6,
    )
    state = DistinctSumState(replace(model, constraints=(model.constraints[0], line)))
    assert state.propagate()
    assert all(Number(4) not in state.domains.values(v.name) for v in model.variables)
    model = make_model([range(1, 4)] * 2, 2)
    x, y = (v.name for v in model.variables)
    line = LinearSumConstraint(
        Atom("linear"), ((1, x), (-1, y)), ConstraintOperator.EQUAL, 2
    )
    state = DistinctSumState(
        replace(model, constraints=(model.constraints[0], line)), pair_fast=True
    )
    assert not state.coupled
    assert state.propagate()
    assert state.domains.values(x) == (Number(3),)
    assert state.domains.values(y) == (Number(1),)


def test_full_domains_not_just_endpoints_are_used():
    supported, _ = distinct_supports(((3,), (1, 2, 100), (1, 2, 100)), (1, 7, 7), 6)
    assert supported is not None and supported[0] == 1


def test_own_exclusive_values_are_not_in_other_variables_union():
    supported, _ = distinct_supports(((1, 10), (2, 3), (4, 5)), (3, 3, 3), 9)
    assert supported is not None and supported[0] == 1


def test_fixed_duplicates_and_insufficient_distinct_values_fail():
    assert distinct_supports(((1,), (1,), (2, 3)), (1, 1, 3), 4)[0] is None
    assert distinct_supports(((1, 2),) * 3, (3,) * 3, 4)[0] is None


def test_signed_huge_translations_are_safe():
    shift = 10**40
    alphabets = (
        (shift + 1, shift + 2, shift + 3, shift + 4),
        (-1, -2, -3, -4),
        (1, 2, 3, 4),
    )
    oracle = [
        values
        for values in product(*alphabets)
        if len(set(values)) == 3 and sum(values) == shift + 4
    ]
    supported, _ = distinct_supports(alphabets, (15,) * 3, shift + 4)
    assert supported is not None
    for values in oracle:
        assert all(
            supported[i] & (1 << alphabets[i].index(v)) for i, v in enumerate(values)
        )


def test_union_bounds_preserve_every_exhaustive_joint_support():
    rng = Random(131033)
    for case in range(400):
        count = rng.randrange(2, 7)
        alphabets = []
        masks = []
        for _ in range(count):
            values = rng.sample(range(-3, 6), rng.randrange(1, 5))
            if case % 5 == 0:
                values = [v + 10**40 for v in values]
            alphabets.append(tuple(values))
            masks.append(rng.randrange(1, 1 << len(values)))
        domains = [
            tuple(v for i, v in enumerate(a) if m & (1 << i))
            for a, m in zip(alphabets, masks, strict=True)
        ]
        target = sum(rng.choice(d) for d in domains) + rng.choice([-1, 0, 0, 1])
        oracle = [
            values
            for values in product(*domains)
            if len(set(values)) == count and sum(values) == target
        ]
        supported, _ = distinct_supports(alphabets, masks, target)
        if oracle:
            assert supported is not None
            for values in oracle:
                assert all(
                    supported[i] & (1 << alphabets[i].index(v))
                    for i, v in enumerate(values)
                )
        if supported is not None:
            assert all(s & m == s for s, m in zip(supported, masks, strict=True))


@pytest.mark.parametrize(
    "settings",
    [
        {},
        dict(max_active=2),
        dict(max_active=4, max_candidates=128),
        dict(max_active=2, pair_fast=True),
        dict(max_active=3, max_candidates=24, pair_fast=True),
    ],
)
def test_search_preserves_every_solution_with_global_alldiff_and_local_sums(settings):
    rng = Random(131034)
    for _ in range(60):
        count = rng.randrange(2, 6)
        domains = [rng.sample(range(-2, 5), rng.randrange(2, 5)) for _ in range(count)]
        scope = sorted(rng.sample(range(count), rng.randrange(2, count + 1)))
        target = sum(rng.choice(domains[i]) for i in scope) + rng.choice([-1, 0, 1])
        model = make_model(domains, target, scope)
        oracle = {
            values
            for values in product(*domains)
            if len(set(values)) == count and sum(values[i] for i in scope) == target
        }
        result = search(
            DistinctSumState(model, **settings),
            Query(kind=QueryKind.ENUMERATE),
            policy="mrv",
        )
        observed = {
            tuple(s.assignment[v.name].value for v in model.variables)
            for s in result.solutions
        }
        assert observed == oracle


def test_rollback_siblings_recompute_bounds_from_current_masks():
    model = make_model([range(1, 6)] * 3, 9)
    state = DistinctSumState(model)
    root = state.checkpoint()
    for value in [1, 5, 3, 1]:
        state.rollback(root)
        state.restrict(model.variables[0].name, Number(value))
        assert state.propagate()
        oracle = [
            values
            for values in product(range(1, 6), repeat=3)
            if values[0] == value and len(set(values)) == 3 and sum(values) == 9
        ]
        for values in oracle:
            assert all(
                Number(x) in state.domains.values(v.name)
                for v, x in zip(model.variables, values, strict=True)
            )
        if value == 1:
            assert Number(4) not in state.domains.values(model.variables[1].name)
    state.rollback(root)
    state.release(root)
    assert state.domains.snapshot() == model.domains


def test_partial_or_guarded_alldiff_does_not_authorize_joint_filtering():
    model = make_model([range(1, 5)] * 3, 6)
    different, total = model.constraints
    guard = Triple(Atom("g"), Atom("is"), Atom("true"))
    for constraint in [
        replace(different, variables=different.variables[:2]),
        GuardedConstraint(Atom("guarded"), guard, different),
    ]:
        candidate = replace(model, constraints=(constraint, total))
        state = DistinctSumState(candidate)
        assert not state.coupled
        assert state.propagate()
        assert Number(4) in state.domains.values(model.variables[2].name)


def test_deadline_is_respected():
    with pytest.raises(TimeoutError):
        DistinctSumState(make_model([range(1, 5)] * 3, 6)).propagate(deadline=0)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        dict(max_active=2, pair_fast=True),
        dict(max_active=3, max_candidates=24, pair_fast=True),
    ],
)
def test_all_eight_three_by_three_magic_squares_are_preserved(settings):
    model, _ = build(3)
    boards = []
    for state in (NativeState(model), DistinctSumState(model, **settings)):
        result = search(state, Query(kind=QueryKind.ENUMERATE), policy="mrv")
        squares = {tuple(validate(3, s.assignment, model)) for s in result.solutions}
        assert len(squares) == 8
        boards.append(squares)
    assert boards[0] == boards[1]
