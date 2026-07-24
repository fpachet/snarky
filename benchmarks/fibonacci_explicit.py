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
    AdaptiveInstantiationStrategy,
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    NaiveInstantiationStrategy,
    Rule,
    SemiNaiveInstantiationStrategy,
    parse_rules,
    parse_term,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = (
    PROJECT_ROOT
    / "rulebases"
    / "small"
    / "fibonacci_explicit"
    / "fibonacci_explicit.rules"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--n", type=int)
    target.add_argument(
        "--range",
        dest="n_range",
        type=int,
        nargs=2,
        metavar=("START", "END"),
    )
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--strategy",
        choices=(
            "naive",
            "indexed",
            "semi-naive",
            "adaptive",
            "both",
            "all",
        ),
        default="all",
    )
    arguments = parser.parse_args()
    try:
        ranks = resolve_ranks(arguments.n, arguments.n_range)
    except ValueError as error:
        parser.error(str(error))
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")

    rules = parse_rules(RULES_PATH.read_text(encoding="utf-8"))
    strategy_names: tuple[str, ...]
    if arguments.strategy == "both":
        strategy_names = ("naive", "indexed")
    elif arguments.strategy == "all":
        strategy_names = ("naive", "indexed", "semi-naive", "adaptive")
    else:
        strategy_names = (arguments.strategy,)
    cases = [
        measure_case(rank, rules, strategy_names, arguments.repeat)
        for rank in ranks
    ]
    payload: dict[str, Any] = {
        "benchmark": "fibonacci_explicit",
        "repeat": arguments.repeat,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    if len(cases) == 1:
        payload.update(cases[0])
    else:
        payload["range"] = [ranks[0], ranks[-1]]
        payload["cases"] = cases
    print(json.dumps(payload, indent=2, sort_keys=True))


def resolve_ranks(
    n: int | None,
    n_range: tuple[int, int] | None,
) -> tuple[int, ...]:
    if n_range is None:
        rank = 10 if n is None else n
        if rank < 1:
            raise ValueError("--n must be positive")
        return (rank,)
    start, end = n_range
    if start < 1 or end < start:
        raise ValueError("--range requires 1 <= START <= END")
    return tuple(range(start, end + 1))


def measure_case(
    n: int,
    rules: tuple[Rule, ...],
    strategy_names: tuple[str, ...],
    repeat: int,
) -> dict[str, Any]:
    expected_result = fibonacci(n)
    initial_facts = fibonacci_facts(n)
    return {
        "n": n,
        "expected_result": expected_result,
        "strategies": [
            measure(
                name,
                rules,
                initial_facts,
                repeat,
                expected_result,
            )
            for name in strategy_names
        ],
    }


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
                "domain_filter_runs": strategy.metrics.domain_filter_runs,
                "domain_filter_fallbacks": (
                    strategy.metrics.domain_filter_fallbacks
                ),
                "domain_filter_selections": (
                    strategy.metrics.domain_filter_selections
                ),
                "domain_filter_rejections": (
                    strategy.metrics.domain_filter_rejections
                ),
                "domain_rows_examined": (
                    strategy.metrics.domain_rows_examined
                ),
                "domain_input_rows": strategy.metrics.domain_input_rows,
                "domain_specialized_revisions": (
                    strategy.metrics.domain_specialized_revisions
                ),
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
    if name == "semi-naive":
        return SemiNaiveInstantiationStrategy()
    if name == "adaptive":
        return AdaptiveInstantiationStrategy()
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
