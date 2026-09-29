"""First-party tiny fixtures: no network or external corpus needed in CI."""

from dataclasses import replace
from itertools import product

import pytest

from benchmarks.scheduling_instances import (
    JobShop,
    Project,
    build_model,
    parse_jobshop,
    parse_psplib,
    validate_jobshop,
    validate_project,
)
from benchmarks.scheduling_standard import checked, sha
from snarky import Number
from snarky.finite import Query, QueryKind, solve
from snarky.finite.oracle import feasible
from snarky.finite.predicates import integer

SM = """projects : 1
jobs (incl. supersource/sink ) : 4
horizon : 3
RESOURCES
- renewable : 1 R
- nonrenewable : 0 N
- doubly constrained : 0 D
PROJECT INFORMATION:
pronr. #jobs rel.date duedate tardcost MPM-Time
1 2 0 2 0 2
PRECEDENCE RELATIONS:
jobnr. #modes #successors successors
1 1 2 2 3
2 1 1 4
3 1 1 4
4 1 0
REQUESTS/DURATIONS:
jobnr. mode duration R 1
1 1 0 0
2 1 2 2
3 1 1 1
4 1 0 0
RESOURCEAVAILABILITIES:
R 1
2
"""
JSP = """preamble
instance tiny
++++++++++++++++++
synthetic 2x2
2 2
0 2 1 1
1 1 0 2
++++++++++++++++++
"""


def valid(check, instance, starts, objective):
    try:
        check(instance, starts, objective)
        return True
    except ValueError:
        return False


def test_importers():
    project = parse_psplib(SM, "tiny")
    assert project.durations == (0, 2, 1, 0)
    assert project.successors == ((1, 2), (3,), (3,), ())
    assert project.demands == ((0,), (2,), (1,), (0,))
    assert parse_jobshop(JSP, "tiny").jobs == (((0, 2), (1, 1)), ((1, 1), (0, 2)))


@pytest.mark.parametrize(
    "old,new",
    [
        ("projects : 1", "projects : 2"),
        ("horizon : 3", "horizon : 2"),
        ("- nonrenewable : 0", "- nonrenewable : 1"),
        ("- doubly constrained : 0", "- doubly constrained : 1"),
        ("1 2 0 2 0 2", "1 2 1 2 0 2"),
        ("1 1 2 2 3", "1 2 2 2 3"),
        ("1 1 2 2 3", "1 1 2 2 2"),
        ("1 1 2 2 3", "1 1 2 2 9"),
        ("2 1 1 4", "2 1 1 1"),
        ("3 1 1 4", "3 1 0"),
        ("1 1 2 2 3", "1 1 1 2"),
        ("2 1 2 2", "2 1 0 2"),
        ("1 1 0 0", "1 1 1 0"),
        ("1 1 0 0", "1 1 0 1"),
        ("2 1 2 2", "2 1 2 3"),
        ("2 1 2 2", "2 1 -2 2"),
        ("2 1 2 2", "2 1 2"),
        ("RESOURCEAVAILABILITIES:", "MISSING:"),
        ("horizon : 3", "horizon : 3\nhorizon : 3"),
    ],
)
def test_bad_project(old, new):
    with pytest.raises(ValueError):
        parse_psplib(SM.replace(old, new))


@pytest.mark.parametrize(
    "old,new",
    [
        ("2 2\n", "3 2\n"),
        ("0 2 1 1", "0 2 0 1"),
        ("0 2 1 1", "0 0 1 1"),
        ("0 2 1 1", "0 -2 1 1"),
        ("0 2 1 1", "0 2 2 1"),
        ("0 2 1 1", "0 2 1"),
        ("instance tiny", "instance other"),
    ],
)
def test_bad_jobshop(old, new):
    with pytest.raises(ValueError):
        parse_jobshop(JSP.replace(old, new), "tiny")


def test_duplicate_jobshop():
    with pytest.raises(ValueError):
        parse_jobshop(JSP + JSP, "tiny")


@pytest.mark.parametrize("capacity", [2, 3])
@pytest.mark.parametrize("chain", [False, True])
def test_project_exhaustive(capacity, chain):
    p = replace(parse_psplib(SM), capacities=(capacity,))
    if chain:
        p = replace(p, successors=((1, 2), (2, 3), (3,), ()))
    model, names, m, metadata = build_model(p)
    expected = set()
    domains = {v.name: set(v.domain) for v in model.variables}
    for a, b in product(range(4), repeat=2):
        c = max(a + 2, b + 1)
        starts = (0, a, b, c)
        if c > 3:
            continue
        original = valid(validate_project, p, starts, c)
        assignment = dict(zip(names, map(Number, starts), strict=True))
        encoded = all(v in domains[k] for k, v in assignment.items()) and feasible(
            model, assignment, ()
        )
        assert encoded == original
        if original:
            expected.add(starts)
    result = solve(model, Query(QueryKind.ENUMERATE))
    got = set()
    for sol in result.solutions:
        starts = tuple(integer(sol.assignment[x]) for x in names)
        # Epigraph slack is allowed by the model, and cannot improve the minimum.
        actual = max(starts[1] + 2, starts[2] + 1)
        canonical = (*starts[:-1], actual)
        validate_project(p, canonical, actual)
        got.add(canonical)
    assert got == expected
    optimum = solve(model, Query(QueryKind.MINIMIZE), value_policy="objective")
    assert optimum.status == "optimal"
    assert optimum.incumbent.objective_value == min(x[-1] for x in expected)
    assert metadata["lower_bound"] <= optimum.incumbent.objective_value
    assert integer(optimum.incumbent.assignment[m]) == optimum.incumbent.objective_value


