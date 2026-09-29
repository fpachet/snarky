"""Input-only local improvement of validated scheduling incumbents."""

from __future__ import annotations

from random import Random
from time import perf_counter

from benchmarks.scheduling_constructive import jobshop_schedule, project_schedule
from benchmarks.scheduling_instances import (
    Project,
    topological,
    validate_jobshop,
    validate_project,
)


def jobshop_graph(instance, orders):
    """Earliest schedule and longest remaining paths for complete machine orders."""
    m = instance.machines
    durations = tuple(d for job in instance.jobs for _, d in job)
    n = len(durations)
    successors = [[] for _ in durations]
    degree = [0] * n
    for i in range(n):
        if (i + 1) % m:
            successors[i].append(i + 1)
            degree[i + 1] += 1
    for row in orders:
        for a, b in zip(row, row[1:], strict=False):
            successors[a].append(b)
            degree[b] += 1
    queue = [i for i in range(n) if degree[i] == 0]
    heads = [0] * n
    for a in queue:
        end = heads[a] + durations[a]
        for b in successors[a]:
            heads[b] = max(heads[b], end)
            degree[b] -= 1
            if degree[b] == 0:
                queue.append(b)
    if len(queue) != n:
        return None
    tails = [0] * n
    for a in reversed(queue):
        tails[a] = max((durations[b] + tails[b] for b in successors[a]), default=0)
    return max(s + d for s, d in zip(heads, durations, strict=True)), heads, tails


def machine_orders(instance, starts):
    operations = [op for job in instance.jobs for op in job]
    return [
        sorted(
            (i for i, (r, _) in enumerate(operations) if r == machine),
            key=lambda i: (starts[i], i),
        )
        for machine in range(instance.machines)
    ]


def improve_incumbent(instance, seed, *, iterations=2000, deadline=None):
    """Deterministic tabu moves for job shop, priority mutations for projects.

    References never enter selection or stopping. Only an input-derived lower
    bound can stop the job-shop heuristic early. No heuristic result is a proof.
    """
    if iterations < 0:
        raise ValueError("iterations must be nonnegative")
    begun = perf_counter()
    best, best_starts = seed["objective"], list(seed["starts"])
    validator = validate_project if isinstance(instance, Project) else validate_jobshop
    validator(instance, best_starts, best)
    history = [dict(objective=best, starts=list(best_starts), seconds=0.0)]
    rng = Random(3292026)
    steps = 0
    if isinstance(instance, Project):
        heads = [0] * len(instance.durations)
        for i in topological(instance.successors):
            for j in instance.successors[i]:
                heads[j] = max(heads[j], heads[i] + instance.durations[i])
        lower = max(h + d for h, d in zip(heads, instance.durations, strict=True))
        for r, cap in enumerate(instance.capacities):
            work = sum(
                d * q[r]
                for d, q in zip(instance.durations, instance.demands, strict=True)
            )
            lower = max(lower, (work + cap - 1) // cap)
        priority = sorted(range(len(best_starts)), key=lambda i: (best_starts[i], i))
        current = best
        for step in range(iterations):
            if (
                best == lower
                or len(priority) < 4
                or (deadline is not None and perf_counter() >= deadline)
            ):
                break
            candidate = priority.copy()
            a, b = rng.sample(range(1, len(candidate) - 1), 2)
            candidate.insert(b, candidate.pop(a))
            ranks = [0] * len(candidate)
            for rank, i in enumerate(candidate):
                ranks[i] = rank
            objective, starts = project_schedule(instance, ranks)
            steps += 1
            if objective <= current or rng.random() < 0.03:
                priority, current = candidate, objective
            if objective < best:
                best, best_starts = objective, list(starts)
                history.append(
                    dict(
                        objective=best,
                        starts=best_starts,
                        seconds=perf_counter() - begun,
                    )
                )
            if step % 200 == 199:
                priority = sorted(
                    range(len(best_starts)), key=lambda i: (best_starts[i], i)
                )
                current = best
    else:
        durations = [d for job in instance.jobs for _, d in job]
        lower = max(
            max(sum(d for _, d in job) for job in instance.jobs),
            max(
                sum(d for job in instance.jobs for r, d in job if r == machine)
                for machine in range(instance.machines)
            ),
        )
        orders = machine_orders(instance, best_starts)
        tabu = {}
        stale = 0
        for step in range(iterations):
            if best == lower or (deadline is not None and perf_counter() >= deadline):
                break
            result = jobshop_graph(instance, orders)
            assert result is not None
            objective, heads, tails = result
            choices = []
            for machine, row in enumerate(orders):
                for k, (a, b) in enumerate(zip(row, row[1:], strict=False)):
                    # Adjacent machine arcs lying on some critical path.
                    if (
                        heads[a] + durations[a] != heads[b]
                        or heads[b] + durations[b] + tails[b] != objective
                    ):
                        continue
                    row[k], row[k + 1] = b, a
                    candidate = jobshop_graph(instance, orders)
                    row[k], row[k + 1] = a, b
                    if candidate is not None and (
                        tabu.get((b, a), -1) <= step or candidate[0] < best
                    ):
                        choices.append(
                            (candidate[0], rng.random(), machine, k, a, b, candidate[1])
                        )
            if not choices or stale >= 80:
                _, starts = jobshop_schedule(instance, step + 10000)
                orders = machine_orders(instance, starts)
                tabu.clear()
                stale = 0
                continue
            objective, _, machine, k, a, b, starts = min(choices)
            orders[machine][k], orders[machine][k + 1] = b, a
            tabu[(a, b)] = step + 7 + rng.randrange(5)
            steps += 1
            stale += 1
            if objective < best:
                validator(instance, starts, objective)
                best, best_starts = objective, list(starts)
                stale = 0
                history.append(
                    dict(
                        objective=best,
                        starts=best_starts,
                        seconds=perf_counter() - begun,
                    )
                )
    validator(instance, best_starts, best)
    return dict(
        objective=best,
        starts=best_starts,
        steps=steps,
        seconds=perf_counter() - begun,
        history=history,
    )
