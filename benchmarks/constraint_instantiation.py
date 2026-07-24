"""Compare indexed joins with safe domain filtering on a selective rule."""

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
    FactPremise,
    IndexedInstantiationStrategy,
    Rule,
    Triple,
    Variable,
    add,
)


def _problem(
    size: int,
    scenario: str,
) -> tuple[Rule, tuple[Fact, ...]]:
    if scenario == "chain":
        values = tuple(Atom(f"value{index}") for index in range(size))
        variables = tuple(
            Variable(f"value_{index}") for index in range(size + 1)
        )
        premises = tuple(
            FactPremise(
                Triple(
                    variables[index],
                    Atom(f"edge_{index}"),
                    variables[index + 1],
                )
            )
            for index in range(size)
        )
        rule = Rule(
            "propagation_chain",
            (
                *premises,
                FactPremise(
                    Triple(
                        variables[-1],
                        Atom("fixed"),
                        Atom("yes"),
                    )
                ),
            ),
            (
                add(
                    Triple(
                        variables[0],
                        Atom("solution"),
                        variables[-1],
                    )
                ),
            ),
        )
        facts = (
            *(
                Fact(Triple(value, Atom(f"edge_{index}"), value))
                for index in range(size)
                for value in values
            ),
            Fact(Triple(values[0], Atom("fixed"), Atom("yes"))),
        )
        return rule, facts

    x = Variable("x")
    y = Variable("y")
    z = Variable("z")
    p = Atom("p")
    q = Atom("q")
    r = Atom("r")
    rule = Rule(
        "constrained_triangle",
        (
            FactPremise(Triple(x, p, y)),
            FactPremise(Triple(x, q, z)),
            FactPremise(Triple(y, r, z)),
        ),
        (add(Triple(x, Atom("solution"), y)),),
    )
    if scenario == "neutral":
        facts = tuple(
            fact
            for index in range(size)
            for fact in (
                Fact(
                    Triple(
                        Atom(f"x{index}"),
                        p,
                        Atom(f"y{index}"),
                    )
                ),
                Fact(
                    Triple(
                        Atom(f"x{index}"),
                        q,
                        Atom(f"z{index}"),
                    )
                ),
                Fact(
                    Triple(
                        Atom(f"y{index}"),
                        r,
                        Atom(f"z{index}"),
                    )
                ),
            )
        )
    else:
        last_relation = (
            (Fact(Triple(Atom("y0"), r, Atom("z0"))),)
            if scenario == "favorable"
            else tuple(
                Fact(
                    Triple(
                        Atom(f"y{y_index}"),
                        r,
                        Atom(f"z{z_index}"),
                    )
                )
                for y_index in range(size)
                for z_index in range(size)
            )
        )
        facts = (
            *(
                Fact(
                    Triple(
                        Atom(f"x{x_index}"),
                        p,
                        Atom(f"y{y_index}"),
                    )
                )
                for x_index in range(size)
                for y_index in range(size)
            ),
            *(
                Fact(
                    Triple(
                        Atom(f"x{x_index}"),
                        q,
                        Atom(f"z{z_index}"),
                    )
                )
                for x_index in range(size)
                for z_index in range(size)
            ),
            *last_relation,
        )
    return rule, facts


def run(size: int, repeat: int, scenario: str) -> dict[str, object]:
    rule, facts = _problem(size, scenario)
    results: dict[str, object] = {}
    for name, strategy_type in (
        ("indexed", IndexedInstantiationStrategy),
        (
            "domain-full-scan",
            lambda: ConstraintInstantiationStrategy(
                use_propagation_queue=False
            ),
        ),
        ("domain-filtered", ConstraintInstantiationStrategy),
        ("adaptive", AdaptiveInstantiationStrategy),
    ):
        samples: list[float] = []
        final_strategy = None
        final_activations: tuple[object, ...] = ()
        for _ in range(repeat):
            strategy = strategy_type()
            started = time.perf_counter()
            activations = strategy.instantiate(rule, facts)
            samples.append(time.perf_counter() - started)
            final_strategy = strategy
            final_activations = activations
        assert final_strategy is not None
        metrics = final_strategy.metrics
        results[name] = {
            "median_seconds": statistics.median(samples),
            "min_seconds": min(samples),
            "max_seconds": max(samples),
            "activations": len(final_activations),
            "match_attempts": metrics.match_attempts,
            "domain_match_attempts": metrics.domain_match_attempts,
            "domain_values_removed": metrics.domain_values_removed,
            "domain_candidates_removed": metrics.domain_candidates_removed,
            "domain_filter_selections": metrics.domain_filter_selections,
            "domain_filter_rejections": metrics.domain_filter_rejections,
            "domain_propagator_revisions": (
                metrics.domain_propagator_revisions
            ),
            "domain_rows_examined": metrics.domain_rows_examined,
            "domain_input_rows": metrics.domain_input_rows,
            "domain_specialized_revisions": (
                metrics.domain_specialized_revisions
            ),
            "domain_specialized_value_checks": (
                metrics.domain_specialized_value_checks
            ),
        }
    indexed = results["indexed"]
    filtered = results["domain-filtered"]
    adaptive = results["adaptive"]
    assert isinstance(indexed, dict)
    assert isinstance(filtered, dict)
    assert isinstance(adaptive, dict)
    return {
        "size": size,
        "scenario": scenario,
        "facts": len(facts),
        "repeat": repeat,
        "strategies": results,
        "speedup": (
            indexed["median_seconds"] / filtered["median_seconds"]
        ),
        "adaptive_speedup": (
            indexed["median_seconds"] / adaptive["median_seconds"]
        ),
        "matching_reduction": (
            indexed["match_attempts"] / filtered["match_attempts"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=80)
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument(
        "--scenario",
        choices=("favorable", "neutral", "adverse", "chain"),
        default="favorable",
    )
    arguments = parser.parse_args()
    if arguments.size < 1 or arguments.repeat < 1:
        parser.error("--size and --repeat must be positive")
    print(
        json.dumps(
            run(arguments.size, arguments.repeat, arguments.scenario),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
