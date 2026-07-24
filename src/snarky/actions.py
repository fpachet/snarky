"""Rule actions supported by the reference engine."""

from __future__ import annotations

from dataclasses import dataclass

from .expressions import NumericExpression, evaluate_arithmetic
from .facts import Fact
from .substitutions import Substitution
from .terms import Atom, Status, Term, Variable


@dataclass(frozen=True, slots=True)
class AddFact:
    """Instantiate and add a fact to the store."""

    entity: Term
    status: Term = Status.VRAI

    def instantiate(self, substitution: Substitution) -> Fact:
        return Fact(
            entity=substitution.apply(self.entity),
            status=substitution.apply(self.status),
        )


@dataclass(frozen=True, slots=True)
class RemoveFact:
    """Instantiate and remove a fact from the working memory."""

    entity: Term
    status: Term = Status.VRAI

    def instantiate(self, substitution: Substitution) -> Fact:
        return Fact(
            entity=substitution.apply(self.entity),
            status=substitution.apply(self.status),
        )


@dataclass(frozen=True, slots=True)
class Let:
    """Bind a local variable for the actions that follow in the same rule."""

    variable: Variable
    expression: NumericExpression

    def apply(self, substitution: Substitution) -> Substitution:
        value = evaluate_arithmetic(self.expression, substitution)
        return substitution.bind(self.variable, value)


@dataclass(frozen=True, slots=True)
class Fresh:
    """Bind a new atom for the actions that follow in one activation."""

    variable: Variable
    prefix: str = "fresh"

    def __post_init__(self) -> None:
        if not self.prefix or any(character.isspace() for character in self.prefix):
            raise ValueError("FRESH prefix must be a non-empty atom fragment")

    def apply(
        self,
        substitution: Substitution,
        value: Atom,
    ) -> Substitution:
        return substitution.bind(self.variable, value)


Action = AddFact | RemoveFact | Let | Fresh


def add(entity: Term, status: Term = Status.VRAI) -> AddFact:
    """Public convenience constructor mirroring the documented API."""

    return AddFact(entity, status)


def remove(entity: Term, status: Term = Status.VRAI) -> RemoveFact:
    """Public convenience constructor for removing an instantiated fact."""

    return RemoveFact(entity, status)


def let(variable: Variable, expression: NumericExpression) -> Let:
    """Public convenience constructor for a local arithmetic binding."""

    return Let(variable, expression)


def fresh(variable: Variable, prefix: str = "fresh") -> Fresh:
    """Public convenience constructor for a deterministic fresh atom."""

    return Fresh(variable, prefix)
