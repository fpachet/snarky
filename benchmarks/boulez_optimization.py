"""Paired Boulez optimization measurements, ablations and regression controls.

Workers import the selected checkout before any solver modules. Timing, profiling
and traced-allocation runs are distinct; the latter are not latency measurements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / "benchmarks/results/blues_published_witness_2026-09-16.json"
SUDOKU_INPUT = Path(
    "third_party/test_rulebases/clips-6.4.2/clips_examples_642/"
    "sudoku/puzzles/grid3x3-p7.clp"
)


def worker(args):
    sys.path[:0] = [str(args.checkout / "src"), str(args.checkout)]
    from benchmarks.blues_corpus import training_sequences
    from benchmarks.blues_markov import CORPUS, native_model, train, validate_solution
    from snarky import Atom
    from snarky.finite import Query, QueryKind, solve
    from snarky.finite.cli import result_payload

    started = perf_counter()
    source = train(
        training_sequences(
            json.loads(CORPUS.read_text()), "boulez_two_family_proposed", all_keys=True
        )
    )
    trained = perf_counter()
    model = native_model(source, "boulez")
    constructed = perf_counter()
    names = tuple(v.name for v in model.variables)
    witness = json.loads(WITNESS.read_text())
    target = source.score(tuple(witness["sequence"]))
    options = {"policy": "mrv", "value_policy": "objective", "bounding": args.mode}
    if args.seeded:
        options["initial_assignment"] = dict(
            zip(names, map(Atom, witness["sequence"]), strict=True)
        )
    if args.memory:
        import tracemalloc

        tracemalloc.start()
    before = perf_counter()
    result = solve(
        model, Query(QueryKind.MAXIMIZE, time_limit_seconds=args.seconds), **options
    )
    elapsed = perf_counter() - before
    peak = None
    if args.memory:
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    validate_solution(source, "boulez", result, names)
    data = result_payload(result)
    data.update(
        {
            "training_seconds": trained - started,
            "construction_seconds": constructed - trained,
            "prepare_and_search_seconds": elapsed,
            "traced_peak_bytes": peak,
            "seeded": args.seeded,
            "bound_policy": args.mode,
            "target_product": str(target),
            "first_solution_seconds": result.incumbent_history[0].elapsed_seconds
            if result.incumbent_history
            else None,
            "target_reached_seconds": next(
                (
                    r.elapsed_seconds
                    for r in result.incumbent_history
                    if r.value >= target
                ),
                None,
            ),
            "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        }
    )
    if result.incumbent:
        p = Fraction(result.incumbent.objective_value)
        data["log_probability"] = math.log(p.numerator) - math.log(p.denominator)
        data["sequence"] = [result.incumbent.assignment[v].name for v in names]
        data["equals_published_sequence"] = data["sequence"] == witness["sequence"]
    print(json.dumps(data))


def collect(args):
    from benchmarks.redesign_comparison import (
        CLASSICAL_CASES,
        CSP_CASES,
        JOIN_CASES,
        MARKOV_CASES,
        RULE_CASES,
        snapshot,
    )

    if args.output is None or args.output.exists():
        raise ValueError("supply a fresh output filename")
    # Check external fixture dependencies before starting any measurements.
    puzzle = (ROOT / SUDOKU_INPUT).read_bytes()
    assert (args.reference / SUDOKU_INPUT).read_bytes() == puzzle
    payload = {
        "portfolio": "boulez_optimization_v1",
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "hash_seed": os.environ.get("PYTHONHASHSEED", "unspecified"),
        "reference_commit": "e5e25cf",
        "candidate_base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "candidate_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"])
        ),
        "repeat": args.repeat,
        "search_seconds": args.seconds,
        "hardware_note": "same host; background/thermal state not controlled",
        "timing_scope": (
            "native preparation and search; training/construction separate; "
            "one discarded warmup per configuration"
        ),
        "witness_sha256": hashlib.sha256(WITNESS.read_bytes()).hexdigest(),
        "witness": json.loads(WITNESS.read_text()),
        "sudoku_input": {
            "path": str(SUDOKU_INPUT),
            "sha256": hashlib.sha256(puzzle).hexdigest(),
            "text": puzzle.decode(),
        },
        "sources": {},
        "runs": {},
        "memory": {},
        "regressions": {},
    }
    for label, root in (("reference", args.reference), ("candidate", ROOT)):
        archive = args.output.with_suffix(f".{label}.tar.gz")
        payload["sources"][label] = {
            "archive": archive.name,
            "sha256": snapshot(root, archive),
        }
    configurations = (
        ("reference_chain", args.reference, "auto", False),
        ("candidate_chain", ROOT, "chain", False),
        ("candidate_assignment", ROOT, "auto", False),
        ("candidate_assignment_seeded", ROOT, "auto", True),
    )

    def run(configuration, memory=False):
        _, root, mode, seeded = configuration
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--checkout",
            str(root),
            "--mode",
            mode,
            "--seconds",
            str(60 if memory and mode == "auto" and root == ROOT else args.seconds),
        ]
        if seeded:
            command.append("--seeded")
        if memory:
            command.append("--memory")
        return json.loads(subprocess.check_output(command, cwd=root, text=True))

    for config in configurations:
        print(f"Warmup {config[0]}", flush=True)
        run(config)
        payload["runs"][config[0]] = []
    for i in range(args.repeat):
        for config in configurations if i % 2 == 0 else configurations[::-1]:
            result = run(config)
            payload["runs"][config[0]].append(result)
            args.output.with_suffix(".partial.json").write_text(
                json.dumps(payload, indent=2) + "\n"
            )
            print(
                config[0],
                i,
                result["status"],
                result.get("log_probability"),
                flush=True,
            )
    for config in (configurations[0], configurations[2]):
        print(f"Traced allocation {config[0]}", flush=True)
        payload["memory"][config[0]] = run(config, True)
    regression_cases = [
        *(("rules/" + case, "rules") for case in RULE_CASES),
        *((case, "legacy") for case in (*JOIN_CASES, *CLASSICAL_CASES)),
        *((case, "native") for case in CSP_CASES),
        ("mixed_magic3", "mixed"),
        *((case, "native") for case in MARKOV_CASES),
    ]
    for i, (case, mode) in enumerate(regression_cases):
        print(f"Regression {case}", flush=True)
        results = {}
        roots = (("reference", args.reference), ("candidate", ROOT))
        for label, root in roots if i % 2 == 0 else roots[::-1]:
            command = [
                sys.executable,
                str(ROOT / "benchmarks/redesign_comparison.py"),
                "--worker",
                "--checkout",
                str(root),
                "--case",
                case,
                "--mode",
                mode,
                "--repeat",
                str(args.repeat),
            ]
            results[label] = json.loads(
                subprocess.check_output(command, cwd=root, text=True)
            )
        a = results["reference"]["runs"][0]["observation"]
        b = results["candidate"]["runs"][0]["observation"]
        assert {k: v for k, v in a.items() if not k.endswith("_seconds")} == {
            k: v for k, v in b.items() if not k.endswith("_seconds")
        }, case
        payload["regressions"][case] = results
        args.output.with_suffix(".partial.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
    for label, root in (("reference", args.reference), ("candidate", ROOT)):
        assert (root / SUDOKU_INPUT).read_bytes() == puzzle
        assert snapshot(root) == payload["sources"][label]["sha256"], (
            "sources changed during collection"
        )
    payload["finished_at"] = datetime.now(UTC).isoformat()
    with args.output.open("x") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")
    print(args.output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--checkout", type=Path, default=ROOT)
    parser.add_argument("--mode", choices=("auto", "chain"), default="auto")
    parser.add_argument("--seeded", action="store_true")
    parser.add_argument("--memory", action="store_true")
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--reference", type=Path, default=Path("/tmp/snarky-boulez-reference-e5e25cf")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeat < 1 or not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("positive repeat and finite positive seconds required")
    if args.worker:
        worker(args)
    else:
        collect(args)


if __name__ == "__main__":
    main()
