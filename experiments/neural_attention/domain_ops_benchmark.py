"""Sequential same-search benchmarks for domain-store and propagation overhead."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import platform
import sys
from functools import cache
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter
from types import ModuleType

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_search_tuning import RankedDomains, RankedState, prepare

ARCHIVE = (
    Path(__file__).resolve().parents[2]
    / "benchmarks/history/magic_domain_ops_2026-10-13"
)
NAMES = ("domains", "numeric", "alldifferent", "propagation", "mixed")
COMMON = ("model", "constraints", "kernels", "capacity", "nvalue", "scheduling_kernels")


@cache
def load_runtime(folder):
    """Load an internally coherent frozen bundle, sharing immutable model types."""
    folder = Path(folder).resolve()
    tag = hashlib.sha256(str(folder).encode()).hexdigest()[:12]
    prefix = f"snarky._domain_ops_{tag}"
    package = ModuleType(prefix)
    package.__path__ = []
    sys.modules[prefix] = package
    for name in COMMON:
        sys.modules[f"{prefix}.{name}"] = importlib.import_module(
            f"snarky.finite.{name}"
        )
    for name in NAMES:
        loader = importlib.machinery.SourceFileLoader(
            f"{prefix}.{name}", str(folder / (name + ".py.txt"))
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[loader.name] = module
        loader.exec_module(module)
        setattr(package, name, module)
    return package


def coupled_class(runtime, source):
    """Bind the same experimental filter to each bundle's NativeState base."""
    original = Path(source).read_text()
    old = "from snarky.finite.propagation import NativeState"
    new = f"from {runtime.__name__}.propagation import NativeState"
    assert original.count(old) == 1
    module = ModuleType(runtime.__name__ + ".sum_distinct")
    exec(compile(original.replace(old, new), str(source), "exec"), module.__dict__)
    return module.DistinctSumState


def canonical_removals(removals):
    return tuple((r.variable, r.values, r.cause) for r in removals)


def logical_result(result):
    """Compare every result field except elapsed clock time and record classes."""
    return (
        result.status,
        result.termination,
        result.explored_nodes,
        result.failed_branches,
        result.pruned_branches,
        result.constraint_revisions,
        result.objective_bound,
        result.incumbent_values,
        result.backend,
        result.arithmetic,
        result.diagnostic,
        tuple((r.value, r.explored_nodes) for r in result.incumbent_history),
        tuple(
            (
                dict(s.assignment),
                s.facts,
                s.objective_value,
                s.derivations,
                canonical_removals(s.reductions),
                s.contributions,
            )
            for s in result.solutions
        ),
    )


