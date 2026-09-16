"""Iterative reversible DFS and exact numeric branch-and-bound over problem states."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from fractions import Fraction
from time import perf_counter
from typing import Protocol

from ..engine.group_execution import InferenceLimitError
from ..terms import Atom, Term
from .bounds import NoObjectiveCompletion, ObjectiveBound, compile_objective_bound
from .domains import FiniteDomains
from .model import (
    FiniteModel,
    IncumbentRecord,
    Query,
    QueryKind,
    QueryResult,
    ResultStatus,
    Solution,
    Termination,
)
from .oracle import feasible
from .product_objective import RationalProductObjective
from .propagation import NativeState


class SearchState[Checkpoint](Protocol):
    model: FiniteModel
    domains: FiniteDomains

    @property
    def failure(self) -> Atom | None: ...
    @property
    def revisions(self) -> int: ...

    def checkpoint(self) -> Checkpoint: ...
    def rollback(self, checkpoint: Checkpoint) -> None: ...
    def release(self, checkpoint: Checkpoint) -> None: ...
    def restrict(self, variable: Term, value: Term) -> None: ...
    def propagate(self, *, deadline: float | None = None) -> bool: ...
    def solution(self) -> Solution: ...


@dataclass(slots=True)
class _Frame[Checkpoint]:
    checkpoint: Checkpoint
    variable: Term
    values: Iterator[Term]


@dataclass(frozen=True, slots=True)
class SearchProgress:
    """Opt-in observation of DFS, not a proof or a remaining-frontier bound.

    Nodes count entered nodes, including a currently unfinished propagation.
    Only ``result`` on the final event carries a termination/proof status.
    Observers must not mutate search state. Exceptions unwind checkpoints.
    """

    event: str
    explored_nodes: int
    failed_branches: int
    pruned_branches: int
    constraint_revisions: int
    depth: int
    elapsed_seconds: float
    incumbent: Solution | None
    root_objective_bound: int | Fraction | None
    result: QueryResult | None = None


def solve(
    model: FiniteModel,
    query: Query | None = None,
    *,
    variable_order: tuple[Atom, ...] | None = None,
    reverse_values: bool = False,
    policy: str = "dom_wdeg",
    bounding: str = "auto",
    value_policy: str = "declared",
    initial_assignment: Mapping[Term, Term] | None = None,
    on_progress: Callable[[SearchProgress], None] | None = None,
) -> QueryResult:
    """Run native domains, adding the rule coordinator only for mixed models."""
    query = Query() if query is None else query
    if initial_assignment is not None and query.kind not in (
        QueryKind.MINIMIZE,
        QueryKind.MAXIMIZE,
    ):
        raise ValueError("initial assignment requires an optimization query")
    if query.kind in (QueryKind.PARTITION, QueryKind.SAMPLE_EXACT):
        if on_progress is not None:
            raise ValueError("progress observation requires a DFS search query")
        from .inference import infer

        return infer(model, query, backend="weighted_search")
    if model.rules:
        from .mixed import MixedState

        return search(
            MixedState(model),
            query,
            variable_order=variable_order,
            reverse_values=reverse_values,
            policy=policy,
            bounding=bounding,
            value_policy=value_policy,
            initial_assignment=initial_assignment,
            on_progress=on_progress,
        )
    return search(
        NativeState(model),
        query,
        variable_order=variable_order,
        reverse_values=reverse_values,
        policy=policy,
        bounding=bounding,
        value_policy=value_policy,
        initial_assignment=initial_assignment,
        on_progress=on_progress,
    )


def search[Checkpoint](
    state: SearchState[Checkpoint],
    query: Query,
    *,
    variable_order: tuple[Atom, ...] | None = None,
    reverse_values: bool = False,
    policy: str = "dom_wdeg",
    bounding: str = "auto",
    value_policy: str = "declared",
    initial_assignment: Mapping[Term, Term] | None = None,
    on_progress: Callable[[SearchProgress], None] | None = None,
) -> QueryResult:
    """The controller owns incumbents; state checkpoints own only branch state."""
    model = state.model
    if query.kind in (QueryKind.PARTITION, QueryKind.SAMPLE_EXACT):
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend="native",
            diagnostic="unsupported query",
        )
    optimizing = query.kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE)
    if initial_assignment is not None and not optimizing:
        raise ValueError("initial assignment requires an optimization query")
    if optimizing and model.objective is None:
        raise ValueError("optimization requires an explicit objective")
    if policy not in ("mrv", "dom_wdeg"):
        raise ValueError("unknown native search policy")
    if bounding not in ("auto", "chain", "local"):
        raise ValueError("bounding must be auto, chain or local")
    if value_policy not in ("declared", "objective"):
        raise ValueError("value_policy must be declared or objective")
    if value_policy == "objective" and not optimizing:
        raise ValueError("objective value ordering requires an optimization query")
    names = tuple(var.name for var in model.variables)
    if initial_assignment is not None and (
        set(initial_assignment) != set(names)
        or any(initial_assignment[v] not in state.domains.values(v) for v in names)
    ):
        raise ValueError("initial assignment must cover current domains exactly")
    if variable_order is not None and (
        len(variable_order) != len(names) or set(variable_order) != set(names)
    ):
        raise ValueError("variable_order must contain every variable exactly once")
    names = names if variable_order is None else variable_order
    started = perf_counter()
    deadline = (
        None if query.time_limit_seconds is None else started + query.time_limit_seconds
    )
    weights = {constraint.name: 1 for constraint in model.constraints}
    # Visit each scope once, preserving constraint order and the old membership
    # semantics for scopes with repeated references (e.g. predicates).
    incident: dict[Term, list[Atom]] = {var: [] for var in names}
    for constraint in model.constraints:
        for var in dict.fromkeys(constraint.variables):
            incident[var].append(constraint.name)
    solutions: list[Solution] = []
    history: list[int | Fraction] = []
    objective_bound: ObjectiveBound = (
        model.objective.bounds if model.objective is not None else lambda domains: None
    )
    milestones: list[IncumbentRecord] = []
    frames: list[_Frame[Checkpoint]] = []
    explored = failed = pruned = 0
    global_bound = None
    observed_root_bound = None
    termination = Termination.EXHAUSTED
    diagnostic = ""
    root = state.checkpoint()

    def emit(event: str, result: QueryResult | None = None) -> None:
        if on_progress is not None:
            on_progress(
                SearchProgress(
                    event,
                    explored,
                    failed,
                    pruned,
                    state.revisions,
                    len(frames),
                    perf_counter() - started,
                    solutions[0] if solutions else None,
                    observed_root_bound,
                    result,
                )
            )

    def advance() -> bool:
        while frames:
            frame = frames[-1]
            state.rollback(frame.checkpoint)
            value = next(frame.values, None)
            if value is None:
                state.release(frame.checkpoint)
                frames.pop()
                continue
            state.restrict(frame.variable, value)
            return True
        return False

    try:
        emit("start")
        if initial_assignment is not None:
            seed_checkpoint = state.checkpoint()
            try:
                for name in names:
                    state.restrict(name, initial_assignment[name])
                if not state.propagate(deadline=deadline):
                    raise ValueError("initial assignment is infeasible")
                seed_solution = state.solution()
                if not feasible(model, seed_solution.assignment, seed_solution.facts):
                    raise ValueError("initial assignment is infeasible")
                assert seed_solution.objective_value is not None
                solutions.append(seed_solution)
                history.append(seed_solution.objective_value)
                milestones.append(
                    IncumbentRecord(
                        seed_solution.objective_value, 0, perf_counter() - started
                    )
                )
                emit("incumbent")
            finally:
                state.rollback(seed_checkpoint)
                state.release(seed_checkpoint)
        if bounding != "local" and optimizing:
            objective_bound = compile_objective_bound(
                model, deadline=deadline, use_permutation=bounding == "auto"
            )
        while True:
            if query.max_nodes is not None and explored >= query.max_nodes:
                termination = Termination.NODE_LIMIT
                break
            if deadline is not None and perf_counter() >= deadline:
                termination = Termination.TIME_LIMIT
                break
            explored += 1
            if on_progress is not None:
                emit("node")
            try:
                consistent = state.propagate(deadline=deadline)
            except TimeoutError:
                termination = Termination.TIME_LIMIT
                break
            except InferenceLimitError as error:
                termination = Termination.RESOURCE_LIMIT
                diagnostic = str(error)
                break
            if not consistent:
                failed += 1
                if state.failure in weights:
                    weights[state.failure] += 1
                if not advance():
                    break
                continue
            if optimizing:
                assert model.objective is not None
                try:
                    bounds = objective_bound(state.domains.snapshot())
                except NoObjectiveCompletion:
                    failed += 1
                    if not advance():
                        break
                    continue
                bound = (
                    None
                    if bounds is None
                    else bounds[0 if query.kind is QueryKind.MINIMIZE else 1]
                )
                if explored == 1:
                    global_bound = bound
                    observed_root_bound = bound
                if on_progress is not None:
                    emit("bound")
                incumbent = solutions[0].objective_value if solutions else None
                if (
                    bound is not None
                    and incumbent is not None
                    and (
                        bound >= incumbent
                        if query.kind is QueryKind.MINIMIZE
                        else bound <= incumbent
                    )
                ):
                    pruned += 1
                    if not advance():
                        break
                    continue
            if state.domains.complete:
                solution = state.solution()
                if feasible(model, solution.assignment, solution.facts):
                    value = solution.objective_value
                    if optimizing:
                        assert value is not None
                        previous = solutions[0].objective_value if solutions else None
                        if previous is None or (
                            value < previous
                            if query.kind is QueryKind.MINIMIZE
                            else value > previous
                        ):
                            solutions[:] = [solution]
                            history.append(value)
                            milestones.append(
                                IncumbentRecord(
                                    value, explored, perf_counter() - started
                                )
                            )
                            emit("incumbent")
                            if global_bound is not None and value == global_bound:
                                # The root relaxation bounds every remaining branch.
                                # Reaching it proves optimality without visiting them.
                                break
                    else:
                        solutions.append(solution)
                        if query.kind is QueryKind.SOLVE or (
                            query.max_solutions is not None
                            and len(solutions) >= query.max_solutions
                        ):
                            termination = Termination.SOLUTION_LIMIT
                            break
                else:
                    failed += 1
                if not advance():
                    break
                continue
            unresolved = [var for var in names if state.domains.size(var) > 1]
            if variable_order is not None:
                variable = unresolved[0]
            else:
                variable = min(
                    unresolved,
                    key=lambda var: (
                        state.domains.size(var)
                        / max(1, sum(weights[c] for c in incident[var]))
                        if policy == "dom_wdeg"
                        else state.domains.size(var)
                    ),
                )
            values = state.domains.values(variable)
            if reverse_values:
                values = values[::-1]
            if value_policy == "objective":
                current_domains = dict(state.domains.snapshot())
                ranked = []
                for symbol in values:
                    current_domains[variable] = frozenset((symbol,))
                    try:
                        interval = objective_bound(current_domains)
                    except NoObjectiveCompletion:
                        pruned += 1
                        continue
                    priority = (
                        0
                        if interval is None
                        else (
                            interval[0]
                            if query.kind is QueryKind.MINIMIZE
                            else -interval[1]
                        )
                    )
                    if interval is not None and solutions:
                        incumbent = solutions[0].objective_value
                        assert incumbent is not None
                        if (
                            interval[0] >= incumbent
                            if query.kind is QueryKind.MINIMIZE
                            else interval[1] <= incumbent
                        ):
                            pruned += 1
                            continue
                    ranked.append((priority, symbol))
                values = tuple(
                    symbol for _, symbol in sorted(ranked, key=lambda item: item[0])
                )
            frames.append(_Frame(state.checkpoint(), variable, iter(values)))
            if not advance():
                break
    except TimeoutError:
        termination = Termination.TIME_LIMIT
    except InferenceLimitError as error:
        termination = Termination.RESOURCE_LIMIT
        diagnostic = str(error)
    finally:
        for frame in reversed(frames):
            state.rollback(frame.checkpoint)
            state.release(frame.checkpoint)
        state.rollback(root)
        state.release(root)

    complete = termination is Termination.EXHAUSTED
    if not solutions:
        status = ResultStatus.INFEASIBLE if complete else ResultStatus.UNKNOWN
    elif optimizing and complete:
        status = ResultStatus.OPTIMAL
        global_bound = solutions[0].objective_value
    else:
        status = ResultStatus.FEASIBLE
    result = QueryResult(
        status,
        termination,
        tuple(solutions),
        explored,
        backend="native",
        objective_bound=global_bound,
        arithmetic="rational_product"
        if isinstance(model.objective, RationalProductObjective)
        else "integer",
        failed_branches=failed,
        pruned_branches=pruned,
        constraint_revisions=state.revisions,
        incumbent_values=tuple(history),
        incumbent_history=tuple(milestones),
        elapsed_seconds=perf_counter() - started,
        diagnostic=diagnostic,
    )
    emit("finished", result)
    return result
