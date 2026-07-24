"""Finite-domain constraint and SAT interfaces with a reference solver."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from .facts import Fact
from .terms import Atom, Status, Term, Triple

type Assignment = Mapping[str, Term]
type ConstraintEvaluator = Callable[[Assignment], bool]
ASSIGNED = Atom("assigned")


@dataclass(frozen=True, slots=True)
class ConstraintVariable:
    name: str
    domain: tuple[Term, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("constraint variable name cannot be empty")
        domain = tuple(dict.fromkeys(self.domain))
        if not domain:
            raise ValueError(f"variable {self.name!r} has an empty domain")
        object.__setattr__(self, "domain", domain)


@dataclass(frozen=True, slots=True)
class FiniteConstraint:
    """A named relation evaluated once all referenced variables are bound."""

    name: str
    variables: tuple[str, ...]
    evaluator: ConstraintEvaluator

    def __post_init__(self) -> None:
        variables = tuple(self.variables)
        if not variables:
            raise ValueError("a finite constraint needs at least one variable")
        if len(set(variables)) != len(variables):
            raise ValueError("constraint variables must be unique")
        object.__setattr__(self, "variables", variables)

    def ready(self, assignment: Assignment) -> bool:
        return all(variable in assignment for variable in self.variables)

    def accepts(self, assignment: Assignment) -> bool:
        return not self.ready(assignment) or self.evaluator(assignment)


@dataclass(frozen=True, slots=True)
class ConstraintProblem:
    variables: tuple[ConstraintVariable, ...]
    constraints: tuple[FiniteConstraint, ...]

    def __post_init__(self) -> None:
        variables = tuple(self.variables)
        constraints = tuple(self.constraints)
        names = {variable.name for variable in variables}
        if len(names) != len(variables):
            raise ValueError("constraint variable names must be unique")
        for constraint in constraints:
            unknown = set(constraint.variables) - names
            if unknown:
                raise ValueError(
                    f"constraint {constraint.name!r} references unknown "
                    f"variables: {sorted(unknown)!r}"
                )
        object.__setattr__(self, "variables", variables)
        object.__setattr__(self, "constraints", constraints)


@dataclass(frozen=True, slots=True)
class ConstraintSolution:
    bindings: tuple[tuple[str, Term], ...]

    @property
    def assignment(self) -> dict[str, Term]:
        return dict(self.bindings)

    def as_facts(
        self,
        relation: Atom = ASSIGNED,
    ) -> tuple[Fact, ...]:
        """Bridge a solver result back into explainable working-memory facts."""

        return tuple(
            Fact(Triple(Atom(name), relation, value), Status.VRAI)
            for name, value in self.bindings
        )


class ConstraintSolver(Protocol):
    def solve(
        self,
        problem: ConstraintProblem,
        *,
        max_solutions: int = 1,
    ) -> tuple[ConstraintSolution, ...]: ...


class BacktrackingConstraintSolver:
    """Deterministic finite-domain solver used as the portable reference."""

    def solve(
        self,
        problem: ConstraintProblem,
        *,
        max_solutions: int = 1,
    ) -> tuple[ConstraintSolution, ...]:
        if max_solutions < 1:
            raise ValueError("max_solutions must be positive")
        assignment: dict[str, Term] = {}
        solutions: list[ConstraintSolution] = []
        ordered = tuple(
            sorted(
                enumerate(problem.variables),
                key=lambda item: (len(item[1].domain), item[0]),
            )
        )

        def visit(position: int) -> None:
            if len(solutions) >= max_solutions:
                return
            if position == len(ordered):
                solutions.append(
                    ConstraintSolution(
                        tuple(
                            (variable.name, assignment[variable.name])
                            for variable in problem.variables
                        )
                    )
                )
                return
            _, variable = ordered[position]
            for value in variable.domain:
                assignment[variable.name] = value
                if all(
                    constraint.accepts(assignment)
                    for constraint in problem.constraints
                ):
                    visit(position + 1)
                del assignment[variable.name]

        visit(0)
        return tuple(solutions)


@dataclass(frozen=True, slots=True)
class SatLiteral:
    variable: str
    positive: bool = True


@dataclass(frozen=True, slots=True)
class SatClause:
    literals: tuple[SatLiteral, ...]

    def __post_init__(self) -> None:
        literals = tuple(self.literals)
        if not literals:
            raise ValueError("a SAT clause cannot be empty")
        object.__setattr__(self, "literals", literals)


@dataclass(frozen=True, slots=True)
class SatProblem:
    variables: tuple[str, ...]
    clauses: tuple[SatClause, ...]

    def as_constraint_problem(self) -> ConstraintProblem:
        true = Atom("true")
        false = Atom("false")
        variables = tuple(
            ConstraintVariable(name, (false, true)) for name in self.variables
        )

        def clause_constraint(index: int, clause: SatClause) -> FiniteConstraint:
            names = tuple(dict.fromkeys(item.variable for item in clause.literals))

            def accepts(
                assignment: Assignment,
                literals: tuple[SatLiteral, ...] = clause.literals,
            ) -> bool:
                return any(
                    (assignment[literal.variable] == true)
                    is literal.positive
                    for literal in literals
                )

            return FiniteConstraint(f"clause_{index}", names, accepts)

        constraints = tuple(
            clause_constraint(index, clause)
            for index, clause in enumerate(self.clauses, start=1)
        )
        return ConstraintProblem(variables, constraints)
