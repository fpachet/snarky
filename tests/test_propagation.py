import pytest

from snarky import (
    Atom,
    ConstraintInstantiationStrategy,
    DomainStore,
    Fact,
    Number,
    PropagationReason,
    PropagationState,
    Variable,
    parse_rules,
    parse_term,
)


def test_domain_store_records_reductions_and_rolls_back() -> None:
    variable = Variable("pitch")
    low = Atom("c4")
    middle = Atom("e4")
    high = Atom("g4")
    store = DomainStore({variable: {low, middle, high}})
    checkpoint = store.checkpoint()

    removed = store.retain(
        variable,
        {low, middle},
        PropagationReason("rule", "range"),
    )

    assert removed == frozenset((high,))
    assert store.result().reductions[0].reason.source == "range"
    store.rollback(checkpoint)
    assert store.result().domains[variable] == frozenset(
        (low, middle, high)
    )
    assert store.result().reductions == ()


def test_domain_contradiction_is_reversible() -> None:
    variable = Variable("voice")
    value = Atom("soprano")
    store = DomainStore({variable: {value}})
    checkpoint = store.checkpoint()

    store.remove(
        variable,
        value,
        PropagationReason("constraint", "four voices required"),
    )

    result = store.result()
    assert not result.consistent
    assert result.contradiction is not None
    assert result.contradiction.variable == variable
    store.rollback(checkpoint)
    assert store.result().consistent
    assert store[variable] == {value}


def test_domain_store_can_disable_unused_trail_recording() -> None:
    variable = Variable("value")
    store = DomainStore(
        {variable: {Number(1), Number(2)}},
        record_trail=False,
    )

    store.restrict(
        variable,
        Number(1),
        PropagationReason("filter"),
    )

    assert store[variable] == {Number(1)}
    assert store.result().reductions
    with pytest.raises(RuntimeError, match="trail recording is disabled"):
        store.checkpoint()


def test_propagation_state_restores_domains_and_active_masks() -> None:
    variable = Variable("queen")
    one = Number(1)
    two = Number(2)
    state = PropagationState(
        DomainStore({variable: {one, two}}),
        {0: 0b1111},
    )
    outer = state.checkpoint()
    state.domains.restrict(
        variable,
        one,
        PropagationReason("choice", "try row one"),
    )
    state.set_active_mask(0, 0b0101)
    inner = state.checkpoint()
    state.set_active_mask(1, 0b0011)

    state.rollback(inner)
    assert state.active_masks == {0: 0b0101}
    state.rollback(outer)
    assert state.active_masks == {0: 0b1111}
    assert state.domains[variable] == {one, two}


def test_constraint_strategy_exposes_structured_propagation_result() -> None:
    (rule,) = parse_rules(
        """
        RULE ordered
        WHEN
            (left value $left)
            (right value $right)
            $left < $right
        THEN
            ADD ($left before $right)
        END
        """
    )
    facts = tuple(
        Fact(parse_term(text))
        for text in (
            "(left value 1)",
            "(left value 3)",
            "(right value 2)",
        )
    )
    strategy = ConstraintInstantiationStrategy()

    strategy.instantiate(rule, facts)
    result = strategy.last_propagation_results[rule]

    assert result.consistent
    assert result.reductions
    assert {
        reduction.reason.kind for reduction in result.reductions
    } <= {"comparison", "table"}
