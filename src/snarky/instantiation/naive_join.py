"""Exhaustive ordered-premise joins used as the semantic oracle."""

from __future__ import annotations

from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import ComparisonPremise, FactPremise
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
