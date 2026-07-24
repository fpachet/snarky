"""Immutable recursive terms used by the inference engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class _PreHashed:
    """Private slot shared by immutable values with a structural hash."""

    __slots__ = ("_hash",)

    _hash: int


@dataclass(frozen=True, slots=True)
class Atom(_PreHashed):
    """An atomic symbolic value."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("an atom name cannot be empty")
        object.__setattr__(self, "_hash", hash((self.name,)))

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(self) -> tuple[type[Atom], tuple[str]]:
        return Atom, (self.name,)


@dataclass(frozen=True, slots=True)
class Number(_PreHashed):
    """A numeric term kept distinct from symbolic atoms."""

    value: int | float

    def __post_init__(self) -> None:
        object.__setattr__(self, "_hash", hash((self.value,)))

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(
        self,
    ) -> tuple[type[Number], tuple[int | float]]:
        return Number, (self.value,)


@dataclass(frozen=True, slots=True)
class Variable(_PreHashed):
    """A rule variable, named without its external ``$`` prefix."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a variable name cannot be empty")
        if self.name.startswith("$"):
            raise ValueError("Variable.name must not contain the '$' prefix")
        object.__setattr__(self, "_hash", hash((self.name,)))

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(self) -> tuple[type[Variable], tuple[str]]:
        return Variable, (self.name,)


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
class Triple(_PreHashed):
    """A recursive three-place proposition."""

    subject: Term
    relation: Term
    object: Term

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_hash",
            hash((self.subject, self.relation, self.object)),
        )

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(
        self,
    ) -> tuple[type[Triple], tuple[Term, Term, Term]]:
        return Triple, (self.subject, self.relation, self.object)


@dataclass(frozen=True, slots=True, eq=False)
class FiniteSet(_PreHashed):
    """An immutable finite set with stable presentation order."""

    elements: tuple[Term, ...]

    def __post_init__(self) -> None:
        unique = tuple(dict.fromkeys(self.elements))
        object.__setattr__(self, "elements", unique)
        object.__setattr__(self, "_hash", hash(frozenset(unique)))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FiniteSet)
            and frozenset(self.elements) == frozenset(other.elements)
        )

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(self) -> tuple[type[FiniteSet], tuple[tuple[Term, ...]]]:
        return FiniteSet, (self.elements,)


@dataclass(frozen=True, slots=True)
class FiniteSequence(_PreHashed):
    """An immutable ordered finite sequence that preserves duplicates."""

    elements: tuple[Term, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "elements", tuple(self.elements))
        object.__setattr__(self, "_hash", hash(self.elements))

    def __hash__(self) -> int:
        return self._hash

    def __reduce__(
        self,
    ) -> tuple[type[FiniteSequence], tuple[tuple[Term, ...]]]:
        return FiniteSequence, (self.elements,)


type Term = (
    Atom
    | Number
    | Variable
    | Status
    | Triple
    | FiniteSet
    | FiniteSequence
)
type Proposition = Triple


def is_ground(term: Term) -> bool:
    """Return whether *term* contains no variable at any depth."""

    if isinstance(term, Variable):
        return False
    if isinstance(term, Triple):
        return all(is_ground(part) for part in _triple_parts(term))
    if isinstance(term, (FiniteSet, FiniteSequence)):
        return all(is_ground(element) for element in term.elements)
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
    if isinstance(term, (FiniteSet, FiniteSequence)):
        collection_variables: set[Variable] = set()
        for element in term.elements:
            collection_variables.update(variables_in(element))
        return frozenset(collection_variables)
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
    if isinstance(term, FiniteSet):
        return f"[{' '.join(render_term(element) for element in term.elements)}]"
    if isinstance(term, FiniteSequence):
        return (
            f"SEQ[{' '.join(render_term(element) for element in term.elements)}]"
        )
    raise TypeError(f"unsupported term: {term!r}")


def _triple_parts(triple: Triple) -> tuple[Term, Term, Term]:
    return triple.subject, triple.relation, triple.object
