"""Independent exhaustive oracles for precedence search and local improvement."""

from itertools import product
from random import Random

import pytest

from snarky.finite.scheduling_search import (
    SchedulingProblem,
    solve_schedule,
    validate_schedule,
)


def original_valid(problem, starts):
    ds = problem.durations
    if any(
        starts[i] + ds[i] > starts[j]
        for i, row in enumerate(problem.successors)
        for j in row
    ):
        return False
    for t in range(max(s + d for s, d in zip(starts, ds, strict=True))):
        for r, cap in enumerate(problem.capacities):
            if (
                sum(
                    problem.demands[i][r]
                    for i, (s, d) in enumerate(zip(starts, ds, strict=True))
                    if s <= t < s + d
                )
                > cap
            ):
                return False
    return True


def test_order_search_matches_exhaustive_integer_schedules():
    rng = Random(4567)
    for _ in range(100):
        n = rng.randrange(1, 5)
        ds = tuple(rng.randrange(1, 4) for _ in range(n))
        caps = (rng.randrange(1, 4), rng.randrange(1, 4))
        problem = SchedulingProblem(
            ds,
            tuple(
                tuple(j for j in range(i + 1, n) if rng.random() < 0.2)
                for i in range(n)
            ),
            tuple(tuple(rng.randrange(c + 1) for c in caps) for _ in range(n)),
            caps,
        )
        seed = tuple(sum(ds[:i]) for i in range(n))
        horizon = sum(ds)
        optimum = horizon
        for starts in product(*(range(horizon - d + 1) for d in ds)):
            obj = max(s + d for s, d in zip(starts, ds, strict=True))
            if obj < optimum and original_valid(problem, starts):
                optimum = obj
        for energy, nfl, policy in (
            (False, False, "first"),
            (False, False, "critical"),
            (True, True, "first"),
            (True, True, "critical"),
        ):
            got = solve_schedule(
                problem,
                seed,
                seconds=2,
                energetic=energy,
                not_first_last=nfl,
                conflict_policy=policy,
            )
            assert got.status == "optimal"
            assert got.objective == got.bound == optimum
            assert original_valid(problem, got.starts)
            assert all(original_valid(problem, starts) for _, starts, _ in got.history)
        interrupted = solve_schedule(problem, seed, seconds=1e-12)
        assert interrupted.status == "feasible"
        assert interrupted.bound <= optimum <= interrupted.objective
        assert original_valid(problem, interrupted.starts)


def test_cumulative_cover_requires_more_than_pairwise_incompatibility():
    # Every pair fits, but all three cannot overlap. Branching only on pairs
    # whose summed demand exceeds capacity would miss this overload.
    p = SchedulingProblem((2, 2, 2), ((), (), ()), ((1,),) * 3, (2,))
    got = solve_schedule(p, (0, 2, 4))
    assert got.status == "optimal" and got.objective == 4
    assert got.nodes > 1
    assert original_valid(p, got.starts)


