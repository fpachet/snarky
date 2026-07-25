"""Dependency-aware joint fixed points for rules and state propagators."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Sequence

from .engine import FactMutationKind, InferenceEvent, InferenceSession
from .facts import Fact
from .premises import (
    CollectPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from .rules import RuleGroup
from .terms import Term, Triple, is_ground

type SessionPropagator = Callable[[InferenceSession], None]
type _RelationWatch = frozenset[Term] | None
type _Component = tuple[str, int]


class JointFixedPointScheduler:
    """Run only components affected by visible fact deltas.

    ``None`` is the conservative wildcard watch. Propagators may expose a
    ``watched_relations`` iterable; ordinary callables without metadata are
    treated as depending on every fact. Rule-group watches are compiled from
    factual premises, including correlated and aggregate blocks.
    """

    def __init__(
        self,
        groups: Sequence[RuleGroup],
        propagators: Sequence[SessionPropagator],
        *,
        maximum_rounds: int,
    ) -> None:
        self.groups = tuple(groups)
        self.propagators = tuple(propagators)
        self.maximum_rounds = maximum_rounds
        self._group_watches = tuple(
            _group_watch(group) for group in self.groups
        )
        self._propagator_watches = tuple(
            _propagator_watch(propagator)
            for propagator in self.propagators
        )

    def run(self, session: InferenceSession) -> None:
        components: tuple[_Component, ...] = (
            *(
                ("propagator", index)
                for index in range(len(self.propagators))
            ),
            *(("group", index) for index in range(len(self.groups))),
        )
        pending = deque(components)
        queued = set(components)
        maximum_runs = self.maximum_rounds * max(1, len(components))
        runs = 0

        while pending:
            if runs >= maximum_runs:
                raise RuntimeError(
                    "choice propagation did not stabilize within "
                    f"{self.maximum_rounds} dependency rounds"
                )
            component = pending.popleft()
            queued.remove(component)
            before = session.event_count
            kind, index = component
            if kind == "propagator":
                self.propagators[index](session)
            else:
                session.run_group(self.groups[index])
            runs += 1

            changed = _changed_relations(session.events_since(before))
            if changed == frozenset():
                continue
            for target in components:
                if target == component or target in queued:
                    continue
                target_kind, target_index = target
                watch = (
                    self._propagator_watches[target_index]
                    if target_kind == "propagator"
                    else self._group_watches[target_index]
                )
                if _is_affected(watch, changed):
                    pending.append(target)
                    queued.add(target)


def _propagator_watch(
    propagator: SessionPropagator,
) -> _RelationWatch:
    declared = getattr(propagator, "watched_relations", None)
    if declared is None:
        return None
    return frozenset(declared)


def _group_watch(group: RuleGroup) -> _RelationWatch:
    relations: set[Term] = set()
    found_fact = False
    for rule in group.rules:
        for premise in rule.premises:
            watch, contains_fact = _premise_watch(premise)
            found_fact = found_fact or contains_fact
            if watch is None and contains_fact:
                return None
            if watch is not None:
                relations.update(watch)
    return frozenset(relations) if found_fact else None


def _premise_watch(
    premise: Premise,
) -> tuple[_RelationWatch, bool]:
    if isinstance(premise, FactPremise):
        entity = premise.entity
        if not isinstance(entity, Triple) or not is_ground(entity.relation):
            return None, True
        return frozenset((entity.relation,)), True
    if isinstance(
        premise,
        (
            ExistsPremise,
            NotExistsPremise,
            CountPremise,
            UniquePremise,
            CollectPremise,
        ),
    ):
        relations: set[Term] = set()
        found_fact = False
        for nested in premise.premises:
            watch, contains_fact = _premise_watch(nested)
            found_fact = found_fact or contains_fact
            if watch is None and contains_fact:
                return None, True
            if watch is not None:
                relations.update(watch)
        return frozenset(relations), found_fact
    return frozenset(), False


def _changed_relations(
    events: tuple[InferenceEvent, ...],
) -> _RelationWatch:
    transitions: dict[Fact, tuple[FactMutationKind, FactMutationKind]] = {}
    facts: dict[Fact, Fact] = {}
    for event in events:
        previous = transitions.get(event.fact)
        transitions[event.fact] = (
            event.kind if previous is None else previous[0],
            event.kind,
        )
        facts[event.fact] = event.fact
    relations: set[Term] = set()
    for fact_key, (initial, final) in transitions.items():
        if initial is not final:
            continue
        fact = facts[fact_key]
        entity = fact.entity
        if not isinstance(entity, Triple):
            return None
        relations.add(entity.relation)
    return frozenset(relations)


def _is_affected(
    watch: _RelationWatch,
    changed: _RelationWatch,
) -> bool:
    return (
        watch is None
        or changed is None
        or not watch.isdisjoint(changed)
    )
