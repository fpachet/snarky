"""Collect a fixed, non-Bach redesign baseline with individual timing samples."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmarks import classical_csp, incremental_conjunctions, rulebase_suite
from benchmarks.support import PROJECT_ROOT, git_commit, git_dirty

SOURCE_ROOTS = (
    "src", "csp_solver", "sudoku", "rulebases", "benchmarks",
    "pyproject.toml", "uv.lock",
)
TIMING_FIELDS = {"median_seconds", "min_seconds", "max_seconds", "runs"}


def source_digest() -> tuple[str, int]:
    """Hash tracked workload/runtime files, excluding historical output records."""
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--", *SOURCE_ROOTS], cwd=PROJECT_ROOT,
    )
    paths = sorted(
        path.decode() for path in output.split(b"\0")
        if path and not path.startswith(b"benchmarks/results/")
    )
    digest = hashlib.sha256()
    for relative in paths:
        digest.update(relative.encode() + b"\0")
        path = PROJECT_ROOT / relative
        digest.update(path.read_bytes() if path.is_file() else b"<deleted>")
        digest.update(b"\0")
    return digest.hexdigest(), len(paths)


def cases() -> dict[str, Callable[[], dict[str, Any]]]:
    selected: dict[str, Callable[[], dict[str, Any]]] = {}
    for scenario in (
        "small/triangle_closure", "thesis/hanoi",
        "thesis/monkey_bananas/neopus_mea",
    ):
        for strategy in ("indexed", "semi-naive"):
            selected[f"rules/{scenario}/{strategy}"] = (
                lambda scenario=scenario, strategy=strategy:
                rulebase_suite.measure(scenario, strategy, 1)
            )
    for groups in (25, 100):
        for mode in ("cold", "streamed"):
            operation = getattr(incremental_conjunctions, f"measure_{mode}")
            selected[f"joins/{groups}x8/{mode}"] = (
                lambda groups=groups, operation=operation: operation(groups, 8, 1)
            )
    # The classical runner has its own validators and deterministic counter checks.
    selected["classical"] = lambda: classical_csp.run(1)
    return selected


def collect(repeat: int) -> dict[str, Any]:
    initial_digest, file_count = source_digest()
    payload: dict[str, Any] = {
        "schema_version": 1,
        "suite": "redesign_baseline_v1",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "commit": git_commit(PROJECT_ROOT),
        "working_tree_dirty": git_dirty(PROJECT_ROOT),
        "working_tree_status": subprocess.check_output(
            ["git", "status", "--short"], cwd=PROJECT_ROOT, text=True,
        ).splitlines(),
        "source_sha256": initial_digest,
        "source_file_count": file_count,
        "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "python_hash_seed": os.environ.get("PYTHONHASHSEED", "unspecified"),
        "gc_enabled": gc.isenabled(),
        "repeat": repeat,
        "discarded_warmups_per_case": 1,
        "peak_memory_bytes": None,
        "protocol": (
            "Sequential single-process collection; one discarded warmup; existing "
            "runner timing scopes preserved; raw one-repeat records retained; "
            "no competing benchmark process launched by this collector."
        ),
        "results": {},
    }
    for name, operation in cases().items():
        print(f"Collecting {name}", file=sys.stderr, flush=True)
        operation()
        runs = [operation() for _ in range(repeat)]
        grouped = (
            {key: [run["results"][key] for run in runs]
             for key in runs[0]["results"]}
            if name == "classical" else {name: runs}
        )
        for key, records in grouped.items():
            stable = {k: v for k, v in records[0].items() if k not in TIMING_FIELDS}
            if any(
                {k: v for k, v in record.items() if k not in TIMING_FIELDS} != stable
                for record in records[1:]
            ):
                raise RuntimeError(f"non-deterministic counters for {key}")
            seconds = [record["median_seconds"] for record in records]
            payload["results"][key] = {
                "samples_seconds": seconds,
                "median_seconds": statistics.median(seconds),
                "min_seconds": min(seconds),
                "max_seconds": max(seconds),
                "counters": stable,
                "raw_runs": records,
            }
    if source_digest()[0] != initial_digest:
        raise RuntimeError("workload/runtime sources changed during collection")
    payload["finished_at_utc"] = datetime.now(UTC).isoformat()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")
    if arguments.output.exists():
        parser.error("output exists; use a new record name")
    result = collect(arguments.repeat)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")
    print(arguments.output)


if __name__ == "__main__":
    main()
