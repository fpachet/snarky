#!/usr/bin/env python3
"""Build an exact-survivor V22 constraint model for generative ablation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import yaml

from snarky import parse_rule_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = (
    REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
)
RULES_DIRECTORY = (
    REPOSITORY
    / "harmonizer/bach_rule_induction/rules/v22_candidate_constraints"
)
DEFAULT_MODEL = FACTOR_BASE / "v22_shared_root_motion_full_model.json"
DEFAULT_AUDIT = (
    FACTOR_BASE / "v22_constraint_candidate_full_validation.json"
)
DEFAULT_OUTPUT = (
    FACTOR_BASE / "v22_shared_root_motion_candidate_constraints_model.json"
)
DEFAULT_CATALOGUE = RULES_DIRECTORY / "constraints.yaml"
DEFAULT_PROGRAM = RULES_DIRECTORY / "candidate_constraints.rules"


def constraint_features() -> tuple[tuple[str, k3.FeatureSpec], ...]:
    """Return only predicates with zero exceptions in train and validation."""

    rows: list[tuple[str, k3.FeatureSpec]] = [
        (
            "nonadjacent_voice_order",
            k3.FeatureSpec(
                "central_ordered_gap_le",
                2,
                other_voice=0,
                value=-1,
            ),
        ),
        (
            "nonadjacent_voice_order",
            k3.FeatureSpec(
                "central_ordered_gap_le",
                0,
                other_voice=2,
                value=-1,
            ),
        ),
        (
            "directional_alto_bass_order",
            k3.FeatureSpec(
                "central_ordered_gap_le",
                1,
                other_voice=3,
                value=-1,
            ),
        ),
        (
            "outer_voice_minimum_spacing",
            k3.FeatureSpec(
                "central_ordered_gap_le",
                0,
                other_voice=3,
                value=1,
            ),
        ),
        (
            "outer_voice_minimum_spacing",
            k3.FeatureSpec(
                "central_ordered_gap_le",
                3,
                other_voice=0,
                value=1,
            ),
        ),
    ]
    for voice in range(3):
        rows.extend(
            (
                (
                    "melodic_major_seventh",
                    k3.FeatureSpec(
                        "abs_class_from_previous",
                        voice,
                        value=11,
                    ),
                ),
                (
                    "melodic_major_seventh",
                    k3.FeatureSpec(
                        "abs_class_to_next",
                        voice,
                        value=11,
                    ),
                ),
                (
                    "melodic_beyond_octave",
                    k3.FeatureSpec(
                        "abs_step_from_previous_gt",
                        voice,
                        value=12,
                    ),
                ),
                (
                    "melodic_beyond_octave",
                    k3.FeatureSpec(
                        "abs_step_to_next_gt",
                        voice,
                        value=12,
                    ),
                ),
            )
        )
    for target, other in ((1, 2), (2, 1), (2, 3), (3, 2)):
        rows.append(
            (
                "direct_arrival_minor_second",
                k3.FeatureSpec(
                    "pair_arrival_abs_class_same_sign",
                    target,
                    other_voice=other,
                    value=1,
                    complexity=2,
                ),
            )
        )
    for interval_class in (1, 11):
        rows.append(
            (
                "preserved_dissonance_in_direct_motion",
                k3.FeatureSpec(
                    "any_pair_abs_class_preserved_same_sign",
                    -1,
                    value=interval_class,
                    complexity=4,
                ),
            )
        )
    return tuple(rows)


def build_model(
    source: dict[str, Any],
    audit: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    survivors = {
        row["feature"]["key"]: row for row in audit["survivors"]
    }
    records = []
    for index, (schema, feature) in enumerate(
        constraint_features(),
        start=1,
    ):
        if feature.key not in survivors:
            raise ValueError(
                f"Constraint was not an exact full-split survivor: {feature.key}"
            )
        evidence = survivors[feature.key]
        records.append(
            {
                "id": f"C-K3-V22-{index:03d}",
                "schema": schema,
                "feature": feature.to_dict(),
                "status": "EMPIRICAL_PRETEST_FILTER",
                "absolute_prohibition": True,
                "evidence": {
                    "train_pieces": 251,
                    "train_opportunities": evidence["full_train"][
                        "testable_opportunities"
                    ],
                    "train_activations": 0,
                    "validation_pieces": 50,
                    "validation_opportunities": evidence["full_validation"][
                        "testable_opportunities"
                    ],
                    "validation_activations": 0,
                    "test_opened": False,
                },
            }
        )
    result = json.loads(json.dumps(source))
    result["experiment"] = {
        **source["experiment"],
        "id": "K3-V22-SHARED-ROOT-MOTION-CANDIDATE-CONSTRAINTS-1",
        "status": "GENERATIVE_ABLATION_NOT_PROMOTED_TO_MUST",
        "hard_constraint_count": len(records),
        "test_loaded": False,
    }
    result["model"]["constraints"] = records
    catalogue = {
        "schema_version": 1,
        "id": "S-LEARNED-V22-CANDIDATE-CONSTRAINTS",
        "status": "EMPIRICAL_PRETEST_FILTERS_NOT_MUST",
        "source_audit": str(DEFAULT_AUDIT.resolve()),
        "semantics": "remove_candidate_before_choice_normalization",
        "counts": {
            "constraint_predicates": len(records),
            "logical_schemas": len({row["schema"] for row in records}),
        },
        "constraints": records,
        "provenance_guards": {
            "all_predicates_zero_exception_on_train_and_validation": True,
            "named_harmonic_exclusion_kept_soft": True,
            "historical_rules_loaded": False,
            "test_opened": False,
        },
    }
    return result, catalogue


def render_program(catalogue: dict[str, Any]) -> str:
    lines = [
        "# Candidate constraints learned as zero-exception predicates.",
        "# They remain pretest filters and are not yet declared MUST.",
        "GROUP k3_v22_candidate_constraints",
    ]
    for record in catalogue["constraints"]:
        constraint_id = record["id"]
        lines.extend(
            [
                f"    RULE reject_{constraint_id}",
                "    WHEN",
                f"        ($scope k3_constraint_active {constraint_id})",
                "    THEN",
                (
                    "        ADD "
                    f"($scope k3_candidate_forbidden {constraint_id})"
                ),
                "    END",
                "",
            ]
        )
    lines.extend(("END_GROUP", ""))
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--program", type=Path, default=DEFAULT_PROGRAM)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = json.loads(args.model.read_text(encoding="utf-8"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    model, catalogue = build_model(source, audit)
    args.output.write_text(
        json.dumps(model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.catalogue.parent.mkdir(parents=True, exist_ok=True)
    catalogue["source_audit"] = str(args.audit.resolve())
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    program = render_program(catalogue)
    (parsed_group,) = parse_rule_groups(program)
    if len(parsed_group.rules) != len(catalogue["constraints"]):
        raise ValueError("Snarky program lost V22 candidate constraints")
    args.program.write_text(program, encoding="utf-8")
    print(
        f"[v22-constraints] wrote {len(parsed_group.rules)} predicates in "
        f"{catalogue['counts']['logical_schemas']} schemas",
        flush=True,
    )
    print(f"[v22-constraints] wrote {args.output}", flush=True)
    print(f"[v22-constraints] wrote {args.program}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
