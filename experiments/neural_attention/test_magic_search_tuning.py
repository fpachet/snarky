"""Ordering adapters preserve native solution sets and checkpoint restoration."""

import pytest

from benchmarks.alice_magic import validate
from experiments.neural_attention.magic_search_tuning import RankedState, prepare
from snarky.finite.model import Query, QueryKind
from snarky.finite.search import search, solve


@pytest.mark.parametrize(
    "order", ["middle", "middle_high", "line_average", "line_midpoints"]
)
@pytest.mark.parametrize("tie", ["row_major", "degree", "reverse"])
def test_tuning_preserves_all_small_solutions_and_restores_native_domains(order, tie):
    original, model = prepare(3, order, tie, symmetry=False)
    state = RankedState(model, order)
    result = search(state, Query(QueryKind.ENUMERATE), policy="mrv")
    expected = solve(original, Query(QueryKind.ENUMERATE), policy="mrv")
    assert result.complete and expected.complete
    assert {tuple(validate(3, s.assignment, original)) for s in result.solutions} == {
        tuple(validate(3, s.assignment, original)) for s in expected.solutions
    }
    assert state.native.domains.snapshot() == original.domains
    assert not state.native.domains.removals


@pytest.mark.parametrize(
    "order", ["middle", "middle_high", "line_average", "line_midpoints"]
)
def test_tuning_preserves_small_symmetry_representative(order):
    original, model = prepare(3, order, "degree", symmetry=True)
    result = search(RankedState(model, order), Query(QueryKind.ENUMERATE), policy="mrv")
    assert result.complete and len(result.solutions) == 1
    validate(3, result.solutions[0].assignment, original)


@pytest.mark.parametrize("order", ["line_average", "line_midpoints"])
def test_ranking_changes_order_only_at_propagated_partial_states(order):
    _, model = prepare(4, order, "row_major", symmetry=False)
    state = RankedState(model, order)
    root = state.checkpoint()
    assert state.propagate()
    for step in range(5):
        snapshot = state.native.domains.snapshot()
        unresolved = [v for v in model.variables if state.domains.size(v.name) > 1]
        if not unresolved:
            break
        variable = unresolved[step % len(unresolved)].name
        values = state.domains.values(variable)
        assert set(values) == snapshot[variable]
        assert state.native.domains.snapshot() == snapshot
        state.restrict(variable, values[0])
        if not state.propagate():
            break
    state.rollback(root)
    state.release(root)
    assert state.domains.snapshot() == model.domains
