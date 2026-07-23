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
