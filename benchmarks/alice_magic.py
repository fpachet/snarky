"""ALICE-inspired redundant linear deductions for normal magic squares.

No engine changes: compare the original native model with one-round overlapping
sum differences and exact Gaussian elimination. Originals are always retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from time import perf_counter

from snarky import Atom, Number
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.model import FiniteModel, FiniteVariable, Query
from snarky.finite.propagation import NativeState
from snarky.finite.search import solve

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("baseline", "pair_differences", "elimination")


def build(size):
    names = tuple(Atom(f"cell_{i}") for i in range(size * size))
    variables = tuple(
        FiniteVariable(v, tuple(Number(i) for i in range(1, size * size + 1)))
        for v in names
    )
    lines = [
        *(tuple(r * size + c for c in range(size)) for r in range(size)),
        *(tuple(r * size + c for r in range(size)) for c in range(size)),
        tuple(i * size + i for i in range(size)),
        tuple(i * size + size - 1 - i for i in range(size)),
    ]
    target = size * (size * size + 1) // 2
    rows = [
        tuple(int(i in line) for i in range(size * size)) + (target,) for line in lines
    ]
    constraints = (AllDifferentConstraint(Atom("distinct"), names),) + tuple(
        SumConstraint(Atom(f"line_{i}"), tuple(names[j] for j in line), target)
        for i, line in enumerate(lines)
    )
    return FiniteModel(f"magic_{size}", variables, constraints), rows


def normalize(row, proof):
    denominator = math.lcm(*(x.denominator for x in row))
    integers = tuple(int(x * denominator) for x in row)
    divisor = math.gcd(*integers)
    if not divisor:
        return None
    sign = 1 if next(x for x in integers if x) > 0 else -1
    scale = Fraction(sign * denominator, divisor)
    return tuple(sign * x // divisor for x in integers), tuple(x * scale for x in proof)


def derive(original, variant):
    rows = [list(map(Fraction, row)) for row in original]
    proofs = [[Fraction(i == j) for j in range(len(rows))] for i in range(len(rows))]
    candidates = []
    if variant == "pair_differences":
        for i, j in combinations(range(len(rows)), 2):
            if not any(
                a and b for a, b in zip(rows[i][:-1], rows[j][:-1], strict=True)
            ):
                continue
            candidates.append(
                (
                    [a - b for a, b in zip(rows[i], rows[j], strict=True)],
                    [a - b for a, b in zip(proofs[i], proofs[j], strict=True)],
                )
            )
    elif variant == "elimination":
        pivot = 0
        for column in range(len(rows[0]) - 1):
            selected = next(
                (i for i in range(pivot, len(rows)) if rows[i][column]), None
            )
            if selected is None:
                continue
            rows[pivot], rows[selected] = rows[selected], rows[pivot]
            proofs[pivot], proofs[selected] = proofs[selected], proofs[pivot]
            scale = rows[pivot][column]
            rows[pivot] = [x / scale for x in rows[pivot]]
            proofs[pivot] = [x / scale for x in proofs[pivot]]
            for i in range(len(rows)):
                if i == pivot or not rows[i][column]:
                    continue
                scale = rows[i][column]
                rows[i] = [
                    a - scale * b for a, b in zip(rows[i], rows[pivot], strict=True)
                ]
                proofs[i] = [
                    a - scale * b for a, b in zip(proofs[i], proofs[pivot], strict=True)
                ]
            pivot += 1
        candidates = list(zip(rows, proofs, strict=True))
    elif variant != "baseline":
        raise ValueError(variant)
    seen = set(original)
    result = []
    for row, proof in candidates:
        normalized = normalize(row, proof)
        if normalized is None:
            continue
        row, proof = normalized
        if row in seen:
            continue
        assert any(row[:-1]), "inconsistent input equations"
        # Exact certificate: every added equation is a rational combination of
        # original equations, including the right-hand side.
        assert all(
            sum(p * source[j] for p, source in zip(proof, original, strict=True))
            == value
            for j, value in enumerate(row)
        )
        seen.add(row)
        result.append((row, proof))
    return result


def prepare(size, variant):
    model, rows = build(size)
    deductions = derive(rows, variant)
    names = tuple(v.name for v in model.variables)
    extra = tuple(
        LinearSumConstraint(
            Atom(f"derived_{i}"),
            tuple((c, v) for c, v in zip(row[:-1], names, strict=True) if c),
            ConstraintOperator.EQUAL,
            row[-1],
        )
        for i, (row, _) in enumerate(deductions)
    )
    return FiniteModel(
        model.name, model.variables, model.constraints + extra
    ), deductions


def validate(size, assignment, model):
    values = [int(assignment[v.name].value) for v in model.variables]
    assert sorted(values) == list(range(1, size * size + 1))
    target = size * (size * size + 1) // 2
    assert all(sum(values[r * size : (r + 1) * size]) == target for r in range(size))
    assert all(
        sum(values[r * size + c] for r in range(size)) == target for c in range(size)
    )
    assert sum(values[i * size + i] for i in range(size)) == target
    assert sum(values[i * size + size - 1 - i] for i in range(size)) == target
    return values


def trial(size, variant, policy, limit, iteration):
    started = perf_counter()
    model, _ = prepare(size, variant)
    prepared = perf_counter()
    result = solve(model, Query(time_limit_seconds=limit), policy=policy)
    finished = perf_counter()
    squares = [validate(size, s.assignment, model) for s in result.solutions]
    return dict(
        iteration=iteration,
        variant=variant,
        policy=policy,
        prepare_seconds=prepared - started,
        solve_seconds=finished - prepared,
        total_seconds=finished - started,
        status=result.status.value,
        termination=result.termination.value,
        nodes=result.explored_nodes,
        failures=result.failed_branches,
        revisions=result.constraint_revisions,
        squares=squares,
    )


def collect(args):
    output = dict(
        started_at=datetime.now(UTC).isoformat(),
        command=sys.argv,
        python=sys.version,
        python_hash_seed=os.environ.get("PYTHONHASHSEED", "random"),
        platform=platform.platform(),
        commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        git_status=subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ),
        source_hashes={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "src/snarky").rglob("*.py"))
        },
        benchmark_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol=dict(
            repeats=args.repeats,
            warmups=args.warmups,
            solve_time_limit_seconds=args.limit,
            policies=args.policies,
            timing=(
                "model construction + deductions/certificates + solver; "
                "solution validation excluded"
            ),
            workload="first solution, blank normal magic square, no symmetry breaking",
            order="variants rotated each round; warmups precede measured rounds",
            caveat=(
                "dom_wdeg degree and failure weights change with extra "
                "constraints; MRV control included"
            ),
        ),
        cases=[],
    )
    for size in args.sizes:
        case = dict(size=size, variants={}, samples=[])
        for variant in VARIANTS:
            model, deductions = prepare(size, variant)
            state = NativeState(model)
            assert state.propagate()
            case["variants"][variant] = dict(
                constraints=len(model.constraints),
                derived=len(deductions),
                root_domain_values=sum(
                    len(state.domains.values(v.name)) for v in model.variables
                ),
                deductions=[
                    dict(
                        coefficients=row[:-1],
                        target=row[-1],
                        source_multipliers=list(map(str, proof)),
                    )
                    for row, proof in deductions
                ],
            )
        for iteration in range(-args.warmups, args.repeats):
            offset = iteration % len(VARIANTS)
            for policy in args.policies:
                for variant in VARIANTS[offset:] + VARIANTS[:offset]:
                    sample = trial(size, variant, policy, args.limit, iteration)
                    case["samples"].append(sample)
                    print(
                        size,
                        iteration,
                        policy,
                        variant,
                        sample["termination"],
                        sample["nodes"],
                        round(sample["total_seconds"], 4),
                        flush=True,
                    )
        case["summary"] = {}
        for policy in args.policies:
            for variant in VARIANTS:
                samples = [
                    s
                    for s in case["samples"]
                    if s["iteration"] >= 0
                    and s["policy"] == policy
                    and s["variant"] == variant
                ]
                case["summary"][f"{policy}/{variant}"] = dict(
                    completed=sum(bool(s["squares"]) for s in samples),
                    medians={
                        key: statistics.median(s[key] for s in samples)
                        for key in (
                            "prepare_seconds",
                            "solve_seconds",
                            "total_seconds",
                            "nodes",
                            "failures",
                            "revisions",
                        )
                    },
                )
        output["cases"].append(case)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2) + "\n")
    output["finished_at"] = datetime.now(UTC).isoformat()
    args.output.write_text(json.dumps(output, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[4, 5])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--limit", type=float, default=10)
    parser.add_argument(
        "--policies",
        nargs="+",
        choices=["dom_wdeg", "mrv"],
        default=["dom_wdeg", "mrv"],
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or args.limit <= 0 or min(args.sizes) < 3:
        parser.error("require repeats >= 1, warmups >= 0, limit > 0 and sizes >= 3")
    collect(args)


if __name__ == "__main__":
    main()
