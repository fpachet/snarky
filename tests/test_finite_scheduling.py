"""Scheduling propagators, reference semantics, activation and rollback."""

from dataclasses import replace
from itertools import product
from random import Random

import pytest

from snarky import Atom, Fact, Number, Triple, parse_rule_groups
from snarky.finite import (
    AnyOfConstraint,
    Capacity,
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    NoOverlap,
    OptionalTask,
    Precedence,
    Query,
    QueryKind,
    ResultStatus,
    TableFactor,
    Task,
    availability_constraints,
    enumerate_model,
    solve,
)
from snarky.finite.constraints import (
    ConstraintOperator,
    LinearSumConstraint,
    TableConstraint,
)
from snarky.finite.mixed import MixedState
from snarky.finite.propagation import NativeState

X, Y, Z, R, S, P, Q = map(Atom, ("x", "y", "z", "r", "s", "p", "q"))
ALICE, BOB = Atom("alice"), Atom("bob")
A, B = Task("a", X, 3, R), Task("b", Y, 2, S)


def variable(name, values):
    return FiniteVariable(
        name, tuple(Number(v) if type(v) is int else v for v in values)
    )


def state(variables, *constraints):
    return NativeState(FiniteModel("schedule", tuple(variables), constraints))


def values(s, v):
    return set(s.domains.values(v))


def test_precedence_reuses_linear_and_prunes_both_directions():
    c = Precedence(A, B)
    assert isinstance(c, LinearSumConstraint)
    s = state((variable(X, range(8, 13)), variable(Y, range(9, 15))), c)
    assert s.propagate()
    assert values(s, X) == set(map(Number, range(8, 12)))
    assert values(s, Y) == set(map(Number, range(11, 15)))
    assert all(r.cause == c.name for r in s.domains.removals)
    impossible = state((variable(X, [12]), variable(Y, [9, 14])), c)
    assert not impossible.propagate()
    assert impossible.failure == c.name


def test_non_overlap_prunes_an_order_and_allows_touching_endpoints():
    s = state((variable(X, [8, 9]), variable(Y, [9, 10, 11, 12])), NoOverlap(A, B))
    assert s.propagate()
    assert values(s, Y) == {Number(11), Number(12)}
    s.restrict(Y, Number(11))
    assert s.propagate()
    assert values(s, X) == {Number(8)}
    assert solve(s.model).status is ResultStatus.FEASIBLE


def test_resource_non_overlap_filters_resources_and_respects_rollback():
    c = NoOverlap(A, B, when_same_resource=True)
    s = state(
        (
            variable(X, [8]),
            variable(Y, [9]),
            variable(R, [ALICE, BOB]),
            variable(S, [ALICE, BOB]),
        ),
        c,
    )
    assert s.propagate()
    before = s.domains.snapshot()
    mark = s.checkpoint()
    s.restrict(R, ALICE)
    assert s.propagate()
    assert values(s, S) == {BOB}
    s.rollback(mark)
    assert s.domains.snapshot() == before
    s.restrict(R, BOB)
    assert s.propagate()
    assert values(s, S) == {ALICE}
    s.release(mark)
    temporal = state(
        (
            variable(X, [8]),
            variable(Y, [9, 11]),
            variable(R, [ALICE]),
            variable(S, [ALICE]),
        ),
        c,
    )
    assert temporal.propagate()
    assert values(temporal, Y) == {Number(11)}


def test_capacity_violation_pruning_demands_and_absence():
    c = Capacity((A, B), capacity=2, demands=(2, 1))
    s = state((variable(X, [8]), variable(Y, [9, 10, 11])), c)
    assert s.propagate()
    assert values(s, Y) == {Number(11)}
    bad = state((variable(X, [8]), variable(Y, [9, 10])), c)
    assert not bad.propagate()
    optional = OptionalTask(B, P)
    s = state(
        (variable(X, [8]), variable(Y, [9]), variable(P, [0, 1])),
        Capacity((A, optional), capacity=1),
    )
    assert s.propagate()
    assert values(s, P) == {Number(0)}
    assert state((), Capacity((), 0)).propagate()
    assert state((variable(X, [8]),), Capacity((A,), 0, demands=(0,))).propagate()


