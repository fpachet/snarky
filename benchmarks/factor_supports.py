"""Interleaved factor-support benchmark against a chosen committed source.

Run: python -m benchmarks.factor_supports --baseline-ref 1a453ad --output result.json
Only the factor evaluator is swapped; both use the current matching engine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
import types
from pathlib import Path

from snarky import Atom, Fact, Triple, Variable, when
from snarky.factors import FactorGroup, FactorModel, evaluate_factor_model, factor


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], text=True).strip()


def run(baseline_ref: str, sizes: list[int], repeat: int) -> dict[str, object]:
    baseline_commit = git("rev-parse", "--verify", baseline_ref)
    source = git("show", f"{baseline_commit}:src/snarky/factors.py")
    reference = types.ModuleType("snarky._factor_support_reference")
    reference.__package__ = "snarky"
    sys.modules[reference.__name__] = reference
    exec(compile(source, "<committed factor evaluator>", "exec"), reference.__dict__)
    implementations = {
        "baseline": reference.evaluate_factor_model,
        "current": evaluate_factor_model,
    }
    variable = Variable("witness")
    model = FactorModel("support_scaling", (FactorGroup("many", (factor(
        "witness", Atom("shared_scope"),
        (when(Triple(variable, Atom("kind"), Atom("item"))),), log_weight=1.0,
    ),)),))
    rows = []
    for size in sizes:
        facts = tuple(
            Fact(Triple(Atom(f"item_{index}"), Atom("kind"), Atom("item")))
            for index in range(size)
        )
        samples: dict[str, list[float]] = {name: [] for name in implementations}
        expected = ("witness", "many", Atom("shared_scope"), 1.0, facts, size)

        def measure(name: str, facts=facts, expected=expected) -> float:
            start = time.perf_counter()
            result = implementations[name](model, facts)
            elapsed = time.perf_counter() - start
            assert result.log_score == 1.0 and len(result.activations) == 1
            activation = result.activations[0]
            assert (
                activation.factor_name, activation.group_name, activation.scope,
                activation.log_weight, activation.support_facts,
                activation.witness_count,
            ) == expected
            return elapsed

        for name in implementations:
            measure(name)  # Warm both implementations; validate every result.
        for iteration in range(repeat):
            names = list(implementations)
            if iteration % 2:
                names.reverse()
            for name in names:
                samples[name].append(measure(name))
        medians = {name: statistics.median(values) for name, values in samples.items()}
        rows.append({"witnesses": size, "samples_seconds": samples,
                     "median_seconds": medians,
                     "speedup": medians["baseline"] / medians["current"]})
    current_source = Path(__file__).resolve().parents[1] / "src/snarky/factors.py"
    return {
        "baseline_commit": baseline_commit, "current_commit": git("rev-parse", "HEAD"),
        "current_dirty": bool(git("status", "--porcelain")),
        "current_factor_source_sha256": hashlib.sha256(
            current_source.read_bytes()
        ).hexdigest(),
        "python": platform.python_version(), "platform": platform.platform(),
        "protocol": (
            "Shared current matcher; warmed evaluator-only A/B, alternating order"
        ),
        "repeat": repeat, "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[500, 1000, 2000, 4000])
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.repeat < 1 or any(size < 1 for size in arguments.sizes):
        parser.error("repeat and sizes must be positive")
    result = run(arguments.baseline_ref, arguments.sizes, arguments.repeat)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["results"], indent=2))


if __name__ == "__main__":
    main()
