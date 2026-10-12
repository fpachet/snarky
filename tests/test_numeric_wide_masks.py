"""Compiled n-ary equality supports agree with enumeration and rollback oracles."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import numeric
from snarky.finite.constraints import ConstraintOperator as Op
from snarky.finite.constraints import LinearSumConstraint, SumConstraint
from snarky.finite.model import FiniteModel, FiniteVariable, Query, QueryKind
from snarky.finite.propagation import NativeState
from snarky.finite.search import solve


def test_numeric_rank_cache_matches_value_oracle_across_shrinks_and_restores():
    values = (3, -8, 10**40, -2, 0, 7)
    column = numeric.NumericColumn(Atom("x"), values)
    masks = list(range(1, 1 << len(values)))
    Random(124).shuffle(masks)
    # Repeated full restores and singletons exercise large cache transitions.
    masks += [63, 4, 63, 1, 32, 1, 63]
    for mask in masks:
        live = [v for i, v in enumerate(values) if mask & (1 << i)]
        assert column.extrema(mask) == (min(live), max(live))
        for bound in (-9, -8, -3, 0, 3, 7, 8, 10**40, 10**40 + 1):
            for upper in (False, True):
                expected = sum(
                    1 << i
                    for i, v in enumerate(values)
                    if mask & (1 << i) and (v <= bound if upper else v >= bound)
                )
                assert column.threshold(mask, bound, upper) == expected


@pytest.mark.parametrize("target", [-4800, -1600, 0, 1600, 1601, 4800])
def test_newly_compiled_spans_match_enumerated_signed_holey_supports(target):
    values = [[1600, -1600, 0]] * 3
    coefficients = [2, -1, 1]
    model = make_model(values, coefficients, target)
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    rows = [
        row
        for row in product(*values)
        if sum(c * v for c, v in zip(coefficients, row, strict=True)) == target
    ]
    assert fast.propagate() == slow.propagate() == bool(rows)
    assert fast.domains.snapshot() == slow.domains.snapshot()
    assert fast.domains.removals == slow.domains.removals
    assert fast._numeric.plans[0][1] is not None
    if rows:
        assert fast.domains.snapshot() == {
            v.name: frozenset(Number(row[i]) for row in rows)
            for i, v in enumerate(model.variables)
        }


def test_span_limit_still_falls_back_above_new_boundary():
    values = [[0, numeric._MAX_EQUALITY_SPAN + 1], [1, 0], [1, 0]]
    model = make_model(values, [1, 1, 1], 1)
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    assert fast.propagate() == slow.propagate()
    assert fast.domains.snapshot() == slow.domains.snapshot()
    assert fast.domains.removals == slow.domains.removals
    assert fast._numeric.plans[0][1] is None
    assert not fast._numeric.columns


def test_newly_compiled_signed_span_preserves_full_search_and_rollback():
    values = [[1600, -1600, 0]] * 3
    values[0] = [v + 10**40 for v in values[0]]
    model = make_model(values, [2, -1, 1], 1600 + 2 * 10**40)
    fast = solve(model, Query(QueryKind.ENUMERATE))
    slow = solve(model, Query(QueryKind.ENUMERATE), numeric_masks=False)
    assert fast.complete and fast.solutions
    for attribute in (
        "status",
        "solutions",
        "explored_nodes",
        "failed_branches",
        "constraint_revisions",
    ):
        assert getattr(fast, attribute) == getattr(slow, attribute)


@pytest.mark.parametrize("operator", tuple(Op))
def test_shared_numeric_layouts_keep_independent_caches_and_declared_orders(operator):
    model = make_model([[3, -2, 0, 1]] * 3, [1, 1, 1], 2)
    model = replace(
        model, constraints=(replace(model.constraints[0], operator=operator),)
    )
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    plan = fast._numeric.get(0, model.constraints[0])
    assert plan is not None
    left, right, _ = plan.columns
    assert left is not right and left.values is right.values
    roots = [s.checkpoint() for s in (fast, slow)]
    for a, b in ((3, -2), (0, 1), (-2, 3), (1, 3)):
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            state.restrict(model.variables[0].name, Number(a))
            state.restrict(model.variables[1].name, Number(b))
        assert fast.propagate() == slow.propagate()
        assert fast.domains.snapshot() == slow.domains.snapshot()
        assert fast.domains.removals == slow.domains.removals
        for v in model.variables:
            assert fast.domains.values(v.name) == slow.domains.values(v.name)
    for state, root in zip((fast, slow), roots, strict=True):
        state.rollback(root)
        state.release(root)
        assert state.domains.snapshot() == model.domains


def make_model(values, coefficients, target):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, v)))
        for i, v in enumerate(values)
    )
    constraint = LinearSumConstraint(
        Atom("sum"),
        tuple(zip(coefficients, (v.name for v in variables), strict=True)),
        Op.EQUAL,
        target,
    )
    return FiniteModel("wide", variables, (constraint,))


def test_signed_holey_shuffled_equalities_match_exhaustive_supports_and_restore():
    rng = Random(920261012)
    for case in range(500):
        count = rng.randrange(3, 7)
        values = [rng.sample(range(-5, 7), rng.randrange(1, 5)) for _ in range(count)]
        coefficients = [rng.choice((-3, -1, 1, 2)) for _ in values]
        target = rng.randrange(-20, 21)
        if case % 5 == 0:
            target = sum(
                c * rng.choice(v) for c, v in zip(coefficients, values, strict=True)
            )
        if case % 13 == 0:
            values[0] = [v + 10**40 for v in values[0]]
            target += coefficients[0] * 10**40
        model = make_model(values, coefficients, target)
        fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
        roots = [s.checkpoint() for s in (fast, slow)]
        for visit in range(4):
            for state, root in zip((fast, slow), roots, strict=True):
                state.rollback(root)
                if visit:
                    variable = model.variables[0]
                    state.restrict(
                        variable.name,
                        variable.domain[(visit - 1) % len(variable.domain)],
                    )
            before = fast.domains.snapshot()
            names = tuple(v.name for v in model.variables)
            rows = [
                row
                for row in product(*(before[n] for n in names))
                if sum(c * v.value for c, v in zip(coefficients, row, strict=True))
                == target
            ]
            good = fast.propagate()
            assert good == slow.propagate() == bool(rows)
            assert fast.domains.snapshot() == slow.domains.snapshot()
            assert fast.domains.removals == slow.domains.removals
            assert fast.revisions == slow.revisions
            assert fast.failure == slow.failure
            if good:
                assert fast.domains.snapshot() == {
                    n: frozenset(row[i] for row in rows) for i, n in enumerate(names)
                }
                assert fast._numeric.plans[0][1] is not None
                # Repeat the support call on filtered masks, then visit a sibling.
                assert (
                    fast._numeric.plans[0][1].supports(fast.domains, target) is not None
                )
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            state.release(root)
            assert state.domains.snapshot() == model.domains
            assert not state.domains.removals


@pytest.mark.parametrize("budget", ["_MAX_EQUALITY_SPAN", "_MAX_EQUALITY_TOTAL_BITS"])
def test_wide_sum_budget_falls_back_exactly(monkeypatch, budget):
    monkeypatch.setattr(numeric, budget, 0)
    model = make_model([range(3)] * 4, [1, -1, 2, 1], 2)
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    assert fast.propagate() == slow.propagate()
    assert fast.domains.snapshot() == slow.domains.snapshot()
    assert fast._numeric.plans[0][1] is None
    assert not fast._numeric.columns


def test_huge_sparse_span_falls_back_and_empty_domain_is_infeasible():
    for values in ([[-(10**40), 10**40]] * 3, [[], [1, 2], [3, 4]]):
        model = make_model(values, [1, 1, 1], 0)
        fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
        assert fast.propagate() == slow.propagate()
        assert fast.domains.snapshot() == slow.domains.snapshot()
        assert fast._numeric.plans[0][1] is None


def test_complete_nary_sum_search_preserves_outputs_and_search_counters():
    model = make_model([[3, 0, 1, 2]] * 4, [1, 1, 1, 1], 5)
    model = replace(
        model,
        constraints=(
            SumConstraint(Atom("sum"), tuple(v.name for v in model.variables), 5),
        ),
    )
    fast = solve(model, Query(QueryKind.ENUMERATE))
    slow = solve(model, Query(QueryKind.ENUMERATE), numeric_masks=False)
    for attribute in (
        "status",
        "solutions",
        "explored_nodes",
        "failed_branches",
        "constraint_revisions",
    ):
        assert getattr(fast, attribute) == getattr(slow, attribute)


def test_nary_cache_is_tagged_with_target_as_well_as_masks():
    model = make_model([range(3)] * 3, [1, 1, 1], 3)
    state = NativeState(model)
    plan = state._numeric.get(0, model.constraints[0])
    assert plan is not None
    assert plan.supports(state.domains, 3) == (7, 7, 7)
    assert plan.supports(state.domains, 0) == (1, 1, 1)
    assert plan.supports(state.domains, 9) is None
    assert plan.supports(state.domains, 3) == (7, 7, 7)


def test_every_fixed_term_pattern_matches_reference_under_sibling_rollback():
    coefficients = [2, -1, 3, 1, -2, 1]
    model = make_model([[-3, 0, 2]] * 6, coefficients, 3)
    fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
    roots = [s.checkpoint() for s in (fast, slow)]
    for pattern in range(64):
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            for i, variable in enumerate(model.variables):
                if pattern & (1 << i):
                    state.restrict(variable.name, variable.domain[i % 3])
        before = fast.domains.snapshot()
        rows = [
            row
            for row in product(*(before[v.name] for v in model.variables))
            if sum(c * v.value for c, v in zip(coefficients, row, strict=True)) == 3
        ]
        valid = fast.propagate()
        assert valid == slow.propagate() == bool(rows)
        assert fast.domains.snapshot() == slow.domains.snapshot()
        assert fast.domains.removals == slow.domains.removals
        if valid:
            assert fast.domains.snapshot() == {
                v.name: frozenset(row[i] for row in rows)
                for i, v in enumerate(model.variables)
            }
    for state, root in zip((fast, slow), roots, strict=True):
        state.rollback(root)
        state.release(root)
        assert state.domains.snapshot() == model.domains
