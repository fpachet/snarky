from snarky import (
    Fact,
    ForwardEngine,
    InferenceSession,
    RunResult,
    SessionCheckpoint,
    parse_rule_groups,
)
from snarky.engine import (
    RunResult as EngineRunResult,
)
from snarky.engine import (
    SessionCheckpoint as EngineSessionCheckpoint,
)
from snarky.engine.forward import (
    RunResult as ForwardRunResult,
)
from snarky.engine.forward import (
    SessionCheckpoint as ForwardSessionCheckpoint,
)
from snarky.engine.session_state import RunResult as StateRunResult
from snarky.parser import parse_term


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_results_keep_provenance_across_mutation_and_repeated_rollback() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP derive
            RULE step
            WHEN
                seed
            THEN
                ADD conclusion
            END
        END_GROUP
        """
    )
    session = InferenceSession((_fact("seed"),))
    checkpoint = session.checkpoint()
    result = session.run_group(group)
    snapshot = session.snapshot()
    conclusion = _fact("conclusion")
    expected = snapshot.provenance.derivations(conclusion)
    assert expected
    for _ in range(2):
        session.assume(_fact("later"))
        session.rollback(checkpoint)
        for saved in (result, snapshot):
            assert conclusion in saved.facts
            assert saved.provenance.derivations(conclusion) == expected
            assert saved.provenance.depth(conclusion) == 1
            assert saved.provenance.derivations(_fact("later")) == ()
        session.run_group(group)
    session.release(checkpoint)


def test_assumptions_shorten_dependent_proofs_and_rollback_restores_depths() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP derive
            RULE first
            WHEN
                seed
            THEN
                ADD middle
            END
            RULE second
            WHEN
                middle
            THEN
                ADD end
            END
        END_GROUP
        """
    )
    session = InferenceSession((_fact("seed"),))
    session.run_group(group)
    middle, end = _fact("middle"), _fact("end")
    historical = session.provenance.derivations(end)
    checkpoint = session.checkpoint()
    for _ in range(2):
        session.assume(middle)
        assert session.provenance.depth(middle) == 0
        assert session.provenance.depth(end) == 1
        shortest = session.provenance.minimal_derivation(end)
        assert shortest is not None and shortest.proof_depth == 1
        assert session.provenance.derivations(end) == historical
        session.rollback(checkpoint)
        assert session.provenance.depth(middle) == 1
        assert session.provenance.depth(end) == 2
    session.release(checkpoint)


def test_a_shorter_rule_proof_updates_existing_descendants_reversibly() -> None:
    long_path, shortcut = parse_rule_groups(
        """
        GROUP long_path
            RULE first
            WHEN
                seed
            THEN
                ADD middle
            END
            RULE second
            WHEN
                middle
            THEN
                ADD end
            END
            RULE third
            WHEN
                end
            THEN
                ADD descendant
            END
        END_GROUP
        GROUP shortcut
            RULE short
            WHEN
                seed
            THEN
                ADD end
            END
        END_GROUP
        """
    )
    session = InferenceSession((_fact("seed"),))
    session.run_group(long_path)
    checkpoint = session.checkpoint()
    session.run_group(shortcut)
    assert session.provenance.depth(_fact("end")) == 1
    assert session.provenance.depth(_fact("descendant")) == 2
    session.rollback(checkpoint)
    assert session.provenance.depth(_fact("end")) == 2
    assert session.provenance.depth(_fact("descendant")) == 3
    session.release(checkpoint)


def test_checkpoint_type_keeps_its_public_import_paths() -> None:
    session = InferenceSession(())
    checkpoint = session.checkpoint()

    assert type(checkpoint) is SessionCheckpoint
    assert SessionCheckpoint is EngineSessionCheckpoint
    assert SessionCheckpoint is ForwardSessionCheckpoint
    session.release(checkpoint)


def test_run_result_keeps_its_public_import_paths() -> None:
    result = InferenceSession(()).snapshot()

    assert type(result) is RunResult
    assert RunResult is EngineRunResult
    assert RunResult is ForwardRunResult
    assert RunResult is StateRunResult


def test_checkpoint_restores_fact_order_provenance_and_fresh_names() -> None:
    (derive,) = parse_rule_groups(
        """
        GROUP derive
            RULE make_middle
            WHEN
                start
            THEN
                ADD middle
            END

            RULE make_fresh
            WHEN
                request
            THEN
                FRESH $node PREFIX node
                ADD (request generated $node)
            END
        END_GROUP
        """
    )
    initial = (
        _fact("start"),
        _fact("request"),
        _fact("(node-1 kind reserved)"),
    )
    session = ForwardEngine(()).create_session(initial)
    checkpoint = session.checkpoint()

    session.run_group(derive)
    generated = _fact("(request generated node-2)")
    assert generated in session.facts
    assert session.provenance.minimal_derivation(_fact("middle")) is not None
    session.retract(_fact("request"))
    session.assume(_fact("branch_only"))

    session.rollback(checkpoint)

    assert session.facts == initial
    assert session.events == ()
    assert session.provenance.minimal_derivation(_fact("middle")) is None
    session.run_group(derive)
    assert generated in session.facts
    session.rollback(checkpoint)
    assert session.facts == initial
    session.release(checkpoint)


def test_fact_snapshots_are_cached_and_invalidated_by_rollback() -> None:
    session = InferenceSession((_fact("a"), _fact("b")))
    initial = session.facts

    assert session.facts is initial
    checkpoint = session.checkpoint()
    session.assume(_fact("c"))
    branch = session.facts
    assert branch is session.facts
    assert branch is not initial

    session.rollback(checkpoint)

    restored = session.facts
    assert restored == initial
    assert restored is session.facts
    assert restored is not branch
    session.release(checkpoint)


def test_checkpoint_restores_negative_refraction_state() -> None:
    (negative,) = parse_rule_groups(
        """
        GROUP negative
            RULE absent_blocker
            WHEN
                trigger
                NOT EXISTS blocker
            THEN
                ADD conclusion
            END
        END_GROUP
        """
    )
    blocker = _fact("blocker")
    conclusion = _fact("conclusion")
    session = InferenceSession((_fact("trigger"),))
    session.run_group(negative)
    checkpoint = session.checkpoint()

    session.assume(blocker)
    session.retract(blocker)
    session.run_group(negative)
    assert session.snapshot().fired_activation_count == 2

    session.rollback(checkpoint)

    assert conclusion in session.facts
    assert session.snapshot().fired_activation_count == 1
    session.run_group(negative)
    assert session.snapshot().fired_activation_count == 1
    session.assume(blocker)
    session.retract(blocker)
    session.run_group(negative)
    assert session.snapshot().fired_activation_count == 2
    session.rollback(checkpoint)
    session.release(checkpoint)


def test_checkpoint_restores_truth_maintenance_cascade() -> None:
    (derive,) = parse_rule_groups(
        """
        GROUP derive
            RULE a_to_b
            WHEN
                a
            THEN
                ADD b
            END

            RULE b_to_c
            WHEN
                b
            THEN
                ADD c
            END
        END_GROUP
        """
    )
    session = ForwardEngine(
        (),
        truth_maintenance=True,
    ).create_session((_fact("a"),))
    session.run_group(derive)
    baseline = session.facts
    checkpoint = session.checkpoint()

    assert session.retract(_fact("a")) == (
        _fact("a"),
        _fact("b"),
        _fact("c"),
    )
    assert session.facts == ()

    session.rollback(checkpoint)

    assert session.facts == baseline
    assert session.provenance.minimal_derivation(_fact("c")) is not None
    session.release(checkpoint)
