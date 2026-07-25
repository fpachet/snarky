"""Benchmark branching from a populated adaptive domain strategy."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from typing import Any

from snarky import AdaptiveInstantiationStrategy

from .constraint_instantiation import _problem


def measure(
    size: int,
    forks_per_sample: int,
    repeat: int,
    *,
    sanitize_propagation_results: bool,
) -> dict[str, Any]:
    rule, facts = _problem(size, "favorable")
    strategy = AdaptiveInstantiationStrategy()
    strategy.instantiate(rule, facts)
    if sanitize_propagation_results:
        strategy.last_propagation_results.clear()
        for memory in strategy._domain_memories.values():
            memory.cached_result = None

    samples: list[float] = []
    final_branch = None
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(forks_per_sample):
            final_branch = strategy.fork_for_branch()
        samples.append(
            (time.perf_counter() - started) / forks_per_sample
        )
    assert final_branch is not None
    if (
        type(final_branch) is not AdaptiveInstantiationStrategy
        or len(final_branch._domain_memories)
        != len(strategy._domain_memories)
        or final_branch._filter_decisions != strategy._filter_decisions
    ):
        raise RuntimeError("branch did not preserve adaptive filter state")
    return {
        "median_seconds_per_fork": statistics.median(samples),
        "min_seconds_per_fork": min(samples),
        "max_seconds_per_fork": max(samples),
        "facts": len(facts),
        "domain_memories": len(strategy._domain_memories),
        "adaptive_decisions": len(strategy._filter_decisions),
        "sanitize_propagation_results": sanitize_propagation_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=40)
    parser.add_argument("--forks-per-sample", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=11)
    parser.add_argument(
        "--sanitize-propagation-results",
        action="store_true",
    )
    arguments = parser.parse_args()
    if (
        arguments.size < 1
        or arguments.forks_per_sample < 1
        or arguments.repeat < 1
    ):
        parser.error("size, forks per sample, and repeat must be positive")
    print(
        json.dumps(
            {
                "benchmark": "constraint_branching",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "size": arguments.size,
                "forks_per_sample": arguments.forks_per_sample,
                "repeat": arguments.repeat,
                "result": measure(
                    arguments.size,
                    arguments.forks_per_sample,
                    arguments.repeat,
                    sanitize_propagation_results=(
                        arguments.sanitize_propagation_results
                    ),
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