def test_capacity_partial_domains_and_shared_variable_correlations():
    # Filter candidate starts against the already fixed first interval.
    a, b = Task("a", X, 2), Task("b", Y, 2)
    s = state((variable(X, [0]), variable(Y, [0, 1, 2, 3])), Capacity((a, b), 1))
    assert s.propagate()
    assert values(s, Y) == {Number(2), Number(3)}
    shared = Task("shared", X, 2)
    s = state((variable(X, [0, 3]),), Capacity((a, shared), 1))
    assert not s.propagate()
    shared_presence = (OptionalTask(a, P), OptionalTask(b, P))
    s = state(
        (variable(X, [0]), variable(Y, [0]), variable(P, [0, 1])),
        Capacity(shared_presence, 1),
    )
    assert s.propagate()
    assert values(s, P) == {Number(0)}


def test_availability_guard_and_optional_activation():
    constraints = availability_constraints(A, {ALICE: (8, 12), BOB: (10, 18)})
    s = state((variable(X, range(6, 14)), variable(R, [ALICE, BOB])), *constraints)
    assert s.propagate()
    assert Number(6) not in values(s, X)  # joint availability filtering
    mark = s.checkpoint()
    s.restrict(R, ALICE)
    assert s.propagate()
    assert values(s, X) == {Number(8), Number(9)}
    assert any(r.cause.name.startswith("availability:a:") for r in s.domains.removals)
    s.rollback(mark)
    s.restrict(R, BOB)
    assert s.propagate()
    assert values(s, X) == set(map(Number, range(10, 14)))
    s.release(mark)
    optional = OptionalTask(A, P)
    s = state(
        (variable(X, [6]), variable(R, [ALICE]), variable(P, [0, 1])),
        *availability_constraints(optional, {ALICE: (8, 18)}),
    )
    assert s.propagate()
    assert values(s, P) == {Number(0)}
    s = state(
        (variable(X, [8]), variable(R, [BOB])),
        *availability_constraints(A, {ALICE: (8, 18)}),
    )
    assert not s.propagate()


@pytest.mark.parametrize("factory", [Precedence, NoOverlap])
def test_optional_pair_prunes_presence_only_when_necessary(factory):
    s = state(
        (variable(X, [8]), variable(Y, [9]), variable(P, [0, 1]), variable(Q, [0, 1])),
        factory(OptionalTask(A, P), OptionalTask(B, Q)),
    )
    assert s.propagate()
    assert values(s, P) == values(s, Q) == {Number(0), Number(1)}
    mark = s.checkpoint()
    s.restrict(P, Number(1))
    assert s.propagate()
    assert values(s, Q) == {Number(0)}
    s.rollback(mark)
    s.restrict(P, Number(0))
    assert s.propagate()
    assert values(s, Q) == {Number(0), Number(1)}
    s.release(mark)


def test_anyof_scope_union_nested_tables_and_false_constant():
    c = AnyOfConstraint(
        Atom("or"),
        (
            TableConstraint(Atom("x"), (X,), ((Number(1),),)),
            AnyOfConstraint(
                Atom("nested"), (TableConstraint(Atom("y"), (Y,), ((Number(2),),)),)
            ),
        ),
    )
    s = state((variable(X, [0, 1]), variable(Y, [0, 2])), c)
    assert s.propagate()
    assert values(s, X) == {Number(0), Number(1)}
    s.restrict(X, Number(0))
    assert s.propagate()
    assert values(s, Y) == {Number(2)}
    assert not state((), AnyOfConstraint(Atom("false"), ())).propagate()
    for c in (Precedence(A, A), NoOverlap(A, A)):
        assert not state((variable(X, [0, 1]),), c).propagate()


