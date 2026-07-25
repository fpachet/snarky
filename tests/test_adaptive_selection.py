from snarky import parse_rules
from snarky.instantiation.adaptive_selection import (
    _AdaptiveFilterSelector,
    _FilterAssessment,
)
from snarky.instantiation.domain_planning import _compile_domain_plan


def _triangle_rule():
    return parse_rules(
        """
        RULE triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )[0]


def test_adaptive_selector_checks_shape_and_table_distribution() -> None:
    plan = _compile_domain_plan(_triangle_rule())
    selector = _AdaptiveFilterSelector(
        enabled=True,
        minimum_domain_rows=10,
        minimum_bucket_ratio=8,
    )

    assert selector.accepts_shape(
        plan,
        4,
        comparisons_supported=True,
    )
    assert selector.accepts_tables(
        plan,
        (100, 100, 1),
        comparisons_supported=True,
    )
    assert not selector.accepts_tables(
        plan,
        (10, 10, 10),
        comparisons_supported=True,
    )


def test_adaptive_selector_tracks_defer_probe_and_decision_lifecycle() -> None:
    rule = _triangle_rule()
    selector = _AdaptiveFilterSelector(
        enabled=True,
        minimum_candidate_reduction=0.10,
        cost_probe_reduction_ceiling=0.75,
        minimum_cost_probe_uses=2,
    )

    first = selector.assess(
        rule,
        row_count=100,
        retained_count=50,
        consistent=True,
    )
    second = selector.assess(
        rule,
        row_count=100,
        retained_count=50,
        consistent=True,
    )

    assert first is _FilterAssessment.DEFER
    assert second is _FilterAssessment.PROBE
    assert selector.record_probe(
        rule,
        filter_elapsed=1.0,
        fallback_elapsed=2.0,
    )
    assert selector.decision(rule) is True
    assert selector.cost_ratios[rule] == 2.0

    selector.clear()

    assert selector.decision(rule) is None
    assert selector.cost_ratios == {}
    assert selector.use_counts == {}


def test_adaptive_selector_commits_clear_filter_outcomes_immediately() -> None:
    rule = _triangle_rule()
    selector = _AdaptiveFilterSelector(enabled=True)

    assert selector.assess(
        rule,
        row_count=100,
        retained_count=100,
        consistent=True,
    ) is _FilterAssessment.REJECT
    assert selector.decision(rule) is False

    selector.clear()

    assert selector.assess(
        rule,
        row_count=100,
        retained_count=0,
        consistent=False,
    ) is _FilterAssessment.SELECT
    assert selector.decision(rule) is True
