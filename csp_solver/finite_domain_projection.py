"""Rollback-aware projection of canonical finite-domain facts."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from snarky import (
    Atom,
    Fact,
    FactMutationKind,
    FiniteSequence,
    InferenceEvent,
    InferenceEventCursor,
    InferenceSession,
    Number,
    Status,
    Term,
    Triple,
)

CSP_PROBLEM = Atom("csp_problem")
CSP_VARIABLE = Atom("csp_variable")
KIND = Atom("kind")
VARIABLE = Atom("variable")
CANDIDATE = Atom("candidate")
VALUE = Atom("value")
DECISION = Atom("decision")
CHOICE_WEIGHT = Atom("choice_weight")

_TOPOLOGY_RELATIONS = frozenset((KIND, VARIABLE, CHOICE_WEIGHT))


@dataclass(slots=True)
class FiniteDomainSnapshot:
    """Mutable internal projection; consumers must treat it as read-only."""

    cursor: InferenceEventCursor
    base_position: int
    trail: list[InferenceEvent]
    present: set[Fact]
    problems: dict[Term, Fact]
    problem_variables: list[tuple[Term, Term, Fact]]
    csp_variables: dict[Term, Fact]
    candidates: dict[Term, dict[Term, Fact]]
    candidate_order: dict[Fact, int]
    values: dict[Term, dict[Term, Fact]]
    decisions: list[tuple[Term, Term, Fact]]
    weights: dict[tuple[Term, Term], tuple[Term, float, Fact]]


class FiniteDomainProjection:
    """Maintain finite-domain indexes from session deltas and rollback."""

    def __init__(self) -> None:
        self._states: WeakKeyDictionary[
            InferenceSession,
            FiniteDomainSnapshot,
        ] = WeakKeyDictionary()

    def snapshot(
        self,
        session: InferenceSession,
    ) -> FiniteDomainSnapshot:
        state = self._states.get(session)
        if state is None:
            return self._rebuild(session)

        current = session.event_cursor()
        if current.generation == state.cursor.generation:
            events = session.events_after(state.cursor)
            if events is None:
                return self._rebuild(session)
            if not self._apply_events(state, events):
                return self._rebuild(session)
        else:
            origin = current.generation_origin
            if (
                origin < state.base_position
                or origin > state.cursor.position
            ):
                return self._rebuild(session)
            rollback_count = state.cursor.position - origin
            for _ in range(rollback_count):
                event = state.trail.pop()
                if not self._apply_event(state, event, forward=False):
                    return self._rebuild(session)
            events = session.events_since(origin)
            if not self._apply_events(state, events):
                return self._rebuild(session)

        state.cursor = current
        return state

    def _rebuild(
        self,
        session: InferenceSession,
    ) -> FiniteDomainSnapshot:
        cursor = session.event_cursor()
        state = FiniteDomainSnapshot(
            cursor,
            cursor.position,
            [],
            set(session.facts),
            {},
            [],
            {},
            {},
            {},
            {},
            [],
            {},
        )
        for order, fact in enumerate(session.facts):
            self._index_initial_fact(state, fact, order)
        self._states[session] = state
        return state

    def _apply_events(
        self,
        state: FiniteDomainSnapshot,
        events: tuple[InferenceEvent, ...],
    ) -> bool:
        for event in events:
            if not self._apply_event(state, event, forward=True):
                return False
            state.trail.append(event)
        return True

    def _apply_event(
        self,
        state: FiniteDomainSnapshot,
        event: InferenceEvent,
        *,
        forward: bool,
    ) -> bool:
        added = event.kind is FactMutationKind.ADD
        if not forward:
            added = not added
        fact = event.fact
        entity = fact.entity
        if (
            fact.status is Status.VRAI
            and isinstance(entity, Triple)
            and entity.relation in _TOPOLOGY_RELATIONS
        ):
            return False
        if added:
            state.present.add(fact)
        else:
            state.present.discard(fact)
        if fact.status is not Status.VRAI or not isinstance(entity, Triple):
            return True
        if entity.relation == CANDIDATE:
            domain = state.candidates.setdefault(entity.subject, {})
            if added:
                domain[entity.object] = fact
                if fact not in state.candidate_order:
                    state.candidate_order[fact] = len(
                        state.candidate_order
                    )
            else:
                domain.pop(entity.object, None)
                if not domain:
                    state.candidates.pop(entity.subject, None)
        elif entity.relation == VALUE:
            known = state.values.setdefault(entity.subject, {})
            if added:
                known[entity.object] = fact
            else:
                known.pop(entity.object, None)
                if not known:
                    state.values.pop(entity.subject, None)
        elif entity.relation == DECISION:
            item = (entity.subject, entity.object, fact)
            if added:
                state.decisions.append(item)
            else:
                with suppress(ValueError):
                    state.decisions.remove(item)
        return True

    @staticmethod
    def _index_initial_fact(
        state: FiniteDomainSnapshot,
        fact: Fact,
        order: int,
    ) -> None:
        if fact.status is not Status.VRAI:
            return
        entity = fact.entity
        if not isinstance(entity, Triple):
            return
        if entity.relation == KIND and entity.object == CSP_PROBLEM:
            state.problems[entity.subject] = fact
        elif entity.relation == VARIABLE:
            state.problem_variables.append(
                (entity.subject, entity.object, fact)
            )
        elif (
            entity.relation == KIND
            and entity.object == CSP_VARIABLE
        ):
            state.csp_variables[entity.subject] = fact
        elif entity.relation == CANDIDATE:
            state.candidates.setdefault(entity.subject, {})[
                entity.object
            ] = fact
            state.candidate_order[fact] = order
        elif entity.relation == VALUE:
            state.values.setdefault(entity.subject, {})[
                entity.object
            ] = fact
        elif entity.relation == DECISION:
            state.decisions.append(
                (entity.subject, entity.object, fact)
            )
        elif (
            entity.relation == CHOICE_WEIGHT
            and isinstance(entity.object, FiniteSequence)
            and len(entity.object.elements) == 2
        ):
            value, weight_term = entity.object.elements
            if isinstance(weight_term, Number) and isinstance(
                weight_term.value,
                (int, float),
            ):
                state.weights[(entity.subject, value)] = (
                    weight_term,
                    float(weight_term.value),
                    fact,
                )
