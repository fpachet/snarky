"""Reproduce interchangeable workforce tasks without a population-service dependency.

Run --output PATH for interleaved fresh-process ablations. The reference workload
kernel is restored from commit f8c82b5; it is used only by the benchmark harness.
"""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import io
import json
import os
import platform
import pstats
import statistics
import subprocess
import sys
import types
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from snarky import Atom, Number
from snarky.finite import (
    FactorObjective,
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    TableFactor,
    Task,
    Workload,
    availability_constraints,
    interchangeable_task_constraints,
    no_overlap_constraints,
    solve,
)
from snarky.finite.predicates import integer

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "benchmarks/data/scheduling_symmetry/inputs.json"
REFERENCE = "f8c82b5"
WINDOWS = {"early": (8, 11), "late": (13, 16)}


def build_model(workers, jobs, *, symmetry=False):
    """Same finite model as the POC, with optional public symmetry constraints."""
    variables, constraints, tasks, factors = [], [], [], []
    for job in jobs:
        start, resource = Atom(job["name"] + "_start"), Atom(job["name"] + "_resource")
        emergency = Atom("emergency_" + job["name"])
        eligible = [w for w in workers if w["skill"] == job["skill"]]
        variables.extend(
            (
                FiniteVariable(start, tuple(map(Number, job["starts"]))),
                FiniteVariable(
                    resource, (*[Atom(w["name"]) for w in eligible], emergency)
                ),
            )
        )
        task = Task(job["name"], start, job["duration"], resource)
        tasks.append(task)
        windows = {Atom(w["name"]): WINDOWS[w["availability"]] for w in eligible}
        windows[emergency] = (min(job["starts"]), max(job["starts"]) + job["duration"])
        constraints.extend(availability_constraints(task, windows))
        factors.append(
            TableFactor("cost_" + job["name"], (resource,), {(emergency,): 100})
        )
    domains = {v.name: v.domain for v in variables}
    constraints.extend(no_overlap_constraints(tasks, domains))
    constraints.extend(Workload(tasks, Atom(w["name"]), maximum=2) for w in workers)
    if symmetry:
        groups = {}
        for job, task in zip(jobs, tasks, strict=True):
            groups.setdefault(
                (job["skill"], tuple(job["starts"]), job["duration"]), []
            ).append(task)
        for group in groups.values():
            constraints.extend(
                interchangeable_task_constraints(
                    group,
                    domains,
                    resource_order=tuple(Atom(w["name"]) for w in workers),
                    private_resources={
                        t.name: Atom("emergency_" + t.name) for t in group
                    },
                    certified=True,
                    distinct_resources=True,
                )
            )
    return FiniteModel(
        "population_workforce",
        tuple(variables),
        tuple(constraints),
        objective=FactorObjective(tuple(factors)),
    ), tuple(tasks)


def matching_cost(workers, jobs):
    """Independent oracle for exactly this one-job-per-worker fixture family."""
    if any(j["duration"] != 2 for j in jobs):
        raise ValueError("oracle requires two-hour jobs and two-hour worker limits")
    edges = []
    for job in jobs:
        edges.append(
            [
                i
                for i, w in enumerate(workers)
                if w["skill"] == job["skill"]
                and any(
                    WINDOWS[w["availability"]][0] <= s
                    and s + job["duration"] <= WINDOWS[w["availability"]][1]
                    for s in job["starts"]
                )
            ]
        )
    owners = {}

    def augment(job, seen):
        for worker in edges[job]:
            if worker not in seen:
                seen.add(worker)
                if worker not in owners or augment(owners[worker], seen):
                    owners[worker] = job
                    return True
        return False

    return 100 * (len(jobs) - sum(augment(i, set()) for i in range(len(jobs))))


