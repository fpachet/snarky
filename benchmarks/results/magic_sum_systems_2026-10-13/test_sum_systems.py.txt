"""Exact independent oracles for the opt-in residual-system experiment."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from benchmarks.alice_magic import build, validate
from snarky import Atom, Number
from snarky.finite.constraints import ConstraintOperator, LinearSumConstraint
from snarky.finite.model import FiniteModel, FiniteVariable, Query, QueryKind
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .sum_systems import SumSystemState


def model_for(domains, equations):
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, values)))
        for i, values in enumerate(domains)
    )
    constraints = tuple(
        LinearSumConstraint(
            Atom(f"e{i}"),
            tuple((c, variables[j].name) for j, c in enumerate(coefficients) if c),
            ConstraintOperator.EQUAL,
            target,
        )
        for i, (coefficients, target) in enumerate(equations)
    )
    return FiniteModel("sum_system_test", variables, constraints)


def test_triangle_assigns_three_variables_without_search():
    model = model_for(
        [range(21)] * 3, [([1, 1, 0], 10), ([1, 0, 1], 12), ([0, 1, 1], 14)]
    )
    baseline, exact = NativeState(model), SumSystemState(model)
    assert baseline.propagate() and exact.propagate()
    assert not baseline.domains.complete
    assert exact.domains.complete
    assert [exact.domains.values(v.name)[0].value for v in model.variables] == [4, 6, 8]
    assert exact.stats["assignments"] == 3
    assert exact.stats["full_rank"] >= 1


@pytest.mark.parametrize("target", [13, 14])
def test_fractional_or_out_of_domain_unique_solution_is_rejected(target):
    domains = [range(21)] * 3
    if target == 14:
        domains = [[v for v in range(21) if v != 4], range(21), range(21)]
    model = model_for(domains, [([1, 1, 0], 10), ([1, 0, 1], 12), ([0, 1, 1], target)])
    baseline = NativeState(model)
    assert baseline.propagate()
    exact = SumSystemState(model)
    assert not exact.propagate()
    assert exact.stats["contradictions"] == 1


def test_dependent_square_system_is_not_treated_as_unique():
    model = model_for(
        [range(11)] * 4,
        [
            ([1, 1, 0, 0], 10),
            ([0, 0, 1, 1], 10),
            ([1, 0, 1, 0], 10),
            ([0, 1, 0, 1], 10),
        ],
    )
    baseline, exact = NativeState(model), SumSystemState(model)
    assert baseline.propagate() and exact.propagate()
    assert exact.domains.snapshot() == baseline.domains.snapshot()
    assert exact.stats["rank_deficient"] >= 1
    assert exact.stats["assignments"] == 0


def test_inconsistent_dependent_system_has_exact_zero_row_certificate():
    model = model_for([range(11)] * 2, [([1, 1], 10), ([2, 2], 22)])
    exact = SumSystemState(model)
    exact.discover(3, None)
    assert not exact.evaluate(None)[0]
    assert exact.stats["rank_deficient"] >= 1


def test_same_fixed_pattern_different_rhs_and_topology_survive_rollback():
    # For fixed t: x+y=10+t, x+z=12, y+z=14. t=0 => (4,6,8),
    # t=2 => (5,7,7); t=1 has no integer solution.
    model = model_for(
        [range(21)] * 3 + [[0, 1, 2]],
        [
            ([1, 1, 0, -1], 10),
            ([1, 0, 1, 0], 12),
            ([0, 1, 1, 0], 14),
        ],
    )
    exact = SumSystemState(model)
    root = exact.checkpoint()
    for t, expected in [(0, [4, 6, 8]), (2, [5, 7, 7]), (1, None), (0, [4, 6, 8])]:
        exact.rollback(root)
        exact.restrict(model.variables[3].name, Number(t))
        assert exact.propagate() == (expected is not None)
        if expected:
            assert [
                exact.domains.values(v.name)[0].value for v in model.variables[:3]
            ] == expected
    exact.rollback(root)
    assert exact.propagate()
    assert not exact.domains.complete
    exact.rollback(root)
    exact.release(root)
    assert exact.domains.snapshot() == model.domains


def test_huge_integer_translation_and_negative_coefficients():
    shift = 10**50
    model = model_for(
        [range(shift, shift + 21), range(21), range(-20, 1)],
        [
            ([1, 1, 0], shift + 10),
            ([1, 0, -1], shift + 12),
            ([0, 1, -1], 14),
        ],
    )
    exact = SumSystemState(model)
    assert exact.propagate()
    assert [exact.domains.values(v.name)[0].value for v in model.variables] == [
        shift + 4,
        6,
        -8,
    ]


def test_reused_structural_plan_recomputes_rhs_for_sibling_branch():
    model = model_for(
        [range(21)] * 3 + [[0, 2]],
        [([1, 1, 0, -1], 10), ([1, 0, 1, 0], 12), ([0, 1, 1, 0], 14)],
    )
    exact = SumSystemState(model)
    root = exact.checkpoint()
    plans = None
    for t, expected in [(0, [4, 6, 8]), (2, [5, 7, 7])]:
        exact.rollback(root)
        exact.restrict(model.variables[3].name, Number(t))
        assert NativeState.propagate(exact)
        if plans is None:
            exact.discover(7, None)
            plans = exact.systems
        else:
            assert exact.systems is plans
        assert exact.evaluate(None)[0]
        assert [
            exact.domains.values(v.name)[0].value for v in model.variables[:3]
        ] == expected
    exact.rollback(root)
    exact.release(root)


def test_non_integer_and_inequality_constraints_are_excluded():
    model = model_for([[0.0, 1.0]] * 2, [([1, 1], 1)])
    assert not SumSystemState(model).equations
    model = model_for([range(3)] * 2, [([1, 1], 2)])
    model = replace(
        model,
        constraints=(
            replace(model.constraints[0], operator=ConstraintOperator.LESS_EQUAL),
        ),
    )
    assert not SumSystemState(model).equations


@pytest.mark.parametrize("budget", [1, 128])
def test_random_models_preserve_all_exhaustively_checked_solutions(budget):
    rng = Random(131029)
    for _ in range(100):
        count = rng.randrange(2, 6)
        domains = [rng.sample(range(-2, 4), rng.randrange(2, 5)) for _ in range(count)]
        planted = [rng.choice(d) for d in domains]
        equations = []
        for _ in range(rng.randrange(2, 6)):
            coefficients = [rng.choice([-2, -1, 0, 1, 2]) for _ in range(count)]
            if not any(coefficients):
                coefficients[0] = 1
            target = sum(c * v for c, v in zip(coefficients, planted, strict=True))
            if rng.randrange(4) == 0:
                target += rng.choice([-1, 1])
            equations.append((coefficients, target))
        model = model_for(domains, equations)
        oracle = {
            values
            for values in product(*domains)
            if all(
                sum(c * v for c, v in zip(coefficients, values, strict=True)) == target
                for coefficients, target in equations
            )
        }
        exact = SumSystemState(model, budget=budget)
        result = search(exact, Query(kind=QueryKind.ENUMERATE), policy="mrv")
        observed = {
            tuple(s.assignment[v.name].value for v in model.variables)
            for s in result.solutions
        }
        assert observed == oracle


def test_expired_deadline_is_respected():
    model = model_for(
        [range(21)] * 3, [([1, 1, 0], 10), ([1, 0, 1], 12), ([0, 1, 1], 14)]
    )
    with pytest.raises(TimeoutError):
        SumSystemState(model).propagate(deadline=0)


@pytest.mark.parametrize("max_size", [4, 8])
def test_all_eight_normal_three_by_three_magic_squares_are_preserved(max_size):
    model, _ = build(3)
    solutions = []
    for state in (
        NativeState(model),
        SumSystemState(model, max_variables=max_size, max_equations=max_size),
    ):
        result = search(state, Query(kind=QueryKind.ENUMERATE), policy="mrv")
        boards = [validate(3, s.assignment, model) for s in result.solutions]
        assert len(boards) == 8
        solutions.append({tuple(board) for board in boards})
    assert solutions[0] == solutions[1]


def test_small_discovery_budget_is_reported_and_only_loses_optimization():
    model = model_for(
        [range(21)] * 3, [([1, 1, 0], 10), ([1, 0, 1], 12), ([0, 1, 1], 14)]
    )
    exact = SumSystemState(model, budget=1)
    assert exact.propagate()
    assert exact.stats["budget_hits"] == 1
    assert exact.stats["assignments"] == 0
