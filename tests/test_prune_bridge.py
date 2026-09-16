"""The benchmark adapter must preserve original primitive semantics exactly."""

import json
from itertools import product

import pytest

from benchmarks.prune_bridge import Bridge, UnsupportedModel, validate_assignment
from benchmarks.prune_comparison import VENDOR, digest, load_cases, parse, verify
from snarky.finite import Query, QueryKind, solve


def document(constraints, domains=None, solve_spec=None):
    return {
        "variables": {
            name: {"type": "int", "domain": [[min(d), max(d)]]}
            for name, d in (domains or {"x": range(3), "y": range(3)}).items()
        },
        "arrays": {},
        "constraints": [{"id": name, "args": args} for name, args in constraints],
        "output": [],
        "solve": solve_spec or {"method": "satisfy"},
        "version": "1.0",
    }


def compare(doc):
    names = list(doc["variables"])
    domains = [
        range(v["domain"][0][0], v["domain"][0][1] + 1)
        if v["type"] == "int"
        else range(2)
        for v in doc["variables"].values()
    ]
    expected = set()
    for row in product(*domains):
        assignment = dict(zip(names, row, strict=True))
        try:
            validate_assignment(doc, assignment)
        except AssertionError:
            continue
        expected.add(row)
    bridge = Bridge(doc)
    actual = solve(bridge.model, Query(QueryKind.ENUMERATE))
    assert actual.complete
    projected = [
        tuple(bridge.raw_assignment(s)[name] for name in names)
        for s in actual.solutions
    ]
    assert len(projected) == len(set(projected)), "lowering adds spurious multiplicity"
    assert set(projected) == expected
    return bridge, expected


@pytest.mark.parametrize("kind", ["int_lin_eq", "int_lin_le", "int_lin_ne"])
@pytest.mark.parametrize(
    "coefficients,variables,rhs",
    [
        ([2, -1], ["x", "y"], 1),
        ([1, -1], ["x", "y"], 0),
        ([1, -1], ["x", "x"], 0),
        ([1, -1], ["x", "x"], 1),
        ([0, 1, -2], ["x", "y", 1], 0),
        ([1, 1], ["x", 2], "y"),
    ],
)
def test_linear_aliases_constants_and_disequality(kind, coefficients, variables, rhs):
    compare(document([(kind, [coefficients, variables, rhs])]))


@pytest.mark.parametrize("values", [["x", "y"], ["x", "x"], ["x", 0], ["x", 0, 0], []])
def test_all_different_with_constants_and_repeated_variables(values):
    compare(document([("fzn_all_different_int", [values])]))


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, "n"])
@pytest.mark.parametrize("values", [["x", "y", "z"], ["x", "y", "x"], ["x", 0, "y"]])
def test_nvalue_encoding_exactly_matches_distinct_count(count, values):
    compare(
        document(
            [("fzn_nvalue", [count, values])],
            {"x": range(3), "y": range(3), "z": range(2), "n": range(4)},
        )
    )


def test_booleans_clause_and_integer_channel():
    doc = document(
        [("bool_clause", [["p"], ["q"]]), ("bool2int", ["p", "x"])], {"x": range(2)}
    )
    doc["variables"].update(p={"type": "bool"}, q={"type": "bool"})
    compare(doc)


def test_unknown_predicates_and_billion_value_domains_fail_before_materialization():
    with pytest.raises(UnsupportedModel, match="predicate"):
        Bridge(document([("silently_ignored_constraint", [])]))
    doc = document([])
    doc["variables"]["x"]["domain"] = [[0, 1_000_000_000]]
    with pytest.raises(UnsupportedModel, match="explicit domain limit"):
        Bridge(doc)
    with pytest.raises(UnsupportedModel, match="tuple budget"):
        Bridge(document([("int_lin_ne", [[2, 3], ["x", "y"], 1])]), max_table=2)


def test_constants_only_and_objective():
    bridge, _ = compare(document([("int_lin_eq", [[1], [1], 2])]))
    assert solve(bridge.model).status.value == "infeasible"
    bridge, _ = compare(
        document([], solve_spec={"method": "maximize", "objective": "x"})
    )
    best = solve(bridge.model, Query(QueryKind.MAXIMIZE))
    assert best.complete and best.incumbent.objective_value == 2


def test_catalog_counts_and_solution_streams():
    cases = load_cases()
    assert len(cases) == 54 and len({c["id"] for c in cases}) == 54
    assert parse('{"a":1}\n----------\n==========\n')["status"] == "complete"
    assert parse("=====UNSATISFIABLE=====\n")["status"] == "unsat"


def test_vendored_inputs_match_upstream_hashes():
    provenance = json.loads((VENDOR / "PROVENANCE.json").read_text())
    for path, expected in provenance["files"].items():
        assert digest(VENDOR / path) == expected, path


def test_validation_rejects_false_proofs_missing_solutions_and_incomplete_optima():
    solved = parse('{"objective":17}\n----------\n==========\n')
    infeasible = parse("=====UNSATISFIABLE=====\n")
    case = {"objective": {"field": "objective", "direction": "minimize", "optimum": 17}}
    verify(solved, solved, case, "first")
    for result in (infeasible, parse(""), parse('{"objective":17}\n----------\n')):
        with pytest.raises(AssertionError):
            verify(result, solved, case, "first")
    with pytest.raises(AssertionError):
        verify(
            parse('{"objective":18}\n----------\n==========\n'), solved, case, "first"
        )
    with pytest.raises(AssertionError):
        verify(parse('{"x":1}\n----------\n==========\n'), solved, {}, "all")
