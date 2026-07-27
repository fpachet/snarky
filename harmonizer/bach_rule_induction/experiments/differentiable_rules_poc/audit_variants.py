#!/usr/bin/env python3
"""Audit exact melodic variants and build a conservative grouped split.

For a soprano-conditioned harmonization task, two pieces with the same
transposition-invariant soprano contour and rhythm belong to one leakage group,
even when their lower voices differ. The audit never evaluates a model or a
test-set metric.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import run_poc as base

SPLIT_ORDER = ("train", "validation", "test")
SPLIT_PRIORITY = {name: index for index, name in enumerate(SPLIT_ORDER)}


def stable_fingerprint(value: Any) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def piece_fingerprints(
    opportunities: base.Opportunities,
    tick_resolution: int = 48,
) -> dict[str, dict[str, str | int]]:
    """Build exact transposition-invariant fingerprints for every piece."""

    records: dict[str, dict[str, str | int]] = {}
    for piece_id in sorted(np.unique(opportunities.piece_ids).tolist()):
        indices = np.flatnonzero(opportunities.piece_ids == piece_id)
        indices = indices[np.argsort(opportunities.offsets_current[indices])]
        durations = np.rint(
            (
                opportunities.offsets_current[indices]
                - opportunities.offsets_previous[indices]
            )
            * tick_resolution
        ).astype(int)
        soprano_delta = (
            opportunities.chosen_soprano[indices]
            - opportunities.previous_soprano[indices]
        ).astype(int)
        bass_delta = (
            opportunities.current_bass[indices] - opportunities.previous_bass[indices]
        ).astype(int)
        source_class = (
            np.abs(
                opportunities.previous_soprano[indices]
                - opportunities.previous_bass[indices]
            )
            % 12
        ).astype(int)
        target_class = (
            np.abs(
                opportunities.chosen_soprano[indices]
                - opportunities.current_bass[indices]
            )
            % 12
        ).astype(int)
        records[piece_id] = {
            "opportunity_count": int(indices.shape[0]),
            "soprano_fingerprint": stable_fingerprint(
                [durations.tolist(), soprano_delta.tolist()]
            ),
            "outer_voice_fingerprint": stable_fingerprint(
                [
                    durations.tolist(),
                    soprano_delta.tolist(),
                    bass_delta.tolist(),
                    source_class.tolist(),
                    target_class.tolist(),
                ]
            ),
        }
    return records


def index_groups(
    fingerprints: dict[str, dict[str, str | int]],
    field: str,
) -> list[list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for piece_id, record in fingerprints.items():
        grouped[str(record[field])].append(piece_id)
    return sorted(
        (sorted(members) for members in grouped.values()),
        key=lambda members: (members[0], len(members)),
    )


def split_mapping(splits: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for split_name in SPLIT_ORDER:
        for piece_id in splits[split_name]:
            if piece_id in mapping:
                raise ValueError(f"Piece appears twice in splits: {piece_id}")
            mapping[piece_id] = split_name
    return mapping


def conservative_grouped_split(
    old_splits: dict[str, Any],
    soprano_groups: list[list[str]],
) -> tuple[dict[str, list[str]], list[dict[str, str]]]:
    """Move a whole group to its earliest previously exposed partition."""

    old_mapping = split_mapping(old_splits)
    new_mapping: dict[str, str] = {}
    for members in soprano_groups:
        destinations = [old_mapping[piece_id] for piece_id in members]
        destination = min(destinations, key=SPLIT_PRIORITY.__getitem__)
        for piece_id in members:
            new_mapping[piece_id] = destination

    if set(new_mapping) != set(old_mapping):
        missing = sorted(set(old_mapping) - set(new_mapping))
        extra = sorted(set(new_mapping) - set(old_mapping))
        raise ValueError(f"Split/group mismatch: missing={missing}, extra={extra}")

    grouped = {
        split_name: sorted(
            piece_id
            for piece_id, assigned in new_mapping.items()
            if assigned == split_name
        )
        for split_name in SPLIT_ORDER
    }
    moved = [
        {
            "piece_id": piece_id,
            "from": old_mapping[piece_id],
            "to": new_mapping[piece_id],
        }
        for piece_id in sorted(new_mapping)
        if old_mapping[piece_id] != new_mapping[piece_id]
    ]
    return grouped, moved


def crossing_groups(
    groups: list[list[str]],
    mapping: dict[str, str],
) -> list[list[dict[str, str]]]:
    crossings = []
    for members in groups:
        if len(members) < 2:
            continue
        split_names = {mapping[piece_id] for piece_id in members}
        if len(split_names) <= 1:
            continue
        crossings.append(
            [{"piece_id": piece_id, "split": mapping[piece_id]} for piece_id in members]
        )
    return crossings


def duplicate_records(
    groups: list[list[str]],
    old_mapping: dict[str, str],
    new_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            "members": members,
            "old_splits": sorted(
                {old_mapping[piece_id] for piece_id in members},
                key=SPLIT_PRIORITY.__getitem__,
            ),
            "new_split": new_mapping[members[0]],
        }
        for members in groups
        if len(members) > 1
    ]


def markdown_report(result: dict[str, Any]) -> str:
    old = result["old_split"]
    new = result["grouped_split"]
    audit = result["audit"]
    lines = [
        "# Audit des variantes et partage groupé",
        "",
        "## Résultat",
        "",
        (
            f"- Ancien partage : {old['counts']['train']}/"
            f"{old['counts']['validation']}/{old['counts']['test']}."
        ),
        (
            f"- Nouveau partage conservateur : {new['counts']['train']}/"
            f"{new['counts']['validation']}/{new['counts']['test']}."
        ),
        (
            f"- Groupes de soprano dupliqués : "
            f"{audit['soprano_duplicate_group_count']} "
            f"({audit['soprano_duplicate_piece_count']} pièces)."
        ),
        (
            f"- Groupes de soprano traversant l'ancien partage : "
            f"{audit['old_soprano_crossing_group_count']}."
        ),
        (
            f"- Groupes traversant le nouveau partage : "
            f"{audit['new_soprano_crossing_group_count']}."
        ),
        (
            f"- Le nouveau test contient {new['counts']['test']} pièces, "
            "toutes déjà réservées au test historique et jamais promues depuis "
            "train ou validation."
        ),
        "",
        "## Définition d'une variante",
        "",
        "Deux pièces appartiennent au même groupe lorsque la suite exacte des",
        "durées quantifiées et des intervalles mélodiques de soprano est",
        "identique. La hauteur absolue est ignorée, ce qui rend le test invariant",
        "par transposition. Pour la tâche soprano-conditionnée, cette définition",
        "est volontairement plus prudente qu'une identité de l'harmonisation.",
        "",
        "## Déplacements conservateurs",
        "",
        "| Pièce | Ancien | Nouveau |",
        "|---|---|---|",
    ]
    for moved in result["moved_pieces"]:
        lines.append(f"| `{moved['piece_id']}` | {moved['from']} | {moved['to']} |")
    lines.extend(
        [
            "",
            "## Groupes qui traversaient l'ancien partage",
            "",
        ]
    )
    for group in audit["old_soprano_crossing_groups"]:
        members = ", ".join(f"`{item['piece_id']}` ({item['split']})" for item in group)
        lines.append(f"- {members}")
    lines.extend(
        [
            "",
            "Le test est construit sans consulter aucune métrique de modèle. Un",
            "groupe est déplacé vers la partition la plus anciennement exposée :",
            "`train` avant `validation`, puis `test`. Aucun élément anciennement",
            "vu en train ou validation ne peut donc entrer dans le nouveau test.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = base.experiment_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--opportunities",
        type=Path,
        default=root / "work/opportunities-full.npz",
    )
    parser.add_argument(
        "--old-splits",
        type=Path,
        default=root / "results/splits.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "results/splits.variant-safe.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=root / "results/VARIANT_AUDIT.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    opportunities = base.load_opportunities(args.opportunities)
    old_splits = json.loads(args.old_splits.read_text(encoding="utf-8"))
    fingerprints = piece_fingerprints(opportunities)
    soprano_groups = index_groups(fingerprints, "soprano_fingerprint")
    outer_groups = index_groups(fingerprints, "outer_voice_fingerprint")
    grouped, moved = conservative_grouped_split(old_splits, soprano_groups)
    old_mapping = split_mapping(old_splits)
    new_mapping = split_mapping(grouped)
    old_soprano_crossings = crossing_groups(soprano_groups, old_mapping)
    new_soprano_crossings = crossing_groups(soprano_groups, new_mapping)
    old_outer_crossings = crossing_groups(outer_groups, old_mapping)

    if new_soprano_crossings:
        raise AssertionError("Grouped split still leaks a soprano variant")
    if any(old_mapping[piece_id] != "test" for piece_id in grouped["test"]):
        raise AssertionError("Previously exposed piece entered the new test")

    result = {
        "schema_version": 1,
        "strategy": "exact_soprano_contour_and_rhythm_conservative_grouping",
        "source_split": str(args.old_splits.resolve()),
        "tick_resolution": 48,
        "old_split": {"counts": {name: len(old_splits[name]) for name in SPLIT_ORDER}},
        "grouped_split": {
            "train": grouped["train"],
            "validation": grouped["validation"],
            "test": grouped["test"],
            "counts": {name: len(grouped[name]) for name in SPLIT_ORDER},
        },
        "moved_pieces": moved,
        "audit": {
            "soprano_duplicate_group_count": sum(
                len(group) > 1 for group in soprano_groups
            ),
            "soprano_duplicate_piece_count": sum(
                len(group) for group in soprano_groups if len(group) > 1
            ),
            "outer_voice_duplicate_group_count": sum(
                len(group) > 1 for group in outer_groups
            ),
            "outer_voice_duplicate_piece_count": sum(
                len(group) for group in outer_groups if len(group) > 1
            ),
            "old_soprano_crossing_group_count": len(old_soprano_crossings),
            "old_outer_voice_crossing_group_count": len(old_outer_crossings),
            "new_soprano_crossing_group_count": len(new_soprano_crossings),
            "old_soprano_crossing_groups": old_soprano_crossings,
            "old_outer_voice_crossing_groups": old_outer_crossings,
            "soprano_duplicate_groups": duplicate_records(
                soprano_groups, old_mapping, new_mapping
            ),
            "outer_voice_duplicate_groups": duplicate_records(
                outer_groups, old_mapping, new_mapping
            ),
        },
    }
    base.json_dump(args.output, result)
    args.report.write_text(markdown_report(result), encoding="utf-8")
    print(f"[done] wrote {args.output}", flush=True)
    print(f"[done] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