def test_dummies_arbitrary_indices_callbacks_and_input_validation():
    p = SchedulingProblem(
        (0, 2, 1, 0), ((2, 1), (3,), (1,), ()), ((0,), (1,), (1,), (0,)), (1,)
    )
    calls = []
    got = solve_schedule(
        p, (0, 2, 1, 4), on_incumbent=lambda obj, starts: calls.append((obj, starts))
    )
    assert got.status == "optimal" and got.objective == 3
    assert calls and validate_schedule(p, calls[-1][1]) == 3
    for seconds in [0, -1, float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            solve_schedule(p, got.starts, seconds=seconds)
    with pytest.raises(ValueError):
        solve_schedule(p, (0, 0, 0, 0))
    with pytest.raises(ValueError):
        SchedulingProblem((1, 1), ((1,), (0,)), ((1,), (1,)), (1,))
    with pytest.raises(ValueError):
        SchedulingProblem((0,), ((),), ((1,),), (1,))
    with pytest.raises(ValueError):
        SchedulingProblem((1,), ((),), ((2,),), (1,))


def test_local_search_and_derived_conflicts_preserve_models():
    from benchmarks.scheduling_constructive import construct_incumbent
    from benchmarks.scheduling_instances import build_model, parse_jobshop, parse_psplib
    from benchmarks.scheduling_local import improve_incumbent
    from snarky.finite import Query, QueryKind, solve
    from tests.test_scheduling_standard import JSP, SM

    for p in [parse_psplib(SM), parse_jobshop(JSP, "tiny")]:
        seed = construct_incumbent(p, project_trials=4, jobshop_trials=4)
        a = improve_incumbent(p, seed, iterations=30)
        b = improve_incumbent(p, seed, iterations=30)
        assert a["starts"] == b["starts"] and a["objective"] == b["objective"]
        assert a["objective"] <= seed["objective"]
        assert improve_incumbent(p, seed, deadline=0)["objective"] == seed["objective"]
        for compact in [False, True]:
            base, _, _, _ = build_model(p, compact=compact)
            extra, _, _, _ = build_model(p, compact=compact, conflicts=True)
            expected = solve(base, Query(QueryKind.ENUMERATE))
            got = solve(extra, Query(QueryKind.ENUMERATE))
            assert {
                tuple(s.assignment[v.name] for v in base.variables)
                for s in expected.solutions
            } == {
                tuple(s.assignment[v.name] for v in extra.variables)
                for s in got.solutions
            }


def test_jobshop_proofs_against_machine_order_enumeration():
    from itertools import permutations

    rng = Random(928)
    for _ in range(30):
        jobs, machines = 3, 2
        routes = [rng.sample(range(machines), machines) for _ in range(jobs)]
        ds = tuple(rng.randrange(1, 6) for _ in range(jobs * machines))
        original = [(i, i + 1) for i in range(0, jobs * machines, machines)]
        groups = [
            [
                i
                for i in range(jobs * machines)
                if routes[i // machines][i % machines] == r
            ]
            for r in range(machines)
        ]
        optimum = sum(ds)
        for rows in product(*(permutations(group) for group in groups)):
            arcs = original + [
                (a, b) for row in rows for a, b in zip(row, row[1:], strict=False)
            ]
            starts = [0] * len(ds)
            # Independent relaxation oracle: any change on the nth pass means
            # a positive-duration directed cycle, hence an invalid machine order.
            for _pass in range(len(ds)):
                changed = False
                for a, b in arcs:
                    if starts[b] < starts[a] + ds[a]:
                        starts[b] = starts[a] + ds[a]
                        changed = True
                if not changed:
                    optimum = min(
                        optimum, max(s + d for s, d in zip(starts, ds, strict=True))
                    )
                    break
        p = SchedulingProblem(
            ds,
            tuple((i + 1,) if i % machines == 0 else () for i in range(len(ds))),
            tuple(tuple(int(i in group) for group in groups) for i in range(len(ds))),
            (1,) * machines,
        )
        seed = tuple(sum(ds[:i]) for i in range(len(ds)))
        for energy, nfl, policy in (
            (False, False, "first"),
            (False, False, "critical"),
            (True, True, "first"),
            (True, True, "critical"),
        ):
            got = solve_schedule(
                p, seed, energetic=energy, not_first_last=nfl, conflict_policy=policy
            )
            assert got.status == "optimal" and got.objective == got.bound == optimum
            assert original_valid(p, got.starts)


def test_timeout_during_energy_or_order_propagation_preserves_incumbent(monkeypatch):
    from snarky.finite import scheduling_search

    p = SchedulingProblem((3, 2, 2), ((), (), ()), ((1,),) * 3, (2,))
    calls = 0

    def timer():
        nonlocal calls
        calls += 1
        return 0.0 if calls < 5 else 20.0

    with monkeypatch.context() as patch:
        patch.setattr(scheduling_search, "perf_counter", timer)
        result = solve_schedule(p, (0, 3, 5), seconds=1, energetic=True)
    assert result.status == "feasible"
    assert original_valid(p, result.starts)
    assert result.bound <= 4 <= result.objective
    assert solve_schedule(p, result.starts).objective == 4


def test_optional_bounds_preserve_every_feasible_window_assignment():
    from math import inf

    from snarky.finite.scheduling_search import _energy_possible, _not_first_last

    rng = Random(9345)
    for _ in range(150):
        n, horizon = rng.randrange(2, 5), rng.randrange(4, 8)
        ds = tuple(rng.randrange(1, 4) for _ in range(n))
        cap = rng.randrange(1, 4)
        p = SchedulingProblem(
            ds, ((),) * n, tuple((rng.randrange(1, cap + 1),) for _ in ds), (cap,)
        )
        heads = [rng.randrange(horizon - d + 1) for d in ds]
        latest = [
            rng.randrange(h, horizon - d + 1) for h, d in zip(heads, ds, strict=True)
        ]
        tails = [horizon - s - d for s, d in zip(latest, ds, strict=True)]
        feasible = [
            starts
            for starts in product(
                *(range(a, b + 1) for a, b in zip(heads, latest, strict=True))
            )
            if original_valid(p, starts)
        ]
        possible = _energy_possible(p, heads, tails, [list(range(n))], horizon, inf)
        if feasible:
            assert possible
        if all(q == (cap,) for q in p.demands):
            nh, nt = _not_first_last(ds, heads, tails, [list(range(n))], horizon + 1)
            for starts in feasible:
                assert all(s >= h for s, h in zip(starts, nh, strict=True))
                assert all(
                    horizon - s - d >= t for s, d, t in zip(starts, ds, nt, strict=True)
                )
