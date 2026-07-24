"""Compare instantiation strategies on the binary-constraint rulebase."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from snarky import (
    AdaptiveInstantiationStrategy,
    ForwardEngine,
    IndexedInstantiationStrategy,
    NaiveInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from snarky.parser import parse_rule_groups
from snarky.serialization.yaml_format import load_facts

_STRATEGIES = {
    "naive": NaiveInstantiationStrategy,
    "indexed": IndexedInstantiationStrategy,
    "semi-naive": SemiNaiveInstantiationStrategy,
    "adaptive": AdaptiveInstantiationStrategy,
}


def run(repeat: int, batch_size: int) -> dict[str, object]:
    root = Path(__file__).parents[1] / "rulebases" / "constraints" / "binary"
    groups = parse_rule_groups((root / "rules.rules").read_text())
    initial_facts = load_facts(root / "initial_facts.yaml")
    results: dict[str, object] = {}

    for name, strategy_type in _STRATEGIES.items():
        samples: list[float] = []
        final_session = None
        for _ in range(repeat):
            started = time.perf_counter()
            for _ in range(batch_size):
                final_session = ForwardEngine(
                    (),
                    strategy=strategy_type(),
                ).create_session(initial_facts)
                for group in groups:
                    final_session.run_group(group)
            samples.append(
                (time.perf_counter() - started) / batch_size
            )

        assert final_session is not None
        snapshot = final_session.snapshot()
        results[name] = {
            "median_seconds": statistics.median(samples),
            "min_seconds": min(samples),
            "max_seconds": max(samples),
            "facts": len(final_session.facts),
            "activations": snapshot.fired_activation_count,
            "cycles": snapshot.cycles,
            "match_attempts": final_session.strategy.metrics.match_attempts,
            "domain_filter_runs": (
                final_session.strategy.metrics.domain_filter_runs
            ),
            "domain_filter_fallbacks": (
                final_session.strategy.metrics.domain_filter_fallbacks
            ),
            "domain_filter_selections": (
                final_session.strategy.metrics.domain_filter_selections
            ),
            "domain_filter_rejections": (
                final_session.strategy.metrics.domain_filter_rejections
            ),
            "domain_rows_examined": (
                final_session.strategy.metrics.domain_rows_examined
            ),
            "domain_input_rows": (
                final_session.strategy.metrics.domain_input_rows
            ),
        }

    naive = results["naive"]
    indexed = results["indexed"]
    semi_naive = results["semi-naive"]
    adaptive = results["adaptive"]
    assert isinstance(naive, dict)
    assert isinstance(indexed, dict)
    assert isinstance(semi_naive, dict)
    assert isinstance(adaptive, dict)
    return {
        "repeat": repeat,
        "batch_size": batch_size,
        "strategies": results,
        "speedup_indexed_over_naive": (
            naive["median_seconds"] / indexed["median_seconds"]
        ),
        "speedup_semi_naive_over_naive": (
            naive["median_seconds"] / semi_naive["median_seconds"]
        ),
        "speedup_adaptive_over_semi_naive": (
            semi_naive["median_seconds"] / adaptive["median_seconds"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument("--batch-size", type=int, default=10)
    arguments = parser.parse_args()
    if arguments.repeat < 1 or arguments.batch_size < 1:
        parser.error("--repeat and --batch-size must be positive")
    print(
        json.dumps(
            run(arguments.repeat, arguments.batch_size),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
