"""Product optimization and bounds against direct rational arithmetic."""

import json
from fractions import Fraction
from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    RationalProductObjective,
    ResultStatus,
    Termination,
    WeightTable,
    enumerate_model,
    solve,
)
from snarky.finite.bounds import compile_objective_bound
from snarky.finite.cli import result_payload
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    CountConstraint,
)
from snarky.finite.propagation import NativeState
from snarky.finite.search import search


@pytest.mark.parametrize("seed", range(8))
def test_exact_products_bounds_and_minmax_match_direct_enumeration(seed):
    rng = Random(seed)
    names = tuple(map(Atom, ("x", "y", "z")))
    values = tuple(map(Number, range(3)))
    factors = [WeightTable("constant", (), {(): Fraction(2, 3)})]
    for i in range(2):
        # Include zero weights, weights > 1, missing rows, and nonzero defaults.
        rows = {
            row: Fraction(rng.randrange(5), rng.randrange(1, 7))
            for row in product(values, repeat=2)
            if rng.random() < 0.7
        }
        factors.append(
            WeightTable(str(i), names[i : i + 2], rows, default=Fraction(1, 7))
        )
    model = FiniteModel(
        "product",
        tuple(FiniteVariable(v, values) for v in names),
        (AllDifferentConstraint(Atom("distinct"), names),),
        objective=RationalProductObjective(tuple(factors)),
    )

    # Direct reference uses raw table rows, not objective evaluation or search.
    def direct(row):
        score = Fraction(2, 3)
        for i in range(2):
            score *= factors[i + 1].values.get(row[i : i + 2], factors[i + 1].default)
        return score

    expected = [direct(row) for row in product(values, repeat=3) if len(set(row)) == 3]
    for mode in ("local", "auto"):
        bound = (
            model.objective.bounds
            if mode == "local"
            else compile_objective_bound(model)
        )
        for x in values:
            domains = {
                names[0]: frozenset((x,)),
                names[1]: frozenset(values),
                names[2]: frozenset(values[:2]),
            }
            low, high = bound(domains)
            residual = [direct(row) for row in product((x,), values, values[:2])]
            assert low <= min(residual) <= max(residual) <= high
        for kind, choose in ((QueryKind.MINIMIZE, min), (QueryKind.MAXIMIZE, max)):
            for order in (names, names[::-1]):
                result = solve(
                    model,
                    Query(kind),
                    bounding=mode,
                    variable_order=order,
                    value_policy="objective",
                )
                assert result.status is ResultStatus.OPTIMAL
                assert (
                    result.incumbent.objective_value
                    == result.objective_bound
                    == choose(expected)
                )
                assert result.arithmetic == "rational_product"
                assert enumerate_model(
                    model, Query(kind)
                ).incumbent.objective_value == choose(expected)
                json.dumps(result_payload(result))


def test_zero_weights_are_not_infeasibility_and_empty_product_is_one():
    x = Atom("x")
    model = FiniteModel(
        "zero",
        (FiniteVariable(x, (Number(0), Number(1))),),
        objective=RationalProductObjective((WeightTable("zero", (x,), {}),)),
    )
    result = solve(model, Query(QueryKind.MAXIMIZE))
    assert (
        result.status is ResultStatus.OPTIMAL and result.incumbent.objective_value == 0
    )
    empty = solve(
        FiniteModel("empty", objective=RationalProductObjective()),
        Query(QueryKind.MAXIMIZE),
    )
    assert empty.status is ResultStatus.OPTIMAL and empty.incumbent.objective_value == 1


def test_long_scope_fallback_and_near_tie_do_not_round_away_better_solution():
    names = tuple(map(Atom, ("x", "y", "z")))
    values = (Number(0), Number(1))
    epsilon = Fraction(1, 10**40)
    objective = RationalProductObjective(
        (
            WeightTable(
                "long",
                (names[0], names[2]),
                {(Number(1), Number(1)): 1 + epsilon},
                default=1,
            ),
        )
    )
    model = FiniteModel(
        "tie", tuple(FiniteVariable(v, values) for v in names), objective=objective
    )
    result = solve(model, Query(QueryKind.MAXIMIZE))
    assert result.incumbent.objective_value == 1 + epsilon
    assert result.status is ResultStatus.OPTIMAL


def test_bound_compilation_timeout_restores_state(monkeypatch):
    import snarky.finite.bounds as bounds

    def timeout(*args, **kwargs):
        raise TimeoutError("compilation budget")

    monkeypatch.setattr(bounds, "ProductChainBound", timeout)
    x = Atom("x")
    state = NativeState(
        FiniteModel(
            "timeout",
            (FiniteVariable(x, (Number(0),)),),
            objective=RationalProductObjective(),
        )
    )
    before = state.domains.snapshot()
    result = search(state, Query(QueryKind.MAXIMIZE))
    assert result.status is ResultStatus.UNKNOWN
    assert result.termination is Termination.TIME_LIMIT
    assert state.domains.snapshot() == before


def test_product_node_limit_preserves_incumbent_and_sound_bound():
    x = Atom("x")
    values = tuple(map(Number, (0, 1, 2)))
    objective = RationalProductObjective(
        (
            WeightTable(
                "x",
                (x,),
                {(value,): Fraction(i + 1, 5) for i, value in enumerate(values)},
            ),
        )
    )
    model = FiniteModel("limited", (FiniteVariable(x, values),), objective=objective)
    result = solve(model, Query(QueryKind.MAXIMIZE, max_nodes=2), bounding="local")
    assert result.status is ResultStatus.FEASIBLE
    assert result.termination is Termination.NODE_LIMIT
    assert result.incumbent.objective_value == Fraction(1, 5)
    assert result.objective_bound == Fraction(3, 5)


@pytest.mark.parametrize("target", [0, 1, 2])
def test_counter_bound_respects_partial_scope_and_domain_restrictions(target):
    names = tuple(map(Atom, ("x", "y", "z")))
    values = tuple(map(Number, (0, 1)))
    model = FiniteModel(
        "count",
        tuple(FiniteVariable(v, values) for v in names),
        (
            CountConstraint(
                Atom("count"),
                (names[0], names[2]),
                Number(1),
                ConstraintOperator.EQUAL,
                target,
            ),
        ),
        objective=RationalProductObjective(
            tuple(
                WeightTable(
                    str(i),
                    (v,),
                    {(Number(0),): Fraction(1, 3), (Number(1),): Fraction(2, 3)},
                )
                for i, v in enumerate(names)
            )
        ),
    )
    bound = compile_objective_bound(model)
    for fixed in values:
        domains = dict(model.domains)
        domains[names[0]] = frozenset((fixed,))
        candidates = [
            model.objective.evaluate(dict(zip(names, row, strict=True)))
            for row in product((fixed,), values, values)
            if sum(v == Number(1) for v in (row[0], row[2])) == target
        ]
        assert bound(domains)[1] == max(candidates, default=Fraction(0))
    result = solve(model, Query(QueryKind.MAXIMIZE), value_policy="objective")
    oracle = enumerate_model(model, Query(QueryKind.MAXIMIZE))
    assert result.status is ResultStatus.OPTIMAL
    assert result.incumbent.objective_value == oracle.incumbent.objective_value
