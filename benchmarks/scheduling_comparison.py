"""Fresh-process scheduling A/B measurements; no external data or solver.

python -m benchmarks.scheduling_comparison --baseline /path/to/snapshot \
    --output benchmarks/results/scheduling_2026-09-26.json

The snapshot must contain src/snarky and benchmarks/workforce_scheduling.py.
Each timing includes solve/bound compilation and excludes imports/model construction.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import platform
import statistics
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]


def worker(args):
    sys.path.insert(0, str(args.runtime))
    sys.path.insert(0, str(args.runtime / "src"))
    from benchmarks.workforce_scheduling import build_model
    from snarky import Number
    from snarky.finite import Query, QueryKind, solve

    if "wide_starts" in inspect.signature(build_model).parameters:
        model, tasks = build_model(wide_starts=args.case == "wide")
    else:
        model, tasks = build_model()
        if args.case == "wide":
            starts = {t.start for t in tasks}
            model = replace(
                model,
                variables=tuple(
                    replace(v, domain=tuple(map(Number, range(6, 19))))
                    if v.name in starts
                    else v
                    for v in model.variables
                ),
            )
    if args.audit:
        result = solve(model, Query(QueryKind.ENUMERATE))
        rows = sorted(
            (
                tuple(
                    (
                        t.name,
                        repr(solution.assignment[t.start]),
                        repr(solution.assignment[t.resource]),
                    )
                    for t in tasks
                ),
                solution.objective_value,
            )
            for solution in result.solutions
        )
        print(
            json.dumps(
                dict(
                    complete=result.complete,
                    count=len(rows),
                    projection_sha256=hashlib.sha256(
                        json.dumps(rows).encode()
                    ).hexdigest(),
                )
            )
        )
        return
    start = perf_counter()
    result = solve(
        model,
        Query(QueryKind.MINIMIZE, time_limit_seconds=args.seconds),
        bounding=args.bounding,
        value_policy=args.value_policy,
    )
    print(
        json.dumps(
            dict(
                seconds=perf_counter() - start,
                status=result.status,
                termination=result.termination,
                nodes=result.explored_nodes,
                revisions=result.constraint_revisions,
                failures=result.failed_branches,
                pruned=result.pruned_branches,
                bound=result.objective_bound,
                objective=None
                if result.incumbent is None
                else result.incumbent.objective_value,
                variables=len(model.variables),
                constraints=len(model.constraints),
            )
        )
    )


def sources(root):
    files = sorted((root / "src/snarky").rglob("*.py"))
    files.append(root / "benchmarks/workforce_scheduling.py")
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("generated/scheduling_comparison.json")
    )
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--runtime", type=Path, default=ROOT)
    parser.add_argument("--case", choices=("demo", "wide"), default="demo")
    parser.add_argument("--bounding", default="auto")
    parser.add_argument("--value-policy", default="declared")
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return
    if args.repeat < 1 or args.seconds <= 0:
        parser.error("repeat and seconds must be positive")
    variants = [
        ("current_local", ROOT, "local", "declared"),
        ("current_auto", ROOT, "auto", "declared"),
        ("current_ordered", ROOT, "auto", "objective"),
    ]
    if args.baseline:
        variants.insert(0, ("before", args.baseline.resolve(), "auto", "declared"))
    report = dict(
        timestamp=datetime.now(UTC).isoformat(),
        platform=platform.platform(),
        python=platform.python_version(),
        repeats=args.repeat,
        limit_seconds=args.seconds,
        timing=(
            "fresh process; solve including bound compilation; "
            "excludes imports/construction"
        ),
        commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        dirty_status=subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True
        ),
        sources={str(root): sources(root) for _, root, _, _ in variants},
        note="Wide case expands every task start to 6..18; "
        "cost tables retain their zero defaults. "
        "This is a search-flexibility probe, not a calibrated workforce cost model.",
        runs=[],
    )
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for repeat in range(args.repeat):
        for case in ("demo", "wide"):
            for label, runtime, bounding, ordering in variants:
                command = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--runtime",
                    str(runtime),
                    "--case",
                    case,
                    "--bounding",
                    bounding,
                    "--value-policy",
                    ordering,
                    "--seconds",
                    str(args.seconds),
                ]
                raw = subprocess.run(
                    command,
                    cwd=runtime,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=args.seconds + 30,
                )
                row = dict(
                    label=label,
                    case=case,
                    repeat=repeat,
                    command=command,
                    **json.loads(raw.stdout),
                )
                report["runs"].append(row)
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                print(
                    label,
                    case,
                    row["status"],
                    round(row["seconds"], 4),
                    row["nodes"],
                    flush=True,
                )
    for case in ("demo", "wide"):
        for label, *_ in variants:
            rows = [
                r for r in report["runs"] if r["case"] == case and r["label"] == label
            ]
            print(case, label, "median", statistics.median(r["seconds"] for r in rows))
    print(args.output.resolve())


if __name__ == "__main__":
    main()
