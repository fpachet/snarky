from __future__ import annotations

from build_v22_constraint_ablation import (
    build_model,
    constraint_features,
    render_program,
)

from snarky import parse_rule_groups


def test_build_model_uses_only_full_split_survivors() -> None:
    rows = constraint_features()
    audit = {
        "survivors": [
            {
                "feature": {"key": feature.key},
                "full_train": {"testable_opportunities": 10},
                "full_validation": {"testable_opportunities": 3},
            }
            for _, feature in rows
        ]
    }
    source = {
        "experiment": {"id": "source"},
        "model": {"rules": []},
    }

    model, catalogue = build_model(source, audit)
    (parsed_group,) = parse_rule_groups(render_program(catalogue))

    assert len(rows) == 23
    assert len(model["model"]["constraints"]) == 23
    assert catalogue["counts"]["logical_schemas"] == 7
    assert len(parsed_group.rules) == 23
