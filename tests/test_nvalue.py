"""Independent NValue predicate, sound-filtering and search oracles."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    NValueConstraint,
    Query,
    QueryKind,
    solve,
)
from snarky.finite.nvalue import _cover_possible, revise_nvalue
from snarky.finite.predicates import accepts
from snarky.finite.propagation import NativeState


def supports(constraint, domains):
    variables = constraint.variables
    result = {v: set() for v in variables}
    found = False
    for row in product(*(domains[v] for v in variables)):
        assignment = dict(zip(variables, row, strict=True))
        target = (
            constraint.count
            if isinstance(constraint.count, int)
            else assignment[constraint.count].value
        )
        valid = (
            len({assignment[v] for v in constraint.scope} | set(constraint.constants))
            == target
        )
        assert accepts(constraint, assignment) == valid
        if valid:
            found = True
            for v, value in assignment.items():
                result[v].add(value)
    return found, result


@pytest.mark.parametrize("budget", [0, 2000])
def test_filter_never_removes_exhaustive_supports_with_constants_and_count_alias(
    monkeypatch, budget
):
    import snarky.finite.nvalue as module

    monkeypatch.setattr(module, "_COVER_NODES", budget)
    rng = Random(12274)
    names = tuple(map(Atom, ("a", "b", "c", "d")))
    alphabet = tuple(map(Number, range(-1, 5)))
    for case in range(500):
        scope = names[: rng.randrange(5)]
        count = rng.choice([rng.randrange(-1, 6), Atom("k"), *scope])
        constants = tuple(rng.sample(alphabet, rng.randrange(3)))
        constraint = NValueConstraint(
            Atom("nvalue"), (*scope, *scope[:1]), count, constants
        )
        original = {
            v: set(rng.sample(alphabet, rng.randrange(1, 4)))
            for v in constraint.variables
        }
        valid, expected = supports(constraint, original)
        actual = {v: set(d) for v, d in original.items()}
        consistent = revise_nvalue(constraint, actual)
        if valid:
            assert consistent
            assert all(expected[v] <= actual[v] <= original[v] for v in original)
        if case < 100:
            model = FiniteModel(
                "nvalue",
                tuple(FiniteVariable(v, tuple(d)) for v, d in original.items()),
                (constraint,),
            )
            found = solve(model, Query(QueryKind.ENUMERATE))
            oracle = {
                row
                for row in product(*(original[v] for v in constraint.variables))
                if len(
                    {
                        dict(zip(constraint.variables, row, strict=True))[v]
                        for v in scope
                    }
                    | set(constants)
                )
                == (
                    count
                    if isinstance(count, int)
                    else dict(zip(constraint.variables, row, strict=True))[count].value
                )
            }
            assert found.complete
            assert {
                tuple(s.assignment[v] for v in constraint.variables)
                for s in found.solutions
            } == oracle


def test_empty_constants_repeated_references_and_symbolic_values():
    x, y, k = map(Atom, ("x", "y", "k"))
    for scope, count, constants in [
        ((), 0, ()),
        ((), 1, (Atom("red"),)),
        ((x, x, y), k, (Atom("red"), Atom("red"))),
        ((k, x), k, ()),
    ]:
        c = NValueConstraint(Atom("n"), scope, count, constants)
        d = {
            v: ({Number(1), Number(2)} if v == k else {Atom("red"), Atom("blue")})
            for v in c.variables
        }
        valid, expected = supports(c, d)
        assert revise_nvalue(c, d) == valid
        if valid:
            assert all(expected[v] <= d[v] for v in d)


def test_one_and_all_distinct_specializations_filter_exactly():
    a, b, c = map(Atom, "abc")
    for count in (1, 3, 4):
        for constants in ((), (Number(0),)):
            constraint = NValueConstraint(Atom("n"), (a, b, c), count, constants)
            domains = {
                a: {Number(0), Number(1)},
                b: {Number(0), Number(1)},
                c: {Number(0), Number(1), Number(2)},
            }
            valid, expected = supports(constraint, domains)
            assert revise_nvalue(constraint, domains) == valid
            if valid:
                assert domains == expected


def test_cover_budget_cannot_become_a_false_infeasibility_proof():
    domains = [{0, 1}, {1, 2}, {0, 2}]
    assert _cover_possible(domains, 1, 0) is None
    assert _cover_possible(domains, 1, 100) is False
    assert _cover_possible(domains, 2, 100) is True
    rng = Random(817)
    for _ in range(250):
        sets = [
            set(rng.sample(range(6), rng.randrange(1, 5)))
            for _ in range(rng.randrange(1, 7))
        ]
        for slots in range(1, 4):
            expected = any(len(set(row)) <= slots for row in product(*sets))
            for budget in (1, 2000):
                actual = _cover_possible(sets, slots, budget)
                assert actual is None or actual == expected


def test_nvalue_rollback_including_count_as_scoped_variable():
    x, y, k = map(Atom, ("x", "y", "k"))
    model = FiniteModel(
        "n",
        tuple(FiniteVariable(v, tuple(map(Number, (0, 1, 2, 3)))) for v in (x, y, k)),
        (NValueConstraint(Atom("n"), (x, y, k), k),),
    )
    state = NativeState(model)
    before = state.domains.snapshot()
    root = state.checkpoint()
    for value in (0, 1, 3, 2, 0):
        state.restrict(k, Number(value))
        state.propagate()
        state.rollback(root)
        assert state.domains.snapshot() == before and not state.domains.removals
    state.release(root)


def test_matching_bound_and_cover_limits_are_conservative():
    from snarky.finite.nvalue import _maximum_new_values

    rng = Random(118)
    for _ in range(200):
        domains = [
            set(rng.sample(range(6), rng.randrange(1, 5)))
            for _ in range(rng.randrange(1, 7))
        ]
        mandatory = set(rng.sample(range(6), rng.randrange(3)))
        mandatory.update(next(iter(d)) for d in domains if len(d) == 1)
        actual = len(mandatory) + _maximum_new_values(domains, mandatory)
        expected = max(len(set(row) | mandatory) for row in product(*domains))
        assert actual == expected
    assert _cover_possible([{i, i + 1} for i in range(300)], 2, 100) is None
    assert _cover_possible([{0, i} for i in range(1, 30)], 17, 100) is None


def test_literal_validation_and_integer_count_domains():
    from snarky import Variable

    with pytest.raises(ValueError, match="count"):
        NValueConstraint(Atom("n"), (), True)
    with pytest.raises(ValueError, match="ground"):
        NValueConstraint(Atom("n"), (), 0, (Variable("value"),))
    with pytest.raises(TypeError, match="integer"):
        revise_nvalue(
            NValueConstraint(Atom("n"), (), Atom("k")), {Atom("k"): {Atom("red")}}
        )
