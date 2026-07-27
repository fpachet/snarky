from snarky import (
    Fact,
    FactDelta,
    ForwardEngine,
    IndexedInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    parse_rules,
    parse_term,
)


def test_simple_event_rule_specialization_matches_generic_delta_join() -> None:
    rule = parse_rules(
        """
        RULE positive_value
        WHEN
            ($item value $value)
            $value > 0
        THEN
            ADD ($item accepted $value)
        END
        """
    )[0]
    facts = (
        Fact(parse_term("(a value 2)")),
        Fact(parse_term("(b value 0)")),
        Fact(parse_term("(c unrelated 3)")),
    )
    delta = FactDelta(added=facts, revision=1)
    specialized = SemiNaiveInstantiationStrategy()
    generic = SemiNaiveInstantiationStrategy(use_event_rules=False)

    specialized_activations = specialized.instantiate(rule, facts, delta)
    generic_activations = generic.instantiate(rule, facts, delta)

    assert specialized_activations == generic_activations
    assert len(specialized_activations) == 1
    assert specialized.metrics.event_rule_evaluations == 1
    assert specialized.metrics.event_rule_candidates == 3
    assert generic.metrics.event_rule_evaluations == 0


def test_multi_fact_rule_uses_generic_delta_join() -> None:
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
    right = Fact(parse_term("(node right b)"))
    strategy = SemiNaiveInstantiationStrategy()

    activations = strategy.instantiate(
        rule,
        (left, right),
        FactDelta(added=(left, right), revision=1),
    )

    assert len(activations) == 1
    assert strategy.metrics.event_rule_evaluations == 0


def test_event_rule_setting_is_preserved_across_branch_forks() -> None:
    strategy = SemiNaiveInstantiationStrategy(
        use_event_rules=False,
        use_partial_join_memory=False,
    )

    branch = strategy.fork_for_branch()

    assert branch.use_event_rules is False
    assert branch.use_partial_join_memory is False


def test_partial_memory_matches_generic_across_add_and_remove() -> None:
    rule = parse_rules(
        """
        RULE compatible_after_filter
        WHEN
            ($group left $left)
            ($group right $right)
            $left != $right
            ($left compatible $right)
        THEN
            ADD ($left paired_with $right)
        END
        """
    )[0]
    left = Fact(parse_term("(group left a)"))
    first_right = Fact(parse_term("(group right b1)"))
    second_right = Fact(parse_term("(group right b2)"))
    first_edge = Fact(parse_term("(a compatible b1)"))
    second_edge = Fact(parse_term("(a compatible b2)"))
    facts = (left, first_right, second_right)
    memory = SemiNaiveInstantiationStrategy()
    generic = SemiNaiveInstantiationStrategy(
        use_partial_join_memory=False,
    )

    assert memory.instantiate(rule, facts) == generic.instantiate(rule, facts)
    facts = (*facts, first_edge)
    first_delta = FactDelta(added=(first_edge,), revision=1)
    assert memory.instantiate(rule, facts, first_delta) == (
        generic.instantiate(rule, facts, first_delta)
    )
    facts = (*facts, second_edge)
    second_delta = FactDelta(added=(second_edge,), revision=2)
    assert memory.instantiate(rule, facts, second_delta) == (
        generic.instantiate(rule, facts, second_delta)
    )

    memory.invalidate(frozenset((first_right,)))
    generic.invalidate(frozenset((first_right,)))
    facts = tuple(fact for fact in facts if fact != first_right)
    removal = FactDelta(
        removed=frozenset((first_right,)),
        revision=3,
    )
    assert memory.instantiate(rule, facts, removal) == (
        generic.instantiate(rule, facts, removal)
    )
    assert memory.metrics.partial_join_builds == 1
    assert memory.metrics.partial_join_updates == 2


