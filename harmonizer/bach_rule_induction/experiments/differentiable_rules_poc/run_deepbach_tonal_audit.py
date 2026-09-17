#!/usr/bin/env python3
"""Audit the frozen tonal rule in reproducible DeepBach generations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import run_poc as base

SLUR_SYMBOL = "__"
REST_SYMBOLS = {"rest", "START", "END"}


def load_deepbach_dataset(deepbach_root: Path) -> Any:
    compat_root = deepbach_root / "compat/keras3"
    sys.path.insert(0, str(compat_root))
    from deepbach_compat import load_historical_dataset

    return load_historical_dataset()


def note_name_to_midi(note_name: str) -> int | None:
    if note_name in REST_SYMBOLS:
        return None
    match = re.fullmatch(r"([A-Ga-g])([#b-]*)(-?\d+)", note_name)
    if match is None:
        raise ValueError(f"Unsupported DeepBach note name: {note_name}")
    letter, accidentals, octave_text = match.groups()
    pitch_class = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }[letter.upper()]
    pitch_class += accidentals.count("#")
    pitch_class -= accidentals.count("b") + accidentals.count("-")
    return (int(octave_text) + 1) * 12 + pitch_class


def decode_sequence(
    sequence: np.ndarray,
    index2notes: list[dict[int, str]],
) -> tuple[np.ndarray, np.ndarray]:
    if sequence.ndim != 2 or sequence.shape[1] != 4:
        raise ValueError(f"Expected time × 4 sequence, got {sequence.shape}")
    sounding = np.full(sequence.shape, -1, dtype=np.int16)
    attacks = np.zeros(sequence.shape, dtype=np.bool_)
    for voice in range(4):
        current: int | None = None
        for time_index, token in enumerate(sequence[:, voice]):
            note_name = index2notes[voice][int(token)]
            if note_name != SLUR_SYMBOL:
                current = note_name_to_midi(note_name)
                attacks[time_index, voice] = True
            sounding[time_index, voice] = -1 if current is None else current
    return sounding, attacks


def relative_signature(pitches: np.ndarray, tonic: int = 0) -> list[int]:
    return sorted({int((pitch - tonic) % 12) for pitch in pitches})


def audit_decoded_sequence(
    sounding: np.ndarray,
    attacks: np.ndarray,
    *,
    tonic: int = 0,
) -> dict[str, Any]:
    rows = []
    alto_attacks = 0
    for time_index in range(1, sounding.shape[0]):
        if not attacks[time_index, 1]:
            continue
        if np.any(sounding[time_index - 1] < 0) or np.any(
            sounding[time_index] < 0
        ):
            continue
        alto_attacks += 1
        source = sounding[time_index - 1]
        target = sounding[time_index]
        proxy = (
            (source[1] - tonic) % 12 == 11
            and (source[3] - tonic) % 12 == 2
            and (target[3] - tonic) % 12 == 4
        )
        if not proxy:
            continue
        resolved_pitch = int(source[1] + 1)
        resolved_target = target.copy()
        resolved_target[1] = resolved_pitch
        exact = relative_signature(source, tonic) == [2, 5, 11] and (
            relative_signature(resolved_target, tonic) == [0, 4, 7]
        )
        resolved = bool(target[1] == resolved_pitch)
        rows.append(
            {
                "time_index": time_index,
                "resolved": resolved,
                "exact_candidate_context": exact,
                "frozen_candidate_strength": 2 if exact else 1,
                "source_signature": relative_signature(source, tonic),
                "observed_target_signature": relative_signature(
                    target,
                    tonic,
                ),
                "resolved_candidate_target_signature": relative_signature(
                    resolved_target,
                    tonic,
                ),
                "source_satb": [int(value) for value in source],
                "target_satb": [int(value) for value in target],
            }
        )
    exact_rows = [row for row in rows if row["exact_candidate_context"]]
    return {
        "eligible_alto_attacks": alto_attacks,
        "proxy_opportunities": len(rows),
        "proxy_resolutions": sum(row["resolved"] for row in rows),
        "proxy_resolution_rate": (
            sum(row["resolved"] for row in rows) / len(rows) if rows else None
        ),
        "exact_opportunities": len(exact_rows),
        "exact_resolutions": sum(row["resolved"] for row in exact_rows),
        "exact_resolution_rate": (
            sum(row["resolved"] for row in exact_rows) / len(exact_rows)
            if exact_rows
            else None
        ),
        "violations": [row for row in rows if not row["resolved"]],
        "rows": rows,
    }


def audit_generation(
    sequence_path: Path,
    index2notes: list[dict[int, str]],
) -> dict[str, Any]:
    sequence = np.load(sequence_path, allow_pickle=False)
    sounding, attacks = decode_sequence(sequence, index2notes)
    run_path = sequence_path.with_name("run.json")
    manifest = (
        json.loads(run_path.read_text(encoding="utf-8"))
        if run_path.exists()
        else None
    )
    return {
        "sequence": str(sequence_path.resolve()),
        "sequence_sha256": base.sha256_file(sequence_path),
        "run_manifest": str(run_path.resolve()) if run_path.exists() else None,
        "run": manifest,
        "audit": audit_decoded_sequence(sounding, attacks),
    }


def aggregate(generations: list[dict[str, Any]]) -> dict[str, Any]:
    audits = [record["audit"] for record in generations]
    proxy_opportunities = sum(
        audit["proxy_opportunities"] for audit in audits
    )
    proxy_resolutions = sum(audit["proxy_resolutions"] for audit in audits)
    exact_opportunities = sum(
        audit["exact_opportunities"] for audit in audits
    )
    exact_resolutions = sum(audit["exact_resolutions"] for audit in audits)
    return {
        "generation_count": len(generations),
        "eligible_alto_attacks": sum(
            audit["eligible_alto_attacks"] for audit in audits
        ),
        "proxy_opportunities": proxy_opportunities,
        "proxy_resolutions": proxy_resolutions,
        "proxy_resolution_rate": (
            proxy_resolutions / proxy_opportunities
            if proxy_opportunities
            else None
        ),
        "exact_opportunities": exact_opportunities,
        "exact_resolutions": exact_resolutions,
        "exact_resolution_rate": (
            exact_resolutions / exact_opportunities
            if exact_opportunities
            else None
        ),
        "violation_count": sum(
            len(audit["violations"]) for audit in audits
        ),
    }


def markdown_report(result: dict[str, Any]) -> str:
    aggregate_record = result["aggregate"]
    bach = result["bach_test_reference"]

    def ratio(numerator: int, denominator: int) -> str:
        return f"{numerator}/{denominator}" if denominator else "0/0"

    bach_proxy = ratio(
        bach["proxy_resolutions"],
        bach["proxy_opportunities"],
    )
    bach_exact = ratio(
        bach["exact_resolutions"],
        bach["exact_opportunities"],
    )
    deepbach_proxy = ratio(
        aggregate_record["proxy_resolutions"],
        aggregate_record["proxy_opportunities"],
    )
    deepbach_exact = ratio(
        aggregate_record["exact_resolutions"],
        aggregate_record["exact_opportunities"],
    )
    lines = [
        "# POC V3.9 — audit de générations DeepBach",
        "",
        "## Portée",
        "",
        "- Générations Keras 3 avec poids Keras 2 historiques inchangés.",
        "- Compatibilité opérationnelle ; comparaison TensorFlow 1.1 en attente.",
        "- Métadonnées générées en do majeur.",
        "- Audit sur les attaques d'alto, sans réparation Snarky.",
        "",
        "## Comparaison",
        "",
        "| Corpus | Proxy résolu | Noyau exact résolu |",
        "|---|---:|---:|",
        f"| Bach test gelé | {bach_proxy} | {bach_exact} |",
        f"| DeepBach généré | {deepbach_proxy} | {deepbach_exact} |",
        "",
        (
            f"Violations DeepBach observées : "
            f"`{aggregate_record['violation_count']}`."
        ),
        "",
    ]
    if aggregate_record["proxy_opportunities"] < 5:
        lines.extend(
            [
                "Le support généré est insuffisant pour une comparaison de taux.",
                "Le résultat sert d'audit de cas, pas d'estimation statistique.",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = base.experiment_root()
    project_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deepbach-root",
        type=Path,
        default=project_root.parent / "deepbach-reference",
    )
    parser.add_argument(
        "--sequence",
        type=Path,
        action="append",
        required=True,
    )
    parser.add_argument(
        "--bach-test-result",
        type=Path,
        default=root / "results/v3_8_frozen_harmonic_test.json",
    )
    parser.add_argument("--results-dir", type=Path, default=root / "results")
    parser.add_argument("--output-stem", default="v3_9_deepbach_tonal_audit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    deepbach_root = args.deepbach_root.resolve()
    dataset = load_deepbach_dataset(deepbach_root)
    generations = [
        audit_generation(path.resolve(), dataset.index2notes)
        for path in args.sequence
    ]
    bach_result_path = args.bach_test_result.resolve()
    bach_result = json.loads(bach_result_path.read_text(encoding="utf-8"))
    bach_coverage = bach_result["coverage"]["test"]
    proxy = bach_coverage["TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4"]
    exact = bach_coverage["TONAL_EXACT_VII6_TO_I6"]
    result = {
        "schema_version": 1,
        "experiment": {
            "name": "differentiable_rules_poc_v3_9_deepbach_tonal_audit",
            "generation_count": len(generations),
            "snarky_repair_applied": False,
        },
        "source": {
            "deepbach_root": str(deepbach_root),
            "upstream_manifest": str(deepbach_root / "UPSTREAM.json"),
            "upstream_manifest_sha256": base.sha256_file(
                deepbach_root / "UPSTREAM.json"
            ),
            "bach_test_result": str(bach_result_path),
            "bach_test_result_sha256": base.sha256_file(bach_result_path),
        },
        "bach_test_reference": {
            "proxy_opportunities": proxy["opportunities"],
            "proxy_resolutions": proxy["conclusion_chosen"],
            "exact_opportunities": exact["opportunities"],
            "exact_resolutions": exact["conclusion_chosen"],
        },
        "generations": generations,
        "aggregate": aggregate(generations),
    }
    results_dir = args.results_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / f"{args.output_stem}.json"
    report_path = results_dir / f"{args.output_stem.upper()}_REPORT.md"
    base.json_dump(json_path, result)
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"[done] wrote {json_path}", flush=True)
    print(f"[done] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
