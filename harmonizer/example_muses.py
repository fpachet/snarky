"""Harmonize an example MuSES soprano and export MIDI and MusicXML."""

from __future__ import annotations

import argparse
from pathlib import Path

from muses.base.temporals import TemporalCollection, TemporalNote
from muses.io import write_musicxml

from .muses_harmonizer import MusesHarmonization, harmonize_temporal_collection


def build_example_soprano() -> TemporalCollection:
    """Return a two-measure C-major soprano with a small rhythmic profile."""

    return TemporalCollection(
        name="soprano_donne",
        temporals=(
            TemporalNote(67, 0.0, 1.0, velocity=72, midi_channel=0),
            TemporalNote(64, 1.0, 1.0, velocity=70, midi_channel=0),
            TemporalNote(60, 2.0, 2.0, velocity=68, midi_channel=0),
            TemporalNote(64, 4.0, 1.0, velocity=70, midi_channel=0),
            TemporalNote(67, 5.0, 1.0, velocity=72, midi_channel=0),
            TemporalNote(72, 6.0, 2.0, velocity=76, midi_channel=0),
        ),
        instrument="choir",
        program_change=52,
        melody_type="melody",
        end_beat=8.0,
    )


def generate_example(
    output_directory: Path,
) -> tuple[MusesHarmonization, Path, Path]:
    """Run Snarky and write both formats through the MuSES API."""

    soprano = build_example_soprano()
    result = harmonize_temporal_collection(
        soprano,
        given_voice="soprano",
        piece_name="snarky_soprano_satb",
        title="Soprano harmonisé par Snarky",
        composer="Snarky / MuSES",
    )[0]

    output_directory.mkdir(parents=True, exist_ok=True)
    midi_path = output_directory / "snarky_soprano_satb.mid"
    musicxml_path = output_directory / "snarky_soprano_satb.musicxml"
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
    arguments = parser.parse_args()
    result, midi_path, musicxml_path = generate_example(arguments.output_directory)

    print(f"{result.piece.title}:")
    for voice in result.piece.melodies:
        pitches = [note.pitch for note in voice.temporals]
        print(f"  {voice.name:8s} {pitches}")
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
