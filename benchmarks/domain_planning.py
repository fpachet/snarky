"""Benchmark compilation of wide finite-domain constraint plans."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from typing import Any

from snarky import Rule, parse_rules
from snarky.instantiation.domain_planning import _compile_domain_plan


def _wide_rule(variable_count: int) -> Rule:
    variables = " ".join(
        f"$value_{index}" for index in range(variable_count)
    )
    return parse_rules(
        f"""
        RULE wide_domain_plan
        WHEN
            (SEQ[{variables}] values anchor)
            $value_0 != $value_1
        THEN
            ADD (domain plan ready)
        END
        """
    )[0]


def measure(
    variable_count: int,
    iterations: int,
    repeat: int,
) -> dict[str, Any]:
    rule = _wide_rule(variable_count)
    samples: list[float] = []
    final_plan = None
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(iterations):
            _compile_domain_plan.cache_clear()
            final_plan = _compile_domain_plan(rule)
        samples.append(
            (time.perf_counter() - started) / iterations
        )
    assert final_plan is not None
    if (
        not final_plan.applicable
        or not final_plan.cyclic
        or len(final_plan.variables) != variable_count
    ):
        raise RuntimeError("wide rule produced an unexpected domain plan")
    return {
        "median_seconds_per_plan": statistics.median(samples),
        "min_seconds_per_plan": min(samples),
        "max_seconds_per_plan": max(samples),
        "variables": len(final_plan.variables),
        "tables": len(final_plan.tables),
        "comparisons": len(final_plan.comparisons),
        "incidence_entries": len(final_plan.incidence),
        "component_entries": len(final_plan.components),
        "cyclic": final_plan.cyclic,
        "applicable": final_plan.applicable,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variables", type=int, default=200)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--repeat", type=int, default=11)
    arguments = parser.parse_args()
    if (
        arguments.variables < 2
        or arguments.iterations < 1
        or arguments.repeat < 1
    ):
        parser.error(
            "--variables must be at least two; iterations and repeat "
            "must be positive"
        )
    print(
        json.dumps(
            {
                "benchmark": "domain_planning",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "variable_count": arguments.variables,
                "iterations": arguments.iterations,
                "repeat": arguments.repeat,
                "result": measure(
                    arguments.variables,
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
