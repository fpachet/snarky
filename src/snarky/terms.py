"""Immutable recursive terms used by the inference engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class Atom:
    """An atomic symbolic value."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("an atom name cannot be empty")


@dataclass(frozen=True, slots=True)
class Number:
    """A numeric term kept distinct from symbolic atoms."""

    value: int | float


@dataclass(frozen=True, slots=True)
class Variable:
    """A rule variable, named without its external ``$`` prefix."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a variable name cannot be empty")
        if self.name.startswith("$"):
            raise ValueError("Variable.name must not contain the '$' prefix")


class Status(StrEnum):
    """Built-in explicit statuses.

    Facts may also use arbitrary ground terms as statuses.
    """

    VRAI = "VRAI"
    FAUX = "FAUX"
    INEXISTANT = "INEXISTANT"
    NOMBRE = "NOMBRE"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Triple:
    """A recursive three-place proposition."""

    subject: Term
    relation: Term
    object: Term


type Term = Atom | Number | Variable | Status | Triple
type Proposition = Triple


def is_ground(term: Term) -> bool:
    """Return whether *term* contains no variable at any depth."""

    if isinstance(term, Variable):
        return False
    if isinstance(term, Triple):
        return all(is_ground(part) for part in _triple_parts(term))
    return True


def variables_in(term: Term) -> frozenset[Variable]:
    """Collect all variables recursively contained in *term*."""

    if isinstance(term, Variable):
        return frozenset((term,))
    if isinstance(term, Triple):
        variables: set[Variable] = set()
        for part in _triple_parts(term):
            variables.update(variables_in(part))
        return frozenset(variables)
    return frozenset()


def render_term(term: Term) -> str:
    """Render a term in the small, parser-compatible textual syntax."""

    if isinstance(term, Atom):
        return term.name
    if isinstance(term, Number):
        return str(term.value)
    if isinstance(term, Variable):
        return f"${term.name}"
    if isinstance(term, Status):
        return term.value
    if isinstance(term, Triple):
        subject, relation, object_ = (render_term(part) for part in _triple_parts(term))
        return f"({subject} {relation} {object_})"
    raise TypeError(f"unsupported term: {term!r}")


def _triple_parts(triple: Triple) -> tuple[Term, Term, Term]:
    return triple.subject, triple.relation, triple.object
