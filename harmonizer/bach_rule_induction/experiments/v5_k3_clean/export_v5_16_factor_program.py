#!/usr/bin/env python3
"""Export the frozen V5.16 catalogue to Snarky's pure FACTOR syntax."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
DEFAULT_CATALOGUE = (
    REPOSITORY / "harmonizer/bach_rule_induction/rule_bases/k3_clean/v5_16_factors.yaml"
)
DEFAULT_OUTPUT = (
    REPOSITORY
    / "harmonizer/bach_rule_induction/factor_bases/k3_v5_16_reference"
    / "v5_16_reference.factors"
)


def render_factor_program(
    catalogue: dict[str, Any],
    *,
    group_name: str = "k3_v5_16_reference",
    source_label: str = "v5_16_factors.yaml",
) -> str:
    """Render terminal factors over an immutable K3 activation snapshot."""

    lines = [
        f"# Generated from {source_label}; do not edit weights by hand.",
        "# k3_factor_active facts are immutable outputs of the feature evaluator.",
        f"FACTOR_GROUP {group_name}",
    ]
    for record in catalogue["factors"]:
        factor_id = str(record["id"])
        weight = float(record["parameter"]["log_weight"])
        lines.extend(
            [
                f"    FACTOR {factor_id}",
                "    SCOPE $scope",
                f"    LOG_WEIGHT {weight:.17g}",
                "    WHEN",
                f"        ($scope k3_factor_active {factor_id})",
                "    END_FACTOR",
                "",
            ]
        )
    lines.append("END_FACTOR_GROUP")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalogue = yaml.safe_load(args.catalogue.read_text(encoding="utf-8"))
    if not isinstance(catalogue, dict):
        raise ValueError("factor catalogue must be a mapping")
    text = render_factor_program(catalogue)
    groups = parse_factor_groups(text)
    expected = int(catalogue["counts"]["canonical_factors_after_merge"])
    if len(groups) != 1 or len(groups[0].factors) != expected:
        raise ValueError("rendered factor program does not preserve factor count")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"[factor-program] wrote {expected} factors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
