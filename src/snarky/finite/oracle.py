"""Exhaustive finite reference: no propagation, heuristics, or objective pruning."""

from __future__ import annotations

from collections.abc import Mapping
from itertools import product
from time import perf_counter
from types import MappingProxyType

from ..facts import Fact
from ..terms import Term
from .closure import reference_closure
from .model import (
    FactConstraint,
    FiniteModel,
    GuardedConstraint,
    PredicateConstraint,
    Query,
    QueryKind,
    QueryResult,
    ResultStatus,
    Solution,
    Termination,
    score_solution,
)
from .predicates import accepts


def feasible(
    model: FiniteModel,
    assignment: Mapping[Term, Term],
    facts: frozenset[Fact],
) -> bool:
    for constraint in model.constraints:
        if isinstance(constraint, GuardedConstraint):
            if constraint.guard in facts and not accepts(
                constraint.constraint, assignment
            ):
                return False
        elif isinstance(constraint, FactConstraint):
            if (
                not set(constraint.required) <= facts
                or set(constraint.forbidden) & facts
            ):
                return False
        elif isinstance(constraint, PredicateConstraint):
            # Restrict extension callbacks to their declared assignment scope.
            scoped = MappingProxyType(
                {var: assignment[var] for var in constraint.variables}
            )
            result = constraint.predicate(scoped, facts)
            if type(result) is not bool:
                raise TypeError("constraint predicates must return bool")
            if not result:
                return False
        elif not accepts(constraint, assignment):
            return False
    return True


def enumerate_model(model: FiniteModel, query: Query | None = None) -> QueryResult:
    query = Query() if query is None else query
    if query.kind in (QueryKind.PARTITION, QueryKind.SAMPLE_EXACT):
        from .inference import infer

        return infer(model, query, backend="enumeration")
    optimizing = query.kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE)
    if optimizing and model.objective is None:
        raise ValueError("optimization requires an explicit objective")
    deadline = (
        None
        if query.time_limit_seconds is None
        else perf_counter() + query.time_limit_seconds
    )
    solutions: list[Solution] = []
    explored = 0
    termination = Termination.EXHAUSTED
    names = tuple(var.name for var in model.variables)
    for values in product(*(var.domain for var in model.variables)):
        if query.max_nodes is not None and explored >= query.max_nodes:
            termination = Termination.NODE_LIMIT
            break
        if deadline is not None and perf_counter() >= deadline:
            termination = Termination.TIME_LIMIT
            break
        explored += 1
        assignment: Mapping[Term, Term] = MappingProxyType(
            dict(zip(names, values, strict=True))
        )
        try:
            facts = reference_closure(model, assignment, deadline=deadline)
        except TimeoutError:
            termination = Termination.TIME_LIMIT
            break
        if not feasible(model, assignment, facts):
            continue
        score, contributions = score_solution(model, assignment, facts, reference=True)
        solution = Solution(assignment, facts, score, contributions=contributions)
        if optimizing:
            previous = solutions[0].objective_value if solutions else None
            assert score is not None
            if previous is None or (
                score < previous
                if query.kind is QueryKind.MINIMIZE
                else score > previous
            ):
                solutions[:] = [solution]
        else:
            solutions.append(solution)
            if query.kind is QueryKind.SOLVE or (
                query.max_solutions is not None
                and len(solutions) >= query.max_solutions
            ):
                termination = Termination.SOLUTION_LIMIT
                break
    complete = termination is Termination.EXHAUSTED
    if not solutions:
        status = ResultStatus.INFEASIBLE if complete else ResultStatus.UNKNOWN
    elif optimizing and complete:
        status = ResultStatus.OPTIMAL
    else:
        status = ResultStatus.FEASIBLE
    return QueryResult(
        status,
        termination,
        tuple(solutions),
        explored,
        objective_bound=(
            solutions[0].objective_value
            if optimizing and complete and solutions
            else None
        ),
    )
