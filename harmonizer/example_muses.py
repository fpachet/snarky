"""Harmonize an example MuSES soprano and export MIDI and MusicXML."""

from __future__ import annotations

import argparse
from pathlib import Path

from muses.base.temporals import TemporalCollection, TemporalNote
from muses.io import write_musicxml

from .muses_harmonizer import MusesHarmonization, harmonize_temporal_collection

LONG_HARMONIC_RHYTHM = (0, 1, 2, 3, 4, 4, 5, 6)


def build_example_soprano() -> TemporalCollection:
    """Return a two-measure soprano designed for an I-ii-V7-I cadence."""

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


def generate_example(
    output_directory: Path,
    *,
    long_form: bool = False,
) -> tuple[MusesHarmonization, Path, Path]:
    """Run Snarky and write both formats through the MuSES API."""

    soprano = (
        build_long_example_soprano()
        if long_form
        else build_example_soprano()
    )
    stem = (
        "snarky_long_soprano_satb"
        if long_form
        else "snarky_soprano_satb"
    )
    result = harmonize_temporal_collection(
        soprano,
        given_voice="soprano",
        harmonic_rhythm=LONG_HARMONIC_RHYTHM if long_form else None,
        piece_name=stem,
        title=(
            "Long soprano harmonized by Snarky"
            if long_form
            else "Soprano harmonized by Snarky"
        ),
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
    parser.add_argument(
        "--long",
        action="store_true",
        help="generate the four-measure, eight-note example",
    )
    arguments = parser.parse_args()
    result, midi_path, musicxml_path = generate_example(
        arguments.output_directory,
        long_form=arguments.long,
    )

    print(f"{result.piece.title}:")
    for voice in result.piece.melodies:
        pitches = [note.pitch for note in voice.temporals]
        print(f"  {voice.name:8s} {pitches}")
    print("  chords  ", list(result.symbolic.chords))
    print("  inversions", list(result.symbolic.inversions))
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
