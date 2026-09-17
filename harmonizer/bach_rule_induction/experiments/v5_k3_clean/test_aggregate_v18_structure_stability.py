from __future__ import annotations

from aggregate_v18_structure_stability import _aggregate, _jaccard


def _model(*keys: str) -> dict:
    return {
        "model": {
            "rules": [
                {
                    "feature": {"key": key},
                    "family": "family",
                    "clause": key,
                    "weight": -1.0,
                }
                for key in keys
            ]
        }
    }


def test_jaccard_handles_empty_and_overlapping_sets() -> None:
    assert _jaccard(set(), set()) == 1.0
    assert _jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_aggregate_extracts_only_unanimous_stable_rules() -> None:
    result = _aggregate(
        [
            _model("a", "b"),
            _model("a", "c"),
            _model("a", "b"),
        ]
    )

    assert [row["clause"] for row in result["unanimous_core"]] == ["a"]
    assert result["rules_selected_at_least_3"] == 1
    assert result["rules_selected_at_least_4"] == 0
