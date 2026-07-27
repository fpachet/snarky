import random

from hypothesis import given, settings
from hypothesis import strategies as st

from snarky import (
    Atom,
    Fact,
    FactMutationKind,
    ForwardEngine,
    GroupExecutionMode,
    GroupStopReason,
    IndexedInstantiationStrategy,
    InferenceSession,
    NaiveInstantiationStrategy,
    RemoveFact,
    SemiNaiveInstantiationStrategy,
    SessionCheckpoint,
    Triple,
    parse_rule_groups,
    parse_rules,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_event_cursor_reports_deltas_and_expires_on_rollback() -> None:
    session = InferenceSession(())
    cursor = session.event_cursor()
    first = _fact("(item state first)")
    session.assume(first)

    events = session.events_after(cursor)

    assert events is not None
    assert tuple(event.fact for event in events) == (first,)
    checkpoint = session.checkpoint()
    branch_cursor = session.event_cursor()
    session.assume(_fact("(item state second)"))
    session.rollback(checkpoint)

    assert session.events_after(branch_cursor) is None
    session.release(checkpoint)


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


def test_unmaterialized_group_run_preserves_delta_without_fact_snapshot() -> None:
    (rule,) = parse_rules(
        """
        RULE derive
        WHEN
            seed
        THEN
            ADD derived
        END
        """
    )
    engine = ForwardEngine((rule,))
    session = engine.create_session(())
    session.assume(_fact("seed"))
    cursor = session.event_cursor()

    result = session.run_group(
        engine.default_group,
        materialize_result=False,
    )

    assert result is None
    assert session._store._snapshot_revision != session._store._revision
    events = session.events_after(cursor)
    assert events is not None
    assert tuple(event.fact for event in events) == (_fact("derived"),)
    assert session.facts == (_fact("seed"), _fact("derived"))
    assert session._store._snapshot_revision == session._store._revision


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


def _observable_state(session: InferenceSession) -> tuple[object, ...]:
    snapshot = session.snapshot()
    return (
        snapshot.facts,
        snapshot.derived_facts,
        snapshot.derivations,
        snapshot.cycles,
        snapshot.fired_activation_count,
        snapshot.events,
    )


def test_generated_mutation_sequences_match_naive_oracle() -> None:
    (derive,) = parse_rule_groups(
        """
        GROUP derive
            RULE copy_source
            WHEN
                ($item source $value)
            THEN
                ADD ($item derived $value)
            END

            RULE expose_unblocked
            WHEN
                ($item derived $value)
                NOT EXISTS ($item blocked $value)
            THEN
                ADD ($item available $value)
            END
        END_GROUP
        """
    )
    strategies = (
        NaiveInstantiationStrategy(),
        IndexedInstantiationStrategy(),
        SemiNaiveInstantiationStrategy(),
    )
    sessions = tuple(
        ForwardEngine((), strategy=strategy).create_session(())
        for strategy in strategies
    )
    generator = random.Random(20260725)
    items = tuple(Atom(f"item_{index}") for index in range(4))
    values = tuple(Atom(f"value_{index}") for index in range(3))
    checkpoints: tuple[SessionCheckpoint, ...] | None = None

    for step in range(24):
        item = generator.choice(items)
        value = generator.choice(values)
        relation = generator.choice((Atom("source"), Atom("blocked")))
        fact = Fact(Triple(item, relation, value))
        mutation = generator.choice(("assume", "retract"))
        for session in sessions:
            if mutation == "assume":
                session.assume(fact)
            else:
                session.retract(fact)
            session.run_group(derive)

        if step == 7:
            checkpoints = tuple(session.checkpoint() for session in sessions)
        elif step == 15:
            assert checkpoints is not None
            for session, checkpoint in zip(
                sessions,
                checkpoints,
                strict=True,
            ):
                session.rollback(checkpoint)
                session.release(checkpoint)

        expected = _observable_state(sessions[0])
        assert all(
            _observable_state(session) == expected
            for session in sessions[1:]
        )


@settings(max_examples=40, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from(
                (
                    "assume_source",
                    "retract_source",
                    "assume_blocked",
                    "retract_blocked",
                    "branch_source",
                    "branch_blocked",
                )
            ),
            st.integers(min_value=0, max_value=3),
            st.integers(min_value=0, max_value=2),
        ),
        min_size=1,
        max_size=20,
    )
)
def test_property_mutation_sequences_match_naive_oracle(
    operations: list[tuple[str, int, int]],
) -> None:
    (derive,) = parse_rule_groups(
        """
        GROUP derive
            RULE copy_source
            WHEN
                ($item source $value)
            THEN
                ADD ($item derived $value)
            END

            RULE expose_unblocked
            WHEN
                ($item derived $value)
                NOT EXISTS ($item blocked $value)
            THEN
                ADD ($item available $value)
            END
        END_GROUP
        """
    )
    sessions = tuple(
        ForwardEngine((), strategy=strategy).create_session(())
        for strategy in (
            NaiveInstantiationStrategy(),
            IndexedInstantiationStrategy(),
            SemiNaiveInstantiationStrategy(),
        )
    )

    for action, item_index, value_index in operations:
        relation = (
            Atom("source")
            if action.endswith("source")
            else Atom("blocked")
        )
        fact = Fact(
            Triple(
                Atom(f"item_{item_index}"),
                relation,
                Atom(f"value_{value_index}"),
            )
        )
        if action.startswith("branch"):
            checkpoints = tuple(
                session.checkpoint() for session in sessions
            )
            for session in sessions:
                session.assume(fact)
                session.run_group(derive)
            for session, checkpoint in zip(
                sessions,
                checkpoints,
                strict=True,
            ):
                session.rollback(checkpoint)
                session.release(checkpoint)
        else:
            for session in sessions:
                if action.startswith("assume"):
                    session.assume(fact)
                else:
                    session.retract(fact)
                session.run_group(derive)

        expected = _observable_state(sessions[0])
        assert all(
            _observable_state(session) == expected
            for session in sessions[1:]
        )