@pytest.mark.parametrize("durations", [(1, 1, 1, 1), (2, 1, 1, 2), (1, 2, 2, 1)])
@pytest.mark.parametrize("same_route", [True, False])
def test_jobshop_exhaustive(durations, same_route):
    a, b, c, d = durations
    p = JobShop(
        "tiny",
        (((0, a), (1, b)), ((0, c), (1, d)) if same_route else ((1, c), (0, d))),
        2,
    )
    model, names, m, metadata = build_model(p)
    h = sum(durations)
    domains = {v.name: set(v.domain) for v in model.variables}
    expected = set()
    for starts in product(range(h), repeat=4):
        obj = max(s + d for s, d in zip(starts, durations, strict=True))
        if obj > h:
            continue
        original = valid(validate_jobshop, p, starts, obj)
        assignment = dict(zip(names, map(Number, starts), strict=True))
        assignment[m] = Number(obj)
        encoded = all(v in domains[k] for k, v in assignment.items()) and feasible(
            model, assignment, ()
        )
        assert encoded == original
        if original:
            expected.add(starts)
    result = solve(model, Query(QueryKind.ENUMERATE))
    got = {tuple(integer(sol.assignment[x]) for x in names) for sol in result.solutions}
    assert got == expected
    optimum = solve(model, Query(QueryKind.MINIMIZE), value_policy="objective")
    expected_opt = min(
        max(s + d for s, d in zip(st, durations, strict=True)) for st in expected
    )
    assert optimum.status == "optimal"
    assert optimum.incumbent.objective_value == expected_opt
    assert metadata["lower_bound"] <= expected_opt


@pytest.mark.parametrize(
    "starts,obj",
    [
        ((0, 0, 0, 2), 2),  # resource conflict
        ((0, 0, 2, 2), 2),  # sink arc
        ((1, 1, 3, 4), 4),  # source
        ((0, -1, 2, 3), 3),
        ((0, False, 2, 3), 3),
        ((0, 0, 2, 3), 4),
        ((0, 0, 2, 4), 4),  # objective slack
        ((0, 0, 2), 3),
    ],
)
def test_project_validator_rejects(starts, obj):
    with pytest.raises(ValueError):
        validate_project(parse_psplib(SM), starts, obj)


def test_jobshop_validator_and_touching_endpoints():
    p = parse_jobshop(JSP, "tiny")
    assert validate_jobshop(p, (0, 2, 0, 2), 4)
    for starts, obj in [
        ((0, 1, 0, 2), 4),
        ((0, 2, 0, 1), 3),
        ((0, 2, 0, 2), 5),
        ((0, 2, 0), 4),
    ]:
        with pytest.raises(ValueError):
            validate_jobshop(p, starts, obj)


def test_cache_integrity(tmp_path):
    (tmp_path / "fixture").write_bytes(b"fixture")
    manifest = {"files": {"fixture": {"sha256": sha(b"fixture")}}}
    assert checked(tmp_path, "fixture", manifest) == b"fixture"
    (tmp_path / "fixture").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        checked(tmp_path, "fixture", manifest)


def test_multiple_resources_and_non_numeric_topological_order():
    # Original first-party fork/join with arc 3->2 (indices 2->1).
    p = Project(
        "multi",
        (0, 1, 1, 2, 0),
        ((2, 3), (4,), (1,), (4,), ()),
        ((0, 0), (2, 0), (0, 2), (1, 1), (0, 0)),
        (2, 2),
        4,
    )
    model, names, m, _ = build_model(p)
    expected = set()
    for a, b, c in product(range(4), repeat=3):
        obj = max(a + 1, b + 1, c + 2)
        starts = (0, a, b, c, obj)
        if obj <= 4 and valid(validate_project, p, starts, obj):
            expected.add(starts)
    result = solve(model, Query(QueryKind.ENUMERATE))
    got = set()
    for sol in result.solutions:
        st = tuple(integer(sol.assignment[x]) for x in names)
        obj = max(st[1] + 1, st[2] + 1, st[3] + 2)
        normalized = (*st[:-1], obj)
        validate_project(p, normalized, obj)
        got.add(normalized)
    assert got == expected
    result = solve(model, Query(QueryKind.MINIMIZE), value_policy="objective")
    assert result.status == "optimal"
    assert result.incumbent.objective_value == min(x[-1] for x in expected)
