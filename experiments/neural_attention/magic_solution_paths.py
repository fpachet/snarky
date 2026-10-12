"""Extract successful DFS decisions, keeping propagation and failed work separate."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from copy import deepcopy
from math import isqrt
from pathlib import Path
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.constraints import SumConstraint
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_search_tuning import RankedState, prepare


class PathState(RankedState):
    """Trail observations with native checkpoints; snapshot before DFS unwinds."""

    def __init__(self, model, order):
        super().__init__(model, order)
        self.path = []
        self.paths = []
        self.root_forced = []
        self.names = tuple(v.name for v in model.variables)
        self.indices = {v: int(v.name.removeprefix("cell_")) for v in self.names}
        self.lines = [c for c in model.constraints if isinstance(c, SumConstraint)]

    def checkpoint(self):
        return self.native.checkpoint(), len(self.path)

    def rollback(self, checkpoint):
        native, depth = checkpoint
        self.native.rollback(native)
        del self.path[depth:]

    def release(self, checkpoint):
        self.native.release(checkpoint[0])

    def restrict(self, variable, value):
        unresolved = [v for v in self.names if self.domains.size(v) > 1]
        minimum = min(self.domains.size(v) for v in unresolved)
        lines = []
        for line in self.lines:
            if variable in line.variables:
                remaining = sum(self.domains.size(v) > 1 for v in line.variables)
                lines.append({"line": line.name.name, "unfixed": remaining})
        self.path.append(
            {
                "step": len(self.path) + 1,
                "cell": self.indices[variable],
                "value": value.value,
                "domain_size": self.domains.size(variable),
                "value_rank": self.domains.values(variable).index(value) + 1,
                "minimum_domain_size": minimum,
                "mrv_ties": sum(self.domains.size(v) == minimum for v in unresolved),
                "first_unfixed_cell": min(self.indices[v] for v in unresolved),
                "unfixed_before": len(unresolved),
                "incident_lines": lines,
                "forced": [],
            }
        )
        self.native.restrict(variable, value)

    def propagate(self, **kwargs):
        before = {v for v in self.names if self.domains.size(v) == 1}
        valid = self.native.propagate(**kwargs)
        if valid:
            forced = [
                {"cell": self.indices[v], "value": self.domains.values(v)[0].value}
                for v in self.names
                if v not in before and self.domains.size(v) == 1
            ]
            if self.path:
                self.path[-1]["forced"] = forced
            else:
                self.root_forced = forced
        return valid

    def solution(self):
        solution = self.native.solution()
        self.paths.append(
            {
                "decisions": deepcopy(self.path),
                "root_forced": deepcopy(self.root_forced),
            }
        )
        return solution


def describe(size, path):
    decisions = path["decisions"]
    grid = [None] * (size * size)
    fixed = [None] * (size * size)
    for item in path["root_forced"]:
        fixed[item["cell"]] = 0
    for item in decisions:
        grid[item["cell"]] = item["step"]
        fixed[item["cell"]] = item["step"]
        for forced in item["forced"]:
            assert fixed[forced["cell"]] is None
            fixed[forced["cell"]] = item["step"]
    assert all(step is not None for step in fixed)
    cells = [item["cell"] for item in decisions]
    pairs = list(zip(cells, cells[1:], strict=False))
    return {
        "decisions": len(cells),
        "forced_cells": size * size - len(cells),
        "nonfirst_value_decisions": sum(d["value_rank"] > 1 for d in decisions),
        "row_major_frontier_choices": sum(
            d["cell"] == d["first_unfixed_cell"] for d in decisions
        ),
        "unique_mrv_choices": sum(d["mrv_ties"] == 1 for d in decisions),
        "same_row_transitions": sum(a // size == b // size for a, b in pairs),
        "transitions": len(pairs),
        "domain_sizes": dict(
            sorted(Counter(d["domain_size"] for d in decisions).items())
        ),
        "decision_grid": [grid[r * size : (r + 1) * size] for r in range(size)],
        "fixed_step_grid": [fixed[r * size : (r + 1) * size] for r in range(size)],
        "chain": [
            f"r{d['cell'] // size + 1}c{d['cell'] % size + 1}={d['value']}"
            for d in decisions
        ],
    }


def replay(original, model, order, path, limit):
    """Reuse only variable order, then separately test the value-informed oracle."""
    by_index = {int(v.name.name.removeprefix("cell_")): v.name for v in model.variables}
    chosen = [by_index[d["cell"]] for d in path["decisions"]]
    variable_order = tuple(
        chosen + [v.name for v in model.variables if v.name not in chosen]
    )
    outcomes = {}
    for mode in ("variable_order_only", "variable_and_solution_values"):
        state = RankedState(model, order)
        if mode == "variable_and_solution_values":
            values = {by_index[d["cell"]]: d["value"] for d in path["decisions"]}
            old_values = state.domains.values

            def ranked(variable, values=values, old_values=old_values):
                symbols = old_values(variable)
                return tuple(
                    sorted(symbols, key=lambda v: v.value != values.get(variable))
                )

            state.domains.values = ranked
        started = perf_counter()
        result = search(
            state,
            Query(time_limit_seconds=limit),
            policy="mrv",
            variable_order=variable_order,
        )
        for solution in result.solutions:
            validate(isqrt(len(original.variables)), solution.assignment, original)
        outcomes[mode] = {
            "seconds": perf_counter() - started,
            "solved": bool(result.solutions),
            "termination": result.termination.value,
            "nodes": result.explored_nodes,
            "failures": result.failed_branches,
            "revisions": result.constraint_revisions,
        }
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=float, default=10)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        Path("experiments/neural_attention/magic_search_tuning.py"),
        Path("experiments/neural_attention/optimize_magic6.py"),
    ]
    frozen = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (args.output / "frozen.json").write_text(
        json.dumps(
            {"hashes": frozen, "limit": args.limit, "repeats": args.repeats}, indent=2
        )
        + "\n"
    )
    records = []
    for size, order in ((6, "middle"), (7, "middle_high"), (8, "middle_high")):
        for repeat in range(args.repeats):
            original, model = prepare(size, order, "row_major", True)
            state = PathState(model, order)
            result = search(state, Query(time_limit_seconds=args.limit), policy="mrv")
            if not result.solutions:
                raise AssertionError(f"known solved configuration timed out: {size}")
            square = validate(size, result.solutions[0].assignment, original)
            assert len(state.paths) == 1 and not state.path
            path = state.paths[0]
            for decision in path["decisions"]:
                assert square[decision["cell"]] == decision["value"]
                assert decision["domain_size"] == decision["minimum_domain_size"]
            record = {
                "size": size,
                "order": order,
                "symmetry": True,
                "repeat": repeat,
                "nodes": result.explored_nodes,
                "failures": result.failed_branches,
                "revisions": result.constraint_revisions,
                "square": square,
                "path": path,
                "summary": describe(size, path),
            }
            records.append(record)
            print(
                json.dumps(
                    {
                        k: record[k]
                        for k in ("size", "repeat", "nodes", "failures", "summary")
                    }
                ),
                flush=True,
            )
            (args.output / "paths.json").write_text(
                json.dumps(records, indent=2) + "\n"
            )
    replay_results = []
    for record in records:
        if record["repeat"]:
            continue
        original, model = prepare(record["size"], record["order"], "row_major", True)
        outcomes = replay(original, model, record["order"], record["path"], args.limit)
        replay_results.append({"size": record["size"], **outcomes})
        print(json.dumps(replay_results[-1]), flush=True)
    (args.output / "replay.json").write_text(
        json.dumps(replay_results, indent=2) + "\n"
    )
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in frozen.items()
    )


if __name__ == "__main__":
    main()