def test_rules_activate_capacity_with_existing_guard_and_provenance():
    guard = Fact(Triple(Atom("pool"), Atom("limit"), Atom("small")))
    rules = parse_rule_groups("""
        GROUP policy
            RULE small_pool
            WHEN
                (r value alice)
            THEN
                ADD (pool limit small)
            END
        END_GROUP
    """)
    model = FiniteModel(
        "guarded",
        (variable(X, [8]), variable(Y, [9, 11]), variable(R, [ALICE, BOB])),
        (GuardedConstraint(Atom("staff_limit"), guard, Capacity((A, B), 1)),),
        rules=rules,
    )
    s = MixedState(model)
    assert s.propagate()
    before = s.domains.snapshot()
    mark = s.checkpoint()
    s.restrict(R, ALICE)
    assert s.propagate()
    assert values(s, Y) == {Number(11)}
    solution = s.solution()
    assert guard in solution.facts
    assert solution.derivations
    assert any(r.cause == Atom("staff_limit") for r in solution.reductions)
    s.rollback(mark)
    assert s.domains.snapshot() == before
    assert guard not in s.closed_facts()
    s.restrict(R, BOB)
    assert s.propagate()
    assert values(s, Y) == {Number(9), Number(11)}
    s.release(mark)


def test_table_preferences_and_combined_optimization_remain_soft():
    ops = TableFactor("operational", (X,), {(Number(8),): 2})
    preference = TableFactor("early_penalty", (X,), {(Number(6),): 5})
    model = FiniteModel(
        "preferences",
        (variable(X, [6, 8]),),
        objective=FactorObjective((ops, preference)),
    )
    all_solutions = solve(model, Query(QueryKind.ENUMERATE))
    assert {s.objective_value for s in all_solutions.solutions} == {2, 5}
    operational = solve(
        replace(model, objective=FactorObjective((ops,))), Query(QueryKind.MINIMIZE)
    )
    combined = solve(model, Query(QueryKind.MINIMIZE))
    assert operational.incumbent.assignment[X] == Number(6)
    assert combined.incumbent.assignment[X] == Number(8)
    assert combined.incumbent.objective_value == 2


def test_random_small_schedules_match_direct_slot_oracle():
    rng = Random(781)
    variables = (
        variable(X, [-1, 0, 2]),
        variable(Y, [0, 1, 3]),
        variable(R, [ALICE, BOB]),
        variable(S, [ALICE, BOB]),
        variable(P, [0, 1]),
        variable(Q, [0, 1]),
    )
    names = tuple(v.name for v in variables)
    for _ in range(12):
        a = Task("a", X, rng.randint(1, 3), R, P)
        b = Task("b", Y, rng.randint(1, 3), S, Q)
        demand = (rng.randint(0, 2), rng.randint(0, 2))
        limit = rng.randint(0, 3)
        model = FiniteModel(
            "random",
            variables,
            (NoOverlap(a, b, when_same_resource=True), Capacity((a, b), limit, demand)),
        )
        expected = set()
        for row in product(*(v.domain for v in variables)):
            x, y, r, s, p, q = row
            disjoint = (
                x.value + a.duration <= y.value or y.value + b.duration <= x.value
            )
            if p.value and q.value and r == s and not disjoint:
                continue
            if any(
                (demand[0] if p.value and x.value <= t < x.value + a.duration else 0)
                + (demand[1] if q.value and y.value <= t < y.value + b.duration else 0)
                > limit
                for t in range(-1, 7)
            ):
                continue
            expected.add(row)
        reference = enumerate_model(model, Query(QueryKind.ENUMERATE))
        assert {
            tuple(s.assignment[v] for v in names) for s in reference.solutions
        } == expected
        for reverse in (False, True):
            actual = solve(model, Query(QueryKind.ENUMERATE), reverse_values=reverse)
            assert {
                tuple(s.assignment[v] for v in names) for s in actual.solutions
            } == expected
        root = NativeState(model)
        if root.propagate():
            for row in expected:
                assert all(
                    value in values(root, var)
                    for var, value in zip(names, row, strict=True)
                )
        else:
            assert not expected


def test_maximum_working_time_uses_existing_channels_and_linear_sum():
    hours = Z
    model = FiniteModel(
        "hours",
        (variable(R, [ALICE, BOB]), variable(hours, [0, 3])),
        (
            TableConstraint(
                Atom("assigned_hours"),
                (R, hours),
                ((ALICE, Number(3)), (BOB, Number(0))),
            ),
            LinearSumConstraint(
                Atom("alice_hours"), ((1, hours),), ConstraintOperator.LESS_EQUAL, 2
            ),
        ),
    )
    s = NativeState(model)
    assert s.propagate()
    assert values(s, R) == {BOB}


