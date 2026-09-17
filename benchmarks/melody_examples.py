"""Reproduce the 2011 melody examples; save exact scores and repeat timings.

Run: PYTHONHASHSEED=0 PYTHONPATH=src:. python -m benchmarks.melody_examples
The paper fixture is research data and is excluded from Python distributions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import subprocess
import sys
import tracemalloc
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from snarky.finite import MarkovGeneration, NGramModel, Query, QueryKind, solve
from snarky.terms import Number

from . import melody_reference as reference


def exact(value):
    value = Fraction(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def display(value, algebraic=False):
    return (
        int(value)
        if algebraic
        else math.log(value.numerator) - math.log(value.denominator)
    )


def pitches(sequence):
    return [v.value for v in sequence]


def timed(call, repeats):
    samples = []
    result = None
    for _ in range(repeats):
        start = perf_counter()
        result = call()
        samples.append(perf_counter() - start)
    return result, {
        "samples_seconds": samples,
        "median_seconds": statistics.median(samples),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/results/melody_examples_2026-09-16.json"),
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--csp-seconds", type=float, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    if args.output.exists():
        parser.error("use a new output path; benchmark records are immutable")
    fixture = json.loads(reference.CORPUS.read_text())
    corpus = [r["pitches"] for r in fixture["training"]]
    source, training_time = timed(
        lambda: NGramModel.train([tuple(map(Number, s)) for s in corpus], 5),
        args.repeats,
    )
    domains = ((Number(4),),) + (source.alphabet,) * 15 + ((Number(4),),)
    requests = {
        mode: MarkovGeneration(
            source,
            domains,
            mode,
            1 if mode == "fixed" else 4,
            None if mode == "fixed" else 5,
        )
        for mode in reference.MODES
    }
    output = {
        "schema_version": 1,
        "training": training_time,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "working_tree_diff_sha256": hashlib.sha256(
                subprocess.check_output(["git", "diff"])
            ).hexdigest(),
        },
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                reference.CORPUS,
                Path(__file__),
                Path(reference.__file__),
                Path("src/snarky/finite/variable_markov.py"),
                Path("src/snarky/finite/product_objective.py"),
                Path("src/snarky/finite/sparse_chain.py"),
                Path("src/snarky/finite/bounds.py"),
            )
        },
        "timing_scope": (
            "Training excluded. DP includes graph construction. CSP includes "
            "finite-model compilation and solve; graph construction excluded. "
            "Reference includes counting and raw-window DP. Same process, "
            "sequential runs; no heavy tests running."
        ),
        "semantics": {
            "initial": "unit",
            "startup": "progressive eligible order",
            "forbidden_order": 5,
            "smoothing": (
                "arithmetic mean of all eligible order-1..4 probabilities, "
                "including zero terms"
            ),
            "cross_score_display": (
                "natural log for probabilities; exact integer for algebraic"
            ),
            "contour": (
                "alpha*log2(P)-(1-alpha)*squared_pitch_distance; exact rational "
                "comparison"
            ),
        },
        "modes": {},
        "published_cross_scores": fixture["published_cross_scores"],
        "columns": list(reference.MODES),
        "recomputed_cross_scores": {},
    }
    for mode, request in requests.items():
        optimum, dp_time = timed(lambda r=request: r.graph().optimum(), args.repeats)
        reference_result, ref_time = timed(
            lambda r=request: reference.optimum(
                corpus,
                [pitches(d) for d in domains],
                r.mode,
                r.order,
                forbidden=r.forbidden_order,
            ),
            args.repeats,
        )
        assert optimum.score == reference_result[0]
        graph, graph_time = timed(request.graph, args.repeats)
        _, compile_time = timed(graph.compile, args.repeats)
        printed = tuple(map(Number, fixture["published_solutions"][mode]))
        assert optimum.score == request.score(printed)
        record = {
            "score": exact(optimum.score),
            "display_score": display(optimum.score, mode == "algebraic"),
            "sequence": pitches(optimum.sequence),
            "printed_sequence_is_optimal": True,
            "same_sequence_as_printed": optimum.sequence == printed,
            "states": len({e.target for layer in graph.layers for e in layer}),
            "edges": sum(map(len, graph.layers)),
            "dp": dp_time,
            "graph_construction": graph_time,
            "finite_model_compilation": compile_time,
            "raw_window_reference": ref_time,
        }
        for seeded in (False, True):

            def csp(r=graph, seed=seeded, witness=optimum):
                return solve(
                    r.compile(),
                    Query(QueryKind.MAXIMIZE, time_limit_seconds=args.csp_seconds),
                    value_policy="objective",
                    initial_assignment=r.assignment(witness.sequence) if seed else None,
                )

            result, timing = timed(csp, args.repeats)
            if seeded:
                assert result.incumbent.objective_value == optimum.score
            if result.complete:
                assert result.incumbent.objective_value == optimum.score
            record["csp_seeded" if seeded else "csp_unseeded"] = {
                **timing,
                "status": result.status.value,
                "nodes": result.explored_nodes,
                "failed_branches": result.failed_branches,
                "pruned_branches": result.pruned_branches,
                "constraint_revisions": result.constraint_revisions,
                "solver_elapsed_seconds": result.elapsed_seconds,
                "incumbent_history": [
                    {
                        "score": exact(record.value),
                        "seconds": record.elapsed_seconds,
                    }
                    for record in result.incumbent_history
                ],
                "incumbent": exact(result.incumbent.objective_value)
                if result.incumbent
                else None,
                "bound": exact(result.objective_bound)
                if result.objective_bound is not None
                else None,
            }
        output["modes"][mode] = record
        output["recomputed_cross_scores"][mode] = [
            display(
                request.score(
                    tuple(map(Number, fixture["published_solutions"][column]))
                ),
                mode == "algebraic",
            )
            for column in reference.MODES
        ]
        print(
            mode,
            record["display_score"],
            dp_time["median_seconds"],
            record["csp_unseeded"]["status"],
            flush=True,
        )
    base = requests["algebraic"]
    output["anti_copy"] = {}
    for forbidden in (None, 5):
        request = replace(base, forbidden_order=forbidden)
        result, timing = timed(lambda r=request: r.graph().optimum(), args.repeats)
        sequence = pitches(result.sequence)
        observed = reference.counts(corpus, 5)[0][5]
        copies = [
            i
            for i in range(len(sequence) - 5)
            if tuple(sequence[i : i + 6]) in observed
        ]
        if forbidden:
            assert not copies
        output["anti_copy"][str(forbidden)] = {
            "sequence": sequence,
            "score": exact(result.score),
            "copied_six_note_windows": copies,
            **timing,
        }
    target = (4, 7, 11, 16, 21, 24, 28, 28, 24, 21, 16, 12, 9, 7, 6, 4, 4)
    output["contour"] = {"target": target, "runs": []}
    for alpha in (Fraction(0), Fraction(1, 2), Fraction(9, 10), Fraction(1)):
        request = replace(requests["max_order"], contour=target, alpha=alpha)
        result, timing = timed(lambda r=request: r.graph().optimum(), args.repeats)
        reference_result = reference.optimum(
            corpus,
            [pitches(d) for d in domains],
            "max_order",
            4,
            forbidden=5,
            contour=target,
            alpha=alpha,
        )
        assert result.score == reference_result[0]
        seq = pitches(result.sequence)
        output["contour"]["runs"].append(
            {
                "alpha": str(alpha),
                "sequence": seq,
                "squared_distance": sum(
                    (x - y) ** 2 for x, y in zip(seq, target, strict=True)
                ),
                "style_log_probability": display(
                    requests["max_order"].score(result.sequence)
                ),
                "combined_score": exact(result.score),
                **timing,
            }
        )
    output["continuation"] = {
        "initial_prefix": [4],
        "alpha": "9/10",
        "chunks": [],
        "optimality": (
            "Each chunk is optimal given its fixed prefix. This does not imply"
            " a globally optimal stream."
        ),
    }
    prefix = (Number(4),)
    combined_target = []
    product_score = Fraction(1)
    for target in (
        (4, 7, 11, 16, 21, 28),
        (28, 24, 21, 16, 11, 7),
        (7, 9, 12, 16, 12, 4),
    ):
        request = MarkovGeneration(
            source,
            (source.alphabet,) * len(target),
            "max_order",
            4,
            5,
            prefix,
            contour=target,
            alpha=Fraction(9, 10),
        )
        result, timing = timed(lambda r=request: r.graph().optimum(), args.repeats)
        expected = reference.optimum(
            corpus,
            [pitches(source.alphabet)] * len(target),
            "max_order",
            4,
            forbidden=5,
            prefix=pitches(prefix),
            contour=target,
            alpha=Fraction(9, 10),
        )
        assert result.score == expected[0]
        output["continuation"]["chunks"].append(
            {
                "target": target,
                "prefix": pitches(prefix),
                "sequence": pitches(result.sequence),
                "score": exact(result.score),
                **timing,
            }
        )
        prefix += result.sequence
        combined_target.extend(target)
        product_score *= result.score
    whole = MarkovGeneration(
        source,
        (source.alphabet,) * len(combined_target),
        "max_order",
        4,
        5,
        (Number(4),),
        contour=tuple(combined_target),
        alpha=Fraction(9, 10),
    )
    assert whole.score(prefix[1:]) == product_score
    output["continuation"]["whole_stream_score"] = exact(product_score)
    output["continuation"]["globally_optimal_score"] = exact(
        whole.graph().optimum().score
    )
    # Allocation probes are separate from every timing sample.
    for mode, request in requests.items():
        tracemalloc.start()
        request.graph().optimum()
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        output["modes"][mode]["dp_python_allocation_peak_bytes"] = peak
    from .redesign_comparison import snapshot

    args.output.parent.mkdir(parents=True, exist_ok=True)
    archive = args.output.with_suffix(".sources.tar.gz")
    output["source_archive"] = {
        "file": archive.name,
        "content_sha256": snapshot(Path.cwd(), archive),
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
