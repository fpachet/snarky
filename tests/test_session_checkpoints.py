from snarky import Fact, ForwardEngine, InferenceSession, parse_rule_groups
from snarky.parser import parse_term


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


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
