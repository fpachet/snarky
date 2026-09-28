"""Fresh-process A/B timing of the existing scheduling regression tests.

This measures the old versus new workload filter on identical tests, without
adding symmetry constraints or using timings as assertions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from benchmarks.scheduling_symmetry import REFERENCE, ROOT, install_reference

TESTS = (
    "tests/test_finite_scheduling.py",
    "tests/test_finite_scheduling_extended.py",
    "tests/test_finite_factor_bounds.py",
)


class Timings:
    def __init__(self):
        self.calls = {}
        self.outcomes = {}

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.calls[report.nodeid] = report.duration
            self.outcomes[report.nodeid] = report.outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--reference", action="store_true")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument(
        "--output", type=Path, default=Path("generated/scheduling_test_comparison.json")
    )
    args = parser.parse_args()
    if args.worker:
        import pytest

        if args.reference:
            install_reference()
        timings = Timings()
        start = perf_counter()
        status = pytest.main(
            ["-o", "addopts=", "-p", "no:terminal", *TESTS], plugins=[timings]
        )
        elapsed = perf_counter() - start
        if status != 0:
            raise RuntimeError(f"pytest failed: {status}")
        print(
            json.dumps(
                dict(
                    pytest_seconds=elapsed,
                    calls=timings.calls,
                    outcomes=timings.outcomes,
                )
            )
        )
        return
    if args.repeat < 1 or args.output.exists():
        parser.error("repeat must be positive and output must be a new path")
    sources = [
        *sorted((ROOT / "src/snarky").rglob("*.py")),
        *(ROOT / p for p in TESTS),
        Path(__file__).resolve(),
        ROOT / "benchmarks/scheduling_symmetry.py",
        ROOT / "benchmarks/workforce_scheduling.py",
        ROOT / "benchmarks/workforce_scheduling_extended.py",
    ]
    hashes = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources
    }
    result = dict(
        python=sys.version,
        platform=platform.platform(),
        reference_commit=REFERENCE,
        tests=TESTS,
        repeats=args.repeat,
        source_sha256=hashes,
        runs=[],
    )
    for repeat in range(args.repeat):
        for reference in (True, False) if repeat % 2 == 0 else (False, True):
            cmd = [
                sys.executable,
                "-m",
                "benchmarks.scheduling_test_comparison",
                "--worker",
            ]
            if reference:
                cmd.append("--reference")
            run = json.loads(
                subprocess.check_output(
                    cmd, cwd=ROOT, text=True, env={**os.environ, "PYTHONHASHSEED": "0"}
                )
            )
            assert all(outcome == "passed" for outcome in run["outcomes"].values())
            run.update(reference=reference, repeat=repeat)
            result["runs"].append(run)
            print(
                "reference" if reference else "current",
                round(run["pytest_seconds"], 4),
                flush=True,
            )
    assert hashes == {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources
    }
    result["summary"] = []
    for reference in (True, False):
        runs = [r for r in result["runs"] if r["reference"] == reference]
        result["summary"].append(
            dict(
                reference=reference,
                median_pytest_seconds=statistics.median(
                    r["pytest_seconds"] for r in runs
                ),
                median_call_seconds=statistics.median(
                    sum(r["calls"].values()) for r in runs
                ),
                per_module_call_seconds={
                    module: statistics.median(
                        sum(
                            value
                            for node, value in r["calls"].items()
                            if node.startswith(module + "::")
                        )
                        for r in runs
                    )
                    for module in TESTS
                },
            )
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