@settings(max_examples=30, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from(("assume", "retract", "branch")),
            st.integers(min_value=0, max_value=3),
            st.integers(min_value=0, max_value=2),
        ),
        min_size=1,
        max_size=20,
    )
)
def test_property_truth_maintenance_sequences_match_naive_oracle(
    operations: list[tuple[str, int, int]],
) -> None:
    (derive,) = parse_rule_groups(
        """
        GROUP derive
            RULE source_to_middle
            WHEN
                ($item source $value)
            THEN
                ADD ($item middle $value)
            END

            RULE middle_to_final
            WHEN
                ($item middle $value)
            THEN
                ADD ($item final $value)
            END
        END_GROUP
        """
    )
    sessions = tuple(
        ForwardEngine(
            (),
            strategy=strategy,
            truth_maintenance=True,
        ).create_session(())
        for strategy in (
            NaiveInstantiationStrategy(),
            IndexedInstantiationStrategy(),
            SemiNaiveInstantiationStrategy(),
        )
    )

    for action, item_index, value_index in operations:
        fact = Fact(
            Triple(
                Atom(f"item_{item_index}"),
                Atom("source"),
                Atom(f"value_{value_index}"),
            )
        )
        if action == "branch":
            checkpoints = tuple(
                session.checkpoint() for session in sessions
            )
            for session in sessions:
                session.assume(fact)
                session.run_group(derive)
            for session, checkpoint in zip(
                sessions,
                checkpoints,
                strict=True,
            ):
                session.rollback(checkpoint)
                session.release(checkpoint)
        else:
            for session in sessions:
                if action == "assume":
                    session.assume(fact)
                else:
                    session.retract(fact)
                session.run_group(derive)

        expected = _observable_state(sessions[0])
        assert all(
            _observable_state(session) == expected
            for session in sessions[1:]
        )
