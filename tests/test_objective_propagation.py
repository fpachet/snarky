"""Improving cuts preserve optima, joint fixed points and reusable search state."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Fact, Number, Triple, parse_rule_groups
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    LinearObjective,
    Query,
    QueryKind,
    solve,
)
from snarky.finite.constraints import (
    ConstraintOperator as Op,
)
from snarky.finite.constraints import (
    LinearSumConstraint,
    TableConstraint,
)
from snarky.finite.mixed import MixedState
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

X, Y, C, Z = map(Atom, ("x", "y", "cost", "z"))


def variable(name, values):
    return FiniteVariable(name, tuple(map(Number, values)))


def test_signed_holey_objectives_match_exhaustive_optima_with_and_without_cuts():
    rng = Random(17391)
    for _ in range(100):
        domains = [rng.sample(range(-4, 6), rng.randrange(1, 5)) for _ in range(3)]
        coefficients = [rng.choice((-3, -1, 1, 2)) for _ in domains]
        offset = rng.choice((-(10**30), 0, 10**30))
        target = rng.randrange(-6, 7)
        rows = [row for row in product(*domains) if row[0] + row[1] - row[2] >= target]
        model = FiniteModel(
            "oracle",
            tuple(variable(v, d) for v, d in zip((X, Y, C), domains, strict=True)),
            (
                LinearSumConstraint(
                    Atom("limit"), ((1, X), (1, Y), (-1, C)), Op.GREATER_EQUAL, target
                ),
            ),
            objective=LinearObjective(
                tuple(zip(coefficients, (X, Y, C), strict=True)), offset
            ),
        )
        scores = [
            offset + sum(a * b for a, b in zip(coefficients, row, strict=True))
            for row in rows
        ]
        for kind, best in ((QueryKind.MINIMIZE, min), (QueryKind.MAXIMIZE, max)):
            for enabled in (False, True):
                seed = (
                    dict(zip((X, Y, C), map(Number, rows[-1]), strict=True))
                    if rows
                    else None
                )
                result = solve(
                    model,
                    Query(kind),
                    reverse_values=True,
                    objective_propagation=enabled,
                    initial_assignment=seed,
                )
                assert result.complete
                if scores:
                    assert result.status.value == "optimal"
                    assert (
                        result.incumbent.objective_value
                        == result.objective_bound
                        == best(scores)
                    )
                    assert (
                        tuple(result.incumbent.assignment[v].value for v in (X, Y, C))
                        in rows
                    )
                else:
                    assert result.status.value == "infeasible"


def test_cost_cut_propagates_through_sum_and_rules_and_rolls_back():
    ready = Fact(Triple(Atom("plan"), Atom("state"), Atom("ready")))
    model = FiniteModel(
        "mixed cut",
        (
            variable(X, range(4)),
            variable(Y, range(4)),
            variable(C, range(7)),
            variable(Z, (7, 8)),
        ),
        (
            LinearSumConstraint(
                Atom("cost_definition"), ((1, X), (1, Y), (-1, C)), Op.EQUAL, 0
            ),
            GuardedConstraint(
                Atom("ready_requires_seven"),
                ready,
                TableConstraint(Atom("seven"), (Z,), ((Number(7),),)),
            ),
        ),
        rules=parse_rule_groups("""GROUP classify
            RULE zero
            WHEN
                (x value 0)
                (y value 0)
            THEN
                ADD (plan state ready)
            END
            END_GROUP"""),
        objective=LinearObjective(((1, C),)),
    )
    state = MixedState(model)
    root = state.checkpoint()
    domains, facts = state.domains.snapshot(), state.session.snapshot().facts
    assert state.propagate(
        objective_cut=LinearSumConstraint(Atom("cut"), ((1, C),), Op.LESS_EQUAL, 0)
    )
    assert state.domains.complete
    assert ready in state.session.facts
    assert state.domains.values(Z) == (Number(7),)
    state.rollback(root)
    state.release(root)
    assert (
        state.domains.snapshot() == domains and state.session.snapshot().facts == facts
    )
    seed = {X: Number(3), Y: Number(3), C: Number(6), Z: Number(8)}
    result = search(state, Query(QueryKind.MINIMIZE), initial_assignment=seed)
    assert result.status.value == "optimal" and result.objective_bound == 0
    assert (
        state.domains.snapshot() == domains and state.session.snapshot().facts == facts
    )


def test_cut_is_rescheduled_when_another_constraint_changes_its_scope():
    model = FiniteModel(
        "fixed point",
        (variable(X, range(6)), variable(Y, range(6))),
        (LinearSumConstraint(Atom("lower_y"), ((1, Y),), Op.GREATER_EQUAL, 4),),
    )
    state = NativeState(model)
    assert state.propagate(
        objective_cut=LinearSumConstraint(
            Atom("cut"), ((1, X), (1, Y)), Op.LESS_EQUAL, 4
        )
    )
    assert state.domains.values(X) == (Number(0),)
    assert state.domains.values(Y) == (Number(4),)


def branch_model():
    return FiniteModel(
        "rollback",
        (variable(X, range(5)), variable(Y, range(5))),
        (
            LinearSumConstraint(
                Atom("__objective_cut"), ((1, X), (1, Y)), Op.GREATER_EQUAL, 3
            ),
        ),
        objective=LinearObjective(((1, X), (1, Y))),
    )


def test_latest_cut_is_reapplied_after_backtracking_and_state_can_be_reused():
    cuts = []

    class TrackedState(NativeState):
        def propagate(self, **kwargs):
            cut = kwargs.get("objective_cut")
            if cut is not None:
                cuts.append(cut)
            return super().propagate(**kwargs)

    state = TrackedState(branch_model())
    original = state.domains.snapshot()
    result = search(state, Query(QueryKind.MINIMIZE), reverse_values=True)
    assert result.status.value == "optimal" and result.objective_bound == 3
    assert len(result.incumbent_values) > 2
    assert cuts and all(c.name == Atom("__objective_cut_") for c in cuts)
    assert [c.target for c in cuts] == sorted((c.target for c in cuts), reverse=True)
    assert state.domains.snapshot() == original and not state.domains.removals
    again = search(state, Query(QueryKind.ENUMERATE))
    assert len(again.solutions) == sum(
        x + y >= 3 for x, y in product(range(5), repeat=2)
    )


@pytest.mark.parametrize("interruption", ["exception", "timeout", "node_limit"])
def test_interrupted_improvement_search_restores_domains_and_preserves_seed(
    interruption,
):
    class InterruptedState(NativeState):
        def propagate(self, **kwargs):
            ok = super().propagate(**kwargs)
            if kwargs.get("objective_cut") is not None:
                if interruption == "timeout":
                    raise TimeoutError("cut interrupted")
                if interruption == "exception":
                    raise RuntimeError("cut interrupted")
            return ok

    state = InterruptedState(branch_model())
    parent = state.checkpoint()
    state.restrict(X, Number(4))
    before, removals = state.domains.snapshot(), state.domains.removals
    options = dict(initial_assignment={X: Number(4), Y: Number(4)})
    query = Query(QueryKind.MINIMIZE, max_nodes=1)
    if interruption == "exception":
        with pytest.raises(RuntimeError, match="cut interrupted"):
            search(state, query, **options)
    else:
        result = search(state, query, **options)
        assert not result.complete and result.status.value == "feasible"
        assert result.incumbent.objective_value == 8
        assert result.termination.value == (
            "time_limit" if interruption == "timeout" else "node_limit"
        )
    assert state.domains.snapshot() == before and state.domains.removals == removals
    state.rollback(parent)
    state.release(parent)


def test_constant_and_cancelled_objective_and_satisfaction_ignore_cuts():
    model = FiniteModel(
        "constant",
        (variable(X, range(3)),),
        objective=LinearObjective(((1, X), (-1, X)), 17),
    )
    for kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE):
        result = solve(model, Query(kind), initial_assignment={X: Number(2)})
        assert result.status.value == "optimal" and result.objective_bound == 17
    assert len(solve(model, Query(QueryKind.ENUMERATE)).solutions) == 3
