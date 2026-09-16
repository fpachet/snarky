"""Same-FlatZinc-JSON Prune/Snarky comparison, independently checked by Gecode.

This collector keeps compilation and independent checking outside solver-process
measurements. Python startup, decoding, native preparation and solving are inside
Snarky's process timing; Rust startup, decoding, preparation and solving are inside
Prune's. Solver-native statistics are retained but are not interchangeable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import signal
import statistics
import subprocess
import sys
import tarfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "benchmarks/data/prune_d82c64c"
REVISION = "d82c64c29e823513845e56a54e22e21606c0698c"
SUITES = {
    "initial": "manifest.json",
    "extended": "extended_manifest.json",
    "optimization": "cop_manifest.json",
    "all_different": "all_different_manifest.json",
    "incremental_all_different": "all_different_incremental_manifest.json",
    "nvalue": "nvalue_manifest.json",
    "large_domains": "domain_manifest.json",
}
DEFAULT_MINIZINC = "/Applications/MiniZincIDE.app/Contents/Resources/minizinc"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, *, seconds, text=None):
    environment = os.environ.copy()
    environment.update(
        PYTHONHASHSEED="0",
        PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT),
        LC_ALL="C",
    )
    started = perf_counter()
    process = subprocess.Popen(
        list(map(str, command)),
        cwd=ROOT,
        env=environment,
        stdin=subprocess.PIPE if text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timeout = False
    try:
        stdout, stderr = process.communicate(text, timeout=seconds)
    except subprocess.TimeoutExpired:
        timeout = True
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    return {
        "command": list(map(str, command)),
        "seconds": perf_counter() - started,
        "returncode": process.returncode,
        "timed_out": timeout,
        "stdout": stdout,
        "stderr": stderr,
    }


def parse(text):
    solutions = []
    block = []
    status = "unknown"

    def flush():
        if block:
            solutions.append(
                json.dumps(
                    json.loads("\n".join(block)), sort_keys=True, separators=(",", ":")
                )
            )
            block.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("%"):
            continue
        if line == "----------":
            flush()
        elif line == "==========":
            flush()
            status = "complete"
        elif line == "=====UNSATISFIABLE=====":
            flush()
            status = "unsat"
        elif line.startswith("====="):
            flush()
            status = "unknown"
        else:
            block.append(raw)
    flush()
    if status == "unknown" and solutions:
        status = "feasible"
    return {"status": status, "solutions": sorted(set(solutions))}


def load_cases():
    cases = []
    for suite, manifest in SUITES.items():
        for entry in json.loads((VENDOR / "benchmarks" / manifest).read_text())[
            "instances"
        ]:
            cases.append({"id": suite + "/" + entry["name"], "suite": suite, **entry})
    return cases


def prepare(case, output, minizinc, prune):
    stem = case["id"].replace("/", "--")
    source = VENDOR / case["model"]
    actual = source
    patch = None
    if source.name == "dominating_queens_nvalue.mzn":
        # The pinned upstream declaration is rejected by MiniZinc 2.9.7. Only
        # remove the invalid index binder; the comprehension/constraints stay intact.
        original = source.read_text()
        needle = "array[square in squares] of set of int: dominators"
        if original.count(needle) != 1:
            raise ValueError("unexpected upstream NValue model")
        actual = output / "artifacts" / f"{stem}.mzn"
        actual.write_text(
            original.replace(needle, "array[squares] of set of int: dominators")
        )
        patch = {
            "kind": "MiniZinc syntax compatibility",
            "before": needle,
            "after": "array[squares] of set of int: dominators",
            "original_sha256": digest(source),
            "patched_sha256": digest(actual),
        }
    config = output / "prune.msc"
    if not config.exists():
        config.write_text(
            json.dumps(
                {
                    "id": "org.snarky.prune.comparison",
                    "name": "Prune shared benchmark compiler",
                    "version": "0.1.0",
                    "mznlib": str(VENDOR / "minizinc/prune"),
                    "executable": str(prune),
                    "tags": ["cp", "int"],
                    "inputType": "FZN",
                    "needsSolns2Out": True,
                }
            )
        )
    fzn = output / "artifacts" / f"{stem}.fzn.json"
    ozn = output / "artifacts" / f"{stem}.ozn"
    data = [VENDOR / p for p in case.get("data", [])]
    command = [
        minizinc,
        "--compile",
        "--solver",
        config,
        "--fzn-format",
        "json",
        "--output-mode",
        "json",
        "--output-fzn-to-file",
        fzn,
        "--output-ozn-to-file",
        ozn,
        actual,
        *data,
    ]
    compilation = run(command, seconds=60)
    if compilation["returncode"] or compilation["timed_out"]:
        raise RuntimeError(compilation)
    document = json.loads(fzn.read_text())
    return {
        "fzn": fzn,
        "ozn": ozn,
        "model": actual,
        "data": data,
        "patch": patch,
        "compilation": compilation,
        "fzn_sha256": digest(fzn),
        "variables": len(document["variables"]),
        "constraints": len(document["constraints"]),
        "annotations": document["solve"].get("ann", []),
        "compiler_solved": not document["variables"] and not document["constraints"],
    }


def normalized(raw, prepared, minizinc):
    normalization = run([minizinc, "--ozn-file", prepared["ozn"]], seconds=15, text=raw)
    if normalization["returncode"] or normalization["timed_out"]:
        raise RuntimeError(normalization)
    return parse(normalization["stdout"])


def reference(case, prepared, mode, minizinc, seconds, fixed=None):
    command = [
        minizinc,
        "--solver",
        "org.gecode.gecode",
        "-p",
        "1",
        "--output-mode",
        "json",
    ]
    if mode == "all" and not case.get("objective"):
        command.append("-a")
    if fixed is not None:
        command.extend(["--cmdline-json-data", fixed])
    command.extend([prepared["model"], *prepared["data"]])
    record = run(command, seconds=seconds)
    if record["returncode"] or record["timed_out"]:
        raise RuntimeError("Gecode validation did not complete: " + json.dumps(record))
    record["normalized"] = parse(record["stdout"])
    return record


def verify(stream, expected, case, mode):
    if stream["status"] == "unsat":
        if expected["status"] != "unsat":
            raise AssertionError("unexpected unsatisfiability")
        return
    if expected["status"] == "unsat" or not stream["solutions"]:
        raise AssertionError("unexpected or missing solution")
    if mode == "all":
        assert (
            stream["status"] == "complete"
            and stream["solutions"] == expected["solutions"]
        )
    if case.get("objective"):
        assert stream["status"] == "complete", "optimization proof missing"
        specification = case["objective"]
        values = [json.loads(s)[specification["field"]] for s in stream["solutions"]]
        choose = min if specification["direction"] == "minimize" else max
        assert choose(values) == specification["optimum"], (values, specification)


def collect(args):
    if args.output.exists():
        raise ValueError("use a new output directory")
    args.output.mkdir(parents=True)
    (args.output / "artifacts").mkdir()
    cases = [
        c for c in load_cases() if not args.only or any(s in c["id"] for s in args.only)
    ]
    if not cases:
        raise ValueError("no selected cases")
    source_files = [
        *sorted((ROOT / "src").rglob("*.py")),
        ROOT / "benchmarks/prune_bridge.py",
        Path(__file__),
        *sorted(VENDOR.rglob("*")),
    ]
    hashes = {
        str(p.relative_to(ROOT)): digest(p)
        for p in source_files
        if p.is_file() and "__pycache__" not in p.parts
    }
    with tarfile.open(args.output / "sources.tar.gz", "x:gz") as archive:
        for name in hashes:
            archive.add(ROOT / name, arcname=name)
    output = {
        "schema_version": 1,
        "started_at": datetime.now(UTC).isoformat(),
        "prune_revision": REVISION,
        "snarky_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "snarky_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        ),
        "python": sys.version,
        "platform": platform.platform(),
        "machine_notes": args.machine_notes,
        "rustc": run(["rustc", "--version"], seconds=5)["stdout"].strip(),
        "cargo": run(["cargo", "--version"], seconds=5)["stdout"].strip(),
        "minizinc": run([args.minizinc, "--version"], seconds=5)["stdout"],
        "prune_binary_sha256": digest(args.prune),
        "source_hashes": hashes,
        "protocol": {
            "seconds": args.seconds,
            "repeats": args.repeats,
            "warmups": args.warmups,
            "timing": (
                "fresh solver process: startup, JSON parsing, model preparation"
                " and search, output rendering and Snarky primitive checks; "
                "MiniZinc compilation and external correctness checks excluded"
            ),
            "snarky_policy": (
                "dom_wdeg; declared ascending values; FlatZinc search "
                "annotations not translated"
            ),
            "snarky_nvalue_encoding": "native",
            "prune_policy": (
                "upstream defaults and declared annotations; automatic "
                "portfolio where unannotated"
            ),
            "order": "alternated per repetition",
            "validation": (
                "Gecode original-model reference plus fixed-output validation; "
                "Snarky independently checks original FlatZinc constraints"
            ),
            "heldout": "Not used for adapter development or policy tuning",
        },
        "coverage": {
            "requested_instances": 85,
            "available_instances": 54,
            "missing_suites": {"csplib": 20, "reserved_validation": 11},
        },
        "cases": [],
    }
    destination = args.output / "results.json"
    for case in cases:
        prepared = prepare(case, args.output, args.minizinc, args.prune)
        case_record = {
            **case,
            "artifact": str(prepared["fzn"].relative_to(args.output)),
            "fzn_sha256": prepared["fzn_sha256"],
            "compiled_variables": prepared["variables"],
            "compiled_constraints": prepared["constraints"],
            "compiler_solved": prepared["compiler_solved"],
            "search_annotations": prepared["annotations"],
            "compatibility_patch": prepared["patch"],
            "compilation": prepared["compilation"],
            "modes": {},
        }
        for mode in case["modes"]:
            checked = reference(
                case, prepared, mode, args.minizinc, args.validation_seconds
            )
            expected = checked["normalized"]
            if case.get("objective"):
                verify(expected, expected, case, mode)
            data = {"reference": checked, "samples": [], "warmups": []}
            validated = set()
            for iteration in range(args.warmups + args.repeats):
                order = (
                    ("prune", "snarky") if iteration % 2 == 0 else ("snarky", "prune")
                )
                for engine in order:
                    command = (
                        [args.prune, "-s", prepared["fzn"]]
                        if engine == "prune"
                        else [
                            sys.executable,
                            "-m",
                            "benchmarks.prune_bridge",
                            prepared["fzn"],
                        ]
                    )
                    if mode == "all":
                        command.insert(-1, "-a" if engine == "prune" else "--all")
                    record = run(command, seconds=args.seconds)
                    record.update(engine=engine, iteration=iteration - args.warmups)
                    if record["timed_out"]:
                        record["outcome"] = "timeout"
                    elif record["returncode"] == 3 and engine == "snarky":
                        record["outcome"] = "unsupported"
                    elif record["returncode"]:
                        record["outcome"] = "error"
                        raise RuntimeError(record)
                    else:
                        stream = normalized(record["stdout"], prepared, args.minizinc)
                        verify(stream, expected, case, mode)
                        for solution in stream["solutions"]:
                            if solution not in validated and mode != "all":
                                verification = reference(
                                    case,
                                    prepared,
                                    "first",
                                    args.minizinc,
                                    args.validation_seconds,
                                    fixed=solution,
                                )
                                if not verification["normalized"]["solutions"]:
                                    raise AssertionError(
                                        "Gecode rejected fixed solution"
                                    )
                                validated.add(solution)
                        record["normalized"] = stream
                        record["outcome"] = (
                            "unsat"
                            if stream["status"] == "unsat"
                            else "optimal"
                            if case.get("objective")
                            else "complete"
                            if mode == "all"
                            else "satisfiable"
                        )
                        if engine == "snarky":
                            record["native_statistics"] = json.loads(
                                record["stderr"].splitlines()[-1]
                            )
                    data["warmups" if iteration < args.warmups else "samples"].append(
                        record
                    )
                    print(
                        case["id"],
                        mode,
                        iteration - args.warmups,
                        engine,
                        record["outcome"],
                        f"{record['seconds']:.4f}s",
                        flush=True,
                    )
            case_record["modes"][mode] = data
        output["cases"].append(case_record)
        destination.write_text(json.dumps(output, indent=2) + "\n")
    for name, sha in hashes.items():
        assert digest(ROOT / name) == sha, f"source changed during collection: {name}"
    output["finished_at"] = datetime.now(UTC).isoformat()
    destination.write_text(json.dumps(output, indent=2) + "\n")
    summarize(output, args.output / "summary.csv")


def summarize(record, destination):
    rows = []
    for case in record["cases"]:
        for mode, data in case["modes"].items():
            selected = {
                engine: [s for s in data["samples"] if s["engine"] == engine]
                for engine in ("prune", "snarky")
            }
            medians = {
                engine: statistics.median(s["seconds"] for s in samples)
                for engine, samples in selected.items()
            }
            comparable = all(
                all(
                    s["outcome"] not in ("timeout", "unsupported", "error")
                    for s in samples
                )
                for samples in selected.values()
            )
            for engine, samples in selected.items():
                rows.append(
                    {
                        "instance": case["id"],
                        "mode": mode,
                        "engine": engine,
                        "median_process_seconds": medians[engine],
                        "outcomes": ",".join(s["outcome"] for s in samples),
                        "compiler_solved": case["compiler_solved"],
                        "median_native_solve_seconds": statistics.median(
                            s["native_statistics"]["solve_seconds"] for s in samples
                        )
                        if all("native_statistics" in s for s in samples)
                        else "",
                        "median_bridge_preparation_seconds": statistics.median(
                            s["native_statistics"]["preparation_seconds"]
                            for s in samples
                        )
                        if all("native_statistics" in s for s in samples)
                        else "",
                        "snarky_over_prune_ratio": medians["snarky"] / medians["prune"]
                        if comparable
                        else "",
                        "par2_seconds": statistics.mean(
                            2 * record["protocol"]["seconds"]
                            if s["outcome"] == "timeout"
                            else s["seconds"]
                            for s in samples
                        )
                        if all(s["outcome"] != "unsupported" for s in samples)
                        else "",
                    }
                )
    with destination.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prune", type=Path, required=True)
    parser.add_argument("--minizinc", type=Path, default=Path(DEFAULT_MINIZINC))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--validation-seconds", type=float, default=60)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument(
        "--machine-notes", default="Hardware/power conditions not supplied"
    )
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or args.seconds <= 0:
        parser.error("invalid measurement limits")
    args.output = args.output.resolve()
    args.prune = args.prune.resolve()
    collect(args)


if __name__ == "__main__":
    main()
