"""Measure reusable native kernels, candidate pruning and persistent build caching."""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_residual_enumeration import Compiler, Kernel
from .magic_residual_evaluation import HybridState, check_witness
from .magic_residual_study import freeze, settings
from .magic_search_tuning import RankedState, prepare

ARCHIVE = Path("benchmarks/history/magic_residual_enumeration_2026-10-14")


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def initialize(args):
    extra = [
        args.reference,
        Path(__file__).with_name("test_magic_residual_enumeration.py"),
    ]
    if args.phase == "replay":
        extra.extend(args.capture.glob("states_*.json.gz"))
        extra.append(ARCHIVE / "replay/runs.jsonl")
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        extra_files=extra,
    )
    old, old_report = Kernel.build(args.output / "old.so", source=args.reference)
    new, new_report = Kernel.build(args.output / "new.so")
    save(args.output / "compile.json", dict(old=old_report, new=new_report))
    return old, new


def cache(args):
    initialize(args)
    cache_dir = args.output / "cold_cache"
    _, cold = Kernel.build(args.output / "cold.so", cache_dir=cache_dir)
    _, warm = Kernel.build(args.output / "warm.so", cache_dir=cache_dir)
    code = (
        "import json; from experiments.neural_attention.magic_residual_enumeration "
        "import Kernel; _, r = Kernel.build("
        + repr(str(args.output / "other_process.so"))
        + ", cache_dir="
        + repr(str(cache_dir))
        + "); print(json.dumps(r))"
    )
    other = json.loads(subprocess.check_output([sys.executable, "-c", code], text=True))
    assert not cold["cache_hit"] and cold["compile_seconds"] > 0
    assert warm["cache_hit"] and warm["loaded_reused"]
    assert other["cache_hit"] and not other["loaded_reused"]
    assert warm["compile_seconds"] == other["compile_seconds"] == 0
    report = dict(cold=cold, same_process=warm, new_process=other)
    save(args.output / "cache.json", report)
    print(json.dumps({k: v["seconds"] for k, v in report.items()}), flush=True)


