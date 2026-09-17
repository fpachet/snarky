import pytest

from snarky import (
    ExistsPremise,
    Fact,
    FactDelta,
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


def test_query_registered_after_unrelated_deltas_is_invalidated_later() -> None:
    positive_rule = parse_rules(
        """
        RULE observe_source
        WHEN
            ($item source yes)
        THEN
            ADD ($item observed yes)
        END
        """
    )[0]
    query_rule = parse_rules(
        """
        RULE expose_unblocked
        WHEN
            ($item source yes)
            NOT EXISTS ($item blocked yes)
        THEN
            ADD ($item available yes)
        END
        """
    )[0]
    source = _fact("(a source yes)")
    blocked = _fact("(a blocked yes)")
    strategy = SemiNaiveInstantiationStrategy()

    strategy.instantiate(
        positive_rule,
        (source,),
        FactDelta(added=(source,), revision=1),
    )
    assert strategy.instantiate(query_rule, (source,), None)

    assert (
        strategy.instantiate(
            query_rule,
            (source, blocked),
            FactDelta(added=(blocked,), revision=2),
        )
        == ()
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


def test_compact_existentials_and_explicit_negative_terminator() -> None:
    compact = parse_rules(
        """
        RULE compact
        WHEN
            (cell kind cell)
            EXISTS (cell candidate 1)
            NOT EXISTS (cell rejected 1)
        THEN
            ADD compact_ok
        END
        """
    )[0]
    block = parse_rules(
        """
        RULE negative_block
        WHEN
            (cell kind cell)
            NOT EXISTS
                (cell candidate $value)
                $value != 1
            END_NOT_EXISTS
        THEN
            ADD block_ok
        END
        """
    )[0]

    assert isinstance(compact.premises[1], ExistsPremise)
    assert isinstance(compact.premises[2], NotExistsPremise)
    assert isinstance(block.premises[1], NotExistsPremise)

    result = ForwardEngine((compact, block)).run(
        (
            _fact("(cell kind cell)"),
            _fact("(cell candidate 1)"),
        )
    )
    assert _fact("compact_ok") in result.facts
    assert _fact("block_ok") in result.facts


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


def test_group_without_negative_dependencies_skips_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    group = parse_rule_groups(
        """
        GROUP derive
            RULE derive_result
            WHEN
                seed
            THEN
                ADD result
            END
        END_GROUP
        """
    )[0]
    session = ForwardEngine(()).create_session((_fact("seed"),))

    def fail_if_called(_: tuple[Fact, ...]) -> None:
        raise AssertionError("negative refraction should not be reconciled")

    monkeypatch.setattr(
        session,
        "_reconcile_negative_refraction",
        fail_if_called,
    )

    result = session.run_group(group)

    assert result.added_facts == (_fact("result"),)


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
    assert strategy.metrics.activation_cache_hits == 1


def test_composite_existential_promotes_a_residual_witness() -> None:
    rule = parse_rules(
        """
        RULE derive_supported
        WHEN
            (query seed yes)
            EXISTS
                (domain candidate $value)
                (relation allows SEQ[key $value])
            END_EXISTS
        THEN
            ADD (query supported yes)
        END
        """
    )[0]
    seed = _fact("(query seed yes)")
    first_candidate = _fact("(domain candidate a)")
    second_candidate = _fact("(domain candidate b)")
    first_pair = _fact("(relation allows SEQ[key a])")
    second_pair = _fact("(relation allows SEQ[key b])")
    distractors = tuple(
        _fact(f"(noise-{index} irrelevant value)")
        for index in range(124)
    )
    initial = (
        seed,
        first_candidate,
        second_candidate,
        first_pair,
        second_pair,
        *distractors,
    )
    strategy = IndexedInstantiationStrategy()

    first = strategy.instantiate(rule, initial)
    strategy.invalidate(frozenset((first_candidate,)))
    remaining = tuple(fact for fact in initial if fact != first_candidate)
    second = strategy.instantiate(
        rule,
        remaining,
        FactDelta(
            removed=frozenset((first_candidate,)),
            revision=1,
        ),
    )

    assert len(first) == 1
    assert len(second) == 1
    assert second_candidate in second[0].premise_facts
    assert strategy.metrics.residual_witness_promotions == 1


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
