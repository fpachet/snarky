"""Benchmark declarative arithmetic filtering before factual joins."""

from __future__ import annotations

import argparse
import json
import statistics
import time

from snarky import (
    AdaptiveInstantiationStrategy,
    Atom,
    ConstraintInstantiationStrategy,
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    Number,
    Triple,
    parse_rules,
)

_RULE = parse_rules(
    """
    RULE constrained_sum
    WHEN
        (left value $left)
        (right value $right)
        (total value $total)
        CONSTRAINT $left + $right == $total
    THEN
        ADD (sum state found)
    END
    """
)[0]

_STRATEGY_NAMES = (
    "indexed",
    "domain-generic",
    "domain-filtered",
    "adaptive",
)


def _facts(size: int) -> tuple[Fact, ...]:
    left = Atom("left")
    right = Atom("right")
    total = Atom("total")
    value = Atom("value")
    return (
        *(
            Fact(Triple(left, value, Number(candidate)))
            for candidate in range(1, size + 1)
        ),
        *(
            Fact(Triple(right, value, Number(candidate)))
            for candidate in range(1, size + 1)
        ),
        Fact(Triple(total, value, Number(2))),
    )


def measure(
    size: int,
    repeat: int,
    strategy_name: str,
) -> dict[str, int | float | str]:
    facts = _facts(size)
    samples: list[float] = []
    final_strategy: InstantiationStrategy | None = None
    final_result = None
    for _ in range(repeat):
        strategy = _make_strategy(strategy_name, size)
        started = time.perf_counter()
        result = ForwardEngine((_RULE,), strategy=strategy).run(facts)
        samples.append(time.perf_counter() - started)
        final_strategy = strategy
        final_result = result
    assert final_strategy is not None
    assert final_result is not None
    metrics = final_strategy.metrics
    return {
        "name": strategy_name,
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "facts": len(final_result.facts),
        "activations": final_result.fired_activation_count,
        "match_attempts": metrics.match_attempts,
        "domain_match_attempts": metrics.domain_match_attempts,
        "domain_specialized_revisions": (
            metrics.domain_specialized_revisions
        ),
        "domain_specialized_value_checks": (
            metrics.domain_specialized_value_checks
        ),
        "domain_projection_rows_examined": (
            metrics.domain_projection_rows_examined
        ),
        "domain_projection_updates": metrics.domain_projection_updates,
        "domain_state_reuses": metrics.domain_state_reuses,
        "domain_component_resets": metrics.domain_component_resets,
    }


def _make_strategy(
    strategy_name: str,
    size: int,
) -> InstantiationStrategy:
    if strategy_name == "indexed":
        return IndexedInstantiationStrategy()
    if strategy_name == "domain-generic":
        return ConstraintInstantiationStrategy(
            comparison_product_limit=size * size,
            use_specialized_comparisons=False,
        )
    if strategy_name == "domain-filtered":
        return ConstraintInstantiationStrategy()
    if strategy_name == "adaptive":
        return AdaptiveInstantiationStrategy()
    raise ValueError(f"unknown strategy: {strategy_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--repeat", type=int, default=7)
    arguments = parser.parse_args()
    if arguments.size < 1 or arguments.repeat < 1:
        parser.error("--size and --repeat must be positive")
    results = [
        measure(arguments.size, arguments.repeat, name)
        for name in _STRATEGY_NAMES
    ]
    indexed = results[0]
    adaptive = results[-1]
    print(
        json.dumps(
            {
                "benchmark": "arithmetic_constraints",
                "size": arguments.size,
                "repeat": arguments.repeat,
                "strategies": results,
                "adaptive_speedup": (
                    float(indexed["median_seconds"])
                    / float(adaptive["median_seconds"])
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
