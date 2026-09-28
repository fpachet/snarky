"""Caller-certified task symmetry, independent oracles and unsafe counterexamples."""

from dataclasses import replace
from itertools import product

import pytest

from benchmarks.scheduling_symmetry import build_model, matching_cost, validate
from snarky import Atom, Number
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    NoOverlap,
    Precedence,
    Query,
    QueryKind,
    TableFactor,
    Task,
    Workload,
    enumerate_model,
    interchangeable_task_constraints,
    solve,
)
from snarky.finite.constraints import TableConstraint


def inputs(nworkers, njobs, starts=(8, 9), reverse=False):
    workers = [
        dict(name=f"w{i}", skill="A", availability="early" if i % 2 == 0 else "late")
        for i in range(nworkers)
    ]
    jobs = [
        dict(name=f"j{i}", skill="A", starts=starts, duration=2) for i in range(njobs)
    ]
    return (workers[::-1], jobs[::-1]) if reverse else (workers, jobs)


def brute_cost(workers, jobs):
    """Exhaustive assignment oracle using only the independent schedule checker."""
    options = [
        [
            dict(job=j["name"], resource=r, start=s, end=s + j["duration"])
            for r in [*(w["name"] for w in workers), "emergency_" + j["name"]]
            for s in j["starts"]
        ]
        for j in jobs
    ]
    best, count = None, 0
    for rows in product(*options):
        cost = 100 * sum(r["resource"] == "emergency_" + r["job"] for r in rows)
        try:
            validate(workers, jobs, rows, cost)
        except AssertionError:
            continue
        count += 1
        best = cost if best is None else min(best, cost)
    return best, count


@pytest.mark.parametrize("starts", [(8, 9), (13, 14), (8, 13)])
@pytest.mark.parametrize("nworkers,njobs", [(0, 2), (1, 3), (2, 2), (3, 2)])
@pytest.mark.parametrize("reverse", [False, True])
def test_small_optima_and_every_witness_against_independent_oracle(
    starts, nworkers, njobs, reverse
):
    workers, jobs = inputs(nworkers, njobs, starts, reverse)
    expected, count = brute_cost(workers, jobs)
    assert matching_cost(workers, jobs) == expected
    for symmetry in (False, True):
        model, tasks = build_model(workers, jobs, symmetry=symmetry)
        result = solve(model, Query(QueryKind.MINIMIZE), value_policy="objective")
        assert (
            result.status == "optimal" and result.incumbent.objective_value == expected
        )
        enumerated = solve(model, Query(QueryKind.ENUMERATE))
        reference = enumerate_model(model, Query(QueryKind.ENUMERATE))
        assert {tuple(s.assignment.items()) for s in enumerated.solutions} == {
            tuple(s.assignment.items()) for s in reference.solutions
        }
        if not symmetry:
            assert len(enumerated.solutions) == count
        for sol in enumerated.solutions:
            rows = [
                dict(
                    job=t.name,
                    resource=sol.assignment[t.resource].name,
                    start=sol.assignment[t.start].value,
                    end=sol.assignment[t.start].value + t.duration,
                )
                for t in tasks
            ]
            validate(workers, jobs, rows, sol.objective_value)


def helper(tasks, model, **kwargs):
    return interchangeable_task_constraints(
        tasks,
        model.domains,
        resource_order=(Atom("w0"), Atom("w1")),
        certified=True,
        private_resources={t.name: Atom("emergency_" + t.name) for t in tasks},
        **kwargs,
    )


def test_validation_and_explicit_certification():
    workers, jobs = inputs(2, 2)
    model, tasks = build_model(workers, jobs)
    with pytest.raises(ValueError, match="certification"):
        interchangeable_task_constraints(
            tasks, model.domains, resource_order=(), certified=False
        )
    for overrides in (
        dict(resource_order=(Atom("w0"),)),
        dict(resource_order=(Atom("w0"), Atom("w0"))),
        dict(private_resources={"j0": Atom("emergency_j0")}),
        dict(
            private_resources={"j0": Atom("emergency_j0"), "j1": Atom("emergency_j0")}
        ),
        dict(private_resources={"j0": Atom("w0"), "j1": Atom("w1")}),
    ):
        opts = dict(
            resource_order=(Atom("w0"), Atom("w1")),
            certified=True,
            private_resources={t.name: Atom("emergency_" + t.name) for t in tasks},
        )
        opts.update(overrides)
        with pytest.raises(ValueError):
            interchangeable_task_constraints(tasks, model.domains, **opts)
    for other in (
        replace(tasks[1], duration=1),
        replace(tasks[1], present=Atom("p")),
        replace(tasks[1], resource=tasks[0].resource),
        replace(tasks[1], start=tasks[0].start),
        replace(tasks[1], name=tasks[0].name),
    ):
        with pytest.raises(ValueError):
            helper((tasks[0], other), model)
    for var, removed, message in (
        (tasks[1].start, Number(9), "start domains"),
        (tasks[1].resource, Atom("w1"), "shared eligibility"),
    ):
        domains = dict(model.domains)
        domains[var] = tuple(x for x in domains[var] if x != removed)
        with pytest.raises(ValueError, match=message):
            interchangeable_task_constraints(
                tasks,
                domains,
                resource_order=(Atom("w0"), Atom("w1")),
                certified=True,
                private_resources={t.name: Atom("emergency_" + t.name) for t in tasks},
            )


