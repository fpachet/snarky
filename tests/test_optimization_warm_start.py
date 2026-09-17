"""Warm starts are fully checked assignments, with fresh scores and rollback."""

from dataclasses import replace

import pytest

from snarky import Atom, Number
from snarky.finite import (
    Query,
    QueryKind,
    ResultStatus,
    Termination,
    enumerate_model,
    solve,
)
from snarky.finite.mixed import MixedState
from snarky.finite.propagation import NativeState
from snarky.finite.search import search
from tests.test_finite_mixed import allocation


@pytest.mark.parametrize("mixed", [False, True])
@pytest.mark.parametrize("kind", [QueryKind.MINIMIZE, QueryKind.MAXIMIZE])
def test_seed_checked_rescored_and_search_restores_domains_and_facts(mixed, kind):
    model = allocation()
    if not mixed:
        model = replace(model, rules=(), constraints=model.constraints[:1])
    state = MixedState(model) if mixed else NativeState(model)
    before = state.domains.snapshot()
    before_facts = state.session.snapshot().facts if mixed else None
    oracle = enumerate_model(model, Query(kind))
    seeds = enumerate_model(model, Query(QueryKind.ENUMERATE)).solutions
    for seed in seeds:
        result = search(
            state,
            Query(kind),
            initial_assignment=seed.assignment,
            value_policy="objective",
        )
        assert result.status is ResultStatus.OPTIMAL
        assert result.incumbent.objective_value == oracle.incumbent.objective_value
        assert result.incumbent_history[0].explored_nodes == 0
        assert result.incumbent_history[0].value == seed.objective_value
        assert state.domains.snapshot() == before
        if mixed:
            assert state.session.snapshot().facts == before_facts


def test_invalid_seed_rejected_with_state_restored():
    state = MixedState(allocation())
    before = state.domains.snapshot()
    for assignment in (
        {},
        {Atom("x"): Number(99)},
        {Atom("x"): Number(1), Atom("y"): Number(2), Atom("z"): Number(3)},
    ):
        with pytest.raises(ValueError, match="initial assignment"):
            search(state, Query(QueryKind.MAXIMIZE), initial_assignment=assignment)
        assert state.domains.snapshot() == before
        assert not state.session.facts
    with pytest.raises(ValueError, match="optimization"):
        solve(state.model, initial_assignment={})
    seed = enumerate_model(state.model).incumbent.assignment
    state.restrict(Atom("x"), Number(1))
    with pytest.raises(ValueError, match="current domains"):
        search(state, Query(QueryKind.MAXIMIZE), initial_assignment=seed)


def test_valid_seed_survives_compilation_timeout(monkeypatch):
    # Import the module explicitly (the public package may export a function).
    import importlib

    module = importlib.import_module("snarky.finite.search")
    model = allocation()
    seed = enumerate_model(model).incumbent

    def timeout(*args, **kwargs):
        raise TimeoutError("test compilation")

    monkeypatch.setattr(module, "compile_objective_bound", timeout)
    state = MixedState(model)
    before = state.domains.snapshot()
    result = search(
        state, Query(QueryKind.MAXIMIZE), initial_assignment=seed.assignment
    )
    assert result.status is ResultStatus.FEASIBLE
    assert result.termination is Termination.TIME_LIMIT
    assert result.incumbent.objective_value == seed.objective_value
    assert result.objective_bound is None
    assert state.domains.snapshot() == before
