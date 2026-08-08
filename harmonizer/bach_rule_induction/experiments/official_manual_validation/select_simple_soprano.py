#!/usr/bin/env python3
"""Select a simple training-split soprano for homorhythmic harmonization."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from harmonizer.official_manual import _part_events, _xml_root, parse_musicxml_satb

HERE = Path(__file__).resolve().parent
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE.parent / "v5_k3_clean/work/scores"
DEFAULT_OUTPUT = HERE / "results/simple_soprano_selection.json"
DEFAULT_REPORT = HERE / "results/SIMPLE_SOPRANO_SELECTION.md"
SIMPLE_DURATIONS = frozenset((Fraction(1, 2), Fraction(1), Fraction(2), Fraction(4)))
MAJOR_SCALE = frozenset((0, 2, 4, 5, 7, 9, 11))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _score_path(scores: Path, piece_id: str) -> Path:
    stem = piece_id.rsplit("/", 1)[-1]
    for suffix in (".mxl", ".musicxml", ".xml"):
        path = scores / f"{stem}{suffix}"
        if path.exists():
            return path
    raise FileNotFoundError(piece_id)


def _profile(path: Path, piece_id: str) -> dict[str, Any]:
    parsed = parse_musicxml_satb(path)
    root = _xml_root(path)
    soprano_events = tuple(
        event
        for event in _part_events(root.findall("part")[0])
        if event.pitch is not None and event.attack
    )
    pitches = tuple(int(event.pitch) for event in soprano_events)
    durations = tuple(event.duration for event in soprano_events)
    motions = tuple(
        right - left for left, right in zip(pitches[:-1], pitches[1:], strict=True)
    )
    nonzero = sum(motion != 0 for motion in motions)
    step_count = sum(0 < abs(motion) <= 2 for motion in motions)
    chromatic = sum(
        (pitch - parsed.tonic_pc) % 12 not in MAJOR_SCALE for pitch in pitches
    )
    mode = (root.findtext(".//part/measure/attributes/key/mode") or "major").lower()
    beats = root.findtext(".//part/measure/attributes/time/beats")
    beat_type = root.findtext(".//part/measure/attributes/time/beat-type")
    return {
        "piece_id": piece_id,
        "score": str(path.resolve()),
        "mode": mode,
        "meter": f"{beats}/{beat_type}",
        "attacks": len(pitches),
        "unique_pitches": len(set(pitches)),
        "duration_values": sorted({str(value) for value in durations}),
        "simple_durations_only": all(value in SIMPLE_DURATIONS for value in durations),
        "chromatic_notes": chromatic,
        "chromatic_rate": 0.0 if not pitches else chromatic / len(pitches),
        "maximum_leap": max((abs(value) for value in motions), default=0),
        "step_rate": 0.0 if nonzero == 0 else step_count / nonzero,
    }


def _selection_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["mode"] != "major",
        not row["simple_durations_only"],
        row["chromatic_rate"],
        row["maximum_leap"] > 7,
        abs(row["attacks"] - 32),
        -row["step_rate"],
        row["piece_id"],
    )


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    profiles = sorted(
        (
            _profile(_score_path(args.scores, piece_id), piece_id)
            for piece_id in splits["train"]
        ),
        key=_selection_key,
    )
    eligible = [
        row
        for row in profiles
        if row["mode"] == "major"
        and row["simple_durations_only"]
        and 20 <= row["attacks"] <= 48
        and row["chromatic_rate"] <= 0.05
        and row["maximum_leap"] <= 7
    ]
    if not eligible:
        raise ValueError("No soprano satisfies the preregistered simplicity filter")
    selected = eligible[0]
    payload = {
        "id": "OFFICIAL-MANUAL-SIMPLE-SOPRANO-SELECTION-1",
        "status": "TRAIN_ONLY_FROZEN_SELECTION",
        "test_loaded": False,
        "selection_filter": {
            "split": "train251",
            "mode": "major",
            "allowed_durations_in_quarter_lengths": ["1/2", "1", "2", "4"],
            "minimum_attacks": 20,
            "maximum_attacks": 48,
            "maximum_chromatic_rate": 0.05,
            "maximum_leap": 7,
        },
        "selected": selected,
        "top_ten": eligible[:10],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report = [
        "# Sélection d'un soprano simple",
        "",
        "La sélection utilise exclusivement les 251 chorals de train.",
        "",
        f"- Pièce : `{selected['piece_id']}`.",
        f"- Attaques : `{selected['attacks']}`.",
        f"- Durées : `{selected['duration_values']}` noires.",
        f"- Chromatisme : `{100 * selected['chromatic_rate']:.2f} %`.",
        f"- Saut maximal : `{selected['maximum_leap']}` demi-tons.",
        f"- Mouvement conjoint : `{100 * selected['step_rate']:.2f} %`.",
        "",
        "Aucune information des voix inférieures ne participe au classement.",
    ]
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"[simple-soprano] selected {selected['piece_id']}")
    print(f"[simple-soprano] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
