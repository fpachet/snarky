"""Reproducible benchmark for the explicit Fibonacci rule base."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
from pathlib import Path
from time import perf_counter
from typing import Any

from snarky import (
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    NaiveInstantiationStrategy,
    Rule,
    parse_rules,
    parse_term,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = (
    PROJECT_ROOT
    / "tests"
    / "rulebases"
    / "fibonacci_explicit"
    / "fibonacci_explicit.rules"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--strategy",
        choices=("naive", "indexed", "both"),
        default="both",
    )
    arguments = parser.parse_args()
    if arguments.n < 1 or arguments.repeat < 1:
        parser.error("--n and --repeat must be positive")

    rules = parse_rules(RULES_PATH.read_text(encoding="utf-8"))
    initial_facts = fibonacci_facts(arguments.n)
    strategy_names = (
        ("naive", "indexed")
        if arguments.strategy == "both"
        else (arguments.strategy,)
    )
    results = [
        measure(name, rules, initial_facts, arguments.repeat, fibonacci(arguments.n))
        for name in strategy_names
    ]
    payload = {
        "benchmark": "fibonacci_explicit",
        "n": arguments.n,
        "expected_result": fibonacci(arguments.n),
        "repeat": arguments.repeat,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "strategies": results,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def measure(
    name: str,
    rules: tuple[Rule, ...],
    initial_facts: tuple[Fact, ...],
    repeat: int,
    expected_result: int,
) -> dict[str, Any]:
    runs: list[dict[str, int | float]] = []
    for _ in range(repeat):
        strategy = make_strategy(name)
        start = perf_counter()
        result = ForwardEngine(rules, strategy=strategy).run(initial_facts)
        elapsed = perf_counter() - start
        expected_fact = Fact(parse_term(f"(racine resultat {expected_result})"))
        if expected_fact not in result.facts:
            raise RuntimeError(f"missing expected fact: {expected_fact!r}")
        runs.append(
            {
                "seconds": elapsed,
                "facts": len(result.facts),
                "derived_facts": len(result.derived_facts),
                "cycles": result.cycles,
                "fired_activations": result.fired_activation_count,
                "match_attempts": strategy.metrics.match_attempts,
                "candidate_facts": strategy.metrics.candidate_facts,
                "activations_produced": strategy.metrics.activations_produced,
                "index_builds": strategy.metrics.index_builds,
            }
        )
    elapsed_values = [float(run["seconds"]) for run in runs]
    return {
        "name": name,
        "mean_seconds": statistics.mean(elapsed_values),
        "median_seconds": statistics.median(elapsed_values),
        "min_seconds": min(elapsed_values),
        "max_seconds": max(elapsed_values),
        "runs": runs,
    }


def make_strategy(name: str) -> InstantiationStrategy:
    if name == "naive":
        return NaiveInstantiationStrategy()
    if name == "indexed":
        return IndexedInstantiationStrategy()
    raise ValueError(f"unknown strategy: {name}")


def fibonacci_facts(n: int) -> tuple[Fact, ...]:
    if n < 1:
        raise ValueError("n must be positive")
    return (Fact(parse_term(f"(racine fibonacci {n})")),)


def fibonacci(n: int) -> int:
    if n < 1:
        raise ValueError("n must be positive")
    previous, current = 1, 1
    for _ in range(3, n + 1):
        previous, current = current, previous + current
    return current


if __name__ == "__main__":
    main()
