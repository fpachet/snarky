"""Monotone rule actions supported by the reference engine."""

from __future__ import annotations

from dataclasses import dataclass

from .expressions import NumericExpression, evaluate_arithmetic
from .facts import Fact
from .substitutions import Substitution
from .terms import Status, Term, Variable


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
class Let:
    """Bind a local variable for the actions that follow in the same rule."""

    variable: Variable
    expression: NumericExpression

    def apply(self, substitution: Substitution) -> Substitution:
        value = evaluate_arithmetic(self.expression, substitution)
        return substitution.bind(self.variable, value)


Action = AddFact | Let


def add(entity: Term, status: Term = Status.VRAI) -> AddFact:
    """Public convenience constructor mirroring the documented API."""

    return AddFact(entity, status)


def let(variable: Variable, expression: NumericExpression) -> Let:
    """Public convenience constructor for a local arithmetic binding."""

    return Let(variable, expression)
