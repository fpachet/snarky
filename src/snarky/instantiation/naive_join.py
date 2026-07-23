"""Exhaustive ordered-premise joins used as the semantic oracle."""

from __future__ import annotations

from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import (
    ComparisonPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
)
from ..rules import Rule
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from .base import Activation, InstantiationMetrics


class NaiveInstantiationStrategy:
    """Scan every fact and join premises by deterministic backtracking."""

    def __init__(self, matcher: PatternMatcher | None = None) -> None:
        self.matcher = matcher or PatternMatcher()
        self.metrics = InstantiationMetrics()

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        del delta
        activations: list[Activation] = []
        self._extend(
            rule,
            facts,
            premise_index=0,
            substitution=EMPTY_SUBSTITUTION,
            supports=(),
            output=activations,
        )
        self.metrics.activations_produced += len(activations)
        return tuple(activations)

    def invalidate(self) -> None:
        """No-op because the naïve strategy retains no fact index."""

    def _extend(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        premise_index: int,
        substitution: Substitution,
        supports: tuple[Fact, ...],
        output: list[Activation],
    ) -> None:
        if premise_index == len(rule.premises):
            output.append(Activation(substitution, supports))
            return
        premise = rule.premises[premise_index]
        if isinstance(premise, ComparisonPremise):
            if premise.evaluate(substitution):
                self._extend(
                    rule,
                    facts,
                    premise_index + 1,
                    substitution,
                    supports,
                    output,
                )
            return
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            witness = self._first_witness(
                premise.premises,
                facts,
                substitution,
            )
            succeeds = witness is not None
            if isinstance(premise, NotExistsPremise):
                succeeds = not succeeds
                witness = ()
            if succeeds:
                self._extend(
                    rule,
                    facts,
                    premise_index + 1,
                    substitution,
                    (*supports, *(witness or ())),
                    output,
                )
            return
        if not isinstance(premise, FactPremise):
            raise TypeError(f"unsupported premise: {premise!r}")
        for fact in facts:
            self.metrics.candidate_facts += 1
            self.metrics.match_attempts += 1
            matched = premise.match(fact, substitution, self.matcher)
            if matched is not None:
                self._extend(
                    rule,
                    facts,
                    premise_index + 1,
                    matched,
                    (*supports, fact),
                    output,
                )

    def _first_witness(
        self,
        premises: tuple[Premise, ...],
        facts: tuple[Fact, ...],
        substitution: Substitution,
    ) -> tuple[Fact, ...] | None:
        return self._first_witness_from(
            premises,
            facts,
            premise_index=0,
            substitution=substitution,
            supports=(),
        )

    def _first_witness_from(
        self,
        premises: tuple[Premise, ...],
        facts: tuple[Fact, ...],
        premise_index: int,
        substitution: Substitution,
        supports: tuple[Fact, ...],
    ) -> tuple[Fact, ...] | None:
        if premise_index == len(premises):
            return supports
        premise = premises[premise_index]
        if isinstance(premise, ComparisonPremise):
            if not premise.evaluate(substitution):
                return None
            return self._first_witness_from(
                premises,
                facts,
                premise_index + 1,
                substitution,
                supports,
            )
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested = self._first_witness(
                premise.premises,
                facts,
                substitution,
            )
            succeeds = nested is not None
            if isinstance(premise, NotExistsPremise):
                succeeds = not succeeds
                nested = ()
            if not succeeds:
                return None
            return self._first_witness_from(
                premises,
                facts,
                premise_index + 1,
                substitution,
                (*supports, *(nested or ())),
            )
        if not isinstance(premise, FactPremise):
            raise TypeError(f"unsupported premise: {premise!r}")
        for fact in facts:
            self.metrics.candidate_facts += 1
            self.metrics.match_attempts += 1
            matched = premise.match(fact, substitution, self.matcher)
            if matched is None:
                continue
            witness = self._first_witness_from(
                premises,
                facts,
                premise_index + 1,
                matched,
                (*supports, fact),
            )
            if witness is not None:
                return witness
        return None
