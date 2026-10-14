"""Bounded larger magic-square runs with the saved native 20x20 strategy."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from random import Random
from statistics import median

from .magic_native_variants import append, run, save
from .magic_residual_study import freeze
from .native_variants import VariantKernel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[21, 22])
    parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if (
        not math.isfinite(args.seconds)
        or args.seconds <= 0
        or args.repeats < 1
        or any(n < 3 for n in args.sizes)
    ):
        parser.error("require positive seconds and sizes >=3")
    folder = Path(__file__).parent
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        extra_files=[
            Path(__file__),
            *folder.glob("*.c"),
            *(
                folder / name
                for name in (
                    "magic_native_variants.py",
                    "native_variants.py",
                    "native_search.py",
                    "model_batch.py",
                    "sum_kernel.py",
                    "alldiff_kernel.py",
                    "native_best_parameters.json",
                )
            ),
        ],
    )
    kernel, compilation = VariantKernel.build_variant(
        args.output / "budget_both.so", mode="budget", delta=True, shared=True
    )
    save(args.output / "compile.json", compilation)
    run(3, "budget_both", kernel, 0, 30)
    rows = []
    schedule = [
        (size, seed, repeat)
        for size in args.sizes
        for seed in args.seeds
        for repeat in range(args.repeats)
    ]
    Random(141026).shuffle(schedule)
    save(args.output / "schedule.json", schedule)
    for size, seed, repeat in schedule:
        settings = dict(
            policy="dom_wdeg",
            order="random",
            tie="row_major",
            symmetry=False,
            seed=seed,
        )
        print(
            json.dumps(dict(starting_size=size, seed=seed, repeat=repeat)), flush=True
        )
        row = run(size, "budget_both", kernel, 0, args.seconds, settings)
        row["nodes_per_second"] = row["nodes"] / row["search_seconds"]
        row["repeat"] = repeat
        rows.append(row)
        append(args.output / "runs.jsonl", row)
    summary = []
    for size in args.sizes:
        for seed in args.seeds:
            group = [
                r for r in rows if r["size"] == size and r["settings"]["seed"] == seed
            ]
            summary.append(
                dict(
                    size=size,
                    seed=seed,
                    repeats=len(group),
                    solved=sum(bool(r["squares"]) for r in group),
                    seconds=median(r["seconds"] for r in group),
                    search_seconds=median(r["search_seconds"] for r in group),
                    nodes=[r["nodes"] for r in group],
                    terminations=[r["termination"] for r in group],
                )
            )
    save(args.output / "summary.json", summary)


if __name__ == "__main__":
    main()
