"""Sequential A/B of opt-in residual sum systems against the unchanged solver."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_search_tuning import RankedDomains, RankedState, prepare
from .sum_systems import SumSystemState


class SystemRankedState(RankedState):
    def __init__(self, model, order, **settings):
        self.native = SumSystemState(model, **settings)
        self.model = model
        self.domains = RankedDomains(self.native.domains, model, order)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[6, 8, 9, 11, 12, 16])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=float, default=20)
    parser.add_argument("--max-variables", type=int, default=4)
    parser.add_argument("--max-equations", type=int, default=4)
    parser.add_argument("--budget", type=int, default=128)
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=["baseline", "discovery_only", "exact"],
        default=["baseline", "discovery_only", "exact"],
    )
    parser.add_argument(
        "--presets",
        type=Path,
        default=Path(__file__).with_name("magic_best_parameters.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        args.repeats < 1
        or args.limit <= 0
        or any(n < 3 for n in args.sizes)
        or min(args.max_variables, args.max_equations) < 2
        or args.budget < 1
    ):
        parser.error("invalid size, repeat count, limit, or system budget")
    args.output.mkdir(parents=True, exist_ok=False)
    presets = json.loads(args.presets.read_text())
    sources = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        Path(__file__).with_name("sum_systems.py"),
        Path(__file__).with_name("magic_search_tuning.py"),
        Path(__file__).with_name("optimize_magic6.py"),
        Path("benchmarks/alice_magic.py"),
        args.presets,
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    schedule = [
        (size, variant, repeat)
        for size in args.sizes
        for variant in args.variants
        for repeat in range(args.repeats)
    ]
    Random(131026).shuffle(schedule)
    frozen = dict(
        python=platform.python_version(),
        source_hashes=hashes,
        schedule=schedule,
        presets=presets,
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        scope=(
            "Sequential runs, setup and structural compilation included; imports and "
            "independent validation excluded. Native and experimental revisions are "
            "recorded separately. 15 uses first 80 nodes, sizes >=17 first 30. "
            "Derived failures do not increment original dom_wdeg weights."
        ),
    )
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    for name in ("sum_systems.py", "magic_sum_system_benchmark.py"):
        (args.output / (name + ".txt")).write_bytes(
            Path(__file__).with_name(name).read_bytes()
        )
    rows, signatures = [], {}
    for size, variant, repeat in schedule:
        settings = {
            **presets["default"],
            **presets["known_size_overrides"].get(str(size), {}),
        }
        started = perf_counter()
        original, model = prepare(
            size,
            settings["order"],
            settings["tie"],
            settings["symmetry"],
            seed=settings.get("seed", 0),
        )
        if variant == "baseline":
            state = RankedState(model, settings["order"])
        else:
            state = SystemRankedState(
                model,
                settings["order"],
                max_variables=args.max_variables,
                max_equations=args.max_equations,
                budget=args.budget,
                deductions=variant == "exact",
            )
        result = search(
            state,
            Query(
                time_limit_seconds=args.limit,
                max_nodes=80 if size == 15 else 30 if size >= 17 else None,
            ),
            policy=settings["policy"],
        )
        seconds = perf_counter() - started
        squares = [validate(size, s.assignment, original) for s in result.solutions]
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
            stats={} if variant == "baseline" else state.native.stats,
        )
        signature = (
            row["nodes"],
            row["failures"],
            row["revisions"],
            row["termination"],
            squares,
        )
        key = (size, variant)
        if key in signatures:
            assert signatures[key] == signature, "non-deterministic work or time limit"
        signatures[key] = signature
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
    summary = [
        dict(
            size=size,
            variants={
                variant: dict(
                    median_seconds=median(
                        r["total_seconds"]
                        for r in rows
                        if r["size"] == size and r["variant"] == variant
                    ),
                    nodes=next(
                        r["nodes"]
                        for r in rows
                        if r["size"] == size and r["variant"] == variant
                    ),
                    stats=next(
                        r["stats"]
                        for r in rows
                        if r["size"] == size and r["variant"] == variant
                    ),
                )
                for variant in args.variants
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
