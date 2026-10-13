"""Compare individual propagation kernels on identical deterministic magic searches."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.alldifferent import MaskColumn
from snarky.finite.model import Query
from snarky.finite.numeric import NumericPlan
from snarky.finite.search import search

from .magic_search_tuning import RankedState, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument(
        "--candidate", type=Path, help="optional experimental kernel source"
    )
    parser.add_argument(
        "--kernel", choices=["alldifferent", "sum"], default="alldifferent"
    )
    parser.add_argument(
        "--presets",
        type=Path,
        default=Path(__file__).with_name("magic_best_parameters.json"),
    )
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 11, 12, 13, 15, 16])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1 or any(n < 3 for n in args.sizes):
        parser.error("require positive repeats and sizes at least three")
    args.output.mkdir(parents=True, exist_ok=False)
    module_spec = importlib.util.spec_from_file_location(
        f"snarky.finite._{args.kernel}_before", args.before
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    kernel_class = NumericPlan if args.kernel == "sum" else MaskColumn
    method = "_equality_supports" if args.kernel == "sum" else "decode"
    original_method = getattr(kernel_class, method)
    optimized = original_method
    if args.candidate:
        candidate_spec = importlib.util.spec_from_file_location(
            f"snarky.finite._{args.kernel}_candidate", args.candidate
        )
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        optimized = getattr(getattr(candidate, kernel_class.__name__), method)
    implementations = dict(
        baseline=getattr(getattr(module, kernel_class.__name__), method),
        optimized=optimized,
    )
    preset = json.loads(args.presets.read_text())
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        args.before,
        args.presets,
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
    ]
    if args.candidate:
        files.append(args.candidate)
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    specs = [
        (n, variant, repeat)
        for n in args.sizes
        for variant in implementations
        for repeat in range(args.repeats)
    ]
    Random(121026).shuffle(specs)
    (args.output / "frozen.json").write_text(
        json.dumps(
            dict(
                source_hashes=hashes,
                schedule=specs,
                presets=preset,
                kernel=f"{kernel_class.__name__}.{method}",
                scope=(
                    "Sequential timing, model/state setup included, imports and "
                    "validation excluded. Only the recorded kernel method is swapped. "
                    "15x15 is the first 80 nodes; sizes >=17 are the first 30 nodes."
                ),
            ),
            indent=2,
        )
        + "\n"
    )
    rows, signatures = [], {}
    try:
        for size, variant, repeat in specs:
            settings = {
                **preset["default"],
                **preset["known_size_overrides"].get(str(size), {}),
            }
            setattr(kernel_class, method, implementations[variant])
            started = perf_counter()
            original, model = prepare(
                size,
                settings["order"],
                settings["tie"],
                settings["symmetry"],
                seed=settings.get("seed", 0),
            )
            state = RankedState(model, settings["order"])
            result = search(
                state,
                Query(
                    max_nodes=80 if size == 15 else 30 if size >= 17 else None,
                    time_limit_seconds=60,
                ),
                policy=settings["policy"],
            )
            seconds = perf_counter() - started
            squares = [validate(size, s.assignment, original) for s in result.solutions]
            signature = (
                result.explored_nodes,
                result.failed_branches,
                result.constraint_revisions,
                result.termination.value,
                squares,
            )
            if size in signatures:
                assert signatures[size] == signature, "kernel changed search work"
            signatures[size] = signature
            row = dict(
                size=size,
                variant=variant,
                repeat=repeat,
                settings=settings,
                total_seconds=seconds,
                nodes=result.explored_nodes,
                failures=result.failed_branches,
                revisions=result.constraint_revisions,
                termination=result.termination.value,
                squares=squares,
            )
            rows.append(row)
            with (args.output / "runs.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(
                json.dumps(
                    {k: v for k, v in row.items() if k not in ("squares", "settings")}
                ),
                flush=True,
            )
    finally:
        setattr(kernel_class, method, original_method)
    summary = [
        dict(
            size=size,
            medians={
                variant: median(
                    r["total_seconds"]
                    for r in rows
                    if r["size"] == size and r["variant"] == variant
                )
                for variant in implementations
            },
        )
        for size in args.sizes
    ]
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )


if __name__ == "__main__":
    main()
