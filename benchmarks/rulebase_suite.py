"""Compare instantiation strategies across documented rule bases."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from typing import Any

from benchmarks.support import PROJECT_ROOT, git_commit, git_dirty
from rulebases.runner import run_scenario
from snarky import (
    AdaptiveInstantiationStrategy,
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)

SCENARIOS = (
    "constraints/global",
    "small/factorial_explicit",
    "small/combinations_foreach",
    "thesis/equality_transitivity",
    "thesis/tomorrow_date",
    "thesis/petri_net",
    "thesis/monkey_bananas/simple",
    "thesis/monkey_bananas/neopus_mea",
    "thesis/muses",
    "thesis/four_queens",
    "thesis/hanoi",
)

_STRATEGIES = {
    "indexed": IndexedInstantiationStrategy,
    "semi-naive": SemiNaiveInstantiationStrategy,
    "adaptive": AdaptiveInstantiationStrategy,
}


def _adaptive_scanned() -> InstantiationStrategy:
    return AdaptiveInstantiationStrategy(
        use_compact_tables=False,
        use_compact_join=False,
    )


def _adaptive_bitset_filter() -> InstantiationStrategy:
    return AdaptiveInstantiationStrategy(
        use_compact_join=False,
    )


_COMPACT_TABLE_STRATEGIES = {
    "adaptive-scanned": _adaptive_scanned,
    "adaptive-bitset-filter": _adaptive_bitset_filter,
    "adaptive-compact": AdaptiveInstantiationStrategy,
}
_ALL_STRATEGIES = _STRATEGIES | _COMPACT_TABLE_STRATEGIES


def measure(
    scenario: str,
    strategy_name: str,
    repeat: int,
) -> dict[str, Any]:
    samples: list[float] = []
    final_strategy: InstantiationStrategy | None = None
    final_result = None
    for _ in range(repeat):
        strategy: InstantiationStrategy = _ALL_STRATEGIES[strategy_name]()
        started = time.perf_counter()
        result = run_scenario(scenario, strategy=strategy)
        samples.append(time.perf_counter() - started)
        if result.missing_expected_facts:
            raise RuntimeError(
                f"{scenario}: missing {result.missing_expected_facts!r}"
            )
        final_strategy = strategy
        final_result = result.result

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
        "cycles": final_result.cycles,
        "match_attempts": metrics.match_attempts,
        "domain_filter_runs": metrics.domain_filter_runs,
        "domain_filter_fallbacks": metrics.domain_filter_fallbacks,
        "domain_filter_selections": metrics.domain_filter_selections,
        "domain_filter_rejections": metrics.domain_filter_rejections,
        "domain_input_rows": metrics.domain_input_rows,
        "domain_rows_examined": metrics.domain_rows_examined,
        "domain_specialized_revisions": (
            metrics.domain_specialized_revisions
        ),
        "domain_specialized_value_checks": (
            metrics.domain_specialized_value_checks
        ),
        "domain_global_revisions": metrics.domain_global_revisions,
        "domain_global_value_checks": metrics.domain_global_value_checks,
        "domain_projection_rows_examined": (
            metrics.domain_projection_rows_examined
        ),
        "domain_projection_updates": metrics.domain_projection_updates,
        "domain_state_reuses": metrics.domain_state_reuses,
        "domain_component_resets": metrics.domain_component_resets,
        "domain_bitset_intersections": (
            metrics.domain_bitset_intersections
        ),
        "domain_bitset_value_events": metrics.domain_bitset_value_events,
        "domain_bitset_support_checks": (
            metrics.domain_bitset_support_checks
        ),
        "domain_compact_join_rows": metrics.domain_compact_join_rows,
        "domain_delta_join_variants": metrics.domain_delta_join_variants,
        "domain_delta_join_skips": metrics.domain_delta_join_skips,
        "domain_cost_probes": metrics.domain_cost_probes,
        "domain_cost_probe_deferrals": metrics.domain_cost_probe_deferrals,
        "domain_cost_probe_rejections": (
            metrics.domain_cost_probe_rejections
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument(
        "--strategy",
        choices=(*_ALL_STRATEGIES, "all", "compact-tables"),
        default="all",
    )
    parser.add_argument(
        "scenarios",
        nargs="*",
        choices=SCENARIOS,
    )
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")
    if arguments.strategy == "all":
        strategy_names = tuple(_STRATEGIES)
    elif arguments.strategy == "compact-tables":
        strategy_names = tuple(_COMPACT_TABLE_STRATEGIES)
    else:
        strategy_names = (arguments.strategy,)
    scenarios = arguments.scenarios or SCENARIOS
    results = [
        {
            "scenario": scenario,
            "strategies": [
                measure(scenario, strategy_name, arguments.repeat)
                for strategy_name in strategy_names
            ],
        }
        for scenario in scenarios
    ]
    print(
        json.dumps(
            {
                "benchmark": "documented_rulebases",
                "repeat": arguments.repeat,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "snarky_commit": git_commit(PROJECT_ROOT),
                "snarky_dirty": git_dirty(PROJECT_ROOT),
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
