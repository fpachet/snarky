"""Immutable substitutions and their recursive application."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping

from .terms import Term, Triple, Variable


class Substitution(Mapping[Variable, Term]):
    """An immutable variable-to-term mapping.

    Bindings retain insertion order for deterministic activation and proof
    rendering. Variable equality, rather than names alone, defines identity.
    """

    __slots__ = ("_bindings",)

    def __init__(
        self,
        bindings: Mapping[Variable, Term] | Iterable[tuple[Variable, Term]] = (),
    ) -> None:
        items = bindings.items() if isinstance(bindings, Mapping) else bindings
        unique: dict[Variable, Term] = {}
        for variable, term in items:
            if not isinstance(variable, Variable):
                raise TypeError("substitution keys must be Variable instances")
            if variable in unique and unique[variable] != term:
                raise ValueError(f"conflicting binding for ${variable.name}")
            unique[variable] = term
        self._bindings = tuple(unique.items())

    def __getitem__(self, key: Variable) -> Term:
        for variable, term in self._bindings:
            if variable == key:
                return term
        raise KeyError(key)

    def __iter__(self) -> Iterator[Variable]:
        return (variable for variable, _ in self._bindings)

    def __len__(self) -> int:
        return len(self._bindings)

    def __hash__(self) -> int:
        return hash(frozenset(self._bindings))

    def __repr__(self) -> str:
        content = ", ".join(
            f"${variable.name}={term!r}" for variable, term in self._bindings
        )
        return f"Substitution({content})"

    @property
    def key(self) -> tuple[tuple[str, Term], ...]:
        """Return a stable, name-sorted representation for activation keys."""

        return tuple(
            sorted(
                (
                    (variable.name, self.apply(term))
                    for variable, term in self._bindings
                ),
                key=lambda item: item[0],
            )
        )

    def bind(self, variable: Variable, term: Term) -> Substitution:
        """Return a new substitution containing one additional binding."""

        if variable in self:
            if self.apply(variable) != self.apply(term):
                raise ValueError(f"conflicting binding for ${variable.name}")
            return self
        return Substitution((*self._bindings, (variable, term)))

    def apply(self, term: Term) -> Term:
        """Apply this substitution recursively to *term*."""

        return self._apply(term, frozenset())

    def _apply(self, term: Term, seen: frozenset[Variable]) -> Term:
        if isinstance(term, Variable) and term in self:
            if term in seen:
                raise ValueError(f"cyclic substitution through ${term.name}")
            return self._apply(self[term], seen | {term})
        if isinstance(term, Triple):
            return Triple(
                self._apply(term.subject, seen),
                self._apply(term.relation, seen),
                self._apply(term.object, seen),
            )
        return term


EMPTY_SUBSTITUTION = Substitution()