def test_partial_memory_keeps_comparison_levels_outside_state_budget() -> None:
    rule = parse_rules(
        """
        RULE compatible_after_filter
        WHEN
            ($group left $left)
            ($group right only_right)
            $left != only_right
            ($left compatible only_right)
        THEN
            ADD ($left accepted yes)
        END
        """
    )[0]
    first_left = Fact(parse_term("(group left first)"))
    second_left = Fact(parse_term("(group left second)"))
    right = Fact(parse_term("(group right only_right)"))
    first_edge = Fact(parse_term("(first compatible only_right)"))
    second_edge = Fact(parse_term("(second compatible only_right)"))
    strategy = SemiNaiveInstantiationStrategy(partial_join_limit=5)
    facts = (first_left, second_left, right)

    assert strategy.instantiate(rule, facts) == ()
    facts = (*facts, first_edge)
    assert len(
        strategy.instantiate(
            rule,
            facts,
            FactDelta(added=(first_edge,), revision=1),
        )
    ) == 1
    facts = (*facts, second_edge)
    assert len(
        strategy.instantiate(
            rule,
            facts,
            FactDelta(added=(second_edge,), revision=2),
        )
    ) == 1
    assert strategy.metrics.partial_join_builds == 1
    assert strategy.metrics.partial_join_bypasses == 0


def test_partial_memory_falls_back_when_prefix_exceeds_budget() -> None:
    rule = parse_rules(
        """
        RULE compatible_after_filter
        WHEN
            ($group left $left)
            ($group right $right)
            $left != $right
            ($left compatible $right)
        THEN
            ADD ($left paired_with $right)
        END
        """
    )[0]
    left = Fact(parse_term("(group left a)"))
    right = Fact(parse_term("(group right b)"))
    edge = Fact(parse_term("(a compatible b)"))
    strategy = SemiNaiveInstantiationStrategy(partial_join_limit=1)

    assert strategy.instantiate(rule, (left, right)) == ()
    activations = strategy.instantiate(
        rule,
        (left, right, edge),
        FactDelta(added=(edge,), revision=1),
    )

    assert len(activations) == 1
    assert strategy.metrics.partial_join_builds == 0
    assert strategy.metrics.partial_join_bypasses == 1


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


def test_adaptive_structural_index_uses_bound_sequence_elements() -> None:
    rule = parse_rules(
        """
        RULE find_structured_pair
        WHEN
            (query relation $relation)
            (query left $left)
            ($relation allows SEQ[$left $right])
        THEN
            ADD (result value $right)
        END
        """
    )[0]
    facts = (
        Fact(parse_term("(query relation relation-a)")),
        Fact(parse_term("(query left left-17)")),
        *tuple(
            Fact(
                parse_term(
                    f"(relation-a allows SEQ[left-{index} right-{index}])"
                )
            )
            for index in range(40)
        ),
    )
    strategy = IndexedInstantiationStrategy()

    activations = strategy.instantiate(rule, facts)

    assert len(activations) == 1
    assert strategy.metrics.match_attempts == 3


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


def test_large_ordered_fact_set_keeps_stable_delta_ranks() -> None:
    rule = parse_rules(
        """
        RULE select_target
        WHEN
            (target relation $value)
        THEN
            ADD (result value $value)
        END
        """
    )[0]
    old = Fact(parse_term("(target relation old)"))
    new = Fact(parse_term("(target relation new)"))
    noise = tuple(
        Fact(parse_term(f"(noise-{index} unrelated value)"))
        for index in range(1_600)
    )
    initial = (old, *noise)
    strategy = SemiNaiveInstantiationStrategy(use_event_rules=False)

    first = strategy.instantiate(rule, initial)
    strategy.invalidate(frozenset((old,)))
    updated = (*noise, new)
    second = strategy.instantiate(
        rule,
        updated,
        FactDelta(
            added=(new,),
            removed=frozenset((old,)),
            revision=1,
        ),
    )

    assert first[0].substitution.key == (("value", parse_term("old")),)
    assert second[0].substitution.key == (("value", parse_term("new")),)
    assert strategy.metrics.index_builds == 1
    assert strategy.metrics.index_removals == 1
