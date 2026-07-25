"""Action staging, fact mutations, and truth-maintenance cascades."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..actions import (
    Action,
    AddFact,
    Choice,
    ForEach,
    Fresh,
    Let,
    RemoveFact,
)
from ..facts import Fact
from ..rules import Rule, RuleGroup
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import Atom, FiniteSequence, FiniteSet, Term, Triple
from .events import FactMutationKind, InferenceEvent
from .group_execution import InferenceLimitError

if TYPE_CHECKING:
    from .forward import InferenceSession


@dataclass(frozen=True, slots=True)
class _ActivationOutcome:
    added_facts: tuple[Fact, ...]
    removed_facts: tuple[Fact, ...]

    @property
    def mutation_count(self) -> int:
        return len(self.added_facts) + len(self.removed_facts)


def _assume(
    session: InferenceSession,
    facts: tuple[Fact, ...],
    label: str,
) -> tuple[Fact, ...]:
    added: list[Fact] = []
    for fact in facts:
        session._provenance.assume(fact)
        session._assumed_facts.add(fact)
        if not session._store.add(fact):
            continue
        session._reserve_fact_atoms(fact)
        session._next_time_tag += 1
        session._set_fact_time_tag(fact, session._next_time_tag)
        added.append(fact)
        session._events.append(
            InferenceEvent(
                sequence=len(session._events) + 1,
                kind=FactMutationKind.ADD,
                fact=fact,
                rule_name=f"<{label}>",
                rule_group="<assumptions>",
                substitution=EMPTY_SUBSTITUTION,
                premises=(),
                cycle=session._cycles,
            )
        )
    if len(session._store) > session.limits.max_facts:
        raise InferenceLimitError(
            f"maximum fact count ({session.limits.max_facts}) exceeded"
        )
    if added and session._negative_refraction_plans:
        session._reconcile_negative_refraction(tuple(added))
    return tuple(added)


def _retract(
    session: InferenceSession,
    facts: tuple[Fact, ...],
    label: str,
) -> tuple[Fact, ...]:
    removed: list[Fact] = []
    for fact in facts:
        session._assumed_facts.discard(fact)
        if not session._store.remove(fact):
            continue
        session._set_fact_time_tag(fact, None)
        removed.append(fact)
        session._record_external_removal(fact, label)
    if session.truth_maintenance and removed:
        removed.extend(session._cascade_unsupported())
    absent = frozenset(removed)
    if absent:
        session.strategy.invalidate(absent)
        session._expire_removed_supports(absent)
    return tuple(removed)


def _fire_activation(
    session: InferenceSession,
    group: RuleGroup,
    rule: Rule,
    substitution: Substitution,
    premise_facts: tuple[Fact, ...],
) -> _ActivationOutcome:
    staged: list[tuple[FactMutationKind, Fact, Substitution]] = []
    session._stage_actions(rule.actions, substitution, staged)

    added: list[Fact] = []
    removed: list[Fact] = []
    for kind, fact, action_substitution in staged:
        if kind is FactMutationKind.ADD:
            derivation = session._provenance.record(
                fact,
                rule.name,
                action_substitution,
                premise_facts,
                session._cycles,
                rule_group=group.name,
            )
            session._derivations.append(derivation)
            if not session._store.add(fact):
                continue
            session._next_time_tag += 1
            session._set_fact_time_tag(fact, session._next_time_tag)
            added.append(fact)
            if len(session._store) > session.limits.max_facts:
                raise InferenceLimitError(
                    f"maximum fact count ({session.limits.max_facts}) exceeded"
                )
        elif session._store.remove(fact):
            session._assumed_facts.discard(fact)
            session._set_fact_time_tag(fact, None)
            removed.append(fact)
        else:
            continue
        session._events.append(
            InferenceEvent(
                sequence=len(session._events) + 1,
                kind=kind,
                fact=fact,
                rule_name=rule.name,
                rule_group=group.name,
                substitution=action_substitution,
                premises=premise_facts,
                cycle=session._cycles,
            )
        )

    if session.truth_maintenance and removed:
        removed.extend(session._cascade_unsupported())
    if removed:
        absent_after_activation = frozenset(
            fact for fact in removed if fact not in session._store
        )
        if absent_after_activation:
            session.strategy.invalidate(absent_after_activation)
        session._expire_removed_supports(absent_after_activation)
    present_additions = tuple(
        fact for fact in added if fact in session._store
    )
    if present_additions and session._negative_refraction_plans:
        session._reconcile_negative_refraction(present_additions)
    return _ActivationOutcome(tuple(added), tuple(removed))


def _cascade_unsupported(session: InferenceSession) -> list[Fact]:
    """Retract facts outside the grounded positive justification closure."""

    current = frozenset(session._store.facts)
    supported = {
        fact
        for fact in current
        if fact in session._initial_facts or fact in session._assumed_facts
    }
    changed = True
    while changed:
        changed = False
        for fact in current - supported:
            if any(
                all(premise in supported for premise in derivation.premises)
                for derivation in session._provenance.derivations(fact)
            ):
                supported.add(fact)
                changed = True
    cascaded: list[Fact] = []
    for fact in session._store.facts:
        if fact in supported or not session._store.remove(fact):
            continue
        session._set_fact_time_tag(fact, None)
        cascaded.append(fact)
        session._record_external_removal(fact, "tms")
    return cascaded


def _record_external_removal(
    session: InferenceSession,
    fact: Fact,
    label: str,
) -> None:
    session._events.append(
        InferenceEvent(
            sequence=len(session._events) + 1,
            kind=FactMutationKind.REMOVE,
            fact=fact,
            rule_name=f"<{label}>",
            rule_group="<truth-maintenance>",
            substitution=EMPTY_SUBSTITUTION,
            premises=(),
            cycle=session._cycles,
        )
    )


def _stage_actions(
    session: InferenceSession,
    actions: tuple[Action, ...],
    substitution: Substitution,
    staged: list[tuple[FactMutationKind, Fact, Substitution]],
) -> Substitution:
    action_substitution = substitution
    for action in actions:
        if isinstance(action, Let):
            action_substitution = action.apply(action_substitution)
            continue
        if isinstance(action, Fresh):
            value = session._next_fresh_atom(action.prefix)
            action_substitution = action.apply(action_substitution, value)
            continue
        if isinstance(action, AddFact):
            fact = action.instantiate(action_substitution)
            session._reserve_fact_atoms(fact)
            staged.append(
                (FactMutationKind.ADD, fact, action_substitution)
            )
            continue
        if isinstance(action, RemoveFact):
            staged.append(
                (
                    FactMutationKind.REMOVE,
                    action.instantiate(action_substitution),
                    action_substitution,
                )
            )
            continue
        if isinstance(action, ForEach):
            collection = action_substitution.apply(action.collection)
            if not isinstance(collection, (FiniteSet, FiniteSequence)):
                raise TypeError(
                    "FOR EACH collection must be a ground finite "
                    "set or sequence"
                )
            if action.variable in action_substitution:
                raise ValueError(
                    f"FOR EACH variable ${action.variable.name} "
                    "is already bound"
                )
            for element in collection.elements:
                session._stage_actions(
                    action.actions,
                    action_substitution.bind(action.variable, element),
                    staged,
                )
            continue
        if isinstance(action, Choice):
            raise RuntimeError(
                "CHOICE actions require RuleChoiceProvider and "
                "SessionChoiceSearch"
            )
        raise TypeError(f"unsupported action: {action!r}")
    return action_substitution


def _next_fresh_atom(session: InferenceSession, prefix: str) -> Atom:
    counter = session._fresh_counters.get(prefix, 0)
    while True:
        counter += 1
        name = f"{prefix}-{counter}"
        if name not in session._reserved_atom_names:
            session._fresh_counters[prefix] = counter
            session._reserved_atom_names.add(name)
            return Atom(name)


def _reserve_fact_atoms(session: InferenceSession, fact: Fact) -> None:
    session._reserved_atom_names.update(_atom_names_in(fact.entity))
    session._reserved_atom_names.update(_atom_names_in(fact.status))


def _atom_names_in(term: Term) -> tuple[str, ...]:
    if isinstance(term, Atom):
        return (term.name,)
    if isinstance(term, Triple):
        return (
            *_atom_names_in(term.subject),
            *_atom_names_in(term.relation),
            *_atom_names_in(term.object),
        )
    if isinstance(term, FiniteSet):
        return tuple(
            name
            for element in term.elements
            for name in _atom_names_in(element)
        )
    if isinstance(term, FiniteSequence):
        return tuple(
            name
            for element in term.elements
            for name in _atom_names_in(element)
        )
    return ()
