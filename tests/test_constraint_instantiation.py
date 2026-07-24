import random
from collections.abc import MutableMapping

from snarky import (
    AdaptiveInstantiationStrategy,
    ComparisonPremise,
    ConstraintInstantiationStrategy,
    Fact,
    FactDelta,
    ForwardEngine,
    IndexedInstantiationStrategy,
    InstantiationMetrics,
    NaiveInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    Term,
    Variable,
    parse_rules,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


class _CountingPropagator:
    def __init__(self) -> None:
        self.calls = 0

    def accepts(self, premise: ComparisonPremise) -> bool:
        return True

    def revise(
        self,
        premise: ComparisonPremise,
        domains: MutableMapping[Variable, set[Term]],
        metrics: InstantiationMetrics,
    ) -> set[Variable] | None:
        self.calls += 1
        return set()


def test_custom_domain_propagator_is_used_before_builtin_ones() -> None:
    (rule,) = parse_rules(
        """
        RULE custom_propagator
        WHEN
            (left value $left)
            (right value $right)
            $left < $right
        THEN
            ADD ($left before $right)
        END
        """
    )
    facts = (
        _fact("(left value 1)"),
        _fact("(right value 2)"),
    )
    propagator = _CountingPropagator()
    strategy = ConstraintInstantiationStrategy(
        propagators=(propagator,),
    )

    assert strategy.instantiate(rule, facts) == (
        NaiveInstantiationStrategy().instantiate(rule, facts)
    )
    assert propagator.calls > 0


def test_domain_filter_preserves_activations_and_reduces_join_candidates() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    size = 40
    facts = (
        *(
            _fact(f"(x{x_index} p y{y_index})")
            for x_index in range(size)
            for y_index in range(size)
        ),
        _fact("(x0 q z0)"),
        _fact("(y0 r z0)"),
    )
    indexed = IndexedInstantiationStrategy()
    constrained = ConstraintInstantiationStrategy()

    expected = indexed.instantiate(rule, facts)
    actual = constrained.instantiate(rule, facts)

    assert actual == expected
    assert len(actual) == 1
    assert constrained.metrics.match_attempts == 3
    assert constrained.metrics.match_attempts < indexed.metrics.match_attempts
    assert constrained.metrics.domain_candidates_removed >= size * size - 1
    assert constrained.metrics.domain_values_removed > 0


def test_adaptive_strategy_selects_filter_for_late_selective_table() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    size = 16
    facts = (
        *(
            _fact(f"(x{x_index} p y{y_index})")
            for x_index in range(size)
            for y_index in range(size)
        ),
        *(
            _fact(f"(x{x_index} q z{z_index})")
            for x_index in range(size)
            for z_index in range(size)
        ),
        _fact("(y0 r z0)"),
    )
    strategy = AdaptiveInstantiationStrategy(
        minimum_observed_speedup=0.001,
    )

    expected = IndexedInstantiationStrategy().instantiate(rule, facts)
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.metrics.domain_filter_selections == 1
    assert strategy.metrics.domain_filter_rejections == 0
    assert strategy.metrics.domain_cost_probes == 0


def test_adaptive_strategy_rejects_observably_expensive_filter() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    size = 16
    facts = (
        *(
            _fact(f"(x{x_index} p y{y_index})")
            for x_index in range(size)
            for y_index in range(size)
        ),
        *(
            _fact(f"(x{x_index} q z{z_index})")
            for x_index in range(size)
            for z_index in range(size)
        ),
        _fact("(y0 r z0)"),
    )
    strategy = AdaptiveInstantiationStrategy(
        minimum_observed_speedup=1_000_000,
        cost_probe_reduction_ceiling=1.0,
        minimum_cost_probe_uses=1,
    )

    expected = SemiNaiveInstantiationStrategy().instantiate(rule, facts)
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.metrics.domain_cost_probes == 1
    assert strategy.metrics.domain_cost_probe_rejections == 1
    assert strategy.metrics.domain_filter_rejections == 1
    assert strategy.metrics.domain_filter_fallbacks == 2
    assert strategy.metrics.domain_filter_probe_seconds > 0
    assert strategy.metrics.domain_fallback_probe_seconds > 0


def test_adaptive_strategy_rejects_filter_for_uniform_small_joins() -> None:
    (rule,) = parse_rules(
        """
        RULE aligned_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    size = 64
    facts = tuple(
        fact
        for index in range(size)
        for fact in (
            _fact(f"(x{index} p y{index})"),
            _fact(f"(x{index} q z{index})"),
            _fact(f"(y{index} r z{index})"),
        )
    )
    strategy = AdaptiveInstantiationStrategy()

    expected = IndexedInstantiationStrategy().instantiate(rule, facts)
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.metrics.domain_filter_runs == 0
    assert strategy.metrics.domain_filter_rejections == 1
    assert strategy.metrics.domain_filter_fallbacks == 1


def test_adaptive_strategy_keeps_indexed_matching_for_acyclic_chain() -> None:
    size = 12
    premises = "\n".join(
        f"            ($value_{index} edge_{index} $value_{index + 1})"
        for index in range(size)
    )
    (rule,) = parse_rules(
        f"""
        RULE propagation_chain
        WHEN
{premises}
            ($value_{size} fixed yes)
        THEN
            ADD ($value_0 solution $value_{size})
        END
        """
    )
    facts = (
        *(
            _fact(f"(value{value} edge_{edge} value{value})")
            for edge in range(size)
            for value in range(size)
        ),
        _fact("(value0 fixed yes)"),
    )
    strategy = AdaptiveInstantiationStrategy()

    expected = IndexedInstantiationStrategy().instantiate(rule, facts)
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.metrics.domain_filter_runs == 0
    assert strategy.metrics.domain_filter_rejections == 1


def test_adaptive_strategy_rejects_unspecialized_arithmetic_comparison() -> None:
    (rule,) = parse_rules(
        """
        RULE comparison_join
        WHEN
            ($x p $y)
            ($x q $z)
            CONSTRAINT $y + 1 != $z
        THEN
            ADD ($x solution yes)
        END
        """
    )
    facts = tuple(
        fact
        for index in range(128)
        for fact in (
            _fact(f"(x{index} p {index})"),
            _fact(f"(x{index} q {index})"),
        )
    )
    strategy = AdaptiveInstantiationStrategy()

    expected = IndexedInstantiationStrategy().instantiate(rule, facts)
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.metrics.domain_filter_runs == 0
    assert strategy.metrics.domain_filter_rejections == 1


def test_specialized_order_comparison_filters_without_cartesian_product() -> None:
    (rule,) = parse_rules(
        """
        RULE ordered_values
        WHEN
            (left value $left)
            (right value $right)
            $left < $right
        THEN
            ADD ($left accepted $right)
        END
        """
    )
    facts = (
        *(_fact(f"(left value {value})") for value in range(1, 81)),
        _fact("(right value 2)"),
    )
    strategy = ConstraintInstantiationStrategy()

    expected = IndexedInstantiationStrategy().instantiate(rule, facts)
    assert strategy.instantiate(rule, facts) == expected
    assert strategy.metrics.domain_specialized_revisions > 0
    assert strategy.metrics.domain_combinations_tested == 0
    assert strategy.metrics.domain_candidates_removed == 79


def test_arithmetic_constraint_propagates_bidirectionally() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_sum
        WHEN
            (left value $left)
            (right value $right)
            (total value $total)
            CONSTRAINT $left + $right == $total
        THEN
            ADD (SEQ[$left $right] sums_to $total)
        END
        """
    )
    facts = (
        *(_fact(f"(left value {value})") for value in range(1, 81)),
        *(_fact(f"(right value {value})") for value in range(1, 81)),
        _fact("(total value 2)"),
    )
    indexed = IndexedInstantiationStrategy()
    strategy = AdaptiveInstantiationStrategy()

    expected = indexed.instantiate(rule, facts)
    actual = strategy.instantiate(rule, facts)

    assert actual == expected
    assert len(actual) == 1
    assert strategy.metrics.domain_filter_selections == 1
    assert strategy.metrics.domain_specialized_revisions > 0
    assert strategy.metrics.domain_combinations_tested == 0
    assert strategy.metrics.match_attempts == 3
    assert strategy.metrics.match_attempts < indexed.metrics.match_attempts


def test_arithmetic_constraint_supports_all_let_binary_operators() -> None:
    operators = {
        "+": 8,
        "-": 2,
        "*": 15,
        "/": 5 / 3,
        "%": 2,
    }
    for operator, expected in operators.items():
        (rule,) = parse_rules(
            f"""
            RULE arithmetic_{ord(operator)}
            WHEN
                (left value $left)
                (right value $right)
                (result value $result)
                CONSTRAINT $left {operator} $right == $result
            THEN
                ADD (arithmetic result ok)
            END
            """
        )
        facts = (
            _fact("(left value 5)"),
            _fact("(right value 3)"),
            _fact(f"(result value {expected})"),
        )

        naive = NaiveInstantiationStrategy().instantiate(rule, facts)
        constrained = ConstraintInstantiationStrategy().instantiate(
            rule,
            facts,
        )

        assert constrained == naive
        assert len(constrained) == 1


def test_generated_additive_constraints_match_naive_oracle() -> None:
    randomizer = random.Random(20260724)
    for case in range(20):
        operator = randomizer.choice(("+", "-"))
        left_values = sorted(
            randomizer.sample(range(-8, 9), randomizer.randint(2, 7))
        )
        right_values = sorted(
            randomizer.sample(range(-8, 9), randomizer.randint(2, 7))
        )
        target_values = sorted(
            randomizer.sample(range(-12, 13), randomizer.randint(1, 6))
        )
        (rule,) = parse_rules(
            f"""
            RULE generated_arithmetic_{case}
            WHEN
                (left value $left)
                (right value $right)
                (target value $target)
                CONSTRAINT $left {operator} $right == $target
            THEN
                ADD (SEQ[$left $right] reaches $target)
            END
            """
        )
        facts = (
            *(_fact(f"(left value {value})") for value in left_values),
            *(_fact(f"(right value {value})") for value in right_values),
            *(_fact(f"(target value {value})") for value in target_values),
        )
        expected = NaiveInstantiationStrategy().instantiate(rule, facts)

        assert (
            ConstraintInstantiationStrategy().instantiate(rule, facts)
            == expected
        )
        assert AdaptiveInstantiationStrategy().instantiate(rule, facts) == (
            expected
        )


def test_all_different_propagates_singletons_and_hall_pairs() -> None:
    (rule,) = parse_rules(
        """
        RULE hall_pair
        WHEN
            (first value $first)
            (second value $second)
            (third value $third)
            ALL_DIFFERENT SEQ[$first $second $third]
        THEN
            ADD (SEQ[$first $second $third] state solution)
        END
        """
    )
    facts = (
        _fact("(first value 1)"),
        _fact("(first value 2)"),
        _fact("(second value 1)"),
        _fact("(second value 2)"),
        _fact("(third value 1)"),
        _fact("(third value 2)"),
        _fact("(third value 3)"),
    )
    naive = NaiveInstantiationStrategy()
    strategy = ConstraintInstantiationStrategy()

    actual = strategy.instantiate(rule, facts)

    assert actual == naive.instantiate(rule, facts)
    assert strategy.metrics.domain_global_revisions > 0
    assert strategy.metrics.domain_candidates_removed >= 2
    assert {
        activation.substitution.apply(parse_term("$third"))
        for activation in actual
    } == {parse_term("3")}


def test_nvalue_filters_count_and_handles_tight_lower_bound() -> None:
    (rule,) = parse_rules(
        """
        RULE bounded_nvalue
        WHEN
            (first value $first)
            (second value $second)
            (third value $third)
            (cardinality value $count)
            NVALUE $count OF SEQ[$first $second $third]
        THEN
            ADD (SEQ[$first $second $third] distinct_count $count)
        END
        """
    )
    facts = (
        _fact("(first value red)"),
        _fact("(second value red)"),
        _fact("(second value blue)"),
        _fact("(third value red)"),
        _fact("(third value blue)"),
        _fact("(cardinality value 1)"),
    )
    naive = NaiveInstantiationStrategy()
    strategy = ConstraintInstantiationStrategy()

    actual = strategy.instantiate(rule, facts)

    assert actual == naive.instantiate(rule, facts)
    assert len(actual) == 1
    assert strategy.metrics.domain_global_value_checks > 0


def test_incremental_domains_restore_values_after_addition() -> None:
    (rule,) = parse_rules(
        """
        RULE incremental_all_different
        WHEN
            (left value $left)
            (right value $right)
            ALL_DIFFERENT SEQ[$left $right]
        THEN
            ADD (SEQ[$left $right] state solution)
        END
        """
    )
    initial = (
        _fact("(left value 1)"),
        _fact("(right value 1)"),
        _fact("(right value 2)"),
    )
    added = _fact("(left value 2)")
    strategy = ConstraintInstantiationStrategy()

    first = strategy.instantiate(rule, initial)
    expanded = strategy.instantiate(
        rule,
        (*initial, added),
        FactDelta(added=(added,), revision=1),
    )

    oracle = SemiNaiveInstantiationStrategy()
    assert first == oracle.instantiate(rule, initial)
    assert expanded == oracle.instantiate(
        rule,
        (*initial, added),
        FactDelta(added=(added,), revision=1),
    )
    assert len(expanded) == 1
    assert strategy.metrics.domain_component_resets == 1
    assert strategy.metrics.domain_table_rebuilds == 1


def test_incremental_domain_state_is_reused_for_irrelevant_delta() -> None:
    (rule,) = parse_rules(
        """
        RULE cached_all_different
        WHEN
            (left value $left)
            (right value $right)
            ALL_DIFFERENT SEQ[$left $right]
        THEN
            ADD (SEQ[$left $right] state solution)
        END
        """
    )
    facts = (
        _fact("(left value 1)"),
        _fact("(right value 2)"),
    )
    irrelevant = _fact("(unrelated state changed)")
    strategy = ConstraintInstantiationStrategy()

    expected = strategy.instantiate(rule, facts)
    projection_rows = strategy.metrics.domain_projection_rows_examined
    actual = strategy.instantiate(
        rule,
        (*facts, irrelevant),
        FactDelta(added=(irrelevant,), revision=1),
    )

    assert expected
    assert actual == ()
    assert strategy.metrics.domain_state_reuses == 1
    assert strategy.metrics.domain_projection_rows_examined == projection_rows


def test_generated_global_constraints_match_naive_oracle() -> None:
    nvalue_rule, all_different_rule = parse_rules(
        """
        RULE generated_nvalue
        WHEN
            (first value $first)
            (second value $second)
            (third value $third)
            (count value $count)
            NVALUE $count OF SEQ[$first $second $third]
        THEN
            ADD (SEQ[$first $second $third] cardinality $count)
        END

        RULE generated_all_different
        WHEN
            (first value $first)
            (second value $second)
            (third value $third)
            ALL_DIFFERENT SEQ[$first $second $third]
        THEN
            ADD (SEQ[$first $second $third] state distinct)
        END
        """
    )
    for seed in range(20):
        randomizer = random.Random(seed + 1000)
        facts = tuple(
            _fact(f"({variable} value {value})")
            for variable in ("first", "second", "third")
            for value in range(1, 5)
            if randomizer.random() < 0.65
        )
        if any(
            not any(
                fact.entity == parse_term(f"({variable} value {value})")
                for fact in facts
                for value in range(1, 5)
            )
            for variable in ("first", "second", "third")
        ):
            continue
        facts = (
            *facts,
            *(_fact(f"(count value {value})") for value in range(1, 4)),
        )
        for rule in (nvalue_rule, all_different_rule):
            expected = NaiveInstantiationStrategy().instantiate(rule, facts)
            assert (
                ConstraintInstantiationStrategy().instantiate(rule, facts)
                == expected
            )
            assert (
                AdaptiveInstantiationStrategy(
                    minimum_domain_rows=1,
                ).instantiate(rule, facts)
                == expected
            )


def test_empty_filtered_domain_rejects_rule_before_join() -> None:
    (rule,) = parse_rules(
        """
        RULE impossible_join
        WHEN
            ($x p $y)
            ($x q $z)
        THEN
            ADD ($x compatible $y)
        END
        """
    )
    facts = (
        _fact("(a p b)"),
        _fact("(c q d)"),
    )
    strategy = ConstraintInstantiationStrategy()

    assert strategy.instantiate(rule, facts) == ()
    assert strategy.metrics.domain_filter_runs == 1
    assert strategy.metrics.match_attempts == 0


def test_relation_variables_are_filtered_as_order_two_terms() -> None:
    (rule,) = parse_rules(
        """
        RULE select_relation
        WHEN
            ($subject $relation $object)
            ($relation kind transitive)
        THEN
            ADD ($subject selected $object)
        END
        """
    )
    facts = (
        _fact("(alice parent bob)"),
        _fact("(alice likes jazz)"),
        _fact("(parent kind transitive)"),
        _fact("(likes kind aesthetic)"),
    )
    naive = NaiveInstantiationStrategy()
    strategy = ConstraintInstantiationStrategy()

    assert strategy.instantiate(rule, facts) == naive.instantiate(rule, facts)
    assert strategy.metrics.domain_candidates_removed > 0


def test_bounded_comparison_domains_are_revised_before_matching() -> None:
    (rule,) = parse_rules(
        """
        RULE ordered_pair
        WHEN
            (source left $left)
            (source right $right)
            $left < $right
        THEN
            ADD ($left before $right)
        END
        """
    )
    facts = (
        _fact("(source left 1)"),
        _fact("(source left 3)"),
        _fact("(source left 5)"),
        _fact("(source right 0)"),
        _fact("(source right 2)"),
        _fact("(source right 4)"),
    )
    naive = NaiveInstantiationStrategy()
    strategy = ConstraintInstantiationStrategy()

    assert strategy.instantiate(rule, facts) == naive.instantiate(rule, facts)
    assert strategy.metrics.domain_revisions > 0


def test_domain_tables_follow_addition_and_removal_deltas() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    first = (
        _fact("(a p b)"),
        _fact("(a q c)"),
        _fact("(b r c)"),
    )
    added = (
        _fact("(d p e)"),
        _fact("(d q f)"),
        _fact("(e r f)"),
    )
    strategy = ConstraintInstantiationStrategy()

    initial = strategy.instantiate(rule, first)
    expanded_facts = (*first, *added)
    expanded = strategy.instantiate(
        rule,
        expanded_facts,
        FactDelta(added=added, revision=1),
    )
    removed = frozenset((first[1],))
    final_facts = tuple(fact for fact in expanded_facts if fact not in removed)
    reduced = strategy.instantiate(
        rule,
        final_facts,
        FactDelta(removed=removed, revision=2),
    )
    restored_facts = (*final_facts, first[1])
    restored = strategy.instantiate(
        rule,
        restored_facts,
        FactDelta(added=(first[1],), revision=3),
    )

    oracle = SemiNaiveInstantiationStrategy()
    assert initial == oracle.instantiate(rule, first)
    assert expanded == oracle.instantiate(
        rule,
        expanded_facts,
        FactDelta(added=added, revision=1),
    )
    assert reduced == oracle.instantiate(
        rule,
        final_facts,
        FactDelta(removed=removed, revision=2),
    )
    assert restored == oracle.instantiate(
        rule,
        restored_facts,
        FactDelta(added=(first[1],), revision=3),
    )
    assert strategy.metrics.domain_table_rebuilds == 1
    assert strategy.metrics.domain_table_updates == 3
    assert strategy.metrics.domain_bitset_updates == 5
    assert strategy.metrics.domain_rows_examined == 0


def test_compact_tables_replace_row_scans_and_preserve_join_results() -> None:
    (rule,) = parse_rules(
        """
        RULE compact_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    size = 20
    facts = (
        *(
            _fact(f"(x{x_index} p y{y_index})")
            for x_index in range(size)
            for y_index in range(size)
        ),
        *(_fact(f"(x{index} q z{index})") for index in range(size)),
        *(_fact(f"(y{index} r z{index})") for index in range(size)),
    )
    scanned = ConstraintInstantiationStrategy(
        use_compact_tables=False,
        use_compact_join=False,
    )
    compact = ConstraintInstantiationStrategy()

    expected = scanned.instantiate(rule, facts)
    actual = compact.instantiate(rule, facts)

    assert actual == expected
    assert compact.metrics.domain_rows_examined == 0
    assert scanned.metrics.domain_rows_examined > 0
    assert compact.metrics.domain_bitset_intersections > 0
    assert compact.metrics.domain_compact_join_rows > 0


def test_forward_engine_can_use_domain_filter_without_semantic_changes() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    facts = (
        _fact("(a p b)"),
        _fact("(a q c)"),
        _fact("(b r c)"),
    )

    expected = ForwardEngine((rule,)).run(facts)
    actual = ForwardEngine(
        (rule,),
        strategy=ConstraintInstantiationStrategy(),
    ).run(facts)

    assert actual.facts == expected.facts
    assert actual.derivations == expected.derivations
    assert actual.cycles == expected.cycles


def test_unsupported_negative_rule_falls_back_to_indexed_strategy() -> None:
    (rule,) = parse_rules(
        """
        RULE unblocked
        WHEN
            ($x candidate yes)
            NOT EXISTS
                ($x blocked yes)
            END_EXISTS
        THEN
            ADD ($x accepted yes)
        END
        """
    )
    facts = (
        _fact("(a candidate yes)"),
        _fact("(b candidate yes)"),
        _fact("(b blocked yes)"),
    )
    indexed = IndexedInstantiationStrategy()
    strategy = ConstraintInstantiationStrategy()

    assert strategy.instantiate(rule, facts) == indexed.instantiate(rule, facts)
    assert strategy.metrics.domain_filter_fallbacks == 1


def test_generated_positive_programs_match_naive_instantiation() -> None:
    rules = parse_rules(
        """
        RULE generated_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END

        RULE generated_distinct_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
            $y != $z
        THEN
            ADD ($x distinct_solution $y)
        END
        """
    )
    for seed in range(30):
        generator = random.Random(seed)
        facts = tuple(
            _fact(f"({left} {relation} {right})")
            for relation in ("p", "q", "r")
            for left in ("a", "b", "c", "d")
            for right in ("a", "b", "c", "d")
            if generator.random() < 0.35
        )
        for rule in rules:
            expected = NaiveInstantiationStrategy().instantiate(rule, facts)
            assert (
                ConstraintInstantiationStrategy().instantiate(rule, facts)
                == expected
            )
            assert (
                AdaptiveInstantiationStrategy().instantiate(rule, facts)
                == expected
            )
