"""Compare Snarky and CLAIRE4 on the Talarian filter benchmark."""

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
RESULT_PREFIX = "SNARKY_CLAIRE_FILTER_RESULT "
DEFAULT_SIZES = (100, 1_000, 5_000)
SLOT_NAMES = ("n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "n0")
COUNTER_NAMES = (
    "nc1",
    "nc2",
    "nc3",
    "nc4",
    "nc5",
    "nc6",
    "nc7",
    "nc8",
    "nc9",
    "nc0",
)
_CLAIRE_RESULT = re.compile(
    r"size=(?P<size>\d+) "
    r"preparation_ns=(?P<preparation_ns>\d+) "
    r"inference_ns=(?P<inference_ns>\d+) "
    r"rule_firings=(?P<rule_firings>\d+) "
    r"outputs=(?P<outputs>\d+) "
    r"checksum=(?P<checksum>\d+)"
)


def _rule_text() -> str:
    return "\n\n".join(
        f"""\
RULE filter_{slot}
WHEN
    ($frame {slot} $value)
    $value > 0
THEN
    ADD ($frame {counter} 4)
END"""
        for slot, counter in zip(SLOT_NAMES, COUNTER_NAMES, strict=True)
    )


FILTER_RULES = parse_rules(_rule_text())


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
        raise ValueError("CLAIRE output has no filter result marker")
    match = _CLAIRE_RESULT.fullmatch(marker)
    if match is None:
        raise ValueError(f"malformed CLAIRE filter marker: {marker!r}")
    parsed = {
        key: int(value)
        for key, value in match.groupdict().items()
    }
    parsed["preparation_seconds"] = (
        parsed.pop("preparation_ns") / 1_000_000_000.0
    )
    parsed["seconds"] = parsed.pop("inference_ns") / 1_000_000_000.0
    return parsed


def build_filter_facts(size: int) -> tuple[Fact, ...]:
    """Build ten positive input facts for each frame."""

    return tuple(
        Fact(
            Triple(
                Atom(f"frame_{frame}"),
                Atom(slot),
                Number(frame),
            )
        )
        for frame in range(1, size + 1)
        for slot in SLOT_NAMES
    )


def validate_metrics(size: int, sample: dict[str, Any]) -> None:
    """Reject executions that did not perform the normalized workload."""

    expected = 10 * size
    if sample["rule_firings"] != expected:
        raise RuntimeError(
            f"expected {expected} rule firings, "
            f"received {sample['rule_firings']}"
        )
    if sample["outputs"] != expected:
        raise RuntimeError(
            f"expected {expected} outputs, "
            f"received {sample['outputs']}"
        )
    if sample["checksum"] != 40 * size:
        raise RuntimeError(
            f"expected checksum {40 * size}, "
            f"received {sample['checksum']}"
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
    size: int,
    repeat: int,
    *,
    use_event_rules: bool = True,
) -> dict[str, Any]:
    """Measure one assume-and-saturate update per positive input."""

    samples: list[dict[str, Any]] = []
    for _ in range(repeat):
        strategy = SemiNaiveInstantiationStrategy(
            use_event_rules=use_event_rules,
        )
        engine = ForwardEngine(
            FILTER_RULES,
            strategy=strategy,
            limits=EngineLimits(max_facts=20 * size + 1),
        )
        preparation_started = perf_counter()
        facts = build_filter_facts(size)
        session = engine.create_session(())
        preparation_elapsed = perf_counter() - preparation_started

        inference_started = perf_counter()
        outputs = 0
        for fact in facts:
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
                raise RuntimeError("Snarky emitted an invalid filter delta")
            outputs += len(events)
        inference_elapsed = perf_counter() - inference_started
        sample: dict[str, Any] = {
            "seconds": inference_elapsed,
            "preparation_seconds": preparation_elapsed,
            "rule_firings": strategy.metrics.activations_produced,
            "outputs": outputs,
            "checksum": 4 * outputs,
            "match_attempts": strategy.metrics.match_attempts,
            "candidate_facts": strategy.metrics.candidate_facts,
            "activations_produced": strategy.metrics.activations_produced,
            "rule_evaluations": (
                session.agenda_metrics.rule_recomputations
            ),
            "rule_skips": session.agenda_metrics.rule_reuses,
            "event_rule_evaluations": (
                strategy.metrics.event_rule_evaluations
            ),
            "event_rule_candidates": (
                strategy.metrics.event_rule_candidates
            ),
        }
        validate_metrics(size, sample)
        samples.append(sample)
    return _summarize(
        samples,
        (
            "rule_firings",
            "outputs",
            "checksum",
            "match_attempts",
            "candidate_facts",
            "activations_produced",
            "rule_evaluations",
            "rule_skips",
            "event_rule_evaluations",
            "event_rule_candidates",
        ),
    )


def measure_claire(
    size: int,
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
        f"benchmark({size})",
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
        if parsed["size"] != size:
            raise RuntimeError(
                f"CLAIRE returned size {parsed['size']} for size {size}"
            )
        validate_metrics(size, parsed)
        samples.append(parsed)
    return _summarize(
        samples,
        ("rule_firings", "outputs", "checksum"),
    )


def run(
    sizes: tuple[int, ...],
    repeat: int,
    *,
    engine: str,
    claire_root: Path | None = None,
    claire_binary: Path | None = None,
    use_event_rules: bool = True,
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
    for size in sizes:
        case: dict[str, Any] = {"size": size}
        if engine in {"both", "snarky"}:
            case["snarky"] = measure_snarky(
                size,
                repeat,
                use_event_rules=use_event_rules,
            )
        if selected_binary is not None:
            case["claire_interpreted"] = measure_claire(
                size,
                repeat,
                selected_binary,
            )
        results.append(case)

    payload: dict[str, Any] = {
        "benchmark": "claire_talarian_filter",
        "protocol": {
            "frames": "N independent frames",
            "rules": 10,
            "input_facts_per_frame": 10,
            "expected_rule_firings_per_frame": 10,
            "expected_outputs_per_frame": 10,
            "scheduling": "one input update followed by saturation",
            "dependency_scheduling": (
                "only rules affected by each fact mutation are evaluated"
            ),
            "event_rule_specialization": use_event_rules,
            "timing_scope": {
                "snarky": "ten assume-and-run_group updates per frame",
                "claire": "ten rule-triggering slot updates per frame",
            },
            "preparation_scope": {
                "snarky": "input fact construction and empty session creation",
                "claire": "FILTER_FRAME object construction",
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
        "--sizes",
        nargs="+",
        type=int,
        default=DEFAULT_SIZES,
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
        "--disable-event-rules",
        action="store_true",
    )
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")
    if any(size < 1 for size in arguments.sizes):
        parser.error("--sizes must be positive")
    rendered = json.dumps(
        run(
            tuple(arguments.sizes),
            arguments.repeat,
            engine=arguments.engine,
            claire_root=arguments.claire_root,
            claire_binary=arguments.claire_binary,
            use_event_rules=not arguments.disable_event_rules,
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
