"""Persistent index-assisted joins and semi-naïve instantiation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypeVar

from ..computed import ComputedPremise
from ..facts import Fact
from ..matching import PatternMatcher
from ..premises import (
    BindPremise,
    CollectPremise,
    CombinationsPremise,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from ..rules import Rule
from ..substitutions import (
    EMPTY_SUBSTITUTION,
    BindingFrame,
    Substitution,
    TermBindings,
)
from ..terms import FiniteSet, Term, Triple, Variable, is_ground
from .base import (
    Activation,
    FactDelta,
    InstantiationMetrics,
    WitnessCache,
    WitnessCacheKey,
    witness_cache_key,
)
from .compiled import (
    CompiledAggregatePremise,
    CompiledBindPremise,
    CompiledBlock,
    CompiledCollectPremise,
    CompiledCombinationsPremise,
    CompiledComparisonPremise,
    CompiledExistentialPremise,
    CompiledFactPremise,
    all_fact_plans,
    compile_fact_premise,
    compile_rule,
    negative_fact_plans,
    simple_fact_plan,
)

IndexKeyT = TypeVar("IndexKeyT")
type WatchToken = tuple[str, object]


def _apply_compiled_binding(
    premise: BindPremise | ComputedPremise,
    frame: BindingFrame,
) -> bool:
    if isinstance(premise, BindPremise):
        bound_value = frame.apply(premise.value)
        return is_ground(bound_value) and frame.bind_ground(
            premise.target,
            bound_value,
        )
    accepted, computed_value = premise.resolve(frame)
    if not accepted:
        return False
    if premise.target is None:
        return True
    assert computed_value is not None
    return frame.bind_ground(premise.target, computed_value)


@dataclass(frozen=True, slots=True)
class _RuleMemory:
    activations: tuple[Activation, ...]


@dataclass(frozen=True, slots=True)
class _PartialState:
    substitution: Substitution
    supports: tuple[Fact, ...]


class IndexedInstantiationStrategy:
    """Use persistent exact indexes while preserving exhaustive joins.

    One index is shared by the rules evaluated over the same working-memory
    snapshot. Premises and candidates keep their naïve insertion order, so
    this strategy changes work but not observable results.
    """

    def __init__(
        self,
        matcher: PatternMatcher | None = None,
        *,
        partial_join_limit: int = 2_048,
    ) -> None:
        if partial_join_limit < 1:
            raise ValueError("partial_join_limit must be positive")
        self.matcher = matcher or PatternMatcher()
        self.partial_join_limit = partial_join_limit
        self.metrics = InstantiationMetrics()
        self._index: FactIndex | None = None
        self._pending_removed: set[Fact] = set()
        self._witness_cache: WitnessCache = {}
        self._query_blocks: dict[WitnessCacheKey, CompiledBlock] = {}
        self._negative_watchers: defaultdict[
            WatchToken, set[WitnessCacheKey]
        ] = defaultdict(set)
        self._creation_watchers: defaultdict[
            WatchToken, set[WitnessCacheKey]
        ] = defaultdict(set)
        self._support_watchers: defaultdict[
            Fact, set[WitnessCacheKey]
        ] = defaultdict(set)
        self._query_registrations: dict[
            WitnessCacheKey,
            tuple[
                frozenset[WatchToken],
                frozenset[WatchToken],
                tuple[Fact, ...],
            ],
        ] = {}
        self._query_counts: dict[WitnessCacheKey, int] = {}
        self._simple_query_facts: dict[
            WitnessCacheKey, tuple[Fact, ...]
        ] = {}
        self._query_aggregate_supports: dict[
            WitnessCacheKey, tuple[Fact, ...]
        ] = {}
        self._rule_memories: dict[Rule, _RuleMemory] = {}
        self._positive_join_memories: dict[
            Rule, tuple[tuple[_PartialState, ...], ...]
        ] = {}
        self._partial_memory_disabled: set[Rule] = set()
        self._processed_revision = 0

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        changes = _normalize_delta(delta)
        index = self._index_for(rule, facts, changes)
        positive_rule = self._is_positive_compiled_rule(rule)
        if (
            positive_rule
            and rule not in self._partial_memory_disabled
            and rule not in self._positive_join_memories
            and not self._should_materialize_positive(rule, index)
        ):
            self._partial_memory_disabled.add(rule)
            self.metrics.partial_join_bypasses += 1
        if positive_rule and rule not in self._partial_memory_disabled:
            result = self._instantiate_positive_memory(
                rule,
                index,
                changes,
            )
            if result is not None:
                self.metrics.activations_produced += len(result)
                self._rule_memories[rule] = _RuleMemory(result)
                return result
        reused = self._reuse_rule_memory(rule, changes)
        if reused is not None:
            self.metrics.activations_produced += len(reused)
            return reused
        activations = self._join(rule, index)
        self.metrics.activations_produced += len(activations)
        result = tuple(activations)
        self._rule_memories[rule] = _RuleMemory(result)
        return result

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        """Apply removals to the shared index, or discard it if unspecified."""

        if self._index is None:
            return
        if not removed:
            self._index = None
            self._pending_removed.clear()
            self._witness_cache.clear()
            self._query_blocks.clear()
            self._clear_query_watchers()
            self._rule_memories.clear()
            self._positive_join_memories.clear()
            self._partial_memory_disabled.clear()
            self._processed_revision = 0
            return
        self._pending_removed.update(removed)
        self._invalidate_query_memories((), removed)

    @staticmethod
    def _is_positive_compiled_rule(rule: Rule) -> bool:
        return all(
            isinstance(
                premise,
                (CompiledFactPremise, CompiledComparisonPremise),
            )
            for premise in compile_rule(rule).block.premises
        )

    def _instantiate_positive_memory(
        self,
        rule: Rule,
        index: FactIndex,
        delta: FactDelta | None,
    ) -> tuple[Activation, ...] | None:
        memory = self._positive_join_memories.get(rule)
        if memory is None or delta is None:
            memory = self._build_positive_memory(rule, index)
            if memory is not None:
                self.metrics.partial_join_builds += 1
        elif delta.changed:
            memory = self._update_positive_memory(
                rule,
                index,
                memory,
                delta,
            )
            if memory is not None:
                self.metrics.partial_join_updates += 1
        else:
            self.metrics.activation_cache_hits += 1
        if memory is None:
            self._positive_join_memories.pop(rule, None)
            self._partial_memory_disabled.add(rule)
            return None
        self._positive_join_memories[rule] = memory
        return tuple(
            Activation(state.substitution, state.supports)
            for state in memory[-1]
        )

    def _should_materialize_positive(
        self,
        rule: Rule,
        index: FactIndex,
    ) -> bool:
        estimate = 1
        frame = BindingFrame()
        for premise in compile_rule(rule).block.premises:
            if not isinstance(premise, CompiledFactPremise):
                continue
            estimate *= max(
                1,
                len(index.candidates_compiled(premise, frame)),
            )
            if estimate > self.partial_join_limit:
                return False
        return True

    def _build_positive_memory(
        self,
        rule: Rule,
        index: FactIndex,
    ) -> tuple[tuple[_PartialState, ...], ...] | None:
        levels: list[tuple[_PartialState, ...]] = [
            (_PartialState(EMPTY_SUBSTITUTION, ()),)
        ]
        for premise in compile_rule(rule).block.premises:
            if not isinstance(
                premise,
                (CompiledFactPremise, CompiledComparisonPremise),
            ):
                raise TypeError(
                    f"non-positive compiled premise: {premise!r}"
                )
            remaining = self.partial_join_limit - sum(
                len(level) for level in levels
            )
            levels.append(
                self._advance_positive_states(
                    levels[-1],
                    premise,
                    index,
                    max_states=remaining + 1,
                )
            )
            if sum(len(level) for level in levels) > self.partial_join_limit:
                return None
        return tuple(levels)

    def _update_positive_memory(
        self,
        rule: Rule,
        index: FactIndex,
        memory: tuple[tuple[_PartialState, ...], ...],
        delta: FactDelta,
    ) -> tuple[tuple[_PartialState, ...], ...] | None:
        retained_levels = [
            tuple(
                state
                for state in level
                if delta.removed.isdisjoint(state.supports)
            )
            for level in memory
        ]
        if delta.removed:
            self.metrics.activation_cache_filtered += sum(
                len(previous) - len(retained)
                for previous, retained in zip(
                    memory,
                    retained_levels,
                    strict=True,
                )
            )
        if not delta.added:
            self.metrics.activation_cache_hits += 1
            return tuple(retained_levels)

        updated: list[tuple[_PartialState, ...]] = [retained_levels[0]]
        new_prefixes: tuple[_PartialState, ...] = ()
        for position, premise in enumerate(
            compile_rule(rule).block.premises
        ):
            retained_current = retained_levels[position]
            retained_next = retained_levels[position + 1]
            generated: list[_PartialState] = []
            if isinstance(premise, CompiledComparisonPremise):
                generated.extend(
                    state
                    for state in new_prefixes
                    if premise.source.evaluate(state.substitution)
                )
            elif isinstance(premise, CompiledFactPremise):
                generated.extend(
                    self._advance_positive_fact_states(
                        new_prefixes,
                        premise,
                        index,
                    )
                )
                generated.extend(
                    self._advance_positive_fact_states(
                        retained_current,
                        premise,
                        index,
                        candidates=delta.added,
                    )
                )
            else:
                raise TypeError(
                    f"non-positive compiled premise: {premise!r}"
                )
            existing_keys = {
                _partial_state_key(state) for state in retained_next
            }
            unique_new: dict[
                tuple[
                    tuple[tuple[str, Term], ...],
                    tuple[Fact, ...],
                ],
                _PartialState,
            ] = {}
            for state in generated:
                key = _partial_state_key(state)
                if key not in existing_keys:
                    unique_new.setdefault(key, state)
            new_prefixes = tuple(unique_new.values())
            combined = (*retained_next, *new_prefixes)
            ordered = tuple(
                sorted(
                    combined,
                    key=lambda state: tuple(
                        index.ranks[fact] for fact in state.supports
                    ),
                )
            )
            updated.append(ordered)
            if sum(len(level) for level in updated) > self.partial_join_limit:
                return None
        return tuple(updated)

    def _advance_positive_states(
        self,
        states: tuple[_PartialState, ...],
        premise: CompiledFactPremise | CompiledComparisonPremise,
        index: FactIndex,
        *,
        max_states: int | None = None,
    ) -> tuple[_PartialState, ...]:
        if isinstance(premise, CompiledComparisonPremise):
            output = tuple(
                state
                for state in states
                if premise.source.evaluate(state.substitution)
            )
            return output if max_states is None else output[:max_states]
        return self._advance_positive_fact_states(
            states,
            premise,
            index,
            max_states=max_states,
        )

    def _advance_positive_fact_states(
        self,
        states: tuple[_PartialState, ...],
        premise: CompiledFactPremise,
        index: FactIndex,
        *,
        candidates: Sequence[Fact] | None = None,
        max_states: int | None = None,
    ) -> tuple[_PartialState, ...]:
        output: list[_PartialState] = []
        candidate_filter = (
            frozenset(candidates) if candidates is not None else None
        )
        for state in states:
            frame = BindingFrame(state.substitution.items())
            indexed_candidates = index.candidates_compiled(premise, frame)
            selected = (
                indexed_candidates
                if candidate_filter is None
                else tuple(
                    fact
                    for fact in indexed_candidates
                    if fact in candidate_filter
                )
            )
            self.metrics.candidate_facts += len(selected)
            for fact in selected:
                self.metrics.match_attempts += 1
                checkpoint = frame.checkpoint()
                if premise.match(fact.entity, fact.status, frame):
                    output.append(
                        _PartialState(
                            frame.freeze(),
                            (*state.supports, fact),
                        )
                    )
                    if (
                        max_states is not None
                        and len(output) >= max_states
                    ):
                        return tuple(output)
                frame.rollback(checkpoint)
        return tuple(output)

    def _reuse_rule_memory(
        self,
        rule: Rule,
        delta: FactDelta | None,
    ) -> tuple[Activation, ...] | None:
        memory = self._rule_memories.get(rule)
        if memory is None or delta is None or delta.added:
            return None
        if not delta.removed:
            self.metrics.activation_cache_hits += 1
            return memory.activations
        if self._removal_can_enable_negative(rule, delta.removed):
            return None
        retained = tuple(
            activation
            for activation in memory.activations
            if delta.removed.isdisjoint(activation.premise_facts)
        )
        self.metrics.activation_cache_hits += 1
        self.metrics.activation_cache_filtered += (
            len(memory.activations) - len(retained)
        )
        self._rule_memories[rule] = _RuleMemory(retained)
        return retained

    @staticmethod
    def _removal_can_enable_negative(
        rule: Rule,
        removed: frozenset[Fact],
    ) -> bool:
        dependencies = negative_fact_plans(compile_rule(rule).block)
        if not dependencies:
            return False
        frame = BindingFrame()
        for fact in removed:
            for premise in dependencies:
                checkpoint = frame.checkpoint()
                matches = premise.match(fact.entity, fact.status, frame)
                frame.rollback(checkpoint)
                if matches:
                    return True
        return False

    def _index_for(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | None,
    ) -> FactIndex:
        del rule
        if delta is not None:
            self._apply_query_delta(delta)
        if delta is not None and delta.removed:
            self._pending_removed.update(delta.removed)
        index = self._index
        if index is None:
            index = FactIndex(facts)
            self._index = index
            self._pending_removed.clear()
            self._witness_cache.clear()
            self._query_blocks.clear()
            self._clear_query_watchers()
            self.metrics.index_builds += 1
            self.metrics.indexed_facts += len(facts)
            return index
        if self._pending_removed:
            removed = frozenset(self._pending_removed)
            removal_count = index.remove(removed)
            self.metrics.index_removals += removal_count
            self._pending_removed.clear()

        if delta is None:
            indexed = tuple(index.facts)
            if facts[: len(indexed)] == indexed:
                added = index.extend(facts[len(indexed) :])
                self.metrics.indexed_facts += added
            elif indexed != facts:
                index = FactIndex(facts)
                self._index = index
                if delta is None:
                    self._witness_cache.clear()
                    self._query_blocks.clear()
                    self._clear_query_watchers()
                self.metrics.index_builds += 1
                self.metrics.indexed_facts += len(facts)
            return index

        if delta is not None and delta.added:
            added = index.extend(delta.added)
            self.metrics.indexed_facts += added
        if tuple(index.facts) != facts:
            index = FactIndex(facts)
            self._index = index
            if delta is None:
                self._witness_cache.clear()
                self._query_blocks.clear()
                self._clear_query_watchers()
            self.metrics.index_builds += 1
            self.metrics.indexed_facts += len(facts)
        return index

    def _apply_query_delta(self, delta: FactDelta) -> None:
        if delta.revision and delta.revision <= self._processed_revision:
            return
        if delta.changed:
            self._invalidate_query_memories(delta.added, delta.removed)
        if delta.revision:
            self._processed_revision = delta.revision

    def _invalidate_query_memories(
        self,
        added: tuple[Fact, ...],
        removed: frozenset[Fact],
    ) -> None:
        candidates: set[WitnessCacheKey] = set()
        for fact in removed:
            candidates.update(self._support_watchers.get(fact, ()))
            for token in _fact_watch_tokens(fact):
                candidates.update(self._negative_watchers.get(token, ()))
        for fact in added:
            for token in _fact_watch_tokens(fact):
                candidates.update(self._negative_watchers.get(token, ()))
                candidates.update(self._creation_watchers.get(token, ()))

        expired: list[WitnessCacheKey] = []
        for key in candidates:
            if key in self._simple_query_facts:
                self._update_simple_query(key, added, removed)
                continue
            block = self._query_blocks[key]
            witness = self._witness_cache.get(key)
            if witness is not None and any(
                fact in removed for fact in witness
            ):
                expired.append(key)
                continue
            bindings = (
                (Variable(name), term)
                for name, term in key[1]
            )
            frame = BindingFrame(bindings)
            negative = negative_fact_plans(block)
            if removed and self._facts_match_plans(removed, negative, frame):
                expired.append(key)
                continue
            if added and negative and self._facts_match_plans(
                added,
                negative,
                frame,
            ):
                expired.append(key)
                continue
            if (
                added
                and witness is None
                and self._facts_match_plans(
                    added,
                    all_fact_plans(block),
                    frame,
                )
            ):
                expired.append(key)
        for key in expired:
            self._remove_query_registration(key)
        self.metrics.witness_cache_invalidations += len(expired)

    def _update_simple_query(
        self,
        key: WitnessCacheKey,
        added: tuple[Fact, ...],
        removed: frozenset[Fact],
    ) -> None:
        block = self._query_blocks[key]
        plan = simple_fact_plan(block)
        if plan is None:
            raise TypeError("simple query memory requires one fact premise")
        previous = self._simple_query_facts[key]
        matching = [fact for fact in previous if fact not in removed]
        frame = BindingFrame(
            (Variable(name), term)
            for name, term in key[1]
        )
        for fact in added:
            if fact in matching:
                continue
            checkpoint = frame.checkpoint()
            matches = plan.match(fact.entity, fact.status, frame)
            frame.rollback(checkpoint)
            if matches:
                matching.append(fact)
        current = tuple(matching)
        if current == previous:
            return
        witness = (current[0],) if current else None
        self._register_query_memory(
            key,
            block,
            witness,
            simple_facts=current,
        )
        self.metrics.query_counter_updates += 1

    def _register_query_memory(
        self,
        key: WitnessCacheKey,
        block: CompiledBlock,
        witness: tuple[Fact, ...] | None,
        *,
        simple_facts: tuple[Fact, ...] | None = None,
        count_value: int | None = None,
        aggregate_supports: tuple[Fact, ...] = (),
    ) -> None:
        self._remove_query_registration(key)
        frame = BindingFrame(
            (Variable(name), term)
            for name, term in key[1]
        )
        negative_tokens = frozenset(
            _plan_watch_token(plan, frame)
            for plan in negative_fact_plans(block)
        )
        creation_tokens = (
            frozenset(
                _plan_watch_token(plan, frame)
                for plan in all_fact_plans(block)
            )
            if (
                witness is None
                or simple_facts is not None
                or count_value is not None
            )
            else frozenset()
        )
        supports = (
            simple_facts
            if simple_facts is not None
            else aggregate_supports or (witness or ())
        )
        for token in negative_tokens:
            self._negative_watchers[token].add(key)
        for token in creation_tokens:
            self._creation_watchers[token].add(key)
        for fact in supports:
            self._support_watchers[fact].add(key)
        self._witness_cache[key] = witness
        self._query_blocks[key] = block
        self._query_registrations[key] = (
            negative_tokens,
            creation_tokens,
            supports,
        )
        if simple_facts is not None:
            self._query_counts[key] = len(simple_facts)
            self._simple_query_facts[key] = simple_facts
            self._query_aggregate_supports[key] = simple_facts
        elif count_value is not None:
            self._query_counts[key] = count_value
            self._query_aggregate_supports[key] = aggregate_supports

    def _remove_query_registration(
        self,
        key: WitnessCacheKey,
    ) -> None:
        registration = self._query_registrations.pop(key, None)
        if registration is not None:
            negative_tokens, creation_tokens, supports = registration
            for token in negative_tokens:
                self._discard_watcher(self._negative_watchers, token, key)
            for token in creation_tokens:
                self._discard_watcher(self._creation_watchers, token, key)
            for fact in supports:
                self._discard_watcher(self._support_watchers, fact, key)
        self._witness_cache.pop(key, None)
        self._query_blocks.pop(key, None)
        self._query_counts.pop(key, None)
        self._simple_query_facts.pop(key, None)
        self._query_aggregate_supports.pop(key, None)

    @staticmethod
    def _discard_watcher(
        watchers: defaultdict[IndexKeyT, set[WitnessCacheKey]],
        token: IndexKeyT,
        key: WitnessCacheKey,
    ) -> None:
        watched = watchers.get(token)
        if watched is None:
            return
        watched.discard(key)
        if not watched:
            watchers.pop(token, None)

    def _clear_query_watchers(self) -> None:
        self._negative_watchers.clear()
        self._creation_watchers.clear()
        self._support_watchers.clear()
        self._query_registrations.clear()
        self._query_counts.clear()
        self._simple_query_facts.clear()
        self._query_aggregate_supports.clear()

    @staticmethod
    def _facts_match_plans(
        facts: Iterable[Fact],
        plans: tuple[CompiledFactPremise, ...],
        frame: BindingFrame,
    ) -> bool:
        for fact in facts:
            for plan in plans:
                checkpoint = frame.checkpoint()
                matches = plan.match(fact.entity, fact.status, frame)
                frame.rollback(checkpoint)
                if matches:
                    return True
        return False

    def _join(
        self,
        rule: Rule,
        index: FactIndex,
    ) -> list[Activation]:
        activations: list[Activation] = []
        frame = BindingFrame()
        self._extend_compiled(
            compile_rule(rule).block,
            index,
            premise_index=0,
            frame=frame,
            supports=[],
            output=activations,
        )
        return activations

    def _extend_compiled(
        self,
        block: CompiledBlock,
        index: FactIndex,
        premise_index: int,
        frame: BindingFrame,
        supports: list[Fact],
        output: list[Activation],
    ) -> None:
        if premise_index == len(block.premises):
            output.append(Activation(frame.freeze(), tuple(supports)))
            return
        premise = block.premises[premise_index]
        if isinstance(premise, CompiledComparisonPremise):
            if premise.source.evaluate(frame):
                self._extend_compiled(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
            return
        if isinstance(premise, CompiledBindPremise):
            checkpoint = frame.checkpoint()
            if _apply_compiled_binding(premise.source, frame):
                self._extend_compiled(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
            frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledCombinationsPremise):
            for value in premise.source.values(frame):
                checkpoint = frame.checkpoint()
                if frame.bind_ground(premise.source.target, value):
                    self._extend_compiled(
                        block,
                        index,
                        premise_index + 1,
                        frame,
                        supports,
                        output,
                    )
                frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledCollectPremise):
            collection, collection_supports = self._collect_compiled_values(
                premise,
                index,
                frame,
            )
            checkpoint = frame.checkpoint()
            if frame.bind_ground(premise.source.target, collection):
                support_count = len(supports)
                supports.extend(collection_supports)
                self._extend_compiled(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledAggregatePremise):
            count_value, aggregate_supports = self._count_compiled_query(
                premise.block,
                index,
                frame,
            )
            if _aggregate_accepts(premise.source, count_value):
                support_count = len(supports)
                supports.extend(aggregate_supports)
                self._extend_compiled(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            return
        if isinstance(premise, CompiledExistentialPremise):
            witness = self._first_compiled_witness(
                premise.block,
                index,
                frame,
            )
            succeeds = witness is not None
            if premise.negated:
                succeeds = not succeeds
                witness = ()
            if succeeds:
                support_count = len(supports)
                supports.extend(witness or ())
                self._extend_compiled(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            return
        if not isinstance(premise, CompiledFactPremise):
            raise TypeError(f"unsupported compiled premise: {premise!r}")
        candidates = index.candidates_compiled(premise, frame)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            checkpoint = frame.checkpoint()
            if premise.match(fact.entity, fact.status, frame):
                supports.append(fact)
                self._extend_compiled(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                supports.pop()
            frame.rollback(checkpoint)

    def _first_compiled_witness(
        self,
        block: CompiledBlock,
        index: FactIndex,
        frame: BindingFrame,
    ) -> tuple[Fact, ...] | None:
        key = (
            block.source,
            frame.projected_key(block.correlated_variables),
        )
        if key in self._witness_cache:
            self.metrics.witness_cache_hits += 1
            return self._witness_cache[key]
        self.metrics.witness_cache_misses += 1
        simple_plan = simple_fact_plan(block)
        if simple_plan is not None:
            matching_facts: list[Fact] = []
            candidates = index.candidates_compiled(simple_plan, frame)
            self.metrics.candidate_facts += len(candidates)
            for fact in candidates:
                self.metrics.match_attempts += 1
                checkpoint = frame.checkpoint()
                if simple_plan.match(fact.entity, fact.status, frame):
                    matching_facts.append(fact)
                frame.rollback(checkpoint)
            simple_facts = tuple(matching_facts)
            simple_witness = (simple_facts[0],) if simple_facts else None
            self._register_query_memory(
                key,
                block,
                simple_witness,
                simple_facts=simple_facts,
            )
            return simple_witness
        checkpoint = frame.checkpoint()
        supports: list[Fact] = []
        witness = self._first_compiled_witness_from(
            block,
            index,
            premise_index=0,
            frame=frame,
            supports=supports,
        )
        frame.rollback(checkpoint)
        self._register_query_memory(key, block, witness)
        return witness

    def _first_compiled_witness_from(
        self,
        block: CompiledBlock,
        index: FactIndex,
        premise_index: int,
        frame: BindingFrame,
        supports: list[Fact],
    ) -> tuple[Fact, ...] | None:
        if premise_index == len(block.premises):
            return tuple(supports)
        premise = block.premises[premise_index]
        if isinstance(premise, CompiledComparisonPremise):
            if not premise.source.evaluate(frame):
                return None
            return self._first_compiled_witness_from(
                block,
                index,
                premise_index + 1,
                frame,
                supports,
            )
        if isinstance(premise, CompiledBindPremise):
            checkpoint = frame.checkpoint()
            if not _apply_compiled_binding(premise.source, frame):
                frame.rollback(checkpoint)
                return None
            witness = self._first_compiled_witness_from(
                block,
                index,
                premise_index + 1,
                frame,
                supports,
            )
            frame.rollback(checkpoint)
            return witness
        if isinstance(premise, CompiledCombinationsPremise):
            for value in premise.source.values(frame):
                checkpoint = frame.checkpoint()
                if frame.bind_ground(premise.source.target, value):
                    witness = self._first_compiled_witness_from(
                        block,
                        index,
                        premise_index + 1,
                        frame,
                        supports,
                    )
                    frame.rollback(checkpoint)
                    if witness is not None:
                        return witness
                else:
                    frame.rollback(checkpoint)
            return None
        if isinstance(premise, CompiledCollectPremise):
            collection, collection_supports = self._collect_compiled_values(
                premise,
                index,
                frame,
            )
            checkpoint = frame.checkpoint()
            if not frame.bind_ground(premise.source.target, collection):
                frame.rollback(checkpoint)
                return None
            support_count = len(supports)
            supports.extend(collection_supports)
            witness = self._first_compiled_witness_from(
                block,
                index,
                premise_index + 1,
                frame,
                supports,
            )
            del supports[support_count:]
            frame.rollback(checkpoint)
            return witness
        if isinstance(premise, CompiledAggregatePremise):
            count_value, aggregate_supports = self._count_compiled_query(
                premise.block,
                index,
                frame,
            )
            if not _aggregate_accepts(premise.source, count_value):
                return None
            support_count = len(supports)
            supports.extend(aggregate_supports)
            witness = self._first_compiled_witness_from(
                block,
                index,
                premise_index + 1,
                frame,
                supports,
            )
            del supports[support_count:]
            return witness
        if isinstance(premise, CompiledExistentialPremise):
            nested = self._first_compiled_witness(
                premise.block,
                index,
                frame,
            )
            succeeds = nested is not None
            if premise.negated:
                succeeds = not succeeds
                nested = ()
            if not succeeds:
                return None
            support_count = len(supports)
            supports.extend(nested or ())
            witness = self._first_compiled_witness_from(
                block,
                index,
                premise_index + 1,
                frame,
                supports,
            )
            del supports[support_count:]
            return witness
        if not isinstance(premise, CompiledFactPremise):
            raise TypeError(f"unsupported compiled premise: {premise!r}")
        candidates = index.candidates_compiled(premise, frame)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            checkpoint = frame.checkpoint()
            if premise.match(fact.entity, fact.status, frame):
                supports.append(fact)
                witness = self._first_compiled_witness_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                )
                supports.pop()
                frame.rollback(checkpoint)
                if witness is not None:
                    return witness
            else:
                frame.rollback(checkpoint)
        return None

    def _count_compiled_query(
        self,
        block: CompiledBlock,
        index: FactIndex,
        frame: BindingFrame,
    ) -> tuple[int, tuple[Fact, ...]]:
        key = (
            block.source,
            frame.projected_key(block.correlated_variables),
        )
        if key in self._query_counts:
            self.metrics.witness_cache_hits += 1
            return (
                self._query_counts[key],
                self._query_aggregate_supports[key],
            )
        self.metrics.witness_cache_misses += 1
        if key in self._witness_cache:
            self._remove_query_registration(key)

        simple_plan = simple_fact_plan(block)
        if simple_plan is not None:
            matching_facts: list[Fact] = []
            candidates = index.candidates_compiled(simple_plan, frame)
            self.metrics.candidate_facts += len(candidates)
            for fact in candidates:
                self.metrics.match_attempts += 1
                checkpoint = frame.checkpoint()
                if simple_plan.match(fact.entity, fact.status, frame):
                    matching_facts.append(fact)
                frame.rollback(checkpoint)
            simple_facts = tuple(matching_facts)
            witness = (simple_facts[0],) if simple_facts else None
            self._register_query_memory(
                key,
                block,
                witness,
                simple_facts=simple_facts,
            )
            return len(simple_facts), simple_facts

        checkpoint = frame.checkpoint()
        supports: list[Fact] = []
        witnesses: list[tuple[Fact, ...]] = []
        self._collect_compiled_witnesses_from(
            block,
            index,
            premise_index=0,
            frame=frame,
            supports=supports,
            output=witnesses,
        )
        frame.rollback(checkpoint)
        witness_tuple = tuple(witnesses)
        aggregate_supports = _aggregate_supports(witness_tuple)
        first = witness_tuple[0] if witness_tuple else None
        self._register_query_memory(
            key,
            block,
            first,
            count_value=len(witness_tuple),
            aggregate_supports=aggregate_supports,
        )
        return len(witness_tuple), aggregate_supports

    def _collect_compiled_witnesses_from(
        self,
        block: CompiledBlock,
        index: FactIndex,
        premise_index: int,
        frame: BindingFrame,
        supports: list[Fact],
        output: list[tuple[Fact, ...]],
    ) -> None:
        if premise_index == len(block.premises):
            output.append(tuple(supports))
            return
        premise = block.premises[premise_index]
        if isinstance(premise, CompiledComparisonPremise):
            if premise.source.evaluate(frame):
                self._collect_compiled_witnesses_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
            return
        if isinstance(premise, CompiledBindPremise):
            checkpoint = frame.checkpoint()
            if _apply_compiled_binding(premise.source, frame):
                self._collect_compiled_witnesses_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
            frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledCombinationsPremise):
            for value in premise.source.values(frame):
                checkpoint = frame.checkpoint()
                if frame.bind_ground(premise.source.target, value):
                    self._collect_compiled_witnesses_from(
                        block,
                        index,
                        premise_index + 1,
                        frame,
                        supports,
                        output,
                    )
                frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledCollectPremise):
            collection, collection_supports = self._collect_compiled_values(
                premise,
                index,
                frame,
            )
            checkpoint = frame.checkpoint()
            if frame.bind_ground(premise.source.target, collection):
                support_count = len(supports)
                supports.extend(collection_supports)
                self._collect_compiled_witnesses_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledExistentialPremise):
            nested = self._first_compiled_witness(
                premise.block,
                index,
                frame,
            )
            succeeds = nested is not None
            if premise.negated:
                succeeds = not succeeds
                nested = ()
            if succeeds:
                support_count = len(supports)
                supports.extend(nested or ())
                self._collect_compiled_witnesses_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            return
        if isinstance(premise, CompiledAggregatePremise):
            count_value, aggregate_supports = self._count_compiled_query(
                premise.block,
                index,
                frame,
            )
            if _aggregate_accepts(premise.source, count_value):
                support_count = len(supports)
                supports.extend(aggregate_supports)
                self._collect_compiled_witnesses_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            return
        if not isinstance(premise, CompiledFactPremise):
            raise TypeError(f"unsupported compiled premise: {premise!r}")
        candidates = index.candidates_compiled(premise, frame)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            checkpoint = frame.checkpoint()
            if premise.match(fact.entity, fact.status, frame):
                supports.append(fact)
                self._collect_compiled_witnesses_from(
                    block,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                supports.pop()
            frame.rollback(checkpoint)

    def _collect_compiled_values(
        self,
        premise: CompiledCollectPremise,
        index: FactIndex,
        frame: BindingFrame,
    ) -> tuple[FiniteSet, tuple[Fact, ...]]:
        checkpoint = frame.checkpoint()
        projected: list[tuple[Term, tuple[Fact, ...]]] = []
        self._collect_compiled_projection_from(
            premise.block,
            premise.source.projection,
            index,
            premise_index=0,
            frame=frame,
            supports=[],
            output=projected,
        )
        frame.rollback(checkpoint)
        collection = FiniteSet(
            tuple(dict.fromkeys(value for value, _ in projected))
        )
        supports = tuple(
            dict.fromkeys(
                fact
                for _, witness_supports in projected
                for fact in witness_supports
            )
        )
        return collection, supports

    def _collect_compiled_projection_from(
        self,
        block: CompiledBlock,
        projection: Term,
        index: FactIndex,
        premise_index: int,
        frame: BindingFrame,
        supports: list[Fact],
        output: list[tuple[Term, tuple[Fact, ...]]],
    ) -> None:
        if premise_index == len(block.premises):
            value = frame.apply(projection)
            if not is_ground(value):
                raise ValueError("COLLECT projection must be ground")
            output.append((value, tuple(supports)))
            return
        premise = block.premises[premise_index]
        if isinstance(premise, CompiledComparisonPremise):
            if premise.source.evaluate(frame):
                self._collect_compiled_projection_from(
                    block,
                    projection,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
            return
        if isinstance(premise, CompiledBindPremise):
            checkpoint = frame.checkpoint()
            if _apply_compiled_binding(premise.source, frame):
                self._collect_compiled_projection_from(
                    block,
                    projection,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
            frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledCombinationsPremise):
            for value in premise.source.values(frame):
                checkpoint = frame.checkpoint()
                if frame.bind_ground(premise.source.target, value):
                    self._collect_compiled_projection_from(
                        block,
                        projection,
                        index,
                        premise_index + 1,
                        frame,
                        supports,
                        output,
                    )
                frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledCollectPremise):
            collection, collection_supports = self._collect_compiled_values(
                premise,
                index,
                frame,
            )
            checkpoint = frame.checkpoint()
            if frame.bind_ground(premise.source.target, collection):
                support_count = len(supports)
                supports.extend(collection_supports)
                self._collect_compiled_projection_from(
                    block,
                    projection,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            frame.rollback(checkpoint)
            return
        if isinstance(premise, CompiledAggregatePremise):
            count_value, aggregate_supports = self._count_compiled_query(
                premise.block,
                index,
                frame,
            )
            if _aggregate_accepts(premise.source, count_value):
                support_count = len(supports)
                supports.extend(aggregate_supports)
                self._collect_compiled_projection_from(
                    block,
                    projection,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            return
        if isinstance(premise, CompiledExistentialPremise):
            witness = self._first_compiled_witness(
                premise.block,
                index,
                frame,
            )
            succeeds = witness is not None
            if premise.negated:
                succeeds = not succeeds
                witness = ()
            if succeeds:
                support_count = len(supports)
                supports.extend(witness or ())
                self._collect_compiled_projection_from(
                    block,
                    projection,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                del supports[support_count:]
            return
        if not isinstance(premise, CompiledFactPremise):
            raise TypeError(f"unsupported compiled premise: {premise!r}")
        candidates = index.candidates_compiled(premise, frame)
        self.metrics.candidate_facts += len(candidates)
        for fact in candidates:
            self.metrics.match_attempts += 1
            checkpoint = frame.checkpoint()
            if premise.match(fact.entity, fact.status, frame):
                supports.append(fact)
                self._collect_compiled_projection_from(
                    block,
                    projection,
                    index,
                    premise_index + 1,
                    frame,
                    supports,
                    output,
                )
                supports.pop()
            frame.rollback(checkpoint)

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
        if isinstance(premise, (BindPremise, ComputedPremise)):
            bound = premise.apply(substitution)
            if bound is not None:
                self._extend(
                    rule,
                    index,
                    premise_index + 1,
                    bound,
                    supports,
                    output,
                    witness_cache,
                )
            return
        if isinstance(premise, CombinationsPremise):
            for value in premise.values(substitution):
                try:
                    bound = substitution.bind(premise.target, value)
                except ValueError:
                    continue
                self._extend(
                    rule,
                    index,
                    premise_index + 1,
                    bound,
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
        if isinstance(premise, (BindPremise, ComputedPremise)):
            bound = premise.apply(substitution)
            if bound is None:
                return None
            return self._first_witness_from(
                premises,
                index,
                premise_index + 1,
                bound,
                supports,
                witness_cache,
            )
        if isinstance(premise, CombinationsPremise):
            for value in premise.values(substitution):
                try:
                    bound = substitution.bind(premise.target, value)
                except ValueError:
                    continue
                witness = self._first_witness_from(
                    premises,
                    index,
                    premise_index + 1,
                    bound,
                    supports,
                    witness_cache,
                )
                if witness is not None:
                    return witness
            return None
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
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        changes = _normalize_delta(delta)
        index = self._index_for(rule, facts, changes)
        has_existential = any(
            isinstance(
                premise,
                (
                    ExistsPremise,
                    NotExistsPremise,
                    CountPremise,
                    UniquePremise,
                    CollectPremise,
                ),
            )
            for premise in rule.premises
        )
        if (
            changes is None
            or changes.removed
            or (changes.added and has_existential)
        ):
            activations = self._join(rule, index)
        elif not changes.added:
            activations = []
        else:
            fact_premises = tuple(
                position
                for position, premise in enumerate(rule.premises)
                if isinstance(premise, FactPremise)
            )
            premise_groups = self._premise_groups(rule)
            delta_start = len(index) - len(changes.added)
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
            next_group = group_index + 1
            next_remaining = (
                premise_groups[next_group][0]
                if next_group < len(premise_groups)
                else ()
            )
            barrier_index = premise_groups[group_index][1]
            substitutions: tuple[Substitution, ...] = (substitution,)
            if barrier_index is not None:
                barrier = rule.premises[barrier_index]
                if isinstance(barrier, ComparisonPremise):
                    substitutions = (
                        (substitution,)
                        if barrier.evaluate(substitution)
                        else ()
                    )
                elif isinstance(barrier, (BindPremise, ComputedPremise)):
                    bound = barrier.apply(substitution)
                    substitutions = () if bound is None else (bound,)
                elif isinstance(barrier, CombinationsPremise):
                    substitutions = tuple(
                        substitution.bind(barrier.target, value)
                        for value in barrier.values(substitution)
                    )
                else:
                    raise TypeError(
                        f"unsupported delta barrier: {barrier!r}"
                    )
            for next_substitution in substitutions:
                self._extend_delta_variant(
                    rule,
                    index,
                    premise_groups,
                    next_group,
                    next_remaining,
                    anchor,
                    delta_start,
                    next_substitution,
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
            elif isinstance(
                premise,
                (
                    ComparisonPremise,
                    BindPremise,
                    CombinationsPremise,
                    ComputedPremise,
                ),
            ):
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
        self.by_subject_relation: defaultdict[
            tuple[Term, Term], list[Fact]
        ] = defaultdict(list)
        self.by_relation_object: defaultdict[
            tuple[Term, Term], list[Fact]
        ] = defaultdict(list)
        self.by_subject_object: defaultdict[
            tuple[Term, Term], list[Fact]
        ] = defaultdict(list)
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
                self.by_subject_relation[
                    (fact.entity.subject, fact.entity.relation)
                ].append(fact)
                self.by_relation_object[
                    (fact.entity.relation, fact.entity.object)
                ].append(fact)
                self.by_subject_object[
                    (fact.entity.subject, fact.entity.object)
                ].append(fact)
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
                self._remove_from_bucket(
                    self.by_subject_relation,
                    (fact.entity.subject, fact.entity.relation),
                    fact,
                )
                self._remove_from_bucket(
                    self.by_relation_object,
                    (fact.entity.relation, fact.entity.object),
                    fact,
                )
                self._remove_from_bucket(
                    self.by_subject_object,
                    (fact.entity.subject, fact.entity.object),
                    fact,
                )
        self.facts[:] = [fact for fact in self.facts if fact not in present]
        self.ranks = {fact: rank for rank, fact in enumerate(self.facts)}
        return len(present)

    @staticmethod
    def _remove_from_bucket(
        buckets: defaultdict[IndexKeyT, list[Fact]],
        key: IndexKeyT,
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
        return self.candidates_compiled(
            compile_fact_premise(premise),
            substitution,
        )

    def candidates_compiled(
        self,
        premise: CompiledFactPremise,
        bindings: TermBindings,
    ) -> Sequence[Fact]:
        buckets: list[Sequence[Fact]] = []

        status = premise.status.resolve(bindings)
        if status is not None:
            buckets.append(self.by_status.get(status, ()))

        if premise.triple_parts is None:
            entity = premise.entity.resolve(bindings)
            if entity is not None:
                buckets.append(self.by_entity.get(entity, ()))
            return min(buckets, key=len) if buckets else self.facts

        subject = premise.triple_parts[0].resolve(bindings)
        relation = premise.triple_parts[1].resolve(bindings)
        object_ = premise.triple_parts[2].resolve(bindings)
        if subject is not None and relation is not None and object_ is not None:
            buckets.append(
                self.by_entity.get(
                    Triple(subject, relation, object_),
                    (),
                )
            )
        for part, part_index in (
            (subject, self.by_subject),
            (relation, self.by_relation),
            (object_, self.by_object),
        ):
            if part is not None:
                buckets.append(part_index.get(part, ()))
        if subject is not None and relation is not None:
            buckets.append(
                self.by_subject_relation.get(
                    (subject, relation),
                    (),
                )
            )
        if relation is not None and object_ is not None:
            buckets.append(
                self.by_relation_object.get(
                    (relation, object_),
                    (),
                )
            )
        if subject is not None and object_ is not None:
            buckets.append(
                self.by_subject_object.get(
                    (subject, object_),
                    (),
                )
            )

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


def _normalize_delta(
    delta: FactDelta | tuple[Fact, ...] | None,
) -> FactDelta | None:
    if delta is None or isinstance(delta, FactDelta):
        return delta
    return FactDelta(added=delta)


def _plan_watch_token(
    premise: CompiledFactPremise,
    bindings: TermBindings,
) -> WatchToken:
    entity = premise.entity.resolve(bindings)
    if entity is not None:
        return "entity", entity
    if premise.triple_parts is not None:
        subject = premise.triple_parts[0].resolve(bindings)
        relation = premise.triple_parts[1].resolve(bindings)
        object_ = premise.triple_parts[2].resolve(bindings)
        if subject is not None and relation is not None:
            return "subject_relation", (subject, relation)
        if relation is not None and object_ is not None:
            return "relation_object", (relation, object_)
        if subject is not None and object_ is not None:
            return "subject_object", (subject, object_)
        if subject is not None:
            return "subject", subject
        if relation is not None:
            return "relation", relation
        if object_ is not None:
            return "object", object_
    status = premise.status.resolve(bindings)
    if status is not None:
        return "status", status
    return "any", None


def _fact_watch_tokens(fact: Fact) -> tuple[WatchToken, ...]:
    tokens: list[WatchToken] = [
        ("any", None),
        ("entity", fact.entity),
        ("status", fact.status),
    ]
    if isinstance(fact.entity, Triple):
        tokens.extend(
            (
                ("subject", fact.entity.subject),
                ("relation", fact.entity.relation),
                ("object", fact.entity.object),
                (
                    "subject_relation",
                    (fact.entity.subject, fact.entity.relation),
                ),
                (
                    "relation_object",
                    (fact.entity.relation, fact.entity.object),
                ),
                (
                    "subject_object",
                    (fact.entity.subject, fact.entity.object),
                ),
            )
        )
    return tuple(tokens)


def _partial_state_key(
    state: _PartialState,
) -> tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]]:
    return state.substitution.key, state.supports


def _aggregate_accepts(
    premise: CountPremise | UniquePremise,
    count_value: int,
) -> bool:
    if isinstance(premise, UniquePremise):
        return count_value == 1
    return premise.accepts(count_value)


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
