"""Matched Python-controller/native DFS benchmark over identical batch filters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky import Number
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_residual_study import freeze, settings
from .magic_search_tuning import prepare
from .model_batch import PRIME, SEED, UINT64, BatchNative, ModelSpec
from .native_search import SearchKernel, solve


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def matched(row):
    return tuple(
        row[k]
        for k in (
            "nodes",
            "failures",
            "revisions",
            "support_calls",
            "cache_hits",
            "reductions",
            "work_digest",
            "termination",
            "squares",
        )
    )


def run(n, kernel, variant, max_nodes, seconds):
    p = settings(n)
    started = perf_counter()
    original, model = prepare(
        n, p["order"], p["tie"], p["symmetry"], seed=p.get("seed", 0)
    )
    spec = ModelSpec(model)
    if variant == "native":
        result = solve(
            spec, kernel, policy=p["policy"], max_nodes=max_nodes, seconds=seconds
        )
        elapsed = perf_counter() - started
        assignments = [
            dict(zip(spec.names, map(Number, values), strict=True))
            for values in result.pop("solutions")
        ]
        result.pop("candidate_solutions")
    else:
        state = BatchNative(model, spec, kernel)
        context, digest = state.batch, [SEED]
        original_execute = context.execute

        def execute(*args, **kwargs):
            status = original_execute(*args, **kwargs)
            for i in (4, 5):
                digest[0] = ((digest[0] ^ int(context.counts[i])) * PRIME) & UINT64
            return status

        context.execute = execute
        searched = perf_counter()
        python = search(
            state,
            Query(max_nodes=max_nodes, time_limit_seconds=seconds),
            policy=p["policy"],
        )
        elapsed = perf_counter() - started
        result = dict(
            nodes=python.explored_nodes,
            failures=python.failed_branches,
            termination=python.termination.value,
            **{
                k: state.batch_totals[k]
                for k in ("revisions", "support_calls", "cache_hits", "reductions")
            },
            work_digest=digest[0],
            search_seconds=perf_counter() - searched,
            solution_count=len(python.solutions),
        )
        assignments = [s.assignment for s in python.solutions]
    result.update(
        size=n,
        variant=variant,
        seconds=elapsed,
        settings=p,
        squares=[validate(n, assignment, original) for assignment in assignments],
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 9, 16, 20])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--large-nodes", type=int, default=5000)
    parser.add_argument("--attempt-seconds", type=float, default=0)
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.large_nodes < 1
        or args.attempt_seconds < 0
        or any(n < 3 for n in args.sizes)
    ):
        parser.error(
            "require positive repetitions/node limit, sizes >=3, nonnegative time"
        )
    folder = Path(__file__).parent
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        extra_files=[
            folder / name
            for name in (
                "model_batch.py",
                "model_batch_runtime.c",
                "sum_support.c",
                "alldiff_support.c",
                "native_search.py",
                "native_search.c",
                "native_search_sanitize.c",
                "test_native_search.py",
                "magic_native_search.py",
            )
        ],
    )
    kernel, report = SearchKernel.build_search(args.output / "search.so")
    save(args.output / "compile.json", report)
    # One unreported warmup per path avoids first-call loader effects in short solves.
    for variant in ("python", "native"):
        run(3, kernel, variant, 10000, 30)
    blocks = [(n, r) for n in args.sizes for r in range(args.repeats)]
    rng = Random(141026)
    rng.shuffle(blocks)
    schedule = []
    for n, repeat in blocks:
        variants = ["python", "native"]
        rng.shuffle(variants)
        schedule.extend((n, repeat, v) for v in variants)
    save(args.output / "schedule.json", schedule)
    signatures, rows = {}, []
    for n, repeat, variant in schedule:
        row = run(n, kernel, variant, 10000 if n <= 16 else args.large_nodes, 60)
        row["repeat"] = repeat
        assert row["termination"] != "time_limit", "increase matched-run cutoff"
        if n in signatures:
            assert signatures[n] == matched(row), (
                "native search changed work or witness"
            )
        signatures[n] = matched(row)
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("settings", "squares")}
            ),
            flush=True,
        )
    summary = []
    for n in args.sizes:
        group = [r for r in rows if r["size"] == n]
        times = {
            v: median(r["seconds"] for r in group if r["variant"] == v)
            for v in ("python", "native")
        }
        summary.append(
            dict(
                size=n,
                **times,
                speedup=times["python"] / times["native"],
                reduction_percent=100 * (1 - times["native"] / times["python"]),
                nodes=group[0]["nodes"],
                solved=bool(group[0]["squares"]),
            )
        )
    save(args.output / "summary.json", summary)
    if args.attempt_seconds:
        row = run(20, kernel, "native", 0, args.attempt_seconds)
        row["nodes_per_second"] = row["nodes"] / row["search_seconds"]
        save(args.output / "attempt20.json", row)
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("settings", "squares")}
            ),
            flush=True,
        )
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
        for p, h in frozen["source_hashes"].items()
    )
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
