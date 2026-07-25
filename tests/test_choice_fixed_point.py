from dataclasses import dataclass

from snarky import Atom, Fact, InferenceSession, Triple
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
