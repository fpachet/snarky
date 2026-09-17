"""Mask arithmetic matches exhaustive supports and the set kernels under rollback."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from snarky import Atom, Fact, Number, Triple
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    LinearObjective,
    Query,
    QueryKind,
    numeric,
    solve,
)
from snarky.finite.constraints import ConstraintOperator as Op
from snarky.finite.constraints import LinearSumConstraint, SumConstraint
from snarky.finite.domains import FiniteDomains
from snarky.finite.propagation import NativeState
from snarky.finite.search import search


def model_for(domains, coefficients, operator, target):
    names = tuple(Atom(f"x{i}") for i in range(len(domains)))
    c = LinearSumConstraint(
        Atom("sum"), tuple(zip(coefficients, names, strict=True)), operator, target
    )
    return FiniteModel(
        "numeric",
        tuple(
            FiniteVariable(v, tuple(map(Number, d)))
            for v, d in zip(names, domains, strict=True)
        ),
        (c,),
    )


def test_random_signed_holey_supports_and_nested_rollback_match_oracles():
    rng = Random(17702)
    for case in range(650):
        count = rng.randrange(1, 6)
        values = [rng.sample(range(-6, 8), rng.randrange(0, 6)) for _ in range(count)]
        coeffs = [rng.choice((-3, -1, 1, 2)) for _ in values]
        op = (
            rng.choice(tuple(Op))
            if count <= 2
            else rng.choice((Op.LESS_EQUAL, Op.GREATER_EQUAL))
        )
        target = rng.randrange(-14, 15)
        if case % 13 == 0:
            # Huge magnitudes must not be used as bit indexes.
            values[0] = [v + 10**40 for v in values[0]]
            target += coeffs[0] * 10**40
        model = model_for(values, coeffs, op, target)
        fast, slow = NativeState(model), NativeState(model, numeric_masks=False)
        roots = [s.checkpoint() for s in (fast, slow)]
        names = tuple(v.name for v in model.variables)
        for visit in range(4):
            for state, root in zip((fast, slow), roots, strict=True):
                state.rollback(root)
            if visit and values[0]:
                selected = Number(values[0][(visit - 1) % len(values[0])])
                fast.restrict(names[0], selected)
                slow.restrict(names[0], selected)
            before = fast.domains.snapshot()
            rows = [
                r
                for r in product(*(before[v] for v in names))
                if (
                    (sum(c * x.value for c, x in zip(coeffs, r, strict=True)) == target)
                    if op is Op.EQUAL
                    else (
                        sum(c * x.value for c, x in zip(coeffs, r, strict=True))
                        <= target
                    )
                    if op is Op.LESS_EQUAL
                    else (
                        sum(c * x.value for c, x in zip(coeffs, r, strict=True))
                        >= target
                    )
                )
            ]
            good = fast.propagate()
            assert good == slow.propagate() == bool(rows)
            assert fast.domains.snapshot() == slow.domains.snapshot()
            assert fast.domains.removals == slow.domains.removals
            assert fast.revisions == slow.revisions
            assert fast.failure == slow.failure
            if good:
                assert fast.domains.snapshot() == {
                    v: frozenset(r[i] for r in rows) for i, v in enumerate(names)
                }
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            state.release(root)
            assert state.domains.snapshot() == model.domains
            assert not state.domains.removals


def test_retain_mask_matches_set_trail_events_and_nested_restore():
    v = FiniteVariable(Atom("x"), tuple(map(Number, (9, -1, 30, 0))))
    fast, slow = FiniteDomains((v,)), FiniteDomains((v,))
    rng = Random(19)
    for _ in range(100):
        roots = [s.checkpoint() for s in (fast, slow)]
        for _ in range(5):
            mask = rng.randrange(64)
            cause = Atom("reduction")
            assert fast.retain_mask(v.name, mask, cause) == slow.retain(
                v.name, {x for i, x in enumerate(v.domain) if mask & (1 << i)}, cause
            )
            assert fast.snapshot() == slow.snapshot()
            assert fast.removals == slow.removals
            assert fast.take_changed() == slow.take_changed()
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            state.release(root)
        assert fast.snapshot() == slow.snapshot()
        assert fast.take_changed() == slow.take_changed()


@pytest.mark.parametrize("kind", [QueryKind.MINIMIZE, QueryKind.MAXIMIZE])
def test_full_search_and_changing_incumbent_targets_match_reference(kind):
    model = model_for([range(5), range(5)], [1, -2], Op.LESS_EQUAL, 1)
    model = replace(
        model,
        objective=LinearObjective(
            ((3, model.variables[0].name), (-1, model.variables[1].name)), 11
        ),
    )
    fast = solve(model, Query(kind), numeric_masks=True, reverse_values=True)
    slow = solve(model, Query(kind), numeric_masks=False, reverse_values=True)
    for attr in (
        "status",
        "solutions",
        "explored_nodes",
        "failed_branches",
        "pruned_branches",
        "constraint_revisions",
        "incumbent_values",
        "objective_bound",
    ):
        assert getattr(fast, attr) == getattr(slow, attr)
    state = NativeState(model)
    for direction in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE, QueryKind.ENUMERATE):
        actual = search(state, Query(direction))
        expected = solve(model, Query(direction), numeric_masks=False)
        assert actual.solutions == expected.solutions
        assert not state.domains.removals


def test_fallback_budgets_and_wide_equalities(monkeypatch):
    monkeypatch.setattr(numeric, "_MAX_ENTRIES", 0)
    model = model_for([range(3), range(3)], [2, -1], Op.EQUAL, 1)
    state = NativeState(model)
    assert state.propagate()
    assert not state._numeric.columns
    assert state.domains.snapshot() == {
        Atom("x0"): frozenset((Number(1),)),
        Atom("x1"): frozenset((Number(1),)),
    }
    monkeypatch.setattr(numeric, "_MAX_ENTRIES", 100)
    model = model_for([range(3)] * 3, [1, 1, 1], Op.EQUAL, 2)
    state = NativeState(model)
    assert state.propagate()
    assert not state._numeric.columns


def test_inactive_guard_and_removed_noninteger_preserve_validation_timing():
    x = Atom("x")
    guard = Fact(Triple(Atom("mode"), Atom("is"), Atom("active")))
    linear = LinearSumConstraint(Atom("int"), ((1, x),), Op.LESS_EQUAL, 1)
    base = FiniteModel(
        "guard",
        (FiniteVariable(x, (Atom("bad"), Number(0), Number(2))),),
        (GuardedConstraint(Atom("guarded"), guard, linear),),
    )
    for enabled in (False, True):
        state = NativeState(base, numeric_masks=enabled)
        assert state.propagate()
        with pytest.raises(TypeError, match="integer Number"):
            state.propagate(facts=frozenset((guard,)))
        state = NativeState(base, numeric_masks=enabled)
        state.restrict(x, Number(0))
        assert state.propagate(facts=frozenset((guard,)))


def test_binary_sum_and_active_guard_share_mask_path():
    x, y = Atom("x"), Atom("y")
    guard = Fact(Triple(Atom("mode"), Atom("is"), Atom("active")))
    constraint = SumConstraint(Atom("sum"), (x, y), 3)
    model = FiniteModel(
        "guard",
        (
            FiniteVariable(x, tuple(map(Number, (3, 0, 2)))),
            FiniteVariable(y, tuple(map(Number, (1, 0)))),
        ),
        (GuardedConstraint(Atom("guarded"), guard, constraint),),
        context=(guard,),
    )
    state = NativeState(model)
    assert state.propagate()
    assert state._numeric.entries == 5
    assert state.domains.values(x) == (Number(3), Number(2))
    assert state.domains.removals[0].cause == Atom("guarded")