def validate(workers, jobs, schedule, cost):
    """Check original hard semantics and cost without Snarky predicates."""
    by_worker = {w["name"]: w for w in workers}
    by_job = {j["name"]: j for j in jobs}
    assert len(schedule) == len(jobs)
    assert {r["job"] for r in schedule} == set(by_job)
    used, actual_cost = set(), 0
    for row in schedule:
        job = by_job[row["job"]]
        assert job["duration"] == 2
        assert row["start"] in job["starts"]
        assert row["end"] == row["start"] + job["duration"]
        if row["resource"] == "emergency_" + job["name"]:
            actual_cost += 100
        else:
            worker = by_worker[row["resource"]]
            assert worker["name"] not in used
            used.add(worker["name"])
            assert worker["skill"] == job["skill"]
            lo, hi = WINDOWS[worker["availability"]]
            assert lo <= row["start"] < row["end"] <= hi
    assert actual_cost == cost


def reference_source():
    return subprocess.check_output(
        ["git", "show", f"{REFERENCE}:src/snarky/finite/scheduling_kernels.py"],
        cwd=ROOT,
        text=True,
    )


def install_reference():
    # A benchmark-only ablation: production APIs never select a historical kernel.
    from snarky.finite import propagation

    module = types.ModuleType("snarky.finite._reference_scheduling_kernels")
    module.__package__ = "snarky.finite"
    exec(
        compile(reference_source(), "reference_scheduling_kernels.py", "exec"),
        module.__dict__,
    )
    propagation.revise_workload = module.revise_workload


def run_one(workers, jobs, symmetry, seconds):
    tick = perf_counter()
    model, tasks = build_model(workers, jobs, symmetry=symmetry)
    construction = perf_counter() - tick
    tick = perf_counter()
    result = solve(
        model,
        Query(QueryKind.MINIMIZE, time_limit_seconds=seconds),
        value_policy="objective",
    )
    elapsed = perf_counter() - tick
    schedule = []
    cost = None
    if result.incumbent is not None:
        sol = result.incumbent
        cost = sol.objective_value
        schedule = [
            dict(
                job=t.name,
                resource=sol.assignment[t.resource].name,
                start=integer(sol.assignment[t.start]),
                end=integer(sol.assignment[t.start]) + t.duration,
            )
            for t in tasks
        ]
        validate(workers, jobs, schedule, cost)
    # Oracle is deliberately called after search and never fed back into it.
    expected = matching_cost(workers, jobs)
    if result.status == "optimal":
        assert cost == expected
    return dict(
        construction_seconds=construction,
        seconds=elapsed,
        status=result.status,
        termination=result.termination,
        nodes=result.explored_nodes,
        revisions=result.constraint_revisions,
        failures=result.failed_branches,
        pruned=result.pruned_branches,
        bound=result.objective_bound,
        objective=cost,
        oracle_cost=expected,
        witness_validated=bool(schedule),
        schedule=schedule,
        first_incumbent_seconds=(
            result.incumbent_history[0].elapsed_seconds
            if result.incumbent_history
            else None
        ),
        proof_seconds=elapsed if result.status == "optimal" else None,
        incumbent_history=[asdict(x) for x in result.incumbent_history],
    )


