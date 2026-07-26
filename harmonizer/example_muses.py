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
DIATONIC_MELODY = (72, 74, 76, 67, 65, 69, 71, 72)
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
    """Return a four-measure soprano with one harmonic decision per note."""

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
        end_beat=16.0,
    )


def generate_example(
    output_directory: Path,
    *,
    long_form: bool = False,
    extended_form: bool = False,
    diatonic_form: bool = False,
) -> tuple[MusesHarmonization, Path, Path]:
    """Run Snarky and write both formats through the MuSES API."""

    if sum((long_form, extended_form, diatonic_form)) > 1:
        raise ValueError(
            "long_form, extended_form, and diatonic_form are mutually exclusive"
        )
    harmonic_rhythm: tuple[int, ...] | None
    harmonic_plan: tuple[HarmonicPlanDegree | None, ...] | None
    if diatonic_form:
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
            "generate the four-measure example with one harmony per note "
            "(--ornamented is a compatibility alias)"
        ),
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
    )

    print(f"{result.piece.title}:")
    for voice in result.piece.melodies:
        pitches = [note.pitch for note in voice.temporals]
        print(f"  {voice.name:8s} {pitches}")
    print("  chords  ", list(result.symbolic.chords))
    print("  inversions", list(result.symbolic.inversions))
    print("  melodic roles", list(result.symbolic.melodic_roles))
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
