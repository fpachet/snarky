#!/usr/bin/env python3
"""Calibrate one-sided manual-rule budgets without touching the test split."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import yaml

from harmonizer.official_manual import (
    DEFAULT_RULEBASE,
    EMPIRICAL_METRIC_IDS,
    METRIC_SCALE,
    audit_musicxml,
)

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE.parent / "v5_k3_clean/work/scores"
DEFAULT_BUDGETS = DEFAULT_RULEBASE / "empirical_budgets.yaml"
DEFAULT_COMPILED_RULES = DEFAULT_RULEBASE / "empirical_acceptance.rules"
DEFAULT_RESULTS = HERE / "results/empirical_budget_calibration.json"
DEFAULT_REPORT = HERE / "results/EMPIRICAL_BUDGET_CALIBRATION.md"
METRIC_GROUPS = {
    "contrapuntal": (
        "parallel_fifth_rate",
        "parallel_octave_rate",
        "direct_fifth_rate",
        "voice_crossing_rate",
        "voice_overlap_rate",
    ),
    "tendency": (
        "unresolved_leading_tone_ratio",
        "uncompensated_leap_ratio",
        "unresolved_suspension_ratio",
    ),
    "leap": (
        "soprano_maximum_leap",
        "alto_maximum_leap",
        "tenor_maximum_leap",
        "bass_maximum_leap",
    ),
    "repetition": (
        "alto_longest_repeat_run",
        "tenor_longest_repeat_run",
        "bass_longest_repeat_run",
    ),
    "conjunct_motion": (
        "alto_step_deficit",
        "tenor_step_deficit",
        "bass_step_deficit",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--quantile", type=float, default=0.95)
    parser.add_argument(
        "--maximum-validation-exceedance",
        type=float,
        default=0.15,
    )
    parser.add_argument("--budgets", type=Path, default=DEFAULT_BUDGETS)
    parser.add_argument("--compiled-rules", type=Path, default=DEFAULT_COMPILED_RULES)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _score_path(scores: Path, piece_id: str) -> Path:
    stem = piece_id.rsplit("/", 1)[-1]
    for suffix in (".mxl", ".musicxml", ".xml"):
        candidate = scores / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No score for {piece_id} in {scores}")


def _higher_quantile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("cannot calibrate an empty metric")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return ordered[index]


def _piece_metrics(piece_ids: list[str], scores: Path) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for index, piece_id in enumerate(piece_ids, start=1):
        diagnostic = audit_musicxml(_score_path(scores, piece_id))
        rows[piece_id] = {
            str(row["metric_id"]): float(row["value"])
            for row in diagnostic.empirical_metrics
        }
        if index % 50 == 0:
            print(f"[official-manual] audited {index}/{len(piece_ids)} scores")
    return rows


def _exceedance_rate(
    rows: dict[str, dict[str, float]],
    metric_id: str,
    threshold: float,
) -> float:
    return sum(values[metric_id] > threshold for values in rows.values()) / len(rows)


def _joint_acceptance(
    rows: dict[str, dict[str, float]],
    thresholds: dict[str, float],
) -> float:
    return sum(
        all(
            values[metric_id] <= threshold
            for metric_id, threshold in thresholds.items()
        )
        for values in rows.values()
    ) / len(rows)


def _exceeded_budget_count(
    values: dict[str, float], thresholds: dict[str, float]
) -> int:
    return sum(
        values[metric_id] > threshold for metric_id, threshold in thresholds.items()
    )


def _count_budget_acceptance(
    rows: dict[str, dict[str, float]],
    thresholds: dict[str, float],
    maximum_exceeded: int,
) -> float:
    return sum(
        _exceeded_budget_count(values, thresholds) <= maximum_exceeded
        for values in rows.values()
    ) / len(rows)


def _rule_id(metric_id: str) -> str:
    return f"EMPIRICAL-{metric_id.replace('_', '-').upper()}"


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Calibration des budgets empiriques du manuel",
        "",
        "Les seuils sont les quantiles supérieurs calculés sur les 251 chorals",
        "d'entraînement uniquement. Un budget est promu lorsque son taux de",
        "dépassement sur les 50 chorals de validation ne dépasse pas la borne",
        "préenregistrée. Le test n'intervient ni dans le seuil ni dans la promotion.",
        "",
        f"- Quantile train : `{payload['protocol']['train_quantile']:.3f}`.",
        "- Dépassement validation maximal : "
        f"`{payload['protocol']['maximum_validation_exceedance']:.3f}`.",
        f"- Budgets promus : `{payload['decision']['promoted_count']}` / "
        f"`{payload['decision']['candidate_count']}`.",
        "- Acceptation conjointe train / validation / test : "
        f"`{payload['joint_acceptance']['train']:.3f}` / "
        f"`{payload['joint_acceptance']['validation']:.3f}` / "
        f"`{payload['joint_acceptance']['test']:.3f}`.",
        "- Budget conjoint de dépassements autorisés : "
        f"`{payload['count_budget']['maximum_exceeded_budgets']}`.",
        "- Acceptation avec ce budget train / validation / test : "
        f"`{payload['count_budget']['acceptance']['train']:.3f}` / "
        f"`{payload['count_budget']['acceptance']['validation']:.3f}` / "
        f"`{payload['count_budget']['acceptance']['test']:.3f}`.",
        "- Acceptation de toutes les familles train / validation / test : "
        f"`{payload['group_budgets']['joint_acceptance']['train']:.3f}` / "
        f"`{payload['group_budgets']['joint_acceptance']['validation']:.3f}` / "
        f"`{payload['group_budgets']['joint_acceptance']['test']:.3f}`.",
        "",
        "| Métrique | Seuil | Train > | Validation > | Test > | Décision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["metrics"]:
        lines.append(
            f"| `{row['metric_id']}` | {row['threshold']:.6f} | "
            f"{row['train_exceedance']:.3f} | {row['validation_exceedance']:.3f} | "
            f"{row['test_exceedance']:.3f} | "
            f"{'PROMU' if row['promoted'] else 'REJETÉ'} |"
        )
    lines.extend(
        (
            "",
            "## Budgets par famille",
            "",
            "| Famille | Dépassements autorisés | Train | Validation | Test |",
            "|---|---:|---:|---:|---:|",
        )
    )
    for row in payload["group_budgets"]["groups"]:
        lines.append(
            f"| `{row['group_id']}` | {row['maximum_exceeded_budgets']} | "
            f"{row['acceptance']['train']:.3f} | "
            f"{row['acceptance']['validation']:.3f} | "
            f"{row['acceptance']['test']:.3f} |"
        )
    lines.extend(
        (
            "",
            "Les budgets sont des enveloppes statistiques de génération, pas des",
            "interdictions musicologiques universelles. Une pièce authentique peut",
            "donc tomber hors enveloppe, ce que mesure l'acceptation conjointe.",
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    ordered_ids = [*splits["train"], *splits["validation"], *splits["test"]]
    all_rows = _piece_metrics(ordered_ids, args.scores)
    rows = {
        split: {piece_id: all_rows[piece_id] for piece_id in splits[split]}
        for split in ("train", "validation", "test")
    }
    metric_rows = []
    promoted: list[dict[str, Any]] = []
    for metric_id in EMPIRICAL_METRIC_IDS:
        threshold = _higher_quantile(
            [values[metric_id] for values in rows["train"].values()],
            args.quantile,
        )
        exceedances = {
            split: _exceedance_rate(split_rows, metric_id, threshold)
            for split, split_rows in rows.items()
        }
        is_promoted = exceedances["validation"] <= args.maximum_validation_exceedance
        record = {
            "metric_id": metric_id,
            "threshold": threshold,
            "threshold_scaled": math.ceil(threshold * METRIC_SCALE - 1e-12),
            "train_exceedance": exceedances["train"],
            "validation_exceedance": exceedances["validation"],
            "test_exceedance": exceedances["test"],
            "promoted": is_promoted,
        }
        metric_rows.append(record)
        if is_promoted:
            promoted.append({**record, "rule_id": _rule_id(metric_id)})
    thresholds = {row["metric_id"]: row["threshold"] for row in promoted}
    train_exceeded_counts = [
        float(_exceeded_budget_count(values, thresholds))
        for values in rows["train"].values()
    ]
    maximum_exceeded = int(_higher_quantile(train_exceeded_counts, args.quantile))
    promoted_by_id = {row["metric_id"]: row for row in promoted}
    group_budgets = []
    for group_id, declared_metric_ids in METRIC_GROUPS.items():
        metric_ids = tuple(
            metric_id
            for metric_id in declared_metric_ids
            if metric_id in promoted_by_id
        )
        group_thresholds = {
            metric_id: thresholds[metric_id] for metric_id in metric_ids
        }
        maximum_group_exceeded = int(
            _higher_quantile(
                [
                    float(_exceeded_budget_count(values, group_thresholds))
                    for values in rows["train"].values()
                ],
                args.quantile,
            )
        )
        group_budgets.append(
            {
                "group_id": group_id,
                "rule_id": f"EMPIRICAL-GROUP-{group_id.replace('_', '-').upper()}",
                "metric_ids": list(metric_ids),
                "maximum_exceeded_budgets": maximum_group_exceeded,
                "acceptance": {
                    split: _count_budget_acceptance(
                        split_rows,
                        group_thresholds,
                        maximum_group_exceeded,
                    )
                    for split, split_rows in rows.items()
                },
            }
        )
    group_joint_acceptance = {
        split: sum(
            all(
                _exceeded_budget_count(
                    values,
                    {
                        metric_id: thresholds[metric_id]
                        for metric_id in group["metric_ids"]
                    },
                )
                <= group["maximum_exceeded_budgets"]
                for group in group_budgets
            )
            for values in split_rows.values()
        )
        / len(split_rows)
        for split, split_rows in rows.items()
    }
    payload = {
        "id": "OFFICIAL-MANUAL-EMPIRICAL-BUDGET-CALIBRATION-1",
        "status": "FROZEN_AFTER_TEST_REPORT",
        "protocol": {
            "train_quantile": args.quantile,
            "maximum_validation_exceedance": args.maximum_validation_exceedance,
            "threshold_estimation_split": "train251",
            "promotion_split": "validation50",
            "test_split_used_for_fit_or_promotion": False,
        },
        "split_sizes": {split: len(split_rows) for split, split_rows in rows.items()},
        "decision": {
            "candidate_count": len(metric_rows),
            "promoted_count": len(promoted),
            "promoted_metric_ids": [row["metric_id"] for row in promoted],
        },
        "joint_acceptance": {
            split: _joint_acceptance(split_rows, thresholds)
            for split, split_rows in rows.items()
        },
        "count_budget": {
            "maximum_exceeded_budgets": maximum_exceeded,
            "acceptance": {
                split: _count_budget_acceptance(
                    split_rows, thresholds, maximum_exceeded
                )
                for split, split_rows in rows.items()
            },
        },
        "group_budgets": {
            "groups": group_budgets,
            "joint_acceptance": group_joint_acceptance,
        },
        "metrics": metric_rows,
    }
    budget_payload = {
        "schema_version": 1,
        "id": "S-OFFICIAL-MANUAL-EMPIRICAL-BUDGETS-1",
        "status": "FROZEN_AFTER_TEST_REPORT",
        "scale": METRIC_SCALE,
        "protocol": payload["protocol"],
        "promoted_budgets": promoted,
        "maximum_exceeded_budgets": maximum_exceeded,
        "group_budgets": group_budgets,
    }
    args.budgets.parent.mkdir(parents=True, exist_ok=True)
    args.budgets.write_text(
        yaml.safe_dump(budget_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    compiled_lines = [
        "# Fichier compilé par calibrate_empirical_budgets.py.",
        "",
        "GROUP official_manual_empirical_acceptance",
        "    RULE reject_too_many_empirical_budget_exceedances",
        "    WHEN",
        f"        COUNT >= {maximum_exceeded + 1}",
        "            (score exceeds_empirical_budget $metric)",
        "        END_COUNT",
        "    THEN",
        "        ADD (score violates EMPIRICAL-JOINT-BUDGET)",
        "    END",
    ]
    for group in group_budgets:
        compiled_lines.extend(
            (
                "",
                f"    RULE reject_{group['group_id']}_budget",
                "    WHEN",
                f"        COUNT >= {group['maximum_exceeded_budgets'] + 1}",
                "            (SEQ[score "
                f"{group['group_id']}] exceeds_empirical_budget $metric)",
                "        END_COUNT",
                "    THEN",
                f"        ADD (score violates {group['rule_id']})",
                "    END",
            )
        )
    compiled_lines.append("END_GROUP")
    args.compiled_rules.write_text(
        "\n".join(compiled_lines) + "\n",
        encoding="utf-8",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _write_report(args.report, payload)
    print(
        f"[official-manual] promoted {len(promoted)}/{len(metric_rows)} budgets; "
        f"maximum exceedances={maximum_exceeded}; "
        "test count-budget acceptance="
        f"{payload['count_budget']['acceptance']['test']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
