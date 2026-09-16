"""Integer factors: scope multiplicity, immutable explanations, and sound bounds."""

from dataclasses import replace
from itertools import permutations, product
from random import Random

import pytest

from snarky import Atom, Fact, Number, Triple, Variable
from snarky.factors import FactorDefinition
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    IntegerFactor,
    Query,
    QueryKind,
    ResultStatus,
    TableFactor,
    enumerate_model,
    solve,
)
from snarky.finite.constraints import TableConstraint
from snarky.premises import FactPremise
from tests.test_finite_mixed import NARROW, X, Y, Z, allocation


def witness_factor():
    return IntegerFactor(
        FactorDefinition(
            "narrow_preference",
            Variable("owner"),
            (
                FactPremise(NARROW.entity),
                FactPremise(
                    Triple(Variable("owner"), Atom("witness"), Variable("witness"))
                ),
            ),
        ),
        10**25 + 3,
    )


def test_mixed_factor_scoring_deduplicates_witnesses_and_restores_between_branches():
    witnesses = tuple(
        Fact(Triple(Atom(owner), Atom("witness"), Atom(witness)))
        for owner, witness in (("a", "p"), ("a", "q"), ("b", "r"))
    )
    factor = witness_factor()
    model = replace(
        allocation(),
        context=witnesses,
        objective=FactorObjective((factor,), offset=-4),
    )
    reference = enumerate_model(model, Query(QueryKind.ENUMERATE))
    expected = {
        tuple(s.assignment[v] for v in (X, Y, Z)): s.objective_value
        for s in reference.solutions
    }
    assert set(expected.values()) == {-4, 2 * factor.weight - 4}
    for order in permutations((X, Y, Z)):
        for reverse in (True, False):
            actual = solve(
                model,
                Query(QueryKind.ENUMERATE),
                variable_order=order,
                reverse_values=reverse,
            )
            assert {
                tuple(s.assignment[v] for v in (X, Y, Z)): s.objective_value
                for s in actual.solutions
            } == expected
            for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
                result = solve(
                    model, Query(kind), variable_order=order, reverse_values=reverse
                )
                assert result.status is ResultStatus.OPTIMAL
                assert result.incumbent.objective_value == (
                    min(expected.values())
                    if kind is QueryKind.MINIMIZE
                    else max(expected.values())
                )
            best = solve(model, Query(QueryKind.MAXIMIZE)).incumbent
            scopes = {
                c.scope: c for c in best.contributions if c.factor_name == factor.name
            }
            assert scopes[(Atom("a"),)].witness_count == 2
            assert scopes[(Atom("b"),)].witness_count == 1
            assert sum(c.value for c in best.contributions) == best.objective_value
    # Unknown factor bounds do not turn into a falsely finite global bound.
    stopped = solve(model, Query(QueryKind.MAXIMIZE, max_nodes=1))
    assert not stopped.complete and stopped.objective_bound is None


def test_table_factor_bounds_against_all_domain_completions():
    rng = Random(8)
    values = (Number(-2), Number(0), Number(3))
    for _ in range(40):
        entries = {
            row: rng.randrange(-20, 21)
            for row in product(values, repeat=2)
            if rng.random() < 0.6
        }
        factor = TableFactor("pair", (X, Y), entries, default=-7)
        subsets = tuple(
            frozenset(v for i, v in enumerate(values) if mask & (1 << i))
            for mask in range(1, 8)
        )
        for left, right in product(subsets, repeat=2):
            expected = [entries.get((x, y), -7) for x, y in product(left, right)]
            assert factor.bounds({X: left, Y: right}) == (min(expected), max(expected))
        model = FiniteModel(
            "table",
            (FiniteVariable(X, values), FiniteVariable(Y, values)),
            objective=FactorObjective((factor,), offset=11),
        )
        for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
            actual = solve(model, Query(kind), reverse_values=True)
            oracle = enumerate_model(model, Query(kind))
            assert actual.incumbent.objective_value == oracle.incumbent.objective_value


def test_scores_include_propagated_values_and_tables_do_not_define_support(monkeypatch):
    from snarky.engine.forward import ForwardEngine

    monkeypatch.setattr(
        ForwardEngine, "create_session", lambda *_: pytest.fail("session")
    )
    original = {(Number(1),): 17}
    factor = TableFactor("score", (X,), original, default=23)
    original[(Number(1),)] = -99  # model owns immutable copies
    model = FiniteModel(
        "forced",
        (FiniteVariable(X, (Number(1), Number(2))),),
        (TableConstraint(Atom("force"), (X,), ((Number(2),),)),),
        objective=FactorObjective((factor,), offset=-5),
    )
    result = solve(model, Query(QueryKind.MINIMIZE))
    assert result.explored_nodes == 1
    assert result.incumbent.objective_value == result.objective_bound == 18
    assert result.incumbent.contributions[1].value == 23
    # Missing factor rows receive default scores and remain feasible.
    assert (
        len(solve(replace(model, constraints=()), Query(QueryKind.ENUMERATE)).solutions)
        == 2
    )


def test_factor_model_validation_and_constant_objective():
    with pytest.raises(TypeError, match="integers"):
        IntegerFactor(witness_factor().definition, 1.0)
    with pytest.raises(ValueError, match="duplicate"):
        FactorObjective((witness_factor(), witness_factor()))
    with pytest.raises(ValueError, match="undeclared"):
        FiniteModel("bad", objective=FactorObjective((TableFactor("x", (X,), {}),)))
    with pytest.raises(ValueError, match="arity"):
        TableFactor("bad", (X,), {(): 2})
    constant = FiniteModel(
        "empty", objective=FactorObjective((TableFactor("c", (), {(): -3}),))
    )
    result = solve(constant, Query(QueryKind.MINIMIZE))
    assert result.status is ResultStatus.OPTIMAL
    assert result.incumbent.objective_value == -3
