from snarky import (
    Fact,
    FactDelta,
    ForwardEngine,
    IndexedInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    parse_rules,
    parse_term,
)


def test_delta_variants_are_unique_and_restore_naive_order() -> None:
    rule = parse_rules(
        """
        RULE combine
        WHEN
            ($x left $a)
            ($x right $b)
        THEN
            ADD ($a paired_with $b)
        END
        """
    )[0]
    old = (
        Fact(parse_term("(node left a1)")),
        Fact(parse_term("(node right b1)")),
    )
    delta = (
        Fact(parse_term("(node left a2)")),
        Fact(parse_term("(node right b2)")),
    )
    all_facts = (*old, *delta)
    indexed = IndexedInstantiationStrategy()
    semi_naive = SemiNaiveInstantiationStrategy()

    indexed.instantiate(rule, old, None)
    semi_naive.instantiate(rule, old, None)
    exhaustive = indexed.instantiate(rule, all_facts, delta)
    incremental = semi_naive.instantiate(rule, all_facts, delta)

    expected = tuple(
        activation
        for activation in exhaustive
        if any(fact in delta for fact in activation.premise_facts)
    )
    assert incremental == expected
    assert len(incremental) == 3


def test_semi_naive_handles_mutually_recursive_rules() -> None:
    rules = parse_rules(
        """
        RULE p_to_q
        WHEN
            ($x p $y)
        THEN
            ADD ($x q $y)
        END

        RULE q_to_r
        WHEN
            ($x q $y)
        THEN
            ADD ($x r $y)
        END

        RULE r_to_p
        WHEN
            ($x r $y)
        THEN
            ADD ($x p $y)
        END
        """
    )
    initial = (Fact(parse_term("(a p b)")),)

    naive = ForwardEngine(rules).run(initial)
    semi_naive = ForwardEngine(
        rules,
        strategy=SemiNaiveInstantiationStrategy(),
    ).run(initial)

    assert semi_naive.facts == naive.facts
    assert semi_naive.derivations == naive.derivations
    assert semi_naive.cycles == naive.cycles


def test_semi_naive_preserves_textual_comparison_barriers() -> None:
    rule = parse_rules(
        """
        RULE comparison_before_binding
        WHEN
            ($x value $value)
            $later == 1
            ($x later $later)
        THEN
            ADD ($x result $value)
        END
        """
    )[0]
    initial = (Fact(parse_term("(item value 5)")),)
    delta = (Fact(parse_term("(item later 1)")),)
    all_facts = (*initial, *delta)
    exhaustive = IndexedInstantiationStrategy()
    semi_naive = SemiNaiveInstantiationStrategy()

    exhaustive.instantiate(rule, initial, None)
    semi_naive.instantiate(rule, initial, None)

    assert exhaustive.instantiate(rule, all_facts, delta) == ()
    assert semi_naive.instantiate(rule, all_facts, delta) == ()


def test_compound_indexes_intersect_two_bound_triple_positions() -> None:
    rule = parse_rules(
        """
        RULE find_exact_relation
        WHEN
            (target relation $value)
        THEN
            ADD (result value $value)
        END
        """
    )[0]
    facts = (
        Fact(parse_term("(target relation answer)")),
        *tuple(
            Fact(parse_term(f"(target other value{index})"))
            for index in range(40)
        ),
        *tuple(
            Fact(parse_term(f"(node{index} relation value{index})"))
            for index in range(40)
        ),
    )
    strategy = IndexedInstantiationStrategy()

    activations = strategy.instantiate(rule, facts)

    assert len(activations) == 1
    assert strategy.metrics.match_attempts == 1


def test_bounded_partial_join_memory_updates_from_both_delta_kinds() -> None:
    rule = parse_rules(
        """
        RULE combine
        WHEN
            ($item left $left)
            ($item right $right)
        THEN
            ADD ($left paired_with $right)
        END
        """
    )[0]
    left = Fact(parse_term("(node left a)"))
    first_right = Fact(parse_term("(node right b1)"))
    second_right = Fact(parse_term("(node right b2)"))
    strategy = IndexedInstantiationStrategy(partial_join_limit=100)

    initial = (left, first_right)
    first = strategy.instantiate(rule, initial)
    with_addition = strategy.instantiate(
        rule,
        (*initial, second_right),
        FactDelta(added=(second_right,), revision=1),
    )
    strategy.invalidate(frozenset((first_right,)))
    after_removal = strategy.instantiate(
        rule,
        (left, second_right),
        FactDelta(removed=frozenset((first_right,)), revision=2),
    )

    assert len(first) == 1
    assert len(with_addition) == 2
    assert len(after_removal) == 1
    assert after_removal[0].premise_facts == (left, second_right)
    assert strategy.metrics.partial_join_builds == 1
    assert strategy.metrics.partial_join_updates == 2
