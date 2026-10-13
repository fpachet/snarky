"""Offline exact rank/forced-value diagnostics of whole residual sum systems."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from math import gcd
from pathlib import Path
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky import Number
from snarky.finite.constraints import (
    ConstraintOperator,
    LinearSumConstraint,
    SumConstraint,
)
from snarky.finite.model import Query
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

from .magic_search_tuning import RankedDomains, RankedState, prepare
from .sum_systems import Equation, bits


def extract(model):
    positions = {v.name: i for i, v in enumerate(model.variables)}
    integers = {
        v.name
        for v in model.variables
        if all(isinstance(x, Number) and type(x.value) is int for x in v.domain)
    }
    equations = []
    for c in model.constraints:
        if isinstance(c, SumConstraint):
            terms = tuple((1, v) for v in c.variables)
        elif (
            isinstance(c, LinearSumConstraint)
            and c.operator is ConstraintOperator.EQUAL
        ):
            terms = c.terms
        else:
            continue
        if type(c.target) is not int or any(v not in integers for _, v in terms):
            continue
        terms = tuple((coefficient, positions[v]) for coefficient, v in terms)
        equations.append(Equation(terms, c.target, sum(1 << v for _, v in terms)))
    return tuple(equations)


def combine(left, left_scale, right, right_scale):
    result = {k: left_scale * v for k, v in left.items()}
    for k, value in right.items():
        updated = result.get(k, 0) - right_scale * value
        if updated:
            result[k] = updated
        else:
            result.pop(k, None)
    return result


def eliminate(equations, unresolved):
    """Sparse integer Gauss-Jordan; keep exact integer row-combination proofs.

    Pivots are not normalized to one. Common factors are removed only when they
    divide both the coefficient row and its proof, preserving an integer proof.
    No floating point or probabilistic rank estimate is used.
    """
    rows = [{v: c for c, v in e.terms if unresolved & (1 << v)} for e in equations]
    proofs = [{i: 1} for i in range(len(equations))]
    rank = 0
    for column in bits(unresolved):
        candidates = [i for i in range(rank, len(rows)) if column in rows[i]]
        if not candidates:
            continue
        pivot = min(candidates, key=lambda i: (len(rows[i]), i))
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        proofs[rank], proofs[pivot] = proofs[pivot], proofs[rank]
        b = rows[rank][column]
        for i in range(len(rows)):
            if i == rank or column not in rows[i]:
                continue
            a = rows[i][column]
            common = gcd(a, b)
            left_scale, right_scale = b // common, a // common
            rows[i] = combine(rows[i], left_scale, rows[rank], right_scale)
            proofs[i] = combine(proofs[i], left_scale, proofs[rank], right_scale)
            divisor = gcd(*rows[i].values(), *proofs[i].values())
            if divisor > 1:
                rows[i] = {k: v // divisor for k, v in rows[i].items()}
                proofs[i] = {k: v // divisor for k, v in proofs[i].items()}
        rank += 1
    return rows, proofs, rank


def assess(equations, alphabets, masks, plan=None):
    unresolved = sum(1 << v for v, mask in enumerate(masks) if mask.bit_count() > 1)
    rows, proofs, rank = plan if plan is not None else eliminate(equations, unresolved)
    fixed = {
        v: alphabets[v][mask.bit_length() - 1].value
        for v, mask in enumerate(masks)
        if mask.bit_count() == 1
        and isinstance(alphabets[v][mask.bit_length() - 1], Number)
    }
    targets = [
        e.target - sum(c * fixed[v] for c, v in e.terms if v in fixed)
        for e in equations
    ]
    direct_variables = {
        (e.scope & unresolved).bit_length() - 1
        for e in equations
        if (e.scope & unresolved).bit_count() == 1
    }
    forced, inconsistent = [], False
    for row, proof in zip(rows, proofs, strict=True):
        rhs = sum(c * targets[i] for i, c in proof.items())
        if not row:
            if rhs:
                inconsistent = True
            else:
                continue
        elif len(row) == 1:
            v, coefficient = next(iter(row.items()))
            value = Fraction(rhs, coefficient)
            domain = {alphabets[v][i].value for i in bits(masks[v])}
            forced.append(
                dict(
                    variable=v,
                    value=str(value),
                    integral=value.denominator == 1,
                    in_domain=value in domain,
                    direct=v in direct_variables,
                    proof={str(i): c for i, c in proof.items()},
                )
            )
        else:
            continue
        # Verify every useful or inconsistent row against all original residual
        # coefficients, including columns that should cancel to zero.
        rebuilt = defaultdict(int)
        for i, multiplier in proof.items():
            for c, v in equations[i].terms:
                if unresolved & (1 << v):
                    rebuilt[v] += multiplier * c
        assert {v: c for v, c in rebuilt.items() if c} == row
    count = unresolved.bit_count()
    return dict(
        unresolved=count,
        equations=len(equations),
        rank=rank,
        freedom=count - rank,
        fully_determined=count > 0 and rank == count,
        rational_inconsistent=inconsistent,
        forced=forced,
        integer_contradiction=any(
            not f["integral"] or not f["in_domain"] for f in forced
        ),
    )


class CaptureNative(NativeState):
    def __init__(self, model):
        super().__init__(model)
        self.observations = []
        self.calls = 0

    def propagate(self, **kwargs):
        self.calls += 1
        before = dict(
            node=self.calls,
            phase="before",
            masks=tuple(self.domains.mask(v.name) for v in self.model.variables),
        )
        self.observations.append(before)
        result = super().propagate(**kwargs)
        before["native_consistent"] = result
        if result:
            self.observations.append(
                dict(
                    node=self.calls,
                    phase="after",
                    native_consistent=True,
                    masks=tuple(
                        self.domains.mask(v.name) for v in self.model.variables
                    ),
                )
            )
        return result


class CaptureRanked(RankedState):
    def __init__(self, model, order):
        self.native = CaptureNative(model)
        self.model = model
        self.domains = RankedDomains(self.native.domains, model, order)


def summarize(records):
    live = [r for r in records if r["unresolved"]]
    return dict(
        observations=len(records),
        nonterminal=len(live),
        fully_determined=sum(r["fully_determined"] for r in live),
        partial_forced_states=sum(
            bool(r["forced"])
            and not r["fully_determined"]
            and not r["rational_inconsistent"]
            for r in live
        ),
        forced_values=sum(len(r["forced"]) for r in live),
        combined_forced_states=sum(
            any(not f["direct"] for f in r["forced"]) and not r["rational_inconsistent"]
            for r in live
        ),
        rational_contradictions=sum(r["rational_inconsistent"] for r in live),
        integer_contradictions=sum(r["integer_contradiction"] for r in live),
        minimum_freedom=min((r["freedom"] for r in live), default=None),
        maximum_closed_size=max(
            (r["unresolved"] for r in live if r["fully_determined"]), default=0
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 9, 12, 16])
    parser.add_argument("--limit", type=float, default=60)
    parser.add_argument(
        "--presets",
        type=Path,
        default=Path(__file__).with_name("magic_best_parameters.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(n < 3 for n in args.sizes) or args.limit <= 0:
        parser.error("require sizes >=3 and positive search limit")
    args.output.mkdir(parents=True, exist_ok=False)
    presets = json.loads(args.presets.read_text())
    files = [
        *Path("src/snarky").rglob("*.py"),
        Path(__file__),
        Path(__file__).with_name("sum_systems.py"),
        Path(__file__).with_name("magic_search_tuning.py"),
        Path(__file__).with_name("optimize_magic6.py"),
        Path("benchmarks/alice_magic.py"),
        args.presets,
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (args.output / "frozen.json").write_text(
        json.dumps(
            dict(
                source_hashes=hashes,
                presets=presets,
                config={
                    k: str(v) if isinstance(v, Path) else v
                    for k, v in vars(args).items()
                },
                scope=(
                    "Every search node before native propagation, and every "
                    "successful native fixpoint, including off-solution branches. "
                    "Exact offline analysis; no deductions applied. "
                    "15: first 80 nodes; >=17: first 30 nodes."
                ),
            ),
            indent=2,
        )
        + "\n"
    )
    (args.output / "analyzer_snapshot.py.txt").write_bytes(Path(__file__).read_bytes())
    summaries = []
    for size in args.sizes:
        settings = {
            **presets["default"],
            **presets["known_size_overrides"].get(str(size), {}),
        }
        original, model = prepare(
            size,
            settings["order"],
            settings["tie"],
            settings["symmetry"],
            seed=settings.get("seed", 0),
        )
        query = Query(
            time_limit_seconds=args.limit,
            max_nodes=80 if size == 15 else 30 if size >= 17 else None,
        )
        signatures, squares = [], None
        for state_class in (RankedState, CaptureRanked):
            state = state_class(model, settings["order"])
            result = search(state, query, policy=settings["policy"])
            squares = [validate(size, s.assignment, original) for s in result.solutions]
            signatures.append(
                (
                    result.explored_nodes,
                    result.failed_branches,
                    result.constraint_revisions,
                    result.termination.value,
                    squares,
                )
            )
        assert signatures[0] == signatures[1], "instrumentation changed search"
        equations = extract(model)
        alphabets = tuple(v.domain for v in model.variables)
        groups = defaultdict(list)
        for observation in state.native.observations:
            unresolved = sum(
                1 << v
                for v, mask in enumerate(observation["masks"])
                if mask.bit_count() > 1
            )
            groups[unresolved].append(observation)
        print(
            json.dumps(
                dict(
                    size=size,
                    phase="captured",
                    observations=len(state.native.observations),
                    topologies=len(groups),
                )
            ),
            flush=True,
        )
        started = perf_counter()
        records = []
        for index, (unresolved, observations) in enumerate(groups.items()):
            plan = eliminate(equations, unresolved)
            for observation in observations:
                record = assess(equations, alphabets, observation["masks"], plan)
                records.append(
                    dict(
                        node=observation["node"],
                        phase=observation["phase"],
                        native_consistent=observation["native_consistent"],
                        **record,
                    )
                )
            if index and index % 100 == 0:
                print(
                    json.dumps(
                        dict(size=size, phase="analysis", topologies_done=index)
                    ),
                    flush=True,
                )
        records.sort(key=lambda r: (r["node"], r["phase"] == "after"))
        summary = dict(
            size=size,
            settings=settings,
            nodes=result.explored_nodes,
            failures=result.failed_branches,
            revisions=result.constraint_revisions,
            termination=result.termination.value,
            squares=squares,
            distinct_topologies=len(groups),
            analysis_seconds=perf_counter() - started,
            phases={
                phase: summarize([r for r in records if r["phase"] == phase])
                for phase in ("before", "after")
            },
        )
        summaries.append(summary)
        payload = dict(
            summary=summary,
            variables=[v.name.name for v in model.variables],
            equations=[dict(terms=e.terms, target=e.target) for e in equations],
            observations=state.native.observations,
            analysis=records,
        )
        (args.output / f"magic{size}.json").write_text(json.dumps(payload) + "\n")
        print(
            json.dumps(
                {k: v for k, v in summary.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
        (args.output / "summary.json").write_text(
            json.dumps(summaries, indent=2) + "\n"
        )
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha
        for p, sha in hashes.items()
    )


if __name__ == "__main__":
    main()
