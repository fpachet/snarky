"""Oriented recursive pattern matching."""

from __future__ import annotations

from .substitutions import EMPTY_SUBSTITUTION, Substitution
from .terms import FiniteSet, Term, Triple, Variable


class PatternMatcher:
    """Match a rule pattern against a candidate term."""

    def match(
        self,
        pattern: Term,
        candidate: Term,
        substitution: Substitution = EMPTY_SUBSTITUTION,
    ) -> Substitution | None:
        return self._match_general(pattern, candidate, substitution)

    def match_ground(
        self,
        pattern: Term,
        candidate: Term,
        substitution: Substitution = EMPTY_SUBSTITUTION,
    ) -> Substitution | None:
        """Match a known-ground candidate while batching new bindings."""

        pending: dict[Variable, Term] = {}
        if not self._match_ground(
            pattern,
            candidate,
            substitution,
            pending,
        ):
            return None
        return substitution.extend(pending.items())

    def match_ground_pair(
        self,
        first_pattern: Term,
        first_candidate: Term,
        second_pattern: Term,
        second_candidate: Term,
        substitution: Substitution = EMPTY_SUBSTITUTION,
    ) -> Substitution | None:
        """Match two known-ground terms with one temporary binding frame."""

        pending: dict[Variable, Term] = {}
        if not self._match_ground(
            first_pattern,
            first_candidate,
            substitution,
            pending,
        ):
            return None
        if not self._match_ground(
            second_pattern,
            second_candidate,
            substitution,
            pending,
        ):
            return None
        return substitution.extend(pending.items())

    def _match_ground(
        self,
        pattern: Term,
        candidate: Term,
        substitution: Substitution,
        pending: dict[Variable, Term],
    ) -> bool:
        if isinstance(pattern, Variable):
            if pattern in pending:
                return pending[pattern] == candidate
            if pattern in substitution:
                return self._match_ground(
                    substitution.apply(pattern),
                    candidate,
                    substitution,
                    pending,
                )
            pending[pattern] = candidate
            return True
        if isinstance(pattern, Triple):
            if not isinstance(candidate, Triple):
                return False
            return (
                self._match_ground(
                    pattern.subject,
                    candidate.subject,
                    substitution,
                    pending,
                )
                and self._match_ground(
                    pattern.relation,
                    candidate.relation,
                    substitution,
                    pending,
                )
                and self._match_ground(
                    pattern.object,
                    candidate.object,
                    substitution,
                    pending,
                )
            )
        if isinstance(pattern, FiniteSet):
            return pattern == candidate
        return pattern == candidate

    def _match_general(
        self,
        pattern: Term,
        candidate: Term,
        substitution: Substitution,
    ) -> Substitution | None:
        if isinstance(pattern, Variable):
            if pattern in substitution:
                return self._match_general(
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
                matched = self._match_general(
                    pattern_part,
                    candidate_part,
                    current,
                )
                if matched is None:
                    return None
                current = matched
            return current
        if isinstance(pattern, FiniteSet):
            return substitution if pattern == candidate else None
        return substitution if pattern == candidate else None
