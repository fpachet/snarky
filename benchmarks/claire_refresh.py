"""Fresh CLAIRE controls, plus an explicitly separate native-global queens model."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from benchmarks.claire_support import (
    git_commit,
    git_dirty,
    resolve_claire_binary,
    resolve_claire_root,
)
from benchmarks.prune_comparison import ROOT, run
from benchmarks.redesign_comparison import snapshot


def native_queens_model(size):
    from snarky import Atom, Number
    from snarky.finite import FiniteModel, FiniteVariable
    from snarky.finite.constraints import (
        AllDifferentConstraint,
        ConstraintOperator,
        LinearSumConstraint,
    )

    if size < 1:
        raise ValueError("board size must be positive")
    rows = tuple(Atom(f"q{i}") for i in range(1, size + 1))
    up = tuple(Atom(f"up{i}") for i in range(1, size + 1))
    down = tuple(Atom(f"down{i}") for i in range(1, size + 1))
    variables = [
        FiniteVariable(v, tuple(map(Number, range(1, size + 1)))) for v in rows
    ]
    constraints = [
        AllDifferentConstraint(Atom(label), scope)
        for label, scope in (("rows", rows), ("up", up), ("down", down))
    ]
    for column, (q, u, d) in enumerate(zip(rows, up, down, strict=True), 1):
        for auxiliary, offset in ((u, column), (d, -column)):
            variables.append(
                FiniteVariable(
                    auxiliary, tuple(map(Number, range(1 + offset, size + 1 + offset)))
                )
            )
            constraints.append(
                LinearSumConstraint(
                    Atom(f"channel_{auxiliary.name}"),
                    ((1, q), (-1, auxiliary)),
                    ConstraintOperator.EQUAL,
                    -offset,
                )
            )
    return FiniteModel(
        "native_global_queens", tuple(variables), tuple(constraints)
    ), rows


def measure_native(size):
    from benchmarks.claire_n_queens import validate_solution
    from snarky.finite import Query, QueryKind
    from snarky.finite.propagation import NativeState
    from snarky.finite.search import search

    started = perf_counter()
    model, rows = native_queens_model(size)
    built = perf_counter()
    state = NativeState(model)
    prepared = perf_counter()
    result = search(state, Query(QueryKind.SOLVE), policy="mrv")
    ended = perf_counter()
    assert result.solutions
    solution = tuple(result.solutions[0].assignment[v].value for v in rows)
    validate_solution(size, solution)
    return dict(
        seconds=ended - prepared,
        preparation_seconds=prepared - built,
        construction_seconds=built - started,
        solution=solution,
        nodes=result.explored_nodes,
        failures=result.failed_branches,
        revisions=result.constraint_revisions,
        status=result.status.value,
    )


def measure(family, engine, size, binary):
    if engine == "native_global":
        return measure_native(size)
    from benchmarks import (
        claire_n_queens,
        claire_talarian_filter,
        claire_triangle_closure,
    )

    module = {
        "queens": claire_n_queens,
        "talarian": claire_talarian_filter,
        "triangles": claire_triangle_closure,
    }[family]
    result = (
        module.measure_snarky(size, 1)
        if engine == "snarky"
        else module.measure_claire(size, 1, binary)
    )
    return result["runs"][0]


def collect(args):
    args.output.mkdir(parents=True, exist_ok=False)
    claire = resolve_claire_root(args.claire_root)
    binary = resolve_claire_binary(claire)
    source_hash = snapshot(ROOT, args.output / "snarky_sources.tar.gz")
    templates = {}
    for path in sorted((ROOT / "benchmarks").glob("claire_*.cl")):
        (args.output / path.name).write_bytes(path.read_bytes())
        templates[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    record = dict(
        started_at=datetime.now(UTC).isoformat(),
        python=sys.version,
        platform=platform.platform(),
        snarky_commit=git_commit(ROOT),
        snarky_dirty=git_dirty(ROOT),
        snarky_sources_sha256=source_hash,
        claire=dict(
            root=str(claire),
            commit=git_commit(claire),
            dirty=git_dirty(claire),
            mode="bundled interpreter",
            binary=str(binary),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            templates=templates,
        ),
        protocol=dict(
            warmups=1,
            repeats=args.repeats,
            timing="internal search/inference; startup excluded; preparation separate",
            processes="fresh worker per sample, sequential alternating engine order",
            native_variant=(
                "three all-different constraints plus affine diagonal channels; "
                "MRV, ascending values, queens declared before auxiliary variables; "
                "stronger propagation than the historical singleton-rule formulation"
            ),
        ),
        cases=[],
    )
    for family, sizes in (
        ("queens", (8, 10, 12, 14)),
        ("talarian", (100, 1000)),
        ("triangles", (25, 100)),
    ):
        for size in sizes:
            engines = ["snarky", "claire"] + (
                ["native_global"] if family == "queens" else []
            )
            case = dict(family=family, size=size, samples=[])
            stable = {}
            for iteration in range(-1, args.repeats):
                solutions = {}
                for engine in engines if iteration % 2 == 0 else reversed(engines):
                    command = [
                        sys.executable,
                        "-m",
                        "benchmarks.claire_refresh",
                        "--worker",
                        family,
                        engine,
                        str(size),
                        "--binary",
                        str(binary),
                    ]
                    sample = run(command, seconds=60)
                    assert not sample["timed_out"] and sample["returncode"] == 0, sample
                    result = json.loads(sample["stdout"])
                    observation = {
                        k: v for k, v in result.items() if not k.endswith("seconds")
                    }
                    if engine in stable:
                        assert observation == stable[engine]
                    stable[engine] = observation
                    if family == "queens":
                        solutions[engine] = result["solution"]
                    sample.update(engine=engine, iteration=iteration, result=result)
                    case["samples"].append(sample)
                    print(
                        family, size, engine, iteration, result["seconds"], flush=True
                    )
                if family == "queens":
                    assert solutions["snarky"] == solutions["claire"]
            case["median_seconds"] = {
                engine: statistics.median(
                    s["result"]["seconds"]
                    for s in case["samples"]
                    if s["engine"] == engine and s["iteration"] >= 0
                )
                for engine in engines
            }
            record["cases"].append(case)
            (args.output / "results.json").write_text(
                json.dumps(record, indent=2) + "\n"
            )
    assert snapshot(ROOT) == source_hash, "Snarky sources changed"
    assert (
        hashlib.sha256(binary.read_bytes()).hexdigest()
        == record["claire"]["binary_sha256"]
    )
    assert all(
        hashlib.sha256((ROOT / "benchmarks" / name).read_bytes()).hexdigest() == sha
        for name, sha in templates.items()
    )
    record["finished_at"] = datetime.now(UTC).isoformat()
    (args.output / "results.json").write_text(json.dumps(record, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--claire-root", type=Path)
    parser.add_argument("--worker", nargs=3, metavar=("FAMILY", "ENGINE", "SIZE"))
    parser.add_argument("--binary", type=Path)
    args = parser.parse_args()
    if args.worker:
        family, engine, size = args.worker
        print(json.dumps(measure(family, engine, int(size), args.binary)))
    else:
        if args.output is None or args.repeats < 1:
            parser.error("--output and positive --repeats required")
        collect(args)


if __name__ == "__main__":
    main()
