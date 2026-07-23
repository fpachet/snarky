import pytest

from snarky import (
    ComparisonOperator,
    CountPremise,
    Fact,
    FactDelta,
    ForwardEngine,
    IndexedInstantiationStrategy,
    NaiveInstantiationStrategy,
    ParseError,
    SemiNaiveInstantiationStrategy,
    UniquePremise,
    parse_rule_groups,
    parse_rules,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


@pytest.mark.parametrize(
    "strategy",
    (
        NaiveInstantiationStrategy(),
        IndexedInstantiationStrategy(),
        SemiNaiveInstantiationStrategy(),
    ),
)
def test_count_and_unique_are_equivalent_across_strategies(
    strategy: (
        NaiveInstantiationStrategy
        | IndexedInstantiationStrategy
        | SemiNaiveInstantiationStrategy
    ),
) -> None:
    rules = parse_rules(
        """
        RULE classify_pair
        WHEN
            ($item group $group)
            COUNT == 2
                ($peer group $group)
            END_COUNT
            UNIQUE
                ($item label $label)
            END_UNIQUE
        THEN
            ADD ($item classified pair)
        END
        """
    )
    result = ForwardEngine(rules, strategy=strategy).run(
        (
            _fact("(a group g)"),
            _fact("(b group g)"),
            _fact("(c group h)"),
            _fact("(a label first)"),
            _fact("(b label second)"),
            _fact("(c label third)"),
            _fact("(c label fourth)"),
        )
    )

    assert _fact("(a classified pair)") in result.facts
    assert _fact("(b classified pair)") in result.facts
    assert _fact("(c classified pair)") not in result.facts


def test_parser_builds_explicit_count_and_unique_premises() -> None:
    rule = parse_rules(
        """
        RULE aggregate
        WHEN
            seed
            COUNT >= 1
                ($item kind useful)
            END_COUNT
            UNIQUE
                ($item selected yes)
            END_UNIQUE
        THEN
            ADD result
        END
        """
    )[0]

    count_premise = rule.premises[1]
    unique_premise = rule.premises[2]
    assert isinstance(count_premise, CountPremise)
    assert count_premise.operator is ComparisonOperator.GE
    assert count_premise.expected == 1
    assert isinstance(unique_premise, UniquePremise)


def test_simple_count_is_updated_from_a_removal_delta() -> None:
    rule = parse_rules(
        """
        RULE detect_single
        WHEN
            ($item seed yes)
            COUNT == 1
                ($item candidate $value)
            END_COUNT
        THEN
            ADD ($item single yes)
        END
        """
    )[0]
    before = (
        _fact("(a seed yes)"),
        _fact("(a candidate 1)"),
        _fact("(a candidate 2)"),
    )
    removed = _fact("(a candidate 2)")
    after = tuple(fact for fact in before if fact != removed)
    strategy = IndexedInstantiationStrategy()

    assert strategy.instantiate(rule, before) == ()
    strategy.invalidate(frozenset((removed,)))
    activations = strategy.instantiate(
        rule,
        after,
        FactDelta(removed=frozenset((removed,)), revision=1),
    )

    assert len(activations) == 1
    assert strategy.metrics.query_counter_updates > 0


def test_count_refraction_tracks_additions_that_change_cardinality() -> None:
    derive, add_second, clear = parse_rule_groups(
        """
        GROUP derive
            RULE derive_available
            WHEN
                ($item seed yes)
                COUNT == 1
                    ($item candidate $value)
                END_COUNT
            THEN
                ADD ($item available yes)
            END
        END_GROUP

        GROUP add_second
            RULE add_second_candidate
            WHEN
                ($item request_second yes)
            THEN
                ADD ($item candidate 2)
            END
        END_GROUP

        GROUP clear
            RULE clear_second_candidate
            WHEN
                ($item candidate 2)
            THEN
                REMOVE ($item candidate 2)
                REMOVE ($item available yes)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(
        (
            _fact("(a seed yes)"),
            _fact("(a candidate 1)"),
            _fact("(a request_second yes)"),
        )
    )

    first = session.run_group(derive)
    session.run_group(add_second)
    session.run_group(clear)
    reenabled = session.run_group(derive)

    assert first.added_facts == (_fact("(a available yes)"),)
    assert reenabled.added_facts == (_fact("(a available yes)"),)


def test_parser_rejects_malformed_aggregate_blocks() -> None:
    with pytest.raises(ParseError, match="COUNT header"):
        parse_rules(
            """
            RULE malformed
            WHEN
                COUNT approximately 2
                    seed
                END_COUNT
            THEN
                ADD result
            END
            """
        )

    with pytest.raises(ParseError, match="missing END_UNIQUE"):
        parse_rules(
            """
            RULE malformed
            WHEN
                UNIQUE
                    seed
            THEN
                ADD result
            END
            """
        )
