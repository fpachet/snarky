"""Capture and replay fixpoints: Python-controlled C, generic batch, generated batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky import Atom
from snarky.finite.model import Query
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .alldiff_kernel import AllDiffKernel
from .alldiff_kernel import enable as enable_alldiff
from .magic_residual_study import freeze, settings
from .magic_search_tuning import RankedState, prepare
from .model_batch import BatchContext, BatchKernel, ModelSpec, PythonEpisode
from .sum_kernel import SumKernel
from .sum_kernel import enable as enable_sum


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def signature(answer):
    return tuple(
        answer[k]
        for k in (
            "consistent",
            "masks",
            "revisions",
            "reductions",
            "digest",
            "failure",
            "log",
        )
    )


def control(spec, sums, alldiff):
    state = enable_sum(NativeState(spec.model), sums)
    enable_alldiff(state, alldiff)
    root = state.checkpoint()

    def run(masks):
        for name, mask in zip(spec.names, masks, strict=True):
            state.domains.retain_mask(name, mask, Atom("replay"))
        started = perf_counter()
        consistent = state.propagate()
        seconds = perf_counter() - started
        result = (consistent, tuple(state.domains._masks))
        state.rollback(root)
        return seconds, result

    return run


def measure(context, packed, cycles):
    for masks in packed:
        assert context.execute(masks) >= 0
    signatures = []
    started = perf_counter()
    for _ in range(cycles):
        for masks in packed:
            status = context.execute(masks)
            assert status >= 0
            signatures.append((bool(status), *map(int, context.counts)))
    seconds = perf_counter() - started
    digest = hashlib.sha256(json.dumps(signatures).encode()).hexdigest()
    return dict(
        seconds=seconds,
        episodes=cycles * len(packed),
        work_sha256=digest,
        revisions=sum(s[1] for s in signatures),
        support_calls=sum(s[2] for s in signatures),
        cache_hits=sum(s[3] for s in signatures),
        reductions=sum(s[4] for s in signatures),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 9, 16, 20])
    parser.add_argument("--samples", type=int, default=96)
    parser.add_argument("--large-nodes", type=int, default=5000)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if (
        args.samples < 16
        or args.repeats < 1
        or args.large_nodes < 1
        or any(n < 3 for n in args.sizes)
    ):
        parser.error("invalid experiment limits")
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        extra_files=[
            Path(__file__),
            *[
                Path(__file__).with_name(p)
                for p in [
                    "model_batch.py",
                    "model_batch_runtime.c",
                    "test_model_batch.py",
                    "model_batch_sanitize.c",
                    "sum_kernel.py",
                    "sum_support.c",
                    "alldiff_kernel.py",
                    "alldiff_support.c",
                ]
            ],
        ],
    )
    generic, generic_build = BatchKernel.build_model(args.output / "generic.so")
    sums, sum_build = SumKernel.build(args.output / "sum.so")
    alldiff, all_build = AllDiffKernel.build(args.output / "alldiff.so")
    save(
        args.output / "compile.json",
        dict(generic=generic_build, sums=sum_build, alldiff=all_build),
    )
    summaries = []
    for n in args.sizes:
        folder = args.output / str(n)
        folder.mkdir()
        preset = settings(n)
        original, model = prepare(
            n,
            preset["order"],
            preset["tie"],
            preset["symmetry"],
            seed=preset.get("seed", 0),
        )
        spec = ModelSpec(model)
        started = perf_counter()
        special, special_build = BatchKernel.build_model(folder / "special.so", spec)
        special_build["generation_build_load_seconds"] = perf_counter() - started
        save(folder / "compile.json", special_build)
        state = RankedState(model, preset["order"])
        enable_sum(state.native, sums)
        enable_alldiff(state.native, alldiff)
        propagate = state.propagate
        samples = []
        seen = 0
        rng = Random(141026 + n)

        def capture(
            state=state, rng=rng, propagate=propagate, samples=samples, **kwargs
        ):
            nonlocal seen
            masks = tuple(state.native.domains._masks)
            index = seen
            seen += 1
            slot = index if index < args.samples else rng.randrange(12, index + 1)
            answer = propagate(**kwargs)
            if slot < args.samples:
                sample = dict(
                    node=index + 1,
                    masks=masks,
                    consistent=answer,
                    after=tuple(state.native.domains._masks) if answer else None,
                )
                if slot < len(samples):
                    samples[slot] = sample
                else:
                    samples.append(sample)
            return answer

        state.propagate = capture
        result = search(
            state,
            Query(
                max_nodes=5000 if n <= 16 else args.large_nodes, time_limit_seconds=60
            ),
            policy=preset["policy"],
        )
        assert result.termination.value != "time_limit"
        samples.sort(key=lambda s: s["node"])
        save(
            folder / "capture.json",
            dict(
                settings=preset,
                nodes=result.explored_nodes,
                failures=result.failed_branches,
                revisions=result.constraint_revisions,
                termination=result.termination.value,
                squares=[validate(n, s.assignment, original) for s in result.solutions],
                samples=samples,
                model_key=spec.key,
            ),
        )
        python = PythonEpisode(spec)
        ga, sa = (
            BatchContext(spec, generic, audit=True),
            BatchContext(spec, special, audit=True),
        )
        audit = []
        for sample in samples:
            masks = tuple(sample["masks"])
            expected = python.run(masks)
            g, s = ga.run(masks), sa.run(masks)
            assert g == s
            assert signature(g) == signature(expected)
            assert g["consistent"] == sample["consistent"]
            if g["consistent"]:
                assert g["masks"] == tuple(sample["after"])
            audit.append(dict(node=sample["node"], **g))
        save(folder / "audit.json", audit)
        packed = [spec.encode(s["masks"]) for s in samples]
        trial = measure(BatchContext(spec, generic), packed, 1)
        cycles = min(100, max(1, math.ceil(0.15 / trial["seconds"])))
        schedule = []
        for repeat in range(args.repeats):
            pair = ["generic", "special"]
            rng.shuffle(pair)
            schedule.extend((repeat, v) for v in pair)
        save(folder / "schedule.json", schedule)
        runs = []
        works = {}
        for repeat, variant in schedule:
            measured = measure(
                BatchContext(spec, generic if variant == "generic" else special),
                packed,
                cycles,
            )
            if repeat in works:
                assert works[repeat] == measured["work_sha256"]
            works[repeat] = measured["work_sha256"]
            runs.append(dict(repeat=repeat, variant=variant, **measured))
        save(folder / "runs.json", runs)
        controller = control(spec, sums, alldiff)
        for sample in samples:
            controller(sample["masks"])
        control_runs = []
        for _ in range(3):
            seconds = 0
            for sample in samples:
                elapsed, answer = controller(sample["masks"])
                assert answer[0] == sample["consistent"]
                if answer[0]:
                    assert answer[1] == tuple(sample["after"])
                seconds += elapsed
            control_runs.append(seconds)
        save(
            folder / "control.json",
            dict(
                seconds=control_runs,
                scope=(
                    "Sum of preloaded propagation-only intervals; input restoration, "
                    "encoding, decoding, compilation and output excluded. Controller "
                    "uses existing C kernels and original Python queue, which may "
                    "revise constraints in a different order."
                ),
            ),
        )
        times = {
            v: median(r["seconds"] / cycles for r in runs if r["variant"] == v)
            for v in ["generic", "special"]
        }
        summary = dict(
            size=n,
            samples=len(samples),
            cycles=cycles,
            generic_seconds=times["generic"],
            special_seconds=times["special"],
            specialization_reduction_percent=100
            * (1 - times["special"] / times["generic"]),
            python_control_seconds=median(control_runs),
            generic_vs_control_reduction_percent=100
            * (1 - times["generic"] / median(control_runs)),
            cold_special_compile_seconds=special_build["original_compile_seconds"],
            generation_build_load_seconds=special_build[
                "generation_build_load_seconds"
            ],
            special_binary_bytes=special_build["binary_bytes"],
            generic_binary_bytes=generic_build["binary_bytes"],
        )
        saved = times["generic"] - times["special"]
        summary["break_even_episodes"] = (
            special_build["original_compile_seconds"] / (saved / len(samples))
            if saved > 0
            else None
        )
        summaries.append(summary)
        save(args.output / "summary.json", summaries)
        print(json.dumps(summary), flush=True)
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
        for p, h in frozen["source_hashes"].items()
    )


if __name__ == "__main__":
    main()
