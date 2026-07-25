"""Benchmark action parsing for ordinary, nested, and real rule blocks."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from pathlib import Path
from typing import Any

from snarky import parse_rule_groups
from snarky.actions import Action
from snarky.parser_actions import _parse_action_block
from snarky.rules import RuleGroup


def _measure_block(
    lines: tuple[str, ...],
    iterations: int,
    repeat: int,
) -> dict[str, int | float]:
    source = (*lines, "END")
    samples: list[float] = []
    final_actions: list[Action] = []
    final_position = 0
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(iterations):
            final_actions, final_position = _parse_action_block(
                source,
                0,
                "END",
                None,
            )
        samples.append((time.perf_counter() - started) / iterations)
    return {
        "median_seconds_per_call": statistics.median(samples),
        "min_seconds_per_call": min(samples),
        "max_seconds_per_call": max(samples),
        "source_lines": len(lines),
        "actions": len(final_actions),
        "final_position": final_position,
    }


def _measure_rule_groups(
    text: str,
    iterations: int,
    repeat: int,
) -> dict[str, int | float]:
    samples: list[float] = []
    final_groups: tuple[RuleGroup, ...] = ()
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(iterations):
            final_groups = parse_rule_groups(text)
        samples.append((time.perf_counter() - started) / iterations)
    return {
        "median_seconds_per_call": statistics.median(samples),
        "min_seconds_per_call": min(samples),
        "max_seconds_per_call": max(samples),
        "characters": len(text),
        "groups": len(final_groups),
        "rules": sum(len(group.rules) for group in final_groups),
    }


def measure(
    width: int,
    iterations: int,
    repeat: int,
) -> dict[str, Any]:
    ordinary = tuple(
        (
            f"ADD (node_{index} relation value_{index})"
            if index % 2 == 0
            else f"REMOVE (node_{index} relation value_{index})"
        )
        for index in range(width)
    )
    mixed: list[str] = []
    for index in range(max(1, width // 10)):
        mixed.extend(
            (
                f"LET $sum_{index} := {index} + 1",
                f"FRESH $fresh_{index} PREFIX generated",
                f"ADD (node_{index} value $sum_{index})",
                f"REMOVE (node_{index} pending yes)",
                f"FOR EACH $item_{index} IN SEQ[a_{index} b_{index}]",
                f"ADD ($item_{index} selected yes)",
                "END_FOR_EACH",
                f"CHOICE (node_{index} selected $candidate_{index})",
                "FROM",
                f"(node_{index} candidate $candidate_{index})",
                "END_CHOICE",
            )
        )
    project_root = Path(__file__).resolve().parents[1]
    sudoku = "\n".join(
        path.read_text()
        for path in sorted((project_root / "sudoku/rules").glob("*.rules"))
    )
    return {
        "ordinary_block": _measure_block(
            ordinary,
            iterations,
            repeat,
        ),
        "mixed_block": _measure_block(
            tuple(mixed),
            iterations,
            repeat,
        ),
        "sudoku_rulebase": _measure_rule_groups(
            sudoku,
            iterations,
            repeat,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=400)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=11)
    arguments = parser.parse_args()
    if (
        arguments.width < 10
        or arguments.iterations < 1
        or arguments.repeat < 1
    ):
        parser.error("width >= 10, iterations, and repeat must be positive")
    print(
        json.dumps(
            {
                "benchmark": "parser_actions",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "width": arguments.width,
                "iterations": arguments.iterations,
                "repeat": arguments.repeat,
                "results": measure(
                    arguments.width,
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
