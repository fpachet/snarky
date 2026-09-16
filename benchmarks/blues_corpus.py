"""Audit LSDB's selected Blues and build two explicit half-bar corpora.

The source data remain external to Snarky's distributions. The generated compact
research fixture carries its own attribution and licence alongside the JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOTS = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
SUFFIXES = {
    "dominant": "7",
    "minor": "m",
    "major": "",
    "diminished": "dim",
    "half-diminished": "-7b5",
}
SIMPLIFICATION = {
    "dominant": "dominant",
    "minor": "minor",
    "major": "dominant",
    "diminished": "half-diminished",
    "half-diminished": "half-diminished",
}


def chord_symbol(root: int, kind: str) -> str:
    return ROOTS[root % 12] + SUFFIXES[kind]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit_and_extract(source: Path, lsdb_root: Path) -> dict:
    """Validate all numeric transpositions, source hashes, timing and symbols."""
    raw = source.read_bytes()
    data = json.loads(raw)
    sequences = data["sequences"]
    require(len(sequences) == 22, "expected the selected 22 references")
    require(len({s["id"] for s in sequences}) == 22, "duplicate reference id")
    records, changes = [], []
    kinds: Counter[str] = Counter()
    for sequence in sequences:
        identifier = sequence["id"]
        path = (lsdb_root / sequence["source_path"]).resolve()
        require(path.is_relative_to(lsdb_root.resolve()), "source outside LSDB")
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == sequence["source_sha256"],
            f"source hash mismatch: {identifier}",
        )
        require(
            sequence["time_signature"] == "4/4"
            and sequence["bar_count"] == len(sequence["bars"]) == 12
            and sequence["duration_quarter_notes"] == 48,
            f"invalid chorus dimensions: {identifier}",
        )
        raw_chords, reduced_chords, positions = [], [], []
        tonic = sequence["tonic_pc"]
        for number, bar in enumerate(sequence["bars"], 1):
            require(bar["bar"] == number, f"bar numbering: {identifier}")
            cursor = 1
            for chord in bar["chords"]:
                kind = chord["source_notation"]["kind"]
                require(kind in SUFFIXES, f"unsupported chord kind: {kind}")
                require(not chord["source_notation"]["degrees"], "unhandled degrees")
                require(chord["bass_pc"] is None, "unhandled slash chord")
                require(
                    chord["beat"] == cursor
                    and cursor in (1, 3)
                    and chord["duration"] in (2, 4),
                    f"not an exact half-bar grid: {identifier}/{number}",
                )
                cursor += chord["duration"]
                require(cursor <= 5, f"bar overflow: {identifier}/{number}")
                root = (chord["root_pc"] - tonic) % 12
                require(root == chord["root_pc_in_C"], "root transposition mismatch")
                require(
                    chord["bass_pc_in_C"] is None
                    and set(chord["pitch_classes_in_C"])
                    == {(p - tonic) % 12 for p in chord["pitch_classes"]},
                    "pitch/bass transposition mismatch",
                )
                symbol = chord_symbol(root, kind)
                require(symbol == chord["symbol_in_C"], "symbol transposition mismatch")
                reduced_kind = SIMPLIFICATION[kind]
                reduced = chord_symbol(root, reduced_kind)
                kinds[kind] += 1
                for half in range(int(chord["duration"] / 2)):
                    position = len(raw_chords) + 1
                    raw_chords.append(symbol)
                    reduced_chords.append(reduced)
                    positions.append([root, kind])
                    if kind != reduced_kind:
                        changes.append(
                            {
                                "sequence": identifier,
                                "position": position,
                                "bar": number,
                                "beat": chord["beat"] + half * 2,
                                "from": symbol,
                                "to": reduced,
                            }
                        )
            require(cursor == 5, f"incomplete bar: {identifier}/{number}")
        require(len(raw_chords) == 24, "expected 24 half-bar chords")
        records.append(
            {
                "id": identifier,
                "title": sequence["title"],
                "transcription_id": sequence["transcription_id"],
                "source_tonic": sequence["tonic"],
                "source_bar_range": sequence["source_bar_range"],
                "source_sha256": sequence["source_sha256"],
                "source_notes": sequence["notes"],
                "weight": 1,
                "source_faithful": raw_chords,
                "paper_style_proposed": reduced_chords,
                "root_kind": positions,
            }
        )
    return {
        "schema_version": 1,
        "source": "LSDB data/reference/omnibook_blues/references.json",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "licence": "CC BY-NC-SA 2.0 UK; see LICENCE.txt",
        "selection": (
            "22 first complete choruses; alternate takes retained, weight 1 each"
        ),
        "transposition": "Inputs already in C; verify, do not transpose a second time",
        "historical_identity": (
            "Not established; source harmonies differ from paper examples"
        ),
        "simplification_status": (
            "Proposed map for review, not a recovered historical mapping"
        ),
        "simplification": SIMPLIFICATION,
        "source_segment_kinds": dict(sorted(kinds.items())),
        "changes": changes,
        "sequences": records,
    }


def training_sequences(corpus: dict, variant: str, *, all_keys: bool) -> tuple:
    """Retain tune/take multiplicity and optionally augment by all 12 keys once."""
    if variant not in ("source_faithful", "paper_style_proposed"):
        raise ValueError("unknown corpus variant")
    result = []
    for record in corpus["sequences"]:
        for shift in range(12 if all_keys else 1):
            result.append(
                tuple(
                    chord_symbol(
                        root + shift,
                        SIMPLIFICATION[kind]
                        if variant == "paper_style_proposed"
                        else kind,
                    )
                    for root, kind in record["root_kind"]
                )
            )
    return tuple(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lsdb-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_dir = args.lsdb_root / "data/reference/omnibook_blues"
    corpus = audit_and_extract(source_dir / "references.json", args.lsdb_root)
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / "corpus.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite versioned corpus: {output}")
    output.write_text(json.dumps(corpus, indent=2) + "\n")
    (args.output / "LICENCE.txt").write_bytes((source_dir / "LICENCE.txt").read_bytes())
    print(
        json.dumps(
            {
                "references": len(corpus["sequences"]),
                "changed_half_bars": len(corpus["changes"]),
                "source_sha256": corpus["source_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
