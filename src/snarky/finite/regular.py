"""Optional adapter to the public vo_regular_bp product-BP API.

Only finite-window hard predicates and table measures are compiled. Rules and
premise factors are rejected, not dropped. The sibling library owns BP and exact
conditional sampling; this adapter owns model compilation and projections.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from random import Random
from time import perf_counter
from types import MappingProxyType
from typing import Any

from ..terms import Term
from .closure import reference_closure
from .inference import Mass, exp_mass, logsum
from .measure import Measure
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


class _Budget(Exception):
    def __init__(self, reason: Termination) -> None:
        self.reason = reason


class _Unsupported(Exception):
    pass


def _options(bp: Any, time: int, state: Any) -> tuple[tuple[Any, float], ...]:
    options = bp.transition_weights(time, state)
    if not options:
        return ()
    peak = max(weight for _, weight in options)
    total = math.fsum(weight / peak for _, weight in options)
    return tuple(
        (edge, math.log(weight) - math.log(peak) - math.log(total))
        for edge, weight in options
        if weight > 0
    )


@dataclass(frozen=True, slots=True)
class RegularInferenceSummary:
    variables: tuple[Term, ...]
    log_partition: float
    partition: float
    factor_expectations: Mapping[str, Mass]
    _bp: Any
    _marginals: Mapping[Term, Mapping[Term, Mass]]
    certificate: str = "EXACT_REGULAR_BP"

    def _log_probability(self, evidence: Mapping[Term, Term]) -> float:
        if set(evidence) - set(self.variables):
            raise ValueError("evidence names undeclared variables")
        current = {self._bp.start_state: 0.0}
        for time, variable in enumerate(self.variables):
            following: dict[Any, list[float]] = defaultdict(list)
            for state, log_prefix in current.items():
                for edge, log_probability in _options(self._bp, time, state):
                    if variable not in evidence or edge.symbol == evidence[variable]:
                        following[edge.next_state].append(log_prefix + log_probability)
            current = {state: logsum(values) for state, values in following.items()}
        return logsum(list(current.values()))

    def mass(self, evidence: Mapping[Term, Term]) -> float:
        return exp_mass(self.log_partition + self._log_probability(evidence))

    def probability(self, evidence: Mapping[Term, Term]) -> float:
        return math.exp(self._log_probability(evidence))

    def conditional(
        self, variable: Term, given: Mapping[Term, Term] | None = None
    ) -> Mapping[Term, Mass]:
        evidence = {} if given is None else dict(given)
        if variable not in self.variables or variable in evidence:
            raise ValueError("conditional variable must be declared and unassigned")
        denominator = self._log_probability(evidence)
        if denominator == -math.inf:
            raise ValueError("conditioning event has zero mass")
        probabilities = {}
        for value in self._marginals[variable]:
            numerator = self._log_probability({**evidence, variable: value})
            if numerator != -math.inf:
                probabilities[value] = math.exp(numerator - denominator)
        return MappingProxyType(probabilities)

    @property
    def marginals(self) -> Mapping[Term, Mapping[Term, Mass]]:
        return self._marginals

    def sample(self, rng: Random | int | None = None) -> Mapping[Term, Term]:
        values = self._bp.sample(rng=rng)
        return MappingProxyType(dict(zip(self.variables, values, strict=True)))


def infer_regular(
    model: FiniteModel, query: Query, *, max_window: int = 4
) -> QueryResult:
    if query.kind not in (QueryKind.PARTITION, QueryKind.SAMPLE_EXACT):
        raise ValueError("regular inference requires a probability query")
    if type(max_window) is not int or max_window < 0:
        raise ValueError("max_window must be a nonnegative integer")
    if model.rules or any(
        isinstance(c, (FactConstraint, PredicateConstraint, GuardedConstraint))
        for c in model.constraints
    ):
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend="regular_bp",
            diagnostic=(
                "regular BP requires pure bounded-window constraints; "
                "rules and callbacks need weighted search"
            ),
        )
    measure = Measure() if model.measure is None else model.measure
    if measure.factors is not None:
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend="regular_bp",
            diagnostic=(
                "premise factors require weighted search; "
                "regular BP currently compiles table log factors"
            ),
        )
    try:
        bp_library = import_module("vo_regular_bp")
    except ImportError:
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend="regular_bp",
            diagnostic="optional vo_regular_bp package is not installed",
        )
    started = perf_counter()
    deadline = (
        None if query.time_limit_seconds is None else started + query.time_limit_seconds
    )
    names = tuple(var.name for var in model.variables)
    positions: dict[Term, int] = {name: index for index, name in enumerate(names)}
    domains = model.domains
    hard_constraints = tuple(
        c
        for c in model.constraints
        if not isinstance(c, (FactConstraint, PredicateConstraint, GuardedConstraint))
    )
    components = [*model.constraints, *measure.base, *measure.log_tables]
    width = max(
        (
            max(positions[v] for v in c.variables)
            - min(positions[v] for v in c.variables)
            for c in components
            if c.variables
        ),
        default=0,
    )
    if width > max_window:
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend="regular_bp",
            diagnostic=f"memory window {width} exceeds configured {max_window}",
        )
    alphabet = tuple(
        dict.fromkeys(value for var in model.variables for value in var.domain)
    )
    if any(not var.domain for var in model.variables) or any(
        not accepts(c, {}) for c in hard_constraints if not c.variables
    ):
        return QueryResult(
            ResultStatus.ZERO_MASS,
            Termination.EXHAUSTED,
            backend="regular_bp",
            arithmetic="float64_log",
        )
    # Empty models still have one configuration; a harmless graph alphabet is enough.
    if not alphabet:
        from ..terms import Atom

        alphabet = (Atom("__empty_sequence__"),)
    hard = {
        t: tuple(
            c
            for c in hard_constraints
            if c.variables and max(positions[v] for v in c.variables) == t
        )
        for t in range(len(names))
    }
    base = {
        t: tuple(
            table
            for table in measure.base
            if table.variables and max(positions[v] for v in table.variables) == t
        )
        for t in range(len(names))
    }
    soft = {
        t: tuple(
            table
            for table in measure.log_tables
            if table.variables and max(positions[v] for v in table.variables) == t
        )
        for t in range(len(names))
    }
    seen: set[Any] = set()
    edge_cache: dict[tuple[Any, Term], tuple[Any, float] | None] = {}

    def check_budget() -> None:
        if deadline is not None and perf_counter() >= deadline:
            raise _Budget(Termination.TIME_LIMIT)

    def assignment_at(state: Any, symbol: Term) -> dict[Term, Term]:
        time, memory = state
        values = (*memory, symbol)
        return dict(zip(names[time - len(memory) : time + 1], values, strict=True))

    def compile_edge(state: Any, symbol: Term) -> tuple[Any, float] | None:
        check_budget()
        if state not in seen:
            if query.max_nodes is not None and len(seen) >= query.max_nodes:
                raise _Budget(Termination.NODE_LIMIT)
            seen.add(state)
        key = state, symbol
        if key in edge_cache:
            return edge_cache[key]
        time, memory = state
        if time >= len(names) or symbol not in domains[names[time]]:
            edge_cache[key] = None
            return None
        assignment = assignment_at(state, symbol)
        if any(not accepts(c, assignment) for c in hard[time]):
            edge_cache[key] = None
            return None
        logs = [math.log(len(alphabet))]  # cancel the uniform source graph
        for table in base[time]:
            weight = table.weight(assignment)
            if not weight:
                edge_cache[key] = None
                return None
            logs.append(math.log(weight.numerator) - math.log(weight.denominator))
        logs.extend(float(table.contribution(assignment).value) for table in soft[time])
        log_weight = math.fsum(logs)
        weight_float = exp_mass(log_weight)
        if not math.isfinite(weight_float) or weight_float == 0:
            raise _Unsupported(
                "a local edge weight is outside finite positive float range; "
                "use generic inference"
            )
        following = (time + 1, (*memory, symbol)[-width:] if width else ())
        edge_cache[key] = following, weight_float
        return edge_cache[key]

    def next_state(state: Any, symbol: Term) -> Any:
        edge = compile_edge(state, symbol)
        return None if edge is None else edge[0]

    def transition_weight(state: Any, symbol: Term) -> float:
        edge = compile_edge(state, symbol)
        return 0.0 if edge is None else edge[1]

    try:
        constant_log = 0.0
        for table in measure.base:
            if not table.variables:
                weight = table.weight({})
                if not weight:
                    return QueryResult(
                        ResultStatus.ZERO_MASS,
                        Termination.EXHAUSTED,
                        backend="regular_bp",
                        arithmetic="float64_log",
                    )
                constant_log += math.log(weight.numerator) - math.log(
                    weight.denominator
                )
        constant_log += sum(
            table.contribution({}).value
            for table in measure.log_tables
            if not table.variables
        )
        if not math.isfinite(constant_log):
            raise _Unsupported("constant log weight outside supported numerical range")
        graph = bp_library.ContextGraph(
            {
                (): tuple(
                    bp_library.Edge(symbol, 1 / len(alphabet), ())
                    for symbol in alphabet
                )
            },
            max_order=0,
        )
        acceptor = bp_library.WeightedDFA(
            start_state=(0, ()),
            transition_func=next_state,
            transition_weight_func=transition_weight,
            accept_func=lambda state: state[0] == len(names),
        )
        bp = bp_library.run_bp(graph, acceptor, length=len(names))
        check_budget()
        if bp.log_partition_function == -math.inf:
            return QueryResult(
                ResultStatus.ZERO_MASS,
                Termination.EXHAUSTED,
                backend="regular_bp",
                arithmetic="float64_log",
            )
        log_partition = bp.log_partition_function + constant_log
        # Forward probabilities use the public backward-corrected transition masses.
        current = {bp.start_state: 1.0}
        marginals: dict[Term, Mapping[Term, Mass]] = {}
        expectations = {
            table.name: float(table.contribution({}).value)
            if not table.variables
            else 0.0
            for table in measure.log_tables
        }
        for time, variable in enumerate(names):
            check_budget()
            following_masses: dict[Any, list[float]] = defaultdict(list)
            symbol_masses: dict[Term, list[float]] = defaultdict(list)
            feature_masses: dict[str, list[float]] = defaultdict(list)
            for state, prefix in current.items():
                for edge, log_probability in _options(bp, time, state):
                    posterior = prefix * math.exp(log_probability)
                    following_masses[edge.next_state].append(posterior)
                    symbol_masses[edge.symbol].append(posterior)
                    assignment = assignment_at(state[1], edge.symbol)
                    for log_table in soft[time]:
                        feature_masses[log_table.name].append(
                            posterior * log_table.contribution(assignment).value
                        )
            current = {
                state: math.fsum(values) for state, values in following_masses.items()
            }
            marginals[variable] = MappingProxyType(
                {value: math.fsum(values) for value, values in symbol_masses.items()}
            )
            expectations.update(
                {name: math.fsum(values) for name, values in feature_masses.items()}
            )
        distribution = RegularInferenceSummary(
            names,
            log_partition,
            exp_mass(log_partition),
            MappingProxyType(expectations),
            bp,
            MappingProxyType(marginals),
        )
        solutions = []
        if query.kind is QueryKind.SAMPLE_EXACT:
            generator = Random(query.seed)
            for _ in range(query.sample_count):
                check_budget()
                sampled = distribution.sample(generator)
                facts = reference_closure(model, sampled)
                score, contributions = score_solution(model, sampled, facts)
                solutions.append(
                    Solution(sampled, facts, score, contributions=contributions)
                )
        return QueryResult(
            ResultStatus.FEASIBLE,
            Termination.EXHAUSTED,
            tuple(solutions),
            len(seen),
            backend="regular_bp",
            arithmetic="float64_log",
            inference=distribution,
            elapsed_seconds=perf_counter() - started,
        )
    except _Budget as error:
        return QueryResult(
            ResultStatus.UNKNOWN,
            error.reason,
            backend="regular_bp",
            explored_nodes=len(seen),
            arithmetic="float64_log",
            diagnostic="regular compilation/inference budget exceeded",
        )
    except (_Unsupported, OverflowError) as error:
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend="regular_bp",
            arithmetic="float64_log",
            diagnostic=str(error),
        )
