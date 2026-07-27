"""Compare Snarky and CLAIRE4 on streamed triangle closure."""

from __future__ import annotations

import argparse
import json
import platform
import re
import statistics
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.claire_support import (
    PROJECT_ROOT,
    git_commit,
    git_dirty,
    resolve_claire_binary,
    resolve_claire_root,
)
from snarky import (
    Atom,
    EngineLimits,
    Fact,
    FactMutationKind,
    ForwardEngine,
    Number,
    SemiNaiveInstantiationStrategy,
    Triple,
    parse_rules,
)

CLAIRE_SOURCE = Path(__file__).with_suffix(".cl")
RESULT_PREFIX = "SNARKY_CLAIRE_TRIANGLE_RESULT "
WIDTH = 8
DEFAULT_GROUPS = (2, 5, 10, 25)
_CLAIRE_RESULT = re.compile(
    r"groups=(?P<groups>\d+) "
    r"width=(?P<width>\d+) "
    r"preparation_ns=(?P<preparation_ns>\d+) "
    r"inference_ns=(?P<inference_ns>\d+) "
    r"rule_firings=(?P<rule_firings>\d+) "
    r"outputs=(?P<outputs>\d+) "
    r"checksum=(?P<checksum>\d+)"
)

TRIANGLE_RULES = parse_rules(
    """
    RULE close_triangle
    WHEN
        ($hub left $left)
        ($hub right $right)
        $left != $right
        ($left edge $right)
    THEN
        ADD ($hub triangle SEQ[$left $right])
    END
    """
)


def expected_outputs(group_count: int) -> int:
    return group_count * WIDTH * WIDTH


def expected_checksum(group_count: int) -> int:
    return WIDTH * WIDTH * group_count * (group_count + 1) // 2


def build_membership_facts(group_count: int) -> tuple[Fact, ...]:
    """Build the hub-to-left and hub-to-right relations."""

    return tuple(
        Fact(
            Triple(
                Number(group),
                Atom(side),
                Atom(f"{side}_{group}_{item}"),
            )
        )
        for group in range(1, group_count + 1)
        for side in ("left", "right")
        for item in range(1, WIDTH + 1)
    )


def build_closing_edges(group_count: int) -> tuple[Fact, ...]:
    """Build every streamed left-to-right edge."""

    return tuple(
        Fact(
            Triple(
                Atom(f"left_{group}_{left}"),
                Atom("edge"),
                Atom(f"right_{group}_{right}"),
            )
        )
        for group in range(1, group_count + 1)
        for left in range(1, WIDTH + 1)
        for right in range(1, WIDTH + 1)
    )


def parse_claire_result(output: str) -> dict[str, Any]:
    """Parse the stable marker emitted amid CLAIRE's runtime banner."""

    marker = next(
        (
            line[len(RESULT_PREFIX) :]
            for line in output.splitlines()
            if line.startswith(RESULT_PREFIX)
        ),
        None,
    )
    if marker is None:
        raise ValueError("CLAIRE output has no triangle result marker")
    match = _CLAIRE_RESULT.fullmatch(marker)
    if match is None:
        raise ValueError(f"malformed CLAIRE triangle marker: {marker!r}")
    parsed = {
        key: int(value)
        for key, value in match.groupdict().items()
    }
    parsed["preparation_seconds"] = (
        parsed.pop("preparation_ns") / 1_000_000_000.0
    )
    parsed["seconds"] = parsed.pop("inference_ns") / 1_000_000_000.0
    return parsed


def validate_metrics(group_count: int, sample: dict[str, Any]) -> None:
    """Reject executions that differ from the shared graph protocol."""

    expected = expected_outputs(group_count)
    if sample["width"] != WIDTH:
        raise RuntimeError(
            f"expected width {WIDTH}, received {sample['width']}"
        )
    if sample["rule_firings"] != expected:
        raise RuntimeError(
            f"expected {expected} rule firings, "
            f"received {sample['rule_firings']}"
        )
    if sample["outputs"] != expected:
        raise RuntimeError(
            f"expected {expected} outputs, received {sample['outputs']}"
        )
    checksum = expected_checksum(group_count)
    if sample["checksum"] != checksum:
        raise RuntimeError(
            f"expected checksum {checksum}, received {sample['checksum']}"
        )