@pytest.mark.parametrize("duration", [0, -1, True, 1.5])
def test_invalid_task_duration(duration):
    with pytest.raises(ValueError, match="positive integer"):
        Task("invalid", X, duration)


def test_invalid_scheduling_arguments():
    with pytest.raises(ValueError, match="resource"):
        NoOverlap(Task("a", X, 1), B, when_same_resource=True)
    with pytest.raises(ValueError, match="demands"):
        Capacity((A, B), 1, [1])
    with pytest.raises(ValueError, match="capacity"):
        Capacity((A,), -1)
    with pytest.raises(ValueError, match="integer"):
        availability_constraints(A, {ALICE: (8.5, 18)})
    with pytest.raises(ValueError, match="presence"):
        state(
            (variable(X, [0]), variable(P, [2])), Capacity((OptionalTask(A, P),), 1)
        ).propagate()


def test_cumulative_three_tasks_and_weak_propagation_is_documented():
    tasks = (Task("a", X, 2), Task("b", Y, 2), Task("c", Z, 2))
    s = state(
        (variable(X, [0]), variable(Y, [0]), variable(Z, [0, 1, 2])), Capacity(tasks, 2)
    )
    assert s.propagate()
    assert values(s, Z) == {Number(2)}
    # No mandatory-part/energetic reasoning: search detects this impossibility.
    weak = state(
        (variable(X, [0, 1]), variable(Y, [0, 1]), variable(Z, [0, 1])),
        Capacity(tasks, 2),
    )
    assert weak.propagate()
    assert solve(weak.model).status is ResultStatus.INFEASIBLE


def test_workforce_demo_rule_preferences_optimum_and_explanations():
    from benchmarks.workforce_scheduling import WORKERS, build_model, costs

    model, tasks = build_model()
    assert len(WORKERS) == 5 and len(tasks) == 10
    baseline = solve(replace(model, objective=None)).incumbent
    result = solve(model, Query(QueryKind.MINIMIZE))
    oracle = enumerate_model(model, Query(QueryKind.MINIMIZE))
    assert result.status is ResultStatus.OPTIMAL
    assert result.incumbent.objective_value == oracle.incumbent.objective_value == 12
    assert costs(model, baseline) == (0, 24)
    assert costs(model, result.incumbent) == (6, 6)
    assert baseline.assignment != result.incumbent.assignment
    contributions = model.objective.contributions(baseline.assignment, baseline.facts)
    early = next(c for c in contributions if c.factor_name == "human:early")
    assert early.value == 5 and early.support_facts
    assert Fact(Triple(Atom("alice"), Atom("avoid"), Atom("early"))) in baseline.facts
    assert baseline.derivations
    # Persona updates remove their rule-derived preference without changing the
    # hard feasibility constraints or inventing another activation mechanism.
    no_commute = replace(
        model,
        context=tuple(
            f
            for f in model.context
            if f.entity != Triple(Atom("alice"), Atom("commute"), Number(60))
        ),
    )
    rescored = solve(no_commute).incumbent
    assert not any(c.factor_name == "human:early" for c in rescored.contributions)
    assert costs(no_commute, rescored)[1] == 19
    no_human, _ = build_model(human_weight=0)
    operational = solve(no_human, Query(QueryKind.MINIMIZE))
    assert operational.incumbent.objective_value == 0


def test_capacity_large_time_offsets_and_deadline():
    from time import perf_counter

    from snarky.finite.capacity import revise_capacity

    origin = 10**12
    a, b = Task("a", X, 10**9), Task("b", Y, 2)
    c = Capacity((a, b), 1)
    s = state((variable(X, [origin]), variable(Y, [origin, origin + 10**9])), c)
    assert s.propagate()
    assert values(s, Y) == {Number(origin + 10**9)}
    with pytest.raises(TimeoutError):
        revise_capacity(
            c, {X: {Number(0)}, Y: {Number(1)}}, deadline=perf_counter() - 1
        )
