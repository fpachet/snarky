"""Bidirectional recursive unification, separate from forward matching."""

from __future__ import annotations

from .substitutions import EMPTY_SUBSTITUTION, Substitution
from .terms import Term, Triple, Variable, variables_in


class Unifier:
    """Unify two recursive terms with an occurs check."""

    def unify(
        self,
        left: Term,
        right: Term,
        substitution: Substitution = EMPTY_SUBSTITUTION,
    ) -> Substitution | None:
        left = substitution.apply(left)
        right = substitution.apply(right)
        if left == right:
            return substitution
        if isinstance(left, Variable):
            return self._bind(left, right, substitution)
        if isinstance(right, Variable):
            return self._bind(right, left, substitution)
        if isinstance(left, Triple) and isinstance(right, Triple):
            current = substitution
            for left_part, right_part in zip(
                (left.subject, left.relation, left.object),
                (right.subject, right.relation, right.object),
                strict=True,
            ):
                unified = self.unify(left_part, right_part, current)
                if unified is None:
                    return None
                current = unified
            return current
        return None

    @staticmethod
    def _bind(
        variable: Variable,
        term: Term,
        substitution: Substitution,
    ) -> Substitution | None:
        if variable in variables_in(term):
            return None
        return substitution.bind(variable, term)
