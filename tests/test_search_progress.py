"""Progress is observational, truthful at limits, and safe on exceptional exits."""

from dataclasses import FrozenInstanceError

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    LinearObjective,
    Query,
    QueryKind,
    solve,
)
from snarky.finite.constraints import (
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
)
from snarky.finite.model import PredicateConstraint
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

X, Y = Atom("x"), Atom("y")


def model():
    return FiniteModel(
        "progress",
        tuple(FiniteVariable(v, tuple(map(Number, range(3)))) for v in (X, Y)),
        (
            BinaryComparisonConstraint(
                Atom("different"), X, Y, BinaryComparisonOperator.NOT_EQUAL
            ),
        ),
        objective=LinearObjective(((1, X), (1, Y))),
    )


def test_observation_preserves_search_and_does_not_mislabel_root_bound():
    events = []
    query = Query(QueryKind.MINIMIZE)
    plain = solve(model(), query)
    observed = solve(model(), query, on_progress=events.append)
    assert observed.solutions == plain.solutions
    assert (
        observed.explored_nodes,
        observed.failed_branches,
        observed.constraint_revisions,
    ) == (plain.explored_nodes, plain.failed_branches, plain.constraint_revisions)
    assert events[0].event == "start" and events[-1].event == "finished"
    assert all(e.result is None for e in events[:-1])
    assert events[-1].result is observed and observed.complete
    assert events[-1].root_objective_bound == 0 and observed.objective_bound == 1
    assert [
        e.incumbent.objective_value for e in events if e.event == "incumbent"
    ] == list(observed.incumbent_values)
    with pytest.raises(FrozenInstanceError):
        events[-1].depth = 100


def test_node_limit_retains_progress_without_claiming_proof():
    events = []
    state = NativeState(model())
    before = state.domains.snapshot()
    result = search(
        state, Query(QueryKind.MINIMIZE, max_nodes=1), on_progress=events.append
    )
    assert not result.complete and result.status.value == "unknown"
    assert events[-1].result is result
    assert events[-1].explored_nodes == 1
    assert state.domains.snapshot() == before and state.domains.removals == ()


@pytest.mark.parametrize("event", ["start", "node", "bound", "incumbent", "finished"])
def test_observer_exception_restores_nested_state(event):
    state = NativeState(model())
    parent = state.checkpoint()
    state.restrict(X, Number(1))
    before = state.domains.snapshot()
    removals = state.domains.removals

    def observe(progress):
        if progress.event == event:
            raise RuntimeError("observer failed")

    with pytest.raises(RuntimeError, match="observer failed"):
        search(state, Query(QueryKind.MINIMIZE), on_progress=observe)
    assert state.domains.snapshot() == before and state.domains.removals == removals
    state.rollback(parent)
    state.release(parent)


def test_seed_event_is_validated_and_sampling_does_not_silently_ignore_observer():
    events = []
    result = solve(
        model(),
        Query(QueryKind.MINIMIZE),
        initial_assignment={X: Number(2), Y: Number(1)},
        on_progress=events.append,
    )
    assert [
        e.incumbent.objective_value for e in events if e.event == "incumbent"
    ] == list(result.incumbent_values)
    with pytest.raises(ValueError, match="DFS"):
        solve(model(), Query(QueryKind.SAMPLE_EXACT), on_progress=events.append)


def test_interrupted_propagation_returns_unknown_and_restores_state():
    class InterruptedState(NativeState):
        def propagate(self, **kwargs):
            super().propagate(**kwargs)
            self.restrict(X, Number(1))
            raise TimeoutError("kernel interrupted")

    state = InterruptedState(model())
    before = state.domains.snapshot()
    events = []
    result = search(state, Query(QueryKind.MINIMIZE), on_progress=events.append)
    assert result.status.value == "unknown" and result.termination.value == "time_limit"
    assert not result.complete and events[-1].result is result
    assert state.domains.snapshot() == before and state.domains.removals == ()


def test_incident_index_preserves_membership_and_declared_ties_with_aliases():
    variables = tuple(FiniteVariable(v, (Number(0), Number(1))) for v in (Y, X))
    constraint = PredicateConstraint(
        Atom("different"),
        (X, X, Y),
        lambda assignment, facts: assignment[X] != assignment[Y],
    )
    result = solve(FiniteModel("aliases", variables, (constraint,)))
    assert result.incumbent.assignment == {Y: Number(0), X: Number(1)}
