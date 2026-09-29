"""Independent exhaustive checks of clique resources and failed-domain probes."""

from itertools import product
from math import inf
from random import Random

import pytest

from snarky.finite.scheduling_search import (
    SchedulingProblem,
    _paths,
    add_conflict_cliques,
    solve_schedule,
    validate_schedule,
)
from snarky.finite.scheduling_windows import _interval, _shave, solve_windows
from tests.test_scheduling_order import original_valid


def test_cliques_and_window_search_match_exhaustive_schedules():
    rng = Random(319)
    for _ in range(150):
        n = rng.randrange(1, 5)
        ds = tuple(rng.randrange(1, 4) for _ in range(n))
        caps = (rng.randrange(1, 4), rng.randrange(1, 4))
        p = SchedulingProblem(
            ds,
            tuple(
                tuple(j for j in range(i + 1, n) if rng.random() < 0.2)
                for i in range(n)
            ),
            tuple(tuple(rng.randrange(c + 1) for c in caps) for _ in ds),
            caps,
        )
        aug = add_conflict_cliques(p)
        limited = add_conflict_cliques(p, limit=1, node_limit=10)
        seed = tuple(sum(ds[:i]) for i in range(n))
        optimum = sum(ds)
        for starts in product(*(range(sum(ds) - d + 1) for d in ds)):
            valid = original_valid(p, starts)
            assert (
                valid == original_valid(aug, starts) == original_valid(limited, starts)
            )
            if valid:
                optimum = min(
                    optimum, max(s + d for s, d in zip(starts, ds, strict=True))
                )
        for energy, shaving in ((False, False), (False, True), (True, True)):
            got = solve_windows(p, seed, energetic=energy, shaving=shaving)
            assert got.status == "optimal" and got.objective == got.bound == optimum
            assert all(original_valid(p, s) for _, s, _ in got.history)
        got = solve_schedule(aug, seed)
        assert got.status == "optimal" and got.objective == got.bound == optimum
        assert original_valid(p, got.starts)


def test_shaving_preserves_every_feasible_assignment_in_domains_with_holes():
    rng = Random(14562)
    for _ in range(300):
        n, horizon = rng.randrange(1, 5), rng.randrange(3, 9)
        ds = tuple(rng.randrange(4) for _ in range(n))
        caps = (rng.randrange(1, 4), rng.randrange(1, 4))
        permutation = rng.sample(range(n), n)
        edges = [[] for _ in ds]
        for a in range(n):
            for b in range(a + 1, n):
                if rng.random() < 0.3:
                    edges[permutation[a]].append(permutation[b])
        p = SchedulingProblem(
            ds,
            tuple(tuple(row) for row in edges),
            tuple(tuple(rng.randrange(c + 1) if d else 0 for c in caps) for d in ds),
            caps,
        )
        allowed = [
            sorted(
                rng.sample(range(horizon - d + 1), rng.randrange(1, horizon - d + 2))
            )
            for d in ds
        ]
        domains = [sum(1 << s for s in row) for row in allowed]
        feasible = [s for s in product(*allowed) if original_valid(p, s)]
        paths = _paths(p, p.successors)
        assert paths is not None
        resources = [
            [i for i, row in enumerate(p.demands) if row[r]] for r in range(len(caps))
        ]
        for energy in (False, True):
            copy = domains[:]
            stats = dict(
                precedence_failures=0,
                timetable_failures=0,
                timetable_removed=0,
                energy_failures=0,
                energy_removed=0,
                probes=0,
                probe_failures=0,
                probe_removed=0,
            )
            possible = _shave(p, copy, paths[2], resources, inf, energy, stats)
            assert possible or not feasible
            for starts in feasible:
                assert all(copy[i] & (1 << s) for i, s in enumerate(starts))
            assert all(
                after & ~before == 0
                for before, after in zip(domains, copy, strict=True)
            )


def test_cross_resource_clique_is_sound_and_enumeration_limits_are_safe():
    # Each pair conflicts on a different resource. There is no original unary
    # resource for all three, but the combined incompatibility clique is unary.
    p = SchedulingProblem(
        (2, 2, 2), ((),) * 3, ((1, 1, 0), (1, 0, 1), (0, 1, 1)), (1, 1, 1)
    )
    aug = add_conflict_cliques(p)
    assert aug.capacities == (1, 1, 1, 1)
    assert all(row[-1] == 1 for row in aug.demands)
    assert add_conflict_cliques(aug) is aug
    assert add_conflict_cliques(p, limit=0) is p
    assert add_conflict_cliques(p, node_limit=0) is p
    for kw in ({"limit": -1}, {"node_limit": -1}, {"limit": 1.5}):
        with pytest.raises(ValueError):
            add_conflict_cliques(p, **kw)
    assert solve_schedule(aug, (0, 2, 4)).bound == 6


def test_window_timeout_during_probe_keeps_a_valid_incumbent(monkeypatch):
    from snarky.finite import scheduling_windows

    p = SchedulingProblem((3, 2, 2), ((),) * 3, ((1,),) * 3, (2,))
    original = scheduling_windows._propagate
    calls = 0

    def interrupt(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise TimeoutError
        return original(*args, **kwargs)

    monkeypatch.setattr(scheduling_windows, "_propagate", interrupt)
    got = solve_windows(p, (0, 3, 5))
    assert got.status == "feasible" and got.statistics["probes"] == 1
    assert got.bound <= 4 <= got.objective
    assert original_valid(p, got.starts)


def test_zero_duration_dummies_horizon_limit_and_callbacks():
    p = SchedulingProblem(
        (0, 2, 1, 0), ((2, 1), (3,), (1,), ()), ((0,), (1,), (1,), (0,)), (1,)
    )
    calls = []
    got = solve_windows(
        p, (0, 2, 1, 4), on_incumbent=lambda obj, s: calls.append((obj, s))
    )
    assert got.status == "optimal" and got.objective == 3
    assert calls and validate_schedule(p, calls[-1][1]) == 3
    zero = SchedulingProblem((0,), ((),), ((0,),), (1,))
    assert solve_windows(zero, (0,)).objective == 0
    assert _interval(-2, 1) == 3 and _interval(3, 2) == 0
    for seconds in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            solve_windows(p, got.starts, seconds=seconds)
    with pytest.raises(ValueError, match="10,000"):
        solve_windows(zero, (10001,))
