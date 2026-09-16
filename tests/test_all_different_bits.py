"""Exact all-different supports, graph partitions and rollback oracles."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import FiniteModel, FiniteVariable, Query, QueryKind, kernels, solve
from snarky.finite.constraints import AllDifferentConstraint
from snarky.finite.propagation import NativeState


@pytest.mark.parametrize("limit", [0, 2048])
def test_exact_supports_with_holes_symbols_and_invalid_matching_hints(
    monkeypatch, limit
):
    monkeypatch.setattr(kernels, "_ALL_DIFFERENT_BIT_VALUES", limit)
    rng = Random(61812)
    alphabet = (*map(Number, (-(10**100), -1, 0, 17)), Atom("red"), Atom("blue"))
    for case in range(700):
        names = tuple(Atom(f"x{i}") for i in range(rng.randrange(1, 6)))
        domains = {v: set(rng.sample(alphabet, rng.randrange(0, 5))) for v in names}
        expected_rows = {
            row
            for row in product(*(domains[v] for v in names))
            if len(set(row)) == len(names)
        }
        expected = {v: {row[i] for row in expected_rows} for i, v in enumerate(names)}
        hint = {v: rng.choice((*alphabet, Atom("absent"))) for v in names}
        hint[Atom("not_in_scope")] = alphabet[0]
        constraint = AllDifferentConstraint(Atom("distinct"), names)
        actual = {v: set(d) for v, d in domains.items()}
        valid, matching = kernels._revise_all_different_with_matching(
            constraint, actual, hint
        )
        assert valid == bool(expected_rows)
        if valid:
            assert actual == expected
            assert set(matching) == set(names)
            assert len(set(matching.values())) == len(names)
            assert all(matching[v] in actual[v] for v in names)
        if case < 35:
            model = FiniteModel(
                "oracle",
                tuple(FiniteVariable(v, tuple(domains[v])) for v in names),
                (constraint,),
            )
            result = solve(model, Query(QueryKind.ENUMERATE))
            assert result.complete
            assert {
                tuple(s.assignment[v] for v in names) for s in result.solutions
            } == (expected_rows)


def test_bit_graph_partitions_match_independent_reachability():
    rng = Random(8381)
    for _ in range(250):
        size = rng.randrange(1, 25)
        graph = [{j for j in range(size) if rng.random() < 0.15} for _ in range(size)]
        allowed = {i for i in range(size) if rng.random() < 0.8}

        def reachable(start, graph=graph, allowed=allowed):
            reached = {start}
            pending = [start]
            while pending:
                node = pending.pop()
                fresh = (graph[node] & allowed) - reached
                reached.update(fresh)
                pending.extend(fresh)
            return reached

        masks = [sum(1 << v for v in row) for row in graph]
        reverse = [
            sum(1 << u for u, row in enumerate(graph) if v in row) for v in range(size)
        ]
        actual = kernels._bit_components(masks, reverse, sum(1 << v for v in allowed))
        paths = {v: reachable(v) for v in allowed}
        for v in range(size):
            expected = {u for u in allowed if u in paths.get(v, ()) and v in paths[u]}
            assert actual[v] == sum(1 << u for u in expected)


def test_deep_sparse_and_dense_bit_graphs_do_not_use_python_recursion():
    size = 1200
    universe = (1 << size) - 1
    chain = [1 << (i + 1) for i in range(size - 1)] + [0]
    reverse = [0] + [1 << i for i in range(size - 1)]
    assert kernels._bit_components(chain, reverse, universe) == [
        1 << i for i in range(size)
    ]
    dense = [universe] * size
    assert kernels._bit_components(dense, dense, universe) == dense


@pytest.mark.parametrize("limit", [0, 2048])
def test_cached_matching_survives_nested_failures_and_widening(monkeypatch, limit):
    monkeypatch.setattr(kernels, "_ALL_DIFFERENT_BIT_VALUES", limit)
    names = tuple(Atom(f"v{i}") for i in range(4))
    alphabet = tuple(map(Number, range(4)))
    model = FiniteModel(
        "rollback",
        tuple(FiniteVariable(v, alphabet) for v in names),
        (AllDifferentConstraint(Atom("distinct"), names),),
    )
    state = NativeState(model)
    assert state.propagate()
    original = state.domains.snapshot()
    root = state.checkpoint()
    for first in alphabet:
        state.restrict(names[0], first)
        assert state.propagate()
        branch = state.domains.snapshot()
        child = state.checkpoint()
        state.restrict(names[1], first)
        assert not state.propagate()
        state.rollback(child)
        state.release(child)
        assert state.domains.snapshot() == branch
        assert state.propagate()
        state.rollback(root)
        assert state.domains.snapshot() == original
        assert state.propagate()
    state.release(root)
    assert not state.domains.removals


def test_large_value_alphabet_uses_sparse_fallback(monkeypatch):
    def forbidden(*args):
        raise AssertionError("dense bit graph used beyond its value budget")

    monkeypatch.setattr(kernels, "_filter_all_different_bits", forbidden)
    x, y = Atom("x"), Atom("y")
    values = {Number(i) for i in range(kernels._ALL_DIFFERENT_BIT_VALUES + 1)}
    domains = {x: {Number(0)}, y: set(values)}
    assert kernels._revise_all_different(
        AllDifferentConstraint(Atom("d"), (x, y)), domains
    )
    assert domains[y] == values - {Number(0)}


def test_sparse_chain_uses_linear_graph_algorithm_and_exact_supports(monkeypatch):
    def forbidden(*args):
        raise AssertionError("quadratic bit partition used for a large sparse graph")

    monkeypatch.setattr(kernels, "_filter_all_different_bits", forbidden)
    size = 100
    names = tuple(Atom(f"x{i:04}") for i in range(size))
    values = tuple(map(Number, range(size)))
    domains = {
        v: {values[i], values[i + 1 if i < size - 1 else i - 1]}
        for i, v in enumerate(names)
    }
    constraint = AllDifferentConstraint(Atom("chain"), names)
    valid, _ = kernels._revise_all_different_with_matching(
        constraint, domains, dict(zip(names, values, strict=True))
    )
    assert valid
    assert domains == {
        v: {values[i]} if i < size - 2 else set(values[-2:])
        for i, v in enumerate(names)
    }
