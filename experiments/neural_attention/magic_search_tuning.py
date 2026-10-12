"""MRV tie and value order experiments; exact native propagation is unchanged."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from random import Random
from time import perf_counter

from benchmarks.alice_magic import build, validate
from snarky.finite.constraints import SumConstraint
from snarky.finite.model import Query, ResultStatus
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .optimize_magic6 import ordered_model, symmetry_model


class RankedDomains:
    """Expose ranked choices to DFS only; propagation uses the original store."""

    def __init__(self, native, model, order):
        self.native = native
        self.order = order
        self.lines = {
            v.name: [
                c
                for c in model.constraints
                if isinstance(c, SumConstraint) and v.name in c.variables
            ]
            for v in model.variables
        }

    def __getattr__(self, name):
        return getattr(self.native, name)

    def values(self, variable):
        values = self.native.values(variable)
        if self.order not in ("line_average", "line_midpoints") or len(values) <= 1:
            return values
        aims = []
        for line in self.lines[variable]:
            if self.order == "line_average":
                fixed, unresolved = 0, 0
                for other in line.variables:
                    domain = self.native.values(other)
                    if len(domain) == 1:
                        fixed += domain[0].value
                    else:
                        unresolved += 1
                aims.append(Fraction(line.target - fixed, unresolved))
            else:
                other_centers = Fraction(0)
                for other in line.variables:
                    if other != variable:
                        domain = self.native.values(other)
                        other_centers += Fraction(
                            min(v.value for v in domain) + max(v.value for v in domain),
                            2,
                        )
                aims.append(line.target - other_centers)
        if not aims:
            return values
        aim = sum(aims) / len(aims)
        return tuple(sorted(values, key=lambda v: (abs(v.value - aim), v.value)))


class RankedState:
    def __init__(self, model, order):
        self.native = NativeState(model)
        self.model = model
        self.domains = RankedDomains(self.native.domains, model, order)

    def __getattr__(self, name):
        return getattr(self.native, name)


def prepare(size, order, tie, symmetry):
    original, _ = build(size)
    model = ordered_model(original, "middle", 0)
    if order == "middle_high":
        model = replace(
            model,
            variables=tuple(
                replace(
                    v,
                    domain=tuple(
                        sorted(
                            v.domain,
                            key=lambda x: (
                                abs(2 * x.value - size * size - 1),
                                -x.value,
                            ),
                        )
                    ),
                )
                for v in model.variables
            ),
        )
    if symmetry:
        model = symmetry_model(model, size)
    indices = list(range(size * size))
    if tie == "degree":
        indices.sort(
            key=lambda i: (
                -((i // size == i % size) + (i // size + i % size == size - 1))
            )
        )
    elif tie == "reverse":
        indices.reverse()
    elif tie != "row_major":
        raise ValueError(tie)
    model = replace(model, variables=tuple(model.variables[i] for i in indices))
    return original, model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=7)
    parser.add_argument("--limit", type=float, default=2)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--orders",
        nargs="+",
        default=["middle", "middle_high", "line_average", "line_midpoints"],
    )
    parser.add_argument("--ties", nargs="+", default=["row_major", "degree", "reverse"])
    parser.add_argument("--symmetry", choices=["both", "none", "only"], default="both")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    frozen = {
        "python": platform.python_version(),
        "config": {
            k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()
        },
        "source_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                *Path("src/snarky").rglob("*.py"),
                Path(__file__),
                Path("experiments/neural_attention/optimize_magic6.py"),
            ]
        },
    }
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    specs = [
        (order, tie, symmetry, repeat)
        for order in args.orders
        for tie in args.ties
        for symmetry in (
            [False, True] if args.symmetry == "both" else [args.symmetry == "only"]
        )
        for repeat in range(args.repeats)
    ]
    Random(141026).shuffle(specs)
    for order, tie, symmetry, repeat in specs:
        started = perf_counter()
        original, model = prepare(args.size, order, tie, symmetry)
        prepared = perf_counter()
        state = RankedState(model, order)
        result = search(state, Query(time_limit_seconds=args.limit), policy="mrv")
        finished = perf_counter()
        if result.status is ResultStatus.INFEASIBLE:
            raise AssertionError("blank square is feasible")
        squares = [
            validate(args.size, s.assignment, original) for s in result.solutions
        ]
        row = {
            "size": args.size,
            "order": order,
            "tie": tie,
            "symmetry": symmetry,
            "repeat": repeat,
            "seconds": finished - prepared,
            "total_seconds": finished - started,
            "solved": bool(squares),
            "status": result.status.value,
            "termination": result.termination.value,
            "nodes": result.explored_nodes,
            "revisions": result.constraint_revisions,
            "squares": squares,
        }
        with (args.output / "runs.jsonl").open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        print(json.dumps({k: v for k, v in row.items() if k != "squares"}), flush=True)


if __name__ == "__main__":
    main()
