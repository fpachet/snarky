"""Capacity filtering using compulsory intervals and resource-window overloads.

Mandatory tasks with distinct starts share one endpoint load profile per revision.
Optional tasks and aliases retain the reference fixed-interval filter. All caches
are revision-local, so rollback and changed guards require no extra trail state.
"""

from __future__ import annotations

from bisect import bisect_right
from time import perf_counter

from ..terms import Term
from .constraints import CapacityConstraint
from .predicates import integer


def revise_capacity(
    constraint: CapacityConstraint,
    domains: dict[Term, set[Term]],
    *,
    deadline: float | None = None,
) -> bool:
    tasks = constraint.tasks
    if any(t.present is not None for t in tasks) or len(
        {t.start for t in tasks}
    ) != len(tasks):
        return _revise_fixed_capacity(constraint, domains, deadline=deadline)
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("capacity propagation time limit")
    numeric = {v: {integer(x) for x in values} for v, values in domains.items()}
    if any(not values for values in numeric.values()):
        return False
    # Each mandatory part [latest start, earliest end) is occupied in every
    # completion, even with holes in the start domain. The profile also contains
    # fixed intervals as a special case. Zero-demand tasks contribute nothing.
    events: dict[int, int] = {}
    parts: list[tuple[int, int]] = []
    windows: list[tuple[int, int, int]] = []
    for task, demand in zip(tasks, constraint.demands, strict=True):
        if demand > constraint.capacity:
            return False
        earliest, latest = min(numeric[task.start]), max(numeric[task.start])
        lo, hi = latest, earliest + task.duration
        parts.append((lo, hi))
        if demand:
            windows.append((earliest, latest + task.duration, task.duration * demand))
            if lo < hi:
                events[lo] = events.get(lo, 0) + demand
                events[hi] = events.get(hi, 0) - demand
    # For every window [a,b), tasks whose whole feasible execution envelope is
    # inside that window require all their energy there. Summing these demands
    # detects overload even when no task has a mandatory part. O(n^2), no slots.
    by_end = sorted(windows, key=lambda row: row[1])
    for lower in sorted({row[0] for row in windows}):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("capacity propagation time limit")
        energy = 0
        for earliest, end, work in by_end:
            if earliest >= lower:
                energy += work
                if energy > constraint.capacity * (end - lower):
                    return False
    points = sorted(events)
    profile: list[tuple[int, int, int]] = []
    load = 0
    for lo, hi in zip(points, points[1:], strict=False):
        load += events[lo]
        if load > constraint.capacity:
            return False
        if load:
            profile.append((lo, hi, load))
    for task, demand, (own_lo, own_hi) in zip(
        tasks, constraint.demands, parts, strict=True
    ):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("capacity propagation time limit")
        if not demand:
            continue
        forbidden: list[tuple[int, int]] = []
        for lo, hi, load in profile:
            # Remove this task's compulsory contribution before considering its
            # complete candidate interval; otherwise it would be counted twice.
            other = load - (demand if own_lo <= lo and hi <= own_hi else 0)
            if other + demand > constraint.capacity:
                left, right = lo - task.duration + 1, hi - 1
                if forbidden and left <= forbidden[-1][1] + 1:
                    forbidden[-1] = (forbidden[-1][0], max(right, forbidden[-1][1]))
                else:
                    forbidden.append((left, right))
        if not forbidden:
            continue
        lefts = [lo for lo, _ in forbidden]
        supported = set()
        for value in domains[task.start]:
            start = integer(value)
            index = bisect_right(lefts, start) - 1
            if index < 0 or start > forbidden[index][1]:
                supported.add(value)
        if not supported:
            return False
        domains[task.start].intersection_update(supported)
    # Filtering may create another mandatory part. The propagation queue revisits
    # this constraint when a domain changes, rebuilding from the new snapshot.
    return True


def _revise_fixed_capacity(
    constraint: CapacityConstraint,
    domains: dict[Term, set[Term]],
    *,
    deadline: float | None = None,
) -> bool:
    numeric = {v: {integer(x) for x in values} for v, values in domains.items()}
    if any(not values for values in numeric.values()):
        return False
    for task in constraint.tasks:
        if task.present is not None and not numeric[task.present] <= {0, 1}:
            raise ValueError("task presence domains require Number(0/1)")

    def possible(variable: Term | None = None, candidate: int = 0) -> bool:
        events: dict[int, int] = {}
        for task, demand in zip(constraint.tasks, constraint.demands, strict=True):
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("capacity propagation time limit")
            presence = (
                {candidate}
                if task.present == variable and variable is not None
                else numeric[task.present]
                if task.present is not None
                else {1}
            )
            if 0 in presence or not demand:
                continue
            starts = {candidate} if task.start == variable else numeric[task.start]
            if len(starts) != 1:
                continue
            start = next(iter(starts))
            events[start] = events.get(start, 0) + demand
            end = start + task.duration
            events[end] = events.get(end, 0) - demand
        load = 0
        for time in sorted(events):
            load += events[time]
            if load > constraint.capacity:
                return False
        return True

    if not possible():
        return False
    for variable, values in domains.items():
        supported = {v for v in values if possible(variable, integer(v))}
        if not supported:
            return False
        values.intersection_update(supported)
        numeric[variable] = {integer(v) for v in values}
    return True
