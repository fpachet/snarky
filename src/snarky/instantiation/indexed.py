"""Index-assisted ordered joins preserving the naïve strategy's semantics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import ComparisonPremise, FactPremise
from ..rules import Rule
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import Term, Triple, is_ground
from .base import Activation, InstantiationMetrics


class IndexedInstantiationStrategy:
    """Use exact indexes to reduce candidates before structural matching.

    Premises are still visited in textual order and candidates retain fact
    insertion order. The strategy therefore changes the amount of work, not
    activation ordering or rule semantics.
    """

    def __init__(self, matcher: PatternMatcher | None = None) -> None:
        self.matcher = matcher or PatternMatcher()
        self.metrics = InstantiationMetrics()

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
    ) -> tuple[Activation, ...]:
        index = _FactIndex(facts)
        self.metrics.index_builds += 1
        self.metrics.indexed_facts += len(facts)
        activations: list[Activation] = []
        self._extend(
            rule,
            index,
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
        index: _FactIndex,
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
                    index,
                    premise_index + 1,
                    substitution,
                    supports,
                    output,
                )
            return
        if not isinstance(premise, FactPremise):
            raise TypeError(f"unsupported premise: {premise!r}")
        candidates = index.candidates(premise, substitution)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            matched = premise.match(fact, substitution, self.matcher)
            if matched is not None:
                self._extend(
                    rule,
                    index,
                    premise_index + 1,
                    matched,
                    (*supports, fact),
                    output,
                )


class _FactIndex:
    """Per-snapshot exact indexes over a fact and its top-level positions."""

    def __init__(self, facts: tuple[Fact, ...]) -> None:
        self.facts = facts
        self.by_entity = _group(facts, lambda fact: fact.entity)
        self.by_status = _group(facts, lambda fact: fact.status)
        triples = tuple(fact for fact in facts if isinstance(fact.entity, Triple))
        self.by_subject = _group(triples, lambda fact: _triple(fact).subject)
        self.by_relation = _group(triples, lambda fact: _triple(fact).relation)
        self.by_object = _group(triples, lambda fact: _triple(fact).object)

    def candidates(
        self,
        premise: FactPremise,
        substitution: Substitution,
    ) -> tuple[Fact, ...]:
        entity = substitution.apply(premise.entity)
        status = substitution.apply(premise.status)
        buckets: list[tuple[Fact, ...]] = []

        if is_ground(entity):
            buckets.append(self.by_entity.get(entity, ()))
        if is_ground(status):
            buckets.append(self.by_status.get(status, ()))
        if isinstance(entity, Triple):
            for part, index in (
                (entity.subject, self.by_subject),
                (entity.relation, self.by_relation),
                (entity.object, self.by_object),
            ):
                if is_ground(part):
                    buckets.append(index.get(part, ()))

        return min(buckets, key=len) if buckets else self.facts


def _group(
    facts: tuple[Fact, ...],
    key: Callable[[Fact], Term],
) -> dict[Term, tuple[Fact, ...]]:
    grouped: defaultdict[Term, list[Fact]] = defaultdict(list)
    for fact in facts:
        grouped[key(fact)].append(fact)
    return {value: tuple(group) for value, group in grouped.items()}


def _triple(fact: Fact) -> Triple:
    entity = fact.entity
    if not isinstance(entity, Triple):
        raise TypeError("expected a triple fact")
    return entity
