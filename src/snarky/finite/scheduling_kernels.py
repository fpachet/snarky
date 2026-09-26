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
        scope = tuple(
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

    def possible() -> bool:
        lower = upper = 0
        for scope, rows in options:
            _check(deadline)
            loads = [
                load
                for row, load in rows
                if all(
                    value in domains[var] for var, value in zip(scope, row, strict=True)
                )
            ]
            if not loads:
                return False
            lower += min(loads)
            upper += max(loads)
        return lower <= constraint.maximum and upper >= constraint.minimum

    return _filter_candidates(domains, possible, deadline)
