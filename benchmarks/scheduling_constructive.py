"""Input-only constructive incumbents for the scheduling assessment.

No reference objectives, solver bounds, or external schedules enter this module.
Each generated schedule is checked against original semantics before selection.
"""

from __future__ import annotations

from random import Random
from time import perf_counter

from benchmarks.scheduling_instances import (
    Project,
    topological,
    validate_jobshop,
    validate_project,
)


def project_schedule(instance, priority):
    durations = instance.durations
    n, horizon = len(durations), sum(durations)
    predecessors = [[] for _ in durations]
    for i, edges in enumerate(instance.successors):
        for j in edges:
            predecessors[j].append(i)
    usage = [[0] * horizon for _ in instance.capacities]
    starts = [None] * n
    pending = set(range(n))
    while pending:
        i = min(
            (i for i in pending if all(starts[j] is not None for j in predecessors[i])),
            key=lambda i: (priority[i], i),
        )
        earliest = max((starts[j] + durations[j] for j in predecessors[i]), default=0)
        active = [
            (r, q, instance.capacities[r])
            for r, q in enumerate(instance.demands[i])
            if q
        ]
        start = next(
            s
            for s in range(earliest, horizon - durations[i] + 1)
            if all(
                usage[r][t] + q <= cap
                for r, q, cap in active
                for t in range(s, s + durations[i])
            )
        )
        starts[i] = start
        for r, q, _ in active:
            for t in range(start, start + durations[i]):
                usage[r][t] += q
        pending.remove(i)
    objective = max(s + d for s, d in zip(starts, durations, strict=True))
    validate_project(instance, starts, objective)
    return objective, tuple(starts)


def jobshop_schedule(instance, seed):
    """Choose from ready operations conflicting with the earliest completion."""
    rng = Random(seed)
    n, m = len(instance.jobs), instance.machines
    next_operation, job_end, machine_end = [0] * n, [0] * n, [0] * m
    starts = [0] * (n * m)
    for _ in range(n * m):
        ready = [j for j in range(n) if next_operation[j] < m]
        earliest = {
            j: max(job_end[j], machine_end[instance.jobs[j][next_operation[j]][0]])
            for j in ready
        }
        q = min(
            ready,
            key=lambda j: (earliest[j] + instance.jobs[j][next_operation[j]][1], j),
        )
        machine, duration = instance.jobs[q][next_operation[q]]
        finish = earliest[q] + duration
        conflict = [
            j
            for j in ready
            if instance.jobs[j][next_operation[j]][0] == machine
            and earliest[j] < finish
        ]
        j = rng.choice(conflict)
        k = next_operation[j]
        _, duration = instance.jobs[j][k]
        starts[j * m + k] = earliest[j]
        job_end[j] = machine_end[machine] = earliest[j] + duration
        next_operation[j] += 1
    objective = max(job_end)
    validate_jobshop(instance, starts, objective)
    return objective, tuple(starts)


def construct_incumbent(
    instance, *, project_trials=256, jobshop_trials=2048, deadline=None
):
    """Fixed deterministic portfolio; deadline checked between complete trials."""
    if project_trials < 1 or jobshop_trials < 1:
        raise ValueError("trial counts must be positive")
    started = perf_counter()
    best = None
    winning = None
    completed = 0
    history = []
    first_seconds = None
    if isinstance(instance, Project):
        ds = instance.durations
        tails = [0] * len(ds)
        for i in reversed(topological(instance.successors)):
            tails[i] = ds[i] + max(
                (tails[j] for j in instance.successors[i]), default=0
            )
        priorities = [
            list(range(len(ds))),
            [-x for x in tails],
            [-x for x in ds],
            list(ds),
        ]
        trials = project_trials
    else:
        priorities = []
        trials = jobshop_trials
    for seed in range(trials):
        # Always finish one schedule, so a caller can retain a validated witness
        # even if its preparation budget is exceptionally small.
        if completed and deadline is not None and perf_counter() >= deadline:
            break
        if isinstance(instance, Project):
            if seed < len(priorities):
                priority = priorities[seed]
            else:
                priority = list(range(len(instance.durations)))
                Random(seed - len(priorities)).shuffle(priority)
            candidate = project_schedule(instance, priority)
        else:
            candidate = jobshop_schedule(instance, seed)
        completed += 1
        elapsed = perf_counter() - started
        if first_seconds is None:
            first_seconds = elapsed
        if best is None or candidate[0] < best[0]:
            best, winning = candidate, seed
            history.append(dict(objective=best[0], starts=best[1], seconds=elapsed))
    assert best is not None
    return dict(
        objective=best[0],
        starts=best[1],
        trial=winning,
        trials=completed,
        seconds=perf_counter() - started,
        first_seconds=first_seconds,
        best_seconds=history[-1]["seconds"],
        history=history,
    )
