"""Compare whole searches: Python-controlled native filters vs native batches."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .alldiff_kernel import AllDiffKernel
from .alldiff_kernel import enable as enable_alldiff
from .magic_residual_enumeration import Kernel
from .magic_residual_evaluation import HybridState
from .magic_residual_study import freeze, settings
from .magic_search_tuning import RankedDomains, RankedState, prepare
from .model_batch import BatchKernel, BatchNative, ModelSpec
from .sum_kernel import SumKernel
from .sum_kernel import enable as enable_sum


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def record_reductions(domains):
    original = domains.retain_mask
    digest, events = hashlib.sha256(), [0]

    def retain(variable, supported, cause):
        index = domains.index(variable)
        before = domains._masks[index]
        changed = original(variable, supported, cause)
        if changed:
            digest.update(
                json.dumps([index, before, domains._masks[index], str(cause)]).encode()
                + b"\n"
            )
            events[0] += 1
        return changed

    domains.retain_mask = retain
    return digest, events


def signature(row):
    return (
        row["nodes"],
        row["failures"],
        row["revisions"],
        row["termination"],
        row["squares"],
        {k: v for k, v in row["residual_stats"].items() if k != "enum_seconds"},
        row.get("reductions_sha256"),
        row.get("reduction_events"),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["audit", "timing"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 9, 16, 20])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--large-nodes", type=int, default=5000)
    parser.add_argument("--limit", type=float, default=60)
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.large_nodes < 1
        or args.limit <= 0
        or any(n < 3 for n in args.sizes)
    ):
        parser.error("require positive repeats/node/time limits and sizes >=3")
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        extra_files=[
            Path(__file__),
            Path(__file__).with_name("sum_kernel.py"),
            Path(__file__).with_name("sum_support.c"),
            Path(__file__).with_name("test_sum_kernel.py"),
            Path(__file__).with_name("alldiff_kernel.py"),
            Path(__file__).with_name("alldiff_support.c"),
            Path(__file__).with_name("alldiff_kernel_sanitize.c"),
            Path(__file__).with_name("test_alldiff_kernel.py"),
            Path(__file__).with_name("model_batch.py"),
            Path(__file__).with_name("model_batch_runtime.c"),
            Path(__file__).with_name("model_batch_sanitize.c"),
            Path(__file__).with_name("model_batch_sanitize.py"),
            Path(__file__).with_name("test_model_batch.py"),
            Path(__file__).with_name("magic_sum_kernel.py"),
        ],
    )
    residual, residual_build = Kernel.build(args.output / "residual.so")
    sums, sum_build = SumKernel.build(args.output / "sum.so")
    alldiff, alldiff_build = AllDiffKernel.build(args.output / "alldiff.so")
    save(
        args.output / "compile.json",
        dict(residual=residual_build, sums=sum_build, alldiff=alldiff_build),
    )
    generic, generic_build = BatchKernel.build_model(args.output / "generic.so")
    save(args.output / "generic_compile.json", generic_build)
    specialized = {}
    for n in args.sizes:
        p = settings(n)
        _, m = prepare(n, p["order"], p["tie"], p["symmetry"], seed=p.get("seed", 0))
        specialized[n], report = BatchKernel.build_model(
            args.output / f"special{n}.so", ModelSpec(m)
        )
        save(args.output / f"special{n}_compile.json", report)
    repeats = 1 if args.phase == "audit" else args.repeats
    blocks = [
        (n, strategy, r)
        for n in args.sizes
        for strategy in ("cp", "hybrid")
        for r in range(repeats)
    ]
    rng = Random(141026)
    rng.shuffle(blocks)
    schedule = []
    for n, strategy, repeat in blocks:
        pair = ["control", "generic", "special"]
        rng.shuffle(pair)
        schedule.extend((n, strategy, v, repeat) for v in pair)
    save(args.output / "schedule.json", schedule)
    rows, signatures = [], {}
    for n, strategy, variant, repeat in schedule:
        spec = settings(n)
        started = perf_counter()
        original, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        state = (
            RankedState(model, spec["order"])
            if strategy == "cp"
            else HybridState(model, spec["order"], residual, 20, 4, 200000)
        )
        if variant == "control":
            enable_sum(state.native, sums)
            enable_alldiff(state.native, alldiff)
        else:
            state.native = BatchNative(
                model,
                ModelSpec(model),
                generic if variant == "generic" else specialized[n],
            )
            state.domains = RankedDomains(state.native.domains, model, spec["order"])
        audit = (
            record_reductions(state.native.domains) if args.phase == "audit" else None
        )
        result = search(
            state,
            Query(
                max_nodes=10000 if n <= 16 else args.large_nodes,
                time_limit_seconds=args.limit,
            ),
            policy=spec["policy"],
        )
        seconds = perf_counter() - started
        row = dict(
            size=n,
            strategy=strategy,
            variant=variant,
            repeat=repeat,
            seconds=seconds,
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
            termination=result.termination.value,
            squares=[validate(n, s.assignment, original) for s in result.solutions],
            settings=spec,
            residual_stats=dict(state.stats) if strategy == "hybrid" else {},
            batch_stats=dict(state.native.batch_totals) if variant != "control" else {},
        )
        if audit:
            row.update(
                reductions_sha256=audit[0].hexdigest(), reduction_events=audit[1][0]
            )
        assert row["termination"] != "time_limit", (
            "interrupted comparison; increase the run limit"
        )
        key = n, strategy, "control" if variant == "control" else "batch"
        if key in signatures:
            assert signatures[key] == signature(row), (
                "specialization changed search/reductions"
            )
        signatures[key] = signature(row)
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
    summary = []
    for n in args.sizes:
        for strategy in ("cp", "hybrid"):
            group = [r for r in rows if r["size"] == n and r["strategy"] == strategy]
            values = {
                v: median(r["seconds"] for r in group if r["variant"] == v)
                for v in ("control", "generic", "special")
            }
            summary.append(
                dict(
                    size=n,
                    strategy=strategy,
                    solved=all(bool(r["squares"]) for r in group),
                    **values,
                    specialization_reduction_percent=100
                    * (1 - values["special"] / values["generic"]),
                    generic_vs_control_reduction_percent=100
                    * (1 - values["generic"] / values["control"]),
                    native_nodes=next(
                        r["nodes"] for r in group if r["variant"] == "generic"
                    ),
                    control_nodes=next(
                        r["nodes"] for r in group if r["variant"] == "control"
                    ),
                    same_control_search=signature(
                        next(r for r in group if r["variant"] == "control")
                    )[:2]
                    == signature(next(r for r in group if r["variant"] == "generic"))[
                        :2
                    ],
                )
            )
    save(args.output / "summary.json", summary)
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
        for p, h in frozen["source_hashes"].items()
    ), "sources changed during run"
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
