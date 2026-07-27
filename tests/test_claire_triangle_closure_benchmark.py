from __future__ import annotations

import pytest

from benchmarks.claire_triangle_closure import (
    WIDTH,
    build_closing_edges,
    build_membership_facts,
    expected_checksum,
    expected_outputs,
    measure_snarky,
    parse_claire_result,
    validate_metrics,
)


def test_parse_claire_triangle_result_ignores_runtime_banner() -> None:
    output = (
        "-- CLAIRE run-time library v 4.1.6 --\n"
        "SNARKY_CLAIRE_TRIANGLE_RESULT groups=2 width=8 "
        "preparation_ns=12000 inference_ns=34000 "
        "rule_firings=128 outputs=128 checksum=192\n"
    )

    assert parse_claire_result(output) == {
        "groups": 2,
        "width": 8,
        "rule_firings": 128,
        "outputs": 128,
        "checksum": 192,
        "preparation_seconds": 0.000012,
        "seconds": 0.000034,
    }


def test_parse_claire_triangle_result_rejects_missing_marker() -> None:
    with pytest.raises(ValueError, match="no triangle result marker"):
        parse_claire_result("-- CLAIRE run-time library v 4.1.6 --\n")


def test_parse_claire_triangle_result_rejects_malformed_marker() -> None:
    with pytest.raises(ValueError, match="malformed CLAIRE triangle marker"):
        parse_claire_result(
            "SNARKY_CLAIRE_TRIANGLE_RESULT groups=2 width=8\n"
        )


def test_triangle_fact_builders_create_unique_common_graph() -> None:
    memberships = build_membership_facts(3)
    closing_edges = build_closing_edges(3)

    assert len(memberships) == 3 * 2 * WIDTH
    assert len(set(memberships)) == len(memberships)
    assert len(closing_edges) == 3 * WIDTH * WIDTH
    assert len(set(closing_edges)) == len(closing_edges)


def test_triangle_expected_results() -> None:
    assert expected_outputs(3) == 192
    assert expected_checksum(3) == 384


def test_validate_triangle_metrics_rejects_missing_activation() -> None:
    with pytest.raises(RuntimeError, match="rule firings"):
        validate_metrics(
            2,
            {
                "width": WIDTH,
                "rule_firings": 127,
                "outputs": 128,
                "checksum": 192,
            },
        )


def test_snarky_triangle_smoke_uses_partial_join_memory() -> None:
    summary = measure_snarky(2, 1)

    assert summary["rule_firings"] == 128
    assert summary["outputs"] == 128
    assert summary["checksum"] == 192
    assert summary["rule_evaluations"] == 128
    assert summary["rule_skips"] == 128
    assert summary["partial_join_builds"] == 1
    assert summary["partial_join_updates"] == 127
    assert summary["partial_join_bypasses"] == 0
