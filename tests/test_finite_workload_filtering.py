"""Independent differential check of incremental workload contribution bounds."""

from itertools import product
from random import Random
from time import perf_counter

import pytest

from snarky import Atom, Number
from snarky.finite import Task, Workload
from snarky.finite.scheduling_kernels import revise_workload


def reference(constraint, domains):
    """Slow per-candidate min/max relaxation, computed from task semantics."""

    def possible():
        low = high = 0
        for task in constraint.tasks:
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
            contributions = []
            for values in product(*(domains[v] for v in scope)):
                row = dict(zip(scope, values, strict=True))
                load = (
                    task.duration
                    if row[task.resource] == constraint.resource
                    and (task.present is None or row[task.present] == Number(1))
                    else 0
                )
                if load and constraint.window is not None:
                    start = row[task.start].value
                    lo, hi = constraint.window
                    load = max(0, min(start + task.duration, hi) - max(start, lo))
                contributions.append(load)
            if not contributions:
                return False
            low += min(contributions)
            high += max(contributions)
        return low <= constraint.maximum and high >= constraint.minimum

    if not possible():
        return False
    for var in domains:
        original = domains[var]
        supported = set()
        for value in original:
            domains[var] = {value}
            if possible():
                supported.add(value)
        domains[var] = supported
        if not supported:
            return False
    return True


def test_seeded_partial_domains_match_reference_with_aliases_and_clipped_windows():
    rng = Random(20928)
    variables = tuple(map(Atom, ("r0", "r1", "p0", "p1", "s0", "s1")))
    for case in range(350):
        # All variables use 0/1 so starts, presence and resources may safely alias.
        tasks = tuple(
            Task(
                f"t{i}",
                rng.choice(variables),
                rng.randint(1, 3),
                rng.choice(variables),
                rng.choice((*variables, None)),
            )
            for i in range(rng.randint(1, 5))
        )
        window = rng.choice((None, (-1, 2), (0, 1), (1, 3), (1, 1)))
        maximum = rng.randint(0, 8)
        constraint = Workload(
            tasks,
            Number(rng.randint(0, 1)),
            maximum,
            minimum=rng.randint(0, maximum),
            window=window,
        )
        domains = {
            v: set(map(Number, rng.choice(((0,), (1,), (0, 1)))))
            for v in constraint.variables
        }
        for current in (domains, {v: {Number(0), Number(1)} for v in domains}, domains):
            expected = {v: set(values) for v, values in current.items()}
            actual = {v: set(values) for v, values in current.items()}
            ok = reference(constraint, expected)
            assert revise_workload(constraint, actual) == ok, case
            if ok:
                assert actual == expected, case


def test_deadline_checked_when_contributions_are_constant():
    r, s = Atom("resource"), Atom("start")
    constraint = Workload((Task("t", s, 2, r),), Atom("absent"), 2)
    with pytest.raises(TimeoutError):
        revise_workload(constraint, {r: {Atom("worker")}}, deadline=perf_counter() - 1)
