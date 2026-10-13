"""Representation and scheduling changes preserve domain and search semantics."""

from dataclasses import replace
from random import Random

import pytest

from experiments.neural_attention.domain_ops_benchmark import (
    ARCHIVE,
    canonical_removals,
    load_runtime,
    logical_result,
)
from snarky import Atom, Fact, Number, Triple
from snarky.finite.alldifferent import AllDifferentPlans
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
    TableConstraint,
)
from snarky.finite.domains import FiniteDomains
from snarky.finite.mixed import MixedState
from snarky.finite.model import (
    VALUE,
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    LinearObjective,
    Query,
    QueryKind,
)
from snarky.finite.numeric import NumericPlans
from snarky.finite.propagation import NativeState
from snarky.finite.search import search
from tests.test_finite_mixed import allocation


@pytest.fixture(scope="module")
def before():
    return load_runtime(ARCHIVE / "before")


def assert_domains_equal(old, new, variables):
    assert old.snapshot() == new.snapshot()
    for var in variables:
        assert old.mask(var.name) == new.mask(var.name)
        assert old.values(var.name) == new.values(var.name)
        assert old.size(var.name) == new.size(var.name)
    assert old.empty == new.empty
    assert old.complete == new.complete
    assert canonical_removals(old.removals) == canonical_removals(new.removals)
    assert len(old.removals) == new.removal_count
    # Queue order still follows the same symbolic changed-variable set.
    assert list(old.take_changed()) == list(new.take_changed())


def test_random_mutations_nested_release_rollback_and_explanations(before):
    rng = Random(131042)
    pool = [
        Atom("a"),
        Atom("b"),
        *(Number(v) for v in [-(10**40), -2, 0, 1, 3, 10**40]),
    ]
    for _ in range(300):
        variables = tuple(
            FiniteVariable(Atom(f"x{i}"), tuple(rng.sample(pool, rng.randrange(9))))
            for i in range(rng.randrange(7))
        )
        old, new = before.domains.FiniteDomains(variables), FiniteDomains(variables)
        stack = []
        assert_domains_equal(old, new, variables)
        for step in range(40):
            op = rng.randrange(10)
            if op < 2:
                stack.append((old.checkpoint(), new.checkpoint()))
            elif op < 4 and stack:
                position = rng.randrange(len(stack))
                left, right = stack[position]
                old.rollback(left)
                new.rollback(right)
                del stack[position + 1 :]
            elif op == 4 and stack:
                left, right = stack.pop()
                old.release(left)
                new.release(right)
            elif variables:
                variable = rng.choice(variables)
                cause = Atom(f"cause{step}")
                if op < 7:
                    mask = rng.choice(
                        [-1, 1 << 1000, rng.randrange(1 << len(variable.domain))]
                    )
                    assert old.retain_mask(
                        variable.name, mask, cause
                    ) == new.retain_mask(variable.name, mask, cause)
                elif op < 9:
                    values = set(rng.sample(pool, rng.randrange(9)))
                    assert old.retain(variable.name, values, cause) == new.retain(
                        variable.name, values, cause
                    )
                else:
                    value = rng.choice(pool)
                    assert old.retain(variable.name, {value}, cause) == new.assign(
                        variable.name, value, cause
                    )
            assert_domains_equal(old, new, variables)


def test_lazy_explanations_do_not_reuse_same_length_sibling_history():
    x = Atom("x")
    domains = FiniteDomains((FiniteVariable(x, tuple(map(Number, [1, 2, 3]))),))
    root = domains.checkpoint()
    domains.retain_mask(x, 3, Atom("left"))
    left = domains.removals
    domains.rollback(root)
    domains.retain_mask(x, 6, Atom("right"))
    right = domains.removals
    assert left[0].values == frozenset({Number(3)}) and left[0].cause == Atom("left")
    assert right[0].values == frozenset({Number(1)}) and right[0].cause == Atom("right")
    domains.assign(x, Number(2), Atom("fixed"))
    nested = domains.checkpoint()
    domains.assign(x, Number(99), Atom("empty"))
    assert domains.empty and not domains.complete
    domains.rollback(nested)
    domains.release(nested)
    assert domains.complete and not domains.empty
    domains.rollback(root)
    domains.release(root)
    assert not domains.empty and not domains.complete and not domains.removals
    assert left[0].values == frozenset({Number(3)})


