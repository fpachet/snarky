"""Benchmark lexical analysis of long term and arithmetic expressions."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from snarky.parser_lexer import _Token, _tokenize, _tokenize_arithmetic


def _measure(
    tokenize: Callable[[str], tuple[_Token, ...]],
    text: str,
    iterations: int,
    repeat: int,
) -> dict[str, int | float]:
    samples: list[float] = []
    final_tokens: tuple[_Token, ...] = ()
    for _ in range(repeat):
        started = time.perf_counter()
        for _ in range(iterations):
            final_tokens = tokenize(text)
        samples.append(
            (time.perf_counter() - started) / iterations
        )
    return {
        "median_seconds_per_call": statistics.median(samples),
        "min_seconds_per_call": min(samples),
        "max_seconds_per_call": max(samples),
        "characters": len(text),
        "tokens": len(final_tokens),
    }


def measure(
    width: int,
    iterations: int,
    repeat: int,
) -> dict[str, Any]:
    term = "SEQ[" + " ".join(
        f"value_{index}" for index in range(width)
    ) + "]"
    arithmetic = " + ".join(
        f"$value_{index}" for index in range(width)
    )
    return {
        "term": _measure(
            _tokenize,
            term,
            iterations,
            repeat,
        ),
        "arithmetic": _measure(
            _tokenize_arithmetic,
            arithmetic,
            iterations,
            repeat,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1_000)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--repeat", type=int, default=11)
    arguments = parser.parse_args()
    if (
        arguments.width < 1
        or arguments.iterations < 1
        or arguments.repeat < 1
    ):
        parser.error("width, iterations, and repeat must be positive")
    print(
        json.dumps(
            {
                "benchmark": "parser_lexing",
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
