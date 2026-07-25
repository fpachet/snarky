"""Persistent witness and aggregate memories for existential queries."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import cast

from ..facts import Fact
from ..substitutions import BindingFrame, TermBindings
from ..terms import Triple, Variable
from .base import WitnessCache, WitnessCacheKey
from .compiled import (
    CompiledBlock,
    CompiledFactPremise,
    all_fact_plans,
    negative_fact_plans,
)
from .fact_index import (
    FactIndex,
    StructuralKey,
    StructuralSignature,
    _structural_lookup,
)

type WatchToken = tuple[str, object]


class QueryMemory:
    """Own query caches and the watchers that keep them valid."""

    def __init__(self) -> None:
        self.witness_cache: WitnessCache = {}
        self.blocks: dict[WitnessCacheKey, CompiledBlock] = {}
        self.negative_watchers: defaultdict[
            WatchToken, set[WitnessCacheKey]
        ] = defaultdict(set)
        self.creation_watchers: defaultdict[
            WatchToken, set[WitnessCacheKey]
        ] = defaultdict(set)
        self.support_watchers: defaultdict[
            Fact, set[WitnessCacheKey]
        ] = defaultdict(set)
        self.registrations: dict[
            WitnessCacheKey,
            tuple[
                frozenset[WatchToken],
                frozenset[WatchToken],
                tuple[Fact, ...],
            ],
        ] = {}
        self.counts: dict[WitnessCacheKey, int] = {}
        self.simple_facts: dict[WitnessCacheKey, tuple[Fact, ...]] = {}
        self.aggregate_supports: dict[
            WitnessCacheKey, tuple[Fact, ...]
        ] = {}
        self.residual_witnesses: dict[
            WitnessCacheKey,
            tuple[tuple[Fact, ...], ...],
        ] = {}
        self.structural_signatures: set[StructuralSignature] = set()
        self.processed_revision = 0

    def register(
        self,
        key: WitnessCacheKey,
        block: CompiledBlock,
        witness: tuple[Fact, ...] | None,
        *,
        use_structural_watches: bool,
        simple_facts: tuple[Fact, ...] | None = None,
        count_value: int | None = None,
        aggregate_supports: tuple[Fact, ...] = (),
        residual_witnesses: tuple[tuple[Fact, ...], ...] = (),
    ) -> None:
        self.remove(key)
        frame = BindingFrame(
            (Variable(name), term)
            for name, term in key[1]
        )
        negative_tokens = frozenset(
            _plan_watch_token(
                plan,
                frame,
                use_structure=use_structural_watches,
            )
            for plan in negative_fact_plans(block)
        )
        creation_tokens = (
            frozenset(
                _plan_watch_token(
                    plan,
                    frame,
                    use_structure=use_structural_watches,
                )
                for plan in all_fact_plans(block)
            )
            if (
                witness is None
                or simple_facts is not None
                or count_value is not None
            )
            else frozenset()
        )
        for token in (*negative_tokens, *creation_tokens):
            if token[0] == "structure":
                signature, _ = cast(
                    tuple[StructuralSignature, StructuralKey],
                    token[1],
                )
                self.structural_signatures.add(signature)
        supports = (
            simple_facts
            if simple_facts is not None
            else aggregate_supports
            or aggregate_witness_supports(residual_witnesses)
            or (witness or ())
        )
        for token in negative_tokens:
            self.negative_watchers[token].add(key)
        for token in creation_tokens:
            self.creation_watchers[token].add(key)
        for fact in supports:
            self.support_watchers[fact].add(key)
        self.witness_cache[key] = witness
        self.blocks[key] = block
        self.registrations[key] = (
            negative_tokens,
            creation_tokens,
            supports,
        )
        if simple_facts is not None:
            self.counts[key] = len(simple_facts)
            self.simple_facts[key] = simple_facts
            self.aggregate_supports[key] = simple_facts
        elif count_value is not None:
            self.counts[key] = count_value
            self.aggregate_supports[key] = aggregate_supports
        if residual_witnesses:
            self.residual_witnesses[key] = residual_witnesses

    def remove(self, key: WitnessCacheKey) -> None:
        registration = self.registrations.pop(key, None)
        if registration is not None:
            negative_tokens, creation_tokens, supports = registration
            for token in negative_tokens:
                _discard_watcher(self.negative_watchers, token, key)
            for token in creation_tokens:
                _discard_watcher(self.creation_watchers, token, key)
            for fact in supports:
                _discard_watcher(self.support_watchers, fact, key)
        self.witness_cache.pop(key, None)
        self.blocks.pop(key, None)
        self.counts.pop(key, None)
        self.simple_facts.pop(key, None)
        self.aggregate_supports.pop(key, None)
        self.residual_witnesses.pop(key, None)

    def affected_keys(
        self,
        added: tuple[Fact, ...],
        removed: frozenset[Fact],
    ) -> set[WitnessCacheKey]:
        candidates: set[WitnessCacheKey] = set()
        for fact in removed:
            candidates.update(self.support_watchers.get(fact, ()))
            for token in _fact_watch_tokens(
                fact,
                self.structural_signatures,
            ):
                candidates.update(self.negative_watchers.get(token, ()))
        for fact in added:
            for token in _fact_watch_tokens(
                fact,
                self.structural_signatures,
            ):
                candidates.update(self.negative_watchers.get(token, ()))
                candidates.update(self.creation_watchers.get(token, ()))
        return candidates

    def clear(self, *, reset_revision: bool = False) -> None:
        self.witness_cache.clear()
        self.blocks.clear()
        self.negative_watchers.clear()
        self.creation_watchers.clear()
        self.support_watchers.clear()
        self.registrations.clear()
        self.counts.clear()
        self.simple_facts.clear()
        self.aggregate_supports.clear()
        self.residual_witnesses.clear()
        self.structural_signatures.clear()
        if reset_revision:
            self.processed_revision = 0


def facts_match_plans(
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


def aggregate_witness_supports(
    witnesses: tuple[tuple[Fact, ...], ...],
) -> tuple[Fact, ...]:
    return tuple(
        dict.fromkeys(
            fact
            for witness in witnesses
            for fact in witness
        )
    )


def _plan_watch_token(
    premise: CompiledFactPremise,
    bindings: TermBindings,
    *,
    use_structure: bool = True,
) -> WatchToken:
    entity = premise.entity.resolve(bindings)
    if entity is not None:
        return "entity", entity
    if use_structure:
        structural = _structural_lookup(premise, bindings)
        if structural is not None:
            return "structure", structural
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


def _fact_watch_tokens(
    fact: Fact,
    structural_signatures: Iterable[StructuralSignature] = (),
) -> tuple[WatchToken, ...]:
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
    for signature in structural_signatures:
        key = FactIndex._structural_key(fact, signature)
        if key is not None:
            tokens.append(("structure", (signature, key)))
    return tuple(tokens)


def _discard_watcher[WatchKeyT](
    watchers: defaultdict[WatchKeyT, set[WitnessCacheKey]],
    token: WatchKeyT,
    key: WitnessCacheKey,
) -> None:
    watched = watchers.get(token)
    if watched is None:
        return
    watched.discard(key)
    if not watched:
        watchers.pop(token, None)
