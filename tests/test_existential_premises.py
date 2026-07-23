import pytest

from snarky import (
    ExistsPremise,
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    NaiveInstantiationStrategy,
    NotExistsPremise,
    ParseError,
    SemiNaiveInstantiationStrategy,
    parse_rule_groups,
    parse_rules,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


SINGLE_RULE = """
RULE derive_single
WHEN
    ($cell candidate $value)
    NOT EXISTS
        ($cell candidate $other)
        $other != $value
    END_EXISTS
THEN
    ADD ($cell solved $value)
END
"""


@pytest.mark.parametrize(
    "strategy",
    [
        NaiveInstantiationStrategy(),
        IndexedInstantiationStrategy(),
        SemiNaiveInstantiationStrategy(),
    ],
)
def test_correlated_not_exists_is_consistent_across_strategies(
    strategy: (
        NaiveInstantiationStrategy
        | IndexedInstantiationStrategy
        | SemiNaiveInstantiationStrategy
    ),
) -> None:
    rules = parse_rules(SINGLE_RULE)

    single = ForwardEngine(rules, strategy=strategy).run(
        (_fact("(r1c1 candidate 5)"),)
    )

    assert _fact("(r1c1 solved 5)") in single.facts
    assert isinstance(rules[0].premises[1], NotExistsPremise)


def test_correlated_not_exists_rejects_a_present_witness() -> None:
    rules = parse_rules(SINGLE_RULE)

    result = ForwardEngine(rules).run(
        (
            _fact("(r1c1 candidate 5)"),
            _fact("(r1c1 candidate 7)"),
        )
    )

    assert not any(
        fact.entity == parse_term("(r1c1 solved 5)")
        for fact in result.derived_facts
    )


def test_exists_uses_witness_facts_without_exporting_local_bindings() -> None:
    rules = parse_rules(
        """
        RULE detect_peer
        WHEN
            ($cell row $row)
            EXISTS
                ($peer row $row)
                $peer != $cell
            END_EXISTS
        THEN
            ADD ($cell has_peer VRAI)
        END
        """
    )

    result = ForwardEngine(rules).run(
        (
            _fact("(a row 1)"),
            _fact("(b row 1)"),
        )
    )

    assert isinstance(rules[0].premises[1], ExistsPremise)
    derivation = result.provenance.minimal_derivation(
        _fact("(a has_peer VRAI)")
    )
    assert derivation is not None
    assert _fact("(b row 1)") in derivation.premises


def test_not_exists_becomes_true_after_a_correlated_witness_is_removed() -> None:
    derive = parse_rule_groups(f"GROUP derive\n{SINGLE_RULE}\nEND_GROUP")[0]
    eliminate = parse_rule_groups(
        """
        GROUP eliminate
            RULE eliminate_seven
            WHEN
                (r1c1 candidate 7)
            THEN
                REMOVE (r1c1 candidate 7)
            END
        END_GROUP
        """
    )[0]
    session = ForwardEngine(()).create_session(
        (
            _fact("(r1c1 candidate 5)"),
            _fact("(r1c1 candidate 7)"),
        )
    )

    before = session.run_group(derive)
    session.run_group(eliminate)
    after = session.run_group(derive)

    assert before.added_facts == ()
    assert after.added_facts == (_fact("(r1c1 solved 5)"),)


def test_negative_refraction_tracks_only_relevant_additions() -> None:
    derive, add_irrelevant, add_blocker, clear_blocker = parse_rule_groups(
        """
        GROUP derive
            RULE derive_available
            WHEN
                seed
                NOT EXISTS
                    blocker
                END_EXISTS
            THEN
                ADD available
            END
        END_GROUP

        GROUP add_irrelevant
            RULE add_noise
            WHEN
                request_noise
            THEN
                ADD noise
            END
        END_GROUP

        GROUP add_blocker
            RULE block
            WHEN
                request_blocker
            THEN
                ADD blocker
            END
        END_GROUP

        GROUP clear_blocker
            RULE unblock
            WHEN
                blocker
            THEN
                REMOVE blocker
                REMOVE available
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(
        (
            _fact("seed"),
            _fact("request_noise"),
            _fact("request_blocker"),
        )
    )

    first = session.run_group(derive)
    session.run_group(add_irrelevant)
    unchanged = session.run_group(derive)
    session.run_group(add_blocker)
    session.run_group(clear_blocker)
    reenabled = session.run_group(derive)

    assert first.added_facts == (_fact("available"),)
    assert unchanged.fired_activation_count == 0
    assert reenabled.added_facts == (_fact("available"),)


def test_repeated_existential_queries_are_cached_per_instantiation() -> None:
    rules = parse_rules(
        """
        RULE reuse_witness
        WHEN
            ($item group $group)
            ($item tag $tag)
            EXISTS
                ($peer group $group)
                $peer != $item
            END_EXISTS
        THEN
            ADD ($item witnessed $tag)
        END
        """
    )
    strategy = IndexedInstantiationStrategy()

    result = ForwardEngine(rules, strategy=strategy).run(
        (
            _fact("(a group g)"),
            _fact("(a tag first)"),
            _fact("(a tag second)"),
            _fact("(b group g)"),
        )
    )

    assert _fact("(a witnessed first)") in result.facts
    assert _fact("(a witnessed second)") in result.facts
    assert strategy.metrics.witness_cache_hits > 0


def test_existential_witness_cache_survives_an_unchanged_snapshot() -> None:
    rule = parse_rules(SINGLE_RULE)[0]
    facts = (_fact("(r1c1 candidate 5)"),)
    strategy = IndexedInstantiationStrategy()

    first = strategy.instantiate(rule, facts)
    misses_after_first = strategy.metrics.witness_cache_misses
    second = strategy.instantiate(rule, facts, ())

    assert second == first
    assert strategy.metrics.witness_cache_misses == misses_after_first
    assert strategy.metrics.witness_cache_hits > 0


def test_simple_negative_blocker_expires_only_correlated_activation() -> None:
    derive, block, clear = parse_rule_groups(
        """
        GROUP derive
            RULE derive_available
            WHEN
                ($item seed yes)
                NOT EXISTS
                    ($item blocker yes)
                END_EXISTS
            THEN
                ADD ($item available yes)
            END
        END_GROUP

        GROUP block
            RULE add_blocker
            WHEN
                ($item block_requested yes)
            THEN
                ADD ($item blocker yes)
            END
        END_GROUP

        GROUP clear
            RULE clear_blocker
            WHEN
                ($item blocker yes)
            THEN
                REMOVE ($item blocker yes)
                REMOVE ($item available yes)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(
        (
            _fact("(a seed yes)"),
            _fact("(b seed yes)"),
            _fact("(a block_requested yes)"),
        )
    )

    first = session.run_group(derive)
    session.run_group(block)
    session.run_group(clear)
    reenabled = session.run_group(derive)

    assert set(first.added_facts) == {
        _fact("(a available yes)"),
        _fact("(b available yes)"),
    }
    assert reenabled.added_facts == (_fact("(a available yes)"),)
    assert reenabled.fired_activation_count == 1


def test_parser_rejects_malformed_or_unsafe_existential_blocks() -> None:
    with pytest.raises(ParseError, match="missing END_EXISTS"):
        parse_rules(
            """
            RULE broken
            WHEN
                seed
                NOT EXISTS
                    other
            THEN
                ADD result
            END
            """
        )

    with pytest.raises(ParseError, match=r"unbound variables: \$local"):
        parse_rules(
            """
            RULE unsafe
            WHEN
                seed
                EXISTS
                    ($local relation value)
                END_EXISTS
                $local != value
            THEN
                ADD result
            END
            """
        )
