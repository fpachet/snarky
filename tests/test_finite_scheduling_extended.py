"""Extended workforce relations: filtering, independent semantics and rollback."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    AllOfConstraint,
    Coverage,
    ExactlyOne,
    FiniteModel,
    NoOverlap,
    OptionalTask,
    Precedence,
    Query,
    QueryKind,
    ResourceLoadConstraint,
    ResultStatus,
    StartWindow,
    Task,
    Workload,
    availability_constraints,
    enumerate_model,
    no_overlap_constraints,
    resource_capacity_constraints,
    solve,
)
from snarky.finite.propagation import NativeState
from tests.test_finite_scheduling import (
    ALICE,
    BOB,
    A,
    B,
    P,
    Q,
    R,
    S,
    X,
    Y,
    Z,
    state,
    values,
    variable,
)


def test_precedence_lags_rest_and_window_filter_both_sides():
    s = state(
        (variable(X, [6, 7, 8]), variable(Y, [8, 10, 11, 12, 13])),
        Precedence(A, B, min_lag=2, max_lag=3),
        StartWindow(B, 8, 14),
    )
    assert s.propagate()
    assert values(s, X) == {Number(6), Number(7)}
    assert values(s, Y) == {Number(11), Number(12)}
    rest = state(
        (variable(X, [6]), variable(Y, [9, 10, 11])), NoOverlap(A, B, min_gap=2)
    )
    assert rest.propagate() and values(rest, Y) == {Number(11)}
    optional = state(
        (variable(X, [0]), variable(P, [0, 1])), StartWindow(OptionalTask(A, P), 8, 18)
    )
    assert optional.propagate() and values(optional, P) == {Number(0)}
    assert state((), AllOfConstraint(Atom("true"), ())).propagate()


def test_availability_multiple_windows_resource_pruning_and_touching_windows():
    windows = {ALICE: ((8, 10), (13, 18)), BOB: ((9, 11), (11, 13))}
    c = availability_constraints(A, windows)
    s = state(
        (variable(X, [8, 9, 10, 11, 12, 13, 14, 16]), variable(R, [ALICE, BOB])), *c
    )
    assert s.propagate()
    assert values(s, X) == set(map(Number, [9, 10, 13, 14]))
    mark = s.checkpoint()
    s.restrict(X, Number(13))
    assert s.propagate() and values(s, R) == {ALICE}
    s.rollback(mark)
    s.restrict(R, BOB)
    assert s.propagate() and values(s, X) == {Number(9), Number(10)}
    s.release(mark)
    # A worker with no fitting interval is removed before either variable is fixed.
    s = state((variable(X, [9, 10]), variable(R, [ALICE, BOB])), *c)
    assert s.propagate() and values(s, R) == {BOB}


def test_exactly_one_optional_alternatives_and_shared_presence():
    a, b = OptionalTask(A, P), OptionalTask(B, Q)
    s = state((variable(P, [0, 1]), variable(Q, [0, 1])), ExactlyOne((a, b)))
    assert s.propagate()
    s.restrict(P, Number(1))
    assert s.propagate() and values(s, Q) == {Number(0)}
    s = state((variable(P, [0, 1]),), ExactlyOne((A, b := OptionalTask(B, P))))
    assert s.propagate() and values(s, P) == {Number(0)}
    shared = state((variable(P, [0, 1]),), ExactlyOne((a, b)))
    assert not shared.propagate()
    assert not state((), ExactlyOne(())).propagate()


def test_coverage_prunes_presence_worker_and_start_choices():
    a = Task("coverage", X, 2, R, P)
    s = state(
        (variable(X, [7, 8, 9]), variable(R, [ALICE, BOB]), variable(P, [0, 1])),
        Coverage((a,), (8, 10), 1, resources=(ALICE,)),
    )
    assert s.propagate()
    assert values(s, X) == {Number(8)}
    assert values(s, R) == {ALICE}
    assert values(s, P) == {Number(1)}
    assert not state((), Coverage((), (8, 9), 1)).propagate()
    assert state((), Coverage((), (8, 8), 1)).propagate()
    # A late gap must fail even if the start of the coverage window is staffed.
    assert not state(
        (variable(X, [8]),), Coverage((Task("a", X, 1),), (8, 10), 1)
    ).propagate()


def test_resource_capacity_filters_resource_assignment_and_weighted_demands():
    c = resource_capacity_constraints((A, B), {ALICE: 2}, demands=(2, 1))
    s = state(
        (
            variable(X, [8]),
            variable(Y, [8]),
            variable(R, [ALICE]),
            variable(S, [ALICE, BOB]),
        ),
        *c,
    )
    assert s.propagate() and values(s, S) == {BOB}
    c = resource_capacity_constraints((A, B), {ALICE: 2, BOB: 1})
    s = state(
        (
            variable(X, [8]),
            variable(Y, [8]),
            variable(R, [BOB]),
            variable(S, [ALICE, BOB]),
        ),
        *c,
    )
    assert s.propagate() and values(s, S) == {ALICE}


def test_workload_max_min_clipping_presence_and_shared_assignments():
    s = state(
        (variable(R, [ALICE]), variable(S, [ALICE, BOB])), Workload((A, B), ALICE, 4)
    )
    assert s.propagate() and values(s, S) == {BOB}
    s = state(
        (variable(R, [ALICE]), variable(S, [ALICE, BOB])),
        Workload((A, B), ALICE, 5, minimum=5),
    )
    assert s.propagate() and values(s, S) == {ALICE}
    a = OptionalTask(A, P)
    s = state((variable(R, [ALICE]), variable(P, [0, 1])), Workload((a,), ALICE, 2))
    assert s.propagate() and values(s, P) == {Number(0)}
    s = state(
        (variable(X, [6, 7, 8]), variable(R, [ALICE])),
        Workload((A,), ALICE, 1, window=(8, 12)),
    )
    assert s.propagate() and values(s, X) == {Number(6)}
    shared = replace(B, resource=R)
    s = state((variable(R, [ALICE, BOB]),), Workload((A, shared), ALICE, 4))
    assert s.propagate() and values(s, R) == {BOB}


def test_pair_generation_preserves_solutions_and_skips_provably_safe_pairs():
    tasks = (Task("a", X, 2, R), Task("b", Y, 2, S), Task("c", Z, 2, R))
    variables = (
        variable(X, [0, 1]),
        variable(Y, [0, 1]),
        variable(Z, [5, 6]),
        variable(R, [ALICE]),
        variable(S, [BOB]),
    )
    model = FiniteModel("pairs", variables)
    assert no_overlap_constraints(tasks, model.domains) == ()
    assert len(no_overlap_constraints(tasks, model.domains, min_gap=5)) == 1
    unfiltered = replace(
        model,
        constraints=tuple(
            NoOverlap(a, b, when_same_resource=True)
            for i, a in enumerate(tasks)
            for b in tasks[i + 1 :]
        ),
    )
    filtered = replace(model, constraints=no_overlap_constraints(tasks, model.domains))
    assert len(solve(unfiltered, Query(QueryKind.ENUMERATE)).solutions) == len(
        solve(filtered, Query(QueryKind.ENUMERATE)).solutions
    )


def test_seeded_load_constraints_match_direct_assignment_oracle():
    rng = Random(931)
    names = (X, Y, R, S, P, Q)
    variables = (
        variable(X, [-1, 0, 2]),
        variable(Y, [0, 1, 2]),
        variable(R, [ALICE, BOB]),
        variable(S, [ALICE, BOB]),
        variable(P, [0, 1]),
        variable(Q, [0, 1]),
    )
    for i in range(15):
        a = Task("a", X, rng.randint(1, 3), R, P)
        b = Task("b", Y, rng.randint(1, 3), S, Q)
        minimum, maximum = rng.randint(0, 1), rng.randint(1, 2)
        hours_min, hours_max = rng.randint(0, 1), rng.randint(1, 4)
        constraints = (
            ResourceLoadConstraint(
                Atom("pool"), (a, b), minimum, maximum, (0, 3), (ALICE,), (1, 1)
            ),
            Workload((a, b), ALICE, hours_max, minimum=hours_min, window=(0, 3)),
        )
        model = FiniteModel("random_load", variables, constraints)
        expected = set()
        for row in product(*(v.domain for v in variables)):
            x, y, r, s, p, q = row
            loads = [
                sum(
                    int(
                        pres.value
                        and worker == ALICE
                        and start.value <= t < start.value + task.duration
                    )
                    for task, start, worker, pres in ((a, x, r, p), (b, y, s, q))
                )
                for t in range(3)
            ]
            if (
                all(minimum <= load <= maximum for load in loads)
                and hours_min <= sum(loads) <= hours_max
            ):
                expected.add(row)
        for result in (
            enumerate_model(model, Query(QueryKind.ENUMERATE)),
            solve(model, Query(QueryKind.ENUMERATE), reverse_values=bool(i % 2)),
        ):
            assert {
                tuple(s.assignment[v] for v in names) for s in result.solutions
            } == expected
        root = NativeState(model)
        checkpoint = root.checkpoint()
        if root.propagate():
            for row in expected:
                assert all(
                    v in values(root, n) for n, v in zip(names, row, strict=True)
                )
        else:
            assert not expected
        root.rollback(checkpoint)
        assert root.domains.snapshot() == model.domains
        root.release(checkpoint)


def test_scheduling_validation():
    for lag in (-1, True, 0.5):
        with pytest.raises(ValueError):
            Precedence(A, B, min_lag=lag)
    with pytest.raises(ValueError):
        Precedence(A, B, min_lag=2, max_lag=1)
    with pytest.raises(ValueError):
        Coverage((A,), (3, 1), 1)
    with pytest.raises(ValueError):
        Workload((A,), ALICE, 1, minimum=2)
    with pytest.raises(ValueError):
        availability_constraints(A, {ALICE: ((8, 7),)})


def test_extended_workforce_integration_and_absent_preferences():
    from benchmarks.workforce_scheduling_extended import build_extended_model

    model, tasks = build_extended_model()
    result = solve(
        model, Query(QueryKind.MINIMIZE, max_nodes=2000), value_policy="objective"
    )
    assert result.status is ResultStatus.OPTIMAL
    assert result.incumbent.objective_value == 8
    assignment = result.incumbent.assignment
    active = [
        t for t in tasks if t.present is None or assignment[t.present] == Number(1)
    ]
    assert len(active) == 11  # ten mandatory tasks and one follow-up
    for t in active:
        start = assignment[t.start].value
        assert start + t.duration <= 12 or start >= 14
    for worker in {assignment[t.resource] for t in active}:
        intervals = sorted(
            (assignment[t.start].value, t.duration)
            for t in active
            if assignment[t.resource] == worker
        )
        assert 1 <= sum(d for _, d in intervals) <= 6
        assert all(
            s + d + 1 <= following
            for (s, d), (following, _) in zip(intervals, intervals[1:], strict=False)
        )
    assert all(
        sum(
            assignment[t.start].value <= slot < assignment[t.start].value + t.duration
            for t in active
        )
        >= 2
        for slot in (8, 9, 16)
    )
    absent = next(t for t in tasks if t not in active)
    assert not any(
        c.scope == (Atom(absent.name),) for c in result.incumbent.contributions
    )
    assert result.incumbent.derivations


def test_interrupted_revision_can_resume_without_losing_the_queue(monkeypatch):
    s = state(
        (variable(X, [0, 8]), variable(R, [ALICE])),
        *availability_constraints(A, {ALICE: (8, 18)}),
    )
    original = s._revise_constraint

    def interrupted(*args, **kwargs):
        raise TimeoutError("interrupted kernel")

    monkeypatch.setattr(s, "_revise_constraint", interrupted)
    with pytest.raises(TimeoutError):
        s.propagate()
    monkeypatch.setattr(s, "_revise_constraint", original)
    assert s.propagate() and values(s, X) == {Number(8)}
