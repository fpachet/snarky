"""Small scheduling propagators on the existing reversible finite domains."""

from __future__ import annotations

from collections.abc import Callable
from itertools import product
from time import perf_counter

from ..terms import Number, Term
from .constraints import (
    AvailabilityConstraint,
    ResourceLoadConstraint,
    WorkloadConstraint,
)
from .predicates import accepts, integer


def _check(deadline: float | None) -> None:
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("scheduling propagation time limit")


def _filter_candidates(
    domains: dict[Term, set[Term]], possible: Callable[[], bool], deadline: float | None
) -> bool:
    if not possible():
        return False
    for var in domains:
        original = domains[var]
        supported = set()
        for value in original:
            _check(deadline)
            domains[var] = {value}
            if possible():
                supported.add(value)
        domains[var] = supported
        if not supported:
            return False
    return True


def revise_availability(
    constraint: AvailabilityConstraint,
    domains: dict[Term, set[Term]],
    *,
    deadline: float | None = None,
) -> bool:
    # At most start/resource/presence; deduplicated scope respects shared variables.
    scope = constraint.variables
    supported: dict[Term, set[Term]] = {v: set() for v in scope}
    for row in product(*(domains[v] for v in scope)):
        _check(deadline)
        assignment = dict(zip(scope, row, strict=True))
        if accepts(constraint, assignment):
            for v, value in assignment.items():
                supported[v].add(value)
    for var in scope:
        domains[var].intersection_update(supported[var])
    return all(domains.values())


def revise_resource_load(
    constraint: ResourceLoadConstraint,
    domains: dict[Term, set[Term]],
    *,
    deadline: float | None = None,
) -> bool:
    for task in constraint.tasks:
        for value in domains[task.start]:
            integer(value)
        if task.present is not None and any(
            integer(x) not in (0, 1) for x in domains[task.present]
        ):
            raise ValueError("task presence domains require Number(0/1)")
    boundaries = {
        s + offset
        for task in constraint.tasks
        for s in map(integer, domains[task.start])
        for offset in (0, task.duration)
    }
    if constraint.window is not None:
        lo, hi = constraint.window
        boundaries.add(lo)
        slots = tuple(sorted(t for t in boundaries if lo <= t < hi))
    else:
        slots = tuple(sorted(boundaries))
    selected = None if constraint.resources is None else set(constraint.resources)

    def possible() -> bool:
        lower = [0] * len(slots)
        upper = [0] * len(slots)
        for task, demand in zip(constraint.tasks, constraint.demands, strict=True):
            _check(deadline)
            presence = {Number(1)} if task.present is None else domains[task.present]
            if Number(1) not in presence or not demand:
                continue
            forced = presence == {Number(1)}
            if selected is not None:
                assert task.resource is not None
                resources = domains[task.resource]
                if not resources & selected:
                    continue
                forced = forced and resources <= selected
            starts = tuple(map(integer, domains[task.start]))
            for i, t in enumerate(slots):
                if any(s <= t < s + task.duration for s in starts):
                    upper[i] += demand
                # Upper-capacity pruning deliberately uses fixed intervals only.
                if (
                    forced
                    and len(starts) == 1
                    and starts[0] <= t < starts[0] + task.duration
                ):
                    lower[i] += demand
        return all(
            hi >= constraint.minimum
            and (constraint.maximum is None or lo <= constraint.maximum)
            for lo, hi in zip(lower, upper, strict=True)
        )

    return _filter_candidates(domains, possible, deadline)


def revise_workload(
    constraint: WorkloadConstraint,
    domains: dict[Term, set[Term]],
    *,
    deadline: float | None = None,
) -> bool:
    # Local task tables, not a Cartesian product over the complete workforce.
    options: list[tuple[tuple[Term, ...], list[tuple[tuple[Term, ...], int]]]] = []
    for task in constraint.tasks:
        assert task.resource is not None
        scope: tuple[Term, ...] = tuple(
            dict.fromkeys(
                v
                for v in (
                    task.resource,
                    task.present,
                    task.start if constraint.window is not None else None,
                )
                if v is not None
            )
        )
        rows = []
        for row in product(*(domains[v] for v in scope)):
            _check(deadline)
            assignment = dict(zip(scope, row, strict=True))
            present = 1 if task.present is None else integer(assignment[task.present])
            if present not in (0, 1):
                raise ValueError("task presence domains require Number(0/1)")
            load = (
                task.duration
                if present and assignment[task.resource] == constraint.resource
                else 0
            )
            if load and constraint.window is not None:
                start = integer(assignment[task.start])
                lo, hi = constraint.window
                load = max(0, min(start + task.duration, hi) - max(start, lo))
            rows.append((row, load))
        options.append((scope, rows))

    if any(not values for values in domains.values()):
        return False
    # Each candidate only changes relations mentioning its variable. Keep total
    # extrema and replace those incident contributions instead of rescanning the
    # entire workforce. All state is local to this revision, so rollback is free.
    lows, highs = [], []
    incident: dict[Term, list[tuple[int, int]]] = {v: [] for v in domains}
    for i, (scope, rows) in enumerate(options):
        loads = [load for _, load in rows]
        if not loads:
            return False
        lows.append(min(loads))
        highs.append(max(loads))
        # Constant contributions (including ineligible workers) cannot affect
        # candidate support. Retain their constant in the total only.
        if lows[-1] != highs[-1]:
            for position, var in enumerate(scope):
                incident[var].append((i, position))
    lower, upper = sum(lows), sum(highs)
    if lower > constraint.maximum or upper < constraint.minimum:
        return False
    for var, affected in incident.items():
        _check(deadline)
        if not affected:
            continue
        base_low = lower - sum(lows[i] for i, _ in affected)
        base_high = upper - sum(highs[i] for i, _ in affected)
        supported = set()
        for value in domains[var]:
            candidate_low, candidate_high = base_low, base_high
            for i, position in affected:
                _check(deadline)
                loads = [load for row, load in options[i][1] if row[position] == value]
                if not loads:
                    break
                candidate_low += min(loads)
                candidate_high += max(loads)
            else:
                if (
                    candidate_low <= constraint.maximum
                    and candidate_high >= constraint.minimum
                ):
                    supported.add(value)
        if not supported:
            domains[var] = set()
            return False
        if supported == domains[var]:
            continue
        domains[var] = supported
        for i, position in affected:
            scope, rows = options[i]
            rows = [(row, load) for row, load in rows if row[position] in supported]
            options[i] = scope, rows
            loads = [load for _, load in rows]
            low, high = min(loads), max(loads)
            lower += low - lows[i]
            upper += high - highs[i]
            lows[i], highs[i] = low, high
    return True