def worker(args):
    if args.reference:
        install_reference()
    data = json.loads(INPUT.read_text())
    workers, jobs = data["workers"], data["jobs"]
    if args.decomposed:
        records = [
            run_one(
                [w for w in workers if w["skill"] == skill],
                [j for j in jobs if j["skill"] == skill],
                args.symmetry,
                args.seconds,
            )
            for skill in sorted({j["skill"] for j in jobs})
        ]
        schedule = [r for c in records for r in c["schedule"]]
        cost = (
            sum(c["objective"] for c in records)
            if all(c["objective"] is not None for c in records)
            else None
        )
        if cost is not None:
            validate(workers, jobs, schedule, cost)
        proved = all(c["status"] == "optimal" for c in records)
        if proved:
            assert cost == matching_cost(workers, jobs)
        return dict(
            components=records,
            objective=cost,
            status="optimal"
            if proved
            else "feasible"
            if cost is not None
            else "unknown",
            seconds=sum(c["seconds"] for c in records),
            construction_seconds=sum(c["construction_seconds"] for c in records),
            nodes=sum(c["nodes"] for c in records),
            revisions=sum(c["revisions"] for c in records),
            bound=sum(c["bound"] for c in records)
            if all(c["bound"] is not None for c in records)
            else None,
            witness_validated=cost is not None,
        )
    return run_one(workers, jobs, args.symmetry, args.seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--reference", action="store_true")
    parser.add_argument("--symmetry", action="store_true")
    parser.add_argument("--decomposed", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument(
        "--output", type=Path, default=Path("generated/scheduling_symmetry.json")
    )
    args = parser.parse_args()
    if args.worker:
        if args.profile:
            p = cProfile.Profile()
            p.enable()
            record = worker(args)
            p.disable()
            out = io.StringIO()
            pstats.Stats(p, stream=out).strip_dirs().sort_stats(
                "cumulative"
            ).print_stats(35)
            record["profile"] = out.getvalue()
        else:
            record = worker(args)
        print(json.dumps(record))
        return
    if args.repeat < 1 or args.seconds <= 0:
        parser.error("repeat and seconds must be positive")
    if args.output.exists():
        parser.error("choose a new output path; records are never overwritten")
    variants = [
        (name, reference, symmetry, decomposed)
        for decomposed in (False, True)
        for name, reference, symmetry in (
            ("original", True, False),
            ("symmetry_only", True, True),
            ("propagation_only", False, False),
            ("combined", False, True),
        )
    ]
    files = sorted((ROOT / "src/snarky").rglob("*.py")) + [
        Path(__file__).resolve(),
        INPUT,
    ]
    hashes = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }
    archive = dict(
        python=sys.version,
        platform=platform.platform(),
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        source_sha256=hashes,
        input=json.loads(INPUT.read_text()),
        reference_commit=REFERENCE,
        reference_kernel=reference_source(),
        seconds_per_solve=args.seconds,
        repeats=args.repeat,
        runs=[],
        profiles=[],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for repeat in range(args.repeat):
        sequence = variants if repeat % 2 == 0 else list(reversed(variants))
        for name, reference, symmetry, decomposed in sequence:
            cmd = [
                sys.executable,
                "-m",
                "benchmarks.scheduling_symmetry",
                "--worker",
                "--seconds",
                str(args.seconds),
            ]
            cmd += ["--reference"] if reference else []
            cmd += ["--symmetry"] if symmetry else []
            cmd += ["--decomposed"] if decomposed else []
            result = json.loads(
                subprocess.check_output(
                    cmd, cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": "0"}, text=True
                )
            )
            result.update(variant=name, decomposed=decomposed, repeat=repeat)
            archive["runs"].append(result)
            args.output.write_text(json.dumps(archive, indent=2) + "\n")
            print(
                name,
                "components" if decomposed else "monolithic",
                result["status"],
                result["objective"],
                round(result["seconds"], 4),
                result["nodes"],
                flush=True,
            )
    for reference in (True, False):
        cmd = [
            sys.executable,
            "-m",
            "benchmarks.scheduling_symmetry",
            "--worker",
            "--profile",
            "--symmetry",
            "--seconds",
            str(args.seconds),
        ]
        cmd += ["--reference"] if reference else []
        archive["profiles"].append(
            dict(
                reference=reference,
                **json.loads(
                    subprocess.check_output(
                        cmd,
                        cwd=ROOT,
                        text=True,
                        env={**os.environ, "PYTHONHASHSEED": "0"},
                    )
                ),
            )
        )
    assert hashes == {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }
    archive["summary"] = [
        dict(
            variant=name,
            decomposed=decomposed,
            median_seconds=statistics.median(
                r["seconds"]
                for r in archive["runs"]
                if r["variant"] == name and r["decomposed"] == decomposed
            ),
        )
        for name, _, _, decomposed in variants
    ]
    args.output.write_text(json.dumps(archive, indent=2) + "\n")


if __name__ == "__main__":
    main()