def _summarize(
    samples: list[dict[str, Any]],
    counters: Sequence[str],
) -> dict[str, Any]:
    if not samples:
        raise ValueError("at least one sample is required")
    stable = {key: samples[0][key] for key in counters}
    for sample in samples[1:]:
        for key, expected in stable.items():
            if sample[key] != expected:
                raise RuntimeError(
                    f"non-deterministic {key}: "
                    f"{sample[key]!r} != {expected!r}"
                )
    seconds = [float(sample["seconds"]) for sample in samples]
    preparation = [
        float(sample["preparation_seconds"]) for sample in samples
    ]
    median_seconds = statistics.median(seconds)
    return {
        "median_seconds": median_seconds,
        "min_seconds": min(seconds),
        "max_seconds": max(seconds),
        "median_rule_firings_per_second": (
            stable["rule_firings"] / median_seconds
        ),
        "median_preparation_seconds": statistics.median(preparation),
        "min_preparation_seconds": min(preparation),
        "max_preparation_seconds": max(preparation),
        **stable,
        "runs": samples,
    }


def measure_snarky(
    group_count: int,
    repeat: int,
    *,
    use_partial_join_memory: bool = True,
) -> dict[str, Any]:
    """Measure one assume-and-saturate update per closing edge."""

    samples: list[dict[str, Any]] = []
    for _ in range(repeat):
        strategy = SemiNaiveInstantiationStrategy(
            use_partial_join_memory=use_partial_join_memory,
        )
        engine = ForwardEngine(
            TRIANGLE_RULES,
            strategy=strategy,
            limits=EngineLimits(max_facts=144 * group_count + 1),
        )
        preparation_started = perf_counter()
        membership = build_membership_facts(group_count)
        closing_edges = build_closing_edges(group_count)
        session = engine.create_session(membership)
        session.run_group(
            engine.default_group,
            materialize_result=False,
        )
        preparation_elapsed = perf_counter() - preparation_started

        strategy.metrics.reset()
        before_evaluations = session.agenda_metrics.rule_recomputations
        before_skips = session.agenda_metrics.rule_reuses
        outputs = 0
        checksum = 0
        inference_started = perf_counter()
        for edge in closing_edges:
            session.assume(edge)
            cursor = session.event_cursor()
            session.run_group(
                engine.default_group,
                materialize_result=False,
            )
            events = session.events_after(cursor)
            if events is None or any(
                event.kind is not FactMutationKind.ADD for event in events
            ):
                raise RuntimeError("Snarky emitted an invalid triangle delta")
            outputs += len(events)
            for event in events:
                entity = event.fact.entity
                if (
                    not isinstance(entity, Triple)
                    or entity.relation != Atom("triangle")
                    or not isinstance(entity.subject, Number)
                    or not isinstance(entity.subject.value, int)
                ):
                    raise RuntimeError(
                        f"unexpected triangle output: {event.fact!r}"
                    )
                checksum += entity.subject.value
        inference_elapsed = perf_counter() - inference_started
        sample: dict[str, Any] = {
            "groups": group_count,
            "width": WIDTH,
            "seconds": inference_elapsed,
            "preparation_seconds": preparation_elapsed,
            "rule_firings": strategy.metrics.activations_produced,
            "outputs": outputs,
            "checksum": checksum,
            "match_attempts": strategy.metrics.match_attempts,
            "candidate_facts": strategy.metrics.candidate_facts,
            "rule_evaluations": (
                session.agenda_metrics.rule_recomputations
                - before_evaluations
            ),
            "rule_skips": (
                session.agenda_metrics.rule_reuses - before_skips
            ),
            "partial_join_builds": strategy.metrics.partial_join_builds,
            "partial_join_updates": strategy.metrics.partial_join_updates,
            "partial_join_bypasses": strategy.metrics.partial_join_bypasses,
        }
        validate_metrics(group_count, sample)
        samples.append(sample)
    return _summarize(
        samples,
        (
            "groups",
            "width",
            "rule_firings",
            "outputs",
            "checksum",
            "match_attempts",
            "candidate_facts",
            "rule_evaluations",
            "rule_skips",
            "partial_join_builds",
            "partial_join_updates",
            "partial_join_bypasses",
        ),
    )


