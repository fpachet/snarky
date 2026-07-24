"""Benchmark NVALUE, ALL_DIFFERENT, and persistent domain state."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Callable
from typing import Any

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

type StrategyFactory = Callable[[], InstantiationStrategy]

_NVALUE_RULE = parse_rules(
    """
    RULE one_distinct_value
    WHEN
        (anchor value $anchor)
        (left value $left)
        (right value $right)
        (cardinality value $count)
        NVALUE $count OF SEQ[$anchor $left $right]
    THEN
        ADD (SEQ[$anchor $left $right] state solution)
    END
    """
)[0]

_ALL_DIFFERENT_RULE = parse_rules(
    """
    RULE hall_triple
    WHEN
        (first value $first)
        (second value $second)
        (third value $third)
        (fourth value $fourth)
        ALL_DIFFERENT SEQ[$first $second $third $fourth]
    THEN
        ADD (SEQ[$first $second $third $fourth] state solution)
    END
    """
)[0]


def _rebuilt_domains() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_incremental_domains=False,
    )


_STRATEGIES: dict[str, StrategyFactory] = {
    "indexed": IndexedInstantiationStrategy,
    "domain-rebuilt": _rebuilt_domains,
    "domain-incremental": ConstraintInstantiationStrategy,
    "adaptive": AdaptiveInstantiationStrategy,
}


def _fact(subject: str, value: int) -> Fact:
    return Fact(
        Triple(
            Atom(subject),
            Atom("value"),
            Number(value),
        )
    )


def _facts(scenario: str, size: int) -> tuple[Fact, ...]:
    if scenario == "nvalue":
        return (
            _fact("anchor", 1),
            *(_fact("left", value) for value in range(1, size + 1)),
            *(_fact("right", value) for value in range(1, size + 1)),
            _fact("cardinality", 1),
        )
    return (
        *(
            _fact(variable, value)
            for variable in ("first", "second", "third")
            for value in range(1, 4)
        ),
        *(_fact("fourth", value) for value in range(1, size + 1)),
    )


def measure(
    scenario: str,
    size: int,
    repeat: int,
    strategy_name: str,
) -> dict[str, Any]:
    rule = (
        _NVALUE_RULE
        if scenario == "nvalue"
        else _ALL_DIFFERENT_RULE
    )
    facts = _facts(scenario, size)
    samples: list[float] = []
    final_strategy: InstantiationStrategy | None = None
    final_result = None
    for _ in range(repeat):
        strategy = _STRATEGIES[strategy_name]()
        started = time.perf_counter()
        result = ForwardEngine((rule,), strategy=strategy).run(facts)
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
        "domain_filter_runs": metrics.domain_filter_runs,
        "domain_global_revisions": metrics.domain_global_revisions,
        "domain_global_value_checks": metrics.domain_global_value_checks,
        "domain_projection_rows_examined": (
            metrics.domain_projection_rows_examined
        ),
        "domain_projection_updates": metrics.domain_projection_updates,
        "domain_state_reuses": metrics.domain_state_reuses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=("nvalue", "all-different", "all"),
        default="all",
    )
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--repeat", type=int, default=7)
    arguments = parser.parse_args()
    if arguments.size < 4 or arguments.repeat < 1:
        parser.error("--size must be at least 4 and --repeat must be positive")
    scenarios = (
        ("nvalue", "all-different")
        if arguments.scenario == "all"
        else (arguments.scenario,)
    )
    print(
        json.dumps(
            {
                "benchmark": "global_constraints",
                "size": arguments.size,
                "repeat": arguments.repeat,
                "scenarios": [
                    {
                        "name": scenario,
                        "strategies": [
                            measure(
                                scenario,
                                arguments.size,
                                arguments.repeat,
                                strategy_name,
                            )
                            for strategy_name in _STRATEGIES
                        ],
                    }
                    for scenario in scenarios
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
