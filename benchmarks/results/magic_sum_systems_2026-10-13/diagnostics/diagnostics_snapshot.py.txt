"""Favorable constructed systems and clued-square checks for residual discovery."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import build, validate
from snarky import Atom, Number
from snarky.finite.constraints import SumConstraint
from snarky.finite.model import FiniteModel, FiniteVariable, Query
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .sum_systems import SumSystemState


def triangle(scale):
    variables = tuple(
        FiniteVariable(Atom(v), tuple(map(Number, range(20 * scale + 1))))
        for v in "xyz"
    )
    x, y, z = (v.name for v in variables)
    return FiniteModel(
        "constructed_triangle",
        variables,
        (
            SumConstraint(Atom("xy"), (x, y), 10 * scale),
            SumConstraint(Atom("xz"), (x, z), 12 * scale),
            SumConstraint(Atom("yz"), (y, z), 14 * scale),
        ),
    )


def run(model, variant, *, max_size=4):
    started = perf_counter()
    state = (
        NativeState(model)
        if variant == "baseline"
        else SumSystemState(
            model, max_variables=max_size, max_equations=max_size, budget=2048
        )
    )
    result = search(state, Query(time_limit_seconds=10), policy="mrv")
    seconds = perf_counter() - started
    row = dict(
        variant=variant,
        seconds=seconds,
        nodes=result.explored_nodes,
        failures=result.failed_branches,
        termination=result.termination.value,
        assignments=[
            {v.name.name: s.assignment[v.name].value for v in model.variables}
            for s in result.solutions
        ],
        stats={} if variant == "baseline" else state.stats,
    )
    return row, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    files = [Path(__file__), Path(__file__).with_name("sum_systems.py")]
    evidence = dict(
        source_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
        },
        scope=(
            "Separate diagnostics, not magic timing samples. Triangle instances are "
            "deliberately favorable, with ascending choices. Clued 4x4 instances use "
            "a known valid board only to choose clues, never to guide deductions."
        ),
        triangles=[],
        clued_magic=[],
    )
    for scale in (1, 10, 100):
        model = triangle(scale)
        schedule = [(v, r) for v in ("baseline", "exact") for r in range(3)]
        Random(scale).shuffle(schedule)
        rows = []
        for variant, repeat in schedule:
            row, result = run(model, variant)
            row["repeat"] = repeat
            assert len(result.solutions) == 1
            assert [
                result.solutions[0].assignment[v.name].value for v in model.variables
            ] == [4 * scale, 6 * scale, 8 * scale]
            rows.append(row)
        evidence["triangles"].append(
            dict(
                scale=scale,
                runs=rows,
                medians={
                    v: median(r["seconds"] for r in rows if r["variant"] == v)
                    for v in ("baseline", "exact")
                },
            )
        )
    original, _ = build(4)
    reference = [16, 2, 3, 13, 5, 11, 10, 8, 9, 7, 6, 12, 4, 14, 15, 1]
    validate(
        4,
        {v.name: Number(x) for v, x in zip(original.variables, reference, strict=True)},
        original,
    )
    rng = Random(131030)
    # Include a 2x2 cycle with both diagonals, then deterministic random clue masks.
    masks = [{0, 3, 12, 15}] + [
        set(rng.sample(range(16), unresolved))
        for unresolved in (4, 6, 8, 10, 12)
        for _ in range(8)
    ]
    for mask in masks:
        model = replace(
            original,
            variables=tuple(
                v if i in mask else replace(v, domain=(Number(reference[i]),))
                for i, v in enumerate(original.variables)
            ),
        )
        rows = []
        for variant in ("baseline", "exact"):
            row, result = run(model, variant, max_size=8)
            assert len(result.solutions) == 1
            for solution in result.solutions:
                validate(4, solution.assignment, original)
                assert all(
                    solution.assignment[original.variables[i].name].value
                    == reference[i]
                    for i in range(16)
                    if i not in mask
                )
            rows.append(row)
        evidence["clued_magic"].append(dict(unresolved=sorted(mask), runs=rows))
    (args.output / "diagnostics.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (args.output / "diagnostics_snapshot.py.txt").write_bytes(
        Path(__file__).read_bytes()
    )
    print(
        json.dumps(
            dict(
                triangles=[
                    dict(scale=t["scale"], medians=t["medians"])
                    for t in evidence["triangles"]
                ],
                clued_magic_cases=len(masks),
                clued_assignments=sum(
                    c["runs"][1]["stats"]["assignments"]
                    for c in evidence["clued_magic"]
                ),
                clued_contradictions=sum(
                    c["runs"][1]["stats"]["contradictions"]
                    for c in evidence["clued_magic"]
                ),
            )
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
