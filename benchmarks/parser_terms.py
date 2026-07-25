"""Benchmark recursive parsing of representative term shapes."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from pathlib import Path
from typing import Any

from snarky import parse_rules, parse_term
from snarky.rules import Rule
from snarky.terms import FiniteSequence, Term, Triple


def _measure(
    text: str,
    iterations: int,
    repeat: int,
) -> dict[str, int | float]:
    samples: list[float] = []
    final_term: Term | None = None
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(iterations):
            final_term = parse_term(text)
        samples.append((time.perf_counter() - started) / iterations)
    return {
        "median_seconds_per_call": statistics.median(samples),
        "min_seconds_per_call": min(samples),
        "max_seconds_per_call": max(samples),
        "characters": len(text),
        "top_level_elements": (
            len(final_term.elements)
            if isinstance(final_term, FiniteSequence)
            else 0
        ),
        "triple_depth": _triple_depth(final_term),
    }


def _triple_depth(term: Term | None) -> int:
    depth = 0
    while isinstance(term, Triple):
        depth += 1
        term = term.object
    return depth


def _measure_rules(
    text: str,
    iterations: int,
    repeat: int,
) -> dict[str, int | float]:
    samples: list[float] = []
    final_rules: tuple[Rule, ...] = ()
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(iterations):
            final_rules = parse_rules(text)
        samples.append((time.perf_counter() - started) / iterations)
    return {
        "median_seconds_per_call": statistics.median(samples),
        "min_seconds_per_call": min(samples),
        "max_seconds_per_call": max(samples),
        "characters": len(text),
        "rules": len(final_rules),
    }


def measure(
    width: int,
    depth: int,
    iterations: int,
    repeat: int,
) -> dict[str, Any]:
    wide_sequence = "SEQ[" + " ".join(
        f"value_{index}" for index in range(width)
    ) + "]"
    statuses = ("VRAI", "FAUX", "INEXISTANT", "NOMBRE")
    status_sequence = "SEQ[" + " ".join(
        statuses[index % len(statuses)] for index in range(width)
    ) + "]"
    nested_triple = "leaf"
    for index in range(depth):
        nested_triple = f"(node_{index} relation {nested_triple})"
    project_root = Path(__file__).resolve().parents[1]
    status_rulebase = (
        project_root
        / "spinoza/systematic/rules/proofs/E3P18.rules"
    ).read_text()
    return {
        "wide_sequence": _measure(
            wide_sequence,
            iterations,
            repeat,
        ),
        "status_sequence": _measure(
            status_sequence,
            iterations,
            repeat,
        ),
        "nested_triple": _measure(
            nested_triple,
            iterations,
            repeat,
        ),
        "spinoza_status_rulebase": _measure_rules(
            status_rulebase,
            iterations,
            repeat,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1_000)
    parser.add_argument("--depth", type=int, default=100)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--repeat", type=int, default=11)
    arguments = parser.parse_args()
    if (
        arguments.width < 1
        or arguments.depth < 1
        or arguments.iterations < 1
        or arguments.repeat < 1
    ):
        parser.error("width, depth, iterations, and repeat must be positive")
    print(
        json.dumps(
            {
                "benchmark": "parser_terms",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "width": arguments.width,
                "depth": arguments.depth,
                "iterations": arguments.iterations,
                "repeat": arguments.repeat,
                "results": measure(
                    arguments.width,
                    arguments.depth,
                    arguments.iterations,
                    arguments.repeat,
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
