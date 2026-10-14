"""Large-search instrumentation preserves witnesses and accounts for setup limits."""

import pytest

from .magic_large_search import settings, trial


@pytest.mark.parametrize("mode", ["native", "exact", "pairs"])
def test_small_normal_square_is_validated_in_each_mode(mode, capsys):
    spec = dict(policy="dom_wdeg", order="random", tie="random", symmetry=True, seed=1)
    row = trial(3, spec, mode, 2, progress_interval=0)
    assert row["solved"] and row["termination"] == "solution_limit"
    square = row["squares"][0]
    assert sorted(square) == list(range(1, 10))
    assert all(sum(square[i * 3 : (i + 1) * 3]) == 15 for i in range(3))
    assert all(sum(square[i::3]) == 15 for i in range(3))
    assert sum(square[::4]) == sum(square[2:8:2]) == 15
    assert row["observations"]["max_fixed_observed"] == 9
    assert 0 <= row["prepare_seconds"] <= row["total_seconds"]
    assert row["search_seconds"] >= 0
    assert '"event": "progress"' in capsys.readouterr().out


def test_setup_uses_the_attempt_budget():
    row = trial(3, settings([0, 1])[0], "exact", 1e-9)
    assert not row["solved"] and row["termination"] == "setup_budget"
    assert row["nodes"] == 0 and not row["squares"]


def test_schedule_prioritizes_existing_winners_without_duplicates():
    specs = settings([0, 1, 2])
    assert specs[0] == dict(
        policy="dom_wdeg", order="random", tie="random", symmetry=True, seed=1
    )
    assert specs[1] == dict(
        policy="dom_wdeg", order="random", tie="random", symmetry=False, seed=1
    )
    assert len({tuple(sorted(s.items())) for s in specs}) == len(specs)
