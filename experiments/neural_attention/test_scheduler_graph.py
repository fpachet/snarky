"""Prototype supports, search traces and changed scheduling remain correct."""

from dataclasses import replace
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.model import (
    FiniteModel,
    FiniteVariable,
    LinearObjective,
    Query,
    QueryKind,
)
from tests.test_domain_operations import trace_search
from tests.test_finite_mixed import allocation

from .scheduler_graph_benchmark import runtime


@pytest.mark.parametrize(
    "variant",
    ["group", "complement", "graph", "weights_graph", "selective", "weights_selective"],
)
def test_graph_supports_match_baseline_across_shrink_and_widen(variant):
    rng = Random(131051)
    old, new = runtime("before"), runtime(variant)
    for case in range(700):
        pool = [Number(10**30 + i * 7) for i in range(rng.randrange(1, 13))]
        variables = tuple(
            FiniteVariable(
                Atom(f"x{i}"), tuple(rng.sample(pool, rng.randrange(len(pool) + 1)))
            )
            for i in range(rng.randrange(1, 9))
        )
        constraint = AllDifferentConstraint(
            Atom("ad"), tuple(v.name for v in variables)
        )
        stores = [p.domains.FiniteDomains(variables) for p in [old, new]]
        plans = [
            p.alldifferent.AllDifferentPlans(d).get(0, constraint)
            for p, d in zip([old, new], stores, strict=True)
        ]
        roots = [d.checkpoint() for d in stores]
        for stage in range(8):
            if stage % 3 == 0:
                for d, cp in zip(stores, roots, strict=True):
                    d.rollback(cp)
            var = rng.choice(variables)
            mask = rng.randrange(1 << len(var.domain))
            for d in stores:
                d.retain_mask(var.name, mask, Atom("branch"))
            left, right = [p.supports(d) for p, d in zip(plans, stores, strict=True)]
            assert left == right, (case, stage)
            assert plans[0].matching == plans[1].matching
            assert plans[0].owners == plans[1].owners
            if left is not None:
                for d in stores:
                    for v, support in zip(variables, left, strict=True):
                        d.retain_mask(v.name, support, Atom("ad"))
            assert stores[0].snapshot() == stores[1].snapshot()


def random_model(rng, case):
    variables = tuple(
        FiniteVariable(
            Atom(f"x{i}"), tuple(Number(v) for v in rng.sample(range(-2, 6), 4))
        )
        for i in range(4)
    )
    names = tuple(v.name for v in variables)
    return FiniteModel(
        f"case{case}",
        variables,
        (
            AllDifferentConstraint(Atom("ad"), names),
            SumConstraint(Atom("sum"), names[:3], rng.randrange(-3, 12)),
            LinearSumConstraint(
                Atom("linear"),
                tuple((rng.choice([-2, 1, 3]), v) for v in names[1:]),
                ConstraintOperator.LESS_EQUAL,
                rng.randrange(-4, 15),
            ),
        ),
    )


def run_trace(package, model, kind, policy, mixed=False):
    state = (
        package.mixed.MixedState(model)
        if mixed
        else package.propagation.NativeState(model)
    )
    # trace_search imports the live controller, so explicitly select the frozen
    # controller while keeping its observation callbacks and rollback checks.
    from tests import test_domain_operations

    original = test_domain_operations.search
    try:
        test_domain_operations.search = package.search.search
        return trace_search(state, Query(kind=kind), policy)
    finally:
        test_domain_operations.search = original


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
@pytest.mark.parametrize(
    "kind", [QueryKind.ENUMERATE, QueryKind.MINIMIZE, QueryKind.MAXIMIZE]
)
def test_unchanged_full_search_traces_and_weighted_degree_choices(policy, kind):
    rng = Random(131052)
    for case in range(40):
        model = random_model(rng, case)
        if kind is not QueryKind.ENUMERATE:
            model = replace(
                model,
                objective=LinearObjective(
                    tuple((i - 1, v.name) for i, v in enumerate(model.variables))
                ),
            )
        before = run_trace(runtime("before"), model, kind, policy)
        for variant in [
            "weights",
            "group",
            "complement",
            "graph",
            "weights_graph",
            "weights_group",
            "selective",
            "weights_selective",
        ]:
            assert run_trace(runtime(variant), model, kind, policy) == before


