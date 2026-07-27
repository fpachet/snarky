"""Benchmark the symbolic harmonizer and its complete MuSES object bridge."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from benchmarks.support import PROJECT_ROOT, git_commit, git_dirty
from harmonizer import (
    MusesFactories,
    harmonize_notes,
    harmonize_temporal_collection,
)
from snarky.integrations import (
    MusesTemporalCollectionCodec,
    MusesTemporalNoteCodec,
)


class BenchmarkNote:
    def __init__(
        self,
        pitch: int,
        start_time: int | float,
        duration: int | float,
        velocity: int = 60,
        midi_channel: int = 0,
    ) -> None:
        self.pitch = pitch
        self.start_beat = start_time
        self.end_beat = start_time + duration
        self.velocity = velocity
        self.midi_channel = midi_channel

    def duration(self) -> int | float:
        return self.end_beat - self.start_beat


class BenchmarkCollection:
    def __init__(
        self,
        name: str = "",
        temporals: Iterable[BenchmarkNote] | None = None,
        *,
        instrument: str = "",
        program_change: int = 0,
        melody_type: str = "",
        end_beat: int | float = 0.0,
    ) -> None:
        self.name = name
        self.temporals = sorted(
            list(temporals or ()),
            key=lambda note: note.start_beat,
        )
        self.instrument = instrument
        self.program_change = program_change
        self.melody_type = melody_type
        self.end_beat = max((end_beat, *(note.end_beat for note in self.temporals)))


class BenchmarkPiece:
    def __init__(
        self,
        name: str = "unnamed",
        title: str = "unknown",
        composer: str = "unknown",
        melodies: Sequence[BenchmarkCollection] | None = None,
        ticks_per_beat: int = 480,
        time_signature: str = "4/4",
        key_signature: str = "C",
        tempo: int = 500_000,
    ) -> None:
        self.name = name
        self.title = title
        self.composer = composer
        self.melodies = list(melodies or ())
        self.ticks_per_beat = ticks_per_beat
        self.time_signature = time_signature
        self.key_signature = key_signature
        self.tempo = tempo


def _measure(
    operation: Callable[[], tuple[int, int]],
    repeat: int,
) -> dict[str, Any]:
    samples: list[float] = []
    counters: tuple[int, int] | None = None
    for _ in range(repeat):
        started = time.perf_counter()
        current = operation()
        samples.append(time.perf_counter() - started)
        if counters is not None and current != counters:
            raise AssertionError("logical counters changed between repetitions")
        counters = current
    assert counters is not None
    return {
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "decisions": counters[0],
        "solutions": counters[1],
    }


def run(repeat: int) -> dict[str, Any]:
    factories = MusesFactories(
        BenchmarkNote,
        BenchmarkCollection,
        BenchmarkPiece,
    )
    codec = MusesTemporalCollectionCodec(
        note_codec=MusesTemporalNoteCodec(factory=BenchmarkNote),
        factory=BenchmarkCollection,
    )
    source = BenchmarkCollection(
        name="benchmark_soprano",
        temporals=(
            BenchmarkNote(72, 0.0, 1.0),
            BenchmarkNote(69, 1.0, 1.0),
            BenchmarkNote(71, 2.0, 1.0),
            BenchmarkNote(72, 3.0, 1.0),
        ),
        instrument="choir",
    )

    def symbolic() -> tuple[int, int]:
        solutions = harmonize_notes((72, 69, 71, 72), max_solutions=1)
        return len(solutions[0].decisions), len(solutions)

    def object_bridge() -> tuple[int, int]:
        solutions = harmonize_temporal_collection(
            source,
            metric_levels=(3, 1, 2, 1),
            factories=factories,
            codec=codec,
            max_solutions=1,
        )
        return len(solutions[0].symbolic.decisions), len(solutions)

    return {
        "benchmark": "muses_harmonizer",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": repeat,
        "snarky_commit": git_commit(PROJECT_ROOT),
        "snarky_dirty": git_dirty(PROJECT_ROOT),
        "symbolic_note_input": _measure(symbolic, repeat),
        "muses_object_round_trip": _measure(object_bridge, repeat),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=5)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("repeat must be positive")
    print(json.dumps(run(arguments.repeat), indent=2))


if __name__ == "__main__":
    main()
