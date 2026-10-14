"""Replay residual kernels and compare experimental first-solution hybrids."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky import Atom, Number
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_residual_enumeration import Compiler, Kernel
from .magic_residual_study import freeze, settings
from .magic_search_tuning import RankedState, prepare


def build(args):
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
    )
    kernel, report = Kernel.build(args.output / "enumerator.so")
    (args.output / "compile.json").write_text(json.dumps(report, indent=2) + "\n")
    return kernel


def check_witness(residual, witness):
    assert len(witness) == len(residual.domains)
    assert len(set(witness)) == len(witness)
    assert all(v in d for v, d in zip(witness, residual.domains, strict=True))
    for op, terms, target in residual.rows:
        value = sum(c * witness[i] for i, c in terms)
        assert (
            value == target
            if op == 0
            else value <= target
            if op == 1
            else value >= target
        )


def replay(args):
    kernel = build(args)
    records = []
    for path in sorted(args.capture.glob("states_*.json.gz")):
        with gzip.open(path, "rt") as f:
            capture = json.load(f)
        n, spec = capture["size"], capture["settings"]
        original, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        assert capture["domain_orders"] == [
            [v.value for v in var.domain] for var in model.variables
        ]
        compiler = Compiler(model)
        for sample in capture["samples"]:
            started = perf_counter()
            residual = compiler.extract(sample["masks"])
            extracted = perf_counter()
            run = kernel.prepare(residual)
            prepared = perf_counter()
            variants = {}
            for mode in (0, 1, 2):
                timings = []
                for _ in range(3):
                    t = perf_counter()
                    answer = run(mode, args.work_limit)
                    timings.append(perf_counter() - t)
                if answer["witness"] is not None:
                    check_witness(residual, answer["witness"])
                    assignment = {}
                    choices = dict(
                        zip(residual.indices, answer["witness"], strict=True)
                    )
                    for i, var in enumerate(model.variables):
                        value = (
                            choices[i]
                            if i in choices
                            else int(
                                var.domain[sample["masks"][i].bit_length() - 1].value
                            )
                        )
                        assignment[var.name] = Number(value)
                    validate(n, assignment, model)
                variants[str(mode)] = dict(
                    **answer,
                    kernel_seconds=median(timings),
                    total_seconds=extracted
                    - started
                    + prepared
                    - extracted
                    + median(timings),
                )
            t = perf_counter()
            cp = RankedState(model, spec["order"])
            for var, mask in zip(model.variables, sample["masks"], strict=True):
                cp.native.domains.retain_mask(var.name, mask, Atom("captured"))
            setup = perf_counter() - t
            t = perf_counter()
            result = search(cp, Query(time_limit_seconds=0.5), policy=spec["policy"])
            cp_seconds = perf_counter() - t
            solved = bool(result.solutions)
            for s in result.solutions:
                validate(n, s.assignment, original)
            if result.termination.value != "time_limit":
                for answer in variants.values():
                    if answer["status"] != 2:
                        assert bool(answer["status"]) == solved, (
                            "residual feasibility mismatch"
                        )
            if not sample["consistent"]:
                assert not solved
                assert all(v["status"] != 1 for v in variants.values())
            row = dict(
                size=n,
                node=sample["node"],
                remaining=sample["remaining"],
                residual_variables=len(residual.indices),
                invalid=residual.invalid,
                product=sample["product"],
                capture_propagation_seconds=sample["propagation_seconds"],
                extraction_seconds=extracted - started,
                encoding_seconds=prepared - extracted,
                cp_setup_seconds=setup,
                cp_fresh_search_seconds=cp_seconds,
                cp_solved=solved,
                cp_termination=result.termination.value,
                variants=variants,
            )
            records.append(row)
            with (args.output / "runs.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
    summary = []
    for mode in (0, 1, 2):
        for n in sorted({r["size"] for r in records}):
            group = [r for r in records if r["size"] == n]
            answers = [r["variants"][str(mode)] for r in group]
            summary.append(
                dict(
                    size=n,
                    mode=mode,
                    samples=len(group),
                    completed=sum(r["status"] != 2 for r in answers),
                    witnesses=sum(r["status"] == 1 for r in answers),
                    invalid_at_extraction=sum(r["invalid"] for r in group),
                    median_native_total_seconds=median(
                        r["total_seconds"] for r in answers
                    ),
                    median_original_propagation_seconds=median(
                        r["capture_propagation_seconds"] for r in group
                    ),
                    visits=sum(r["visits"] for r in answers),
                )
            )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


class HybridState(RankedState):
    """First-solution feasibility experiment only, outside the production solver."""

    def __init__(self, model, order, kernel, remaining, mode, work_limit):
        super().__init__(model, order)
        self.compiler = Compiler(model)
        self.kernel = kernel
        self.remaining = remaining
        self.mode = mode
        self.work_limit = work_limit
        self.stats = Counter()

    def propagate(self, **kwargs):
        if self.native.domains._unfixed_count <= self.remaining:
            self.stats["attempts"] += 1
            start = perf_counter()
            residual = self.compiler.extract(self.native.domains._masks)
            prepared = self.kernel.prepare(residual)
            answer = prepared(self.mode, self.work_limit)
            self.stats["enum_seconds"] += perf_counter() - start
            self.stats["visits"] += answer["visits"]
            if residual.invalid:
                self.stats["invalid_at_extraction"] += 1
            deadline = kwargs.get("deadline")
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("residual enumeration time limit")
            if answer["status"] == 0:
                # No single propagator owns this joint proof. This deliberate
                # experimental choice changes dom/wdeg's failure-weight updates.
                self.native.failure = Atom("residual_enum_failure")
                self.stats["exhausted"] += 1
                return False
            if answer["status"] == 1:
                self.stats["witnesses"] += 1
                for index, value in zip(
                    residual.indices, answer["witness"], strict=True
                ):
                    self.native.restrict(
                        self.model.variables[index].name, Number(value)
                    )
            else:
                self.stats["fallbacks"] += 1
        return self.native.propagate(**kwargs)


def hybrid(args):
    kernel = build(args)
    schedule = [
        (n, variant, repeat)
        for n in args.sizes
        for variant in ["baseline", *(f"r{k}" for k in args.remaining)]
        for repeat in range(args.repeats)
    ]
    Random(141026).shuffle(schedule)
    (args.output / "schedule.json").write_text(json.dumps(schedule))
    records = []
    for n, variant, repeat in schedule:
        spec = settings(n)
        started = perf_counter()
        original, model = prepare(
            n, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
        )
        state = (
            RankedState(model, spec["order"])
            if variant == "baseline"
            else HybridState(
                model,
                spec["order"],
                kernel,
                int(variant[1:]),
                args.mode,
                args.work_limit,
            )
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
            stats=dict(state.stats) if variant != "baseline" else {},
        )
        records.append(row)
        with (args.output / "runs.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
    summary = []
    for n in args.sizes:
        group = [r for r in records if r["size"] == n]
        variants = sorted({r["variant"] for r in group})
        summary.append(
            dict(
                size=n,
                variants={
                    v: dict(
                        median_seconds=median(
                            r["seconds"] for r in group if r["variant"] == v
                        ),
                        solved=sum(
                            bool(r["squares"]) for r in group if r["variant"] == v
                        ),
                    )
                    for v in variants
                },
            )
        )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["replay", "hybrid"])
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-limit", type=int, default=200000)
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 9, 13, 16])
    parser.add_argument("--remaining", nargs="+", type=int, default=[16, 20, 24])
    parser.add_argument("--mode", type=int, choices=[0, 1, 2, 3, 4], default=2)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=float, default=15)
    args = parser.parse_args()
    if args.work_limit < 0 or args.repeats < 1 or args.limit <= 0:
        parser.error("require nonnegative work budget, positive repeats and time limit")
    if any(n < 3 for n in args.sizes) or any(not 0 <= k <= 32 for k in args.remaining):
        parser.error("require square sizes >=3 and residual sizes in 0..32")
    if args.phase == "replay" and args.capture is None:
        parser.error("replay requires --capture")
    (replay if args.phase == "replay" else hybrid)(args)


if __name__ == "__main__":
    main()
