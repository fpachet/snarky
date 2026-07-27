from __future__ import annotations

import pytest

from benchmarks.claire_talarian_filter import (
    build_filter_facts,
    measure_snarky,
    parse_claire_result,
    validate_metrics,
)


def test_parse_claire_filter_result_ignores_runtime_banner() -> None:
    output = (
        "-- CLAIRE run-time library v 4.1.6 --\n"
        "SNARKY_CLAIRE_FILTER_RESULT size=10 preparation_ns=12000 "
        "inference_ns=34000 rule_firings=100 outputs=100 "
        "checksum=400\n"
    )

    assert parse_claire_result(output) == {
        "size": 10,
        "rule_firings": 100,
        "outputs": 100,
        "checksum": 400,
        "preparation_seconds": 0.000012,
        "seconds": 0.000034,
    }


def test_build_filter_facts_creates_ten_unique_facts_per_frame() -> None:
    facts = build_filter_facts(3)

    assert len(facts) == 30
    assert len(set(facts)) == 30


def test_validate_filter_metrics_rejects_missing_activation() -> None:
    with pytest.raises(RuntimeError, match="rule firings"):
        validate_metrics(
            2,
            {
                "rule_firings": 19,
                "outputs": 20,
                "checksum": 80,
            },
        )


def test_snarky_filter_smoke() -> None:
    summary = measure_snarky(3, 1)

    assert summary["rule_firings"] == 30
    assert summary["outputs"] == 30
    assert summary["checksum"] == 120
    assert summary["rule_evaluations"] == 39
    assert summary["rule_skips"] == 561
    assert summary["event_rule_evaluations"] == 39
    assert summary["event_rule_candidates"] == 48
