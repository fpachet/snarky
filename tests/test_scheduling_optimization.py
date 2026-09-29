"""Exhaustive support/schedule oracles for scheduling propagation improvements."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import FiniteModel, FiniteVariable
from snarky.finite.constraints import (
    AnyOfConstraint,
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.propagation import NativeState


def test_archive_verifier_checks_constructive_history(monkeypatch):
    from copy import deepcopy

    from benchmarks import scheduling_verify
    from benchmarks.scheduling_instances import JobShop

    instance = JobShop("tiny", (((0, 2),),), 1)
    monkeypatch.setattr(scheduling_verify, "load_instance", lambda *args: instance)
    monkeypatch.setattr(scheduling_verify, "reference", lambda *args: (2, "optimal"))
    witness = dict(starts=[0], objective=2)
    archive = dict(
        manifest={},
        runs=[
            dict(
                instance="tiny",
                status="optimal",
                objective=2,
                bound=2,
                reference_objective=2,
                reference_status="optimal",
                witnesses=[witness],
                heuristic={**witness, "history": [witness]},
            )
        ],
    )
    assert scheduling_verify.verify(archive, None) == 3
    invalid = deepcopy(archive)
    invalid["runs"][0]["heuristic"]["history"][0] = {**witness, "starts": [-1]}
    with pytest.raises(ValueError):
        scheduling_verify.verify(invalid, None)
    invalid = deepcopy(archive)
    invalid["runs"][0]["heuristic"]["history"].append(witness)
    with pytest.raises(ValueError, match="does not improve"):
        scheduling_verify.verify(invalid, None)


def test_compiled_disjunction_exact_supports_and_rollback():
    rng = Random(329)
    x, y = Atom("x"), Atom("y")
    for case in range(300):
        values = [
            tuple(sorted(rng.sample(range(-5, 7), rng.randrange(1, 8))))
            for _ in range(2)
        ]
        shift = 10**30 if case % 7 == 0 else 0
        values = [tuple(v + shift for v in vs) for vs in values]
        cs = []
        for side in range(2):
            terms = ((rng.choice((-2, -1, 1, 2)), x), (rng.choice((-2, -1, 1, 2)), y))
            if side:
                terms = terms[::-1]
            cs.append(
                LinearSumConstraint(
                    Atom(f"c{side}"),
                    terms,
                    rng.choice(tuple(ConstraintOperator)),
                    rng.randrange(-9, 10) + shift * sum(c for c, _ in terms),
                )
            )
        model = FiniteModel(
            "or",
            (
                FiniteVariable(x, tuple(map(Number, values[0]))),
                FiniteVariable(y, tuple(map(Number, values[1]))),
            ),
            (AnyOfConstraint(Atom("or"), tuple(cs)),),
        )

        def acceptable(a, b, cs=cs):
            assignment = {x: a, y: b}
            for c in cs:
                value = sum(k * assignment[v] for k, v in c.terms)
                if (
                    (value == c.target)
                    if c.operator is ConstraintOperator.EQUAL
                    else (value <= c.target)
                    if c.operator is ConstraintOperator.LESS_EQUAL
                    else (value >= c.target)
                ):
                    return True
            return False

        for masks in (False, True):
            state = NativeState(model, numeric_masks=masks)
            root = state.checkpoint()
            for restriction in (None, (x, values[0][0]), (y, values[1][-1])):
                state.rollback(root)
                if restriction:
                    state.restrict(restriction[0], Number(restriction[1]))
                expected = [
                    (a, b)
                    for a, b in product(*values)
                    if acceptable(a, b)
                    and (
                        restriction is None
                        or {x: a, y: b}[restriction[0]] == restriction[1]
                    )
                ]
                assert state.propagate() == bool(expected)
                if expected:
                    for i, v in enumerate((x, y)):
                        assert set(state.domains.values(v)) == {
                            Number(row[i]) for row in expected
                        }
            state.rollback(root)
            state.release(root)


def test_numeric_disjunction_falls_back_when_budget_exhausted(monkeypatch):
    from snarky.finite import numeric

    monkeypatch.setattr(numeric, "_MAX_ENTRIES", 0)
    x, y = Atom("x"), Atom("y")
    cs = tuple(
        LinearSumConstraint(
            Atom(f"c{i}"), ((1, a), (-1, b)), ConstraintOperator.LESS_EQUAL, -2
        )
        for i, (a, b) in enumerate(((x, y), (y, x)))
    )
    model = FiniteModel(
        "or",
        tuple(FiniteVariable(v, tuple(map(Number, range(3)))) for v in (x, y)),
        (AnyOfConstraint(Atom("or"), cs),),
    )
    state = NativeState(model)
    assert state.propagate()
    assert set(state.domains.values(x)) == {Number(0), Number(2)}
    assert set(state.domains.values(y)) == {Number(0), Number(2)}


def test_numeric_disjunction_guard_activation_and_rollback():
    from snarky import Fact
    from snarky.finite import GuardedConstraint

    x, y = Atom("x"), Atom("y")
    guard = Fact(Atom("active"))
    alternatives = tuple(
        LinearSumConstraint(
            Atom(f"c{i}"), ((1, a), (-1, b)), ConstraintOperator.LESS_EQUAL, -2
        )
        for i, (a, b) in enumerate(((x, y), (y, x)))
    )
    constraint = GuardedConstraint(
        Atom("guarded"), guard, AnyOfConstraint(Atom("or"), alternatives)
    )
    model = FiniteModel(
        "guard",
        tuple(FiniteVariable(v, tuple(map(Number, range(3)))) for v in (x, y)),
        (constraint,),
    )
    for masks in (False, True):
        state = NativeState(model, numeric_masks=masks)
        assert state.propagate()
        root = state.checkpoint()
        assert state.propagate(facts=frozenset((guard,)))
        assert set(state.domains.values(x)) == {Number(0), Number(2)}
        assert all(r.cause == Atom("guarded") for r in state.domains.removals)
        state.rollback(root)
        assert state.propagate(facts=frozenset())
        assert set(state.domains.values(x)) == set(map(Number, range(3)))
        assert state.propagate(facts=frozenset((guard,)))
        assert set(state.domains.values(x)) == {Number(0), Number(2)}
        state.release(root)


def test_capacity_random_exhaustive_oracle():
    from snarky.finite import Capacity, Query, QueryKind, Task, solve

    rng = Random(927)
    for case in range(250):
        n = rng.randrange(1, 5)
        names = tuple(Atom(f"s{i}") for i in range(n))
        offset = 10**30 if case % 11 == 0 else 0
        domains = [
            tuple(
                offset + x
                for x in sorted(rng.sample(range(-2, 5), rng.randrange(1, 5)))
            )
            for _ in names
        ]
        durations = [rng.randrange(1, 5) for _ in names]
        demands = [rng.randrange(4) for _ in names]
        cap = rng.randrange(5)
        tasks = tuple(
            Task(f"t{i}", v, d)
            for i, (v, d) in enumerate(zip(names, durations, strict=True))
        )
        model = FiniteModel(
            "capacity",
            tuple(
                FiniteVariable(v, tuple(map(Number, ds)))
                for v, ds in zip(names, domains, strict=True)
            ),
            (Capacity(tasks, cap, demands),),
        )
        expected = []
        for starts in product(*domains):
            if all(
                sum(
                    q
                    for s, d, q in zip(starts, durations, demands, strict=True)
                    if s <= t < s + d
                )
                <= cap
                for t in range(
                    min(starts),
                    max(s + d for s, d in zip(starts, durations, strict=True)),
                )
            ):
                expected.append(starts)
        state = NativeState(model)
        root = state.checkpoint()
        for restriction in (None, (names[0], domains[0][0])):
            state.rollback(root)
            remaining = [
                row
                for row in expected
                if restriction is None or row[0] == restriction[1]
            ]
            if restriction:
                state.restrict(restriction[0], Number(restriction[1]))
            consistent = state.propagate()
            if remaining:
                assert consistent
                for i, v in enumerate(names):
                    assert {Number(row[i]) for row in remaining} <= set(
                        state.domains.values(v)
                    )
            if not consistent:
                assert not remaining
        state.rollback(root)
        state.release(root)
        if case % 5 == 0:
            result = solve(model, Query(QueryKind.ENUMERATE))
            actual = {
                tuple(sol.assignment[v].value for v in names)
                for sol in result.solutions
            }
            assert actual == set(expected)


def test_capacity_compulsory_parts_and_energy_without_fixed_starts():
    from snarky.finite import Capacity, Task

    names = tuple(Atom(f"s{i}") for i in range(3))
    # Three tasks need six units inside a five-unit window. No compulsory part.
    model = FiniteModel(
        "energy",
        tuple(FiniteVariable(v, tuple(map(Number, range(4)))) for v in names),
        (Capacity(tuple(Task(f"t{i}", v, 2) for i, v in enumerate(names)), 1),),
    )
    assert not NativeState(model).propagate()
    # Compulsory [1,3) excludes exactly starts 1 and 2 for a unit task.
    model = FiniteModel(
        "parts",
        (
            FiniteVariable(names[0], (Number(0), Number(1))),
            FiniteVariable(names[1], tuple(map(Number, range(5)))),
        ),
        (Capacity((Task("a", names[0], 3), Task("b", names[1], 1)), 1),),
    )
    state = NativeState(model)
    assert state.propagate()
    assert set(state.domains.values(names[1])) == set(map(Number, (0, 3, 4)))


def test_capacity_large_durations_and_timeout_resume():
    from time import perf_counter

    from snarky.finite import Capacity, Task

    x, y = Atom("x"), Atom("y")
    unit = 10**12
    model = FiniteModel(
        "huge",
        (
            FiniteVariable(x, (Number(0), Number(1))),
            FiniteVariable(y, (Number(0), Number(unit), Number(unit + 1))),
        ),
        (Capacity((Task("a", x, unit), Task("b", y, unit)), 1),),
    )
    state = NativeState(model)
    with pytest.raises(TimeoutError):
        state.propagate(deadline=perf_counter() - 1)
    assert state.propagate()
    assert set(state.domains.values(y)) == {Number(unit), Number(unit + 1)}


@pytest.mark.parametrize("family", ["project", "jobshop"])
def test_constructive_incumbent_and_compact_model_equivalence(family):
    from benchmarks.scheduling_constructive import construct_incumbent
    from benchmarks.scheduling_instances import build_model, parse_jobshop, parse_psplib
    from snarky.finite import Query, QueryKind, solve
    from tests.test_scheduling_standard import JSP, SM

    p = parse_psplib(SM) if family == "project" else parse_jobshop(JSP, "tiny")
    seed = construct_incumbent(p, project_trials=16, jobshop_trials=32)
    repeated = construct_incumbent(p, project_trials=16, jobshop_trials=32)
    assert seed["starts"] == repeated["starts"]
    assert seed["objective"] == repeated["objective"]
    assert seed["trials"] == (16 if family == "project" else 32)
    original, _, m, _ = build_model(p)
    baseline = solve(original, Query(QueryKind.ENUMERATE))
    expected = {
        tuple(s.assignment[v.name] for v in original.variables)
        for s in baseline.solutions
        if s.assignment[m].value <= seed["objective"]
    }
    for compact in (False, True):
        model, starts, m, _ = build_model(p, compact=compact, incumbent=seed["starts"])
        got = solve(model, Query(QueryKind.ENUMERATE))
        assert {
            tuple(s.assignment[v.name] for v in model.variables) for s in got.solutions
        } == expected
        initial = dict(zip(starts, map(Number, seed["starts"]), strict=True))
        initial[m] = Number(seed["objective"])
        opt = solve(model, Query(QueryKind.MINIMIZE), initial_assignment=initial)
        assert opt.status == "optimal"
        assert opt.incumbent.objective_value == min(
            s.objective_value for s in baseline.solutions
        )
    with pytest.raises(ValueError):
        build_model(p, incumbent=[0] * len(seed["starts"]))
    with pytest.raises(ValueError):
        construct_incumbent(p, project_trials=0)
    interrupted = construct_incumbent(p, deadline=0)
    assert interrupted["trials"] == 1
