from benchmarks.incremental_conjunctions import (
    build_compatibility_facts,
    build_membership_facts,
    run,
)


def test_conjunction_fact_builders_have_expected_cardinality() -> None:
    assert len(build_membership_facts(3, 4)) == 24
    assert len(build_compatibility_facts(3, 4)) == 48


def test_incremental_conjunctions_smoke() -> None:
    payload = run((2,), 2, 1, barrier_group_counts=(2,))
    (result,) = payload["results"]
    (barrier,) = payload["barrier_results"]

    assert result["expected_outputs"] == 8
    assert result["cold"]["outputs"] == 8
    assert result["streamed"]["outputs"] == 8
    assert result["cold"]["facts"] == result["streamed"]["facts"] == 24
    assert result["cold"]["fired_activations"] == 8
    assert result["streamed"]["fired_activations"] == 8
    assert result["streamed"]["rule_evaluations"] == 8
    assert result["streamed"]["rule_skips"] == 8
    assert barrier["memory"]["outputs"] == 8
    assert barrier["generic"]["outputs"] == 8
    assert barrier["memory"]["facts"] == barrier["generic"]["facts"] == 24
    assert barrier["memory"]["partial_join_builds"] == 1
    assert barrier["memory"]["partial_join_bypasses"] == 0
    assert barrier["generic"]["partial_join_builds"] == 0
