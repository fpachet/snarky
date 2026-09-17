"""Versioned diagnostics and paired Python comparisons on frozen Prune inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.prune_comparison import (
    DEFAULT_MINIZINC,
    ROOT,
    normalized,
    reference,
    run,
    verify,
)

BASE = ROOT / "benchmarks/results/prune_comparison_2026-09-16"
SLOW = (
    "magic_sequence_20",
    "magic_sequence_40",
    "bin_packing_40",
    "queens_50",
    "queens_104",
    "queens_150",
    "all_different_incremental_16",
    "jobshop_ft06_opt",
    "magic_square_5",
    "all_different_pairwise_10",
    "knapsack_20_opt",
    "bin_packing_20_opt",
    "nvalue_queens_6_sat",
    "nvalue_queens_6_unsat",
    "nvalue_queens_7_sat",
    "nvalue_queens_8_sat",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_progress(text):
    """A killed writer may leave one incomplete final JSON line."""
    events = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            if index == len(lines) - 1 and not text.endswith("\n"):
                return events, True
            raise
    return events, False


def snapshot(output, source, name):
    files = {str(p.relative_to(source)): p for p in (source / "src").rglob("*.py")}
    for relative in (
        "benchmarks/csp_diagnostics.py",
        "benchmarks/csp_followup.py",
        "benchmarks/prune_bridge.py",
        "benchmarks/prune_comparison.py",
    ):
        files[relative] = ROOT / relative
    hashes = {name: sha(path) for name, path in files.items()}
    with tarfile.open(output / f"{name}.tar.gz", "x:gz") as archive:
        for relative, path in files.items():
            archive.add(path, arcname=relative)
    return hashes, files


def validate(record, case, mode, minizinc, cache):
    """Validate partial incumbents too, without demanding a proof from a limit."""
    if record["timed_out"]:
        return
    if record["returncode"]:
        raise RuntimeError(record)
    result = json.loads(record["stdout"])
    record["result"] = result
    prepared = {"ozn": BASE / "artifacts" / f"{case['id'].replace('/', '--')}.ozn"}
    stream = normalized(result["flat_output"], prepared, minizinc)
    expected = case["modes"][mode]["reference"]["normalized"]
    if result["complete"] or result["termination"] == "solution_limit":
        verify(stream, expected, case, mode)
    elif mode == "all":
        assert set(stream["solutions"]) <= set(expected["solutions"])
    if mode != "all":
        from benchmarks.prune_comparison import VENDOR

        prepared.update(
            model=BASE / "artifacts" / f"{case['id'].replace('/', '--')}.mzn"
            if case["compatibility_patch"]
            else VENDOR / case["model"],
            data=[VENDOR / p for p in case.get("data", [])],
        )
        for solution in stream["solutions"]:
            key = (case["id"], solution)
            if key not in cache:
                checked = reference(
                    case, prepared, "first", minizinc, 60, fixed=solution
                )
                assert checked["normalized"]["solutions"], (
                    "Gecode rejected an incumbent"
                )
                cache[key] = checked
    record["normalized"] = stream


def collect(args):
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = json.loads((BASE / "results.json").read_text())
    selected = [
        c
        for c in baseline["cases"]
        if (
            any(s in c["id"] for s in args.only)
            if args.only
            else (
                c["name"] in SLOW and c["suite"] != "initial"
                if args.mode == "diagnose"
                else True
            )
        )
    ]
    if not selected:
        raise ValueError("no cases selected")
    sources = {"candidate": ROOT}
    if args.mode == "compare":
        if args.reference_source is None:
            raise ValueError("comparison requires --reference-source")
        sources = {"reference": args.reference_source.resolve(), **sources}
    archives = {
        name: snapshot(args.output, source, name) for name, source in sources.items()
    }
    import subprocess

    record = dict(
        started_at=datetime.now(UTC).isoformat(),
        mode=args.mode,
        python=sys.version,
        platform=platform.platform(),
        baseline_sha256=sha(BASE / "results.json"),
        candidate_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        candidate_dirty=bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        ),
        reference_ref=args.reference_ref,
        source_hashes={name: a[0] for name, a in archives.items()},
        source_paths={name: str(p) for name, p in sources.items()},
        protocol=dict(
            cooperative_seconds=args.seconds if args.mode == "diagnose" else None,
            hard_seconds=args.hard_seconds,
            nodes=args.nodes if args.mode == "diagnose" else None,
            repeats=args.repeats,
            warmups=args.warmups,
            allocation=args.allocation,
            scope=(
                "fresh process plus separate construction/native-preparation/search "
                "timings; CPU/allocation diagnostics separate from "
                "uninstrumented comparisons"
            ),
            policy="dom_wdeg; declared values; encodings may change search trees",
            nvalue_encoding=dict(
                reference=args.reference_nvalue, candidate=args.candidate_nvalue
            ),
            objective_propagation=dict(
                reference=args.reference_objective_propagation,
                candidate=args.candidate_objective_propagation,
            ),
            alldifferent_masks=dict(
                reference=args.reference_alldifferent_masks,
                candidate=args.candidate_alldifferent_masks,
            ),
            numeric_masks=dict(
                reference=args.reference_numeric_masks,
                candidate=args.candidate_numeric_masks,
            ),
        ),
        cases=[],
    )
    cache = {}
    for case in selected:
        artifact = BASE / case["artifact"]
        assert sha(artifact) == case["fzn_sha256"]
        case_record = dict(
            id=case["id"], artifact=case["artifact"], fzn_sha256=sha(artifact), modes={}
        )
        modes = case["modes"] if args.mode == "compare" else ["first"]
        for mode in modes:
            samples = []
            count = 1 if args.mode == "diagnose" else args.warmups + args.repeats
            for iteration in range(count):
                for engine in (
                    list(sources) if iteration % 2 == 0 else list(reversed(sources))
                ):
                    command = [
                        sys.executable,
                        ROOT / "benchmarks/csp_diagnostics.py",
                        "--source",
                        sources[engine],
                        "--model",
                        artifact,
                        "--nvalue",
                        args.reference_nvalue
                        if engine == "reference"
                        else args.candidate_nvalue,
                        "--objective-propagation",
                        args.reference_objective_propagation
                        if engine == "reference"
                        else args.candidate_objective_propagation,
                        "--alldifferent-masks",
                        args.reference_alldifferent_masks
                        if engine == "reference"
                        else args.candidate_alldifferent_masks,
                        "--numeric-masks",
                        args.reference_numeric_masks
                        if engine == "reference"
                        else args.candidate_numeric_masks,
                    ]
                    if mode == "all":
                        command.append("--all")
                    if args.mode == "diagnose":
                        command.extend(
                            [
                                "--diagnostic",
                                "--seconds",
                                str(args.seconds),
                                "--nodes",
                                str(args.nodes),
                            ]
                        )
                        if args.allocation:
                            command.append("--allocation")
                        else:
                            profile = (
                                args.output / f"{case['id'].replace('/', '--')}.prof"
                            )
                            command.extend(["--profile", profile])
                    sample = run(command, seconds=args.hard_seconds)
                    sample.update(
                        engine=engine,
                        iteration=iteration - args.warmups
                        if args.mode == "compare"
                        else 0,
                    )
                    sample["progress"], sample["progress_truncated"] = read_progress(
                        sample["stderr"]
                    )
                    validate(sample, case, mode, args.minizinc, cache)
                    samples.append(sample)
                    result = sample.get("result", {})
                    print(
                        case["id"],
                        mode,
                        engine,
                        sample["iteration"],
                        "hard_timeout" if sample["timed_out"] else result["status"],
                        f"{sample['seconds']:.4f}s",
                        flush=True,
                    )
            case_record["modes"][mode] = samples
        record["cases"].append(case_record)
        (args.output / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    for name, (hashes, files) in archives.items():
        assert all(sha(files[path]) == expected for path, expected in hashes.items()), (
            f"{name} sources changed"
        )
    record["validation_cache"] = list(cache.values())
    record["finished_at"] = datetime.now(UTC).isoformat()
    (args.output / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    if args.mode == "compare":
        rows = []
        for case in record["cases"]:
            for mode, samples in case["modes"].items():
                groups = {
                    engine: [
                        s
                        for s in samples
                        if s["engine"] == engine and s["iteration"] >= 0
                    ]
                    for engine in sources
                }
                row = dict(case=case["id"], mode=mode)
                for engine, ss in groups.items():
                    row[engine] = dict(
                        median_process_seconds=statistics.median(
                            s["seconds"] for s in ss
                        ),
                        completed=sum(
                            not s["timed_out"]
                            and (
                                s["result"]["complete"]
                                or s["result"]["termination"] == "solution_limit"
                            )
                            for s in ss
                        ),
                        samples=len(ss),
                        native_seconds=[
                            s["result"]["solve_seconds"] for s in ss if "result" in s
                        ],
                        nodes=[s["result"]["nodes"] for s in ss if "result" in s],
                        failures=[s["result"]["failures"] for s in ss if "result" in s],
                        revisions=[
                            s["result"]["revisions"] for s in ss if "result" in s
                        ],
                    )
                if all(
                    v["completed"] == v["samples"]
                    for v in (row["reference"], row["candidate"])
                ):
                    row["process_speedup"] = (
                        row["reference"]["median_process_seconds"]
                        / row["candidate"]["median_process_seconds"]
                    )
                    row["same_search_counts"] = all(
                        row["reference"][k] == row["candidate"][k]
                        for k in ("nodes", "failures", "revisions")
                    )
                    row["same_normalized_solutions"] = [
                        s["normalized"] for s in groups["reference"]
                    ] == [s["normalized"] for s in groups["candidate"]]
                rows.append(row)
        (args.output / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["diagnose", "compare"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-source", type=Path)
    parser.add_argument("--reference-ref", default="88c366f")
    parser.add_argument(
        "--reference-nvalue", choices=["native", "decomposed"], default="decomposed"
    )
    parser.add_argument(
        "--candidate-nvalue", choices=["native", "decomposed"], default="native"
    )
    parser.add_argument("--minizinc", type=Path, default=Path(DEFAULT_MINIZINC))
    parser.add_argument(
        "--reference-alldifferent-masks", choices=["auto", "on", "off"], default="auto"
    )
    parser.add_argument(
        "--candidate-alldifferent-masks", choices=["auto", "on", "off"], default="auto"
    )
    parser.add_argument(
        "--reference-numeric-masks", choices=["auto", "on", "off"], default="auto"
    )
    parser.add_argument(
        "--candidate-numeric-masks", choices=["auto", "on", "off"], default="auto"
    )
    parser.add_argument(
        "--reference-objective-propagation",
        choices=["auto", "on", "off"],
        default="auto",
    )
    parser.add_argument(
        "--candidate-objective-propagation",
        choices=["auto", "on", "off"],
        default="auto",
    )
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--seconds", type=float, default=2)
    parser.add_argument("--hard-seconds", type=float, default=10)
    parser.add_argument("--nodes", type=int, default=200)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--allocation", action="store_true")
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.warmups < 0
        or args.hard_seconds <= 0
        or args.seconds <= 0
        or args.nodes < 1
    ):
        parser.error("invalid limits")
    if args.mode == "compare" and args.allocation:
        parser.error("allocation instrumentation is only for diagnostic runs")
    args.output = args.output.resolve()
    collect(args)


if __name__ == "__main__":
    main()
