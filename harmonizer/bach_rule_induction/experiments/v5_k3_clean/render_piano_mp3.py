#!/usr/bin/env python3
"""Render a MIDI file with an explicit acoustic-grand-piano program."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import mido

DEFAULT_SOUNDFONT = Path(
    "/Applications/MuseScore 4.app/Contents/Resources/sound/MS Basic.sf3"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("midi", type=Path)
    parser.add_argument("mp3", type=Path)
    parser.add_argument("--soundfont", type=Path, default=DEFAULT_SOUNDFONT)
    parser.add_argument("--gain", type=float, default=0.7)
    return parser.parse_args()


def force_acoustic_grand_piano(source: Path, target: Path) -> int:
    midi = mido.MidiFile(source)
    rewritten = 0
    for track in midi.tracks:
        for index, message in enumerate(track):
            if message.type == "program_change":
                track[index] = message.copy(program=0)
                rewritten += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    midi.save(target)
    return rewritten


def main() -> int:
    args = parse_args()
    if not args.soundfont.exists():
        raise FileNotFoundError(f"Piano soundfont not found: {args.soundfont}")
    args.mp3.parent.mkdir(parents=True, exist_ok=True)
    piano_midi = args.mp3.with_suffix(".mid")
    rewritten = force_acoustic_grand_piano(args.midi, piano_midi)
    with tempfile.TemporaryDirectory(prefix="snarky-piano-") as directory:
        wav = Path(directory) / "render.wav"
        subprocess.run(
            [
                "fluidsynth",
                "-ni",
                "-g",
                str(args.gain),
                "-R",
                "0",
                "-C",
                "0",
                str(args.soundfont),
                str(piano_midi),
                "-F",
                str(wav),
                "-r",
                "44100",
            ],
            check=True,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(args.mp3),
            ],
            check=True,
        )
    provenance = {
        "source_midi": str(args.midi.resolve()),
        "piano_midi": str(piano_midi.resolve()),
        "mp3": str(args.mp3.resolve()),
        "soundfont": str(args.soundfont.resolve()),
        "midi_bank": 0,
        "midi_program_zero_based": 0,
        "instrument": "Acoustic Grand Piano",
        "program_changes_rewritten": rewritten,
        "sample_rate": 44100,
    }
    provenance_path = args.mp3.with_suffix(".render.json")
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[piano-render] rewrote {rewritten} program changes to program 0")
    print(f"[piano-render] wrote {piano_midi}")
    print(f"[piano-render] wrote {args.mp3}")
    print(f"[piano-render] wrote {provenance_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
