"""Exact integer start-domain search with timetable filtering and root shaving."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from math import isfinite
from time import perf_counter

from .scheduling_search import (
    ScheduleResult,
    SchedulingProblem,
    _overload,
    _paths,
    _resource_bound,
    validate_schedule,
)


def _interval(a: int, b: int) -> int:
    """Bit mask for nonnegative integers in the inclusive interval."""
    a = max(0, a)
    return ((1 << (b - a + 1)) - 1) << a if b >= a else 0


def _bounds(domains: list[int]) -> tuple[list[int], list[int]]:
    return (
        [(d & -d).bit_length() - 1 for d in domains],
        [d.bit_length() - 1 for d in domains],
    )


def _propagate(
    p: SchedulingProblem,
    domains: list[int],
    order: list[int],
    resources: list[list[int]],
    deadline: float,
    energetic: bool,
    stats: dict[str, int],
) -> bool:
    """Remove starts conflicting with precedence, compulsory load, or energy.

    The energy in a window is minimized at one of the extreme allowed starts.
    After reserving every other task's minimum energy, a task may use only the
    remaining capacity-time. This excludes an interval of its start domain.
    """
    ds = p.durations
    edges = p.successors
    while True:
        if perf_counter() >= deadline:
            raise TimeoutError
        before = domains.copy()
        for i in order:
            earliest = (domains[i] & -domains[i]).bit_length() - 1
            for j in edges[i]:
                domains[j] &= ~_interval(0, earliest + ds[i] - 1)
                if not domains[j]:
                    stats["precedence_failures"] += 1
                    return False
        for i in reversed(order):
            if edges[i]:
                latest = min(domains[j].bit_length() - 1 - ds[i] for j in edges[i])
                domains[i] &= _interval(0, latest)
                if not domains[i]:
                    stats["precedence_failures"] += 1
                    return False
        lo, hi = _bounds(domains)
        for r, tasks in enumerate(resources):
            cap = p.capacities[r]
            events: dict[int, int] = {}
            for i in tasks:
                if hi[i] < lo[i] + ds[i]:
                    q = p.demands[i][r]
                    events[hi[i]] = events.get(hi[i], 0) + q
                    end = lo[i] + ds[i]
                    events[end] = events.get(end, 0) - q
            points = sorted(events)
            load = 0
            for a, b in zip(points, points[1:], strict=False):
                load += events[a]
                if load > cap:
                    stats["timetable_failures"] += 1
                    return False
                if not load:
                    continue
                for i in tasks:
                    q = p.demands[i][r]
                    own = q if hi[i] <= a and b <= lo[i] + ds[i] else 0
                    if load - own + q > cap:
                        old = domains[i]
                        domains[i] &= ~_interval(a - ds[i] + 1, b - 1)
                        stats["timetable_removed"] += (old ^ domains[i]).bit_count()
                        if not domains[i]:
                            stats["timetable_failures"] += 1
                            return False
        if domains != before:
            continue
        if not energetic:
            return True
        for r, tasks in enumerate(resources):
            cap = p.capacities[r]
            ends = sorted({hi[i] + ds[i] for i in tasks})
            for a in sorted({lo[i] for i in tasks}):
                if perf_counter() >= deadline:
                    raise TimeoutError
                for b in ends:
                    if b <= a:
                        continue
                    width = b - a
                    energies = [
                        max(0, min(ds[i], width, lo[i] + ds[i] - a, b - hi[i]))
                        * p.demands[i][r]
                        for i in tasks
                    ]
                    slack = cap * width - sum(energies)
                    if slack < 0:
                        stats["energy_failures"] += 1
                        return False
                    for i, energy in zip(tasks, energies, strict=True):
                        allowed = (slack + energy) // p.demands[i][r]
                        if allowed < min(ds[i], width):
                            old = domains[i]
                            domains[i] &= ~_interval(
                                a + allowed - ds[i] + 1, b - allowed - 1
                            )
                            stats["energy_removed"] += (old ^ domains[i]).bit_count()
                            if not domains[i]:
                                stats["energy_failures"] += 1
                                return False
        if domains == before:
            return True


def _shave(
    p: SchedulingProblem,
    domains: list[int],
    order: list[int],
    resources: list[list[int]],
    deadline: float,
    energetic: bool,
    stats: dict[str, int],
) -> bool:
    """Remove only ranges whose restriction fails sound propagation.

    Test both halves and both endpoints of each start domain. No conclusion is
    drawn from successful or interrupted probes. Repeat after any removal.
    """
    while True:
        if not _propagate(p, domains, order, resources, deadline, energetic, stats):
            return False
        before = domains.copy()
        lo, hi = _bounds(domains)
        for i in range(len(domains)):
            if lo[i] == hi[i]:
                continue
            half = _interval(0, (lo[i] + hi[i]) // 2)
            for mask in (half, ~half, 1 << lo[i], 1 << hi[i]):
                if not domains[i] & mask:
                    continue
                trial = domains.copy()
                trial[i] &= mask
                stats["probes"] += 1
                # The inexpensive propagators suffice inside each probe.
                if not _propagate(p, trial, order, resources, deadline, False, stats):
                    stats["probe_failures"] += 1
                    stats["probe_removed"] += (domains[i] & mask).bit_count()
                    domains[i] &= ~mask
                    if not domains[i]:
                        return False
        if domains == before:
            return True


def solve_windows(
    problem: SchedulingProblem,
    incumbent: Sequence[int],
    *,
    seconds: float = 10,
    energetic: bool = False,
    shaving: bool = True,
    on_incumbent: Callable[[int, tuple[int, ...]], None] | None = None,
) -> ScheduleResult:
    """Prove or improve an incumbent using disjoint integer start domains.

    Root shaving tests domain halves and endpoints with sound propagation, then
    search partitions a task's domain into its earliest value and the remainder.
    Optional energy filtering is off by default. Horizon sizes above 10,000 are
    rejected before allocating the bitsets. This shares SchedulingProblem's
    mandatory-task contract; timeout bounds describe the root relaxation.
    """
    if not isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be positive and finite")
    began = perf_counter()
    best = validate_schedule(problem, incumbent)
    if best > 10_000:
        raise ValueError("window search supports incumbent makespans up to 10,000")
    deadline = began + seconds
    best_starts = tuple(incumbent)
    ds = problem.durations
    paths = _paths(problem, problem.successors)
    assert paths is not None
    heads, tails, order = paths
    resources = [
        [i for i in range(len(ds)) if problem.demands[i][r]]
        for r in range(len(problem.capacities))
    ]
    history = [(best, best_starts, 0.0)]
    stats = dict(
        precedence_failures=0,
        timetable_failures=0,
        timetable_removed=0,
        energy_failures=0,
        energy_removed=0,
        branches=0,
        probes=0,
        probe_failures=0,
        probe_removed=0,
    )
    root = max(h + d + t for h, d, t in zip(heads, ds, tails, strict=True))
    nodes = 0
    stack = []
    complete = True
    try:
        root = _resource_bound(problem, heads, tails, resources, deadline, best)
        if root < best:
            stack = [
                [
                    _interval(h, best - 1 - d - t)
                    for h, d, t in zip(heads, ds, tails, strict=True)
                ]
            ]
        if (
            stack
            and shaving
            and not _shave(
                problem, stack[0], order, resources, deadline, energetic, stats
            )
        ):
            stack.clear()
        while stack:
            if perf_counter() >= deadline:
                raise TimeoutError
            domains = stack.pop()
            nodes += 1
            for i in range(len(ds)):
                domains[i] &= _interval(0, best - 1 - ds[i] - tails[i])
            if not all(domains):
                continue
            if not _propagate(
                problem, domains, order, resources, deadline, energetic, stats
            ):
                continue
            lo, hi = _bounds(domains)
            cover = _overload(problem, lo, resources, tails, True)
            if cover is None:
                best = validate_schedule(problem, lo)
                best_starts = tuple(lo)
                history.append((best, best_starts, perf_counter() - began))
                if on_incumbent:
                    on_incumbent(best, best_starts)
                continue
            choices = [i for i in cover if lo[i] < hi[i]]
            assert choices
            i = min(
                choices,
                key=lambda i: (domains[i].bit_count(), -sum(problem.demands[i]), i),
            )
            child = domains.copy()
            left = 1 << lo[i]
            child[i] &= ~left
            stack.append(child)
            child = domains.copy()
            child[i] &= left
            stack.append(child)
            stats["branches"] += 2
    except TimeoutError:
        complete = False
    return ScheduleResult(
        "optimal" if complete else "feasible",
        best,
        best_starts,
        best if complete else min(root, best),
        nodes,
        perf_counter() - began,
        tuple(history),
        dict(stats, frontier=len(stack)),
    )
