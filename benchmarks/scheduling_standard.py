"""Pinned PSPLIB/JSP assessment. Fetch once; run sequential fresh workers offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import traceback
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from benchmarks.scheduling_instances import (
    Project,
    build_model,
    parse_jobshop,
    parse_psplib,
    validate_jobshop,
    validate_project,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/data/scheduling_standard/manifest.json"
CACHE = ROOT / "generated/scheduling_standard/cache"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(cache, name, manifest):
    data = (cache / name).read_bytes()
    if sha(data) != manifest["files"][name]["sha256"]:
        raise ValueError(f"checksum mismatch: {name}")
    return data


def fetch(cache, manifest):
    cache.mkdir(parents=True, exist_ok=True)
    for name, info in manifest["files"].items():
        if (cache / name).exists():
            checked(cache, name, manifest)
            continue
        data = urllib.request.urlopen(info["url"], timeout=60).read()
        if sha(data) != info["sha256"]:
            raise ValueError(
                f"upstream changed: {name}; review before updating manifest"
            )
        (cache / name).write_bytes(data)


def load_instance(cache, name, manifest):
    if name.startswith("j30"):
        import io

        with zipfile.ZipFile(io.BytesIO(checked(cache, "j30.sm.zip", manifest))) as z:
            data = z.read(name + ".sm")
        if sha(data) != manifest["instances"][name]["sha256"]:
            raise ValueError(f"member checksum mismatch: {name}")
        return parse_psplib(data.decode("ascii"), name)
    return parse_jobshop(checked(cache, "jobshop1.txt", manifest).decode("ascii"), name)


def reference(cache, name, manifest):
    # Called only after the solve. Models/workers receive no reference objective.
    if name.startswith("j30"):
        group, replicate = map(int, name[3:].split("_"))
        for line in checked(cache, "j30.opt", manifest).decode("ascii").splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[:2] == [str(group), str(replicate)]:
                return int(fields[2]), "published_proven_optimum"
        raise ValueError("missing PSPLIB optimum")
    info = manifest["jobshop_references"][name]
    return info["objective"], info["status"]


def worker(cache, name, seconds, manifest):
    from snarky.finite import Query, QueryKind, solve
    from snarky.finite.predicates import integer

    t = perf_counter()
    instance = load_instance(cache, name, manifest)
    import_seconds = perf_counter() - t
    t = perf_counter()
    model, starts, makespan, metadata = build_model(instance)
    construction = perf_counter() - t
    witnesses = []
    validation_seconds = 0.0

    def observe(event):
        nonlocal validation_seconds
        if event.event != "incumbent":
            return
        sol = event.incumbent
        schedule = [integer(sol.assignment[s]) for s in starts]
        objective = integer(sol.assignment[makespan])
        # Store the unmodified assignment, including any epigraph slack. A slack
        # incumbent is not passed off as an exact makespan witness.
        record = dict(
            objective=objective,
            starts=schedule,
            search_seconds=event.elapsed_seconds,
            nodes=event.explored_nodes,
            call_seconds=perf_counter() - solve_started,
        )
        witnesses.append(record)
        v = perf_counter()
        validator = (
            validate_project if isinstance(instance, Project) else validate_jobshop
        )
        validator(instance, schedule, objective)
        validation_seconds += perf_counter() - v
        record["validated"] = True

    solve_started = perf_counter()
    try:
        result = solve(
            model,
            Query(QueryKind.MINIMIZE, time_limit_seconds=seconds),
            policy="dom_wdeg",
            value_policy="objective",
            bounding="auto",
            on_progress=observe,
        )
    except Exception:
        return dict(
            status="error",
            termination="exception",
            error=traceback.format_exc(),
            witnesses=witnesses,
            construction_seconds=construction,
            import_seconds=import_seconds,
            model=metadata,
            solve_call_seconds=perf_counter() - solve_started,
        )
    elapsed = perf_counter() - solve_started
    objective = result.incumbent.objective_value if result.incumbent else None
    bound = result.objective_bound
    return dict(
        status=result.status,
        termination=result.termination,
        objective=objective,
        bound=bound,
        absolute_gap=objective - bound
        if objective is not None and bound is not None
        else None,
        relative_gap=(objective - bound) / max(1, abs(objective))
        if objective is not None and bound is not None
        else None,
        nodes=result.explored_nodes,
        revisions=result.constraint_revisions,
        failures=result.failed_branches,
        pruned=result.pruned_branches,
        construction_seconds=construction,
        import_seconds=import_seconds,
        solve_call_seconds=elapsed,
        search_seconds=result.elapsed_seconds,
        validation_seconds=validation_seconds,
        first_feasible_seconds=witnesses[0]["call_seconds"] if witnesses else None,
        best_seconds=witnesses[-1]["call_seconds"] if witnesses else None,
        proof_seconds=elapsed if result.status == "optimal" else None,
        witnesses=witnesses,
        model=metadata,
        diagnostic=result.diagnostic,
    )


def source_hashes():
    paths = sorted((ROOT / "src/snarky").rglob("*.py")) + [
        Path(__file__),
        ROOT / "benchmarks/scheduling_instances.py",
        MANIFEST,
        MANIFEST.with_name("README.md"),
    ]
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--cache", type=Path, default=CACHE)
    p.add_argument("--worker")
    p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--repeat", type=int, default=3)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.repeat < 1:
        p.error("seconds and repeats must be positive and finite")
    manifest = json.loads(MANIFEST.read_text())
    if args.fetch:
        fetch(args.cache, manifest)
        return
    if args.worker:
        print(json.dumps(worker(args.cache, args.worker, args.seconds, manifest)))
        return
    if args.output is None or args.output.exists():
        p.error("choose a new --output; existing evidence is never overwritten")
    hashes = source_hashes()
    archive = dict(
        schema=1,
        created_utc=datetime.now(UTC).isoformat(),
        python=sys.version,
        platform=platform.platform(),
        processor=platform.processor(),
        cpu_count=os.cpu_count(),
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        source_sha256=hashes,
        manifest=manifest,
        settings=dict(
            seconds=args.seconds,
            repeats=args.repeat,
            policy="dom_wdeg",
            value_policy="objective",
            bounding="auto",
            objective_propagation=True,
            numeric_masks=True,
            hashseed=0,
            symmetry=False,
            warm_start=False,
        ),
        runs=[],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    names = manifest["selection"]
    for repeat in range(args.repeat):
        for name in names if repeat % 2 == 0 else reversed(names):
            cmd = [
                sys.executable,
                "-m",
                "benchmarks.scheduling_standard",
                "--worker",
                name,
                "--seconds",
                str(args.seconds),
                "--cache",
                str(args.cache.resolve()),
            ]
            tick = perf_counter()
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    env={**os.environ, "PYTHONHASHSEED": "0"},
                    timeout=args.seconds + 60,
                )
                if proc.returncode:
                    row = dict(
                        status="error",
                        termination="process_failure",
                        returncode=proc.returncode,
                        stdout=proc.stdout,
                        stderr=proc.stderr,
                    )
                else:
                    row = json.loads(proc.stdout)
            except subprocess.TimeoutExpired as e:
                row = dict(status="error", termination="watchdog", error=str(e))
            row.update(
                instance=name, repeat=repeat, process_seconds=perf_counter() - tick
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
        raise RuntimeError("measured sources changed during assessment")


if __name__ == "__main__":
    main()
