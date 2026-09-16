"""CLI projection of finite results, including distinct explanation categories."""

from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

from ..facts import Fact
from ..terms import render_term
from .language import parse_model_document
from .model import QueryResult, ResultStatus, Termination


def _number(value: int | float | Fraction | None) -> int | float | str | None:
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _fact(fact: Fact) -> str:
    return f"{render_term(fact.entity)} ' {render_term(fact.status)}"


def result_payload(result: QueryResult, *, explain: bool = False) -> dict[str, Any]:
    """JSON-friendly values with exact numerator/denominator for rational numbers."""
    solutions = []
    for solution in result.solutions:
        item: dict[str, Any] = {
            "assignment": {
                render_term(k): render_term(v) for k, v in solution.assignment.items()
            },
            "objective": solution.objective_value,
        }
        if explain:
            item["facts"] = sorted(_fact(fact) for fact in solution.facts)
            item["derivations"] = [
                {
                    "fact": _fact(d.fact),
                    "rule": d.rule_name,
                    "group": d.rule_group,
                    "premises": [_fact(f) for f in d.premises],
                    "proof_depth": d.proof_depth,
                }
                for d in solution.derivations
            ]
            item["reductions"] = [
                {
                    "variable": render_term(r.variable),
                    "removed": sorted(render_term(v) for v in r.values),
                    "cause": render_term(r.cause),
                }
                for r in solution.reductions
            ]
            item["contributions"] = [
                {
                    "factor": c.factor_name,
                    "scope": [render_term(v) for v in c.scope],
                    "value": c.value,
                    "witness_count": c.witness_count,
                    "support": [_fact(f) for f in c.support_facts],
                }
                for c in solution.contributions
            ]
        solutions.append(item)
    payload: dict[str, Any] = {
        "status": result.status.value,
        "termination": result.termination.value,
        "backend": result.backend,
        "arithmetic": result.arithmetic,
        "complete": result.complete,
        "objective_bound": result.objective_bound,
        "solutions": solutions,
        "explored_nodes": result.explored_nodes,
        "failed_branches": result.failed_branches,
        "pruned_branches": result.pruned_branches,
        "constraint_revisions": result.constraint_revisions,
        "elapsed_seconds": result.elapsed_seconds,
        "diagnostic": result.diagnostic,
        "incumbents": [
            {
                "value": point.value,
                "nodes": point.explored_nodes,
                "elapsed_seconds": point.elapsed_seconds,
            }
            for point in result.incumbent_history
        ],
    }
    if result.inference is not None:
        distribution = result.inference
        payload["inference"] = {
            "certificate": distribution.certificate,
            "partition": _number(distribution.partition),
            "log_partition": _number(distribution.log_partition),
            "marginals": {
                render_term(var): {
                    render_term(value): _number(p) for value, p in entries.items()
                }
                for var, entries in distribution.marginals.items()
            },
            "factor_expectations": {
                name: _number(value)
                for name, value in distribution.factor_expectations.items()
            },
        }
    return payload


def run_document(path: str, query: str | None, *, explain: bool = False) -> int:
    try:
        document = parse_model_document(Path(path).read_text(encoding="utf-8"))
        result = document.execute(query)
        print(
            json.dumps(
                result_payload(result, explain=explain), indent=2, allow_nan=False
            )
        )
    except (OSError, ValueError) as error:
        print(f"{path}: {error}", file=sys.stderr)
        return 1
    if result.status is ResultStatus.UNSUPPORTED:
        return 3
    if result.status is ResultStatus.UNKNOWN or result.termination in {
        Termination.NODE_LIMIT,
        Termination.TIME_LIMIT,
        Termination.RESOURCE_LIMIT,
    }:
        return 2
    return 0
