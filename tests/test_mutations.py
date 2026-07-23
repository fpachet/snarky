from snarky import (
    Fact,
    FactMutationKind,
    ForwardEngine,
    GroupExecutionMode,
    GroupStopReason,
    IndexedInstantiationStrategy,
    RemoveFact,
    parse_rule_groups,
    parse_rules,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_remove_action_mutates_memory_and_records_an_event() -> None:
    rules = parse_rules(
        """
        RULE consume
        WHEN
            request
        THEN
            REMOVE request
            ADD handled
        END
        """
    )
    engine = ForwardEngine(rules)
    session = engine.create_session((_fact("request"),))

    result = session.run_group(
        engine.default_group,
        mode=GroupExecutionMode.FIRST_CHANGE,
    )

    assert isinstance(rules[0].actions[0], RemoveFact)
    assert result.stop_reason is GroupStopReason.FIRST_CHANGE
    assert result.removed_facts == (_fact("request"),)
    assert result.added_facts == (_fact("handled"),)
    assert result.changed
    assert result.mutation_count == 2
    assert session.facts == (_fact("handled"),)
    assert [event.kind for event in result.events] == [
        FactMutationKind.REMOVE,
        FactMutationKind.ADD,
    ]


def test_actions_are_staged_before_an_activation_changes_memory() -> None:
    group = parse_rule_groups(
        """
        GROUP transaction
            RULE replace
            WHEN
                seed
            THEN
                ADD transient
                REMOVE transient
                ADD final
            END
        END_GROUP
        """
    )[0]
    session = ForwardEngine(()).create_session((_fact("seed"),))

    result = session.run_group(group)

    assert _fact("transient") not in session.facts
    assert _fact("final") in session.facts
    assert result.added_facts == (_fact("transient"), _fact("final"))
    assert result.removed_facts == (_fact("transient"),)


def test_removing_an_absent_fact_is_a_deterministic_non_change() -> None:
    rules = parse_rules(
        """
        RULE sterile_remove
        WHEN
            seed
        THEN
            REMOVE absent
        END
        """
    )

    result = ForwardEngine(rules).run((_fact("seed"),))

    assert result.facts == (_fact("seed"),)
    assert result.events == ()
    assert result.cycles == 1
    assert result.fired_activation_count == 1


def test_refraction_expires_when_an_activation_ceases_to_match() -> None:
    remover, restorer = parse_rule_groups(
        """
        GROUP remover
            RULE remove_target
            WHEN
                target
            THEN
                REMOVE target
            END
        END_GROUP

        GROUP restorer
            RULE restore_target
            WHEN
                restore_request
            THEN
                REMOVE restore_request
                ADD target
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(
        (_fact("target"), _fact("restore_request"))
    )

    first_removal = session.run_group(remover)
    restoration = session.run_group(restorer)
    second_removal = session.run_group(remover)

    assert first_removal.removed_facts == (_fact("target"),)
    assert restoration.added_facts == (_fact("target"),)
    assert second_removal.removed_facts == (_fact("target"),)
    assert _fact("target") not in session.facts


def test_indexed_strategy_updates_its_shared_index_after_removal() -> None:
    group = parse_rule_groups(
        """
        GROUP consume
            RULE consume_item
            WHEN
                ($item state pending)
            THEN
                REMOVE ($item state pending)
                ADD ($item state done)
            END
        END_GROUP
        """
    )[0]
    strategy = IndexedInstantiationStrategy()
    session = ForwardEngine(
        (),
        strategy=strategy,
    ).create_session(
        (
            _fact("(a state pending)"),
            _fact("(b state pending)"),
        )
    )

    result = session.run_group(group)

    assert set(session.facts) == {
        _fact("(a state done)"),
        _fact("(b state done)"),
    }
    assert result.mutation_count == 4
    assert strategy.metrics.index_builds == 1
    assert strategy.metrics.index_removals == 2
