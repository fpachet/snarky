"""Measure declarative binary propagation as domains and chains grow."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from snarky import (
    AdaptiveInstantiationStrategy,
    Atom,
    Fact,
    FiniteSequence,
    ForwardEngine,
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    Triple,
)
from snarky.parser import parse_rule_groups
from snarky.terms import Term


def _fact(subject: Term, relation: str, object_: Term) -> Fact:
    return Fact(Triple(subject, Atom(relation), object_))


def equality_chain(variable_count: int, domain_size: int) -> tuple[Fact, ...]:
    """Create a chain whose singleton first domain propagates to the end."""

    relation = Atom("equality-relation")
    problem = Atom("equality-chain")
    values = tuple(Atom(f"value-{index}") for index in range(domain_size))
    variables = tuple(
        Atom(f"variable-{index}") for index in range(variable_count)
    )
    facts = [
        _fact(relation, "kind", Atom("binary_relation")),
        _fact(problem, "kind", Atom("csp_problem")),
    ]
    facts.extend(
        _fact(
            relation,
            "allows",
            FiniteSequence((value, value)),
        )
        for value in values
    )
    for position, variable in enumerate(variables):
        facts.append(_fact(problem, "variable", variable))
        facts.append(_fact(variable, "kind", Atom("csp_variable")))
        candidates = values[:1] if position == 0 else values
        facts.extend(
            _fact(variable, "candidate", candidate)
            for candidate in candidates
        )
    for position, (left, right) in enumerate(
        zip(variables, variables[1:], strict=False)
    ):
        constraint = Atom(f"constraint-{position}")
        facts.extend(
            (
                _fact(constraint, "kind", Atom("binary_constraint")),
                _fact(constraint, "problem", problem),
                _fact(constraint, "relation", relation),
                _fact(constraint, "left", left),
                _fact(constraint, "right", right),
            )
        )
    return tuple(facts)


def measure(
    variable_count: int,
    domain_size: int,
    repeat: int,
    strategy_name: str,
) -> dict[str, object]:
    root = Path(__file__).parents[1]
    groups = parse_rule_groups(
        (
            root
            / "rulebases"
            / "constraints"
            / "binary"
            / "rules.rules"
        ).read_text()
    )
    propagation = groups[0]
    initial_facts = equality_chain(variable_count, domain_size)
    expected_removals = (variable_count - 1) * (domain_size - 1)
    samples: list[float] = []
    final_session = None
    final_strategy = None
    for _ in range(repeat):
        strategy: InstantiationStrategy
        if strategy_name == "semi-naive":
            strategy = SemiNaiveInstantiationStrategy()
        elif strategy_name == "adaptive":
            strategy = AdaptiveInstantiationStrategy()
        else:
            raise ValueError(f"unknown strategy: {strategy_name}")
        session = ForwardEngine((), strategy=strategy).create_session(
            initial_facts
        )
        started = time.perf_counter()
        session.run_group(propagation)
        samples.append(time.perf_counter() - started)
        final_session = session
        final_strategy = strategy

    assert final_session is not None
    assert final_strategy is not None
    remaining_candidates = sum(
        isinstance(fact.entity, Triple)
        and fact.entity.relation == Atom("candidate")
        for fact in final_session.facts
    )
    if remaining_candidates != variable_count:
        raise AssertionError(
            f"expected {variable_count} candidates, "
            f"found {remaining_candidates}"
        )
    snapshot = final_session.snapshot()
    metrics = final_strategy.metrics
    return {
        "variables": variable_count,
        "domain_size": domain_size,
        "initial_facts": len(initial_facts),
        "final_facts": len(final_session.facts),
        "candidate_removals": expected_removals,
        "repeat": repeat,
        "strategy": strategy_name,
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "cycles": snapshot.cycles,
        "activations": snapshot.fired_activation_count,
        "candidate_facts_examined": metrics.candidate_facts,
        "match_attempts": metrics.match_attempts,
        "index_removals": metrics.index_removals,
        "witness_cache_hits": metrics.witness_cache_hits,
        "witness_cache_misses": metrics.witness_cache_misses,
        "witness_cache_invalidations": (
            metrics.witness_cache_invalidations
        ),
        "structural_index_builds": getattr(
            metrics,
            "structural_index_builds",
            0,
        ),
        "structural_index_lookups": getattr(
            metrics,
            "structural_index_lookups",
            0,
        ),
        "adaptive_join_reorders": getattr(
            metrics,
            "adaptive_join_reorders",
            0,
        ),
        "residual_witness_promotions": (
            getattr(metrics, "residual_witness_promotions", 0)
        ),
        "domain_filter_runs": metrics.domain_filter_runs,
        "domain_filter_fallbacks": metrics.domain_filter_fallbacks,
        "domain_filter_selections": metrics.domain_filter_selections,
        "domain_filter_rejections": metrics.domain_filter_rejections,
        "domain_rows_examined": metrics.domain_rows_examined,
        "domain_input_rows": metrics.domain_input_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variables", type=int, default=16)
    parser.add_argument("--domain-size", type=int, default=12)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--strategy",
        choices=("semi-naive", "adaptive", "both"),
        default="both",
    )
    arguments = parser.parse_args()
    if (
        arguments.variables < 2
        or arguments.domain_size < 2
        or arguments.repeat < 1
    ):
        parser.error(
            "--variables and --domain-size must be at least 2; "
            "--repeat must be positive"
        )
    strategy_names = (
        ("semi-naive", "adaptive")
        if arguments.strategy == "both"
        else (arguments.strategy,)
    )
    results = [
        measure(
                arguments.variables,
                arguments.domain_size,
                arguments.repeat,
                strategy_name,
            )
        for strategy_name in strategy_names
    ]
    print(
        json.dumps(
            {"results": results},
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
