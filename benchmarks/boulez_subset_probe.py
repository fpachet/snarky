"""Reproducible, bounded exact-counting/MDD diagnostics for anchored Boulez.

The C++ kernel avoids measuring Python object overhead as an algorithmic barrier.
It measures the exact layered MDD's size, not a third-party MDD solver's runtime.
Neither script modifies the Snarky runtime or the training corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import random
import subprocess
import tempfile
from collections import Counter
from datetime import UTC, datetime
from fractions import Fraction
from functools import cache
from pathlib import Path
from time import perf_counter

from benchmarks.blues_corpus import ROOTS, training_sequences
from benchmarks.blues_markov import CORPUS, blues_domains, train

ROOT = Path(__file__).resolve().parents[1]
KERNEL = Path(__file__).with_suffix(".cpp")


def run_kernel(
    binary, matrix, before, *, uniform=False, samples=0, seconds=90, diagnose=True
):
    n = len(matrix)
    maximum = max(map(max, matrix))
    # The bound covers every suffix as well as the full anchored path sum.
    assert math.factorial(n - 3) * max(1, maximum) ** (n - 1) < 2**256
    mode = int(uniform) if diagnose else 2
    payload = f"{n - 3} {before} {samples} {mode} {1024**3}\n"
    payload += "\n".join(" ".join(map(str, row)) for row in matrix)
    start = perf_counter()
    try:
        process = subprocess.run(
            [str(binary)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=seconds,
            check=True,
        )
    except subprocess.TimeoutExpired:
        return {"status": "time_limit", "seconds": seconds}
    result = json.loads(process.stdout)
    result["process_seconds"] = perf_counter() - start
    assert result["peak_rss_bytes"] < 1024**3
    for path in result["samples"]:
        assert sorted(path) == list(range(n))
        assert (path[0], path[before + 1], path[-1]) == (n - 3, n - 2, n - 1)
        assert all(matrix[a][b] for a, b in zip(path, path[1:], strict=False))
    assert sum(map(int, result["first_branch_masses"])) == int(result["mass"])
    paths = result["samples"]
    result["sample_count"] = len(paths)
    result["sample_unique_sequences"] = len({tuple(p) for p in paths})
    result["sample_most_common_count"] = max(
        Counter(map(tuple, paths)).values(), default=0
    )
    if paths:
        result["first_step_empirical_total_variation"] = 0.5 * sum(
            abs(count / len(paths) - int(mass) / int(result["mass"]))
            for count, mass in zip(
                result["sample_first_counts"],
                result["first_branch_masses"],
                strict=True,
            )
        )
    result["samples"] = paths[:10]
    return result


def brute(matrix, before):
    f = len(matrix) - 3
    count = mass = 0
    # Collect exact prefix states/arcs and residual languages independently.
    states = [set() for _ in range(f + 4)]
    suffixes = [{} for _ in states]
    for order in itertools.permutations(range(f)):
        path = (f, *order[:before], f + 1, *order[before:], f + 2)
        weight = math.prod(matrix[a][b] for a, b in zip(path, path[1:], strict=False))
        if not weight:
            continue
        count += 1
        mass += weight
        for depth in range(1, len(path)):
            key = (frozenset(path[:depth]), path[depth - 1])
            states[depth].add(key)
            suffix = path[depth:]
            value = math.prod(
                matrix[a][b]
                for a, b in zip(path[depth - 1 :], path[depth:], strict=False)
            )
            suffixes[depth].setdefault(key, {})[suffix] = value
    boolean, weighted = [], []
    for layer in suffixes:
        boolean.append(len({tuple(sorted(v)) for v in layer.values()}))
        weighted_signatures = set()
        for values in layer.values():
            divisor = math.gcd(*values.values())
            weighted_signatures.add(
                tuple(
                    sorted(
                        (suffix, value // divisor) for suffix, value in values.items()
                    )
                )
            )
        weighted.append(len(weighted_signatures))
    return count, mass, [len(s) for s in states], boolean, weighted


def python_partition(matrix, before):
    """Independent generic recursive DP, used only on small restricted instances."""
    n = len(matrix)
    anchors = {0: n - 3, before + 1: n - 2, n - 1: n - 1}
    reserved = set(anchors.values())

    @cache
    def visit(used, last):
        position = used.bit_count()
        if position == n:
            return 1
        choices = [anchors[position]] if position in anchors else range(n - 3)
        return sum(
            matrix[last][b] * visit(used | (1 << b), b)
            for b in choices
            if not used & (1 << b)
            and matrix[last][b]
            and (position in anchors or b not in reserved)
        )

    start = perf_counter()
    total = visit(1 << (n - 3), n - 3)
    return {
        "mass": str(total),
        "states": visit.cache_info().currsize,
        "seconds": perf_counter() - start,
    }


def validate(binary):
    rng = random.Random(1729)
    cases = []
    for n in range(4, 10):
        for before in sorted({0, (n - 3) // 2, n - 3}):
            for dense in (False, True):
                matrix = [
                    [
                        0
                        if a == b or (not dense and rng.random() < 0.45)
                        else rng.randrange(1, 100000)
                        for b in range(n)
                    ]
                    for a in range(n)
                ]
                count, mass, live, boolean, weighted = brute(matrix, before)
                result = run_kernel(binary, matrix, before, samples=100)
                assert int(result["mass"]) == mass, (n, before, result, mass)
                assert result["live_by_depth"] == live, (n, before, "live")
                assert result["boolean_mdd_by_depth"] == boolean, (n, before, "boolean")
                assert result["weighted_mdd_by_depth"] == weighted, (
                    n,
                    before,
                    "weighted",
                )
                unweighted = run_kernel(binary, matrix, before, uniform=True)
                assert int(unweighted["mass"]) == count
                cases.append(
                    {
                        "n": n,
                        "before": before,
                        "dense": dense,
                        "count": str(count),
                        "mass": str(mass),
                    }
                )
    return {
        "status": "passed",
        "exhaustive_cases": cases,
        "checks": [
            "integer mass",
            "solution count",
            "live layer widths",
            "exact Boolean MDD reduction",
            "proportional weighted reduction",
            "sample validity",
            "early and late internal anchors",
        ],
    }


def rank(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    pivot = 0
    for col in range(len(a[0])):
        row = next((r for r in range(pivot, len(a)) if a[r][col]), None)
        if row is None:
            continue
        a[pivot], a[row] = a[row], a[pivot]
        divisor = a[pivot][col]
        a[pivot] = [v / divisor for v in a[pivot]]
        for r in range(pivot + 1, len(a)):
            scale = a[r][col]
            if scale:
                a[r] = [v - scale * p for v, p in zip(a[r], a[pivot], strict=True)]
        pivot += 1
    return pivot


def structural(source):
    symbols = source.alphabet
    matrix = [[source.transitions.get((a, b), 0) for b in symbols] for a in symbols]
    twins = []
    for i, j in itertools.combinations(range(len(symbols)), 2):
        if matrix[i][j] == matrix[j][i] and all(
            matrix[i][k] == matrix[j][k] and matrix[k][i] == matrix[k][j]
            for k in range(len(symbols))
            if k not in (i, j)
        ):
            twins.append([symbols[i], symbols[j]])
    domains = [set(d) for d in blues_domains(source, "boulez")]
    for d in domains:
        if len(d) > 1:
            d.difference_update({"C7", "F7", "G7"})
    changed = True
    while changed:
        previous = [set(d) for d in domains]
        for i in range(23):
            domains[i] = {
                a
                for a in domains[i]
                if any((a, b) in source.transitions for b in domains[i + 1])
            }
            domains[i + 1] = {
                b
                for b in domains[i + 1]
                if any((a, b) in source.transitions for a in domains[i])
            }
        changed = domains != previous
    frontier = [
        len(set.union(*domains[:i]) & set.union(*domains[i:])) for i in range(1, 24)
    ]

    def transpose(symbol, shift):
        return ROOTS[(ROOTS.index(symbol[:-1]) + shift) % 12] + symbol[-1]

    shifts = [
        t
        for t in range(12)
        if all(
            source.transitions.get((transpose(a, t), transpose(b, t)), 0)
            == source.transitions.get((a, b), 0)
            for a in symbols
            for b in symbols
        )
    ]
    # A support-graph degeneracy is a lower bound on treewidth, not its exact value.
    graph = {
        a: {b for b in range(24) if b != a and (matrix[a][b] or matrix[b][a])}
        for a in range(24)
    }
    degeneracy = 0
    while graph:
        a = min(graph, key=lambda v: len(graph[v]))
        degeneracy = max(degeneracy, len(graph[a]))
        for b in graph[a]:
            graph[b].remove(a)
        del graph[a]
    return {
        "alphabet": list(symbols),
        "nonself_edges": sum(a != b for a, b in source.transitions),
        "weighted_twin_pairs": twins,
        "transition_matrix_rank": rank(matrix),
        "zero_diagonal_transition_rank": rank(
            [
                [0 if i == j else x for j, x in enumerate(row)]
                for i, row in enumerate(matrix)
            ]
        ),
        "domain_sizes_after_elementary_propagation": list(map(len, domains)),
        "frontier_by_cut": frontier,
        "transposition_shifts": shifts,
        "anchor_preserving_transposition_shifts": [t for t in shifts if t == 0],
        "support_treewidth_lower_bound_degeneracy": degeneracy,
    }


def anchored_chain_mass(source):
    """Sum-product reference with the three unary anchors but no AllDifferent."""
    domains = blues_domains(source, "boulez")
    current = {a: source.initial[a] for a in domains[0]}
    for domain in domains[1:]:
        current = {
            b: sum(
                (p * source.transitions.get((a, b), 0) for a, p in current.items()),
                Fraction(),
            )
            for b in domain
        }
    return sum(current.values(), Fraction())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=90)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    source = train(
        training_sequences(
            json.loads(CORPUS.read_text()), "boulez_two_family_proposed", all_keys=True
        )
    )
    denominators = {
        a: math.lcm(
            *(p.denominator for (s, _), p in source.transitions.items() if s == a)
        )
        for a in source.alphabet
    }
    payload = {
        "purpose": "bounded Boulez exact sampling and MDD compression probe",
        "started_at": datetime.now(UTC).isoformat(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"])),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                KERNEL,
                CORPUS,
                ROOT / "benchmarks/blues_corpus.py",
                ROOT / "benchmarks/blues_markov.py",
            ]
        },
        "limits": {
            "seconds_per_process": args.seconds,
            "memory_budget_bytes": 1024**3,
            "arithmetic": "checked 256-bit integer sums and products",
            "memory_enforcement": "pre-allocation array budget; post-run RSS assertion",
        },
        "row_denominators": denominators,
        "structural": structural(source),
        "runs": [],
    }
    chain_mass = anchored_chain_mass(source)
    payload["anchors_without_alldifferent_probability"] = str(chain_mass)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.output.write_text(json.dumps(payload, indent=2) + "\n")

    with tempfile.TemporaryDirectory(prefix="boulez-subset-") as tmp:
        binary = Path(tmp) / "probe"
        compiler = ["clang++", "-O3", "-std=c++17", "-Wall", "-Wextra"]
        payload["compiler"] = subprocess.check_output(
            ["clang++", "--version"], text=True
        )
        payload["compile_command"] = compiler + [
            str(KERNEL),
            "-o",
            "<temporary binary>",
        ]
        subprocess.run(
            [*compiler, str(KERNEL), "-o", str(binary)], check=True, timeout=60
        )
        payload["validation"] = validate(binary)
        print("Small exhaustive count, mass, and MDD oracles passed.", flush=True)
        save()
        free = sorted(set(source.alphabet) - {"C7", "F7", "G7"})
        for n in (8, 12, 16, 20, 24):
            symbols = free[: n - 3] + ["C7", "F7", "G7"]
            before = (n - 3) // 3
            matrix = [
                [
                    int(source.transitions.get((a, b), 0) * denominators[a])
                    if a != b
                    else 0
                    for b in symbols
                ]
                for a in symbols
            ]
            for repeat in range(args.repeat if n == 24 else 1):
                result = run_kernel(
                    binary,
                    matrix,
                    before,
                    samples=10000 if n == 24 else 100,
                    seconds=args.seconds,
                )
                result.update(
                    {
                        "n": n,
                        "repeat": repeat,
                        "symbols": symbols,
                        "middle_anchor_position": before + 2,
                        "mode": "weighted",
                        "samples_requested": 10000 if n == 24 else 100,
                    }
                )
                if n <= 12:
                    oracle = python_partition(matrix, before)
                    assert result["mass"] == oracle["mass"]
                    result["python_oracle"] = oracle
                if result["status"] == "complete":
                    denominator = math.prod(denominators[a] for a in symbols[:-1])
                    probability = source.initial["C7"] * Fraction(
                        int(result["mass"]), denominator
                    )
                    result["event_probability"] = str(probability)
                    result["event_probability_float"] = float(probability)
                    result["decoded_samples"] = [
                        [symbols[i] for i in p] for p in result["samples"]
                    ]
                    if n == 24:
                        result["alldifferent_probability_given_anchors"] = str(
                            probability / chain_mass
                        )
                        witness = json.loads(
                            (
                                ROOT
                                / "benchmarks/results"
                                / "blues_published_witness_2026-09-16.json"
                            ).read_text()
                        )["sequence"]
                        result["published_optimum_conditional_probability"] = str(
                            source.score(tuple(witness)) / probability
                        )
                payload["runs"].append(result)
                save()
                print(
                    f"n={n}, repeat={repeat}: {result['status']}, "
                    f"elapsed={result.get('process_seconds')}, "
                    f"live={sum(result.get('live_by_depth', []))}",
                    flush=True,
                )
                if result["status"] != "complete":
                    break
            if n == 24:
                result = run_kernel(
                    binary, matrix, before, uniform=True, seconds=args.seconds
                )
                result.update({"n": n, "mode": "uniform_support", "symbols": symbols})
                payload["runs"].append(result)
                save()
                print(
                    "Unweighted complete-solution count: "
                    f"{result.get('mass', result['status'])}",
                    flush=True,
                )
                # Reverse every edge and both endpoint anchors; path products and
                # solution counts must be identical under this bijection.
                permutation = [*range(n - 3), n - 1, n - 2, n - 3]
                reversed_matrix = [
                    [matrix[b][a] for b in permutation] for a in permutation
                ]
                for uniform in (False, True):
                    reverse = run_kernel(
                        binary,
                        reversed_matrix,
                        n - 3 - before,
                        uniform=uniform,
                        seconds=args.seconds,
                    )
                    forward = next(
                        r
                        for r in payload["runs"]
                        if r["n"] == 24
                        and r["mode"] == ("uniform_support" if uniform else "weighted")
                    )
                    assert reverse["mass"] == forward["mass"]
                    reverse.update(
                        {
                            "n": n,
                            "mode": "reverse_uniform"
                            if uniform
                            else "reverse_weighted",
                            "reversal_mass_check": "passed",
                        }
                    )
                    payload["runs"].append(reverse)
                    save()
                    print(
                        f"Reverse {'count' if uniform else 'mass'} matches exactly.",
                        flush=True,
                    )
                for repeat in range(args.repeat):
                    result = run_kernel(
                        binary,
                        matrix,
                        before,
                        samples=10000,
                        seconds=args.seconds,
                        diagnose=False,
                    )
                    forward = next(
                        r
                        for r in payload["runs"]
                        if r["n"] == 24 and r["mode"] == "weighted"
                    )
                    assert result["mass"] == forward["mass"]
                    assert result["samples"] == forward["samples"]
                    result.update(
                        {
                            "n": n,
                            "mode": "weighted_no_mdd_diagnostics",
                            "repeat": repeat,
                        }
                    )
                    payload["runs"].append(result)
                    save()
                    print(
                        "Counting + 10,000 samples only: "
                        f"{result['process_seconds']:.3f}s",
                        flush=True,
                    )
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()
