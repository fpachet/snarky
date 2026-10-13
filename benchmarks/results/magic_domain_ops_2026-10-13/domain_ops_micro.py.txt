"""Isolate removal recording, explanation reads and assignment/rollback costs."""

import argparse
import hashlib
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from snarky import Atom, Number
from snarky.finite.model import FiniteVariable

from .domain_ops_benchmark import ARCHIVE, canonical_removals, load_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    variables = tuple(
        FiniteVariable(Atom(f"x{i}"), tuple(map(Number, range(256))))
        for i in range(128)
    )
    names = tuple(v.name for v in variables)
    classes = {
        v: load_runtime(ARCHIVE / v).domains.FiniteDomains for v in ["before", "after"]
    }
    schedule = [
        (case, v, r)
        for case in ["sparse", "explained", "assign_rollback"]
        for v in classes
        for r in range(7)
    ]
    Random(131044).shuffle(schedule)
    rows = []
    expected = {}
    cause = Atom("micro")
    for case, variant, repeat in schedule:
        domains = classes[variant](variables)
        root = domains.checkpoint()
        domains.take_changed()
        observed = ()
        started = perf_counter()
        if case == "assign_rollback":
            assign = getattr(domains, "assign", None)
            for turn in range(16):
                value = Number(turn)
                for name in names:
                    if assign is not None:
                        assign(name, value, cause)
                    else:
                        domains.retain(name, {value}, cause)
                assert domains.complete and not domains.empty
                assert domains.values(names[-1]) == (value,)
                domains.take_changed()
                domains.rollback(root)
                domains.take_changed()
        else:
            for turn in range(32):
                keep = ~(1 << turn)
                for name in names:
                    domains.retain_mask(name, keep, cause)
                domains.take_changed()
                if case == "explained":
                    observed = domains.removals
            if case == "sparse":
                domains.rollback(root)
                domains.take_changed()
        seconds = perf_counter() - started
        signature = (
            dict(domains.snapshot()),
            canonical_removals(observed),
            domains.empty,
            domains.complete,
        )
        if case in expected:
            assert signature == expected[case]
        expected[case] = signature
        domains.rollback(root)
        domains.release(root)
        assert domains.snapshot() == {v.name: frozenset(v.domain) for v in variables}
        rows.append(dict(case=case, variant=variant, repeat=repeat, seconds=seconds))
    source_paths = [
        Path(__file__),
        Path(__file__).with_name("domain_ops_benchmark.py"),
        *(ARCHIVE / v / "domains.py.txt" for v in classes),
    ]
    result = dict(
        variables=128,
        alphabet=256,
        repeats=7,
        schedule=schedule,
        scope=(
            "Constructor/imports/final validation excluded. sparse:4096 removals "
            "and rollback. explained:4096 removals with history requested after "
            "each128 reductions. assign_rollback:16 rounds of128 singleton "
            "assignments, status checks, last-value check, changed-event drain "
            "and rollback. Successful explanations are compared separately in "
            "the full-solve benchmarks."
        ),
        source_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths
        },
        runs=rows,
        summary=[
            dict(
                case=case,
                medians={
                    v: median(
                        r["seconds"]
                        for r in rows
                        if r["case"] == case and r["variant"] == v
                    )
                    for v in classes
                },
            )
            for case in expected
        ],
    )
    with args.output.open("x") as output:
        output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
