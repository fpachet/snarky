"""Compiled exact supports and bounded pair eligibility against independent oracles."""

import importlib.machinery
import importlib.util
from pathlib import Path
from random import Random

import pytest

from snarky import Atom, Number
from snarky.finite.numeric import NumericColumn

from .sum_distinct import (
    DistinctSumState,
    compiled_three_supports,
    exact_three_supports,
)
from .test_sum_distinct import make_model
from .test_sum_distinct_exact import oracle_supports
from .test_sum_distinct_optimization import (
    test_full_reduction_and_rollback_traces_match_archived_prototype as compare_traces,
)

PAIRS = dict(max_active=3, pair_fast=True, exact_three=True, max_pairs=64)


def test_compiled_masks_and_deductions_match_5000_exact_cases():
    rng = Random(131039)
    for case in range(5000):
        shift = rng.choice([0, 10**40, -(10**40)])
        pairs = [((rng.randrange(-4, 13) + shift,), 1) for _ in range(rng.randrange(6))]
        for _ in range(3):
            values = rng.sample(range(-4, 13), rng.randrange(2, 12))
            if case % 5 == 0:
                values = [v * 10**40 for v in values]
            live = rng.sample(range(len(values)), rng.randrange(2, len(values) + 1))
            pairs.append((tuple(v + shift for v in values), sum(1 << j for j in live)))
        rng.shuffle(pairs)
        alphabets = tuple(a for a, _ in pairs)
        masks = tuple(m for _, m in pairs)
        columns = tuple(
            NumericColumn(Atom(f"x{i}"), a) for i, a in enumerate(alphabets)
        )
        active = [i for i, m in enumerate(masks) if m & (m - 1)]
        target = sum(
            rng.choice([v for j, v in enumerate(a) if m & (1 << j)]) for a, m in pairs
        ) + rng.choice([-1, 0, 0, 1])
        observed = compiled_three_supports(columns, masks, target, active)
        expected = exact_three_supports(alphabets, masks, target, active)
        assert observed[0] == expected[0]
        assert {k: v for k, v in observed[1].items() if k != "pair_checks"} == {
            k: v for k, v in expected[1].items() if k != "pair_checks"
        }
        sizes = sorted(masks[i].bit_count() for i in active)
        assert observed[1]["pair_checks"] <= sizes[0] * sizes[1]
        assert observed[0] == oracle_supports(alphabets, masks, target)


@pytest.mark.parametrize("shift", [0, 10**40, -(10**40)])
def test_pair_budget_handles_wide_third_domain_and_removes_equal_pair_support(shift):
    domains = [range(1, 9), range(1, 9), range(1, 101)]
    model = make_model([[v + shift for v in d] for d in domains], 17 + 3 * shift)
    legacy = DistinctSumState(
        model, max_active=3, max_candidates=24, pair_fast=True, exact_three=True
    )
    expanded = DistinctSumState(model, **PAIRS)
    assert legacy.propagate() and expanded.propagate()
    third = model.variables[2].name
    assert Number(15 + shift) in legacy.domains.values(third)
    assert Number(15 + shift) not in expanded.domains.values(third)
    assert expanded.stats["exact_calls"] > 0
    assert legacy.stats["exact_calls"] == 0
    masks = tuple((1 << len(v.domain)) - 1 for v in model.variables)
    alphabets = tuple(tuple(x.value for x in v.domain) for v in model.variables)
    expected = oracle_supports(alphabets, masks, 17 + 3 * shift)
    assert expected is not None
    assert tuple(expanded.domains.mask(v.name) for v in model.variables) == expected


def test_pair_budget_skips_more_than_64_pairs():
    model = make_model([range(1, 9), range(1, 10), range(1, 10)], 15)
    state = DistinctSumState(model, **PAIRS)
    assert state.propagate()
    assert state.stats["exact_calls"] == 0
    assert state.stats["gated"] > 0


def test_fast_pair_keeps_precedence_over_pair_budget():
    model = make_model([range(1, 4)] * 2, 4)
    state = DistinctSumState(model, exact_three=True, pair_fast=True, max_pairs=1)
    assert state.propagate()
    assert state.stats["fast_pair_calls"] > 0
    assert state.stats["pair_removals"] == 2


@pytest.mark.parametrize("settings", [dict(max_pairs=-1), dict(max_pairs=64)])
def test_invalid_pair_budget_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        DistinctSumState(make_model([range(1, 5)] * 3, 6), **settings)


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_lookup_reuses_exact_masks_counters_and_full_search_traces(policy):
    source = (
        Path(__file__).resolve().parents[2]
        / "benchmarks/history/magic_sum_distinct_exact_2026-10-13/sum_distinct.py.txt"
    )
    loader = importlib.machinery.SourceFileLoader("_exact_before_lookup", str(source))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    before = importlib.util.module_from_spec(spec)
    loader.exec_module(before)
    compare_traces(
        before,
        dict(max_active=3, max_candidates=24, pair_fast=True, exact_three=True),
        policy,
        ignore_stats=("pair_checks",),
    )


@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_pair_budget_preserves_complete_solution_sets(monkeypatch, policy):
    from . import test_sum_distinct_exact as checks

    monkeypatch.setattr(checks, "SETTINGS", PAIRS)
    checks.test_full_search_preserves_all_solutions_with_overlapping_scopes(policy)


def test_pair_budget_rollback_and_all_magic_three_solutions(monkeypatch):
    from . import test_sum_distinct_exact as checks

    monkeypatch.setattr(checks, "SETTINGS", PAIRS)
    checks.test_sibling_rollback_restores_masks_and_recomputes_supports()
    checks.test_all_eight_three_by_three_magic_squares_are_preserved()
