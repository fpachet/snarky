"""Replay sampled real equality calls, with exact output checks outside timing."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import platform
import subprocess
import tarfile
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky import Atom
from snarky.finite.constraints import ConstraintOperator
from snarky.finite.model import Query
from snarky.finite.numeric import NumericColumn, NumericPlan
from snarky.finite.search import search

from .magic_scaling import PRESET
from .magic_search_tuning import RankedState, prepare


def load_method(name, path):
    loader = importlib.machinery.SourceFileLoader(
        f"snarky.finite._replay_{name}", str(path)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module.NumericPlan._equality_supports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=16)
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if min(args.stride, args.repeats) < 1 or args.size < 3:
        parser.error("positive stride/repeats and size >=3 required")
    args.output.mkdir(parents=True, exist_ok=False)
    paths = {
        name: Path(path) for name, path in json.loads(args.variants.read_text()).items()
    }
    methods = {name: load_method(name, path) for name, path in paths.items()}
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        PRESET,
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_scaling.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
        args.variants,
        *paths.values(),
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (args.output / "frozen.json").write_text(
        json.dumps(
            dict(
                config={
                    k: str(v) if isinstance(v, Path) else v
                    for k, v in vars(args).items()
                },
                source_hashes=hashes,
                python=platform.python_version(),
                platform=platform.platform(),
                git_head=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                git_status=subprocess.check_output(
                    ["git", "status", "--short"], text=True
                ),
                scope="Sample every eighth equality call by default from one solve. "
                "Fresh replay plans preserve column sharing. Sampling omits "
                "intervening cache transitions; all variants use the same sequence. "
                "Timing includes calls and result-list construction, excludes "
                "plan setup and exact result checks. "
                "These are kernel measurements, not whole-solver speedups.",
            ),
            indent=2,
        )
        + "\n"
    )
    with tarfile.open(args.output / "sources.tar.gz", "w:gz") as archive:
        for path in dict.fromkeys(files):
            archive.add(path, arcname=str(path))
    columns, plans, calls = [], [], []
    column_ids, plan_ids = {}, {}
    original_method = NumericPlan._equality_supports
    count = 0

    def record(plan, masks, target):
        nonlocal count
        result = original_method(plan, masks, target)
        count += 1
        if count % args.stride:
            return result
        if id(plan) not in plan_ids:
            indices = []
            for column in plan.columns:
                if id(column) not in column_ids:
                    column_ids[id(column)] = len(columns)
                    columns.append(column.values)
                indices.append(column_ids[id(column)])
            plan_ids[id(plan)] = len(plans)
            plans.append(indices)
        calls.append((plan_ids[id(plan)], masks, target, result))
        return result

    preset = json.loads(PRESET.read_text())
    settings = {
        **preset["default"],
        **preset["known_size_overrides"].get(str(args.size), {}),
    }
    original, model = prepare(
        args.size,
        settings["order"],
        settings["tie"],
        settings["symmetry"],
        seed=settings.get("seed", 0),
    )
    try:
        NumericPlan._equality_supports = record
        result = search(
            RankedState(model, settings["order"]),
            Query(time_limit_seconds=60),
            policy=settings["policy"],
        )
        assert result.solutions, "trace collection did not complete"
        squares = [
            validate(args.size, s.assignment, original) for s in result.solutions
        ]
    finally:
        NumericPlan._equality_supports = original_method
    dataset = dict(
        columns=columns,
        plans=plans,
        calls=calls,
        settings=settings,
        equality_calls=count,
        size=args.size,
        squares=squares,
        nodes=result.explored_nodes,
        revisions=result.constraint_revisions,
    )
    with gzip.open(args.output / "calls.json.gz", "wt") as handle:
        json.dump(dataset, handle)
    schedule = [(name, repeat) for name in methods for repeat in range(args.repeats)]
    Random(131101).shuffle(schedule)
    rows = []
    for name, repeat in schedule:
        replay_columns = [
            NumericColumn(Atom(f"c{i}"), tuple(v)) for i, v in enumerate(columns)
        ]
        replay_plans = [
            NumericPlan(tuple(replay_columns[i] for i in p), ConstraintOperator.EQUAL)
            for p in plans
        ]
        method = methods[name]
        started = perf_counter()
        outputs = [
            method(replay_plans[p], masks, target) for p, masks, target, _ in calls
        ]
        elapsed = perf_counter() - started
        assert outputs == [expected for _, _, _, expected in calls], name
        row = dict(variant=name, repeat=repeat, seconds=elapsed, calls=len(calls))
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
    (args.output / "summary.json").write_text(
        json.dumps(
            {
                name: median(r["seconds"] for r in rows if r["variant"] == name)
                for name in methods
            },
            indent=2,
        )
        + "\n"
    )
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )


if __name__ == "__main__":
    main()
