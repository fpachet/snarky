"""Compiler-free assignment oracles for optional Python equality filtering."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.domains import FiniteDomains
from snarky.finite.model import FiniteModel, FiniteVariable, Query, QueryKind
from snarky.finite.numeric import NumericPlans
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .python_sum_policy import BudgetNumericPlans, enable


def problem(seed):
    rng = Random(seed)
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, rng.sample(range(-5, 9), 4))))
        for i in range(4)
    )
    names = tuple(v.name for v in variables)
    constraints = [AllDifferentConstraint(Atom("a"), names)]
    rows = []
    for j in range(2):
        coefficients = [rng.choice([-3, -1, 1, 2]) for _ in variables]
        target = sum(
            c * v.domain[0].value for c, v in zip(coefficients, variables, strict=True)
        ) + rng.randrange(-3, 4)
        rows.append((coefficients, target))
        constraints.append(
            LinearSumConstraint(
                Atom(f"s{j}"),
                tuple(zip(coefficients, names, strict=True)),
                ConstraintOperator.EQUAL,
                target,
            )
        )

    def valid(values):
        return len(set(values)) == 4 and all(
            sum(c * v for c, v in zip(cs, values, strict=True)) == t for cs, t in rows
        )

    return FiniteModel("oracle", variables, tuple(constraints)), valid


@pytest.mark.parametrize(
    "mode,budget",
    [("bounds", 0), ("budget", 0), ("budget", 512), ("budget", 4000), ("always", 0)],
)
@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_complete_solution_oracles(mode, budget, policy):
    for seed in range(40):
        model, valid = problem(seed)
        expected = {
            values
            for values in product(
                *[[x.value for x in v.domain] for v in model.variables]
            )
            if valid(values)
        }
        state = enable(NativeState(model), mode=mode, budget=budget)
        result = search(
            state, Query(kind=QueryKind.ENUMERATE, max_solutions=None), policy=policy
        )
        observed = {
            tuple(s.assignment[v.name].value for v in model.variables)
            for s in result.solutions
        }
        assert result.termination.value == "exhausted" and observed == expected
        assert len(result.solutions) == len(expected)


@pytest.mark.parametrize("mode", ["bounds", "budget", "always"])
def test_warm_supports_widening_targets_and_fixpoint_cache(mode):
    for seed in range(8):
        model, _ = problem(seed)
        constraint = model.constraints[1]
        domains = FiniteDomains(model.variables)
        plans = BudgetNumericPlans(domains, mode=mode, budget=16)
        plan = plans.get(1, constraint)
        exact = NumericPlans(domains).get(1, constraint)
        rng = Random(seed + 141026)
        for _trial in range(35):
            point = domains.checkpoint()
            masks = tuple(rng.randrange(1, 16) for _ in model.variables)
            for variable, mask in zip(model.variables, masks, strict=True):
                domains.retain_mask(variable.name, mask, Atom("input"))
            target = constraint.target + rng.randrange(-5, 6)
            result = plan.supports(domains, target)
            assert tuple(domains._masks) == masks  # support computation is read-only
            if mode == "always":
                assert result == exact.supports(domains, target)
            for positions in product(
                *[[p for p in range(4) if m & (1 << p)] for m in masks]
            ):
                values = [
                    model.variables[i].domain[p].value for i, p in enumerate(positions)
                ]
                if (
                    sum(
                        c * v
                        for (c, _), v in zip(constraint.terms, values, strict=True)
                    )
                    == target
                ):
                    assert result is not None
                    assert all(result[i] & (1 << p) for i, p in enumerate(positions))
            if result is not None:
                for variable, mask in zip(model.variables, result, strict=True):
                    domains.retain_mask(variable.name, mask, Atom("support"))
                assert plan.supports(domains, target) == result
                # Recompute independently with a fresh plan, bypassing the cache.
                fresh = BudgetNumericPlans(domains, mode=mode, budget=16).get(
                    1, constraint
                )
                assert fresh.supports(domains, target) == result
            domains.rollback(point)
            domains.release(point)
            assert domains.snapshot() == model.domains


def test_huge_origins_multiword_masks_and_fallback():
    shift = 10**80
    variables = tuple(
        FiniteVariable(
            Atom(f"x{i}"), tuple(Number(shift + x) for x in reversed(range(130)))
        )
        for i in range(3)
    )
    names = tuple(v.name for v in variables)
    constraint = LinearSumConstraint(
        Atom("sum"),
        ((2, names[0]), (-1, names[1]), (3, names[2])),
        ConstraintOperator.EQUAL,
        4 * shift + 100,
    )
    model = FiniteModel("wide", variables, (constraint,))
    expected = {
        values
        for values in product(
            *[[v.domain[p].value for p in (0, 64, 129)] for v in variables]
        )
        if 2 * values[0] - values[1] + 3 * values[2] == constraint.target
    }
    for mode in ("bounds", "budget", "always"):
        state = enable(NativeState(model), mode=mode, budget=0)
        for v in variables:
            state.domains.retain_mask(
                v.name, sum(1 << p for p in (0, 64, 129)), Atom("input")
            )
        result = search(state, Query(kind=QueryKind.ENUMERATE, max_solutions=None))
        assert {
            tuple(s.assignment[n].value for n in names) for s in result.solutions
        } == expected
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), (Number(0), Number(10**30))) for i in range(4)
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "fallback",
        variables,
        (
            LinearSumConstraint(
                Atom("sum"),
                tuple((1, n) for n in names),
                ConstraintOperator.EQUAL,
                2 * 10**30,
            ),
        ),
    )
    state = enable(NativeState(model))
    result = search(state, Query(kind=QueryKind.ENUMERATE, max_solutions=None))
    assert len(result.solutions) == 6 and state._numeric.stats["compiled_plans"] == 0
    state.propagate()
    with pytest.raises(ValueError):
        enable(state)


def test_always_exact_preserves_magic_search_and_restores_domains():
    from .magic_search_tuning import prepare

    for n in (3, 4, 8):
        _, model = prepare(n, "middle", "row_major", True)
        original, candidate = (
            NativeState(model),
            enable(NativeState(model), mode="always"),
        )
        a, b = [
            search(state, Query(max_nodes=500, time_limit_seconds=20))
            for state in (original, candidate)
        ]
        assert (
            a.explored_nodes,
            a.failed_branches,
            a.constraint_revisions,
            a.solutions,
        ) == (b.explored_nodes, b.failed_branches, b.constraint_revisions, b.solutions)
        assert candidate.domains.snapshot() == model.domains


def test_span_gate_keeps_small_plans_exact_and_large_plans_sound():
    model, _ = problem(1)
    domains = FiniteDomains(model.variables)
    plans = BudgetNumericPlans(domains, budget=0, min_span=1024)
    assert type(plans.get(1, model.constraints[1])).__name__ == "NumericPlan"
    assert plans.stats["compiled_plans"] == 0
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, [0, 100, 400, 700])))
        for i in range(4)
    )
    names = tuple(v.name for v in variables)
    model = FiniteModel(
        "large_span",
        variables,
        (
            LinearSumConstraint(
                Atom("sum"), tuple((1, n) for n in names), ConstraintOperator.EQUAL, 800
            ),
        ),
    )
    state = enable(NativeState(model), budget=0, min_span=1024)
    result = search(state, Query(kind=QueryKind.ENUMERATE, max_solutions=None))
    expected = {v for v in product([0, 100, 400, 700], repeat=4) if sum(v) == 800}
    assert {
        tuple(s.assignment[n].value for n in names) for s in result.solutions
    } == expected
    assert state._numeric.stats["compiled_plans"] == 1
