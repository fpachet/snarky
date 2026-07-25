"""Incrementally maintained indexes over immutable facts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
from functools import cache
from typing import TypeVar, overload

from ..facts import Fact
from ..premises import FactPremise
from ..substitutions import Substitution, TermBindings
from ..terms import FiniteSequence, Term, Triple, Variable
from .base import Activation, InstantiationMetrics
from .compiled import CompiledFactPremise, compile_fact_premise

IndexKeyT = TypeVar("IndexKeyT")
type TermPath = tuple[str | int, ...]
type StructuralSignature = tuple[TermPath, ...]
type StructuralKey = tuple[Term, ...]
_STRUCTURAL_INDEX_MIN_BUCKET = 8
_ORDERED_FACT_SET_MIN_INITIAL_FACTS = 1_500


class _OrderedFactSet(Sequence[Fact]):
    """Insertion-ordered fact set with constant-time add and removal."""

    __slots__ = ("_members", "_snapshot")

    def __init__(self) -> None:
        self._members: dict[Fact, None] = {}
        self._snapshot: tuple[Fact, ...] | None = None

    def add(self, fact: Fact) -> bool:
        if fact in self._members:
            return False
        self._members[fact] = None
        self._snapshot = None
        return True

    def discard(self, fact: Fact) -> bool:
        if fact not in self._members:
            return False
        del self._members[fact]
        self._snapshot = None
        return True

    def clone(self) -> _OrderedFactSet:
        """Return an isolated container sharing its immutable fact objects."""

        clone = _OrderedFactSet()
        clone._members = self._members.copy()
        clone._snapshot = self._snapshot
        return clone

    def __contains__(self, item: object) -> bool:
        return item in self._members

    def __iter__(self) -> Iterator[Fact]:
        return iter(self._members)

    def __len__(self) -> int:
        return len(self._members)

    @overload
    def __getitem__(self, index: int) -> Fact: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[Fact, ...]: ...

    def __getitem__(
        self,
        index: int | slice,
    ) -> Fact | tuple[Fact, ...]:
        if self._snapshot is None:
            self._snapshot = tuple(self._members)
        return self._snapshot[index]


def _resolved_leaf_constraints(
    term: Term,
    bindings: TermBindings,
    path: TermPath = ("entity",),
) -> tuple[tuple[TermPath, Term], ...]:
    """Return ground leaf constraints visible under the current bindings."""

    if isinstance(term, Variable):
        if term not in bindings:
            return ()
        return ((path, bindings.apply(term)),)
    if isinstance(term, Triple):
        constraints: list[tuple[TermPath, Term]] = []
        for name, part in (
            ("subject", term.subject),
            ("relation", term.relation),
            ("object", term.object),
        ):
            constraints.extend(
                _resolved_leaf_constraints(
                    part,
                    bindings,
                    (*path, name),
                )
            )
        return tuple(constraints)
    if isinstance(term, FiniteSequence):
        sequence_constraints: list[tuple[TermPath, Term]] = []
        for index, element in enumerate(term.elements):
            sequence_constraints.extend(
                _resolved_leaf_constraints(
                    element,
                    bindings,
                    (*path, index),
                )
            )
        return tuple(sequence_constraints)
    return ((path, term),)


@cache
def _contains_sequence(term: Term) -> bool:
    if isinstance(term, FiniteSequence):
        return True
    if isinstance(term, Triple):
        return any(
            _contains_sequence(part)
            for part in (term.subject, term.relation, term.object)
        )
    return False


def _term_at_path(fact: Fact, path: TermPath) -> Term | None:
    """Resolve a previously compiled structural path in one ground fact."""

    if not path:
        return None
    current: Term = fact.entity if path[0] == "entity" else fact.status
    for step in path[1:]:
        if isinstance(step, int):
            if (
                not isinstance(current, FiniteSequence)
                or step >= len(current.elements)
            ):
                return None
            current = current.elements[step]
            continue
        if not isinstance(current, Triple):
            return None
        if step == "subject":
            current = current.subject
        elif step == "relation":
            current = current.relation
        elif step == "object":
            current = current.object
        else:
            return None
    return current


def _structural_lookup(
    premise: CompiledFactPremise,
    bindings: TermBindings,
) -> tuple[StructuralSignature, StructuralKey] | None:
    """Compile one useful partial-structure lookup for a fact premise."""

    if not _contains_sequence(premise.source.entity):
        return None
    if premise.entity.resolve(bindings) is not None:
        return None
    constraints = _resolved_leaf_constraints(
        premise.source.entity,
        bindings,
    )
    if not any(
        isinstance(step, int)
        for path, _ in constraints
        for step in path
    ):
        return None
    ordered = tuple(sorted(constraints, key=lambda item: repr(item[0])))
    return (
        tuple(path for path, _ in ordered),
        tuple(value for _, value in ordered),
    )


class FactIndex:
    """Incrementally maintained indexes over facts and top-level positions."""

    def __init__(
        self,
        facts: Sequence[Fact] = (),
        *,
        metrics: InstantiationMetrics | None = None,
    ) -> None:
        self.metrics = metrics
        self.facts: list[Fact] | _OrderedFactSet = (
            _OrderedFactSet()
            if len(facts) >= _ORDERED_FACT_SET_MIN_INITIAL_FACTS
            else []
        )
        self.ranks: dict[Fact, int] = {}
        self._next_rank = 0
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
        self.by_structure: dict[
            StructuralSignature,
            defaultdict[StructuralKey, _OrderedFactSet],
        ] = {}
        self.extend(facts)

    def extend(self, facts: Sequence[Fact]) -> int:
        added = 0
        for fact in facts:
            if fact in self.ranks:
                continue
            self.ranks[fact] = self._next_rank
            self._next_rank += 1
            if isinstance(self.facts, _OrderedFactSet):
                self.facts.add(fact)
            else:
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
            self._add_to_structural_indexes(fact)
            added += 1
        return added

    def remove(self, facts: frozenset[Fact]) -> int:
        """Remove facts while preserving the insertion order of survivors."""

        present = facts.intersection(self.ranks)
        if not present:
            return 0
        for fact in present:
            if isinstance(self.facts, _OrderedFactSet):
                self.facts.discard(fact)
            del self.ranks[fact]
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
            self._remove_from_structural_indexes(fact)
        if isinstance(self.facts, list):
            self.facts[:] = [
                fact for fact in self.facts if fact not in present
            ]
        return len(present)

    def clone(
        self,
        *,
        metrics: InstantiationMetrics | None = None,
    ) -> FactIndex:
        """Clone mutable buckets while sharing immutable facts and terms."""

        clone = object.__new__(FactIndex)
        clone.metrics = metrics
        clone.facts = (
            self.facts.clone()
            if isinstance(self.facts, _OrderedFactSet)
            else self.facts.copy()
        )
        clone.ranks = self.ranks.copy()
        clone._next_rank = self._next_rank
        clone.by_entity = _clone_list_buckets(self.by_entity)
        clone.by_status = _clone_list_buckets(self.by_status)
        clone.by_subject = _clone_list_buckets(self.by_subject)
        clone.by_relation = _clone_list_buckets(self.by_relation)
        clone.by_object = _clone_list_buckets(self.by_object)
        clone.by_subject_relation = _clone_list_buckets(
            self.by_subject_relation
        )
        clone.by_relation_object = _clone_list_buckets(
            self.by_relation_object
        )
        clone.by_subject_object = _clone_list_buckets(
            self.by_subject_object
        )
        clone.by_structure = {
            signature: defaultdict(
                _OrderedFactSet,
                {
                    key: bucket.clone()
                    for key, bucket in buckets.items()
                },
            )
            for signature, buckets in self.by_structure.items()
        }
        return clone

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

    def delta_start(self, added: Sequence[Fact]) -> int:
        """Return the stable-rank boundary for one append-only delta."""

        return min(
            (self.ranks[fact] for fact in added if fact in self.ranks),
            default=self._next_rank,
        )

    def _add_to_structural_indexes(self, fact: Fact) -> None:
        for signature, buckets in self.by_structure.items():
            key = self._structural_key(fact, signature)
            if key is not None:
                buckets[key].add(fact)

    def _remove_from_structural_indexes(self, fact: Fact) -> None:
        for signature, buckets in self.by_structure.items():
            key = self._structural_key(fact, signature)
            if key is None:
                continue
            bucket = buckets.get(key)
            if bucket is None:
                continue
            bucket.discard(fact)
            if not bucket:
                del buckets[key]

    @staticmethod
    def _structural_key(
        fact: Fact,
        signature: StructuralSignature,
    ) -> StructuralKey | None:
        values: list[Term] = []
        for path in signature:
            value = _term_at_path(fact, path)
            if value is None:
                return None
            values.append(value)
        return tuple(values)

    def structural_candidates(
        self,
        premise: CompiledFactPremise,
        bindings: TermBindings,
    ) -> Sequence[Fact] | None:
        """Return a lazily built index bucket for a partial nested term."""

        lookup = _structural_lookup(premise, bindings)
        if lookup is None:
            return None
        if self.metrics is not None:
            self.metrics.structural_index_lookups += 1
        signature, key = lookup
        buckets = self.by_structure.get(signature)
        if buckets is None:
            buckets = defaultdict(_OrderedFactSet)
            for fact in self.facts:
                fact_key = self._structural_key(fact, signature)
                if fact_key is not None:
                    buckets[fact_key].add(fact)
            self.by_structure[signature] = buckets
            if self.metrics is not None:
                self.metrics.structural_index_builds += 1
        return buckets.get(key, ())

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
        if (
            object_ is None
            and (
                not buckets
                or min(len(bucket) for bucket in buckets)
                > _STRUCTURAL_INDEX_MIN_BUCKET
            )
        ):
            structural = self.structural_candidates(premise, bindings)
            if structural is not None:
                buckets.append(structural)

        return min(buckets, key=len) if buckets else self.facts

    def candidates_partitioned(
        self,
        premise: FactPremise,
        substitution: Substitution,
        delta_start: int,
        *,
        new: bool,
    ) -> Sequence[Fact]:
        return self.candidates_compiled_partitioned(
            compile_fact_premise(premise),
            substitution,
            delta_start,
            new=new,
        )

    def candidates_compiled_partitioned(
        self,
        premise: CompiledFactPremise,
        bindings: TermBindings,
        delta_start: int,
        *,
        new: bool,
    ) -> Sequence[Fact]:
        candidates = self.candidates_compiled(premise, bindings)
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


def _clone_list_buckets[KeyT](
    buckets: defaultdict[KeyT, list[Fact]],
) -> defaultdict[KeyT, list[Fact]]:
    return defaultdict(
        list,
        {key: facts.copy() for key, facts in buckets.items()},
    )
