"""Maintained synthetic Markov probe and higher-order/boundary semantics."""

from itertools import product
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite import (
    MarkovCosts,
    Query,
    QueryKind,
    ResultStatus,
    markov_model,
    solve,
)
from snarky.finite.constraints import AllDifferentConstraint, TableConstraint


@pytest.mark.parametrize("seed", range(6))
def test_original_six_model_probe_has_exact_optimum_and_probability(seed):
    rng = Random(seed)
    alphabet = tuple(Number(i) for i in range(4))
    costs = {}
    for left in alphabet:
        row = [1, 2, 3, 3]  # probabilities 1/2, 1/4, 1/8, 1/8
        rng.shuffle(row)
        costs.update(
            {(left, right): cost for right, cost in zip(alphabet, row, strict=True)}
        )
    source = MarkovCosts(alphabet, 1, {(symbol,): 2 for symbol in alphabet}, costs)
    names = tuple(Atom(f"x{i}") for i in range(5))
    model = markov_model(
        source,
        5,
        names=names,
        constraints=(
            AllDifferentConstraint(Atom("distinct"), names[:4]),
            TableConstraint(
                Atom("repeat"), (names[0], names[-1]), tuple((v, v) for v in alphabet)
            ),
        ),
    )
    expected = {
        sequence: 2 + sum(costs[sequence[i : i + 2]] for i in range(4))
        for sequence in product(alphabet, repeat=5)
        if sequence[0] == sequence[-1] and len(set(sequence[:4])) == 4
    }
    assert len(expected) == 24
    actual = solve(model, Query(QueryKind.ENUMERATE))
    assert actual.complete
    assert {
        tuple(s.assignment[v] for v in names): s.objective_value
        for s in actual.solutions
    } == expected
    for order in (names, names[::-1], names[::2] + names[1::2]):
        for reverse in (False, True):
            optimum = solve(
                model,
                Query(QueryKind.MINIMIZE),
                variable_order=order,
                reverse_values=reverse,
            )
            assert optimum.status is ResultStatus.OPTIMAL
            assert (
                optimum.incumbent.objective_value
                == optimum.objective_bound
                == min(expected.values())
            )
            assert sum(c.value for c in optimum.incumbent.contributions) == min(
                expected.values()
            )


@pytest.mark.parametrize("order", [0, 1, 2, 3])
def test_sparse_higher_order_and_terminal_costs_match_direct_paths(order):
    alphabet = (Atom("a"), Atom("b"))
    rng = Random(order + 100)
    initial = {row: rng.randrange(-7, 5) for row in product(alphabet, repeat=order)}
    transitions = {
        row: rng.randrange(-9, 6)
        for row in product(alphabet, repeat=order + 1)
        if rng.random() < 0.7
    }
    terminal = {row: rng.randrange(-5, 8) for row in product(alphabet, repeat=order)}
    source = MarkovCosts(alphabet, order, initial, transitions, terminal)
    length = max(order, 4)
    model = markov_model(source, length)
    expected = {}
    for sequence in product(alphabet, repeat=length):
        windows = [sequence[i - order : i + 1] for i in range(order, length)]
        if any(window not in transitions for window in windows):
            assert source.sequence_cost(sequence) is None
            continue
        cost = initial[sequence[:order]] + sum(transitions[w] for w in windows)
        cost += terminal[sequence[-order:] if order else ()]
        assert source.sequence_cost(sequence) == cost
        expected[sequence] = cost
    result = solve(model, Query(QueryKind.ENUMERATE))
    names = tuple(var.name for var in model.variables)
    assert {
        tuple(s.assignment[v] for v in names): s.objective_value
        for s in result.solutions
    } == expected
    for kind, select in ((QueryKind.MINIMIZE, min), (QueryKind.MAXIMIZE, max)):
        best = solve(model, Query(kind), reverse_values=True)
        assert best.status is (
            ResultStatus.OPTIMAL if expected else ResultStatus.INFEASIBLE
        )
        if expected:
            assert best.incumbent.objective_value == select(expected.values())


def test_boundary_length_zero_missing_support_and_validation():
    a = Atom("a")
    source = MarkovCosts((a,), 0, {(): 2}, {}, {(): -1})
    assert source.sequence_cost(()) == 1
    result = solve(markov_model(source, 0), Query(QueryKind.MINIMIZE))
    assert (
        result.status is ResultStatus.OPTIMAL and result.incumbent.objective_value == 1
    )
    assert solve(markov_model(source, 1)).status is ResultStatus.INFEASIBLE
    initial_only = MarkovCosts((a,), 1, {(a,): 2}, {}, {(a,): 3})
    assert (
        solve(
            markov_model(initial_only, 1), Query(QueryKind.MINIMIZE)
        ).incumbent.objective_value
        == 5
    )
    assert solve(markov_model(initial_only, 2)).status is ResultStatus.INFEASIBLE
    with pytest.raises(ValueError, match="length"):
        markov_model(initial_only, 0)
    with pytest.raises(ValueError, match="order"):
        MarkovCosts((a,), -1, {}, {})
    with pytest.raises(TypeError, match="integers"):
        MarkovCosts((a,), 0, {(): 0}, {(a,): 0.5})
    with pytest.raises(ValueError, match="empty tuple"):
        MarkovCosts((a,), 0, {}, {})
