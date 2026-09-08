from dataclasses import dataclass

import pytest

from snarky import (
    Atom,
    ChoiceSearchStatus,
    Fact,
    InferenceSession,
    SessionChoiceSearch,
    Triple,
)
from snarky.choice_fixed_point import JointFixedPointScheduler


@dataclass
class _CountingPropagator:
    watched_relations: frozenset[Atom]
    calls: int = 0

    def __call__(self, session: InferenceSession) -> None:
        self.calls += 1


@dataclass
class _OneShotFactPropagator:
    watched_relations: frozenset[Atom]
    fact: Fact
    calls: int = 0

    def __call__(self, session: InferenceSession) -> None:
        self.calls += 1
        session.assume(self.fact, label="test-propagator")


def test_scheduler_requeues_only_components_watching_changed_relations() -> None:
    alpha = Atom("alpha")
    beta = Atom("beta")
    observer = _CountingPropagator(frozenset((alpha,)))
    unrelated = _CountingPropagator(frozenset((beta,)))
    producer = _OneShotFactPropagator(
        frozenset((beta,)),
        Fact(Triple(Atom("subject"), alpha, Atom("object"))),
    )
    scheduler = JointFixedPointScheduler(
        (),
        (observer, unrelated, producer),
        maximum_rounds=10,
    )

    scheduler.run(InferenceSession(()))

    assert observer.calls == 2
    assert unrelated.calls == 1
    assert producer.calls == 1


def test_scheduler_ignores_add_then_retract_net_zero_delta() -> None:
    relation = Atom("relation")
    observed = _CountingPropagator(frozenset((relation,)))
    fact = Fact(Triple(Atom("subject"), relation, Atom("object")))

    class NetZeroPropagator:
        watched_relations = frozenset((Atom("trigger"),))

        def __call__(self, session: InferenceSession) -> None:
            session.assume(fact, label="temporary")
            session.retract(fact, label="temporary")

    scheduler = JointFixedPointScheduler(
        (),
        (observed, NetZeroPropagator()),
        maximum_rounds=10,
    )

    scheduler.run(InferenceSession(()))

    assert observed.calls == 1


def test_search_observes_a_custom_propagators_complete_fixed_point() -> None:
    initial = tuple(Fact(Atom(value)) for value in ("a", "b", "c"))

    def narrow(session: InferenceSession) -> None:
        if len(session.facts) > 1:
            session.retract(session.facts[-1])

    session = InferenceSession(initial)
    result = SessionChoiceSearch(
        groups=(),
        choices=lambda current: (),
        goal=lambda current: len(current.facts) == 1,
        propagators=(narrow,),
    ).solve(session)

    assert result.status is ChoiceSearchStatus.SOLVED
    assert result.solutions[0].session.facts == initial[:1]
    assert session.facts == initial


def test_interacting_propagators_reach_closure() -> None:
    a, b, c = (Fact(Atom(value)) for value in ("a", "b", "c"))

    def first(session: InferenceSession) -> None:
        if b not in session.facts:
            session.retract(a)

    def second(session: InferenceSession) -> None:
        session.retract(c if c in session.facts else b)

    session = InferenceSession((a, b, c))
    JointFixedPointScheduler((), (first, second), maximum_rounds=10).run(session)
    assert session.facts == ()


def test_non_converging_propagator_hits_iteration_guard() -> None:
    fact = Fact(Atom("toggle"))

    def toggle(session: InferenceSession) -> None:
        if fact in session.facts:
            session.retract(fact)
        else:
            session.assume(fact)

    with pytest.raises(RuntimeError, match="did not stabilize"):
        JointFixedPointScheduler((), (toggle,), maximum_rounds=3).run(
            InferenceSession(())
        )
