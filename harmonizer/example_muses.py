"""Harmonize an example MuSES soprano and export MIDI and MusicXML."""

from __future__ import annotations

import argparse
from pathlib import Path

from muses.base.temporals import TemporalCollection, TemporalNote
from muses.io import write_musicxml

from snarky import ChoiceTraversal

from .muses_harmonizer import MusesHarmonization, harmonize_temporal_collection
from .note_solver import HarmonicPlanDegree

LONG_HARMONIC_RHYTHM = (0, 1, 2, 3, 4, 4, 5, 6)
DIATONIC_MELODY = (
    60,
    62,
    64,
    65,
    67,
    69,
    71,
    72,
    76,
    74,
    72,
    69,
    65,
    69,
    71,
    72,
)
MELODIC_ROLE_MELODY = (
    72,
    74,
    67,
    72,
    64,
    69,
    71,
    72,
    67,
    72,
    71,
    72,
    65,
    69,
    71,
    72,
)
MELODIC_ROLE_STARTS = (
    0.0,
    1.0,
    2.0,
    4.0,
    5.0,
    6.0,
    8.0,
    12.0,
    15.0,
    16.0,
    17.0,
    18.0,
    20.0,
    22.0,
    24.0,
    28.0,
)
MELODIC_ROLE_DURATIONS = (
    1.0,
    1.0,
    2.0,
    1.0,
    1.0,
    2.0,
    1.0,
    3.0,
    1.0,
    1.0,
    1.0,
    2.0,
    2.0,
    2.0,
    4.0,
    4.0,
)
MELODIC_ROLE_HARMONIC_PLAN: tuple[HarmonicPlanDegree | None, ...] = (
    None,
    "I",
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    "V",
    None,
    None,
    None,
    None,
    None,
    None,
)
EXTENDED_MELODY = (
    67,
    76,
    69,
    72,
    72,
    76,
    65,
    69,
    67,
    64,
    69,
    72,
    74,
    69,
    71,
    72,
)
EXTENDED_HARMONIC_RHYTHM = (
    0,
    0,
    1,
    1,
    2,
    2,
    3,
    3,
    4,
    4,
    5,
    5,
    6,
    6,
    7,
    8,
)


