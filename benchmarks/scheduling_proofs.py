"""Compare clique resources and domain shaving with the 80abc15 portfolio."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tarfile
import traceback
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from benchmarks.scheduling_instances import (
    Project,
    build_model,
    validate_jobshop,
    validate_project,
)
from benchmarks.scheduling_next import order_problem
from benchmarks.scheduling_standard import (
    CACHE,
    MANIFEST,
    ROOT,
    load_instance,
    reference,
)

PRIOR = ROOT / "benchmarks/results/scheduling_next_2026-09-29.json"
PRIOR_SOURCES = PRIOR.with_name("scheduling_next_2026-09-29_sources.tar.gz")
REFERENCE = ROOT / "generated/scheduling_standard/reference_80abc15"
MAIN = ("previous", "proofs")
VARIANTS = (*MAIN, "cliques", "shaving", "unshaved")


def source_hashes():
    paths = list((ROOT / "src/snarky").rglob("*.py")) + [
        ROOT / "benchmarks" / name
        for name in (
            "scheduling_instances.py",
            "scheduling_standard.py",
            "scheduling_constructive.py",
            "scheduling_improvements.py",
            "scheduling_local.py",
            "scheduling_next.py",
            "scheduling_proofs.py",
            "data/scheduling_standard/manifest.json",
            "data/scheduling_standard/NEXT.md",
            "data/scheduling_standard/PROOFS.md",
        )
    ]
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def prepare_reference():
    hashes = json.loads(PRIOR.read_text())["source_sha256"]
    with tarfile.open(PRIOR_SOURCES) as archive:
        for name, digest in hashes.items():
            if not name.startswith("src/snarky/"):
                continue
            if ".." in Path(name).parts or Path(name).is_absolute():
                raise ValueError("unsafe archived path")
            data = archive.extractfile(name).read()
            assert hashlib.sha256(data).hexdigest() == digest
            target = REFERENCE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return REFERENCE / "src"


def worker(name, variant, seconds, cache, manifest):
    if variant == "previous":
        from benchmarks.scheduling_next import worker as previous_worker

        return previous_worker(name, "order", seconds, cache, manifest)
    from benchmarks.scheduling_constructive import construct_incumbent
    from benchmarks.scheduling_local import improve_incumbent
    from snarky import Number
    from snarky.finite import Query, QueryKind, solve

    instance = load_instance(cache, name, manifest)
    seed = construct_incumbent(instance, deadline=perf_counter() + seconds)
    local = improve_incumbent(
        instance,
        seed,
        iterations=5000,
        deadline=perf_counter() + min(2.0, max(0, seconds - seed["seconds"])),
    )
    heuristic = {
        **seed,
        "objective": local["objective"],
        "starts": local["starts"],
        "seconds": seed["seconds"] + local["seconds"],
        "local_seconds": local["seconds"],
        "local_steps": local["steps"],
        "history": seed["history"]
        + [
            dict(w, seconds=w["seconds"] + seed["seconds"])
            for w in local["history"][1:]
        ],
    }
    heuristic["constructive_objective"] = seed["objective"]
    heuristic["constructive_seconds"] = seed["seconds"]
    heuristic["best_seconds"] = heuristic["history"][-1]["seconds"]
    validator = validate_project if isinstance(instance, Project) else validate_jobshop
    witnesses = [
        dict(
            objective=local["objective"],
            starts=local["starts"],
            validated=True,
            search_seconds=0.0,
        )
    ]
    best_starts, best = local["starts"], local["objective"]
    elapsed = 0.0
    construction = 0.0
    phases = []
    bound = 0
    nodes = 0
    status, termination = "feasible", "preparation_limit"
    project = isinstance(instance, Project)
    if project:
        phase_names = (() if variant == "cliques" else ("windows",)) + (
            "finite_initial",
            "order_cliques" if variant != "shaving" else "order_critical",
        )
    else:
        phase_names = ("order_first", "order_critical")
    for phase in phase_names:
        remaining = seconds - heuristic["seconds"] - elapsed
        if remaining <= 0:
            break
        if phase == "windows":
            budget = min(1.0, remaining)
        elif phase == "finite_initial":
            budget = min(2.5, remaining)
        elif phase == "order_first" and len(phase_names) > 1:
            budget = min(2.0, remaining / 2)
        else:
            budget = remaining
        began = perf_counter()
        if phase.startswith("finite"):
            model, names, makespan, metadata = build_model(
                instance,
                incumbent=best_starts,
            )
            initial = dict(zip(names, map(Number, best_starts), strict=True))
            initial[makespan] = Number(best)
        else:
            problem = order_problem(instance)
            if phase == "order_cliques":
                from snarky.finite.scheduling_search import add_conflict_cliques

                problem = add_conflict_cliques(problem)
            metadata = dict(
                tasks=len(problem.durations), resources=len(problem.capacities)
            )
        construction += perf_counter() - began
        began = perf_counter()

        def accept(objective, starts, offset=elapsed, start_time=began):
            nonlocal best, best_starts
            validator(instance, starts, objective)
            if objective < best:
                best, best_starts = objective, list(starts)
                witnesses.append(
                    dict(
                        objective=best,
                        starts=best_starts,
                        validated=True,
                        search_seconds=offset + perf_counter() - start_time,
                    )
                )

        if phase.startswith("finite"):

            def observe(event, names=names, accept=accept):
                if event.event == "incumbent":
                    sol = event.incumbent
                    accept(
                        sol.objective_value, [sol.assignment[v].value for v in names]
                    )

            result = solve(
                model,
                Query(QueryKind.MINIMIZE, time_limit_seconds=budget),
                initial_assignment=initial,
                policy="dom_wdeg",
                value_policy="objective",
                on_progress=observe,
            )
            phase_bound = result.objective_bound
            phase_nodes = result.explored_nodes
            status, termination = result.status, result.termination
        else:
            from snarky.finite.scheduling_search import solve_schedule

            if phase == "windows":
                from snarky.finite.scheduling_windows import solve_windows

                result = solve_windows(
                    problem,
                    best_starts,
                    seconds=budget,
                    on_incumbent=accept,
                    shaving=variant != "unshaved",
                )
            else:
                result = solve_schedule(
                    problem,
                    best_starts,
                    seconds=budget,
                    on_incumbent=accept,
                    conflict_policy="first" if phase == "order_first" else "critical",
                )
            phase_bound, phase_nodes = result.bound, result.nodes
            status = result.status
            termination = "complete" if status == "optimal" else "time_limit"
        duration = perf_counter() - began
        elapsed += duration
        bound = max(bound, phase_bound if phase_bound is not None else 0)
        nodes += phase_nodes
        phases.append(
            dict(
                phase=phase,
                seconds=duration,
                budget=budget,
                nodes=phase_nodes,
                bound=phase_bound,
                objective=best,
                status=status,
                model=metadata,
                statistics={} if phase.startswith("finite") else result.statistics,
            )
        )
        if status == "optimal":
            break
    validator(instance, best_starts, best)
    return dict(
        status=status,
        termination=termination,
        objective=best,
        bound=bound,
        nodes=nodes,
        heuristic=heuristic,
        witnesses=witnesses,
        phases=phases,
        construction_seconds=construction,
        solve_call_seconds=elapsed,
        algorithm_seconds=heuristic["seconds"] + construction + elapsed,
        absolute_gap=best - bound,
        relative_gap=(best - bound) / max(1, best),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--worker")
    p.add_argument("--variant", choices=VARIANTS, default="proofs")
    p.add_argument("--variants", choices=VARIANTS, nargs="+", default=list(MAIN))
    p.add_argument("--cases", nargs="+")
    p.add_argument("--repeat", type=int, default=3)
    p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--output", type=Path)
    p.add_argument("--cache", type=Path, default=CACHE)
    args = p.parse_args()
    if args.repeat < 1 or not math.isfinite(args.seconds) or args.seconds <= 0:
        p.error("positive repeats and finite positive seconds required")
    manifest = json.loads(MANIFEST.read_text())
    if args.worker:
        print(
            json.dumps(
                worker(args.worker, args.variant, args.seconds, args.cache, manifest)
            )
        )
        return
    names = args.cases or manifest["selection"]
    if set(names) - set(manifest["selection"]):
        p.error("cases must belong to fixed selection")
    if args.output is None or args.output.exists():
        p.error("choose a fresh --output")
    runtime = prepare_reference()
    hashes = source_hashes()
    archive = dict(
        schema=3,
        created_utc=datetime.now(UTC).isoformat(),
        python=sys.version,
        platform=platform.platform(),
        manifest=manifest,
        source_sha256=hashes,
        reference_source_sha256=json.loads(PRIOR.read_text())["source_sha256"],
        settings=dict(
            cases=names,
            variants=args.variants,
            repeats=args.repeat,
            seconds=args.seconds,
            local_iterations=5000,
            local_limit_seconds=2,
            project_trials=256,
            jobshop_trials=2048,
            budget="heuristic and search, construction recorded separately",
            hashseed=0,
        ),
        runs=[],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for repeat in range(args.repeat):
        pairs = [(n, v) for n in names for v in args.variants]
        if repeat % 2:
            pairs.reverse()
        for name, variant in pairs:
            began = perf_counter()
            path = runtime if variant == "previous" else ROOT / "src"
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "benchmarks.scheduling_proofs",
                        "--worker",
                        name,
                        "--variant",
                        variant,
                        "--seconds",
                        str(args.seconds),
                        "--cache",
                        str(args.cache.resolve()),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=args.seconds + 60,
                    env={
                        **os.environ,
                        "PYTHONHASHSEED": "0",
                        "PYTHONPATH": str(path) + os.pathsep + str(ROOT),
                    },
                )
                row = (
                    json.loads(process.stdout)
                    if process.returncode == 0
                    else dict(
                        status="error", stdout=process.stdout, stderr=process.stderr
                    )
                )
            except Exception:
                row = dict(status="error", error=traceback.format_exc())
            row.update(
                instance=name,
                variant=variant,
                repeat=repeat,
                process_seconds=perf_counter() - began,
            )
            value, status = reference(args.cache, name, manifest)
            row.update(reference_objective=value, reference_status=status)
            if row.get("objective") is not None:
                row["reference_gap"] = (row["objective"] - value) / value
                if row["objective"] < value or (
                    row["status"] == "optimal" and row["objective"] != value
                ):
                    row["evaluation_error"] = "contradicts published optimum"
            archive["runs"].append(row)
            args.output.write_text(json.dumps(archive, indent=2) + "\n")
            print(
                name,
                variant,
                repeat,
                row["status"],
                row.get("objective"),
                row.get("bound"),
                round(row["process_seconds"], 3),
                flush=True,
            )
    archive["source_unchanged"] = hashes == source_hashes()
    archive["completed_utc"] = datetime.now(UTC).isoformat()
    args.output.write_text(json.dumps(archive, indent=2) + "\n")
    if not archive["source_unchanged"]:
        raise RuntimeError("measured source changed")


if __name__ == "__main__":
    main()
