"""Compiler-free Python SUM-policy discovery, audits and paired timings."""

import argparse
import hashlib
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from benchmarks.alice_magic import validate
from snarky.finite.model import Query
from snarky.finite.search import search

from .magic_profile import MeasuredNative
from .magic_residual_study import freeze, settings
from .magic_search_tuning import RankedDomains, RankedState, prepare
from .python_sum_policy import enable

VARIANTS = {
    "exact": None,
    "always": dict(mode="always"),
    "bounds": dict(mode="bounds"),
    **{f"budget_{b}": dict(mode="budget", budget=b) for b in (512, 2000, 8000, 32000)},
    "selected": dict(mode="budget", budget=2000, min_span=1024),
}


def preset(n):
    return (
        dict(policy="dom_wdeg", order="random", tie="row_major", symmetry=False, seed=1)
        if n == 20
        else settings(n)
    )


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def record(domains):
    retain, digest, count = domains.retain_mask, hashlib.sha256(), [0]

    def retain_mask(variable, mask, cause):
        index = domains.index(variable)
        before = domains._masks[index]
        changed = retain(variable, mask, cause)
        if changed:
            digest.update(
                json.dumps([index, before, domains._masks[index], str(cause)]).encode()
                + b"\n"
            )
            count[0] += 1
        return changed

    domains.retain_mask = retain_mask
    return digest, count


def signature(row):
    return tuple(
        row[k] for k in ("nodes", "failures", "revisions", "termination", "squares")
    )


def run(n, variant, phase, seconds):
    p = preset(n)
    started = perf_counter()
    original, model = prepare(
        n, p["order"], p["tie"], p["symmetry"], seed=p.get("seed", 0)
    )
    state = RankedState(model, p["order"])
    if phase == "profile":
        state.native = MeasuredNative(model)
        state.domains = RankedDomains(state.native.domains, model, p["order"])
    if VARIANTS[variant] is not None:
        enable(state.native, **VARIANTS[variant])
    audit = record(state.native.domains) if phase == "audit" else None
    entered = perf_counter()
    result = search(
        state,
        Query(max_nodes=100000 if n == 20 else 10000, time_limit_seconds=seconds),
        policy=p["policy"],
    )
    finished = perf_counter()
    row = dict(
        size=n,
        variant=variant,
        phase=phase,
        settings=p,
        seconds=finished - started,
        search_seconds=finished - entered,
        nodes=result.explored_nodes,
        failures=result.failed_branches,
        revisions=result.constraint_revisions,
        termination=result.termination.value,
        squares=[validate(n, s.assignment, original) for s in result.solutions],
        stats=dict(getattr(state.native._numeric, "stats", {})),
    )
    if audit:
        row.update(reductions_sha256=audit[0].hexdigest(), reduction_events=audit[1][0])
    if phase == "profile":
        row.update(times=dict(state.native.times), calls=dict(state.native.calls))
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["pilot", "timing", "audit", "profile"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 9, 16, 20])
    parser.add_argument(
        "--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS)
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seconds", type=float, default=30)
    args = parser.parse_args()
    if args.repeats < 1 or args.seconds <= 0 or any(n < 3 for n in args.sizes):
        parser.error("invalid repetition/time limits or sizes")
    folder = Path(__file__).parent
    freeze(
        args.output,
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        extra_files=[
            folder / name
            for name in (
                "python_sum_policy.py",
                "python_sum_policy_benchmark.py",
                "test_python_sum_policy.py",
                "magic_profile.py",
            )
        ],
    )
    repeats = args.repeats if args.phase == "timing" else 1
    schedule = [
        (n, r, v) for n in args.sizes for r in range(repeats) for v in args.variants
    ]
    Random(141026).shuffle(schedule)
    save(args.output / "schedule.json", schedule)
    rows, signatures = [], {}
    for n, repeat, variant in schedule:
        row = run(n, variant, args.phase, args.seconds)
        row["repeat"] = repeat
        if row["termination"] != "time_limit":
            key = n, variant
            value = signature(row) + (
                row.get("reductions_sha256"),
                row.get("reduction_events"),
            )
            if key in signatures:
                assert signatures[key] == value
            signatures[key] = value
        if args.phase in ("timing", "audit"):
            assert row["termination"] == "solution_limit", (
                "selected comparison did not solve"
            )
        rows.append(row)
        with (args.output / "runs.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("squares", "settings")}
            ),
            flush=True,
        )
    summary = []
    for n in args.sizes:
        exact = next(
            (r for r in rows if r["size"] == n and r["variant"] == "exact"), None
        )
        for variant in args.variants:
            group = [r for r in rows if r["size"] == n and r["variant"] == variant]
            summary.append(
                dict(
                    size=n,
                    variant=variant,
                    seconds=median(r["seconds"] for r in group),
                    search_seconds=median(r["search_seconds"] for r in group),
                    solved=all(bool(r["squares"]) for r in group),
                    nodes=group[0]["nodes"],
                    termination=group[0]["termination"],
                    same_exact_search=exact is not None
                    and all(signature(r) == signature(exact) for r in group),
                )
            )
    save(args.output / "summary.json", summary)
    frozen = json.loads((args.output / "frozen.json").read_text())
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
        for p, h in frozen["source_hashes"].items()
    )


if __name__ == "__main__":
    main()
