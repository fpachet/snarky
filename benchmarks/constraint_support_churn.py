"""Measure residual existential witnesses under repeated support removal."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from typing import cast

from snarky import (
    Atom,
    Fact,
    FactDelta,
    FiniteSequence,
    IndexedInstantiationStrategy,
    Triple,
    parse_rules,
)
from snarky.instantiation.compiled import CompiledBlock
from snarky.instantiation.indexed import FactIndex
from snarky.substitutions import BindingFrame


class _WithoutResidualWitnesses(IndexedInstantiationStrategy):
    @staticmethod
    def _can_retain_residual_witnesses(
        block: CompiledBlock,
        index: FactIndex,
        frame: BindingFrame,
    ) -> bool:
        del block, index, frame
        return False


def _fact(subject: str, relation: str, object_: object) -> Fact:
    term = object_ if isinstance(object_, Atom | FiniteSequence) else Atom(
        str(object_)
    )
    return Fact(Triple(Atom(subject), Atom(relation), term))


def _initial_facts(
    domain_size: int,
    support_stride: int,
) -> tuple[Fact, ...]:
    values = tuple(Atom(f"value-{index}") for index in range(domain_size))
    return (
        _fact("query", "seed", "yes"),
        *(
            _fact("domain", "candidate", value)
            for value in values
        ),
        *(
            _fact(
                "relation",
                "allows",
                FiniteSequence((Atom("key"), value)),
            )
            for index, value in enumerate(values)
            if index % support_stride == 0
        ),
    )


def _measure_strategy(
    strategy_type: type[IndexedInstantiationStrategy],
    domain_size: int,
    support_stride: int,
    steps: int,
    repeat: int,
) -> dict[str, object]:
    rule = parse_rules(
        """
        RULE retain_supported
        WHEN
            (query seed yes)
            EXISTS
                (domain candidate $value)
                (relation allows SEQ[key $value])
            END_EXISTS
        THEN
            ADD (query supported yes)
        END
        """
    )[0]
    initial = _initial_facts(domain_size, support_stride)
    supported_values = {
        fact.entity.object.elements[1]
        for fact in initial
        if (
            isinstance(fact.entity, Triple)
            and fact.entity.subject == Atom("relation")
            and isinstance(fact.entity.object, FiniteSequence)
        )
    }
    candidates = tuple(
        fact
        for fact in initial
        if (
            isinstance(fact.entity, Triple)
            and fact.entity.subject == Atom("domain")
            and fact.entity.relation == Atom("candidate")
            and fact.entity.object in supported_values
        )
    )
    samples: list[float] = []
    final_strategy = None
    for _ in range(repeat):
        strategy = strategy_type()
        facts = initial
        strategy.instantiate(rule, facts)
        started = time.perf_counter()
        for revision, removed in enumerate(candidates[:steps], start=1):
            facts = tuple(fact for fact in facts if fact != removed)
            strategy.invalidate(frozenset((removed,)))
            activations = strategy.instantiate(
                rule,
                facts,
                FactDelta(
                    removed=frozenset((removed,)),
                    revision=revision,
                ),
            )
            if len(activations) != 1:
                raise AssertionError("a residual support should remain")
        samples.append(time.perf_counter() - started)
        final_strategy = strategy
    assert final_strategy is not None
    metrics = final_strategy.metrics
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "witness_cache_hits": metrics.witness_cache_hits,
        "witness_cache_misses": metrics.witness_cache_misses,
        "witness_cache_invalidations": (
            metrics.witness_cache_invalidations
        ),
        "residual_witness_promotions": (
            metrics.residual_witness_promotions
        ),
        "match_attempts": metrics.match_attempts,
    }


def measure(
    domain_size: int,
    support_stride: int,
    steps: int,
    repeat: int,
) -> dict[str, object]:
    without = _measure_strategy(
        _WithoutResidualWitnesses,
        domain_size,
        support_stride,
        steps,
        repeat,
    )
    with_residuals = _measure_strategy(
        IndexedInstantiationStrategy,
        domain_size,
        support_stride,
        steps,
        repeat,
    )
    return {
        "domain_size": domain_size,
        "support_stride": support_stride,
        "removal_steps": steps,
        "repeat": repeat,
        "without_residual_witnesses": without,
        "with_residual_witnesses": with_residuals,
        "speedup": (
            cast(float, without["median_seconds"])
            / cast(float, with_residuals["median_seconds"])
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain-size", type=int, default=1024)
    parser.add_argument("--support-stride", type=int, default=8)
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--repeat", type=int, default=7)
    arguments = parser.parse_args()
    if (
        arguments.domain_size < 3
        or arguments.support_stride < 1
        or arguments.steps < 1
        or arguments.steps
        >= arguments.domain_size // arguments.support_stride
        or arguments.repeat < 1
    ):
        parser.error(
            "--domain-size must be at least 3; --steps must be positive "
            "and leave one supported value; --support-stride and "
            "--repeat must be positive"
        )
    print(
        json.dumps(
            measure(
                arguments.domain_size,
                arguments.support_stride,
                arguments.steps,
                arguments.repeat,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
