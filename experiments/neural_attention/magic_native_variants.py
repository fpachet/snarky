"""Native SUM policy and incremental/storage ablations on magic squares."""

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
from .native_search import solve
from .native_variants import VariantKernel

VARIANTS = {
    "exact": dict(mode="exact"),
    "exact_delta": dict(mode="exact", delta=True),
    "exact_shared": dict(mode="exact", shared=True),
    "exact_both": dict(mode="exact", delta=True, shared=True),
    "bounds_both": dict(mode="bounds", delta=True, shared=True),
    "staged_both": dict(mode="staged", delta=True, shared=True),
    "budget_both": dict(mode="budget", delta=True, shared=True),
}
KEYS = (
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


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def signature(row):
    return tuple(row[k] for k in KEYS)


def run(n, variant, kernel, nodes, limit, p=None):
    p = settings(n) if p is None else p
    started = perf_counter()
    original, model = prepare(
        n, p["order"], p["tie"], p["symmetry"], seed=p.get("seed", 0)
    )
    spec = ModelSpec(model)
    if variant == "python_batch":
        state = BatchNative(model, spec, kernel)
        context, digest = state.batch, [SEED]
        original_execute = context.execute

        def execute(*args, **kwargs):
            status = original_execute(*args, **kwargs)
            for i in (4, 5):
                digest[0] = ((digest[0] ^ int(context.counts[i])) * PRIME) & UINT64
            return status

        context.execute = execute
        entered = perf_counter()
        python = search(
            state,
            Query(max_nodes=nodes or None, time_limit_seconds=limit),
            policy=p["policy"],
        )
        result = dict(
            nodes=python.explored_nodes,
            failures=python.failed_branches,
            termination=python.termination.value,
            work_digest=digest[0],
            search_seconds=perf_counter() - entered,
            solution_count=len(python.solutions),
            **{
                k: state.batch_totals[k]
                for k in ("revisions", "support_calls", "cache_hits", "reductions")
            },
        )
        values = [
            tuple(s.assignment[name].value for name in spec.names)
            for s in python.solutions
        ]
    else:
        result = solve(spec, kernel, policy=p["policy"], max_nodes=nodes, seconds=limit)
        values = result.pop("solutions")
        result.pop("candidate_solutions")
    result["seconds"] = perf_counter() - started
    result.update(
        size=n,
        variant=variant,
        settings=p,
        squares=[
            validate(n, dict(zip(spec.names, map(Number, row), strict=True)), original)
            for row in values
        ],
    )
    return result


def append(path, row):
    with path.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    print(
        json.dumps({k: v for k, v in row.items() if k not in ("squares", "settings")}),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 9, 16, 20])
    parser.add_argument(
        "--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS)
    )
    parser.add_argument("--attempt-seconds", type=float, default=0)
    parser.add_argument("--replays20", type=int, default=5)
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.replays20 < 0
        or args.attempt_seconds < 0
        or any(n < 3 for n in args.sizes)
    ):
        parser.error("invalid repetitions, attempt budget or sizes")
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
                "native_variants.py",
                "linear_bounds.c",
                "alldiff_delta.c",
                "native_shared.c",
                "test_native_variants.py",
                "native_variants_sanitize.py",
                "magic_native_variants.py",
            )
        ],
    )
    kernels = {}
    for variant in args.variants:
        kernels[variant], report = VariantKernel.build_variant(
            args.output / f"{variant}.so", **VARIANTS[variant]
        )
        save(args.output / f"{variant}_compile.json", report)
        run(3, variant, kernels[variant], 50000, 30)
    rng = Random(141026)
    schedule = [
        (n, r, v)
        for n in args.sizes
        for r in range(args.repeats)
        for v in args.variants
    ]
    rng.shuffle(schedule)
    save(args.output / "schedule.json", schedule)
    rows, signatures, exact_signatures = [], {}, {}
    for n, repeat, variant in schedule:
        row = run(n, variant, kernels[variant], 5000 if n >= 20 else 50000, 30)
        row["repeat"] = repeat
        assert row["termination"] != "time_limit", "fixed-prefix run censored"
        key = n, variant
        if key in signatures:
            assert signatures[key] == signature(row)
        signatures[key] = signature(row)
        if VARIANTS[variant]["mode"] == "exact":
            if n in exact_signatures:
                assert exact_signatures[n] == signature(row), (
                    "delta/storage changed propagation/search"
                )
            exact_signatures[n] = signature(row)
        rows.append(row)
        append(args.output / "runs.jsonl", row)
    summary = []
    for n in args.sizes:
        for variant in args.variants:
            group = [r for r in rows if r["size"] == n and r["variant"] == variant]
            summary.append(
                dict(
                    size=n,
                    variant=variant,
                    seconds=median(r["seconds"] for r in group),
                    search_seconds=median(r["search_seconds"] for r in group),
                    nodes=group[0]["nodes"],
                    failures=group[0]["failures"],
                    termination=group[0]["termination"],
                    solved=bool(group[0]["squares"]),
                )
            )
    save(args.output / "summary.json", summary)
    if args.replays20:
        p = dict(
            policy="dom_wdeg", order="random", tie="row_major", symmetry=False, seed=1
        )
        selected = [
            v
            for v in (
                "exact",
                "exact_delta",
                "exact_shared",
                "exact_both",
                "budget_both",
            )
            if v in kernels
        ]
        if "exact" in kernels:
            selected.append("python_batch")
        replay_schedule = [(r, v) for r in range(args.replays20) for v in selected]
        rng.shuffle(replay_schedule)
        save(args.output / "replay20_schedule.json", replay_schedule)
        replay_signatures = {}
        for repeat, variant in replay_schedule:
            row = run(
                20,
                variant,
                kernels["exact" if variant == "python_batch" else variant],
                100000,
                30,
                p,
            )
            row["repeat"] = repeat
            assert row["termination"] == "solution_limit", (
                "20x20 discovery did not reproduce"
            )
            key = (
                "exact"
                if variant
                in (
                    "exact",
                    "exact_delta",
                    "exact_shared",
                    "exact_both",
                    "python_batch",
                )
                else variant
            )
            if key in replay_signatures:
                assert replay_signatures[key] == signature(row)
            replay_signatures[key] = signature(row)
            append(args.output / "replays20.jsonl", row)
    # Separate instrumentation passes: never use these as timing repetitions.
    for variant in args.variants:
        kernel, report = VariantKernel.build_variant(
            args.output / f"profile_{variant}.so", profile=True, **VARIANTS[variant]
        )
        save(args.output / f"profile_{variant}_compile.json", report)
        for n in args.sizes:
            row = run(n, variant, kernel, 5000 if n >= 20 else 50000, 30)
            assert signature(row) == signatures[n, variant]
            append(args.output / "profiles.jsonl", row)
        if args.replays20 and variant in (
            "exact",
            "exact_both",
            "bounds_both",
            "budget_both",
        ):
            p = dict(
                policy="dom_wdeg",
                order="random",
                tie="row_major",
                symmetry=False,
                seed=1,
            )
            row = run(20, variant, kernel, 5000, 30, p)
            if variant in ("exact", "exact_both", "budget_both"):
                assert (
                    signature(row)
                    == replay_signatures[
                        "exact" if variant != "budget_both" else variant
                    ]
                )
            append(args.output / "profiles20.jsonl", row)
    if args.attempt_seconds:
        for choice in ("saved", "random_domwdeg"):
            p = (
                settings(20)
                if choice == "saved"
                else dict(
                    policy="dom_wdeg",
                    order="random",
                    tie="row_major",
                    symmetry=False,
                    seed=1,
                )
            )
            for variant in ("exact_both", "bounds_both", "budget_both"):
                if variant not in kernels:
                    continue
                row = run(20, variant, kernels[variant], 0, args.attempt_seconds, p)
                row["search_choice"] = choice
                row["nodes_per_second"] = row["nodes"] / row["search_seconds"]
                append(args.output / "attempts.jsonl", row)
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
        for p, h in frozen["source_hashes"].items()
    )
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
