"""First-solution search and safe blank-square symmetry experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import replace
from pathlib import Path
from random import Random
from time import perf_counter

from benchmarks.alice_magic import build, validate
from snarky import Atom
from snarky.finite.constraints import (
    ConstraintOperator,
    LinearSumConstraint,
)
from snarky.finite.model import FiniteVariable, Query, ResultStatus
from snarky.finite.search import solve


def ordered_model(model, order, seed):
    """Change declared value order only; keep every original candidate."""
    rng = Random(seed)
    variables = []
    for variable in model.variables:
        values = list(variable.domain)
        if order == "random":
            rng.shuffle(values)
        elif order == "middle":
            center = (min(v.value for v in values) + max(v.value for v in values)) / 2
            values.sort(key=lambda v: (abs(v.value - center), v.value))
        elif order == "ends":
            values = [
                v for pair in zip(values, reversed(values), strict=True) for v in pair
            ]
            values = list(dict.fromkeys(values))
        elif order != "ascending":
            raise ValueError(order)
        variables.append(FiniteVariable(variable.name, tuple(values)))
    return replace(model, variables=tuple(variables))


def symmetry_model(model, size):
    """Blank square only: retain a representative under D4 and complement."""
    original, _ = build(size)
    if (
        model.constraints != original.constraints
        or tuple(v.name for v in model.variables)
        != tuple(v.name for v in original.variables)
        or model.rules
        or model.objective
        or model.domains != original.domains
    ):
        raise ValueError("symmetry experiment requires a blank square")
    names = [v.name for v in model.variables]
    tl, tr, bl, br = (
        names[i] for i in (0, size - 1, size * (size - 1), size * size - 1)
    )
    pairs = [(tl, tr), (tl, bl), (tl, br), (tr, bl)]
    constraints = tuple(
        LinearSumConstraint(
            Atom(f"symmetry_{i}"), ((1, a), (-1, b)), ConstraintOperator.LESS_EQUAL, -1
        )
        for i, (a, b) in enumerate(pairs)
    ) + (
        LinearSumConstraint(
            Atom("symmetry_complement"),
            ((1, tl),),
            ConstraintOperator.LESS_EQUAL,
            (size * size + 1) // 2,
        ),
    )
    return replace(model, constraints=model.constraints + constraints)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=6)
    parser.add_argument("--limit", type=float, default=3)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--orders", nargs="+", default=["random", "middle", "ends"])
    parser.add_argument("--symmetry", choices=["both", "none", "only"], default="both")
    parser.add_argument("--policies", nargs="+", default=["mrv"])
    parser.add_argument(
        "--reference", action="store_true", help="disable numeric masks"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    config = {
        "args": {
            k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()
        },
        "python": platform.python_version(),
        "source_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [*Path("src/snarky").rglob("*.py"), Path(__file__)]
        },
    }
    (args.output / "frozen.json").write_text(json.dumps(config, indent=2) + "\n")
    specs = [
        (order, seed, symmetry, policy, repeat)
        for order in args.orders
        for seed in (args.seeds if order == "random" else [0])
        for symmetry in (
            [False, True] if args.symmetry == "both" else [args.symmetry == "only"]
        )
        for policy in args.policies
        for repeat in range(args.repeats)
    ]
    Random(12026).shuffle(specs)
    for order, seed, symmetry, policy, repeat in specs:
        started = perf_counter()
        original, _ = build(args.size)
        model = ordered_model(original, order, seed)
        if symmetry:
            model = symmetry_model(model, args.size)
        prepared = perf_counter()
        result = solve(
            model,
            Query(time_limit_seconds=args.limit),
            policy=policy,
            numeric_masks=not args.reference,
        )
        finished = perf_counter()
        if result.status is ResultStatus.INFEASIBLE:
            raise AssertionError("blank square is feasible")
        squares = [
            validate(args.size, s.assignment, original) for s in result.solutions
        ]
        row = {
            "size": args.size,
            "order": order,
            "seed": seed,
            "symmetry": symmetry,
            "policy": policy,
            "repeat": repeat,
            "preparation_seconds": prepared - started,
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
