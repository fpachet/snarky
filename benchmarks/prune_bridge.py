"""Strict benchmark-only FlatZinc JSON bridge to Snarky's native finite runtime.

This is not a general FlatZinc frontend. Unsupported constructs and impractical
explicit domains fail before allocation. NValue uses the native constraint by
default; the historical Boolean/table decomposition is available explicitly.
Search annotations are retained in records but Snarky uses its own configured
search policy. The same compiled JSON is supplied to Prune.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from itertools import product
from pathlib import Path
from time import perf_counter

from snarky import Atom, Number
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    LinearObjective,
    Query,
    QueryKind,
    solve,
)
from snarky.finite.constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
    LinearSumConstraint,
    TableConstraint,
)


class UnsupportedModel(ValueError):
    pass


class Bridge:
    def __init__(
        self,
        document,
        *,
        max_domain=10000,
        max_total_domain=1000000,
        max_table=250000,
        nvalue_encoding="native",
    ):
        if nvalue_encoding not in ("native", "decomposed"):
            raise ValueError("unknown NValue encoding")
        self.nvalue_encoding = nvalue_encoding
        self.document = document
        self.max_table = max_table
        self.variables = {}
        self.constraints = []
        self.serial = 0
        self.lowerings = Counter()
        self.total_domain = 0
        self.max_total_domain = max_total_domain
        for name, entry in document["variables"].items():
            if entry["type"] not in ("bool", "int"):
                raise UnsupportedModel(f"unsupported variable type: {entry['type']}")
            ranges = [[0, 1]] if entry["type"] == "bool" else entry.get("domain")
            if ranges is None:
                raise UnsupportedModel("unbounded integer domain")
            volume = sum(hi - lo + 1 for lo, hi in ranges)
            if volume > max_domain:
                raise UnsupportedModel(
                    f"explicit domain limit: {name} has {volume} values"
                )
            self.add_variable(name, (v for lo, hi in ranges for v in range(lo, hi + 1)))
        for constraint in document["constraints"]:
            self.constraint(constraint["id"], constraint["args"])
        method = document["solve"]["method"]
        objective = None
        if method in ("minimize", "maximize"):
            raw = document["solve"]["objective"]
            objective = LinearObjective(((1, self.variable(raw)),))
        elif method != "satisfy":
            raise UnsupportedModel(f"unsupported solve method: {method}")
        self.model = FiniteModel(
            "prune_shared_flatzinc",
            tuple(self.variables.values()),
            tuple(self.constraints),
            objective=objective,
        )

    def name(self, prefix):
        self.serial += 1
        return f"__bridge_{prefix}_{self.serial}"

    def add_variable(self, name, values):
        domain = tuple(Number(int(v)) for v in values)
        self.total_domain += len(domain)
        if self.total_domain > self.max_total_domain:
            raise UnsupportedModel("total explicit domain limit")
        self.variables[name] = FiniteVariable(Atom(name), domain)
        return Atom(name)

    def resolve(self, value):
        if isinstance(value, str) and value in self.document.get("arrays", {}):
            return [self.resolve(v) for v in self.document["arrays"][value]["a"]]
        if isinstance(value, list):
            return [self.resolve(v) for v in value]
        return value

    def variable(self, value):
        if isinstance(value, str):
            if value not in self.variables:
                raise UnsupportedModel(f"unknown variable {value}")
            return Atom(value)
        if type(value) in (int, bool):
            name = f"__bridge_constant_{int(value)}"
            if name not in self.variables:
                self.add_variable(name, [int(value)])
            return Atom(name)
        raise UnsupportedModel(f"unsupported scalar: {value!r}")

    def impossible(self):
        self.add_variable(self.name("false"), [])

    def linear(self, coefficients, values, relation, rhs):
        if type(rhs) not in (int, bool):
            coefficients = [*coefficients, -1]
            values = [*values, rhs]
            rhs = 0
        terms = Counter()
        for coefficient, value in zip(coefficients, values, strict=True):
            if isinstance(value, str):
                terms[self.variable(value)] += coefficient
            else:
                rhs -= coefficient * int(value)
        terms = {v: c for v, c in terms.items() if c}
        if not terms:
            if not {"eq": rhs == 0, "le": rhs >= 0, "ne": rhs != 0}[relation]:
                self.impossible()
            return
        if relation == "ne":
            items = list(terms.items())
            if len(items) == 2 and items[0][1] == -items[1][1] and rhs == 0:
                self.constraints.append(
                    BinaryComparisonConstraint(
                        Atom(self.name("ne")),
                        items[0][0],
                        items[1][0],
                        BinaryComparisonOperator.NOT_EQUAL,
                    )
                )
            else:
                self.table(
                    tuple(terms),
                    lambda row: (
                        sum(c * x for c, x in zip(terms.values(), row, strict=True))
                        != rhs
                    ),
                )
            return
        self.constraints.append(
            LinearSumConstraint(
                Atom(self.name("linear")),
                tuple((c, v) for v, c in terms.items()),
                ConstraintOperator.EQUAL
                if relation == "eq"
                else ConstraintOperator.LESS_EQUAL,
                int(rhs),
            )
        )

    def table(self, scope, predicate):
        unique = tuple(dict.fromkeys(scope))
        positions = [unique.index(v) for v in scope]
        domains = [
            tuple(n.value for n in self.variables[v.name].domain) for v in unique
        ]
        if math.prod(map(len, domains)) > self.max_table:
            raise UnsupportedModel("extensional lowering exceeds tuple budget")
        rows = tuple(
            tuple(Number(x) for x in row)
            for row in product(*domains)
            if predicate(tuple(row[i] for i in positions))
        )
        if not rows:
            self.impossible()
        elif not unique:
            return
        else:
            self.constraints.append(
                TableConstraint(Atom(self.name("table")), unique, rows)
            )

    def nvalue(self, target, values):
        if self.nvalue_encoding == "native":
            from snarky.finite.constraints import NValueConstraint

            scope = tuple(self.variable(v) for v in values if isinstance(v, str))
            constants = tuple(Number(int(v)) for v in values if not isinstance(v, str))
            count = (
                int(target) if type(target) in (int, bool) else self.variable(target)
            )
            self.constraints.append(
                NValueConstraint(Atom(self.name("nvalue")), scope, count, constants)
            )
            self.lowerings["nvalue_native"] += 1
            return
        scope = tuple(dict.fromkeys(self.variable(v) for v in values))
        alphabet = sorted(
            {n.value for v in scope for n in self.variables[v.name].domain}
        )
        if type(target) is int and (
            target > min(len(scope), len(alphabet))
            or target < 0
            or (scope and target == 0)
        ):
            self.impossible()
            return
        if type(target) is int and target == len(scope):
            self.lowerings["nvalue_to_all_different"] += 1
            if scope:
                self.constraints.append(
                    AllDifferentConstraint(Atom(self.name("nvalue_ad")), scope)
                )
            return
        self.lowerings["nvalue_to_incidence_tables"] += 1
        present = []
        for value in alphabet:
            used = self.add_variable(self.name("used"), [0, 1])
            present.append(used.name)
            incidences = []
            for variable in scope:
                domain = self.variables[variable.name].domain
                if Number(value) not in domain:
                    continue
                bit = self.add_variable(self.name("incidence"), [0, 1])
                incidences.append(bit.name)
                self.constraints.append(
                    TableConstraint(
                        Atom(self.name("channel")),
                        (variable, bit),
                        tuple((n, Number(int(n.value == value))) for n in domain),
                    )
                )
            self.linear(
                [1] * len(incidences) + [-len(incidences)],
                [*incidences, used.name],
                "le",
                0,
            )
            self.linear([-1] * len(incidences) + [1], [*incidences, used.name], "le", 0)
        self.linear([1] * len(present), present, "eq", target)

    def constraint(self, identifier, raw):
        args = [self.resolve(x) for x in raw]
        if identifier in ("fzn_all_different_int", "all_different_int"):
            scope = tuple(self.variable(v) for v in args[0])
            if len(set(scope)) != len(scope):
                self.impossible()
            elif scope:
                self.constraints.append(
                    AllDifferentConstraint(Atom(self.name("ad")), scope)
                )
        elif identifier in (
            "int_lin_eq",
            "int_lin_le",
            "int_lin_ne",
            "bool_lin_eq",
            "bool_lin_le",
        ):
            self.linear(*args[:2], identifier.rsplit("_", 1)[-1], args[2])
        elif identifier in (
            "int_eq",
            "int_le",
            "int_lt",
            "int_ne",
            "bool_eq",
            "bool_le",
            "bool_ne",
            "bool2int",
        ):
            relation = {"int_lt": "le", "bool2int": "eq"}.get(
                identifier, identifier.rsplit("_", 1)[-1]
            )
            self.linear([1, -1], args, relation, -1 if identifier == "int_lt" else 0)
        elif identifier == "bool_clause":
            positive, negative = args
            self.linear(
                [-1] * len(positive) + [1] * len(negative),
                [*positive, *negative],
                "le",
                len(negative) - 1,
            )
        elif identifier == "fzn_nvalue":
            self.nvalue(args[0], args[1])
        else:
            raise UnsupportedModel(f"unsupported FlatZinc predicate: {identifier}")

    def raw_assignment(self, solution):
        return {
            name: int(solution.assignment[Atom(name)].value)
            for name in self.document["variables"]
        }

    def render(self, solution):
        assignment = self.raw_assignment(solution)

        def value(raw):
            raw = self.resolve(raw)
            if isinstance(raw, list):
                return "[" + ", ".join(value(v) for v in raw) + "]"
            if isinstance(raw, str):
                number = assignment[raw]
                return (
                    str(bool(number)).lower()
                    if self.document["variables"][raw]["type"] == "bool"
                    else str(number)
                )
            return str(raw).lower() if type(raw) is bool else str(raw)

        return (
            "\n".join(
                f"{name} = {value(name)};" for name in self.document.get("output", [])
            )
            + "\n----------\n"
        )


def validate_assignment(document, assignment):
    """Independent evaluation of original FlatZinc primitives, before lowering."""

    def val(x):
        if isinstance(x, list):
            return [val(v) for v in x]
        if isinstance(x, str):
            if x in document.get("arrays", {}):
                return val(document["arrays"][x]["a"])
            return assignment[x]
        return int(x) if type(x) is bool else x

    for name, entry in document["variables"].items():
        value = assignment[name]
        if entry["type"] == "bool":
            assert value in (0, 1)
        else:
            assert any(lo <= value <= hi for lo, hi in entry["domain"])
    for constraint in document["constraints"]:
        kind = constraint["id"]
        a = [val(x) for x in constraint["args"]]
        if kind in ("fzn_all_different_int", "all_different_int"):
            valid = len(set(a[0])) == len(a[0])
        elif kind in (
            "int_lin_eq",
            "int_lin_le",
            "int_lin_ne",
            "bool_lin_eq",
            "bool_lin_le",
        ):
            total = sum(c * v for c, v in zip(a[0], a[1], strict=True))
            valid = {"eq": total == a[2], "le": total <= a[2], "ne": total != a[2]}[
                kind.rsplit("_", 1)[1]
            ]
        elif kind == "bool_clause":
            valid = any(a[0]) or any(not x for x in a[1])
        elif kind == "fzn_nvalue":
            valid = len(set(a[1])) == a[0]
        elif kind in ("int_eq", "bool_eq", "bool2int"):
            valid = a[0] == a[1]
        elif kind in ("int_le", "bool_le"):
            valid = a[0] <= a[1]
        elif kind == "int_lt":
            valid = a[0] < a[1]
        elif kind in ("int_ne", "bool_ne"):
            valid = a[0] != a[1]
        else:
            raise UnsupportedModel(kind)
        assert valid, (kind, a)


def worker():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--policy", default="dom_wdeg", choices=("dom_wdeg", "mrv"))
    parser.add_argument("--nvalue", choices=("native", "decomposed"), default="native")
    args = parser.parse_args()
    started = perf_counter()
    document = json.loads(args.model.read_text())
    try:
        bridge = Bridge(document, nvalue_encoding=args.nvalue)
    except UnsupportedModel as error:
        print(
            json.dumps({"status": "unsupported", "diagnostic": str(error)}),
            file=sys.stderr,
        )
        raise SystemExit(3) from error
    prepared = perf_counter()
    kind = {
        "satisfy": QueryKind.ENUMERATE if args.all else QueryKind.SOLVE,
        "minimize": QueryKind.MINIMIZE,
        "maximize": QueryKind.MAXIMIZE,
    }[document["solve"]["method"]]
    result = solve(bridge.model, Query(kind), policy=args.policy)
    ended = perf_counter()
    for solution in result.solutions:
        validate_assignment(document, bridge.raw_assignment(solution))
        print(bridge.render(solution), end="")
    if result.status.value == "infeasible":
        print("=====UNSATISFIABLE=====")
    elif result.complete:
        print("==========")
    elif not result.solutions:
        print("=====UNKNOWN=====")
    print(
        json.dumps(
            {
                "status": result.status.value,
                "nodes": result.explored_nodes,
                "failures": result.failed_branches,
                "revisions": result.constraint_revisions,
                "preparation_seconds": prepared - started,
                "solve_seconds": ended - prepared,
                "lowerings": dict(bridge.lowerings),
                "variables": len(bridge.model.variables),
                "constraints": len(bridge.model.constraints),
                "original_variables": len(document["variables"]),
                "objective": result.incumbent.objective_value
                if result.incumbent
                else None,
            }
        ),
        file=sys.stderr,
    )


if __name__ == "__main__":
    worker()