@pytest.mark.parametrize("variant", ["batch", "combined"])
@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_batched_fixpoints_and_complete_solution_sets(variant, policy):
    rng = Random(131053)
    for case in range(100):
        model = random_model(rng, case)
        states = [
            runtime(v).propagation.NativeState(model) for v in ["before", variant]
        ]
        consistent = [s.propagate() for s in states]
        assert consistent[0] == consistent[1]
        if consistent[0]:
            assert states[0].domains.snapshot() == states[1].domains.snapshot()
        solutions = []
        for v in ["before", variant]:
            p = runtime(v)
            state = p.propagation.NativeState(model)
            result = p.search.search(
                state, Query(kind=QueryKind.ENUMERATE), policy=policy
            )
            solutions.append(
                {
                    tuple(s.assignment[x.name] for x in model.variables)
                    for s in result.solutions
                }
            )
        assert solutions[0] == solutions[1]


@pytest.mark.parametrize(
    "variant", ["weights", "batch", "graph", "weights_graph", "combined"]
)
@pytest.mark.parametrize("kind", [QueryKind.ENUMERATE, QueryKind.MAXIMIZE])
def test_mixed_rules_guards_and_objective_cuts(variant, kind):
    model = allocation()
    if kind is QueryKind.MAXIMIZE:
        model = replace(
            model,
            objective=LinearObjective(
                tuple((i + 1, v.name) for i, v in enumerate(model.variables))
            ),
        )
    left = run_trace(runtime("before"), model, kind, "dom_wdeg", mixed=True)
    right = run_trace(runtime(variant), model, kind, "dom_wdeg", mixed=True)
    if variant not in ["batch", "combined"]:
        assert left == right
    else:
        # Logical solution set / optimum are invariant; revision order and
        # explanation order intentionally differ for the batching experiment.
        left_solutions, right_solutions = left[1][-1], right[1][-1]
        assert {tuple(s[0].items()) for s in left_solutions} == {
            tuple(s[0].items()) for s in right_solutions
        }
        assert left[1][6] == right[1][6]  # objective bound


@pytest.mark.parametrize("variant", ["group", "complement", "graph", "selective"])
def test_large_repeated_dense_sparse_and_unused_value_rows(variant):
    rng = Random(131055)
    for n in [16, 32, 64]:
        alphabet = tuple(Number(i) for i in range(n + 7))
        variables = tuple(FiniteVariable(Atom(f"x{i}"), alphabet) for i in range(n))
        constraint = AllDifferentConstraint(
            Atom("ad"), tuple(v.name for v in variables)
        )
        stores, plans = [], []
        for v in ["before", variant]:
            p = runtime(v)
            d = p.domains.FiniteDomains(variables)
            stores.append(d)
            plans.append(p.alldifferent.AllDifferentPlans(d).get(0, constraint))
        roots = [d.checkpoint() for d in stores]
        full = (1 << len(alphabet)) - 1
        rows = [
            [full] * n,
            [full ^ (1 << ((i + 3) % n)) for i in range(n)],
            [(1 << i) | (1 << ((i + 1) % n)) for i in range(n)],
            [sum(1 << j for j in set(rng.sample(range(n), 9)) | {i}) for i in range(n)],
            [((1 << (n // 2)) - 1) << (i // (n // 2) * (n // 2)) for i in range(n)],
            [(1 << i) | (1 << (n + 1)) for i in range(n)],
        ]
        for masks in rows + list(reversed(rows)):
            for d, cp in zip(stores, roots, strict=True):
                d.rollback(cp)
                for variable, mask in zip(variables, masks, strict=True):
                    d.retain_mask(variable.name, mask, Atom("branch"))
            supported = [p.supports(d) for p, d in zip(plans, stores, strict=True)]
            assert supported[0] == supported[1]
            assert plans[0].matching == plans[1].matching
