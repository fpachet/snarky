#!/usr/bin/env python3
"""Audit train-only coverage of deterministic, named harmonic statuses."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import k3
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v20_harmonic_status_coverage_train.json"
DEFAULT_REPORT = FACTOR_BASE / "V20_HARMONIC_STATUS_COVERAGE_TRAIN.md"

CHORD_TEMPLATES: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("major_triad", (0, 4, 7)),
    ("minor_triad", (0, 3, 7)),
    ("diminished_triad", (0, 3, 6)),
    ("augmented_triad", (0, 4, 8)),
    ("dominant_seventh", (0, 4, 7, 10)),
    ("major_seventh", (0, 4, 7, 11)),
    ("minor_seventh", (0, 3, 7, 10)),
    ("half_diminished_seventh", (0, 3, 6, 10)),
    ("diminished_seventh", (0, 3, 6, 9)),
    ("minor_major_seventh", (0, 3, 7, 11)),
)
TRIAD_QUALITIES = frozenset(
    {"major_triad", "minor_triad", "diminished_triad", "augmented_triad"}
)
TEMPLATE_ORDER = {name: index for index, (name, _) in enumerate(CHORD_TEMPLATES)}


@dataclass(frozen=True)
class HarmonicStatus:
    root_pc: int
    root_degree: int
    quality: str
    inversion: int


def analyze_pitch_classes(
    pitches: tuple[int, ...],
    *,
    bass_pitch: int,
    tonic_pc: int,
    qualities: frozenset[str] | None = None,
) -> tuple[HarmonicStatus, ...]:
    """Return every exact named analysis; preserve symmetric ambiguities."""

    pitch_classes = frozenset(int(pitch) % 12 for pitch in pitches)
    bass_pc = int(bass_pitch) % 12
    analyses = []
    for quality, intervals in CHORD_TEMPLATES:
        if qualities is not None and quality not in qualities:
            continue
        for root_pc in range(12):
            expected = frozenset((root_pc + interval) % 12 for interval in intervals)
            if pitch_classes != expected:
                continue
            bass_interval = (bass_pc - root_pc) % 12
            if bass_interval not in intervals:
                continue
            analyses.append(
                HarmonicStatus(
                    root_pc=root_pc,
                    root_degree=(root_pc - tonic_pc) % 12,
                    quality=quality,
                    inversion=intervals.index(bass_interval),
                )
            )
    return tuple(
        sorted(
            analyses,
            key=lambda row: (
                TEMPLATE_ORDER[row.quality],
                row.root_pc,
                row.inversion,
            ),
        )
    )


def triad_plus_one_analyses(
    pitches: tuple[int, ...],
    *,
    bass_pitch: int,
    tonic_pc: int,
) -> tuple[tuple[int, HarmonicStatus], ...]:
    """Find exact triads after removing one pitch class from an unknown block."""

    pitch_classes = frozenset(int(pitch) % 12 for pitch in pitches)
    if len(pitch_classes) != 4:
        return ()
    analyses = []
    for foreign_pc in sorted(pitch_classes):
        reduced = tuple(sorted(pitch_classes - {foreign_pc}))
        reduced_bass = (
            bass_pitch
            if int(bass_pitch) % 12 in reduced
            else min(reduced)
        )
        for status in analyze_pitch_classes(
            reduced,
            bass_pitch=reduced_bass,
            tonic_pc=tonic_pc,
            qualities=TRIAD_QUALITIES,
        ):
            if int(bass_pitch) % 12 not in reduced:
                status = replace(status, inversion=-1)
            analyses.append((foreign_pc, status))
    return tuple(analyses)


def _piece_audit(task: tuple[str, str]) -> dict[str, Any]:
    piece_id, score_path = task
    lattice = k3.extract_piece_lattice(Path(score_path), piece_id)
    counts: Counter[str] = Counter()
    qualities: Counter[str] = Counter()
    degrees: Counter[str] = Counter()
    inversions: Counter[str] = Counter()
    for index, block in enumerate(lattice.blocks):
        strength = "strong" if int(lattice.metric_levels[index]) >= 2 else "weak"
        counts["blocks"] += 1
        counts[f"{strength}_blocks"] += 1
        pitches = tuple(map(int, block))
        analyses = analyze_pitch_classes(
            pitches,
            bass_pitch=int(block[3]),
            tonic_pc=lattice.tonic_pc,
        )
        if analyses:
            counts["exact_named"] += 1
            counts[f"{strength}_exact_named"] += 1
            if len(analyses) == 1:
                counts["exact_unique"] += 1
                counts[f"{strength}_exact_unique"] += 1
                status = analyses[0]
                degrees[str(status.root_degree)] += 1
                inversions[f"{status.quality}:{status.inversion}"] += 1
            else:
                counts["exact_ambiguous"] += 1
                counts[f"{strength}_exact_ambiguous"] += 1
            quality = analyses[0].quality
            qualities[quality] += 1
            counts[
                "exact_triad" if quality in TRIAD_QUALITIES else "exact_seventh"
            ] += 1
            continue
        plus_one = triad_plus_one_analyses(
            pitches,
            bass_pitch=int(block[3]),
            tonic_pc=lattice.tonic_pc,
        )
        if plus_one:
            counts["triad_plus_one"] += 1
            counts[f"{strength}_triad_plus_one"] += 1
            if len(plus_one) == 1:
                counts["triad_plus_one_unique"] += 1
        else:
            counts["unclassified"] += 1
            counts[f"{strength}_unclassified"] += 1
    return {
        "piece_id": piece_id,
        "counts": dict(counts),
        "qualities": dict(qualities),
        "degrees": dict(degrees),
        "inversions": dict(inversions),
    }


def _aggregate(piece_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    qualities: Counter[str] = Counter()
    degrees: Counter[str] = Counter()
    inversions: Counter[str] = Counter()
    quality_pieces: defaultdict[str, set[str]] = defaultdict(set)
    for row in piece_rows:
        counts.update(row["counts"])
        qualities.update(row["qualities"])
        degrees.update(row["degrees"])
        inversions.update(row["inversions"])
        for quality, count in row["qualities"].items():
            if count:
                quality_pieces[quality].add(row["piece_id"])

    def rate(numerator: str, denominator: str) -> float:
        return counts[numerator] / counts[denominator]

    return {
        "counts": dict(sorted(counts.items())),
        "coverage": {
            "exact_named": rate("exact_named", "blocks"),
            "exact_unique": rate("exact_unique", "blocks"),
            "exact_ambiguous": rate("exact_ambiguous", "blocks"),
            "strong_exact_named": rate("strong_exact_named", "strong_blocks"),
            "weak_exact_named": rate("weak_exact_named", "weak_blocks"),
            "triad_plus_one": rate("triad_plus_one", "blocks"),
            "strong_triad_plus_one": rate(
                "strong_triad_plus_one",
                "strong_blocks",
            ),
            "weak_triad_plus_one": rate("weak_triad_plus_one", "weak_blocks"),
            "named_or_triad_plus_one": (
                (counts["exact_named"] + counts["triad_plus_one"])
                / counts["blocks"]
            ),
        },
        "qualities": {
            quality: {
                "blocks": count,
                "piece_support": len(quality_pieces[quality]),
            }
            for quality, count in sorted(
                qualities.items(),
                key=lambda item: (-item[1], item[0]),
            )
        },
        "unique_root_degrees": dict(
            sorted(degrees.items(), key=lambda item: int(item[0]))
        ),
        "unique_inversions": dict(sorted(inversions.items())),
    }


def _markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    coverage = summary["coverage"]
    counts = summary["counts"]
    lines = [
        "# V20 — couverture train des statuts harmoniques nommés",
        "",
        "Cet audit précède toute induction. Il mesure seulement si un vocabulaire",
        "déterministe de fondamentales, qualités et renversements couvre le corpus.",
        "Aucun poids n'est appris et le test réservé n'est pas chargé.",
        "",
        "## Couverture",
        "",
        f"- Chorals de train : `{result['experiment']['pieces']}`.",
        f"- Blocs verticaux : `{counts['blocks']}`.",
        f"- Accord complet nommé : `{100 * coverage['exact_named']:.2f} %`.",
        f"- Analyse unique : `{100 * coverage['exact_unique']:.2f} %`.",
        f"- Analyse symétriquement ambiguë : "
        f"`{100 * coverage['exact_ambiguous']:.2f} %`.",
        f"- Couverture exacte sur temps fort : "
        f"`{100 * coverage['strong_exact_named']:.2f} %`.",
        f"- Couverture exacte sur temps faible : "
        f"`{100 * coverage['weak_exact_named']:.2f} %`.",
        f"- Triade plus une classe étrangère : "
        f"`{100 * coverage['triad_plus_one']:.2f} %`.",
        f"- Accord nommé ou triade plus une étrangère : "
        f"`{100 * coverage['named_or_triad_plus_one']:.2f} %`.",
        "",
        "## Qualités reconnues exactement",
        "",
        "| Qualité | Blocs | Support en chorals |",
        "|---|---:|---:|",
    ]
    for quality, row in summary["qualities"].items():
        lines.append(
            f"| `{quality}` | {row['blocks']} | {row['piece_support']} |"
        )
    lines.extend(
        [
            "",
            "Les analyses ambiguës, notamment les accords symétriques, ne reçoivent",
            "pas arbitrairement une fondamentale. La prochaine décision doit",
            "comparer cette couverture au coût du nouveau vocabulaire avant de",
            "construire la grammaire V20.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument(
        "--split-role",
        choices=("train", "validation"),
        default="train",
    )
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    piece_ids = list(splits[args.split_role])
    if args.split_role == "train":
        piece_ids = sorted(piece_ids, key=generative._stable_order)
    if args.max_pieces is not None:
        piece_ids = piece_ids[: args.max_pieces]
    tasks = [
        (piece_id, str(generative._score_path(args.scores, piece_id)))
        for piece_id in piece_ids
    ]
    if args.workers == 1:
        piece_rows = list(map(_piece_audit, tasks))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            piece_rows = list(executor.map(_piece_audit, tasks))
    result = {
        "experiment": {
            "id": "K3-V20-HARMONIC-STATUS-COVERAGE-1",
            "status": "COVERAGE_AUDIT_ONLY",
            "split_role": args.split_role,
            "pieces": len(piece_rows),
            "workers": args.workers,
            "test_loaded": False,
            "weights_learned": False,
        },
        "templates": [
            {"quality": quality, "intervals": list(intervals)}
            for quality, intervals in CHORD_TEMPLATES
        ],
        "summary": _aggregate(piece_rows),
        "pieces": piece_rows,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v20-coverage] pieces={len(piece_rows)} "
        f"exact={result['summary']['coverage']['exact_named']:.3f} "
        f"plus_one={result['summary']['coverage']['triad_plus_one']:.3f}",
        flush=True,
    )
    print(f"[v20-coverage] wrote {args.output}", flush=True)
    print(f"[v20-coverage] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
