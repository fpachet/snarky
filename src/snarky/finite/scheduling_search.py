"""Exact order search for mandatory, fixed-duration renewable-resource schedules.

This explicit scheduling API branches on precedences, not integer start values.
It does not handle optional tasks, calendars, resource choices or mixed rules.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import combinations
from time import perf_counter


@dataclass(frozen=True)
class SchedulingProblem:
    durations: tuple[int, ...]
    successors: tuple[tuple[int, ...], ...]
    demands: tuple[tuple[int, ...], ...]
    capacities: tuple[int, ...]

    def __post_init__(self) -> None:
        n = len(self.durations)
        if not n or len(self.successors) != n or len(self.demands) != n:
            raise ValueError("inconsistent scheduling dimensions")
        if any(type(d) is not int or d < 0 for d in self.durations):
            raise ValueError("durations must be nonnegative integers")
        if not self.capacities or any(
            type(c) is not int or c <= 0 for c in self.capacities
        ):
            raise ValueError("capacities must be positive integers")
        for i, (edges, demands) in enumerate(
            zip(self.successors, self.demands, strict=True)
        ):
            if len(set(edges)) != len(edges) or any(
                type(j) is not int or j == i or not 0 <= j < n for j in edges
            ):
                raise ValueError("invalid precedence edge")
            if (
                len(demands) != len(self.capacities)
                or any(
                    type(q) is not int or q < 0 or q > c
                    for q, c in zip(demands, self.capacities, strict=True)
                )
                or (self.durations[i] == 0 and any(demands))
            ):
                raise ValueError("invalid task demands")
        if _paths(self, self.successors) is None:
            raise ValueError("cyclic precedences")


@dataclass(frozen=True)
class ScheduleResult:
    status: str
    objective: int
    starts: tuple[int, ...]
    bound: int
    nodes: int
    seconds: float
    history: tuple[tuple[int, tuple[int, ...], float], ...]


def _paths(
    problem: SchedulingProblem,
    successors: Sequence[Sequence[int]],
    head_floor: list[int] | None = None,
    tail_floor: list[int] | None = None,
) -> tuple[list[int], list[int], list[int]] | None:
    ds = problem.durations
    degree = [0] * len(ds)
    for edges in successors:
        for j in edges:
            degree[j] += 1
    order = [i for i, count in enumerate(degree) if not count]
    heads = [0] * len(ds) if head_floor is None else head_floor.copy()
    for i in order:
        end = heads[i] + ds[i]
        for j in successors[i]:
            heads[j] = max(heads[j], end)
            degree[j] -= 1
            if degree[j] == 0:
                order.append(j)
    if len(order) != len(ds):
        return None
    tails = [0] * len(ds) if tail_floor is None else tail_floor.copy()
    for i in reversed(order):
        tails[i] = max(
            tails[i], max((ds[j] + tails[j] for j in successors[i]), default=0)
        )
    return heads, tails, order


def validate_schedule(problem: SchedulingProblem, starts: Sequence[int]) -> int:
    """Check original precedences and half-open resource intervals."""
    if len(starts) != len(problem.durations) or any(
        type(s) is not int or s < 0 for s in starts
    ):
        raise ValueError("invalid starts")
    for i, edges in enumerate(problem.successors):
        if any(starts[i] + problem.durations[i] > starts[j] for j in edges):
            raise ValueError("precedence violation")
    for r, cap in enumerate(problem.capacities):
        events: dict[int, int] = {}
        for i, (s, d) in enumerate(zip(starts, problem.durations, strict=True)):
            q = problem.demands[i][r]
            events[s] = events.get(s, 0) + q
            events[s + d] = events.get(s + d, 0) - q
        load = 0
        for t in sorted(events):
            load += events[t]
            if load > cap:
                raise ValueError("capacity violation")
    return max(s + d for s, d in zip(starts, problem.durations, strict=True))


def _resource_bound(
    problem: SchedulingProblem,
    heads: list[int],
    tails: list[int],
    resources: list[list[int]],
    deadline: float,
    cutoff: int,
) -> int:
    """Work of tasks with head>=a and tail>=b must fit in [a, C-b)."""
    ds = problem.durations
    lower = max(h + d + t for h, d, t in zip(heads, ds, tails, strict=True))
    if lower >= cutoff:
        return lower
    for r, tasks in enumerate(resources):
        if perf_counter() >= deadline:
            raise TimeoutError
        by_tail = sorted(tasks, key=lambda i: tails[i], reverse=True)
        cap = problem.capacities[r]
        for head in {heads[i] for i in tasks}:
            energy = 0
            for i in by_tail:
                if heads[i] >= head:
                    energy += ds[i] * problem.demands[i][r]
                    lower = max(lower, head + (energy + cap - 1) // cap + tails[i])
                    if lower >= cutoff:
                        return lower
    return lower


def _overload(
    problem: SchedulingProblem,
    starts: list[int],
    resources: list[list[int]],
    tails: list[int],
    critical: bool,
) -> list[int] | None:
    """Find a minimal set of simultaneously active tasks exceeding capacity."""
    choices = []
    for r, tasks in enumerate(resources):
        events = sorted((starts[i], i) for i in tasks)
        active: list[int] = []
        for t, i in events:
            active = [j for j in active if starts[j] + problem.durations[j] > t]
            active.append(i)
            load = sum(problem.demands[j][r] for j in active)
            if load > problem.capacities[r]:
                cover = sorted(active, key=lambda j: (problem.demands[j][r], j))
                for j in tuple(cover):
                    if load - problem.demands[j][r] > problem.capacities[r]:
                        cover.remove(j)
                        load -= problem.demands[j][r]
                choices.append(cover)
                if len(cover) == 2 and not critical:
                    return cover
                break
    if not choices:
        return None
    if not critical:
        return min(choices, key=len)

    def rank(cover: list[int]) -> tuple[int, int]:
        path = min(
            starts[a] + problem.durations[a] + problem.durations[b] + tails[b]
            for a in cover
            for b in cover
            if a != b
        )
        return len(cover), -path

    return min(choices, key=rank)


def _energy_possible(
    problem: SchedulingProblem,
    heads: list[int],
    tails: list[int],
    resources: list[list[int]],
    horizon: int,
    deadline: float,
) -> bool:
    """Necessary energy in windows, including partially contained task envelopes.

    The least overlap with [a,b) occurs at one of the two extreme start times.
    Only windows anchored at release times and completion deadlines are checked;
    this is not a complete implementation of energetic filtering.
    """
    ds = problem.durations
    latest = [horizon - ds[i] - tails[i] for i in range(len(ds))]
    for r, tasks in enumerate(resources):
        ends = sorted({horizon - tails[i] for i in tasks})
        for a in sorted({heads[i] for i in tasks}):
            if perf_counter() >= deadline:
                raise TimeoutError
            for b in ends:
                if b <= a:
                    continue
                width = b - a
                energy = sum(
                    max(0, min(ds[i], width, heads[i] + ds[i] - a, b - latest[i]))
                    * problem.demands[i][r]
                    for i in tasks
                )
                if energy > problem.capacities[r] * width:
                    return False
    return True


def _not_first_last(
    ds: tuple[int, ...],
    heads: list[int],
    tails: list[int],
    groups: list[list[int]],
    upper: int,
) -> tuple[list[int], list[int]]:
    """Unary not-first/not-last bounds; no assumption about an actual order.

    If i followed by all of S cannot fit, some j in S must precede i, hence
    start(i)>=min(end-min(j)). The reversed-time argument tightens tails.
    """
    new_heads, new_tails = heads.copy(), tails.copy()
    for tasks in groups:
        for i in tasks:
            for forward in (True, False):
                left, right = (heads, tails) if forward else (tails, heads)
                others = sorted(
                    (j for j in tasks if j != i), key=lambda j: right[j], reverse=True
                )
                work = 0
                minimum_end = max(left) + sum(ds)
                for j in others:
                    work += ds[j]
                    minimum_end = min(minimum_end, left[j] + ds[j])
                    if left[i] + ds[i] + work + right[j] >= upper:
                        target = new_heads if forward else new_tails
                        target[i] = max(target[i], minimum_end)
    return new_heads, new_tails


def solve_schedule(
    problem: SchedulingProblem,
    incumbent: Sequence[int],
    *,
    seconds: float = 10,
    energetic: bool = False,
    not_first_last: bool = False,
    conflict_policy: str = "first",
    on_incumbent: Callable[[int, tuple[int, ...]], None] | None = None,
) -> ScheduleResult:
    """Exhaustive precedence branching with sound resource lower bounds.

    At an overloaded earliest schedule, every feasible completion must separate
    some pair in the overloaded set. Intervals have the Helly property: if all
    pairs overlap then the entire set shares a time point. Branching on both
    orders of every pair is therefore complete (branches may overlap).
    Bounds at timeout are from the root relaxation, not the remaining frontier.
    """
    from math import isfinite

    if not isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be positive and finite")
    if conflict_policy not in ("first", "critical"):
        raise ValueError("conflict_policy must be first or critical")
    began = perf_counter()
    best = validate_schedule(problem, incumbent)
    best_starts = tuple(incumbent)
    deadline = began + seconds
    ds = problem.durations
    resources = [
        [i for i, row in enumerate(problem.demands) if row[r]]
        for r in range(len(problem.capacities))
    ]
    unary = [
        tasks
        for r, tasks in enumerate(resources)
        if all(problem.demands[i][r] == problem.capacities[r] for i in tasks)
    ]
    incompatible = [
        (a, b)
        for a, b in combinations(range(len(ds)), 2)
        if any(
            x + y > c
            for x, y, c in zip(
                problem.demands[a], problem.demands[b], problem.capacities, strict=True
            )
        )
    ]
    stack = [problem.successors]
    seen: set[tuple[int, ...]] = set()
    history = [(best, best_starts, 0.0)]
    nodes = 0
    root_bound = max(max(ds), 0)
    complete = True
    try:
        while stack:
            if perf_counter() >= deadline:
                raise TimeoutError
            edges = stack.pop()
            nodes += 1
            head_floor = [0] * len(ds)
            tail_floor = [0] * len(ds)
            while True:
                paths = _paths(problem, edges, head_floor, tail_floor)
                if paths is None:
                    break
                heads, tails, order = paths
                bound = _resource_bound(
                    problem, heads, tails, resources, deadline, best
                )
                if nodes == 1:
                    root_bound = max(root_bound, bound)
                if bound >= best:
                    break
                if not_first_last:
                    new_heads, new_tails = _not_first_last(
                        ds, heads, tails, unary, best
                    )
                    if new_heads != heads or new_tails != tails:
                        head_floor, tail_floor = new_heads, new_tails
                        continue
                forced = []
                impossible = False
                for a, b in incompatible:
                    # Earliest starts alone do not establish a precedence.
                    if b in edges[a] or a in edges[b]:
                        continue
                    ab = heads[a] + ds[a] + ds[b] + tails[b] < best
                    ba = heads[b] + ds[b] + ds[a] + tails[a] < best
                    if not ab and not ba:
                        impossible = True
                        break
                    if not ab and a not in edges[b]:
                        forced.append((b, a))
                    elif not ba and b not in edges[a]:
                        forced.append((a, b))
                if impossible:
                    break
                if forced:
                    update = [set(row) for row in edges]
                    for a, b in forced:
                        update[a].add(b)
                    edges = tuple(tuple(sorted(row)) for row in update)
                    continue
                # Canonical transitive closures merge states reached through
                # different redundant arcs. Every first visit either closes
                # the state or enqueues a complete cover of its continuations.
                reach = [0] * len(ds)
                for i in reversed(order):
                    for j in edges[i]:
                        reach[i] |= (1 << j) | reach[j]
                key = tuple(reach)
                if key in seen:
                    break
                if len(seen) < 50_000:
                    seen.add(key)
                if energetic and not _energy_possible(
                    problem, heads, tails, resources, best - 1, deadline
                ):
                    break
                cover = _overload(
                    problem, heads, resources, tails, conflict_policy == "critical"
                )
                if cover is None:
                    objective = validate_schedule(problem, heads)
                    if objective < best:
                        best, best_starts = objective, tuple(heads)
                        history.append((best, best_starts, perf_counter() - began))
                        if on_incumbent is not None:
                            on_incumbent(best, best_starts)
                    break
                branches = []
                for a, b in combinations(cover, 2):
                    for i, j in ((a, b), (b, a)):
                        if heads[i] + ds[i] + ds[j] + tails[j] >= best:
                            continue
                        child = list(edges)
                        child[i] = tuple(sorted((*edges[i], j)))
                        # Prefer the incumbent order, then the smaller path bound.
                        priority = (
                            best_starts[i] > best_starts[j],
                            heads[i] + ds[i] + ds[j] + tails[j],
                        )
                        branches.append((priority, tuple(child)))
                stack.extend(child for _, child in sorted(branches, reverse=True))
                break
    except TimeoutError:
        complete = False
    return ScheduleResult(
        "optimal" if complete else "feasible",
        best,
        best_starts,
        best if complete else min(root_bound, best),
        nodes,
        perf_counter() - began,
        tuple(history),
    )
