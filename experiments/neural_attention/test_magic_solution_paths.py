"""Successful-path tracing follows checkpoint rollback, rather than visit history."""

import pytest

from benchmarks.alice_magic import validate
from experiments.neural_attention.magic_search_tuning import prepare
from experiments.neural_attention.magic_solution_paths import (
    PathState,
    describe,
    replay,
)
from snarky.finite.model import Query, QueryKind
from snarky.finite.search import search, solve


@pytest.mark.parametrize("symmetry", [False, True])
def test_every_enumerated_solution_has_its_own_restored_successful_path(symmetry):
    original, model = prepare(3, "middle", "row_major", symmetry)
    state = PathState(model, "middle")
    result = search(state, Query(QueryKind.ENUMERATE), policy="mrv")
    reference = solve(model, Query(QueryKind.ENUMERATE), policy="mrv")
    assert result.solutions == reference.solutions
    assert result.explored_nodes == reference.explored_nodes
    assert result.failed_branches == reference.failed_branches
    assert result.constraint_revisions == reference.constraint_revisions
    assert len(state.paths) == len(result.solutions) == (1 if symmetry else 8)
    assert not state.path and state.domains.snapshot() == original.domains
    for solution, path in zip(result.solutions, state.paths, strict=True):
        square = validate(3, solution.assignment, original)
        summary = describe(3, path)
        assert summary["decisions"] + summary["forced_cells"] == 9
        for decision in path["decisions"]:
            assert square[decision["cell"]] == decision["value"]
            assert decision["domain_size"] == decision["minimum_domain_size"]
            for forced in decision["forced"]:
                assert square[forced["cell"]] == forced["value"]


def test_replay_distinguishes_variable_order_from_solution_value_oracle():
    original, model = prepare(3, "middle", "row_major", True)
    state = PathState(model, "middle")
    search(state, Query(), policy="mrv")
    result = replay(original, model, "middle", state.paths[0], 2)
    assert result["variable_order_only"]["solved"]
    assert result["variable_and_solution_values"]["solved"]
    assert result["variable_and_solution_values"]["failures"] == 0
    assert (
        result["variable_and_solution_values"]["nodes"]
        <= len(state.paths[0]["decisions"]) + 1
    )
