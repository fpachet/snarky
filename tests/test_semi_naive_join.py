from snarky import Fact, parse_rules, parse_term
from snarky.instantiation.base import InstantiationMetrics
from snarky.instantiation.fact_index import FactIndex
from snarky.instantiation.semi_naive_join import (
    has_query_premise,
    join_delta_variants,
)
from snarky.matching import PatternMatcher


def test_delta_join_emits_only_chains_containing_the_new_fact() -> None:
    rule = parse_rules(
        """
        RULE transitive_step
        WHEN
            ($left edge $middle)
            ($middle edge $right)
        THEN
            ADD ($left reaches $right)
        END
        """
    )[0]
    old = Fact(parse_term("(a edge b)"))
    new = Fact(parse_term("(b edge c)"))
    disconnected = Fact(parse_term("(x edge y)"))
    metrics = InstantiationMetrics()

    activations = join_delta_variants(
        rule,
        FactIndex((old, new, disconnected)),
        (new,),
        PatternMatcher(),
        metrics,
    )

    assert len(activations) == 1
    assert activations[0].premise_facts == (old, new)
    assert activations[0].substitution.apply(parse_term("$left")) == (
        parse_term("a")
    )
    assert activations[0].substitution.apply(parse_term("$right")) == (
        parse_term("c")
    )


def test_query_premises_require_a_complete_join_after_additions() -> None:
    (positive,) = parse_rules(
        """
        RULE positive
        WHEN
            (item value $value)
        THEN
            ADD selected
        END
        """
    )
    (existential,) = parse_rules(
        """
        RULE existential
        WHEN
            EXISTS
                (item value $value)
            END_EXISTS
        THEN
            ADD selected
        END
        """
    )

    assert not has_query_premise(positive)
    assert has_query_premise(existential)
