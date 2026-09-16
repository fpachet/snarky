"""Experimental immutable model contracts, separate from operational CHOICE."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..facts import Fact
from ..rules import RuleGroup
from ..terms import (
    Atom,
    FiniteSequence,
    FiniteSet,
    Number,
    Status,
    Term,
    Triple,
    Variable,
    is_ground,
)
from .constraints import PersistentConstraint
from .factors import FactorObjective, ScoreContribution
from .measure import Measure
from .predicates import integer

if TYPE_CHECKING:
    from ..engine.provenance import Derivation
    from .domains import DomainRemoval
    from .inference import InferenceDistribution

VALUE = Atom("value")


@dataclass(frozen=True, slots=True)
class FiniteVariable:
    name: Atom
    domain: tuple[Term, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, Atom):
            raise TypeError("finite decision variable names must be atoms")
        if any(
            not isinstance(
                value,
                (Atom, Number, Status, Triple, FiniteSequence, FiniteSet, Variable),
            )
            for value in self.domain
        ):
            raise TypeError("finite domains require Snarky terms")
        values = tuple(dict.fromkeys(self.domain))
        if any(not is_ground(value) for value in values):
            raise ValueError("finite domains require ground values")
        # Empty domains represent an infeasible model, not malformed syntax.
        object.__setattr__(self, "domain", values)


@dataclass(frozen=True, slots=True)
class PredicateConstraint:
    """Extension contract: a pure predicate over assignments and closed facts.

    Callbacks are trusted application code, not parsed executable source.
    ``variables`` declares the scope; no partial-state pruning is inferred.
    """

    name: Atom
    variables: tuple[Term, ...]
    predicate: Callable[[Mapping[Term, Term], frozenset[Fact]], bool]

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))


@dataclass(frozen=True, slots=True)
class FactConstraint:
    """Require and/or forbid ground facts in the complete deterministic closure."""

    name: Atom
    required: tuple[Fact, ...] = ()
    forbidden: tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "required", tuple(self.required))
        object.__setattr__(self, "forbidden", tuple(self.forbidden))

    @property
    def variables(self) -> tuple[Term, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class GuardedConstraint:
    """Enforce a constraint when a positive ground fact holds in the closure."""

    name: Atom
    guard: Fact
    constraint: PersistentConstraint

    @property
    def variables(self) -> tuple[Term, ...]:
        return self.constraint.variables


type Constraint = (
    PersistentConstraint | PredicateConstraint | FactConstraint | GuardedConstraint
)


@dataclass(frozen=True, slots=True)
class LinearObjective:
    """An exact integer objective, including a constant offset."""

    terms: tuple[tuple[int, Term], ...] = ()
    offset: int = 0

    def __post_init__(self) -> None:
        terms = tuple(self.terms)
        if type(self.offset) is not int or any(type(c) is not int for c, _ in terms):
            raise TypeError("objective coefficients and offset must be integers")
        combined: dict[Term, int] = {}
        for coefficient, variable in terms:
            combined[variable] = combined.get(variable, 0) + coefficient
        object.__setattr__(
            self,
            "terms",
            tuple(
                (coefficient, variable)
                for variable, coefficient in combined.items()
                if coefficient
            ),
        )

    @property
    def variables(self) -> tuple[Term, ...]:
        return tuple(var for _, var in self.terms)

    def evaluate(
        self, assignment: Mapping[Term, Term], facts: frozenset[Fact] = frozenset()
    ) -> int:
        return self.offset + sum(c * integer(assignment[var]) for c, var in self.terms)

    def bounds(self, domains: Mapping[Term, frozenset[Term]]) -> tuple[int, int]:
        ranges = [
            tuple(c * integer(value) for value in domains[var]) for c, var in self.terms
        ]
        return (
            self.offset + sum(min(values) for values in ranges),
            self.offset + sum(max(values) for values in ranges),
        )


@dataclass(frozen=True, slots=True)
class FiniteModel:
    name: str
    variables: tuple[FiniteVariable, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    context: tuple[Fact, ...] = ()
    rules: tuple[RuleGroup, ...] = ()
    objective: LinearObjective | FactorObjective | None = None
    measure: Measure | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a finite model needs a name")
        for attr in ("variables", "constraints", "context", "rules"):
            object.__setattr__(self, attr, tuple(getattr(self, attr)))
        names = [variable.name for variable in self.variables]
        if len(set(names)) != len(names):
            raise ValueError("duplicate finite variable names")
        group_names = [group.name for group in self.rules]
        if len(set(group_names)) != len(group_names):
            raise ValueError("duplicate rule group names")
        constraint_names = [constraint.name for constraint in self.constraints]
        if len(set(constraint_names)) != len(constraint_names):
            raise ValueError("duplicate constraint names")
        scoped = {var for c in self.constraints for var in c.variables}
        if self.measure is not None:
            scoped.update(self.measure.variables)
        if self.objective is not None:
            scoped.update(self.objective.variables)
        if isinstance(self.objective, LinearObjective):
            for _, var in self.objective.terms:
                for value in self.domains.get(var, ()):
                    integer(value)
        if missing := scoped - set(names):
            raise ValueError(f"undeclared decision variables: {missing}")
        # Import locally to keep the model/closure dependency acyclic.
        from .closure import validate_rules

        validate_rules(self)

    @property
    def domains(self) -> Mapping[Term, frozenset[Term]]:
        return MappingProxyType(
            {var.name: frozenset(var.domain) for var in self.variables}
        )


class QueryKind(StrEnum):
    SOLVE = "solve"
    ENUMERATE = "enumerate"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    PARTITION = "partition"
    SAMPLE_EXACT = "sample_exact"


@dataclass(frozen=True, slots=True)
class Query:
    kind: QueryKind = QueryKind.SOLVE
    max_nodes: int | None = None
    max_solutions: int | None = None
    time_limit_seconds: float | None = None
    sample_count: int = 1
    seed: int = 0

    def __post_init__(self) -> None:
        import math

        object.__setattr__(self, "kind", QueryKind(self.kind))
        if type(self.sample_count) is not int or self.sample_count < 1:
            raise ValueError("sample_count must be a positive integer")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer")
        if self.sample_count != 1 and self.kind is not QueryKind.SAMPLE_EXACT:
            raise ValueError("sample_count applies only to sampling queries")
        for value in (self.max_nodes, self.max_solutions):
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError("node/solution limits must be positive integers")
        if self.time_limit_seconds is not None and (
            not math.isfinite(self.time_limit_seconds) or self.time_limit_seconds <= 0
        ):
            raise ValueError("time limit must be finite and positive")
        if self.max_solutions is not None and self.kind not in (
            QueryKind.SOLVE,
            QueryKind.ENUMERATE,
        ):
            raise ValueError("solution limits apply only to feasibility/enumeration")


class ResultStatus(StrEnum):
    FEASIBLE = "feasible"
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"
    ZERO_MASS = "zero_mass"


class Termination(StrEnum):
    EXHAUSTED = "exhausted"
    SOLUTION_LIMIT = "solution_limit"
    NODE_LIMIT = "node_limit"
    TIME_LIMIT = "time_limit"
    RESOURCE_LIMIT = "resource_limit"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class Solution:
    assignment: Mapping[Term, Term]
    facts: frozenset[Fact]
    objective_value: int | None = None
    derivations: tuple[Derivation, ...] = ()
    reductions: tuple[DomainRemoval, ...] = ()
    contributions: tuple[ScoreContribution, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "assignment", MappingProxyType(dict(self.assignment)))
        object.__setattr__(self, "facts", frozenset(self.facts))
        for attr in ("derivations", "reductions", "contributions"):
            object.__setattr__(self, attr, tuple(getattr(self, attr)))


def score_solution(
    model: FiniteModel,
    assignment: Mapping[Term, Term],
    facts: frozenset[Fact],
    *,
    reference: bool = False,
) -> tuple[int | None, tuple[ScoreContribution, ...]]:
    """Evaluate once on the complete snapshot, separately from search decisions."""
    if isinstance(model.objective, FactorObjective):
        contributions = model.objective.contributions(
            assignment, facts, reference=reference
        )
        return sum(c.value for c in contributions), contributions
    return (
        None if model.objective is None else model.objective.evaluate(assignment),
        (),
    )


@dataclass(frozen=True, slots=True)
class IncumbentRecord:
    value: int
    explored_nodes: int
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class QueryResult:
    status: ResultStatus
    termination: Termination
    solutions: tuple[Solution, ...] = ()
    explored_nodes: int = 0
    backend: str = "enumeration"
    objective_bound: int | None = None
    arithmetic: str = "integer"
    diagnostic: str = ""
    failed_branches: int = 0
    pruned_branches: int = 0
    constraint_revisions: int = 0
    incumbent_values: tuple[int, ...] = ()
    incumbent_history: tuple[IncumbentRecord, ...] = ()
    elapsed_seconds: float | None = None
    inference: InferenceDistribution | None = None

    @property
    def complete(self) -> bool:
        return self.termination is Termination.EXHAUSTED

    @property
    def incumbent(self) -> Solution | None:
        return self.solutions[0] if self.solutions else None
