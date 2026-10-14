"""Single-thread complete-search comparison with installed MiniZinc solvers."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import random
import re
import subprocess
import tarfile
from pathlib import Path
from time import perf_counter

from snarky import Atom
from snarky.finite.model import Query, ResultStatus
from snarky.finite.search import search

from .magic_scaling import PRESET
from .magic_search_tuning import RankedState, prepare

MINIZINC = Path("/Applications/MiniZincIDE.app/Contents/Resources/minizinc")


def model_text(size, symmetry, policy, values="indomain_min", alldiff_domain=False):
    symmetry_text = (
        """
constraint square[1,1] < square[1,n];
constraint square[1,1] < square[n,1];
constraint square[1,1] < square[n,n];
constraint square[1,n] < square[n,1];
constraint square[1,1] <= (n*n+1) div 2;
"""
        if symmetry
        else ""
    )
    consistency = " :: domain" if alldiff_domain else ""
    return f"""include "all_different.mzn";
int: n = {size};
int: m = n*(n*n+1) div 2;
array[1..n,1..n] of var 1..n*n: square;
constraint all_different(array1d(square)){consistency};
constraint forall(r in 1..n)(sum(c in 1..n)(square[r,c]) = m);
constraint forall(c in 1..n)(sum(r in 1..n)(square[r,c]) = m);
constraint sum(i in 1..n)(square[i,i]) = m;
constraint sum(i in 1..n)(square[i,n+1-i]) = m;
{symmetry_text}
solve :: int_search(array1d(square), {policy}, {values}, complete) satisfy;
output [show(array1d(square)), "\\n"];
"""


def validate_square(size, flat, symmetry):
    assert len(flat) == size * size
    assert all(type(v) is int for v in flat)
    assert sorted(flat) == list(range(1, size * size + 1))
    target = size * (size * size + 1) // 2
    rows = [flat[r * size : (r + 1) * size] for r in range(size)]
    assert all(sum(row) == target for row in rows)
    assert all(sum(row[c] for row in rows) == target for c in range(size))
    assert sum(rows[i][i] for i in range(size)) == target
    assert sum(rows[i][size - 1 - i] for i in range(size)) == target
    if symmetry:
        assert flat[0] < min(flat[size - 1], flat[-size], flat[-1])
        assert flat[size - 1] < flat[-size]
        assert flat[0] <= (size * size + 1) // 2
    return rows


def command_run(command, timeout):
    started = perf_counter()
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return result, perf_counter() - started


def external_trial(solver, base, limit, size, symmetry, seed=1, free_search=False):
    command = [str(MINIZINC.parent / "bin" / f"fzn-{solver}"), "-s"]
    command += (
        ["-p", "1", "-r", str(seed), "-time"]
        if solver == "gecode"
        else ["--rnd-seed", str(seed), "-t"]
    )
    command += [str(round(limit * 1000)), str(base.with_suffix(".fzn"))]
    if free_search and solver == "chuffed":
        command[2:2] = ["-f"]
    result, elapsed = command_run(command, limit + 15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Ignore variable selection annotation" not in result.stdout, result.stdout
    stats, squares, statuses = {}, [], []
    for line in result.stdout.splitlines():
        match = re.fullmatch(r"%%%mzn-stat: (\w+)=(.+)", line)
        if match:
            stats[match[1]] = json.loads(match[2])
        match = re.fullmatch(r"\w+ = array1d\([^,]+, (\[[^\]]*\])\);", line)
        if match:
            squares.append(validate_square(size, json.loads(match[1]), symmetry))
        if line.startswith("====="):
            statuses.append(line.strip("="))
    assert "UNSATISFIABLE" not in statuses, "blank square is feasible"
    return dict(
        command=command,
        solve_process_seconds=elapsed,
        solved=bool(squares),
        squares=squares,
        statistics=stats,
        statuses=statuses,
        termination="solution_limit" if squares else "unknown",
        stdout=result.stdout,
        stderr=result.stderr,
    )


def snarky_trial(size, spec, limit):
    gc.collect()
    started = perf_counter()
    _, model = prepare(
        size, spec["order"], spec["tie"], spec["symmetry"], seed=spec.get("seed", 0)
    )
    prepared = perf_counter()
    state = RankedState(model, spec["order"])
    remaining = limit - (perf_counter() - prepared)
    result = search(
        state, Query(time_limit_seconds=max(remaining, 1e-9)), policy=spec["policy"]
    )
    finished = perf_counter()
    assert result.status is not ResultStatus.INFEASIBLE
    squares = []
    for solution in result.solutions:
        flat = [
            solution.assignment[Atom(f"cell_{i}")].value for i in range(size * size)
        ]
        squares.append(validate_square(size, flat, spec["symmetry"]))
    return dict(
        prepare_seconds=prepared - started,
        solve_process_seconds=finished - prepared,
        total_seconds=finished - started,
        solved=bool(squares),
        squares=squares,
        termination=result.termination.value,
        statistics=dict(
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 11, 16, 20])
    parser.add_argument(
        "--tracks",
        nargs="+",
        choices=["controlled", "preset"],
        default=["controlled", "preset"],
    )
    parser.add_argument(
        "--solvers",
        nargs="+",
        choices=["snarky", "gecode", "chuffed"],
        default=["snarky", "gecode", "chuffed"],
    )
    parser.add_argument("--limit", type=float, default=10)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--external-values",
        default="indomain_min",
        choices=["indomain_min", "indomain_median", "indomain_random"],
    )
    parser.add_argument("--external-policy", choices=["first_fail", "dom_w_deg"])
    parser.add_argument("--alldiff-domain", action="store_true")
    parser.add_argument(
        "--free-search",
        action="store_true",
        help="Allow Chuffed to alternate annotated and activity search",
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.limit <= 0 or args.repeats < 1 or any(n < 3 for n in args.sizes):
        parser.error("positive budget/repeats and sizes >=3 required")
    if "chuffed" in args.solvers and (
        args.external_values == "indomain_random" or args.external_policy == "dom_w_deg"
    ):
        parser.error("installed Chuffed does not support dom_w_deg or indomain_random")
    args.output.mkdir(parents=True, exist_ok=False)
    preset = json.loads(PRESET.read_text())
    paths = sorted(
        set(
            [
                *Path("src/snarky").rglob("*.py"),
                Path(__file__),
                PRESET,
                Path("benchmarks/alice_magic.py"),
                Path("experiments/neural_attention/magic_scaling.py"),
                Path("experiments/neural_attention/magic_search_tuning.py"),
                Path("experiments/neural_attention/optimize_magic6.py"),
            ]
        )
    )
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    frozen = dict(
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        platform=platform.platform(),
        python=platform.python_version(),
        pythonhashseed=os.environ.get("PYTHONHASHSEED"),
        preset=preset,
        source_hashes=hashes,
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        versions=subprocess.check_output([str(MINIZINC), "--solvers"], text=True),
        binary_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                MINIZINC,
                *(MINIZINC.parent / "bin" / f"fzn-{s}" for s in ["gecode", "chuffed"]),
            ]
        },
        protocol="Sequential, one thread, first solution, no hints/construction. "
        "Controlled: MRV/first_fail, ascending values, row-major ties, five "
        "identical symmetry restrictions (unless external options override search). "
        "Preset: frozen Snarky size settings; Gecode dom_w_deg, Chuffed first_fail, "
        "configured value annotations, same symmetry but different branching. "
        "External compilation measured separately once per solver/case. "
        "Nominal search cutoffs exclude model preparation/compilation. Snarky "
        "charges initialization; external cutoffs are backend-specific (Chuffed "
        "adds initialization time). Actual process/init/search times retained. "
        "External process startup/output and Snarky solution "
        "explanations included. Imports and independent validation excluded. "
        "Counters are solver-specific, not directly equivalent. No speedup "
        "ratios for timeouts. Preset choices were tuned previously on these sizes.",
    )
    (args.output / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n")
    with tarfile.open(args.output / "sources.tar.gz", "w:gz") as archive:
        for path in paths:
            archive.add(path, arcname=str(path))
    rows = []
    for track in args.tracks:
        for size in args.sizes:
            spec = (
                dict(policy="mrv", order="ascending", tie="row_major", symmetry=True)
                if track == "controlled"
                else {
                    **preset["default"],
                    **preset["known_size_overrides"].get(str(size), {}),
                }
            )
            policies = {
                s: args.external_policy
                or (
                    "first_fail"
                    if track == "controlled" or s == "chuffed"
                    else "dom_w_deg"
                )
                for s in args.solvers
            }
            bases, compilation = {}, {}
            for solver in args.solvers:
                if solver == "snarky":
                    continue
                base = args.output / f"{track}_{size}_{solver}"
                external_policy = policies[solver]
                base.with_suffix(".mzn").write_text(
                    model_text(
                        size,
                        spec["symmetry"],
                        external_policy,
                        args.external_values,
                        args.alldiff_domain,
                    )
                )
                command = [
                    str(MINIZINC),
                    "--solver",
                    solver,
                    "--compile",
                    "--statistics",
                    "--output-fzn-to-file",
                    str(base.with_suffix(".fzn")),
                    "--output-ozn-to-file",
                    str(base.with_suffix(".ozn")),
                    str(base.with_suffix(".mzn")),
                ]
                compiled, elapsed = command_run(command, 30)
                assert compiled.returncode == 0, compiled.stderr
                bases[solver], compilation[solver] = base, elapsed
                base.with_suffix(".compile.json").write_text(
                    json.dumps(
                        dict(
                            command=command,
                            seconds=elapsed,
                            stdout=compiled.stdout,
                            stderr=compiled.stderr,
                        ),
                        indent=2,
                    )
                    + "\n"
                )
            for repeat in range(args.repeats):
                order = list(args.solvers)
                random.Random(size * 100 + repeat).shuffle(order)
                for solver in order:
                    print(
                        json.dumps(
                            dict(
                                event="start",
                                solver=solver,
                                track=track,
                                size=size,
                                repeat=repeat,
                            )
                        ),
                        flush=True,
                    )
                    row = dict(
                        solver=solver,
                        track=track,
                        size=size,
                        repeat=repeat,
                        limit_seconds=args.limit,
                        symmetry=spec["symmetry"],
                        settings=spec
                        if solver == "snarky"
                        else dict(
                            policy=policies[solver],
                            values=args.external_values,
                            seed=args.seed,
                            alldiff_domain=args.alldiff_domain,
                            free_search=args.free_search and solver == "chuffed",
                        ),
                        **(
                            snarky_trial(size, spec, args.limit)
                            if solver == "snarky"
                            else external_trial(
                                solver,
                                bases[solver],
                                args.limit,
                                size,
                                spec["symmetry"],
                                seed=args.seed,
                                free_search=args.free_search,
                            )
                        ),
                    )
                    if solver != "snarky":
                        row["prepare_seconds"] = compilation[solver]
                        row["total_seconds"] = (
                            compilation[solver] + row["solve_process_seconds"]
                        )
                    rows.append(row)
                    with (args.output / "runs.jsonl").open("a") as handle:
                        handle.write(json.dumps(row) + "\n")
                    (args.output / "summary.json").write_text(
                        json.dumps(
                            [
                                {
                                    k: v
                                    for k, v in r.items()
                                    if k
                                    not in ["squares", "stdout", "stderr", "command"]
                                }
                                for r in rows
                            ],
                            indent=2,
                        )
                        + "\n"
                    )
                    print(
                        json.dumps(
                            {
                                k: v
                                for k, v in row.items()
                                if k not in ["squares", "stdout", "stderr", "command"]
                            }
                        ),
                        flush=True,
                    )
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )


if __name__ == "__main__":
    main()
