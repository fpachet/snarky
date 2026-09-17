from __future__ import annotations

import audit_v20c_named_root_transitions as audit


def test_aggregate_measures_information_not_present_in_bass_transition() -> None:
    rows = [
        {
            "piece_id": "a",
            "mode": "major",
            "counts": {
                "adjacent_edges": 4,
                "named_unique_edges": 3,
                "root_change_edges": 2,
                "different_from_bass_transition": 1,
            },
            "transitions": {
                "major:0>0": 1,
                "major:0>7": 2,
            },
            "arrivals": {"major:0": 1, "major:7": 2},
            "departures": {"major:0": 3},
        },
        {
            "piece_id": "b",
            "mode": "major",
            "counts": {
                "adjacent_edges": 2,
                "named_unique_edges": 1,
                "root_change_edges": 1,
                "different_from_bass_transition": 1,
            },
            "transitions": {"major:7>0": 1},
            "arrivals": {"major:0": 1},
            "departures": {"major:7": 1},
        },
    ]

    summary = audit._aggregate(rows)

    assert summary["coverage"]["named_unique_edge_rate"] == 4 / 6
    assert summary["coverage"]["root_change_rate_among_named"] == 3 / 4
    assert summary["coverage"]["different_from_bass_transition_rate"] == 0.5
    transition = next(
        row
        for row in summary["transitions"]
        if row["previous_root_degree"] == 0
        and row["current_root_degree"] == 7
    )
    assert transition["blocks"] == 2
    assert transition["piece_support"] == 1
    assert transition["conditional_probability"] == 2 / 3
    assert transition["arrival_marginal"] == 0.5


def test_markdown_does_not_call_a_marginal_a_rule() -> None:
    result = {
        "experiment": {"pieces": 2},
        "summary": audit._aggregate(
            [
                {
                    "piece_id": "a",
                    "mode": "minor",
                    "counts": {
                        "adjacent_edges": 1,
                        "named_unique_edges": 1,
                        "root_change_edges": 1,
                        "different_from_bass_transition": 1,
                    },
                    "transitions": {"minor:7>0": 1},
                    "arrivals": {"minor:0": 1},
                    "departures": {"minor:7": 1},
                }
            ]
        ),
    }

    report = audit._markdown(result)

    assert "ne sont pas encore des règles" in report
    assert "différente de la transition de basses" in report