def test_repeated_workers_allowed_by_default_and_private_emergencies_can_repeat_rank():
    r0, r1, s0, s1 = map(Atom, ("r0", "r1", "s0", "s1"))
    worker = Atom("worker")
    tasks = (Task("a", s0, 1, r0), Task("b", s1, 1, r1))
    model = FiniteModel(
        "reuse",
        tuple(
            FiniteVariable(v, values)
            for v, values in (
                (s0, (Number(8), Number(9))),
                (s1, (Number(8), Number(9))),
                (r0, (worker,)),
                (r1, (worker,)),
            )
        ),
        (Workload(tasks, worker, 2), NoOverlap(*tasks, when_same_resource=True)),
    )
    order = interchangeable_task_constraints(
        tasks, model.domains, resource_order=(worker,), certified=True
    )
    assert (
        solve(replace(model, constraints=(*model.constraints, *order))).incumbent
        is not None
    )
    strict = interchangeable_task_constraints(
        tasks,
        model.domains,
        resource_order=(worker,),
        certified=True,
        distinct_resources=True,
    )
    assert (
        solve(replace(model, constraints=(*model.constraints, *strict))).status
        == "infeasible"
    )
    workers, jobs = inputs(0, 3)
    model, _ = build_model(workers, jobs, symmetry=True)
    assert solve(model, Query(QueryKind.MINIMIZE)).incumbent.objective_value == 300


@pytest.mark.parametrize("kind", ["costs", "restriction", "precedence"])
def test_equal_metadata_does_not_certify_global_symmetry(kind):
    workers, jobs = inputs(2, 2, starts=(8, 13))
    if kind != "precedence":
        workers[1]["availability"] = "early"
    model, tasks = build_model(workers, jobs)
    a, b = Atom("w0"), Atom("w1")
    if kind == "costs":
        factors = tuple(
            TableFactor(
                f"asym{i}",
                (t.resource,),
                {
                    (a,): 10 if i == 0 else 0,
                    (b,): 0 if i == 0 else 10,
                    (Atom("emergency_" + t.name),): 100,
                },
            )
            for i, t in enumerate(tasks)
        )
        model = replace(model, objective=FactorObjective(factors))
    elif kind == "restriction":
        model = replace(
            model,
            constraints=(
                *model.constraints,
                TableConstraint(Atom("specific"), (tasks[0].resource,), ((b,),)),
            ),
        )
    else:
        model = replace(
            model, constraints=(*model.constraints, Precedence(tasks[1], tasks[0]))
        )
    original = solve(model, Query(QueryKind.MINIMIZE))
    assert original.status == "optimal" and original.incumbent.objective_value == 0
    # Deliberately false certification: metadata checks cannot detect these
    # asymmetric constraints/factors. This demonstrates the caller's obligation.
    reduced = replace(
        model,
        constraints=(
            *model.constraints,
            *helper(tasks, model, distinct_resources=True),
        ),
    )
    wrong = solve(reduced, Query(QueryKind.MINIMIZE))
    assert wrong.status == "infeasible" or wrong.incumbent.objective_value > 0
    assert solve(model, Query(QueryKind.MINIMIZE)).incumbent.objective_value == 0


def test_enumeration_unchanged_until_constraints_explicitly_added():
    workers, jobs = inputs(2, 2, starts=(8,))
    workers[1]["availability"] = "early"
    model, tasks = build_model(workers, jobs)
    before = solve(model, Query(QueryKind.ENUMERATE))
    constraints = helper(tasks, model, distinct_resources=True)
    after = solve(model, Query(QueryKind.ENUMERATE))
    assert before == after or before.solutions == after.solutions
    reduced = solve(
        replace(model, constraints=(*model.constraints, *constraints)),
        Query(QueryKind.ENUMERATE),
    )
    assert len(reduced.solutions) < len(before.solutions)


def test_partition_and_sampling_keep_original_labeled_model():
    workers, jobs = inputs(2, 2, starts=(8,))
    workers[1]["availability"] = "early"
    model, tasks = build_model(workers, jobs)
    partition = solve(model, Query(QueryKind.PARTITION)).inference
    sample_query = Query(QueryKind.SAMPLE_EXACT, sample_count=20, seed=19)
    samples = solve(model, sample_query)
    helper(tasks, model, distinct_resources=True)
    again = solve(model, Query(QueryKind.PARTITION)).inference
    assert partition.partition == again.partition == 7
    assert dict(partition.rational_masses) == dict(again.rational_masses)
    assert [s.assignment for s in samples.solutions] == [
        s.assignment for s in solve(model, sample_query).solutions
    ]


def test_maximization_and_identity_renaming_preserve_optimum():
    workers, jobs = inputs(2, 3, starts=(8, 13), reverse=True)
    # Renaming is independent of list order; resource ranks are supplied explicitly.
    for i, worker in enumerate(workers):
        worker["name"] = f"renamed_{100 - i}"
    for i, job in enumerate(jobs):
        job["name"] = f"task_{90 - i}"
    for symmetry in (False, True):
        model, _ = build_model(workers, jobs, symmetry=symmetry)
        result = solve(model, Query(QueryKind.MAXIMIZE))
        assert result.status == "optimal"
        assert result.incumbent.objective_value == 300
        minimum = solve(model, Query(QueryKind.MINIMIZE))
        assert minimum.status == "optimal"
        assert minimum.incumbent.objective_value == matching_cost(workers, jobs)
