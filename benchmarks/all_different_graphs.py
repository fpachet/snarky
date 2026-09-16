"""Separate kernel-only measurements of dense and sparse alternating graphs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from benchmarks.claire_support import git_commit, git_dirty
from benchmarks.prune_comparison import ROOT
from benchmarks.redesign_comparison import snapshot
from snarky import Atom, Number
from snarky.finite import kernels
from snarky.finite.constraints import AllDifferentConstraint


def graph_case(shape, size):
    names = tuple(Atom(f"x{i:04}") for i in range(size))
    values = tuple(map(Number, range(size * (2 if shape == "free" else 1))))
    if shape == "chain":
        domains = {
            v: {values[i], values[i + 1 if i < size - 1 else i - 1]}
            for i, v in enumerate(names)
        }
        expected = {
            v: {values[i]} if i < size - 2 else set(values[-2:])
            for i, v in enumerate(names)
        }
    else:
        domains = {v: set(values) for v in names}
        expected = domains
    return names, domains, expected, dict(zip(names, values[:size], strict=True))


def collect(output, repeats):
    output.mkdir(parents=True, exist_ok=False)
    source_hash = snapshot(ROOT, output / "sources.tar.gz")
    cap, sparse_after = (
        kernels._ALL_DIFFERENT_BIT_VALUES,
        kernels._ALL_DIFFERENT_SPARSE_AFTER,
    )
    result = dict(
        started_at=datetime.now(UTC).isoformat(),
        python=platform.python_version(),
        platform=platform.platform(),
        commit=git_commit(ROOT),
        dirty=git_dirty(ROOT),
        source_hash=source_hash,
        protocol=dict(
            repeats=repeats,
            warmups=1,
            timing="kernel revision only; copies and validation excluded",
            matching="valid identity hint supplied to every strategy",
            strategies="same source: adaptive defaults, forced sparse, forced bits",
            purpose="algorithm-selection stress check; not a solver comparison",
        ),
        cases=[],
    )
    try:
        for shape, size in (
            ("dense", 50),
            ("dense", 150),
            ("free", 150),
            ("chain", 100),
            ("chain", 300),
            ("chain", 600),
        ):
            names, original, expected, hint = graph_case(shape, size)
            constraint = AllDifferentConstraint(Atom("distinct"), names)
            samples = []
            modes = ("adaptive", "sparse", "bits")
            for iteration in range(-1, repeats):
                for mode in modes if iteration % 2 == 0 else reversed(modes):
                    kernels._ALL_DIFFERENT_BIT_VALUES = 0 if mode == "sparse" else cap
                    kernels._ALL_DIFFERENT_SPARSE_AFTER = (
                        cap if mode == "bits" else sparse_after
                    )
                    domains = {v: set(d) for v, d in original.items()}
                    started = perf_counter()
                    valid, matching = kernels._revise_all_different_with_matching(
                        constraint, domains, hint
                    )
                    elapsed = perf_counter() - started
                    assert valid and domains == expected
                    assert len(set(matching.values())) == size
                    samples.append(
                        dict(strategy=mode, iteration=iteration, seconds=elapsed)
                    )
            result["cases"].append(
                dict(
                    shape=shape,
                    size=size,
                    samples=samples,
                    support_sha256=hashlib.sha256(
                        repr(
                            sorted(
                                (repr(v), sorted(map(repr, d)))
                                for v, d in expected.items()
                            )
                        ).encode()
                    ).hexdigest(),
                    medians={
                        mode: statistics.median(
                            s["seconds"]
                            for s in samples
                            if s["strategy"] == mode and s["iteration"] >= 0
                        )
                        for mode in modes
                    },
                )
            )
    finally:
        kernels._ALL_DIFFERENT_BIT_VALUES = cap
        kernels._ALL_DIFFERENT_SPARSE_AFTER = sparse_after
    assert snapshot(ROOT) == source_hash
    result["finished_at"] = datetime.now(UTC).isoformat()
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("positive repeats required")
    collect(args.output, args.repeats)


if __name__ == "__main__":
    main()
