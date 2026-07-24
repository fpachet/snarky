"""Exhaustive ordered-premise joins used as the semantic oracle."""

from __future__ import annotations

from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import (
    CollectPremise,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from ..rules import Rule
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import FiniteSet, Term, is_ground
from .base import (
    Activation,
    FactDelta,
    InstantiationMetrics,
    WitnessCache,
    witness_cache_key,
)


class NaiveInstantiationStrategy:
    """Scan every fact and join premises by deterministic backtracking."""

    def __init__(self, matcher: PatternMatcher | None = None) -> None:
        self.matcher = matcher or PatternMatcher()
        self.metrics = InstantiationMetrics()

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        del delta
        activations: list[Activation] = []
        witness_cache: WitnessCache = {}
        self._extend(
            rule,
            facts,
            premise_index=0,
            substitution=EMPTY_SUBSTITUTION,
            supports=(),
            output=activations,
            witness_cache=witness_cache,
        )
        self.metrics.activations_produced += len(activations)
        return tuple(activations)

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        """No-op because the naïve strategy retains no fact index."""

        del removed

    def _extend(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        premise_index: int,
        substitution: Substitution,
        supports: tuple[Fact, ...],
        output: list[Activation],
        witness_cache: WitnessCache,
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
                    witness_cache,
                )
            return
        if isinstance(premise, CollectPremise):
            collection, collection_supports = self._collect_values(
                premise,
                facts,
                substitution,
                witness_cache,
            )
            self._extend(
                rule,
                facts,
                premise_index + 1,
                substitution.bind(premise.target, collection),
                (*supports, *collection_supports),
                output,
                witness_cache,
            )
            return
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            witness = self._first_witness(
                premise.premises,
                facts,
                substitution,
                witness_cache,
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
                    witness_cache,
                )
            return
        if isinstance(premise, (CountPremise, UniquePremise)):
            witnesses = self._all_witnesses(
                premise.premises,
                facts,
                substitution,
                witness_cache,
            )
            if _aggregate_accepts(premise, len(witnesses)):
                self._extend(
                    rule,
                    facts,
                    premise_index + 1,
                    substitution,
                    (*supports, *_aggregate_supports(witnesses)),
                    output,
                    witness_cache,
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
                    witness_cache,
                )

    def _first_witness(
        self,
        premises: tuple[Premise, ...],
        facts: tuple[Fact, ...],
        substitution: Substitution,
        witness_cache: WitnessCache,
    ) -> tuple[Fact, ...] | None:
        key = witness_cache_key(premises, substitution)
        if key in witness_cache:
            self.metrics.witness_cache_hits += 1
            return witness_cache[key]
        self.metrics.witness_cache_misses += 1
        witness = self._first_witness_from(
            premises,
            facts,
            premise_index=0,
            substitution=substitution,
            supports=(),
            witness_cache=witness_cache,
        )
        witness_cache[key] = witness
        return witness

    def _first_witness_from(
        self,
        premises: tuple[Premise, ...],
        facts: tuple[Fact, ...],
        premise_index: int,
        substitution: Substitution,
        supports: tuple[Fact, ...],
        witness_cache: WitnessCache,
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
                witness_cache,
            )
        if isinstance(premise, CollectPremise):
            collection, collection_supports = self._collect_values(
                premise,
                facts,
                substitution,
                witness_cache,
            )
            return self._first_witness_from(
                premises,
                facts,
                premise_index + 1,
                substitution.bind(premise.target, collection),
                (*supports, *collection_supports),
                witness_cache,
            )
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested = self._first_witness(
                premise.premises,
                facts,
                substitution,
                witness_cache,
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
                witness_cache,
            )
        if isinstance(premise, (CountPremise, UniquePremise)):
            witnesses = self._all_witnesses(
                premise.premises,
                facts,
                substitution,
                witness_cache,
            )
            if not _aggregate_accepts(premise, len(witnesses)):
                return None
            return self._first_witness_from(
                premises,
                facts,
                premise_index + 1,
                substitution,
                (*supports, *_aggregate_supports(witnesses)),
                witness_cache,
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
                witness_cache,
            )
            if witness is not None:
                return witness
        return None

    def _all_witnesses(
        self,
        premises: tuple[Premise, ...],
        facts: tuple[Fact, ...],
        substitution: Substitution,
        witness_cache: WitnessCache,
    ) -> tuple[tuple[Fact, ...], ...]:
        output: list[tuple[Fact, ...]] = []
        self._collect_witnesses_from(
            premises,
            facts,
            premise_index=0,
            substitution=substitution,
            supports=(),
            witness_cache=witness_cache,
            output=output,
        )
        return tuple(output)

    def _collect_witnesses_from(
        self,
        premises: tuple[Premise, ...],
        facts: tuple[Fact, ...],
        premise_index: int,
        substitution: Substitution,
        supports: tuple[Fact, ...],
        witness_cache: WitnessCache,
        output: list[tuple[Fact, ...]],
    ) -> None:
        if premise_index == len(premises):
            output.append(supports)
            return
        premise = premises[premise_index]
        if isinstance(premise, ComparisonPremise):
            if premise.evaluate(substitution):
                self._collect_witnesses_from(
                    premises,
                    facts,
                    premise_index + 1,
                    substitution,
                    supports,
                    witness_cache,
                    output,
                )
            return
        if isinstance(premise, CollectPremise):
            collection, collection_supports = self._collect_values(
                premise,
                facts,
                substitution,
                witness_cache,
            )
            self._collect_witnesses_from(
                premises,
                facts,
                premise_index + 1,
                substitution.bind(premise.target, collection),
                (*supports, *collection_supports),
                witness_cache,
                output,
            )
            return
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested = self._first_witness(
                premise.premises,
                facts,
                substitution,
                witness_cache,
            )
            succeeds = nested is not None
            if isinstance(premise, NotExistsPremise):
                succeeds = not succeeds
                nested = ()
            if succeeds:
                self._collect_witnesses_from(
                    premises,
                    facts,
                    premise_index + 1,
                    substitution,
                    (*supports, *(nested or ())),
                    witness_cache,
                    output,
                )
            return
        if isinstance(premise, (CountPremise, UniquePremise)):
            witnesses = self._all_witnesses(
                premise.premises,
                facts,
                substitution,
                witness_cache,
            )
            if _aggregate_accepts(premise, len(witnesses)):
                self._collect_witnesses_from(
                    premises,
                    facts,
                    premise_index + 1,
                    substitution,
                    (*supports, *_aggregate_supports(witnesses)),
                    witness_cache,
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
                self._collect_witnesses_from(
                    premises,
                    facts,
                    premise_index + 1,
                    matched,
                    (*supports, fact),
                    witness_cache,
                    output,
                )

    def _collect_values(
        self,
        premise: CollectPremise,
        facts: tuple[Fact, ...],
        substitution: Substitution,
        witness_cache: WitnessCache,
    ) -> tuple[FiniteSet, tuple[Fact, ...]]:
        projected: list[tuple[Term, tuple[Fact, ...]]] = []
        self._collect_projected_from(
            premise.premises,
            premise.projection,
            facts,
            premise_index=0,
            substitution=substitution,
            supports=(),
            witness_cache=witness_cache,
            output=projected,
        )
        values = FiniteSet(tuple(dict.fromkeys(value for value, _ in projected)))
        supports = tuple(
            dict.fromkeys(
                fact
                for _, witness_supports in projected
                for fact in witness_supports
            )
        )
        return values, supports

    def _collect_projected_from(
        self,
        premises: tuple[Premise, ...],
        projection: Term,
        facts: tuple[Fact, ...],
        premise_index: int,
        substitution: Substitution,
        supports: tuple[Fact, ...],
        witness_cache: WitnessCache,
        output: list[tuple[Term, tuple[Fact, ...]]],
    ) -> None:
        if premise_index == len(premises):
            value = substitution.apply(projection)
            if not is_ground(value):
                raise ValueError("COLLECT projection must be ground")
            output.append((value, supports))
            return
        premise = premises[premise_index]
        if isinstance(premise, ComparisonPremise):
            if premise.evaluate(substitution):
                self._collect_projected_from(
                    premises,
                    projection,
                    facts,
                    premise_index + 1,
                    substitution,
                    supports,
                    witness_cache,
                    output,
                )
            return
        if isinstance(premise, CollectPremise):
            collection, collection_supports = self._collect_values(
                premise,
                facts,
                substitution,
                witness_cache,
            )
            self._collect_projected_from(
                premises,
                projection,
                facts,
                premise_index + 1,
                substitution.bind(premise.target, collection),
                (*supports, *collection_supports),
                witness_cache,
                output,
            )
            return
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested = self._first_witness(
                premise.premises,
                facts,
                substitution,
                witness_cache,
            )
            succeeds = nested is not None
            if isinstance(premise, NotExistsPremise):
                succeeds = not succeeds
                nested = ()
            if succeeds:
                self._collect_projected_from(
                    premises,
                    projection,
                    facts,
                    premise_index + 1,
                    substitution,
                    (*supports, *(nested or ())),
                    witness_cache,
                    output,
                )
            return
        if isinstance(premise, (CountPremise, UniquePremise)):
            witnesses = self._all_witnesses(
                premise.premises,
                facts,
                substitution,
                witness_cache,
            )
            if _aggregate_accepts(premise, len(witnesses)):
                self._collect_projected_from(
                    premises,
                    projection,
                    facts,
                    premise_index + 1,
                    substitution,
                    (*supports, *_aggregate_supports(witnesses)),
                    witness_cache,
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
                self._collect_projected_from(
                    premises,
                    projection,
                    facts,
                    premise_index + 1,
                    matched,
                    (*supports, fact),
                    witness_cache,
                    output,
                )


def _aggregate_accepts(
    premise: CountPremise | UniquePremise,
    count: int,
) -> bool:
    if isinstance(premise, UniquePremise):
        return count == 1
    return premise.accepts(count)


def _aggregate_supports(
    witnesses: tuple[tuple[Fact, ...], ...],
) -> tuple[Fact, ...]:
    return tuple(
        dict.fromkeys(
            fact
            for witness in witnesses
            for fact in witness
        )
    )
