"""Benchmark reversible propagation against full-state snapshots."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from snarky import (
    DomainStore,
    Number,
    PropagationReason,
    PropagationState,
    Term,
    Variable,
)


def _measure(
    operation: Callable[[], None],
    repeat: int,
) -> dict[str, float]:
    samples: list[float] = []
    for _ in range(repeat):
        started = time.perf_counter()
        operation()
        samples.append(time.perf_counter() - started)
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
    }


def run(
    variable_count: int,
    domain_size: int,
    touched_variables: int,
    iterations: int,
    repeat: int,
) -> dict[str, Any]:
    variables = tuple(
        Variable(f"value_{index}") for index in range(variable_count)
    )
    values: tuple[Term, ...] = tuple(
        Number(value) for value in range(domain_size)
    )
    domains = {variable: set(values) for variable in variables}
    touched = variables[:touched_variables]
    reason = PropagationReason("benchmark", "branch")

    def trail_operation() -> None:
        state = PropagationState(
            DomainStore(domains),
            {index: (1 << domain_size) - 1 for index in range(variable_count)},
        )
        for iteration in range(iterations):
            checkpoint = state.checkpoint()
            selected = values[iteration % domain_size]
            for index, variable in enumerate(touched):
                state.domains.restrict(variable, selected, reason)
                state.set_active_mask(index, 1 << (iteration % domain_size))
            state.rollback(checkpoint)
        if any(state.domains[variable] != set(values) for variable in touched):
            raise AssertionError("trail rollback did not restore domains")

    def snapshot_operation() -> None:
        current_domains = {
            variable: set(domain) for variable, domain in domains.items()
        }
        masks = {
            index: (1 << domain_size) - 1
            for index in range(variable_count)
        }
        for iteration in range(iterations):
            saved_domains = {
                variable: set(domain)
                for variable, domain in current_domains.items()
            }
            saved_masks = dict(masks)
            selected = values[iteration % domain_size]
            for index, variable in enumerate(touched):
                current_domains[variable].intersection_update({selected})
                masks[index] = 1 << (iteration % domain_size)
            current_domains = saved_domains
            masks = saved_masks
        if any(current_domains[variable] != set(values) for variable in touched):
            raise AssertionError("snapshot restore did not restore domains")

    trail = _measure(trail_operation, repeat)
    snapshot = _measure(snapshot_operation, repeat)
    return {
        "benchmark": "propagation_trail",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "variables": variable_count,
        "domain_size": domain_size,
        "touched_variables": touched_variables,
        "iterations": iterations,
        "trail": trail,
        "full_snapshot": snapshot,
        "trail_speedup": (
            snapshot["median_seconds"] / trail["median_seconds"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variables", type=int, default=1_000)
    parser.add_argument("--domain-size", type=int, default=9)
    parser.add_argument("--touched", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--repeat", type=int, default=7)
    arguments = parser.parse_args()
    if (
        arguments.variables < 1
        or arguments.domain_size < 1
        or arguments.touched < 1
        or arguments.touched > arguments.variables
        or arguments.iterations < 1
        or arguments.repeat < 1
    ):
        parser.error("all sizes must be positive and touched <= variables")
    print(
        json.dumps(
            run(
                arguments.variables,
                arguments.domain_size,
                arguments.touched,
                arguments.iterations,
                arguments.repeat,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
