"""Study residual enumeration on real magic-square searches; no solver changes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import platform
import subprocess
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_search_tuning import RankedState, prepare

PRESETS = Path(__file__).with_name("magic_best_parameters.json")
THRESHOLDS = (256, 4096, 65536, 1048576, 16777216)


def freeze(output, config, extra_files=()):
    output.mkdir(parents=True, exist_ok=False)
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        PRESETS,
        Path("benchmarks/alice_magic.py"),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
        Path(__file__).with_name("magic_residual_enumeration.py"),
        Path(__file__).with_name("residual_enum.c"),
    ]
    evaluator = Path(__file__).with_name("magic_residual_evaluation.py")
    if evaluator.exists():
        files.append(evaluator)
    files.extend(Path(__file__).parent.glob("magic_residual*.py"))
    files.extend(extra_files)
    files = list(dict.fromkeys(files))
    record = dict(
        config=config,
        python=platform.python_version(),
        platform=platform.platform(),
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        source_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
        },
    )
    with tarfile.open(output / "sources.tar.gz", "w:gz") as archive:
        for p in files:
            archive.add(p, arcname=str(p).lstrip("/"))
    (output / "frozen.json").write_text(json.dumps(record, indent=2) + "\n")


def settings(size):
    preset = json.loads(PRESETS.read_text())
    return {**preset["default"], **preset["known_size_overrides"].get(str(size), {})}


def product_bound(sizes, cap=THRESHOLDS[-1]):
    if 0 in sizes:
        return 0
    product = 1
    for size in sizes:
        product *= size
        if product > cap:
            return None
    return product


class CaptureState(RankedState):
    def __init__(self, model, order, samples, max_remaining):
        super().__init__(model, order)
        self.depth = 0
        self.rows = []
        self.samples = defaultdict(list)
        self.seen = Counter()
        self.rng = Random(141026)
        self.sample_limit = samples
        self.max_remaining = max_remaining

    def propagate(self, **kwargs):
        domains = self.native.domains
        remaining = domains._unfixed_count
        product = product_bound(domains._sizes)
        selected = None
        bucket = None
        if remaining <= self.max_remaining or product is not None and product > 0:
            bucket = (
                4 * math.ceil(remaining / 4),
                4 * math.ceil(max(1, (product - 1).bit_length()) / 4)
                if product
                else 1000,
            )
            self.seen[bucket] += 1
            group = self.samples[bucket]
            slot = (
                len(group)
                if len(group) < self.sample_limit
                else self.rng.randrange(self.seen[bucket])
            )
            if slot < self.sample_limit:
                selected = (slot, tuple(domains._masks))
        started = perf_counter()
        valid = self.native.propagate(**kwargs)
        seconds = perf_counter() - started
        row = dict(
            node=len(self.rows) + 1,
            depth=self.depth,
            remaining=remaining,
            after_remaining=domains._unfixed_count,
            product=product,
            propagation_seconds=seconds,
            consistent=valid,
        )
        self.rows.append(row)
        if selected is not None:
            slot, masks = selected
            sample = dict(**row, masks=masks)
            group = self.samples[bucket]
            if slot == len(group):
                group.append(sample)
            else:
                group[slot] = sample
        return valid


def capture(args):
    freeze(args.output, vars(args) | {"output": str(args.output)})
    reports = []
    for n in args.sizes:
        spec = settings(n)
        original, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        state = CaptureState(model, spec["order"], args.samples, args.max_remaining)

        def progress(event, state=state):
            state.depth = event.depth

        started = perf_counter()
        result = search(
            state,
            Query(time_limit_seconds=args.limit),
            policy=spec["policy"],
            on_progress=progress,
        )
        seconds = perf_counter() - started
        squares = [validate(n, s.assignment, original) for s in result.solutions]
        total = sum(r["propagation_seconds"] for r in state.rows)
        thresholds = []
        for threshold in THRESHOLDS:
            group = [
                r
                for r in state.rows
                if r["product"] is not None and r["product"] <= threshold
            ]
            thresholds.append(
                dict(
                    threshold=threshold,
                    nodes=len(group),
                    propagation_seconds=sum(r["propagation_seconds"] for r in group),
                    propagation_share=sum(r["propagation_seconds"] for r in group)
                    / total,
                )
            )
        samples = [s for bucket in sorted(state.samples) for s in state.samples[bucket]]
        payload = dict(
            size=n,
            settings=spec,
            samples=samples,
            nodes=state.rows,
            domain_orders=[[v.value for v in var.domain] for var in model.variables],
            variable_names=[var.name.name for var in model.variables],
        )
        with gzip.open(args.output / f"states_{n}.json.gz", "wt") as f:
            json.dump(payload, f)
        report = dict(
            size=n,
            settings=spec,
            search_seconds_instrumented=seconds,
            propagation_seconds=total,
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
            termination=result.termination.value,
            squares=squares,
            samples=len(samples),
            thresholds=thresholds,
        )
        reports.append(report)
        print(
            json.dumps(
                {k: v for k, v in report.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
    (args.output / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 9, 13, 16, 20])
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--max-remaining", type=int, default=24)
    parser.add_argument("--limit", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture(args)


if __name__ == "__main__":
    main()