def install_audit(domains):
    """Separate instrumentation; its timings are not performance measurements."""
    audit = dict(retain_mask_calls=0, no_op_calls=0, mutation_events=0)
    original_retain = domains.retain_mask

    def counted(variable, supported, cause):
        audit["retain_mask_calls"] += 1
        changed = original_retain(variable, supported, cause)
        audit["no_op_calls"] += not changed
        return changed

    class CountEvents(list):
        def append(self, value):
            audit["mutation_events"] += 1
            super().append(value)

    domains.retain_mask = counted
    domains._removals = CountEvents(domains._removals)
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=["before", "records", "indexed", "delta", "after"],
        default=["before", "after"],
    )
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 9, 13, 16])
    parser.add_argument("--mode", choices=["native", "exact"], default="native")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=float, default=30)
    parser.add_argument("--max-nodes", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--audit", action="store_true", help="separate call-count run")
    parser.add_argument(
        "--presets",
        type=Path,
        default=Path(__file__).with_name("magic_best_parameters.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1 or args.limit <= 0 or any(n < 3 for n in args.sizes):
        parser.error("invalid repeats, time limit or size")
    args.output.mkdir(parents=True, exist_ok=False)
    sources = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        args.presets,
        Path(__file__).with_name("magic_search_tuning.py"),
        Path(__file__).with_name("optimize_magic6.py"),
        Path("benchmarks/alice_magic.py"),
    ]
    prototypes = {v: ARCHIVE / v / "sum_distinct.py.txt" for v in args.variants}
    if args.mode == "exact":
        sources.extend(prototypes.values())
    for variant in args.variants:
        sources.extend(ARCHIVE.joinpath(variant, name + ".py.txt") for name in NAMES)
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    runtimes = {v: load_runtime(ARCHIVE / v) for v in args.variants}
    classes = {
        v: (
            coupled_class(runtimes[v], prototypes[v])
            if args.mode == "exact"
            else runtimes[v].propagation.NativeState
        )
        for v in args.variants
    }
    presets = json.loads(args.presets.read_text())
    schedule = [
        (n, v, r)
        for n in args.sizes
        for v in args.variants
        for r in range(args.repeats)
    ]
    Random(131041).shuffle(schedule)
    frozen = dict(
        source_hashes=hashes,
        schedule=schedule,
        presets=presets,
        python=platform.python_version(),
        platform=platform.platform(),
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        scope=(
            "Sequential shuffled runs; model/state/setup included; imports and "
            "independent validation excluded. Prior run state is released and "
            "cyclic garbage collected outside each timed run. Identical logical "
            "results and "
            "explanations required across variants. Default node prefixes: "
            "15 first80, >=17 first30. Shared immutable model types and unchanged "
            "fallback kernels; separate domains, numeric, ALLDIFF, propagation "
            "and mixed modules per bundle."
        ),
    )
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    (args.output / "domain_ops_benchmark.py.txt").write_bytes(
        Path(__file__).read_bytes()
    )
    if args.mode == "exact":
        for variant, source in prototypes.items():
            (args.output / f"{variant}_sum_distinct.py.txt").write_bytes(
                source.read_bytes()
            )
    rows, signatures = [], {}
    for size, variant, repeat in schedule:
        settings = {
            **presets["default"],
            **presets["known_size_overrides"].get(str(size), {}),
        }
        if args.seed is not None:
            settings["seed"] = args.seed
        gc.collect()
        started = perf_counter()
        original, model = prepare(
            size,
            settings["order"],
            settings["tie"],
            settings["symmetry"],
            seed=settings.get("seed", 0),
        )
        state = RankedState.__new__(RankedState)
        kwargs = (
            dict(max_active=3, max_candidates=24, pair_fast=True, exact_three=True)
            if args.mode == "exact"
            else {}
        )
        state.native = classes[variant](model, **kwargs)
        state.model = model
        state.domains = RankedDomains(state.native.domains, model, settings["order"])
        audit = install_audit(state.native.domains) if args.audit else {}
        cap = (
            args.max_nodes
            if args.max_nodes is not None
            else 80
            if size == 15
            else 30
            if size >= 17
            else None
        )
        result = search(
            state,
            Query(time_limit_seconds=args.limit, max_nodes=cap),
            policy=settings["policy"],
        )
        seconds = perf_counter() - started
        squares = [validate(size, s.assignment, original) for s in result.solutions]
        signature = logical_result(result)
        if result.termination.value != "time_limit":
            if size in signatures:
                assert signatures[size] == signature, (
                    f"{size}: representation changed search or explanations"
                )
            signatures[size] = signature
        removals = [
            [
                (repr(r.variable), sorted(map(repr, r.values)), repr(r.cause))
                for r in s.reductions
            ]
            for s in result.solutions
        ]
        row = dict(
            size=size,
            variant=variant,
            repeat=repeat,
            mode=args.mode,
            settings=settings,
            total_seconds=seconds,
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
            termination=result.termination.value,
            squares=squares,
            reductions_sha256=hashlib.sha256(json.dumps(removals).encode()).hexdigest(),
            reduction_events=[len(s.reductions) for s in result.solutions],
            stats=state.native.stats if args.mode == "exact" else {},
            audit=audit,
        )
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {
                    k: v
                    for k, v in row.items()
                    if k not in ["squares", "settings", "stats"]
                }
            ),
            flush=True,
        )
        # Releasing a previous search's large domain alphabets belongs to that
        # run's cleanup, never to the next run's model-construction time.
        del original, model, state, result, signature, removals
    summary = [
        dict(
            size=n,
            variants={
                v: dict(
                    median_seconds=median(
                        r["total_seconds"]
                        for r in rows
                        if r["size"] == n and r["variant"] == v
                    ),
                    runs=[r for r in rows if r["size"] == n and r["variant"] == v],
                )
                for v in args.variants
            },
        )
        for n in args.sizes
    ]
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha
        for p, sha in hashes.items()
    )


if __name__ == "__main__":
    main()