def measure_claire(
    group_count: int,
    repeat: int,
    binary: Path,
    *,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = (
        subprocess.run
    ),
) -> dict[str, Any]:
    """Measure CLAIRE using timers inside the already-loaded source."""

    command = (
        str(binary),
        "-n",
        "-f",
        str(CLAIRE_SOURCE),
        "-e",
        f"benchmark({group_count})",
    )
    samples: list[dict[str, Any]] = []
    for _ in range(repeat):
        completed = run_command(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        parsed = parse_claire_result(completed.stdout)
        if parsed["groups"] != group_count:
            raise RuntimeError(
                f"CLAIRE returned {parsed['groups']} groups "
                f"for {group_count}"
            )
        validate_metrics(group_count, parsed)
        samples.append(parsed)
    return _summarize(
        samples,
        (
            "groups",
            "width",
            "rule_firings",
            "outputs",
            "checksum",
        ),
    )


def run(
    group_counts: tuple[int, ...],
    repeat: int,
    *,
    engine: str,
    claire_root: Path | None = None,
    claire_binary: Path | None = None,
    use_partial_join_memory: bool = True,
) -> dict[str, Any]:
    """Run selected engines and return one machine-readable payload."""

    selected_root: Path | None = None
    selected_binary: Path | None = None
    if engine in {"both", "claire"}:
        selected_root = resolve_claire_root(claire_root)
        selected_binary = resolve_claire_binary(
            selected_root,
            claire_binary,
        )

    results: list[dict[str, Any]] = []
    for group_count in group_counts:
        case: dict[str, Any] = {
            "group_count": group_count,
            "width": WIDTH,
            "expected_outputs": expected_outputs(group_count),
            "expected_checksum": expected_checksum(group_count),
        }
        if engine in {"both", "snarky"}:
            case["snarky"] = measure_snarky(
                group_count,
                repeat,
                use_partial_join_memory=use_partial_join_memory,
            )
        if selected_binary is not None:
            case["claire_interpreted"] = measure_claire(
                group_count,
                repeat,
                selected_binary,
            )
        results.append(case)

    payload: dict[str, Any] = {
        "benchmark": "claire_triangle_closure",
        "protocol": {
            "groups": "N independent hub/left/right groups",
            "width": WIDTH,
            "prepared_memberships_per_group": 2 * WIDTH,
            "streamed_edges_per_group": WIDTH * WIDTH,
            "expected_outputs_per_group": WIDTH * WIDTH,
            "partial_join_memory": use_partial_join_memory,
            "scheduling": "one closing edge followed by saturation",
            "logical_equivalence": (
                "both engines validate firings, outputs, and hub checksum"
            ),
            "timing_scope": {
                "snarky": "assume-and-run_group for every closing edge",
                "claire": "rule-triggering outgoing-set additions",
            },
            "preparation_scope": {
                "snarky": (
                    "fact construction, session creation, initial saturation"
                ),
                "claire": "node, hub, and membership-set construction",
            },
        },
        "repeat": repeat,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "snarky_commit": git_commit(PROJECT_ROOT),
        "snarky_dirty": git_dirty(PROJECT_ROOT),
        "results": results,
    }
    if selected_root is not None and selected_binary is not None:
        payload["claire"] = {
            "root": str(selected_root),
            "binary": str(selected_binary),
            "commit": git_commit(selected_root),
            "dirty": git_dirty(selected_root),
            "mode": "interpreted",
        }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--groups",
        nargs="+",
        type=int,
        default=DEFAULT_GROUPS,
    )
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--engine",
        choices=("both", "snarky", "claire"),
        default="both",
    )
    parser.add_argument("--claire-root", type=Path)
    parser.add_argument("--claire-binary", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--disable-partial-join-memory",
        action="store_true",
    )
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")
    if any(group_count < 1 for group_count in arguments.groups):
        parser.error("--groups must be positive")
    rendered = json.dumps(
        run(
            tuple(arguments.groups),
            arguments.repeat,
            engine=arguments.engine,
            claire_root=arguments.claire_root,
            claire_binary=arguments.claire_binary,
            use_partial_join_memory=(
                not arguments.disable_partial_join_memory
            ),
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