@pytest.mark.parametrize("alphabets", [[], [()], [(Number(1),)], [(Number(1),), ()]])
def test_initial_status_including_vacuous_and_empty_domains(before, alphabets):
    variables = tuple(FiniteVariable(Atom(f"x{i}"), a) for i, a in enumerate(alphabets))
    assert_domains_equal(
        before.domains.FiniteDomains(variables), FiniteDomains(variables), variables
    )


def test_compiled_ids_are_bound_to_their_original_store():
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, [1, 2, 3]))) for i in range(3)
    )
    a, b = FiniteDomains(variables), FiniteDomains(tuple(reversed(variables)))
    b.assign(variables[0].name, Number(1), Atom("first"))
    for var in variables[1:]:
        b.retain_mask(var.name, 6, Atom("others"))
    names = tuple(v.name for v in variables)
    total = SumConstraint(Atom("sum"), names, 6)
    distinct = AllDifferentConstraint(Atom("ad"), names)
    plans = [NumericPlans(a).get(0, total), AllDifferentPlans(a).get(0, distinct)]
    assert plans[0].supports(a, 6) == (7, 7, 7)
    assert plans[1].supports(a) == (7, 7, 7)
    assert plans[0].supports(b, 6) == (1, 6, 6)
    assert plans[1].supports(b) == (1, 6, 6)


def test_compiled_revisions_apply_only_actual_reductions():
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, range(1, 5)))) for i in range(3)
    )
    names = tuple(v.name for v in variables)
    state = NativeState(
        FiniteModel(
            "no_op",
            variables,
            (
                AllDifferentConstraint(Atom("ad"), names),
                SumConstraint(Atom("sum"), names, 6),
            ),
        )
    )
    retain = state.domains.retain_mask
    calls = []

    def recorded(variable, mask, cause):
        before = state.domains.mask(variable)
        calls.append((before, mask))
        return retain(variable, mask, cause)

    state.domains.retain_mask = recorded
    assert state.propagate()
    assert not calls
    state.restrict(names[0], Number(4))
    calls.clear()
    assert not state.propagate()
    assert calls and all(old & supported != old for old, supported in calls)


def states_for(model, before, mixed=False):
    classes = {
        "before": before.mixed.MixedState if mixed else before.propagation.NativeState,
        **{
            v: (
                load_runtime(ARCHIVE / v).mixed.MixedState
                if mixed
                else load_runtime(ARCHIVE / v).propagation.NativeState
            )
            for v in ["records", "indexed", "delta"]
        },
        "after": MixedState if mixed else NativeState,
    }
    return [cls(model) for cls in classes.values()]


