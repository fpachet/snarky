"""Completion-bound admissibility against independent residual enumeration."""

from dataclasses import replace
from itertools import product
from random import Random
from time import perf_counter

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    ResultStatus,
    TableFactor,
    Termination,
    enumerate_model,
    parse_model_document,
    solve,
)
from snarky.finite.bounds import (
    ChainBound,
    NoObjectiveCompletion,
    compile_objective_bound,
)
from snarky.finite.constraints import TableConstraint
from snarky.finite.propagation import NativeState
from snarky.finite.search import search


def random_chain(seed):
    rng = Random(seed)
    values = tuple(Number(i) for i in range(3))
    variables = tuple(FiniteVariable(Atom(f"x{i}"), values) for i in range(5))
    factors, constraints = [], []
    for i in range(3):
        scope = tuple(v.name for v in variables[i : i + 3])
        rows = tuple(product(values, repeat=3))
        factors.append(
            TableFactor(
                f"f{i}",
                scope,
                {row: rng.randrange(-20, 21) for row in rows if rng.random() < 0.8},
                default=-5,
            )
        )
        constraints.append(
            TableConstraint(
                Atom(f"c{i}"), scope, tuple(row for row in rows if rng.random() < 0.85)
            )
        )
    # This wide hard constraint is deliberately relaxed by the DP.
    constraints.append(
        TableConstraint(
            Atom("ends"),
            (variables[0].name, variables[-1].name),
            tuple((v, v) for v in values),
        )
    )
    return FiniteModel(
        "chain",
        variables,
        tuple(constraints),
        objective=FactorObjective(
            (*factors, TableFactor("constant", (), {(): 4})), offset=-9
        ),
    )


@pytest.mark.parametrize("seed", range(8))
def test_bounds_and_ordered_search_agree_with_residual_oracle(seed):
    model = random_chain(seed)
    bound = compile_objective_bound(model)
    assert isinstance(bound, ChainBound)
    complete = enumerate_model(model, Query(QueryKind.ENUMERATE)).solutions
    rng = Random(seed + 900)
    # Revisit expanded and narrowed domains using the same edge cache, as happens
    # after nested rollback. No cached branch bounds may survive as model bounds.
    for _ in range(24):
        domains = {
            v.name: frozenset(value for value in v.domain if rng.random() < 0.75)
            for v in model.variables
        }
        feasible = [
            s.objective_value
            for s in complete
            if all(s.assignment[v] in domain for v, domain in domains.items())
        ]
        try:
            low, high = bound(domains)
        except NoObjectiveCompletion:
            assert not feasible
        else:
            if feasible:
                assert low <= min(feasible) <= max(feasible) <= high
    for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
        oracle = enumerate_model(model, Query(kind))
        for bounding in ("local", "auto"):
            actual = solve(
                model, Query(kind), bounding=bounding, value_policy="objective"
            )
            assert actual.status is oracle.status is ResultStatus.OPTIMAL
            assert actual.incumbent.objective_value == oracle.incumbent.objective_value
            assert actual.objective_bound == oracle.incumbent.objective_value


def test_local_fragment_is_exact_and_model_revisions_get_new_bounds():
    model = random_chain(91)
    local = replace(model, constraints=model.constraints[:-1])
    domains = {v.name: frozenset(v.domain) for v in local.variables}
    expected = [
        s.objective_value
        for s in enumerate_model(local, Query(QueryKind.ENUMERATE)).solutions
    ]
    assert compile_objective_bound(local)(domains) == (min(expected), max(expected))
    # Removing constraints and changing scores cannot reuse an obsolete tight bound.
    changed = replace(
        local,
        constraints=(),
        objective=FactorObjective(
            (TableFactor("replacement", (model.variables[0].name,), {}, default=99),)
        ),
    )
    assert compile_objective_bound(changed)(domains) == (99, 99)
    assert solve(changed, Query(QueryKind.MINIMIZE)).incumbent.objective_value == 99
    assert not isinstance(compile_objective_bound(model, max_edges=1), ChainBound)
    assert not isinstance(compile_objective_bound(model, max_window=1), ChainBound)


def test_bound_timeout_restores_caller_state_and_reports_unknown(monkeypatch):
    model = random_chain(6)
    state = NativeState(model)
    before = state.domains.snapshot()
    bound = compile_objective_bound(model, deadline=perf_counter() - 1)
    with pytest.raises(TimeoutError):
        bound(before)

    def timeout(self, domains):
        raise TimeoutError("bounded test")

    monkeypatch.setattr(ChainBound, "__call__", timeout)
    result = search(state, Query(QueryKind.MINIMIZE), value_policy="objective")
    assert result.status is ResultStatus.UNKNOWN
    assert result.termination is Termination.TIME_LIMIT
    assert state.domains.snapshot() == before


def test_gap_closure_can_prove_optimality_before_remaining_branches():
    x = Atom("x")
    model = FiniteModel(
        "one",
        (FiniteVariable(x, (Number(0), Number(1))),),
        objective=FactorObjective(
            (TableFactor("cost", (x,), {(Number(0),): 100}, default=-7),)
        ),
    )
    best = solve(
        model, Query(QueryKind.MINIMIZE, max_nodes=2), value_policy="objective"
    )
    assert best.status is ResultStatus.OPTIMAL
    assert best.incumbent.objective_value == -7 and best.explored_nodes == 2
    limited = solve(model, Query(QueryKind.MINIMIZE, max_nodes=2))
    assert (
        limited.status is ResultStatus.FEASIBLE
        and limited.incumbent.objective_value == 100
    )
    assert limited.objective_bound == -7


def test_text_query_compiles_search_options_and_rejects_ignored_options():
    source = """MODEL example
VARIABLE x DOMAIN SEQ[0 1]
OBJECTIVE LINEAR
TERMS SEQ[SEQ[1 x]]
END_OBJECTIVE
QUERY best MINIMIZE
BOUNDING local
VALUE_POLICY objective
END_QUERY
END_MODEL
"""
    document = parse_model_document(source)
    assert document.queries[0].value_policy == "objective"
    assert document.execute().status is ResultStatus.OPTIMAL
    for bad in (
        source.replace("MINIMIZE", "ENUMERATE"),
        source.replace("BOUNDING local", "BACKEND enumeration\nBOUNDING local"),
    ):
        with pytest.raises(ValueError, match="native optimization"):
            parse_model_document(bad)
