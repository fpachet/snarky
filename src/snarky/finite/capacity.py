"""Small discrete capacity propagator using already fixed intervals.

Each candidate is tested against the load of fixed, present tasks at each slot.
Unfixed intervals are ignored; there is no mandatory-part/timetable analysis.
The relaxation is exact on singletons and respects shared variable references.
Fixed interval endpoints are aggregated before checking load; calendar slots
are never materialized, even for large time values or long durations.
"""

from __future__ import annotations

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
