from __future__ import annotations

import json
from pathlib import Path

import run_satb_ablation as ablation
import run_satb_group_refit as group_refit


def test_groups_partition_the_readable_catalogue() -> None:
    flattened = [
        rule_id
        for group in group_refit.RULE_GROUPS.values()
        for rule_id in group
    ]
    assert len(flattened) == len(set(flattened))
    assert set(flattened) == set(ablation.RULE_IDS)


def test_each_ablation_keeps_only_other_groups() -> None:
    for removed in group_refit.RULE_GROUPS.values():
        remaining = tuple(
            rule_id for rule_id in ablation.RULE_IDS if rule_id not in removed
        )
        assert set(remaining).isdisjoint(removed)
        assert len(remaining) + len(removed) == len(ablation.RULE_IDS)


def test_canonical_refitted_penalties_exceed_null_controls() -> None:
    results = Path(__file__).resolve().parent / "results"
    authentic = json.loads(
        (results / "v2_5_satb_group_refit.json").read_text(encoding="utf-8")
    )
    null = json.loads(
        (results / "v2_5_satb_group_refit_null.json").read_text(encoding="utf-8")
    )
    authentic_by_group = {
        record["group"]: record["validation_nll_penalty"]
        for record in authentic["model"]["group_ablations"]
    }
    null_by_group = {
        record["group"]: record["validation_nll_penalty"]
        for record in null["model"]["group_ablations"]
    }
    assert authentic["experiment"]["test_opened"] is False
    assert null["experiment"]["test_opened"] is False
    assert all(penalty > 0 for penalty in authentic_by_group.values())
    assert all(
        authentic_by_group[group] > null_by_group[group]
        for group in group_refit.RULE_GROUPS
    )
    assert authentic_by_group["parallels"] > 0.05
    assert abs(null_by_group["parallels"]) < 1e-4
