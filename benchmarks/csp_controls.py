"""Same-worker rule, legacy, mixed and exact-Markov controls for CSP changes."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.csp_followup import BASE
from benchmarks.csp_followup import snapshot as runtime_snapshot
from benchmarks.prune_comparison import ROOT, run
from benchmarks.redesign_comparison import snapshot

CONTROLS = (
    ("rules/small/triangle_closure:indexed", "rules"),
    ("joins/25x8/streamed", "rules"),
    ("magic4", "legacy"),
    ("mixed_magic3", "mixed"),
    ("markov33x8", "native"),
    ("boulez", "auto"),
)


def collect(args):
    args.output.mkdir(parents=True, exist_ok=False)
    roots = {"reference": args.reference.resolve(), "candidate": ROOT}
    hashes = {
        name: snapshot(root, args.output / f"{name}.tar.gz")
        for name, root in roots.items()
    }
    records = dict(
        started_at=datetime.now(UTC).isoformat(),
        python=sys.version,
        platform=platform.platform(),
        sources=hashes,
        reference_ref=args.reference_ref,
        candidate_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        candidate_dirty=bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        ),
        shared_workload_root=str(ROOT),
        protocol=(
            "same worker and workloads; three alternating pairs; workers warm up "
            "before each measurement, Boulez has one discarded paired warmup; "
            "search/preparation timing excludes startup"
        ),
        cases=[],
    )
    witness = (
        ROOT / "benchmarks/results/blues_published_witness_2026-09-16.json"
    ).read_bytes()
    (args.output / "boulez_witness.json").write_bytes(witness)
    records["boulez_witness_sha256"] = hashlib.sha256(witness).hexdigest()
    for case, mode in CONTROLS:
        data = dict(case=case, mode=mode, samples=[], warmups=[])
        iterations = range(-1, 3) if case == "boulez" else range(3)
        for iteration in iterations:
            order = list(roots) if iteration % 2 == 0 else list(reversed(roots))
            for engine in order:
                if case == "boulez":
                    command = [
                        sys.executable,
                        ROOT / "benchmarks/boulez_optimization.py",
                        "--worker",
                        "--checkout",
                        roots[engine],
                        "--mode",
                        "auto",
                        "--seconds",
                        "10",
                    ]
                else:
                    command = [
                        sys.executable,
                        ROOT / "benchmarks/redesign_comparison.py",
                        "--worker",
                        "--checkout",
                        roots[engine],
                        "--case",
                        case,
                        "--mode",
                        mode,
                        "--repeat",
                        "1",
                    ]
                record = run(command, seconds=45)
                assert not record["timed_out"] and record["returncode"] == 0, record
                record.update(
                    engine=engine,
                    iteration=iteration,
                    result=json.loads(record["stdout"]),
                )
                data["warmups" if iteration < 0 else "samples"].append(record)
                print(case, engine, iteration, flush=True)
        by_engine = {
            engine: [r["result"] for r in data["samples"] if r["engine"] == engine]
            for engine in roots
        }
        if case == "boulez":
            invariant = (
                "status",
                "termination",
                "solutions",
                "objective_bound",
                "sequence",
                "equals_published_sequence",
                "explored_nodes",
                "failed_branches",
                "constraint_revisions",
            )
            expected = {k: by_engine["reference"][0][k] for k in invariant}
            assert (
                expected["status"] == "optimal"
                and expected["equals_published_sequence"]
            )
            for samples in by_engine.values():
                assert all({k: s[k] for k in invariant} == expected for s in samples)
            data["medians"] = {
                e: statistics.median(s["prepare_and_search_seconds"] for s in ss)
                for e, ss in by_engine.items()
            }
        else:

            def observation(sample):
                return {
                    k: v
                    for k, v in sample["runs"][0]["observation"].items()
                    if not k.endswith("_seconds")
                }

            expected = observation(by_engine["reference"][0])
            for samples in by_engine.values():
                assert all(observation(s) == expected for s in samples)
            data["medians"] = {
                e: statistics.median(s["runs"][0]["total_seconds"] for s in ss)
                for e, ss in by_engine.items()
            }
        data["same_observation"] = True
        data["speedup"] = data["medians"]["reference"] / data["medians"]["candidate"]
        records["cases"].append(data)
        (args.output / "results.json").write_text(json.dumps(records, indent=2) + "\n")
    for name, root in roots.items():
        assert snapshot(root) == hashes[name]
    if args.memory_reference is not None:
        memory_reference = args.memory_reference.resolve()
        memory_hashes, memory_files = runtime_snapshot(
            args.output, memory_reference, "memory_reference"
        )
        records["memory_reference_sources"] = memory_hashes
        records["memory_protocol"] = (
            "one separate allocation-instrumented run per runtime/case; 30 nodes; "
            "20-second cooperative/30-second external cap; reference includes "
            "the same observation hook, with pre-optimization kernels/index; "
            "traced Python allocation and whole-process RSS are separate scopes"
        )
        records["memory"] = []
        for case in (
            "extended--queens_50",
            "optimization--jobshop_ft06_opt",
            "optimization--knapsack_20_opt",
        ):
            samples = []
            for engine, source in (
                ("reference", memory_reference),
                ("candidate", ROOT),
            ):
                command = [
                    sys.executable,
                    ROOT / "benchmarks/csp_diagnostics.py",
                    "--source",
                    source,
                    "--model",
                    BASE / "artifacts" / f"{case}.fzn.json",
                    "--diagnostic",
                    "--allocation",
                    "--nodes",
                    "30",
                    "--seconds",
                    "20",
                ]
                sample = run(command, seconds=30)
                assert not sample["timed_out"] and sample["returncode"] == 0, sample
                sample.update(engine=engine, result=json.loads(sample["stdout"]))
                assert sample["result"]["progress_hook_available"]
                samples.append(sample)
            invariant = (
                "nodes",
                "failures",
                "revisions",
                "objective",
                "objective_bound",
                "flat_output",
            )
            assert all(
                samples[0]["result"][k] == samples[1]["result"][k] for k in invariant
            )
            records["memory"].append(dict(case=case, samples=samples, same_work=True))
            print(case, "memory", flush=True)
        from benchmarks.csp_followup import sha

        assert all(sha(memory_files[k]) == v for k, v in memory_hashes.items())
        assert snapshot(ROOT) == hashes["candidate"]
    records["finished_at"] = datetime.now(UTC).isoformat()
    (args.output / "results.json").write_text(json.dumps(records, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reference-ref", default="88c366f")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--memory-reference", type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    collect(args)


if __name__ == "__main__":
    main()
