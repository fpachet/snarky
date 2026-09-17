#!/usr/bin/env python3
"""Audit named chord-root transitions before admitting a V20C grammar."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import audit_v20_harmonic_status_coverage as harmonic
import k3
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v20c_named_root_transition_coverage_train.json"
DEFAULT_REPORT = FACTOR_BASE / "V20C_NAMED_ROOT_TRANSITION_COVERAGE_TRAIN.md"
MODE_NAMES = {0: "major", 1: "minor"}


def _unique_status(
    block: Any,
    *,
    tonic_pc: int,
) -> harmonic.HarmonicStatus | None:
    pitches = tuple(map(int, block))
    analyses = harmonic.analyze_pitch_classes(
        pitches,
        bass_pitch=int(block[3]),
        tonic_pc=tonic_pc,
    )
    return analyses[0] if len(analyses) == 1 else None


def _piece_audit(task: tuple[str, str]) -> dict[str, Any]:
    piece_id, score_path = task
    lattice = k3.extract_piece_lattice(Path(score_path), piece_id)
    statuses = [
        _unique_status(block, tonic_pc=lattice.tonic_pc)
        for block in lattice.blocks
    ]
    counts: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    arrivals: Counter[str] = Counter()
    departures: Counter[str] = Counter()
    mode_name = MODE_NAMES[lattice.mode]

    for index in range(1, lattice.size):
        counts["adjacent_edges"] += 1
        previous = statuses[index - 1]
        current = statuses[index]
        if previous is None or current is None:
            continue
        counts["named_unique_edges"] += 1
        previous_degree = int(previous.root_degree)
        current_degree = int(current.root_degree)
        transition = f"{mode_name}:{previous_degree}>{current_degree}"
        transitions[transition] += 1
        departures[f"{mode_name}:{previous_degree}"] += 1
        arrivals[f"{mode_name}:{current_degree}"] += 1
        if previous_degree != current_degree:
            counts["root_change_edges"] += 1

        previous_bass_degree = (
            int(lattice.blocks[index - 1, 3]) - lattice.tonic_pc
        ) % 12
        current_bass_degree = (
            int(lattice.blocks[index, 3]) - lattice.tonic_pc
        ) % 12
        if (
            previous_degree,
            current_degree,
        ) != (
            previous_bass_degree,
            current_bass_degree,
        ):
            counts["different_from_bass_transition"] += 1
        if previous_degree != previous_bass_degree:
            counts["previous_root_differs_from_bass"] += 1
        if current_degree != current_bass_degree:
            counts["current_root_differs_from_bass"] += 1

    return {
        "piece_id": piece_id,
        "mode": mode_name,
        "counts": dict(counts),
        "transitions": dict(transitions),
        "arrivals": dict(arrivals),
        "departures": dict(departures),
    }


def _aggregate(piece_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    arrivals: Counter[str] = Counter()
    departures: Counter[str] = Counter()
    transition_pieces: defaultdict[str, set[str]] = defaultdict(set)
    mode_edges: Counter[str] = Counter()

    for row in piece_rows:
        counts.update(row["counts"])
        transitions.update(row["transitions"])
        arrivals.update(row["arrivals"])
        departures.update(row["departures"])
        mode_edges[row["mode"]] += sum(row["transitions"].values())
        for transition, count in row["transitions"].items():
            if count:
                transition_pieces[transition].add(row["piece_id"])

    rows = []
    for key, count in transitions.items():
        mode_and_previous, current_text = key.split(">")
        mode, previous_text = mode_and_previous.split(":")
        previous = int(previous_text)
        current = int(current_text)
        departure_count = departures[f"{mode}:{previous}"]
        arrival_count = arrivals[f"{mode}:{current}"]
        conditional = count / departure_count
        marginal = arrival_count / mode_edges[mode]
        rows.append(
            {
                "mode": mode,
                "previous_root_degree": previous,
                "current_root_degree": current,
                "blocks": count,
                "piece_support": len(transition_pieces[key]),
                "conditional_probability": conditional,
                "arrival_marginal": marginal,
                "log2_lift_over_arrival_marginal": math.log2(
                    conditional / marginal
                ),
                "changes_root": previous != current,
            }
        )
    rows.sort(
        key=lambda row: (
            -row["blocks"],
            row["mode"],
            row["previous_root_degree"],
            row["current_root_degree"],
        )
    )

    named_edges = counts["named_unique_edges"]
    return {
        "counts": dict(sorted(counts.items())),
        "coverage": {
            "named_unique_edge_rate": (
                named_edges / counts["adjacent_edges"]
                if counts["adjacent_edges"]
                else 0.0
            ),
            "root_change_rate_among_named": (
                counts["root_change_edges"] / named_edges if named_edges else 0.0
            ),
            "different_from_bass_transition_rate": (
                counts["different_from_bass_transition"] / named_edges
                if named_edges
                else 0.0
            ),
        },
        "candidate_cells_observed": len(rows),
        "supported_transition_cells": sum(
            row["blocks"] >= 100 and row["piece_support"] >= 10
            for row in rows
        ),
        "transitions": rows,
    }


def _markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    coverage = summary["coverage"]
    counts = summary["counts"]
    supported_changes = [
        row
        for row in summary["transitions"]
        if row["changes_root"]
        and row["blocks"] >= 100
        and row["piece_support"] >= 10
    ]
    supported_changes.sort(
        key=lambda row: (
            -row["log2_lift_over_arrival_marginal"],
            -row["blocks"],
        )
    )
    lines = [
        "# V20C — couverture train des transitions de fondamentales nommées",
        "",
        "Cet audit est effectué avant toute extension de la grammaire. Il ne",
        "sélectionne aucune règle et n'apprend aucun poids.",
        "",
        "## Test de nouveauté",
        "",
        f"- Chorals de train : `{result['experiment']['pieces']}`.",
        f"- Arêtes entre blocs voisins : `{counts['adjacent_edges']}`.",
        f"- Deux analyses nommées uniques : "
        f"`{100 * coverage['named_unique_edge_rate']:.2f} %`.",
        f"- Changement de fondamentale parmi ces arêtes : "
        f"`{100 * coverage['root_change_rate_among_named']:.2f} %`.",
        f"- Transition de fondamentales différente de la transition de basses : "
        f"`{100 * coverage['different_from_bass_transition_rate']:.2f} %`.",
        f"- Cellules observées : `{summary['candidate_cells_observed']}`.",
        f"- Cellules avec ≥100 occurrences et ≥10 chorals : "
        f"`{summary['supported_transition_cells']}`.",
        "",
        "Le dernier pourcentage mesure directement ce que cette représentation",
        "ajoute à l'expérience V13 : dans un renversement, la fondamentale",
        "analysée n'est pas la note de basse.",
        "",
        "## Changements de fondamentale les plus enrichis",
        "",
        "| Mode | Degré précédent → courant | Blocs | Chorals | "
        "P(courant|précédent) | lift log2 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in supported_changes[:24]:
        lines.append(
            f"| {row['mode']} | {row['previous_root_degree']} → "
            f"{row['current_root_degree']} | {row['blocks']} | "
            f"{row['piece_support']} | "
            f"{100 * row['conditional_probability']:.2f} % | "
            f"{row['log2_lift_over_arrival_marginal']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "Ces enrichissements ne sont pas encore des règles : ils servent",
            "uniquement à décider si la famille est couverte, distincte de V13",
            "et assez parcimonieuse pour être soumise à l'induction exacte.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    piece_ids = sorted(splits["train"], key=generative._stable_order)
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
            "id": "K3-V20C-NAMED-ROOT-TRANSITION-COVERAGE-1",
            "status": "COVERAGE_AND_NOVELTY_AUDIT_ONLY",
            "split_role": "train",
            "pieces": len(piece_rows),
            "workers": args.workers,
            "test_loaded": False,
            "weights_learned": False,
        },
        "summary": _aggregate(piece_rows),
        "pieces": piece_rows,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    coverage = result["summary"]["coverage"]
    print(
        f"[v20c-coverage] pieces={len(piece_rows)} "
        f"named_edges={coverage['named_unique_edge_rate']:.3f} "
        f"differs_from_bass="
        f"{coverage['different_from_bass_transition_rate']:.3f}",
        flush=True,
    )
    print(f"[v20c-coverage] wrote {args.output}", flush=True)
    print(f"[v20c-coverage] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
