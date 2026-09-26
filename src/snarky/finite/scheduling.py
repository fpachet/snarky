"""Thin scheduling conveniences over ordinary finite constraints and factors."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from itertools import combinations
from typing import cast

from ..terms import Atom, Number, Term
from .constraints import (
    AllOfConstraint,
    AnyOfConstraint,
    AvailabilityConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    CapacityConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    PersistentConstraint,
    ResourceLoadConstraint,
    TableConstraint,
    Task,
    WorkloadConstraint,
)
from .predicates import integer


def OptionalTask(task: Task, present: Atom) -> Task:
    """Return a task controlled by an ordinary Number(0/1) decision variable."""
    if task.present is not None:
        raise ValueError("task already has a presence variable")
    return replace(task, present=present)


def _when_present(
    constraint: PersistentConstraint, *tasks: Task
) -> PersistentConstraint:
    presence = tuple(dict.fromkeys(t.present for t in tasks if t.present is not None))
    if not presence:
        return constraint
    return AnyOfConstraint(
        constraint.name,
        (
            *(
                TableConstraint(
                    Atom(f"{constraint.name.name}:absent:{v.name}"),
                    (v,),
                    ((Number(0),),),
                )
                for v in presence
            ),
            constraint,
        ),
    )


def Precedence(
    a: Task,
    b: Task,
    *,
    min_lag: int = 0,
    max_lag: int | None = None,
    name: Atom | None = None,
) -> PersistentConstraint:
    """Bound the gap from a's end to b's start, when both are present."""
    if (
        type(min_lag) is not int
        or min_lag < 0
        or max_lag is not None
        and (type(max_lag) is not int or max_lag < min_lag)
    ):
        raise ValueError("precedence requires 0 <= min_lag <= max_lag")
    name = name or Atom(f"precedence:{a.name}:{b.name}")
    if a.start == b.start:
        return _when_present(AnyOfConstraint(name, ()), a, b)
    minimum = LinearSumConstraint(
        name,
        ((1, a.start), (-1, b.start)),
        ConstraintOperator.LESS_EQUAL,
        -a.duration - min_lag,
    )
    constraint: PersistentConstraint = minimum
    if max_lag is not None:
        constraint = AllOfConstraint(
            name,
            (
                minimum,
                LinearSumConstraint(
                    Atom(name.name + ":maximum_gap"),
                    minimum.terms,
                    ConstraintOperator.GREATER_EQUAL,
                    -a.duration - max_lag,
                ),
            ),
        )
    return _when_present(constraint, a, b)


def NoOverlap(
    a: Task,
    b: Task,
    *,
    when_same_resource: bool = False,
    min_gap: int = 0,
    name: Atom | None = None,
) -> PersistentConstraint:
    """Disjoin the two orders, optionally allowing different resources."""
    name = name or Atom(f"no_overlap:{a.name}:{b.name}")
    # Presence is handled once around the whole disjunction.
    left, right = replace(a, present=None), replace(b, present=None)
    alternatives = [
        Precedence(left, right, min_lag=min_gap),
        Precedence(right, left, min_lag=min_gap),
    ]
    if when_same_resource:
        if a.resource is None or b.resource is None:
            raise ValueError("conditional non-overlap requires both resource variables")
        if a.resource != b.resource:
            alternatives.append(
                BinaryComparisonConstraint(
                    Atom(f"{name.name}:different_resources"),
                    a.resource,
                    b.resource,
                    BinaryComparisonOperator.NOT_EQUAL,
                )
            )
    return _when_present(AnyOfConstraint(name, tuple(alternatives)), a, b)


def Capacity(
    tasks: Sequence[Task],
    capacity: int,
    demands: Sequence[int] | None = None,
    *,
    name: Atom | None = None,
) -> CapacityConstraint:
    """Use one shared pool; demands default to one per present task."""
    tasks = tuple(tasks)
    return CapacityConstraint(
        name or Atom("capacity:" + ":".join(t.name for t in tasks)),
        tasks,
        capacity,
        (1,) * len(tasks) if demands is None else tuple(demands),
    )


def availability_constraints(
    task: Task,
    windows: Mapping[Term, tuple[int, int] | Sequence[tuple[int, int]]],
    *,
    name: Atom | None = None,
) -> tuple[AvailabilityConstraint, ...]:
    """Joint resource/start filtering over one or more windows per resource.

    Missing resources are unavailable. Overlapping/touching windows are merged.
    The tuple return type remains convenient for inclusion in a model's constraints.
    """
    normalized: list[tuple[Term, tuple[tuple[int, int], ...]]] = []
    for resource, value in windows.items():
        if len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
            # Validation in AvailabilityConstraint rejects non-integer endpoints.
            intervals: Sequence[tuple[int, int]] = (cast(tuple[int, int], value),)
        else:
            intervals = cast(Sequence[tuple[int, int]], value)
        normalized.append(
            (resource, tuple((w[0], w[1]) if len(w) == 2 else w for w in intervals))
        )
    return (
        AvailabilityConstraint(
            name or Atom(f"availability:{task.name}:windows"), task, tuple(normalized)
        ),
    )


def StartWindow(
    task: Task, earliest: int, latest_end: int, *, name: Atom | None = None
) -> PersistentConstraint:
    """Release time and deadline for a present task."""
    if (
        type(earliest) is not int
        or type(latest_end) is not int
        or earliest > latest_end
    ):
        raise ValueError("window requires integer earliest <= latest_end")
    name = name or Atom(f"window:{task.name}")
    return _when_present(
        AllOfConstraint(
            name,
            (
                LinearSumConstraint(
                    Atom(name.name + ":release"),
                    ((1, task.start),),
                    ConstraintOperator.GREATER_EQUAL,
                    earliest,
                ),
                LinearSumConstraint(
                    Atom(name.name + ":deadline"),
                    ((1, task.start),),
                    ConstraintOperator.LESS_EQUAL,
                    latest_end - task.duration,
                ),
            ),
        ),
        task,
    )


def ExactlyOne(
    tasks: Sequence[Task], *, name: Atom | None = None
) -> PersistentConstraint:
    """Exactly one alternative is present, using existing Boolean sum arithmetic."""
    tasks = tuple(tasks)
    name = name or Atom("exactly_one:" + ":".join(t.name for t in tasks))
    present = Counter(t.present for t in tasks if t.present is not None)
    target = 1 - sum(t.present is None for t in tasks)
    if not present:
        return AllOfConstraint(name, ()) if target == 0 else AnyOfConstraint(name, ())
    return LinearSumConstraint(
        name,
        tuple((n, v) for v, n in present.items()),
        ConstraintOperator.EQUAL,
        target,
    )


def Coverage(
    tasks: Sequence[Task],
    window: tuple[int, int],
    minimum: int,
    *,
    resources: Sequence[Term] | None = None,
    name: Atom | None = None,
) -> ResourceLoadConstraint:
    """At least minimum active tasks in a window, optionally of selected workers.

    Apply resource non-overlap as well when each worker must be counted only once.
    """
    return ResourceLoadConstraint(
        name or Atom(f"coverage:{window[0]}:{window[1]}"),
        tuple(tasks),
        minimum,
        window=window,
        resources=None if resources is None else tuple(resources),
    )


def resource_capacity_constraints(
    tasks: Sequence[Task],
    capacities: Mapping[Term, int],
    *,
    demands: Sequence[int] | None = None,
    name: Atom | None = None,
) -> tuple[ResourceLoadConstraint, ...]:
    """One capacity per named pool; unlisted pools are unconstrained."""
    tasks = tuple(tasks)
    prefix = (name or Atom("resource_capacity")).name
    return tuple(
        ResourceLoadConstraint(
            Atom(f"{prefix}:{i}"),
            tasks,
            maximum=capacity,
            resources=(resource,),
            demands=(1,) * len(tasks) if demands is None else tuple(demands),
        )
        for i, (resource, capacity) in enumerate(capacities.items())
    )


def Workload(
    tasks: Sequence[Task],
    resource: Term,
    maximum: int,
    *,
    minimum: int = 0,
    window: tuple[int, int] | None = None,
    name: Atom | None = None,
) -> WorkloadConstraint:
    """Limit assigned hours, optionally clipped to a day/week window."""
    return WorkloadConstraint(
        name or Atom(f"workload:{resource!r}:{window!r}"),
        tuple(tasks),
        resource,
        maximum,
        minimum,
        window,
    )


def no_overlap_constraints(
    tasks: Sequence[Task],
    domains: Mapping[Term, Collection[Term]],
    *,
    when_same_resource: bool = True,
    min_gap: int = 0,
) -> tuple[PersistentConstraint, ...]:
    """Build only potentially conflicting pairs, using the model's full domains."""
    if type(min_gap) is not int or min_gap < 0:
        raise ValueError("min_gap must be a nonnegative integer")
    result = []
    for a, b in combinations(tasks, 2):
        if when_same_resource:
            if a.resource is None or b.resource is None:
                raise ValueError("conditional non-overlap requires resources")
            if not set(domains[a.resource]) & set(domains[b.resource]):
                continue
        left, right = (
            tuple(map(integer, domains[a.start])),
            tuple(map(integer, domains[b.start])),
        )
        if (
            left
            and right
            and (
                max(left) + a.duration + min_gap <= min(right)
                or max(right) + b.duration + min_gap <= min(left)
            )
        ):
            continue
        result.append(
            NoOverlap(a, b, when_same_resource=when_same_resource, min_gap=min_gap)
        )
    return tuple(result)
