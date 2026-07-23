"""Immutable substitutions and their recursive application."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping

from .terms import Term, Triple, Variable


class Substitution(Mapping[Variable, Term]):
    """An immutable variable-to-term mapping.

    Bindings retain insertion order for deterministic activation and proof
    rendering. Variable equality, rather than names alone, defines identity.
    """

    __slots__ = ("_bindings", "_lookup")

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
        self._lookup = unique

    def __getitem__(self, key: Variable) -> Term:
        return self._lookup[key]

    def __contains__(self, key: object) -> bool:
        """Use the immutable lookup table instead of Mapping's linear scan."""

        return key in self._lookup

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
        return self.extend(((variable, term),))

    def extend(
        self,
        bindings: Iterable[tuple[Variable, Term]],
    ) -> Substitution:
        """Return one substitution containing a batch of new bindings."""

        lookup = self._lookup.copy()
        ordered = list(self._bindings)
        changed = False
        for variable, term in bindings:
            if not isinstance(variable, Variable):
                raise TypeError("substitution keys must be Variable instances")
            previous = lookup.get(variable)
            if previous is not None:
                if previous != term:
                    raise ValueError(f"conflicting binding for ${variable.name}")
                continue
            lookup[variable] = term
            ordered.append((variable, term))
            changed = True
        if not changed:
            return self
        substitution = object.__new__(Substitution)
        substitution._bindings = tuple(ordered)
        substitution._lookup = lookup
        return substitution

    def apply(self, term: Term) -> Term:
        """Apply this substitution recursively to *term*."""

        if not isinstance(term, (Variable, Triple)):
            return term
        return self._apply(term, set())

    def _apply(self, term: Term, seen: set[Variable]) -> Term:
        if isinstance(term, Variable) and term in self._lookup:
            if term in seen:
                raise ValueError(f"cyclic substitution through ${term.name}")
            seen.add(term)
            resolved = self._apply(self._lookup[term], seen)
            seen.remove(term)
            return resolved
        if isinstance(term, Triple):
            return Triple(
                self._apply(term.subject, seen),
                self._apply(term.relation, seen),
                self._apply(term.object, seen),
            )
        return term


EMPTY_SUBSTITUTION = Substitution()
