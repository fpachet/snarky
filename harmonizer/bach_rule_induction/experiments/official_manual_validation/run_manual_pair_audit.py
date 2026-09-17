#!/usr/bin/env python3
"""Audit the twelve authentic/counterfactual manual pairs with Snarky."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from harmonizer.official_manual import audit_musicxml

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
DEFAULT_MANUAL_ROOT = REPOSITORY.parent / "cours_harmonie/bach-corpus-manual"
DEFAULT_OUTPUT = HERE / "results/manual_pair_audit.json"
DEFAULT_REPORT = HERE / "results/MANUAL_PAIR_AUDIT.md"

TARGETS = {
    "parallel_fifth": ("violates", "MANUAL-PARALLEL-FIFTH"),
    "parallel_octave": ("violates", "MANUAL-PARALLEL-OCTAVE"),
    "direct_fifth": ("violates", "MANUAL-DIRECT-FIFTH"),
    "voice_crossing": ("violates", "MANUAL-VOICE-CROSSING"),
    "voice_overlap": ("violates", "MANUAL-VOICE-OVERLAP"),
    "common_tone": ("satisfies", "MANUAL-COMMON-TONE"),
    "contrary_motion": ("satisfies", "MANUAL-CONTRARY-OUTER"),
    "compensated_leap": ("satisfies", "MANUAL-COMPENSATED-LEAP"),
    "suspension_resolution": (
        "satisfies",
        "MANUAL-SUSPENSION-RESOLUTION",
    ),
    "leading_tone_resolution": ("satisfies", "MANUAL-LEADING-TONE"),
    "singable_line": ("violates", "MANUAL-SINGABLE-LINE"),
    "active_inner_voice": ("violates", "MANUAL-ACTIVE-INNER-VOICE"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual-root", type=Path, default=DEFAULT_MANUAL_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def audit_pairs(manual_root: Path) -> dict[str, Any]:
    rows = []
    for directory in sorted((manual_root / "rules").iterdir()):
        metadata_path = directory / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        code = str(metadata["validation"]["code"])
        relation, rule_id = TARGETS[code]
        authentic = audit_musicxml(directory / "authentic.musicxml")
        counterfactual = audit_musicxml(directory / "counterfactual.musicxml")
        strict_counterfactual = audit_musicxml(
            directory / "counterfactual.musicxml",
            profile="pedagogical_strict",
        )
        authentic_count = authentic.count(relation, rule_id)
        counterfactual_count = counterfactual.count(relation, rule_id)
        passed = (
            counterfactual_count > authentic_count
            if relation == "violates"
            else authentic_count > counterfactual_count
        )
        rows.append(
            {
                "study": directory.name,
                "piece_id": metadata["piece_id"],
                "diagnostic_code": code,
                "relation": relation,
                "rule_id": rule_id,
                "authentic_count": authentic_count,
                "counterfactual_count": counterfactual_count,
                "differential_pass": passed,
                "strict_counterfactual_contradiction": (
                    strict_counterfactual.contradiction
                ),
                "authentic_factor_score": authentic.factor_score,
                "counterfactual_factor_score": counterfactual.factor_score,
                "source_changes": metadata["changes"],
            }
        )
    return {
        "experiment": {
            "id": "OFFICIAL-MANUAL-SNARKY-PARITY-1",
            "status": (
                "PASS"
                if rows and all(row["differential_pass"] for row in rows)
                else "FAIL"
            ),
            "manual_examples_used": len(rows),
            "weights_refitted": False,
            "test_split_loaded": False,
        },
        "manual_root": str(manual_root.resolve()),
        "summary": {
            "passed": sum(row["differential_pass"] for row in rows),
            "total": len(rows),
            "strict_counterfactual_contradictions": sum(
                row["strict_counterfactual_contradiction"] for row in rows
            ),
        },
        "rows": rows,
    }


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Audit Snarky du manuel Bach",
        "",
        "Chaque ligne compare l'extrait authentique et sa mutation pédagogique",
        "avec le même RuleGroup et sans réajuster aucun poids.",
        "",
        f"- Contrastes réussis : `{payload['summary']['passed']}` / "
        f"`{payload['summary']['total']}`.",
        "- Le split test du corpus n'est pas chargé.",
        "",
        "| Étude | Relation | Bach | Variante | Résultat |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['study']} | `{row['relation']}` | "
            f"{row['authentic_count']} | {row['counterfactual_count']} | "
            f"{'PASS' if row['differential_pass'] else 'FAIL'} |"
        )
    lines.extend(
        (
            "",
            "Ce test valide la sémantique différentielle des règles, pas leur",
            "suffisance comme théorie complète du style de Bach.",
        )
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    payload = audit_pairs(args.manual_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(markdown(payload), encoding="utf-8")
    print(
        f"[official-manual] {payload['summary']['passed']}/"
        f"{payload['summary']['total']} contrasts passed"
    )
    print(f"[official-manual] wrote {args.output}")
    print(f"[official-manual] wrote {args.report}")
    return 0 if payload["experiment"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
