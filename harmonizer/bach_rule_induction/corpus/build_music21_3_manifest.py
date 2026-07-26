"""Reconstruct the exact Music21 3.1.0 corpus selection reported by DeepBach."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import music21
from music21 import converter, corpus

EXPECTED_VERSION = "3.1.0"
EXPECTED_API_PATHS = 402
EXPECTED_FOUR_PART = 357
EXPECTED_MONOPHONIC_PARTS = 354
EXPECTED_ARTICLE_PIECES = 352
EXPECTED_AUGMENTED_PIECES = 2503
EXPECTED_PART_NAMES = ("Soprano", "Alto", "Tenor", "Bass")

SOURCE_ARCHIVE = {
    "filename": "music21-3.1.0.tar.gz",
    "url": (
        "https://files.pythonhosted.org/packages/21/58/"
        "5bcb9e27561e205f61645a9a8f5898d8dbb92a9fc26a76230ef51b436375/"
        "music21-3.1.0.tar.gz"
    ),
    "size_bytes": 47_077_984,
    "sha256": "73a33407459e59fc5cfa7ea268088e5e10db9354e01ceceb2295d56373b937d2",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def music21_version() -> str:
    return str(getattr(music21, "VERSION_STR", music21.__version__))


def inspect_score(path: Path, corpus_root: Path) -> tuple[dict[str, Any], Any]:
    relative_path = path.resolve().relative_to(corpus_root.resolve())
    record: dict[str, Any] = {
        "id": relative_path.with_suffix("").as_posix(),
        "source_path": relative_path.as_posix(),
        "sha256": sha256(path),
    }

    try:
        score = converter.parse(str(path))
    except Exception as error:  # pragma: no cover - recorded for corpus audits
        record.update(
            {
                "included": False,
                "exclusion_reason": "parse_error",
                "error": f"{type(error).__name__}: {error}",
            }
        )
        return record, None

    part_names = [part.partName for part in score.parts]
    record.update(
        {
            "part_count": len(score.parts),
            "part_names": part_names,
            "duration_quarter_length": str(score.duration.quarterLength),
        }
    )
    if len(score.parts) != 4:
        record.update(
            {
                "included": False,
                "exclusion_reason": "part_count_not_4",
            }
        )
        return record, None

    voice_pitches: list[list[int]] = []
    try:
        for part in score.parts:
            pitches = [event.pitch.midi for event in part.flat.notes]
            min(pitches)
            max(pitches)
            voice_pitches.append(pitches)
    except AttributeError:
        record.update(
            {
                "included": False,
                "exclusion_reason": "simultaneous_notes_in_part",
            }
        )
        return record, None
    except ValueError:
        record.update(
            {
                "included": False,
                "exclusion_reason": "empty_part",
            }
        )
        return record, None

    record["voice_pitch_ranges"] = [
        {"min": min(pitches), "max": max(pitches)}
        for pitches in voice_pitches
    ]
    if tuple(part_names) != EXPECTED_PART_NAMES:
        record.update(
            {
                "included": False,
                "exclusion_reason": "part_labels_not_explicit_satb",
            }
        )
        return record, voice_pitches

    record["included"] = True
    record["exclusion_reason"] = None
    return record, voice_pitches


def build_manifest() -> dict[str, Any]:
    version = music21_version()
    if version != EXPECTED_VERSION:
        raise RuntimeError(
            f"music21 {EXPECTED_VERSION} is required, found {version}"
        )

    package_root = Path(music21.__file__).resolve().parent
    corpus_root = package_root / "corpus"
    source_paths = [
        Path(path)
        for path in corpus.getBachChorales(fileExtensions="xml")
    ]

    records: list[dict[str, Any]] = []
    included_pitches: dict[str, list[list[int]]] = {}
    monophonic_count = 0
    for path in source_paths:
        record, voice_pitches = inspect_score(path, corpus_root)
        records.append(record)
        if voice_pitches is not None:
            monophonic_count += 1
        if record["included"]:
            included_pitches[str(record["id"])] = voice_pitches

    records.sort(key=lambda record: str(record["id"]))
    global_ranges = [
        {
            "min": min(
                min(voices[voice])
                for voices in included_pitches.values()
            ),
            "max": max(
                max(voices[voice])
                for voices in included_pitches.values()
            ),
        }
        for voice in range(4)
    ]

    augmented_count = 0
    for record in records:
        if not record["included"]:
            continue
        voices = included_pitches[str(record["id"])]
        minimum = max(
            global_ranges[voice]["min"] - min(voices[voice])
            for voice in range(4)
        )
        maximum = min(
            global_ranges[voice]["max"] - max(voices[voice])
            for voice in range(4)
        )
        count = maximum - minimum + 1
        record["allowed_transpositions"] = {
            "min_semitones": minimum,
            "max_semitones": maximum,
            "count": count,
        }
        augmented_count += count

    four_part_count = sum(
        record.get("part_count") == 4 for record in records
    )
    included_count = sum(bool(record["included"]) for record in records)
    summary = {
        "historical_api_paths": len(source_paths),
        "four_part_scores": four_part_count,
        "four_part_scores_without_simultaneous_notes": monophonic_count,
        "article_selection": included_count,
        "augmented_transpositions": augmented_count,
    }
    expected = {
        "historical_api_paths": EXPECTED_API_PATHS,
        "four_part_scores": EXPECTED_FOUR_PART,
        "four_part_scores_without_simultaneous_notes": (
            EXPECTED_MONOPHONIC_PARTS
        ),
        "article_selection": EXPECTED_ARTICLE_PIECES,
        "augmented_transpositions": EXPECTED_AUGMENTED_PIECES,
    }
    if summary != expected:
        raise RuntimeError(
            "historical corpus reconstruction mismatch: "
            f"expected {expected}, found {summary}"
        )

    return {
        "schema_version": 1,
        "source": {
            "package": "music21",
            "version": version,
            "archive": SOURCE_ARCHIVE,
            "deepbach_filter_revision": (
                "18e3c961a835f82dc248892da8454baf80404b31"
            ),
        },
        "selection": {
            "rule": (
                "four parts, no simultaneous notes in a part, and explicit "
                "Soprano/Alto/Tenor/Bass labels"
            ),
            "note": (
                "The explicit SATB-label criterion operationally reconstructs "
                "the article's removal of instrumental parts: it excludes "
                "exactly bwv140.7 and bwv253 and reproduces both published "
                "counts, 352 originals and 2503 transpositions."
            ),
        },
        "summary": summary,
        "global_voice_pitch_ranges": global_ranges,
        "pieces": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("manifest.music21-3.1.0.json"),
    )
    args = parser.parse_args()

    manifest = build_manifest()
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        "reconstructed DeepBach article corpus: "
        f"{manifest['summary']['article_selection']} pieces, "
        f"{manifest['summary']['augmented_transpositions']} transpositions"
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
