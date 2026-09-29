"""Strict benchmark importers, native models and independent schedule validators.

External data is deliberately not bundled. IDs in RCPSP files are 1-based;
internal tuple offsets and job-shop machines are 0-based.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class Project:
    name: str
    durations: tuple[int, ...]
    successors: tuple[tuple[int, ...], ...]
    demands: tuple[tuple[int, ...], ...]
    capacities: tuple[int, ...]
    horizon: int


@dataclass(frozen=True)
class JobShop:
    name: str
    jobs: tuple[tuple[tuple[int, int], ...], ...]
    machines: int


def _rows(section):
    return [
        tuple(map(int, line.split()))
        for line in section.splitlines()
        if re.fullmatch(r"\s*\d+(?:\s+\d+)*\s*", line)
    ]


def topological(successors):
    n = len(successors)
    degree = [0] * n
    for i, edges in enumerate(successors):
        if len(set(edges)) != len(edges) or any(
            j < 0 or j >= n or j == i for j in edges
        ):
            raise ValueError("invalid or duplicate precedence edge")
        for j in edges:
            degree[j] += 1
    ready = [i for i in range(n) if not degree[i]]
    order = []
    while ready:
        i = ready.pop(0)
        order.append(i)
        for j in successors[i]:
            degree[j] -= 1
            if not degree[j]:
                ready.append(j)
    if len(order) != n:
        raise ValueError("cyclic precedence graph")
    return order


def parse_psplib(text, name="project"):
    def header(pattern):
        matches = re.findall(pattern + r"\s*:\s*(\d+)", text, re.M)
        if len(matches) != 1:
            raise ValueError(f"missing/duplicate header: {pattern}")
        return int(matches[0])

    n = header(r"^jobs[^\n:]*")
    h = header(r"^horizon\s*")
    r = header(r"\s*- renewable\s*")
    if (
        header(r"^projects\s*") != 1
        or header(r"\s*- nonrenewable\s*")
        or header(r"\s*- doubly constrained\s*")
    ):
        raise ValueError("requires one project and renewable resources only")
    sections = (
        "PROJECT INFORMATION:",
        "PRECEDENCE RELATIONS:",
        "REQUESTS/DURATIONS:",
        "RESOURCEAVAILABILITIES:",
    )
    if any(text.count(s) != 1 for s in sections):
        raise ValueError("missing/duplicate section")
    info, rest = text.split(sections[0])[1].split(sections[1])
    prec, rest = rest.split(sections[2])
    req, avail = rest.split(sections[3])
    project_info = _rows(info)
    if (
        len(project_info) != 1
        or len(project_info[0]) != 6
        or project_info[0][:3] != (1, n - 2, 0)
    ):
        raise ValueError("requires one zero-release project with source/sink")
    p, q, c = _rows(prec), _rows(req), _rows(avail)
    if n < 3 or r < 1 or h < 1 or len(p) != n or len(q) != n or len(c) != 1:
        raise ValueError("invalid section dimensions")
    if len(c[0]) != r or any(x <= 0 for x in c[0]):
        raise ValueError("invalid capacities")
    successors, durations, demands = [], [], []
    for i, (pr, qr) in enumerate(zip(p, q, strict=True), 1):
        if len(pr) < 3 or pr[:2] != (i, 1) or len(pr) != 3 + pr[2]:
            raise ValueError("invalid precedence row or unsupported modes")
        if len(qr) != 3 + r or qr[:2] != (i, 1):
            raise ValueError("invalid request row or unsupported modes")
        successors.append(tuple(x - 1 for x in pr[3:]))
        durations.append(qr[2])
        demands.append(qr[3:])
    order = topological(successors)
    if (
        durations[0]
        or durations[-1]
        or any(d <= 0 for d in durations[1:-1])
        or any(demands[0])
        or any(demands[-1])
        or successors[-1]
        or any(0 in s for s in successors)
    ):
        raise ValueError("requires zero-demand source/sink and positive real durations")
    reached = {0}
    for i in order:
        if i in reached:
            reached.update(successors[i])
    reaches_sink = {n - 1}
    for i in reversed(order):
        if any(j in reaches_sink for j in successors[i]):
            reaches_sink.add(i)
    if len(reached) != n or len(reaches_sink) != n:
        raise ValueError("all activities must connect source to sink")
    if any(d > cap for row in demands for d, cap in zip(row, c[0], strict=True)):
        raise ValueError("individual demand exceeds capacity")
    # Standard SM horizon is the serial sum, a sufficient bound, not a deadline.
    if h < sum(durations):
        raise ValueError("unsupported horizon smaller than serial bound")
    return Project(name, tuple(durations), tuple(successors), tuple(demands), c[0], h)


def parse_jobshop(text, name):
    blocks = re.split(r"(?m)^\s*instance\s+(\w+)\s*$", text)
    found = [blocks[i + 1] for i in range(1, len(blocks), 2) if blocks[i] == name]
    if len(found) != 1:
        raise ValueError("missing or duplicate instance")
    rows = _rows(found[0])
    if not rows or len(rows[0]) != 2:
        raise ValueError("missing job-shop dimensions")
    n, m = rows[0]
    if n < 1 or m < 1 or len(rows) != n + 1:
        raise ValueError("invalid job count")
    jobs = []
    for row in rows[1:]:
        if len(row) != 2 * m or set(row[::2]) != set(range(m)) or min(row[1::2]) <= 0:
            raise ValueError("requires positive durations and one visit per machine")
        jobs.append(tuple(zip(row[::2], row[1::2], strict=True)))
    return JobShop(name, tuple(jobs), m)


def validate_project(instance, starts, makespan):
    """Check ORIGINAL arcs and slot loads; no solver objects or predicates."""
    if (
        len(starts) != len(instance.durations)
        or type(makespan) is not int
        or any(type(s) is not int or s < 0 for s in starts)
    ):
        raise ValueError("invalid schedule shape or times")
    if starts[0] != 0 or starts[-1] != makespan:
        raise ValueError("dummy source/sink mismatch")
    for i, edges in enumerate(instance.successors):
        if any(starts[i] + instance.durations[i] > starts[j] for j in edges):
            raise ValueError("precedence violation")
    actual = max(
        s + d for s, d in zip(starts[:-1], instance.durations[:-1], strict=True)
    )
    if actual != makespan:
        raise ValueError("makespan is not the maximum real completion")
    for t in range(makespan):
        for r, cap in enumerate(instance.capacities):
            load = sum(
                instance.demands[i][r]
                for i, s in enumerate(starts)
                if s <= t < s + instance.durations[i]
            )
            if load > cap:
                raise ValueError("renewable capacity violation")
    return True


def validate_jobshop(instance, starts, makespan):
    """Check job order and pairwise original machine intervals independently."""
    ops = [op for job in instance.jobs for op in job]
    if (
        len(starts) != len(ops)
        or type(makespan) is not int
        or any(type(s) is not int or s < 0 for s in starts)
    ):
        raise ValueError("invalid schedule shape or times")
    m = instance.machines
    for j in range(len(instance.jobs)):
        for k in range(m - 1):
            i = j * m + k
            if starts[i] + ops[i][1] > starts[i + 1]:
                raise ValueError("job precedence violation")
    for a, b in combinations(range(len(ops)), 2):
        if (
            ops[a][0] == ops[b][0]
            and starts[a] < starts[b] + ops[b][1]
            and starts[b] < starts[a] + ops[a][1]
        ):
            raise ValueError("machine overlap")
    if makespan != max(s + op[1] for s, op in zip(starts, ops, strict=True)):
        raise ValueError("makespan mismatch")
    return True


def build_model(instance, *, compact=False, incumbent=None):
    """Serial horizon, precedence heads/tails, elementary workload lower bound.

    Reference objectives and symmetry never enter this function. An optional
    independently validated incumbent supplies a sound horizon. Compact models
    omit implied end arcs and add redundant unary resource capacities to job shop.
    Makespan is an epigraph variable; minimizing it is equivalent to max(end).
    """
    from snarky import Atom, Number
    from snarky.finite import (
        Capacity,
        FiniteModel,
        FiniteVariable,
        LinearObjective,
        NoOverlap,
        Precedence,
        Task,
    )
    from snarky.finite.constraints import ConstraintOperator, LinearSumConstraint

    if isinstance(instance, Project):
        durations = instance.durations
        successors = instance.successors
    else:
        durations = tuple(d for job in instance.jobs for _, d in job)
        m = instance.machines
        successors = tuple(
            (i + 1,) if (i + 1) % m else () for i in range(len(durations))
        )
    n = len(durations)
    h = sum(durations)
    if incumbent is not None:
        objective = max(s + d for s, d in zip(incumbent, durations, strict=True))
        validator = (
            validate_project if isinstance(instance, Project) else validate_jobshop
        )
        validator(instance, incumbent, objective)
        h = min(h, objective)
    order = topological(successors)
    head, tail = [0] * n, [0] * n
    for i in order:
        for j in successors[i]:
            head[j] = max(head[j], head[i] + durations[i])
    for i in reversed(order):
        tail[i] = max((durations[j] + tail[j] for j in successors[i]), default=0)
    lb = max(head[i] + durations[i] for i in range(n))
    if isinstance(instance, Project):
        for r, cap in enumerate(instance.capacities):
            work = sum(
                d * req[r] for d, req in zip(durations, instance.demands, strict=True)
            )
            lb = max(lb, (work + cap - 1) // cap)
    else:
        for machine in range(instance.machines):
            lb = max(
                lb, sum(d for job in instance.jobs for r, d in job if r == machine)
            )
    starts = tuple(Atom(f"s{i}") for i in range(n))
    makespan = starts[-1] if isinstance(instance, Project) else Atom("makespan")
    variables = []
    for i, var in enumerate(starts):
        lo, hi = head[i], h - durations[i] - tail[i]
        if isinstance(instance, Project):
            if i == 0:
                lo = hi = 0
            if i == n - 1:
                lo = lb
        variables.append(FiniteVariable(var, tuple(map(Number, range(lo, hi + 1)))))
    if isinstance(instance, JobShop):
        variables.append(FiniteVariable(makespan, tuple(map(Number, range(lb, h + 1)))))
    tasks = {i: Task(f"t{i}", starts[i], d) for i, d in enumerate(durations) if d}
    constraints = []
    for i, edges in enumerate(successors):
        for j in edges:
            if i in tasks and j in tasks:
                constraints.append(Precedence(tasks[i], tasks[j]))
            else:
                constraints.append(
                    LinearSumConstraint(
                        Atom(f"arc{i}_{j}"),
                        ((1, starts[i]), (-1, starts[j])),
                        ConstraintOperator.LESS_EQUAL,
                        -durations[i],
                    )
                )
    for i in tasks:
        if compact and (isinstance(instance, Project) or successors[i]):
            continue
        constraints.append(
            LinearSumConstraint(
                Atom(f"end{i}"),
                ((1, starts[i]), (-1, makespan)),
                ConstraintOperator.LESS_EQUAL,
                -durations[i],
            )
        )
    if isinstance(instance, Project):
        for r, cap in enumerate(instance.capacities):
            ids = [i for i in tasks if instance.demands[i][r]]
            if ids:
                constraints.append(
                    Capacity(
                        tuple(tasks[i] for i in ids),
                        cap,
                        tuple(instance.demands[i][r] for i in ids),
                        name=Atom(f"capacity{r}"),
                    )
                )
    else:
        machines = [r for job in instance.jobs for r, _ in job]
        for a, b in combinations(range(n), 2):
            if machines[a] == machines[b]:
                constraints.append(NoOverlap(tasks[a], tasks[b]))
        if compact:
            for machine in range(instance.machines):
                constraints.append(
                    Capacity(
                        tuple(tasks[i] for i in tasks if machines[i] == machine),
                        1,
                        name=Atom(f"machine_capacity{machine}"),
                    )
                )
    return (
        FiniteModel(
            instance.name,
            tuple(variables),
            tuple(constraints),
            objective=LinearObjective(((1, makespan),)),
        ),
        starts,
        makespan,
        {
            "horizon": h,
            "lower_bound": lb,
            "variables": len(variables),
            "constraints": len(constraints),
        },
    )
