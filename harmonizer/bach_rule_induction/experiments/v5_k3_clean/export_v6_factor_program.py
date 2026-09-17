#!/usr/bin/env python3
"""Export selected V6 factors to Snarky's side-effect-free FACTOR syntax."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml
from export_v5_16_factor_program import render_factor_program

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SELECTED = FACTOR_BASE / "selected_factors.yaml"
DEFAULT_OUTPUT = FACTOR_BASE / "v6_induced.factors"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--weights-model",
        type=Path,
        help="Optional model whose weights replace the selected conditional weights",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = yaml.safe_load(args.selected.read_text(encoding="utf-8"))
    if not isinstance(selected, dict):
        raise ValueError("selected factor file must be a mapping")
    factors = copy.deepcopy(selected["factors"])
    source_label = args.selected.name
    if args.weights_model is not None:
        model_payload = json.loads(args.weights_model.read_text(encoding="utf-8"))
        learned_weights = {
            rule["feature"]["key"]: float(rule["weight"])
            for rule in model_payload["model"]["rules"]
        }
        for factor in factors:
            key = factor["feature"]["key"]
            if key not in learned_weights:
                raise ValueError(f"Missing learned weight for {key}")
            factor["parameter"]["log_weight"] = learned_weights[key]
            factor["parameter"]["sign"] = (
                "preference" if learned_weights[key] >= 0 else "avoidance"
            )
        if len(learned_weights) != len(factors):
            raise ValueError("Weight model and selected factor structure differ")
        source_label = args.weights_model.name
    catalogue = {
        "counts": {
            "canonical_factors_after_merge": len(factors),
        },
        "factors": factors,
    }
    text = render_factor_program(
        catalogue,
        group_name="k3_v6_induced",
        source_label=source_label,
    )
    (group,) = parse_factor_groups(text)
    if len(group.factors) != len(factors):
        raise ValueError("V6 factor program lost selected factors")
    args.output.write_text(text, encoding="utf-8")
    print(f"[v6-factor-program] wrote {len(group.factors)} factors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