def build_example_soprano() -> TemporalCollection:
    """Return a two-measure soprano with a perfect cadence."""

    return TemporalCollection(
        name="soprano_donne",
        temporals=(
            TemporalNote(72, 0.0, 2.0, velocity=72, midi_channel=0),
            TemporalNote(69, 2.0, 2.0, velocity=70, midi_channel=0),
            TemporalNote(71, 4.0, 2.0, velocity=74, midi_channel=0),
            TemporalNote(72, 6.0, 2.0, velocity=76, midi_channel=0),
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=8.0,
    )


def build_long_example_soprano() -> TemporalCollection:
    """Return a four-measure soprano with one prolonged harmonic event."""

    return TemporalCollection(
        name="soprano_long_donne",
        temporals=tuple(
            TemporalNote(
                pitch,
                index * 2.0,
                2.0,
                velocity=70 + index,
                midi_channel=0,
            )
            for index, pitch in enumerate((72, 74, 76, 72, 65, 69, 71, 72))
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=16.0,
    )


def build_extended_example_soprano() -> TemporalCollection:
    """Return an eight-measure soprano whose harmony is inferred by rules."""

    return TemporalCollection(
        name="soprano_extended_donne",
        temporals=tuple(
            TemporalNote(
                pitch,
                index * 2.0,
                2.0,
                velocity=68 + index,
                midi_channel=0,
            )
            for index, pitch in enumerate(EXTENDED_MELODY)
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=32.0,
    )


def build_diatonic_example_soprano() -> TemporalCollection:
    """Return an eight-measure soprano using every C-major scale degree."""

    return TemporalCollection(
        name="soprano_diatonic_donne",
        temporals=tuple(
            TemporalNote(
                pitch,
                index * 2.0,
                2.0,
                velocity=70 + index,
                midi_channel=0,
            )
            for index, pitch in enumerate(DIATONIC_MELODY)
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=32.0,
    )


def build_melodic_role_example_soprano() -> TemporalCollection:
    """Return eight bars exhibiting four declaratively selected roles."""

    return TemporalCollection(
        name="soprano_melodic_roles_donne",
        temporals=tuple(
            TemporalNote(
                pitch,
                start,
                duration,
                velocity=70 + index,
                midi_channel=0,
            )
            for index, (pitch, start, duration) in enumerate(
                zip(
                    MELODIC_ROLE_MELODY,
                    MELODIC_ROLE_STARTS,
                    MELODIC_ROLE_DURATIONS,
                    strict=True,
                )
            )
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=32.0,
    )


def generate_example(
    output_directory: Path,
    *,
    long_form: bool = False,
    extended_form: bool = False,
    diatonic_form: bool = False,
    melodic_roles_form: bool = False,
) -> tuple[MusesHarmonization, Path, Path]:
    """Run Snarky and write both formats through the MuSES API."""

    if sum((long_form, extended_form, diatonic_form, melodic_roles_form)) > 1:
        raise ValueError(
            "long_form, extended_form, diatonic_form, and melodic_roles_form "
            "are mutually exclusive"
        )
    harmonic_rhythm: tuple[int, ...] | None
    harmonic_plan: tuple[HarmonicPlanDegree | None, ...] | None
    if melodic_roles_form:
        soprano = build_melodic_role_example_soprano()
        stem = "snarky_melodic_roles_satb"
        harmonic_rhythm = None
        harmonic_plan = MELODIC_ROLE_HARMONIC_PLAN
        traversal = ChoiceTraversal.DEPTH_FIRST
        title = "Melodic roles selected declaratively by Snarky"
    elif diatonic_form:
        soprano = build_diatonic_example_soprano()
        stem = "snarky_diatonic_soprano_satb"
        harmonic_rhythm = None
        harmonic_plan = None
        traversal = ChoiceTraversal.DEPTH_FIRST
        title = "Diatonic soprano harmonized note by note by Snarky"
    elif extended_form:
        soprano = build_extended_example_soprano()
        stem = "snarky_extended_soprano_satb"
        harmonic_rhythm = EXTENDED_HARMONIC_RHYTHM
        harmonic_plan = None
        traversal = ChoiceTraversal.DEPTH_FIRST
        title = "Extended soprano harmonized by Snarky"
    elif long_form:
        soprano = build_long_example_soprano()
        stem = "snarky_long_soprano_satb"
        harmonic_rhythm = LONG_HARMONIC_RHYTHM
        harmonic_plan = None
        traversal = ChoiceTraversal.BEST_FIRST
        title = "Long soprano harmonized by Snarky"
    else:
        soprano = build_example_soprano()
        stem = "snarky_soprano_satb"
        harmonic_rhythm = None
        harmonic_plan = None
        traversal = ChoiceTraversal.BEST_FIRST
        title = "Soprano harmonized by Snarky"
    result = harmonize_temporal_collection(
        soprano,
        given_voice="soprano",
        harmonic_rhythm=harmonic_rhythm,
        harmonic_plan=harmonic_plan,
        traversal=traversal,
        piece_name=stem,
        title=title,
        composer="Snarky / MuSES",
    )[0]

    output_directory.mkdir(parents=True, exist_ok=True)
    midi_path = output_directory / f"{stem}.mid"
    musicxml_path = output_directory / f"{stem}.musicxml"
    result.piece.save_midi(midi_path)
    write_musicxml(result.piece, musicxml_path)
    return result, midi_path, musicxml_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path(__file__).with_name("generated"),
    )
    form = parser.add_mutually_exclusive_group()
    form.add_argument(
        "--long",
        action="store_true",
        help="generate the four-measure, eight-note example",
    )
    form.add_argument(
        "--diatonic",
        "--ornamented",
        dest="diatonic",
        action="store_true",
        help=(
            "generate the eight-measure C-major example with one harmony per note "
            "(--ornamented is a compatibility alias)"
        ),
    )
    form.add_argument(
        "--roles",
        action="store_true",
        help="generate the eight-measure metric-aware melodic-role example",
    )
    form.add_argument(
        "--extended",
        action="store_true",
        help="generate the eight-measure, sixteen-note melody-only example",
    )
    arguments = parser.parse_args()
    result, midi_path, musicxml_path = generate_example(
        arguments.output_directory,
        long_form=arguments.long,
        extended_form=arguments.extended,
        diatonic_form=arguments.diatonic,
        melodic_roles_form=arguments.roles,
    )

    print(f"{result.piece.title}:")
    for voice in result.piece.melodies:
        pitches = [note.pitch for note in voice.temporals]
        print(f"  {voice.name:8s} {pitches}")
    print("  chords  ", list(result.symbolic.chords))
    print("  inversions", list(result.symbolic.inversions))
    print("  metric strengths", list(result.symbolic.metric_strengths))
    print("  metric levels", list(result.symbolic.metric_levels))
    print("  note durations", list(result.symbolic.note_durations))
    print("  melodic roles", list(result.symbolic.melodic_roles))
    print(
        "  voice continuations",
        [
            (
                continuation.voice,
                continuation.previous_position,
                continuation.position,
            )
            for continuation in result.symbolic.voice_continuations
        ],
    )
    print(f"MIDI:     {midi_path}")
    print(f"MusicXML: {musicxml_path}")
    print(
        "rules:",
        ", ".join(
            dict.fromkeys(
                event.rule_group for event in result.symbolic.inference_events
            )
        ),
    )


if __name__ == "__main__":
    main()
