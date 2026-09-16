"""Exact finite inference algorithms with explicit rational/float arithmetic.

The exhaustive and native-search frontends share the declared measure, not a
search weighting policy. Incomplete enumeration never yields a normalized
partial distribution or an allegedly exact sample.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from random import Random
from time import perf_counter
from types import MappingProxyType
from typing import Protocol

from ..factors import evaluate_factor_model
from ..instantiation import NaiveInstantiationStrategy
from ..terms import Term
from .measure import Measure
from .model import (
    FiniteModel,
    Query,
    QueryKind,
    QueryResult,
    ResultStatus,
    Solution,
    Termination,
)

type Mass = Fraction | float


class InferenceDistribution(Protocol):
    @property
    def log_partition(self) -> float: ...
    @property
    def partition(self) -> Mass: ...
    @property
    def certificate(self) -> str: ...
    @property
    def factor_expectations(self) -> Mapping[str, Mass]: ...
    @property
    def marginals(self) -> Mapping[Term, Mapping[Term, Mass]]: ...
    def mass(self, evidence: Mapping[Term, Term]) -> Mass: ...
    def probability(self, evidence: Mapping[Term, Term]) -> Mass: ...
    def conditional(
        self, variable: Term, given: Mapping[Term, Term] | None = None
    ) -> Mapping[Term, Mass]: ...
    def sample(self, rng: Random | int | None = None) -> Mapping[Term, Term]: ...


def logsum(values: list[float]) -> float:
    finite = [value for value in values if value != -math.inf]
    if not finite:
        return -math.inf
    peak = max(finite)
    return peak + math.log(math.fsum(math.exp(value - peak) for value in finite))


def exp_mass(log_value: float) -> float:
    try:
        return math.exp(log_value)
    except OverflowError:
        return math.inf


@dataclass(frozen=True, slots=True)
class InferenceSummary:
    """Materialized finite distribution, suitable for tiny exact reference queries.

    Float log masses remain meaningful when ordinary partition mass overflows.
    Marginals and samples then use log-normalized probabilities. Rational models
    retain exact masses and sample with integer draws, without float conversion.
    """

    variables: tuple[Term, ...]
    log_masses: Mapping[tuple[Term, ...], float]
    rational_masses: Mapping[tuple[Term, ...], Fraction] | None
    factor_expectations: Mapping[str, Mass]
    certificate: str
    log_partition: float
    partition: Mass

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "log_masses", MappingProxyType(dict(self.log_masses)))
        object.__setattr__(
            self,
            "factor_expectations",
            MappingProxyType(dict(self.factor_expectations)),
        )
        if self.rational_masses is not None:
            object.__setattr__(
                self, "rational_masses", MappingProxyType(dict(self.rational_masses))
            )

    def _selected(self, evidence: Mapping[Term, Term]) -> list[tuple[Term, ...]]:
        if set(evidence) - set(self.variables):
            raise ValueError("evidence names undeclared variables")
        indexes = [
            (self.variables.index(var), value) for var, value in evidence.items()
        ]
        return [
            row
            for row in self.log_masses
            if all(row[index] == value for index, value in indexes)
        ]

    def mass(self, evidence: Mapping[Term, Term]) -> Mass:
        """Unnormalized total completion mass of an arbitrary partial assignment."""
        selected = self._selected(evidence)
        if self.rational_masses is not None:
            return sum((self.rational_masses[row] for row in selected), Fraction())
        return exp_mass(logsum([self.log_masses[row] for row in selected]))

    def probability(self, evidence: Mapping[Term, Term]) -> Mass:
        selected = self._selected(evidence)
        if self.rational_masses is not None:
            assert isinstance(self.partition, Fraction)
            return (
                sum((self.rational_masses[row] for row in selected), Fraction())
                / self.partition
            )
        return math.exp(
            logsum([self.log_masses[row] for row in selected]) - self.log_partition
        )

    def conditional(
        self, variable: Term, given: Mapping[Term, Term] | None = None
    ) -> Mapping[Term, Mass]:
        evidence = {} if given is None else dict(given)
        if variable not in self.variables or variable in evidence:
            raise ValueError("conditional variable must be declared and unassigned")
        selected = self._selected(evidence)
        if not selected:
            raise ValueError("conditioning event has zero mass")
        index = self.variables.index(variable)
        by_value: dict[Term, list[tuple[Term, ...]]] = {}
        for row in selected:
            by_value.setdefault(row[index], []).append(row)
        if self.rational_masses is not None:
            denominator = sum(
                (self.rational_masses[row] for row in selected), Fraction()
            )
            return MappingProxyType(
                {
                    value: sum((self.rational_masses[row] for row in rows), Fraction())
                    / denominator
                    for value, rows in by_value.items()
                }
            )
        denominator_log = logsum([self.log_masses[row] for row in selected])
        return MappingProxyType(
            {
                value: math.exp(
                    logsum([self.log_masses[row] for row in rows]) - denominator_log
                )
                for value, rows in by_value.items()
            }
        )

    @property
    def marginals(self) -> Mapping[Term, Mapping[Term, Mass]]:
        return MappingProxyType(
            {variable: self.conditional(variable) for variable in self.variables}
        )

    def sample(self, rng: Random | int | None = None) -> Mapping[Term, Term]:
        generator = rng if isinstance(rng, Random) else Random(rng)
        rows = tuple(self.log_masses)
        if self.rational_masses is not None:
            masses = tuple(self.rational_masses[row] for row in rows)
            denominator = math.lcm(*(mass.denominator for mass in masses))
            weights = [
                mass.numerator * (denominator // mass.denominator) for mass in masses
            ]
            threshold = generator.randrange(sum(weights))
            selected = rows[-1]
            for row, weight in zip(rows, weights, strict=True):
                if threshold < weight:
                    selected = row
                    break
                threshold -= weight
        else:
            peak = max(self.log_masses.values())
            weights_float = [math.exp(self.log_masses[row] - peak) for row in rows]
            threshold_float = generator.random() * math.fsum(weights_float)
            selected = rows[-1]
            for row, float_weight in zip(rows, weights_float, strict=True):
                if threshold_float < float_weight:
                    selected = row
                    break
                threshold_float -= float_weight
        return MappingProxyType(dict(zip(self.variables, selected, strict=True)))


def infer(
    model: FiniteModel, query: Query | None = None, *, backend: str = "weighted_search"
) -> QueryResult:
    """Normalize all feasible completions, using enumeration or native search."""
    query = Query(QueryKind.PARTITION) if query is None else query
    if query.kind not in (QueryKind.PARTITION, QueryKind.SAMPLE_EXACT):
        raise ValueError("inference requires a probability query")
    if backend == "regular_bp":
        from .regular import infer_regular

        return infer_regular(model, query)
    if backend not in ("enumeration", "weighted_search"):
        return QueryResult(
            ResultStatus.UNSUPPORTED,
            Termination.UNSUPPORTED,
            backend=backend,
            diagnostic="unsupported inference backend",
        )
    started = perf_counter()
    deadline = (
        None if query.time_limit_seconds is None else started + query.time_limit_seconds
    )
    enumeration_query = Query(
        QueryKind.ENUMERATE,
        max_nodes=query.max_nodes,
        time_limit_seconds=query.time_limit_seconds,
    )
    from .oracle import enumerate_model
    from .search import solve

    result = (
        enumerate_model(model, enumeration_query)
        if backend == "enumeration"
        else solve(model, enumeration_query)
    )
    measure = Measure() if model.measure is None else model.measure
    arithmetic = "rational" if measure.rational else "float64_log"
    if not result.complete:
        return QueryResult(
            ResultStatus.UNKNOWN,
            result.termination,
            explored_nodes=result.explored_nodes,
            backend=backend,
            arithmetic=arithmetic,
            diagnostic=(
                "completion mass is incomplete; "
                "no normalized distribution or exact sample"
            ),
            elapsed_seconds=perf_counter() - started,
        )
    names = tuple(var.name for var in model.variables)
    log_masses: dict[tuple[Term, ...], float] = {}
    exact: dict[tuple[Term, ...], Fraction] = {}
    features: dict[tuple[Term, ...], dict[str, int]] = {}
    positive_solutions = {}
    for solution in result.solutions:
        if deadline is not None and perf_counter() >= deadline:
            return QueryResult(
                ResultStatus.UNKNOWN,
                Termination.TIME_LIMIT,
                backend=backend,
                arithmetic=arithmetic,
                diagnostic="measure evaluation exceeded time budget",
            )
        mass = Fraction(1)
        for table in measure.base:
            mass *= table.weight(solution.assignment)
        if not mass:
            continue
        row = tuple(solution.assignment[var] for var in names)
        score_parts: list[int | float] = []
        counts: dict[str, int] = {}
        for log_table in measure.log_tables:
            contribution = log_table.contribution(solution.assignment)
            score_parts.append(contribution.value)
            counts[log_table.name] = contribution.value
        if measure.factors is not None:
            evaluated = evaluate_factor_model(
                measure.factors,
                tuple(sorted(solution.facts, key=repr)),
                strategy=NaiveInstantiationStrategy()
                if backend == "enumeration"
                else None,
            )
            for activation in evaluated.activations:
                score_parts.append(activation.log_weight)
                counts[activation.factor_name] = (
                    counts.get(activation.factor_name, 0) + 1
                )
        try:
            score = math.fsum(score_parts)
            log_mass = math.log(mass.numerator) - math.log(mass.denominator) + score
        except OverflowError:
            log_mass = math.inf
        if not math.isfinite(log_mass):
            return QueryResult(
                ResultStatus.UNSUPPORTED,
                Termination.UNSUPPORTED,
                backend=backend,
                arithmetic=arithmetic,
                diagnostic="log mass outside supported numerical range",
            )
        log_masses[row] = log_mass
        if measure.rational:
            exact[row] = mass
        features[row] = counts
        positive_solutions[row] = solution
    if deadline is not None and perf_counter() >= deadline:
        return QueryResult(
            ResultStatus.UNKNOWN,
            Termination.TIME_LIMIT,
            backend=backend,
            arithmetic=arithmetic,
            diagnostic="measure evaluation exceeded time budget",
        )
    if not log_masses:
        return QueryResult(
            ResultStatus.ZERO_MASS,
            Termination.EXHAUSTED,
            explored_nodes=result.explored_nodes,
            backend=backend,
            arithmetic=arithmetic,
            diagnostic="no positive-mass feasible completion",
        )
    partition: Mass = (
        sum(exact.values(), Fraction())
        if measure.rational
        else exp_mass(logsum(list(log_masses.values())))
    )
    log_partition = (
        math.log(partition.numerator) - math.log(partition.denominator)
        if isinstance(partition, Fraction)
        else logsum(list(log_masses.values()))
    )
    feature_names = {table.name for table in measure.log_tables}
    if measure.factors is not None:
        feature_names.update(
            f.name for group in measure.factors.groups for f in group.factors
        )
    expectations: dict[str, Mass] = {
        name: math.fsum(
            counts.get(name, 0) * math.exp(log_masses[row] - log_partition)
            for row, counts in features.items()
        )
        for name in sorted(feature_names)
    }
    summary = InferenceSummary(
        names,
        log_masses,
        exact if measure.rational else None,
        expectations,
        "EXACT_ENUMERATION" if backend == "enumeration" else "EXACT_WEIGHTED_BACKTRACK",
        log_partition,
        partition,
    )
    samples: tuple[Solution, ...] = ()
    if query.kind is QueryKind.SAMPLE_EXACT:
        generator = Random(query.seed)
        # A single draw supplies the whole assignment; never redraw per variable.
        selected = []
        for _ in range(query.sample_count):
            if deadline is not None and perf_counter() >= deadline:
                return QueryResult(
                    ResultStatus.UNKNOWN,
                    Termination.TIME_LIMIT,
                    backend=backend,
                    arithmetic=arithmetic,
                    diagnostic="sampling exceeded time budget",
                )
            assignment = summary.sample(generator)
            selected.append(positive_solutions[tuple(assignment[var] for var in names)])
        samples = tuple(selected)
    return QueryResult(
        ResultStatus.FEASIBLE,
        Termination.EXHAUSTED,
        samples,
        explored_nodes=result.explored_nodes,
        backend=backend,
        arithmetic=arithmetic,
        inference=summary,
        elapsed_seconds=perf_counter() - started,
    )
