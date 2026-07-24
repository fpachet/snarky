"""Reproducible benchmark for the native human-style Sudoku rule base."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
from time import perf_counter
from typing import Any

from snarky import (
    AdaptiveInstantiationStrategy,
    ConstraintInstantiationStrategy,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    TechniquePlanStatus,
)
from sudoku import solve_level


def _generic_domain_strategy() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_specialized_comparisons=False,
    )


def _rebuilt_domain_strategy() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_incremental_domains=False,
    )


def _scanned_table_strategy() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_compact_tables=False,
        use_compact_join=False,
    )


def _bitset_filter_strategy() -> InstantiationStrategy:
    return ConstraintInstantiationStrategy(
        use_compact_join=False,
    )


_PRIMARY_STRATEGIES = {
    "indexed": IndexedInstantiationStrategy,
    "semi-naive": SemiNaiveInstantiationStrategy,
    "adaptive": AdaptiveInstantiationStrategy,
}
_COMPARISON_STRATEGIES = {
    "domain-generic": _generic_domain_strategy,
    "domain-filtered": ConstraintInstantiationStrategy,
}
_DOMAIN_STATE_STRATEGIES = {
    "domain-rebuilt": _rebuilt_domain_strategy,
    "domain-incremental": ConstraintInstantiationStrategy,
}
_COMPACT_TABLE_STRATEGIES = {
    "domain-scanned": _scanned_table_strategy,
    "domain-bitset-filter": _bitset_filter_strategy,
    "domain-compact": ConstraintInstantiationStrategy,
}
_STRATEGIES = (
    _PRIMARY_STRATEGIES
    | _COMPARISON_STRATEGIES
    | _DOMAIN_STATE_STRATEGIES
    | _COMPACT_TABLE_STRATEGIES
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--levels", type=int, nargs="+", default=(1, 6, 7))
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument(
        "--strategy",
        choices=(
            *_STRATEGIES,
            "all",
            "comparisons",
            "domain-state",
            "compact-tables",
        ),
        default="all",
    )
    arguments = parser.parse_args()
    invalid_level = any(
        level not in range(1, 8) for level in arguments.levels
    )
    if arguments.repeat < 1 or invalid_level:
        parser.error("--repeat must be positive and levels must be in 1..7")

    if arguments.strategy == "all":
        strategy_names = tuple(_PRIMARY_STRATEGIES)
    elif arguments.strategy == "comparisons":
        strategy_names = tuple(_COMPARISON_STRATEGIES)
    elif arguments.strategy == "domain-state":
        strategy_names = tuple(_DOMAIN_STATE_STRATEGIES)
    elif arguments.strategy == "compact-tables":
        strategy_names = tuple(_COMPACT_TABLE_STRATEGIES)
    else:
        strategy_names = (arguments.strategy,)
    results = [
        {
            "level": level,
            "strategies": [
                measure(level, arguments.repeat, strategy_name)
                for strategy_name in strategy_names
            ],
        }
        for level in arguments.levels
    ]
    print(
        json.dumps(
            {
                "benchmark": "sudoku",
                "repeat": arguments.repeat,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "levels": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


def measure(
    level: int,
    repeat: int,
    strategy_name: str,
) -> dict[str, Any]:
    runs: list[dict[str, int | float]] = []
    for _ in range(repeat):
        strategy: InstantiationStrategy = _STRATEGIES[strategy_name]()
        start = perf_counter()
        result = solve_level(level, strategy=strategy)
        elapsed = perf_counter() - start
        if result.status is not TechniquePlanStatus.SOLVED:
            raise RuntimeError(f"p{level} was not solved")
        runs.append(
            {
                "seconds": elapsed,
                "match_attempts": strategy.metrics.match_attempts,
                "candidate_facts": strategy.metrics.candidate_facts,
                "witness_cache_hits": strategy.metrics.witness_cache_hits,
                "witness_cache_misses": strategy.metrics.witness_cache_misses,
                "witness_cache_invalidations": (
                    strategy.metrics.witness_cache_invalidations
                ),
                "query_counter_updates": (
                    strategy.metrics.query_counter_updates
                ),
                "activation_cache_hits": (
                    strategy.metrics.activation_cache_hits
                ),
                "partial_join_builds": (
                    strategy.metrics.partial_join_builds
                ),
                "partial_join_updates": (
                    strategy.metrics.partial_join_updates
                ),
                "partial_join_bypasses": (
                    strategy.metrics.partial_join_bypasses
                ),
                "structural_index_builds": (
                    strategy.metrics.structural_index_builds
                ),
                "structural_index_lookups": (
                    strategy.metrics.structural_index_lookups
                ),
                "adaptive_join_reorders": (
                    strategy.metrics.adaptive_join_reorders
                ),
                "residual_witness_promotions": (
                    strategy.metrics.residual_witness_promotions
                ),
                "cycles": result.inference.cycles,
                "fired_activations": result.inference.fired_activation_count,
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
                "domain_specialized_value_checks": (
                    strategy.metrics.domain_specialized_value_checks
                ),
                "domain_combinations_tested": (
                    strategy.metrics.domain_combinations_tested
                ),
                "domain_projection_rows_examined": (
                    strategy.metrics.domain_projection_rows_examined
                ),
                "domain_projection_updates": (
                    strategy.metrics.domain_projection_updates
                ),
                "domain_state_reuses": (
                    strategy.metrics.domain_state_reuses
                ),
                "domain_component_resets": (
                    strategy.metrics.domain_component_resets
                ),
                "domain_global_revisions": (
                    strategy.metrics.domain_global_revisions
                ),
                "domain_global_value_checks": (
                    strategy.metrics.domain_global_value_checks
                ),
                "domain_bitset_builds": (
                    strategy.metrics.domain_bitset_builds
                ),
                "domain_bitset_updates": (
                    strategy.metrics.domain_bitset_updates
                ),
                "domain_bitset_resets": (
                    strategy.metrics.domain_bitset_resets
                ),
                "domain_bitset_intersections": (
                    strategy.metrics.domain_bitset_intersections
                ),
                "domain_bitset_value_events": (
                    strategy.metrics.domain_bitset_value_events
                ),
                "domain_bitset_support_checks": (
                    strategy.metrics.domain_bitset_support_checks
                ),
                "domain_compact_join_rows": (
                    strategy.metrics.domain_compact_join_rows
                ),
            }
        )
    elapsed_values = [float(run["seconds"]) for run in runs]
    return {
        "name": strategy_name,
        "mean_seconds": statistics.mean(elapsed_values),
        "median_seconds": statistics.median(elapsed_values),
        "min_seconds": min(elapsed_values),
        "max_seconds": max(elapsed_values),
        "runs": runs,
    }


if __name__ == "__main__":
    main()