def trace_search(state, query, policy):
    events = []
    restrict, rollback = state.restrict, state.rollback

    def choose(variable, value):
        events.append(("choose", variable, value))
        restrict(variable, value)

    def restore(cp):
        rollback(cp)
        events.append(
            (
                "rollback",
                dict(state.domains.snapshot()),
                canonical_removals(state.domains.removals),
                state.failure,
            )
        )

    state.restrict = choose
    state.rollback = restore

    def progress(event):
        events.append(
            (
                event.event,
                event.explored_nodes,
                event.failed_branches,
                event.pruned_branches,
                event.constraint_revisions,
                event.depth,
                dict(state.domains.snapshot()),
                canonical_removals(state.domains.removals),
                state.failure,
            )
        )

    result = search(state, query, policy=policy, on_progress=progress)
    assert (
        state.domains.snapshot() == state.model.domains and not state.domains.removals
    )
    return events, logical_result(result)


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
@pytest.mark.parametrize(
    "kind", [QueryKind.ENUMERATE, QueryKind.MINIMIZE, QueryKind.MAXIMIZE]
)
def test_search_order_explanations_guards_and_incumbent_cuts(before, policy, kind):
    rng = Random(131043)
    for case in range(40):
        variables = [
            FiniteVariable(
                Atom(f"x{i}"),
                tuple(Number(v) for v in rng.sample(range(-3, 7), rng.randrange(2, 5))),
            )
            for i in range(rng.randrange(3, 6))
        ]
        rng.shuffle(variables)
        names = tuple(v.name for v in variables)
        terms = tuple((rng.choice([-2, -1, 1, 2]), v) for v in names)
        target = rng.randrange(-4, 12)
        guard = Fact(Triple(Atom("mode"), Atom("is"), Atom("on")))
        constraints = [
            LinearSumConstraint(
                Atom("linear"),
                terms,
                ConstraintOperator.EQUAL if case % 3 else ConstraintOperator.LESS_EQUAL,
                target,
            ),
            GuardedConstraint(
                Atom("guarded"),
                guard,
                SumConstraint(Atom("local"), names[:2], rng.randrange(-3, 7)),
            ),
        ]
        if case % 2:
            constraints.append(AllDifferentConstraint(Atom("ad"), names))
        objective = (
            None
            if kind is QueryKind.ENUMERATE
            else LinearObjective(tuple((rng.choice([-1, 1]), v) for v in names))
        )
        model = FiniteModel(
            "replay",
            tuple(variables),
            tuple(constraints),
            context=(guard,) if case % 2 else (),
            objective=objective,
        )
        results = [
            trace_search(s, Query(kind=kind), policy) for s in states_for(model, before)
        ]
        assert all(r == results[0] for r in results)


def test_guard_requeues_when_assignment_changes_outside_guarded_scope(before):
    x, y, z = (Atom(n) for n in ["x", "y", "z"])
    variables = tuple(
        FiniteVariable(n, tuple(map(Number, [1, 2, 3]))) for n in [x, y, z]
    )
    guard = Fact(Triple(x, VALUE, Number(1)))
    model = FiniteModel(
        "off_scope_guard",
        variables,
        (
            GuardedConstraint(
                Atom("guard"), guard, SumConstraint(Atom("guard_sum"), (y, z), 3)
            ),
            TableConstraint(Atom("force_x"), (x,), ((Number(1),),)),
        ),
    )
    results = []
    for state in states_for(model, before):
        assert state.propagate()
        assert (
            state.domains.values(y) == state.domains.values(z) == (Number(1), Number(2))
        )
        results.append(
            (
                state.domains.snapshot(),
                canonical_removals(state.domains.removals),
                state.revisions,
            )
        )
    assert all(r == results[0] for r in results)


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
@pytest.mark.parametrize("kind", [QueryKind.ENUMERATE, QueryKind.MAXIMIZE])
def test_mixed_rules_and_objective_search_preserve_full_observations(
    before, policy, kind
):
    model = allocation()
    if kind is QueryKind.MAXIMIZE:
        model = replace(
            model,
            objective=LinearObjective(
                tuple((i + 1, v.name) for i, v in enumerate(model.variables))
            ),
        )
    results = [
        trace_search(s, Query(kind=kind), policy)
        for s in states_for(model, before, mixed=True)
    ]
    assert all(r == results[0] for r in results)


def test_materialized_explanation_prefix_survives_append_and_nested_rollback():
    x, y = Atom("x"), Atom("y")
    domains = FiniteDomains(
        tuple(FiniteVariable(v, tuple(map(Number, [1, 2, 3]))) for v in [x, y])
    )
    domains.retain_mask(x, 3, Atom("prefix"))
    prefix = domains.removals[0]
    cp = domains.checkpoint()
    domains.assign(y, Number(1), Atom("left"))
    left = domains.removals
    assert left[0] is prefix
    domains.rollback(cp)
    domains.assign(y, Number(3), Atom("right"))
    right = domains.removals
    assert right[0] is prefix
    assert left[1].values == frozenset({Number(2), Number(3)})
    assert right[1].values == frozenset({Number(1), Number(2)})
    domains.rollback(cp)
    domains.release(cp)
    assert domains.removals == (prefix,)
