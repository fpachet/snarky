"""Fresh-process scheduling ablations against the preserved 48abc8a runtime.

Budget: ten seconds of constructive generation plus search, construction separate.
No reference objective is accessed until the worker finishes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

from benchmarks.scheduling_constructive import construct_incumbent
from benchmarks.scheduling_instances import (
    Project,
    build_model,
    validate_jobshop,
    validate_project,
)
from benchmarks.scheduling_standard import (
    CACHE,
    MANIFEST,
    ROOT,
    load_instance,
    reference,
    source_hashes,
    worker,
)

MAIN_VARIANTS = ("baseline", "kernels", "seeded", "combined")
VARIANTS = (*MAIN_VARIANTS, "numeric_only", "capacity_only", "ordering_only")
BASELINE = ROOT / "benchmarks/results/scheduling_standard_2026-09-29.json"
SOURCE_ARCHIVE = BASELINE.with_name("scheduling_standard_2026-09-29_sources.tar.gz")
REFERENCE_ROOT = ROOT / "generated/scheduling_standard/baseline_runtime"


def prepare_reference():
    """Copy only hash-pinned runtime files, without extracting archive paths."""
    manifest = json.loads(BASELINE.read_text())["source_sha256"]
    with tarfile.open(SOURCE_ARCHIVE) as archive:
        for name, digest in manifest.items():
            if not name.startswith("src/snarky/"):
                continue
            if ".." in Path(name).parts or Path(name).is_absolute():
                raise ValueError("invalid archived path")
            data = archive.extractfile(name).read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError("baseline source checksum mismatch")
            target = REFERENCE_ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return REFERENCE_ROOT / "src"


def hashes():
    result = source_hashes()
    for path in (Path(__file__), ROOT / "benchmarks/scheduling_constructive.py"):
        result[str(path.relative_to(ROOT))] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return result


def seeded_worker(cache, name, seconds, manifest, compact):
    from snarky import Number
    from snarky.finite import Query, QueryKind, solve
    from snarky.finite.predicates import integer

    t = perf_counter()
    instance = load_instance(cache, name, manifest)
    import_seconds = perf_counter() - t
    heuristic = construct_incumbent(instance, deadline=perf_counter() + seconds)
    t = perf_counter()
    model, starts, makespan, metadata = build_model(
        instance, compact=compact, incumbent=heuristic["starts"]
    )
    construction = perf_counter() - t
    initial = dict(zip(starts, map(Number, heuristic["starts"]), strict=True))
    initial[makespan] = Number(heuristic["objective"])
    validator = validate_project if isinstance(instance, Project) else validate_jobshop
    witnesses = []
    validation_seconds = 0.0

    def observe(event):
        nonlocal validation_seconds
        if event.event != "incumbent":
            return
        sol = event.incumbent
        schedule = [integer(sol.assignment[s]) for s in starts]
        objective = integer(sol.assignment[makespan])
        record = dict(
            objective=objective,
            starts=schedule,
            search_seconds=event.elapsed_seconds,
            call_seconds=perf_counter() - solve_started,
            nodes=event.explored_nodes,
        )
        witnesses.append(record)
        t = perf_counter()
        validator(instance, schedule, objective)
        validation_seconds += perf_counter() - t
        record["validated"] = True

    remaining = seconds - heuristic["seconds"]
    common = dict(
        heuristic=heuristic,
        construction_seconds=construction,
        import_seconds=import_seconds,
        model=metadata,
        witnesses=witnesses,
        search_budget_seconds=max(0, remaining),
    )
    if remaining <= 0:
        witnesses.append(
            dict(
                objective=heuristic["objective"],
                starts=heuristic["starts"],
                call_seconds=None,
                search_seconds=None,
                nodes=0,
                validated=True,
            )
        )
        return dict(
            **common,
            status="feasible",
            termination="preparation_limit",
            objective=heuristic["objective"],
            bound=metadata["lower_bound"],
            solve_call_seconds=0,
            search_seconds=0,
            nodes=0,
            revisions=0,
            proof_seconds=None,
            first_feasible_seconds=None,
            best_seconds=None,
        )
    solve_started = perf_counter()
    try:
        result = solve(
            model,
            Query(QueryKind.MINIMIZE, time_limit_seconds=remaining),
            value_policy="objective",
            policy="dom_wdeg",
            bounding="auto",
            initial_assignment=initial,
            on_progress=observe,
        )
    except Exception:
        return dict(
            **common,
            status="error",
            termination="exception",
            error=traceback.format_exc(),
            solve_call_seconds=perf_counter() - solve_started,
        )
    elapsed = perf_counter() - solve_started
    obj = result.incumbent.objective_value if result.incumbent else None
    bound = result.objective_bound
    return dict(
        **common,
        status=result.status,
        termination=result.termination,
        objective=obj,
        bound=bound,
        absolute_gap=obj - bound if obj is not None and bound is not None else None,
        relative_gap=(obj - bound) / max(1, abs(obj))
        if obj is not None and bound is not None
        else None,
        nodes=result.explored_nodes,
        revisions=result.constraint_revisions,
        failures=result.failed_branches,
        pruned=result.pruned_branches,
        solve_call_seconds=elapsed,
        search_seconds=result.elapsed_seconds,
        first_feasible_seconds=witnesses[0]["call_seconds"] if witnesses else None,
        best_seconds=witnesses[-1]["call_seconds"] if witnesses else None,
        proof_seconds=elapsed if result.status == "optimal" else None,
        validation_seconds=validation_seconds,
        diagnostic=result.diagnostic,
    )


def run_worker(args, manifest):
    import snarky

    if args.variant in ("numeric_only", "capacity_only", "ordering_only"):
        from snarky.finite import numeric, propagation

        def archived_module(name):
            path = REFERENCE_ROOT / "src/snarky/finite" / (name + ".py")
            module_name = "snarky.finite._scheduling_reference_" + name
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module

        if args.variant != "capacity_only":
            propagation.revise_capacity = archived_module("capacity").revise_capacity
        if args.variant != "numeric_only":
            numeric.NumericPlans.disjunction = lambda self, index, constraint: None
        if args.variant != "ordering_only":
            snarky.finite.solve = archived_module("search").solve

    row = (
        worker(args.cache, args.worker, args.seconds, manifest)
        if args.variant not in ("seeded", "combined")
        else seeded_worker(
            args.cache, args.worker, args.seconds, manifest, args.variant == "combined"
        )
    )
    row["runtime_path"] = str(Path(snarky.__file__).resolve())
    prep = row.get("heuristic", {}).get("seconds", 0)
    build = row.get("construction_seconds", 0)
    row["algorithm_seconds"] = prep + build + row.get("solve_call_seconds", 0)
    row["algorithm_proof_seconds"] = (
        row["algorithm_seconds"] if row["status"] == "optimal" else None
    )
    row["algorithm_first_feasible_seconds"] = (
        row["heuristic"]["first_seconds"]
        if "heuristic" in row
        else build + row["first_feasible_seconds"]
        if row.get("first_feasible_seconds") is not None
        else None
    )
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--worker")
    p.add_argument("--variant", choices=VARIANTS, default="combined")
    p.add_argument(
        "--variants", nargs="+", choices=VARIANTS, default=list(MAIN_VARIANTS)
    )
    p.add_argument("--cases", nargs="+")
    p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--repeat", type=int, default=3)
    p.add_argument("--cache", type=Path, default=CACHE)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.repeat < 1:
        p.error("seconds and repeats must be positive")
    manifest = json.loads(MANIFEST.read_text())
    if args.worker:
        print(json.dumps(run_worker(args, manifest)))
        return
    names = args.cases or manifest["selection"]
    if set(names) - set(manifest["selection"]):
        p.error("cases must be in the fixed selection")
    if args.output is None or args.output.exists():
        p.error("choose a new --output")
    ref = prepare_reference()
    recorded = hashes()
    archive = dict(
        schema=2,
        created_utc=datetime.now(UTC).isoformat(),
        python=sys.version,
        platform=platform.platform(),
        source_sha256=recorded,
        baseline_source_sha256=json.loads(BASELINE.read_text())["source_sha256"],
        manifest=manifest,
        settings=dict(
            variants=args.variants,
            cases=names,
            repeats=args.repeat,
            seconds=args.seconds,
            budget="heuristic plus search; construction recorded separately",
            project_trials=256,
            jobshop_trials=2048,
            hashseed=0,
            policy="dom_wdeg",
            value_policy="objective",
            bounding="auto",
        ),
        runs=[],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for repeat in range(args.repeat):
        pairs = [(name, variant) for name in names for variant in args.variants]
        if repeat % 2:
            pairs.reverse()
        for name, variant in pairs:
            runtime = ref if variant == "baseline" else ROOT / "src"
            command = [
                sys.executable,
                "-m",
                "benchmarks.scheduling_improvements",
                "--worker",
                name,
                "--variant",
                variant,
                "--seconds",
                str(args.seconds),
                "--cache",
                str(args.cache.resolve()),
            ]
            tick = perf_counter()
            try:
                proc = subprocess.run(
                    command,
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    timeout=args.seconds + 60,
                    env={
                        **os.environ,
                        "PYTHONHASHSEED": "0",
                        "PYTHONPATH": str(runtime) + os.pathsep + str(ROOT),
                    },
                )
                row = (
                    json.loads(proc.stdout)
                    if not proc.returncode
                    else dict(
                        status="error",
                        termination="process_failure",
                        stdout=proc.stdout,
                        stderr=proc.stderr,
                        returncode=proc.returncode,
                    )
                )
            except subprocess.TimeoutExpired as error:
                row = dict(status="error", termination="watchdog", error=str(error))
            except Exception:
                row = dict(
                    status="error",
                    termination="harness_error",
                    error=traceback.format_exc(),
                )
            row.update(
                instance=name,
                variant=variant,
                repeat=repeat,
                process_seconds=perf_counter() - tick,
            )
            try:
                target, status = reference(args.cache, name, manifest)
                row.update(reference_objective=target, reference_status=status)
                if row.get("objective") is not None:
                    row["reference_gap"] = (row["objective"] - target) / target
                    if row["objective"] < target or (
                        row["status"] == "optimal" and row["objective"] != target
                    ):
                        row["evaluation_error"] = "contradicts published optimum"
            except Exception:
                row["evaluation_error"] = traceback.format_exc()
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
    archive["source_unchanged"] = recorded == hashes()
    archive["completed_utc"] = datetime.now(UTC).isoformat()
    args.output.write_text(json.dumps(archive, indent=2) + "\n")
    if not archive["source_unchanged"]:
        raise RuntimeError("measured source changed")


if __name__ == "__main__":
    main()
