"""Optimization preserves the archived prototype's supports and search events."""

import importlib.machinery
import importlib.util
from pathlib import Path
from random import Random

import pytest

from snarky.finite.model import Query, QueryKind
from snarky.finite.search import search

from .sum_distinct import DistinctSumState, three_distinct_supports
from .test_sum_distinct import make_model


@pytest.fixture(scope="module")
def before():
    source = (
        Path(__file__).resolve().parents[2]
        / "benchmarks/results/magic_sum_distinct_2026-10-13/sum_distinct.py.txt"
    )
    loader = importlib.machinery.SourceFileLoader("_distinct_before_test", str(source))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_three_variable_supports_and_counters_match_5000_archived_cases(before):
    rng = Random(131035)
    for case in range(5000):
        fixed_count = rng.randrange(6)
        shift = rng.choice([0, 0, 10**40, -(10**40)])
        pool = range(-5, 13) if case % 3 == 0 else range(100, 120)
        fixed = rng.sample(pool, fixed_count)
        pairs = [((value + shift,), 1) for value in fixed]
        for _ in range(3):
            values = rng.sample(range(-5, 13), rng.randrange(2, 13))
            live = rng.sample(range(len(values)), rng.randrange(2, len(values) + 1))
            pairs.append((tuple(v + shift for v in values), sum(1 << i for i in live)))
        rng.shuffle(pairs)
        alphabets, masks = tuple(a for a, _ in pairs), tuple(m for _, m in pairs)
        active = [i for i, m in enumerate(masks) if m & (m - 1)]
        target = sum(
            rng.choice([v for j, v in enumerate(a) if m & (1 << j)]) for a, m in pairs
        ) + rng.randrange(-5, 6)
        expected = before.distinct_supports(alphabets, masks, target)
        observed = three_distinct_supports(alphabets, masks, target, active)
        assert observed == expected


@pytest.mark.parametrize("span", [4096, 4097, 10**40])
def test_bitset_span_boundary_and_huge_offset_fallback_match(before, span):
    base = 10**40
    alphabets = (
        (base, base + span),
        (base + 1, base + span - 1),
        (base + 2, base + span - 2),
    )
    masks = (3, 3, 3)
    target = 3 * base + span
    expected = before.distinct_supports(alphabets, masks, target)
    assert (
        three_distinct_supports(
            alphabets, masks, target, [0, 1, 2], (base, base + span)
        )
        == expected
    )


def audit_domains(state):
    events = []
    domains = state.domains
    names = tuple(v.name for v in state.model.variables)
    retain_mask, retain, rollback = (
        domains.retain_mask,
        domains.retain,
        domains.rollback,
    )

    def mask_event(variable, supported, cause):
        old = domains.mask(variable)
        result = retain_mask(variable, supported, cause)
        if old != domains.mask(variable):
            events.append(("retain_mask", variable, old, domains.mask(variable), cause))
        return result

    def retain_event(variable, supported, cause):
        old = domains.mask(variable)
        result = retain(variable, supported, cause)
        if old != domains.mask(variable):
            events.append(("retain", variable, old, domains.mask(variable), cause))
        return result

    def rollback_event(checkpoint):
        old = tuple(domains.mask(v) for v in names)
        rollback(checkpoint)
        events.append(("rollback", old, tuple(domains.mask(v) for v in names)))

    domains.retain_mask = mask_event
    domains.retain = retain_event
    domains.rollback = rollback_event
    return events


@pytest.mark.parametrize(
    "settings",
    [
        {},
        dict(max_active=2, pair_fast=True),
        dict(max_active=3, max_candidates=24, pair_fast=True),
        dict(max_active=4, max_candidates=128),
        dict(max_active=1, max_candidates=1, pair_fast=True),
        dict(max_candidates=1, pair_fast=True),
        dict(max_candidates=6),
        dict(pair_fast=True),
        dict(max_active=3),
    ],
)
@pytest.mark.parametrize("policy", ["mrv", "dom_wdeg"])
def test_full_reduction_and_rollback_traces_match_archived_prototype(
    before, settings, policy
):
    rng = Random(131036)
    for _ in range(48):
        count = rng.randrange(2, 7)
        domains = [rng.sample(range(-3, 5), rng.randrange(1, 5)) for _ in range(count)]
        scope = sorted(rng.sample(range(count), rng.randrange(2, count + 1)))
        target = sum(rng.choice(domains[i]) for i in scope) + rng.choice([-1, 0, 1])
        model = make_model(domains, target, scope)
        states = [
            cls(model, **settings)
            for cls in [before.DistinctSumState, DistinctSumState]
        ]
        traces = [audit_domains(s) for s in states]
        results = [
            search(s, Query(kind=QueryKind.ENUMERATE), policy=policy) for s in states
        ]
        assert traces[0] == traces[1]
        left, right = results
        assert (
            left.explored_nodes,
            left.failed_branches,
            left.constraint_revisions,
            left.termination,
        ) == (
            right.explored_nodes,
            right.failed_branches,
            right.constraint_revisions,
            right.termination,
        )
        assert [dict(s.assignment) for s in left.solutions] == [
            dict(s.assignment) for s in right.solutions
        ]
        assert {k: v for k, v in states[0].stats.items() if k != "seconds"} == {
            k: v for k, v in states[1].stats.items() if k != "seconds"
        }
