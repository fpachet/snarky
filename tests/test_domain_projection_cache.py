"""Domain reads remain ordered and current across narrowing and restoration."""

from random import Random

from snarky import Atom, Number
from snarky.finite import FiniteVariable
from snarky.finite.domains import FiniteDomains


def test_repeated_reads_failed_branches_and_nested_siblings_preserve_domain_order():
    x, y = Atom("x"), Atom("y")
    declared = (Number(5), Atom("a"), Number(-1), Atom("b"), Number(0))
    state = FiniteDomains(tuple(FiniteVariable(v, declared) for v in (x, y)))
    rng = Random(276)
    outer = state.checkpoint()
    for _ in range(120):
        first = {value for value in declared if rng.randrange(2)}
        state.retain(x, first, Atom("first"))
        expected = tuple(value for value in declared if value in first)
        for _ in range(3):
            assert state.values(x) == expected
            assert state.values(y) == declared
        inner = state.checkpoint()
        for _ in range(4):
            second = {value for value in declared if rng.randrange(2)}
            state.retain(x, second, Atom("second"))
            state.retain(y, set(), Atom("failure"))
            assert state.values(x) == tuple(
                value for value in expected if value in second
            )
            assert state.values(y) == () and state.empty
            state.rollback(inner)
            assert state.values(x) == expected and state.values(y) == declared
        state.release(inner)
        state.rollback(outer)
        assert state.values(x) == declared and state.values(y) == declared
        assert not state.removals
    state.release(outer)
