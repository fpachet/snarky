"""Rule actions supported by the reference engine."""

from __future__ import annotations

from dataclasses import dataclass

from .expressions import NumericExpression, evaluate_arithmetic
from .facts import Fact
from .premises import Premise
from .substitutions import Substitution
from .terms import Atom, Number, Status, Term, Variable


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


@dataclass(frozen=True, slots=True)
class ForEach:
    """Apply nested actions once per member of a finite collection."""

    variable: Variable
    collection: Term
    actions: tuple[Action, ...]

    def __post_init__(self) -> None:
        actions = tuple(self.actions)
        if not actions:
            raise ValueError("FOR EACH requires at least one nested action")
        object.__setattr__(self, "actions", actions)


@dataclass(frozen=True, slots=True)
class Choice:
    """Instantiate one fact by selecting a correlated source solution."""

    entity: Term
    premises: tuple[Premise, ...]
    status: Term = Status.VRAI
    weight: Term = Number(1)

    def __post_init__(self) -> None:
        premises = tuple(self.premises)
        if not premises:
            raise ValueError("CHOICE requires at least one FROM premise")
        object.__setattr__(self, "premises", premises)

    def instantiate(self, substitution: Substitution) -> Fact:
        return Fact(
            entity=substitution.apply(self.entity),
            status=substitution.apply(self.status),
        )

    def resolved_weight(self, substitution: Substitution) -> float:
        resolved = substitution.apply(self.weight)
        if not isinstance(resolved, Number):
            raise TypeError("CHOICE WEIGHT must resolve to a Number")
        return float(resolved.value)


type Action = AddFact | RemoveFact | Let | Fresh | ForEach | Choice


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


def for_each(
    variable: Variable,
    collection: Term,
    *actions: Action,
) -> ForEach:
    """Construct a finite collection action loop."""

    return ForEach(variable, collection, tuple(actions))


def choose(
    entity: Term,
    *premises: Premise,
    status: Term = Status.VRAI,
    weight: Term | None = None,
) -> Choice:
    """Construct a declarative fact-instantiation choice."""

    return Choice(
        entity,
        tuple(premises),
        status,
        weight if weight is not None else Number(1),
    )
