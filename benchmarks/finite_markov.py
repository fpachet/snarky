"""Versioned synthetic Markov optimization portfolio; keeps interrupted runs.

Run sequentially after correctness checks. Timing and allocation tracing use
separate fresh states; memory records use isolated subprocesses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tracemalloc
from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from random import Random
from time import perf_counter
from typing import Any

from benchmarks.support import PROJECT_ROOT, git_commit, git_dirty
from snarky import Atom, Number, Term
from snarky.finite import MarkovCosts, Query, QueryKind, ResultStatus, markov_model
from snarky.finite.constraints import AllDifferentConstraint, TableConstraint
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

# name -> length, alphabet, order, table density, cost range, seed
CASES = {
    "short_dense": (8, 4, 1, 1.0, 8, 11),
    "medium_sparse": (16, 4, 1, 0.75, 8, 12),
    "long_sparse": (32, 4, 1, 0.75, 8, 12),
    "wide_sparse": (16, 8, 1, 0.75, 8, 13),
    "second_order": (16, 4, 2, 0.75, 8, 14),
    "large_costs": (16, 4, 1, 0.75, 100000, 12),
}
MAX_NODES = 1000


def prepare(case: str) -> tuple[MarkovCosts, NativeState]:
    length, size, order, density, cost_range, seed = CASES[case]
    rng = Random(seed)
    alphabet: tuple[Term, ...] = tuple(Number(i) for i in range(size))
    initial = {
        row: rng.randrange(cost_range) for row in product(alphabet, repeat=order)
    }
    transitions = {}
    for row in product(alphabet, repeat=order + 1):
        present = rng.random() < density
        cost = rng.randrange(cost_range)
        if present:
            transitions[row] = cost
    source = MarkovCosts(alphabet, order, initial, transitions)
    names = tuple(Atom(f"x{i}") for i in range(length))
    constraints = (
        AllDifferentConstraint(Atom("distinct_prefix"), names[:size]),
        TableConstraint(
            Atom("return_to_start"),
            (names[0], names[-1]),
            tuple((v, v) for v in alphabet),
        ),
    )
    return source, NativeState(
        markov_model(source, length, names=names, constraints=constraints)
    )


def relaxed_optimum(source: MarkovCosts, length: int) -> int | None:
    """Independent min-plus chain relaxation, dropping the nonregular constraints."""
    costs = dict(source.initial)
    for _ in range(source.order, length):
        following: dict[tuple[Term, ...], int] = {}
        for context, prefix in costs.items():
            for symbol in source.alphabet:
                edge = (*context, symbol)
                if edge in source.transitions:
                    target = edge[1:] if source.order else ()
                    score = prefix + source.transitions[edge]
                    following[target] = min(following.get(target, score), score)
        costs = following
    return min(costs.values()) if costs else None


def measure(case: str, *, memory: bool = False) -> dict[str, Any]:
    if memory:
        tracemalloc.start()
    started = perf_counter()
    source, state = prepare(case)
    prepared = perf_counter()
    preparation_peak = None
    if memory:
        _, preparation_peak = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
    result = search(state, Query(QueryKind.MINIMIZE, max_nodes=MAX_NODES))
    finished = perf_counter()
    search_peak = None
    if memory:
        _, search_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    relaxation = relaxed_optimum(source, len(state.model.variables))
    incumbent = result.incumbent
    if incumbent is not None:
        sequence = tuple(incumbent.assignment[v.name] for v in state.model.variables)
        assert sequence[0] == sequence[-1]
        assert len(set(sequence[: len(source.alphabet)])) == len(source.alphabet)
        assert source.sequence_cost(sequence) == incumbent.objective_value
        assert (
            sum(c.value for c in incumbent.contributions) == incumbent.objective_value
        )
        assert relaxation is not None and relaxation <= incumbent.objective_value
    if (
        result.objective_bound is not None
        and not result.complete
        and relaxation is not None
    ):
        assert result.objective_bound <= relaxation
    if result.status is ResultStatus.OPTIMAL:
        assert result.complete and incumbent is not None
        assert result.objective_bound == incumbent.objective_value
    return {
        "preparation_seconds": prepared - started,
        "search_seconds": finished - prepared,
        "preparation_peak_traced_bytes": preparation_peak,
        "search_peak_traced_bytes": search_peak,
        "status": result.status.value,
        "termination": result.termination.value,
        "objective": None if incumbent is None else incumbent.objective_value,
        "global_bound": result.objective_bound,
        "relaxed_chain_optimum": relaxation,
        "incumbent_values": result.incumbent_values,
        "incumbent_history": [
            {
                "value": point.value,
                "nodes": point.explored_nodes,
                "elapsed_seconds": point.elapsed_seconds,
            }
            for point in result.incumbent_history
        ],
        "time_to_first_incumbent_seconds": (
            result.incumbent_history[0].elapsed_seconds
            if result.incumbent_history
            else None
        ),
        "time_to_proof_seconds": result.elapsed_seconds if result.complete else None,
        "nodes": result.explored_nodes,
        "failures": result.failed_branches,
        "pruned": result.pruned_branches,
        "revisions": result.constraint_revisions,
    }


def source_hash() -> str:
    paths = subprocess.check_output(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "src",
            "csp_solver",
            "benchmarks/finite_markov.py",
            "pyproject.toml",
            "uv.lock",
        ],
        cwd=PROJECT_ROOT,
    )
    digest = hashlib.sha256()
    for name in sorted(set(paths.split(b"\0")) - {b""}):
        digest.update(name + b"\0")
        path = PROJECT_ROOT / name.decode()
        digest.update(path.read_bytes() if path.exists() else b"<deleted>")
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--memory-case", choices=CASES)
    args = parser.parse_args()
    if args.memory_case:
        print(json.dumps(measure(args.memory_case, memory=True)))
        return
    if args.repeat < 1 or args.output is None or args.output.exists():
        parser.error("supply a new output path and a positive repeat count")
    digest = source_hash()
    payload = {
        "suite": "finite_markov_v1",
        "schema_version": 1,
        "started_at": datetime.now(UTC).isoformat(),
        "commit": git_commit(PROJECT_ROOT),
        "dirty": git_dirty(PROJECT_ROOT),
        "source_sha256": digest,
        "python": sys.version,
        "platform": platform.platform(),
        "hash_seed": os.environ.get("PYTHONHASHSEED", "unspecified"),
        "settings": {
            "max_nodes": MAX_NODES,
            "policy": "dom_wdeg",
            "repeat": args.repeat,
            "warmups": 1,
            "cases": CASES,
        },
        "memory_method": (
            "isolated subprocess tracemalloc; search peak includes live "
            "preparation allocations; not RSS"
        ),
        "timing_scope": (
            "preparation constructs source, model, and state; search includes "
            "propagation, scoring, result and rollback; validation excluded"
        ),
        "results": {},
    }
    for case in CASES:
        print(f"Measuring {case}", file=sys.stderr, flush=True)
        measure(case)
        runs = [measure(case) for _ in range(args.repeat)]
        fields = (
            "status",
            "termination",
            "objective",
            "global_bound",
            "nodes",
            "failures",
            "pruned",
            "revisions",
            "incumbent_values",
        )
        assert all(all(run[key] == runs[0][key] for key in fields) for run in runs)
        memory = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "benchmarks.finite_markov",
                    "--memory-case",
                    case,
                ],
                cwd=PROJECT_ROOT,
                text=True,
            )
        )
        payload["results"][case] = {
            "runs": runs,
            "instrumented_memory_run": memory,
            "preparation_median_seconds": statistics.median(
                run["preparation_seconds"] for run in runs
            ),
            "search_median_seconds": statistics.median(
                run["search_seconds"] for run in runs
            ),
        }
    if source_hash() != digest:
        raise RuntimeError("sources changed during measurement")
    payload["finished_at"] = datetime.now(UTC).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(args.output)


if __name__ == "__main__":
    main()
