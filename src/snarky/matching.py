"""Oriented recursive pattern matching."""

from __future__ import annotations

from .substitutions import EMPTY_SUBSTITUTION, Substitution
from .terms import Term, Triple, Variable


class PatternMatcher:
    """Match a rule pattern against a candidate term."""

    def match(
        self,
        pattern: Term,
        candidate: Term,
        substitution: Substitution = EMPTY_SUBSTITUTION,
    ) -> Substitution | None:
        if isinstance(pattern, Variable):
            if pattern in substitution:
                return self.match(
                    substitution.apply(pattern),
                    candidate,
                    substitution,
                )
            return substitution.bind(pattern, candidate)
        if isinstance(pattern, Triple):
            if not isinstance(candidate, Triple):
                return None
            current = substitution
            for pattern_part, candidate_part in zip(
                (pattern.subject, pattern.relation, pattern.object),
                (candidate.subject, candidate.relation, candidate.object),
                strict=True,
            ):
                matched = self.match(pattern_part, candidate_part, current)
                if matched is None:
                    return None
                current = matched
            return current
        return substitution if pattern == candidate else None
