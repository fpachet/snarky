"""Persistent index-assisted joins and semi-naïve instantiation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

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
from ..terms import Term, Triple, is_ground
from .base import (
    Activation,
    InstantiationMetrics,
    WitnessCache,
    witness_cache_key,
)


class IndexedInstantiationStrategy:
    """Use persistent exact indexes while preserving exhaustive joins.

    One index is shared by the rules evaluated over the same working-memory
    snapshot. Premises and candidates keep their naïve insertion order, so
    this strategy changes work but not observable results.
    """

    def __init__(self, matcher: PatternMatcher | None = None) -> None:
        self.matcher = matcher or PatternMatcher()
        self.metrics = InstantiationMetrics()
        self._index: FactIndex | None = None
        self._pending_removed: set[Fact] = set()

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        index = self._index_for(rule, facts, delta)
        activations = self._join(rule, index)
        self.metrics.activations_produced += len(activations)
        return tuple(activations)

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        """Apply removals to the shared index, or discard it if unspecified."""

        if self._index is None:
            return
        if not removed:
            self._index = None
            self._pending_removed.clear()
            return
        self._pending_removed.update(removed)

    def _index_for(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None,
    ) -> FactIndex:
        del rule
        index = self._index
        if index is None:
            index = FactIndex(facts)
            self._index = index
            self._pending_removed.clear()
            self.metrics.index_builds += 1
            self.metrics.indexed_facts += len(facts)
            return index
        if self._pending_removed:
            removed = frozenset(self._pending_removed)
            self.metrics.index_removals += index.remove(removed)
            self._pending_removed.clear()

        if delta is None:
            indexed = tuple(index.facts)
            if facts[: len(indexed)] == indexed:
                self.metrics.indexed_facts += index.extend(
                    facts[len(indexed) :]
                )
            elif indexed != facts:
                index = FactIndex(facts)
                self._index = index
                self.metrics.index_builds += 1
                self.metrics.indexed_facts += len(facts)
            return index

        if delta:
            self.metrics.indexed_facts += index.extend(delta)
        if tuple(index.facts) != facts:
            index = FactIndex(facts)
            self._index = index
            self.metrics.index_builds += 1
            self.metrics.indexed_facts += len(facts)
        return index

    def _join(
        self,
        rule: Rule,
        index: FactIndex,
    ) -> list[Activation]:
        activations: list[Activation] = []
        witness_cache: WitnessCache = {}
        self._extend(
            rule,
            index,
            premise_index=0,
            substitution=EMPTY_SUBSTITUTION,
            supports=(),
            output=activations,
            witness_cache=witness_cache,
        )
        return activations

    def _extend(
        self,
        rule: Rule,
        index: FactIndex,
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
                    index,
                    premise_index + 1,
                    substitution,
                    supports,
                    output,
                    witness_cache,
                )
            return
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            witness = self._first_witness(
                premise.premises,
                index,
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
                    index,
                    premise_index + 1,
                    substitution,
                    (*supports, *(witness or ())),
                    output,
                    witness_cache,
                )
            return
        if not isinstance(premise, FactPremise):
            raise TypeError(f"unsupported premise: {premise!r}")
        candidates: Sequence[Fact] = index.candidates(premise, substitution)
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
                    witness_cache,
                )

    def _first_witness(
        self,
        premises: tuple[Premise, ...],
        index: FactIndex,
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
            index,
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
        index: FactIndex,
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
                index,
                premise_index + 1,
                substitution,
                supports,
                witness_cache,
            )
        if isinstance(premise, (ExistsPremise, NotExistsPremise)):
            nested = self._first_witness(
                premise.premises,
                index,
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
                index,
                premise_index + 1,
                substitution,
                (*supports, *(nested or ())),
                witness_cache,
            )
        if not isinstance(premise, FactPremise):
            raise TypeError(f"unsupported premise: {premise!r}")
        candidates = index.candidates(premise, substitution)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            matched = premise.match(fact, substitution, self.matcher)
            if matched is None:
                continue
            witness = self._first_witness_from(
                premises,
                index,
                premise_index + 1,
                matched,
                (*supports, fact),
                witness_cache,
            )
            if witness is not None:
                return witness
        return None


class SemiNaiveInstantiationStrategy(IndexedInstantiationStrategy):
    """Enumerate only joins containing a fact new to the current rule."""

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        index = self._index_for(rule, facts, delta)
        has_existential = any(
            isinstance(premise, (ExistsPremise, NotExistsPremise))
            for premise in rule.premises
        )
        if delta is None or (delta and has_existential):
            activations = self._join(rule, index)
        elif not delta:
            activations = []
        else:
            fact_premises = tuple(
                position
                for position, premise in enumerate(rule.premises)
                if isinstance(premise, FactPremise)
            )
            premise_groups = self._premise_groups(rule)
            delta_start = len(index) - len(delta)
            unique: dict[
                tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
                Activation,
            ] = {}
            for anchor in fact_premises:
                for activation in self._join_delta_variant(
                    rule,
                    index,
                    premise_groups,
                    anchor,
                    delta_start,
                ):
                    key = activation.substitution.key, activation.premise_facts
                    unique.setdefault(key, activation)
            activations = sorted(
                unique.values(),
                key=index.activation_order,
            )
        self.metrics.activations_produced += len(activations)
        return tuple(activations)

    def _join_delta_variant(
        self,
        rule: Rule,
        index: FactIndex,
        premise_groups: tuple[tuple[tuple[int, ...], int | None], ...],
        anchor: int,
        delta_start: int,
    ) -> list[Activation]:
        """Join from the delta premise, then restore textual support order."""

        activations: list[Activation] = []
        self._extend_delta_variant(
            rule,
            index,
            premise_groups=premise_groups,
            group_index=0,
            remaining=premise_groups[0][0],
            anchor=anchor,
            delta_start=delta_start,
            substitution=EMPTY_SUBSTITUTION,
            supports=(),
            output=activations,
        )
        return activations

    def _extend_delta_variant(
        self,
        rule: Rule,
        index: FactIndex,
        premise_groups: tuple[tuple[tuple[int, ...], int | None], ...],
        group_index: int,
        remaining: tuple[int, ...],
        anchor: int,
        delta_start: int,
        substitution: Substitution,
        supports: tuple[tuple[int, Fact], ...],
        output: list[Activation],
    ) -> None:
        if group_index == len(premise_groups):
            ordered_supports = tuple(
                fact for _, fact in sorted(supports, key=lambda item: item[0])
            )
            output.append(Activation(substitution, ordered_supports))
            return

        if not remaining:
            comparison_index = premise_groups[group_index][1]
            if comparison_index is not None:
                comparison = rule.premises[comparison_index]
                if not isinstance(comparison, ComparisonPremise):
                    raise TypeError(f"expected comparison, got: {comparison!r}")
                if not comparison.evaluate(substitution):
                    return
            next_group = group_index + 1
            next_remaining = (
                premise_groups[next_group][0]
                if next_group < len(premise_groups)
                else ()
            )
            self._extend_delta_variant(
                rule,
                index,
                premise_groups,
                next_group,
                next_remaining,
                anchor,
                delta_start,
                substitution,
                supports,
                output,
            )
            return

        choices: list[tuple[int, int, Sequence[Fact], FactPremise]] = []
        group_positions = premise_groups[group_index][0]
        group_started = len(remaining) < len(group_positions)
        positions = (
            (anchor,) if anchor in remaining and not group_started else remaining
        )
        for premise_index in positions:
            premise = rule.premises[premise_index]
            if not isinstance(premise, FactPremise):
                raise TypeError(f"expected fact premise, got: {premise!r}")
            if premise_index == anchor:
                candidates = index.candidates_partitioned(
                    premise,
                    substitution,
                    delta_start,
                    new=True,
                )
            elif premise_index < anchor:
                candidates = index.candidates_partitioned(
                    premise,
                    substitution,
                    delta_start,
                    new=False,
                )
            else:
                candidates = index.candidates(premise, substitution)
            choices.append((len(candidates), premise_index, candidates, premise))
        _, premise_index, candidates, premise = min(
            choices,
            key=lambda choice: (choice[0], choice[1]),
        )
        next_remaining = tuple(item for item in remaining if item != premise_index)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            matched = premise.match(fact, substitution, self.matcher)
            if matched is not None:
                self._extend_delta_variant(
                    rule,
                    index,
                    premise_groups,
                    group_index,
                    next_remaining,
                    anchor,
                    delta_start,
                    matched,
                    (*supports, (premise_index, fact)),
                    output,
                )

    @staticmethod
    def _premise_groups(
        rule: Rule,
    ) -> tuple[tuple[tuple[int, ...], int | None], ...]:
        groups: list[tuple[tuple[int, ...], int | None]] = []
        facts: list[int] = []
        for position, premise in enumerate(rule.premises):
            if isinstance(premise, FactPremise):
                facts.append(position)
            elif isinstance(premise, ComparisonPremise):
                groups.append((tuple(facts), position))
                facts = []
            else:
                raise TypeError(f"unsupported premise: {premise!r}")
        groups.append((tuple(facts), None))
        return tuple(groups)


class FactIndex:
    """Incrementally maintained indexes over facts and top-level positions."""

    def __init__(self, facts: Sequence[Fact] = ()) -> None:
        self.facts: list[Fact] = []
        self.ranks: dict[Fact, int] = {}
        self.by_entity: defaultdict[Term, list[Fact]] = defaultdict(list)
        self.by_status: defaultdict[Term, list[Fact]] = defaultdict(list)
        self.by_subject: defaultdict[Term, list[Fact]] = defaultdict(list)
        self.by_relation: defaultdict[Term, list[Fact]] = defaultdict(list)
        self.by_object: defaultdict[Term, list[Fact]] = defaultdict(list)
        self.extend(facts)

    def extend(self, facts: Sequence[Fact]) -> int:
        added = 0
        for fact in facts:
            if fact in self.ranks:
                continue
            self.ranks[fact] = len(self.facts)
            self.facts.append(fact)
            self.by_entity[fact.entity].append(fact)
            self.by_status[fact.status].append(fact)
            if isinstance(fact.entity, Triple):
                self.by_subject[fact.entity.subject].append(fact)
                self.by_relation[fact.entity.relation].append(fact)
                self.by_object[fact.entity.object].append(fact)
            added += 1
        return added

    def remove(self, facts: frozenset[Fact]) -> int:
        """Remove facts while preserving the insertion order of survivors."""

        present = facts.intersection(self.ranks)
        if not present:
            return 0
        for fact in present:
            self._remove_from_bucket(self.by_entity, fact.entity, fact)
            self._remove_from_bucket(self.by_status, fact.status, fact)
            if isinstance(fact.entity, Triple):
                self._remove_from_bucket(
                    self.by_subject,
                    fact.entity.subject,
                    fact,
                )
                self._remove_from_bucket(
                    self.by_relation,
                    fact.entity.relation,
                    fact,
                )
                self._remove_from_bucket(
                    self.by_object,
                    fact.entity.object,
                    fact,
                )
        self.facts[:] = [fact for fact in self.facts if fact not in present]
        self.ranks = {fact: rank for rank, fact in enumerate(self.facts)}
        return len(present)

    @staticmethod
    def _remove_from_bucket(
        buckets: defaultdict[Term, list[Fact]],
        key: Term,
        fact: Fact,
    ) -> None:
        bucket = buckets[key]
        bucket.remove(fact)
        if not bucket:
            del buckets[key]

    def candidates(
        self,
        premise: FactPremise,
        substitution: Substitution,
    ) -> Sequence[Fact]:
        entity = substitution.apply(premise.entity)
        status = substitution.apply(premise.status)
        buckets: list[Sequence[Fact]] = []

        if is_ground(entity):
            buckets.append(self.by_entity.get(entity, ()))
        if is_ground(status):
            buckets.append(self.by_status.get(status, ()))
        if isinstance(entity, Triple):
            for part, part_index in (
                (entity.subject, self.by_subject),
                (entity.relation, self.by_relation),
                (entity.object, self.by_object),
            ):
                if is_ground(part):
                    buckets.append(part_index.get(part, ()))

        return min(buckets, key=len) if buckets else self.facts

    def candidates_partitioned(
        self,
        premise: FactPremise,
        substitution: Substitution,
        delta_start: int,
        *,
        new: bool,
    ) -> Sequence[Fact]:
        candidates = self.candidates(premise, substitution)
        split = self._rank_split(candidates, delta_start)
        return candidates[split:] if new else candidates[:split]

    def _rank_split(self, facts: Sequence[Fact], rank: int) -> int:
        low = 0
        high = len(facts)
        while low < high:
            middle = (low + high) // 2
            if self.ranks[facts[middle]] < rank:
                low = middle + 1
            else:
                high = middle
        return low

    def activation_order(self, activation: Activation) -> tuple[int, ...]:
        return tuple(self.ranks[fact] for fact in activation.premise_facts)

    def __len__(self) -> int:
        return len(self.facts)