def replay(args):
    old, new = initialize(args)
    expected = {
        (r["size"], r["node"]): r
        for r in map(
            json.loads, (ARCHIVE / "replay/runs.jsonl").read_text().splitlines()
        )
    }
    rng, records = Random(141026), []
    for path in sorted(args.capture.glob("states_*.json.gz")):
        with gzip.open(path, "rt") as stream:
            captured = json.load(stream)
        spec, n = captured["settings"], captured["size"]
        _, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        assert captured["domain_orders"] == [
            [v.value for v in var.domain] for var in model.variables
        ]
        compiler = Compiler(model)
        for sample in captured["samples"]:
            t = perf_counter()
            residual = compiler.extract(sample["masks"])
            extracted = perf_counter() - t
            sorted_residual = replace(
                residual, domains=tuple(tuple(sorted(d)) for d in residual.domains)
            )
            specs = {
                "old2": (old, 2, residual),
                "new2": (new, 2, residual),
                "equations3": (new, 3, residual),
                "sorted_array3": (new, 3, sorted_residual),
                "bitsets4": (new, 4, residual),
            }
            prepared, encoding = {}, {}
            for name, (kernel, _mode, problem) in specs.items():
                t = perf_counter()
                prepared[name] = kernel.prepare(problem)
                encoding[name] = perf_counter() - t
            schedule = [name for name in specs for _ in range(args.repeats)]
            rng.shuffle(schedule)
            timings = {name: [] for name in specs}
            answers = {}
            for name in schedule:
                t = perf_counter()
                answer = prepared[name](specs[name][1], args.work_limit)
                timings[name].append(perf_counter() - t)
                if name in answers:
                    assert answers[name] == answer
                answers[name] = answer
            assert answers["old2"] == answers["new2"]
            oracle = expected[n, sample["node"]]
            for answer in answers.values():
                if answer["witness"] is not None:
                    check_witness(residual, answer["witness"])
                if answer["status"] != 2:
                    assert bool(answer["status"]) == oracle["cp_solved"]
            # Same numeric order and candidate budget isolates data structure
            # effects from changed value order and skipped occupied candidates.
            assert answers["sorted_array3"] == answers["bitsets4"]
            row = dict(
                size=n,
                node=sample["node"],
                extraction_seconds=extracted,
                residual=asdict(residual),
                variants={
                    name: dict(
                        **answer,
                        encoding_seconds=encoding[name],
                        kernel_seconds=median(timings[name]),
                        kernel_samples=timings[name],
                        total_seconds=extracted
                        + encoding[name]
                        + median(timings[name]),
                    )
                    for name, answer in answers.items()
                },
            )
            records.append(row)
            with (args.output / "runs.jsonl").open("a") as stream:
                stream.write(json.dumps(row) + "\n")
    summary = []
    for n in sorted({r["size"] for r in records}):
        group = [r for r in records if r["size"] == n]
        summary.append(
            dict(
                size=n,
                samples=len(group),
                variants={
                    name: dict(
                        completed=sum(
                            r["variants"][name]["status"] != 2 for r in group
                        ),
                        total_kernel_seconds=sum(
                            r["variants"][name]["kernel_seconds"] for r in group
                        ),
                        total_with_preparation_seconds=sum(
                            r["variants"][name]["total_seconds"] for r in group
                        ),
                        visits=sum(r["variants"][name]["visits"] for r in group),
                    )
                    for name in records[0]["variants"]
                },
            )
        )
    save(args.output / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


def whole(args):
    old, new = initialize(args)
    variants = {
        "cp": (None, None),
        "old2": (old, 2),
        "equations3": (new, 3),
        "bitsets4": (new, 4),
    }
    schedule = [
        (n, v, r) for n in args.sizes for v in variants for r in range(args.repeats)
    ]
    Random(141026).shuffle(schedule)
    save(args.output / "schedule.json", schedule)
    records = []
    for n, variant, repeat in schedule:
        spec = settings(n)
        started = perf_counter()
        original, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        kernel, mode = variants[variant]
        state = (
            RankedState(model, spec["order"])
            if kernel is None
            else HybridState(model, spec["order"], kernel, 20, mode, args.work_limit)
        )
        result = search(
            state, Query(time_limit_seconds=args.limit), policy=spec["policy"]
        )
        seconds = perf_counter() - started
        squares = [validate(n, s.assignment, original) for s in result.solutions]
        row = dict(
            size=n,
            variant=variant,
            repeat=repeat,
            seconds=seconds,
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
            termination=result.termination.value,
            squares=squares,
            settings=spec,
            stats=dict(state.stats) if kernel else {},
        )
        records.append(row)
        with (args.output / "runs.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
    summary = [
        dict(
            size=n,
            variants={
                v: dict(
                    median_seconds=median(
                        r["seconds"]
                        for r in records
                        if r["size"] == n and r["variant"] == v
                    ),
                    solved=sum(
                        bool(r["squares"])
                        for r in records
                        if r["size"] == n and r["variant"] == v
                    ),
                )
                for v in variants
            },
        )
        for n in args.sizes
    ]
    save(args.output / "summary.json", summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["cache", "replay", "whole"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--reference", type=Path, default=ARCHIVE / "residual_enum.c.txt"
    )
    parser.add_argument("--capture", type=Path, default=ARCHIVE / "capture_wide")
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 9, 11, 13, 14, 16])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--work-limit", type=int, default=200000)
    parser.add_argument("--limit", type=float, default=15)
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.work_limit < 0
        or args.limit <= 0
        or any(n < 3 for n in args.sizes)
    ):
        parser.error("require positive repeats/time, nonnegative budget and sizes >=3")
    {"cache": cache, "replay": replay, "whole": whole}[args.phase](args)


if __name__ == "__main__":
    main()
