"""Exact support and rollback oracles for compiled all-different propagation."""

from itertools import product
from random import Random

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    alldifferent,
    solve,
)
from snarky.finite.constraints import AllDifferentConstraint
from snarky.finite.propagation import NativeState


def model_for(alphabets):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(a)) for i, a in enumerate(alphabets)
    )
    return FiniteModel(
        "different",
        variables,
        (AllDifferentConstraint(Atom("distinct"), tuple(v.name for v in variables)),),
    )


def compare(fast, slow):
    before = fast.domains.snapshot()
    scope = tuple(before)
    rows = [r for r in product(*(before[v] for v in scope)) if len(set(r)) == len(r)]
    valid = fast.propagate()
    assert valid == slow.propagate() == bool(rows)
    assert fast.domains.snapshot() == slow.domains.snapshot()
    assert fast.domains.removals == slow.domains.removals
    assert fast.failure == slow.failure
    assert fast.revisions == slow.revisions
    if valid:
        assert fast.domains.snapshot() == {
            v: frozenset(r[i] for r in rows) for i, v in enumerate(scope)
        }


def test_random_exact_supports_nested_rollback_and_sibling_failures():
    rng = Random(71691)
    universe = (
        Atom("a"),
        Atom("b"),
        Number(-(10**40)),
        Number(0),
        Number(7),
        Number(10**40),
    )
    for _ in range(700):
        model = model_for(
            [rng.sample(universe, rng.randrange(6)) for _ in range(rng.randrange(1, 7))]
        )
        states = (NativeState(model), NativeState(model, alldifferent_masks=False))
        roots = [s.checkpoint() for s in states]
        compare(*states)
        for _visit in range(3):
            for state, root in zip(states, roots, strict=True):
                state.rollback(root)
            if model.variables:
                v = rng.choice(model.variables)
                mask = rng.randrange(1 << len(v.domain))
                for state in states:
                    state.domains.retain_mask(v.name, mask, Atom("branch"))
            nested = [s.checkpoint() for s in states]
            compare(*states)
            for state, cp in zip(states, nested, strict=True):
                state.rollback(cp)
            compare(*states)
            for state, cp in zip(states, nested, strict=True):
                state.rollback(cp)
                state.release(cp)
        for state, root in zip(states, roots, strict=True):
            state.rollback(root)
            state.release(root)
            assert state.domains.snapshot() == model.domains


def test_hall_sets_and_free_values_after_matching_repair():
    model = model_for(
        [tuple(map(Number, a)) for a in ((1, 2), (1, 2), (1, 2, 3, 4), (3, 4, 5))]
    )
    states = (NativeState(model), NativeState(model, alldifferent_masks=False))
    roots = [s.checkpoint() for s in states]
    compare(*states)
    for value in (1, 2):
        for state, root in zip(states, roots, strict=True):
            state.rollback(root)
            state.restrict(Atom("x0"), Number(value))
        compare(*states)
    for state, root in zip(states, roots, strict=True):
        state.rollback(root)
        state.release(root)
    compare(*states)


def test_long_sparse_chain_and_cycle_are_exact_without_recursion():
    for cycle in (False, True):
        size = 700
        values = tuple(map(Number, range(size)))
        alphabets = [(values[i], values[(i + 1) % size]) for i in range(size - 1)]
        alphabets.append((values[-1], values[0]) if cycle else (values[-1],))
        model = model_for(alphabets)
        fast = NativeState(model)
        assert fast.propagate()
        assert all(
            fast.domains.size(v.name) == (2 if cycle else 1) for v in model.variables
        )
        assert fast._alldifferent.entries == 2 * size - (not cycle)


def test_budget_and_value_limit_fallback_preserve_reference(monkeypatch):
    model = model_for([tuple(map(Number, range(4)))] * 4)
    for setting in ("_MAX_ENTRIES", "_MAX_VALUES"):
        with monkeypatch.context() as patch:
            patch.setattr(alldifferent, setting, 0)
            fast = NativeState(model)
            compare(fast, NativeState(model, alldifferent_masks=False))
            assert fast._alldifferent.plans[0] is None
            assert fast._alldifferent.entries == 0


def test_complete_search_matches_reference_outputs_and_counters():
    model = model_for(
        [tuple(map(Number, a)) for a in ((3, 1, 2), (1, 2), (2, 3, 4), (3, 4, 5))]
    )
    fast = solve(model, Query(QueryKind.ENUMERATE))
    slow = solve(model, Query(QueryKind.ENUMERATE), alldifferent_masks=False)
    for attr in (
        "status",
        "solutions",
        "explored_nodes",
        "failed_branches",
        "constraint_revisions",
    ):
        assert getattr(fast, attr) == getattr(slow, attr)


def test_sparse_irregular_value_graphs_match_reference():
    rng = Random(1731)
    for _ in range(60):
        values = tuple(Atom(f"value{i}") for i in range(90))
        alphabets = [rng.sample(values, rng.randrange(1, 6)) for _ in range(75)]
        # Include a feasible witness in most models; sparse alternating cycles
        # and paths then matter, instead of testing only immediate failure.
        if rng.randrange(4):
            alphabets = [
                tuple(dict.fromkeys((*a, values[i]))) for i, a in enumerate(alphabets)
            ]
        model = model_for(alphabets)
        fast, slow = NativeState(model), NativeState(model, alldifferent_masks=False)
        roots = [s.checkpoint() for s in (fast, slow)]
        for visit in range(3):
            for state, root in zip((fast, slow), roots, strict=True):
                state.rollback(root)
                if visit:
                    state.restrict(
                        model.variables[visit].name, model.variables[visit].domain[0]
                    )
            assert fast.propagate() == slow.propagate()
            assert fast.domains.snapshot() == slow.domains.snapshot()
            assert fast.domains.removals == slow.domains.removals
        for state, root in zip((fast, slow), roots, strict=True):
            state.rollback(root)
            state.release(root)


def test_guard_activation_and_failure_cause():
    from snarky import Fact, Triple
    from snarky.finite import GuardedConstraint

    base = model_for([(Atom("a"), Atom("b"))] * 3)
    guard = Fact(Triple(Atom("mode"), Atom("is"), Atom("active")))
    model = FiniteModel(
        "guarded",
        base.variables,
        (GuardedConstraint(Atom("outer"), guard, base.constraints[0]),),
    )
    for enabled in (False, True):
        state = NativeState(model, alldifferent_masks=enabled)
        root = state.checkpoint()
        assert state.propagate()
        assert not state.propagate(facts=frozenset((guard,)))
        assert state.failure == Atom("outer")
        assert not state.domains.removals
        state.rollback(root)
        assert state.propagate()
        state.rollback(root)
        state.release(root)
