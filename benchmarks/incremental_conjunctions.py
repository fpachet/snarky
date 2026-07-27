"""Measure cold and streamed three-premise joins in Snarky."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.claire_support import PROJECT_ROOT, git_commit, git_dirty
from snarky import (
    Atom,
    EngineLimits,
    Fact,
    FactMutationKind,
    ForwardEngine,
    Rule,
    SemiNaiveInstantiationStrategy,
    Triple,
    parse_rules,
)

JOIN_RULES = parse_rules(
    """
    RULE compatible_pair
    WHEN
        ($group left $left)
        ($group right $right)
        ($left compatible $right)
    THEN
        ADD ($left paired $right)
    END
    """
)

BARRIER_JOIN_RULES = parse_rules(
    """
    RULE compatible_pair_after_filter
    WHEN
        ($group left $left)
        ($group right $right)
        $left != $right
        ($left compatible $right)
    THEN
        ADD ($left paired $right)
    END
    """
)


def build_membership_facts(
    group_count: int,
    width: int,
) -> tuple[Fact, ...]:
    """Build left and right membership rows for independent join groups."""

    return tuple(
        fact
        for group_index in range(group_count)
        for side in ("left", "right")
        for item_index in range(width)
        for fact in (
            Fact(
                Triple(
                    Atom(f"group_{group_index}"),
                    Atom(side),
                    Atom(f"{side}_{group_index}_{item_index}"),
                )
            ),
        )
    )


def build_compatibility_facts(
    group_count: int,
    width: int,
) -> tuple[Fact, ...]:
    """Build one compatibility edge for every valid left/right pair."""

    return tuple(
        Fact(
            Triple(
                Atom(f"left_{group_index}_{left_index}"),
                Atom("compatible"),
                Atom(f"right_{group_index}_{right_index}"),
            )
        )
        for group_index in range(group_count)
        for left_index in range(width)
        for right_index in range(width)
    )


def expected_output_facts(
    group_count: int,
    width: int,
) -> frozenset[Fact]:
    """Return the exact logical result expected from the join."""

    return frozenset(
        Fact(
            Triple(
                Atom(f"left_{group_index}_{left_index}"),
                Atom("paired"),
                Atom(f"right_{group_index}_{right_index}"),
            )
        )
        for group_index in range(group_count)
        for left_index in range(width)
        for right_index in range(width)
    )


def _validate_session(
    session_facts: tuple[Fact, ...],
    expected: frozenset[Fact],
    *,
    input_fact_count: int,
) -> None:
    outputs = frozenset(
        fact
        for fact in session_facts
        if (
            isinstance(fact.entity, Triple)
            and fact.entity.relation == Atom("paired")
        )
    )
    if outputs != expected:
        raise RuntimeError(
            f"expected {len(expected)} joined outputs, received {len(outputs)}"
        )
    if len(session_facts) != input_fact_count + len(expected):
        raise RuntimeError("join produced an unexpected working-memory size")


def _summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        raise ValueError("at least one sample is required")
    counters = (
        "outputs",
        "facts",
        "fired_activations",
        "match_attempts",
        "candidate_facts",
        "activations_produced",
        "rule_evaluations",
        "rule_skips",
        "partial_join_builds",
        "partial_join_updates",
        "partial_join_bypasses",
    )
    stable = {counter: samples[0][counter] for counter in counters}
    for sample in samples[1:]:
        for counter, expected in stable.items():
            if sample[counter] != expected:
                raise RuntimeError(
                    f"non-deterministic {counter}: "
                    f"{sample[counter]!r} != {expected!r}"
                )
    seconds = [float(sample["seconds"]) for sample in samples]
    return {
        "median_seconds": statistics.median(seconds),
        "min_seconds": min(seconds),
        "max_seconds": max(seconds),
        **stable,
        "runs": samples,
    }


def measure_cold(
    group_count: int,
    width: int,
    repeat: int,
) -> dict[str, Any]:
    """Measure one full join over an already constructed fact memory."""

    membership = build_membership_facts(group_count, width)
    compatibility = build_compatibility_facts(group_count, width)
    expected = expected_output_facts(group_count, width)
    initial = (*membership, *compatibility)
    samples: list[dict[str, Any]] = []
    for _ in range(repeat):
        strategy = SemiNaiveInstantiationStrategy()
        engine = ForwardEngine(
            JOIN_RULES,
            strategy=strategy,
            limits=EngineLimits(max_facts=2 * len(initial) + 1),
        )
        session = engine.create_session(initial)
        cursor = session.event_cursor()
        started = perf_counter()
        session.run_group(
            engine.default_group,
            materialize_result=False,
        )
        seconds = perf_counter() - started
        events = session.events_after(cursor)
        if events is None or any(
            event.kind is not FactMutationKind.ADD for event in events
        ):
            raise RuntimeError("cold join emitted an invalid mutation delta")
        _validate_session(
            session.facts,
            expected,
            input_fact_count=len(initial),
        )
        snapshot = session.snapshot()
        samples.append(
            {
                "seconds": seconds,
                "outputs": len(events),
                "facts": len(session.facts),
                "fired_activations": snapshot.fired_activation_count,
                "match_attempts": strategy.metrics.match_attempts,
                "candidate_facts": strategy.metrics.candidate_facts,
                "activations_produced": (
                    strategy.metrics.activations_produced
                ),
                "rule_evaluations": (
                    session.agenda_metrics.rule_recomputations
                ),
                "rule_skips": session.agenda_metrics.rule_reuses,
                "partial_join_builds": (
                    strategy.metrics.partial_join_builds
                ),
                "partial_join_updates": (
                    strategy.metrics.partial_join_updates
                ),
                "partial_join_bypasses": (
                    strategy.metrics.partial_join_bypasses
                ),
            }
        )
    return _summarize(samples)


def measure_streamed(
    group_count: int,
    width: int,
    repeat: int,
    *,
    rules: tuple[Rule, ...] = JOIN_RULES,
    use_partial_join_memory: bool = True,
) -> dict[str, Any]:
    """Measure one compatibility addition and saturation per valid pair."""

    membership = build_membership_facts(group_count, width)
    compatibility = build_compatibility_facts(group_count, width)
    expected = expected_output_facts(group_count, width)
    samples: list[dict[str, Any]] = []
    for _ in range(repeat):
        strategy = SemiNaiveInstantiationStrategy(
            use_partial_join_memory=use_partial_join_memory,
        )
        engine = ForwardEngine(
            rules,
            strategy=strategy,
            limits=EngineLimits(
                max_facts=(
                    len(membership) + 2 * len(compatibility) + 1
                )
            ),
        )
        session = engine.create_session(membership)
        session.run_group(
            engine.default_group,
            materialize_result=False,
        )
        strategy.metrics.reset()
        before_evaluations = session.agenda_metrics.rule_recomputations
        before_skips = session.agenda_metrics.rule_reuses
        outputs = 0
        started = perf_counter()
        for fact in compatibility:
            session.assume(fact)
            cursor = session.event_cursor()
            session.run_group(
                engine.default_group,
                materialize_result=False,
            )
            events = session.events_after(cursor)
            if events is None or any(
                event.kind is not FactMutationKind.ADD for event in events
            ):
                raise RuntimeError(
                    "streamed join emitted an invalid mutation delta"
                )
            outputs += len(events)
        seconds = perf_counter() - started
        _validate_session(
            session.facts,
            expected,
            input_fact_count=len(membership) + len(compatibility),
        )
        snapshot = session.snapshot()
        samples.append(
            {
                "seconds": seconds,
                "outputs": outputs,
                "facts": len(session.facts),
                "fired_activations": snapshot.fired_activation_count,
                "match_attempts": strategy.metrics.match_attempts,
                "candidate_facts": strategy.metrics.candidate_facts,
                "activations_produced": (
                    strategy.metrics.activations_produced
                ),
                "rule_evaluations": (
                    session.agenda_metrics.rule_recomputations
                    - before_evaluations
                ),
                "rule_skips": (
                    session.agenda_metrics.rule_reuses - before_skips
                ),
                "partial_join_builds": (
                    strategy.metrics.partial_join_builds
                ),
                "partial_join_updates": (
                    strategy.metrics.partial_join_updates
                ),
                "partial_join_bypasses": (
                    strategy.metrics.partial_join_bypasses
                ),
            }
        )
    return _summarize(samples)


def run(
    group_counts: tuple[int, ...],
    width: int,
    repeat: int,
    *,
    barrier_group_counts: tuple[int, ...] = (),
) -> dict[str, Any]:
    """Run the requested conjunction cases and return a JSON-ready result."""

    return {
        "benchmark": "incremental_conjunctions",
        "protocol": {
            "premises": (
                "($group left $left), ($group right $right), "
                "($left compatible $right)"
            ),
            "expected_outputs": "group_count * width^2",
            "cold": "one saturation over all input facts",
            "streamed": (
                "one compatibility addition followed by saturation"
            ),
            "logical_equivalence": (
                "cold and streamed memories are checked against the exact "
                "expected output set"
            ),
            "barrier": (
                "the optional A/B inserts a bound comparison before the "
                "last fact premise"
            ),
        },
        "repeat": repeat,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "snarky_commit": git_commit(PROJECT_ROOT),
        "snarky_dirty": git_dirty(PROJECT_ROOT),
        "results": [
            {
                "group_count": group_count,
                "width": width,
                "expected_outputs": group_count * width * width,
                "cold": measure_cold(group_count, width, repeat),
                "streamed": measure_streamed(group_count, width, repeat),
            }
            for group_count in group_counts
        ],
        "barrier_results": [
            {
                "group_count": group_count,
                "width": width,
                "expected_outputs": group_count * width * width,
                "memory": measure_streamed(
                    group_count,
                    width,
                    repeat,
                    rules=BARRIER_JOIN_RULES,
                ),
                "generic": measure_streamed(
                    group_count,
                    width,
                    repeat,
                    rules=BARRIER_JOIN_RULES,
                    use_partial_join_memory=False,
                ),
            }
            for group_count in barrier_group_counts
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--groups",
        nargs="+",
        type=int,
        default=(25, 100, 250),
    )
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument(
        "--barrier-groups",
        nargs="*",
        type=int,
        default=(),
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")
    if arguments.width < 1:
        parser.error("--width must be positive")
    if any(group_count < 1 for group_count in arguments.groups):
        parser.error("--groups must be positive")
    if any(group_count < 1 for group_count in arguments.barrier_groups):
        parser.error("--barrier-groups must be positive")
    rendered = json.dumps(
        run(
            tuple(arguments.groups),
            arguments.width,
            arguments.repeat,
            barrier_group_counts=tuple(arguments.barrier_groups),
        ),
        indent=2,
    )
    if arguments.output is None:
        print(rendered)
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(f"{rendered}\n", encoding="utf-8")
        print(arguments.output)


if __name__ == "__main__":
    main()
