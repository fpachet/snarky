"""Deterministic forward chaining, persistent sessions, and rule groups."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import Protocol

from ..actions import AddFact, Let, RemoveFact
from ..facts import Fact
from ..instantiation import (
    IndexedInstantiationStrategy,
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from ..matching import PatternMatcher
from ..premises import ExistsPremise, FactPremise, NotExistsPremise, Premise
from ..rules import Rule, RuleGroup
from ..stores.naive import NaiveFactStore
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import Term
from .events import FactMutationKind, InferenceEvent
from .provenance import Derivation, Provenance


class InferenceLimitError(RuntimeError):
    """Raised when a configured execution guard is exceeded."""


@dataclass(frozen=True, slots=True)
class EngineLimits:
    max_cycles: int = 1_000
    max_facts: int = 100_000

    def __post_init__(self) -> None:
        if self.max_cycles < 1 or self.max_facts < 1:
            raise ValueError("engine limits must be positive")


@dataclass(frozen=True, slots=True)
class ActivationKey:
    rule_group: str
    rule_name: str
    substitution: tuple[tuple[str, Term], ...]


class GroupExecutionMode(StrEnum):
    """Ways to execute a rule group within a persistent session."""

    SATURATE = "saturate"
    ONE_CYCLE = "one_cycle"
    FIRST_CHANGE = "first_change"
    UNTIL = "until"


class GroupStopReason(StrEnum):
    """Reason why a rule-group invocation returned."""

    FIXED_POINT = "fixed_point"
    ONE_CYCLE = "one_cycle"
    FIRST_CHANGE = "first_change"
    CONDITION_MET = "condition_met"


class StopCondition(Protocol):
    """Condition evaluated against a persistent inference session."""

    def __call__(self, session: InferenceSession, /) -> bool: ...


@dataclass(frozen=True, slots=True)
class FactExists:
    """Stop when at least one fact matches a fact premise."""

    premise: FactPremise

    def __call__(self, session: InferenceSession, /) -> bool:
        matcher = PatternMatcher()
        return any(
            self.premise.match(fact, EMPTY_SUBSTITUTION, matcher) is not None
            for fact in session.facts
        )


@dataclass(frozen=True, slots=True)
class RunResult:
    facts: tuple[Fact, ...]
    derived_facts: tuple[Fact, ...]
    derivations: tuple[Derivation, ...]
    cycles: int
    fired_activation_count: int
    provenance: Provenance
    events: tuple[InferenceEvent, ...] = ()


@dataclass(frozen=True, slots=True)
class GroupRunResult:
    """Observable result of one rule-group invocation."""

    group_name: str
    mode: GroupExecutionMode
    facts: tuple[Fact, ...]
    added_facts: tuple[Fact, ...]
    derivations: tuple[Derivation, ...]
    cycles: int
    fired_activation_count: int
    stop_reason: GroupStopReason
    provenance: Provenance
    removed_facts: tuple[Fact, ...] = ()
    events: tuple[InferenceEvent, ...] = ()

    @property
    def changed(self) -> bool:
        """Return whether this invocation mutated the working memory."""

        return bool(self.events)

    @property
    def mutation_count(self) -> int:
        """Return the number of effective additions and removals."""

        return len(self.events)


@dataclass(frozen=True, slots=True)
class _ActivationOutcome:
    added_facts: tuple[Fact, ...]
    removed_facts: tuple[Fact, ...]

    @property
    def mutation_count(self) -> int:
        return len(self.added_facts) + len(self.removed_facts)


class InferenceSession:
    """Persistent working memory shared by successive rule-group invocations."""

    def __init__(
        self,
        initial_facts: tuple[Fact, ...],
        strategy: InstantiationStrategy | None = None,
        limits: EngineLimits | None = None,
    ) -> None:
        self.strategy = (
            strategy
            if strategy is not None
            else SemiNaiveInstantiationStrategy()
        )
        self.limits = limits or EngineLimits()
        self._store = NaiveFactStore(initial_facts)
        self._provenance = Provenance(self._store.facts)
        self._initial_facts = frozenset(self._store.facts)
        self._fired: set[ActivationKey] = set()
        self._fired_supports: dict[ActivationKey, tuple[Fact, ...]] = {}
        self._fired_activation_total = 0
        self._derivations: list[Derivation] = []
        self._events: list[InferenceEvent] = []
        self._previous_fact_counts: dict[tuple[str, str], int] = {}
        self._groups: dict[str, RuleGroup] = {}
        self._cycles = 0

    @property
    def facts(self) -> tuple[Fact, ...]:
        """Return the current insertion-ordered fact snapshot."""

        return self._store.facts

    @property
    def provenance(self) -> Provenance:
        """Return cumulative provenance for the session."""

        return self._provenance

    @property
    def events(self) -> tuple[InferenceEvent, ...]:
        """Return the cumulative chronological mutation journal."""

        return tuple(self._events)

    def snapshot(self) -> RunResult:
        """Return the cumulative state using the historical result shape."""

        facts = self._store.facts
        return RunResult(
            facts=facts,
            derived_facts=tuple(
                fact for fact in facts if fact not in self._initial_facts
            ),
            derivations=tuple(self._derivations),
            cycles=self._cycles,
            fired_activation_count=self._fired_activation_total,
            provenance=self._provenance,
            events=tuple(self._events),
        )

    def run_group(
        self,
        group: RuleGroup,
        *,
        mode: GroupExecutionMode = GroupExecutionMode.SATURATE,
        until: StopCondition | None = None,
    ) -> GroupRunResult:
        """Execute *group* according to *mode* while preserving session state."""

        if mode is GroupExecutionMode.UNTIL and until is None:
            raise ValueError("UNTIL mode requires a stop condition")
        if mode is not GroupExecutionMode.UNTIL and until is not None:
            raise ValueError("a stop condition is only valid in UNTIL mode")
        registered = self._groups.setdefault(group.name, group)
        if registered != group:
            raise ValueError(
                f"rule group {group.name!r} was already registered "
                "with a different definition"
            )

        start_derivation_count = len(self._derivations)
        start_event_count = len(self._events)
        start_fired_count = self._fired_activation_total
        if until is not None and until(self):
            return self._group_result(
                group,
                mode,
                start_derivation_count,
                start_event_count,
                start_fired_count,
                cycles=0,
                stop_reason=GroupStopReason.CONDITION_MET,
            )

        for local_cycle in range(1, self.limits.max_cycles + 1):
            self._cycles += 1
            mutations_this_cycle = 0
            for rule in group.rules:
                facts_snapshot = self._store.facts
                state_key = (group.name, rule.name)
                previous_count = self._previous_fact_counts.get(state_key)
                delta = (
                    None
                    if previous_count is None
                    else facts_snapshot[previous_count:]
                )
                self._previous_fact_counts[state_key] = len(facts_snapshot)
                for activation in self.strategy.instantiate(
                    rule,
                    facts_snapshot,
                    delta,
                ):
                    if any(
                        fact not in self._store
                        for fact in activation.premise_facts
                    ):
                        continue
                    key = ActivationKey(
                        group.name,
                        rule.name,
                        activation.substitution.key,
                    )
                    if key in self._fired:
                        continue
                    self._fired.add(key)
                    self._fired_supports[key] = activation.premise_facts
                    self._fired_activation_total += 1
                    outcome = self._fire_activation(
                        group,
                        rule,
                        activation.substitution,
                        activation.premise_facts,
                    )
                    mutations_this_cycle += outcome.mutation_count

                    if until is not None and until(self):
                        return self._group_result(
                            group,
                            mode,
                            start_derivation_count,
                            start_event_count,
                            start_fired_count,
                            cycles=local_cycle,
                            stop_reason=GroupStopReason.CONDITION_MET,
                        )
                    if (
                        mode is GroupExecutionMode.FIRST_CHANGE
                        and outcome.mutation_count
                    ):
                        return self._group_result(
                            group,
                            mode,
                            start_derivation_count,
                            start_event_count,
                            start_fired_count,
                            cycles=local_cycle,
                            stop_reason=GroupStopReason.FIRST_CHANGE,
                        )

            if mode is GroupExecutionMode.ONE_CYCLE:
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.ONE_CYCLE,
                )
            if mutations_this_cycle == 0:
                return self._group_result(
                    group,
                    mode,
                    start_derivation_count,
                    start_event_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.FIXED_POINT,
                )

        raise InferenceLimitError(
            f"rule group {group.name!r} did not stop after "
            f"{self.limits.max_cycles} cycles"
        )

    def _fire_activation(
        self,
        group: RuleGroup,
        rule: Rule,
        substitution: Substitution,
        premise_facts: tuple[Fact, ...],
    ) -> _ActivationOutcome:
        action_substitution = substitution
        staged: list[tuple[FactMutationKind, Fact]] = []
        for action in rule.actions:
            if isinstance(action, Let):
                action_substitution = action.apply(action_substitution)
                continue
            if isinstance(action, AddFact):
                staged.append(
                    (
                        FactMutationKind.ADD,
                        action.instantiate(action_substitution),
                    )
                )
                continue
            if isinstance(action, RemoveFact):
                staged.append(
                    (
                        FactMutationKind.REMOVE,
                        action.instantiate(action_substitution),
                    )
                )
                continue
            raise TypeError(f"unsupported action: {action!r}")

        added: list[Fact] = []
        removed: list[Fact] = []
        for kind, fact in staged:
            if kind is FactMutationKind.ADD:
                derivation = self._provenance.record(
                    fact,
                    rule.name,
                    action_substitution,
                    premise_facts,
                    self._cycles,
                    rule_group=group.name,
                )
                self._derivations.append(derivation)
                if not self._store.add(fact):
                    continue
                added.append(fact)
                if len(self._store) > self.limits.max_facts:
                    raise InferenceLimitError(
                        f"maximum fact count ({self.limits.max_facts}) exceeded"
                    )
            elif self._store.remove(fact):
                removed.append(fact)
            else:
                continue
            self._events.append(
                InferenceEvent(
                    sequence=len(self._events) + 1,
                    kind=kind,
                    fact=fact,
                    rule_name=rule.name,
                    rule_group=group.name,
                    substitution=action_substitution,
                    premises=premise_facts,
                    cycle=self._cycles,
                )
            )

        if removed:
            self._previous_fact_counts.clear()
            absent_after_activation = frozenset(
                fact for fact in removed if fact not in self._store
            )
            if absent_after_activation:
                self.strategy.invalidate(absent_after_activation)
            self._expire_removed_supports(absent_after_activation)
        present_additions = tuple(
            fact for fact in added if fact in self._store
        )
        if present_additions:
            self._reconcile_negative_refraction(present_additions)
        return _ActivationOutcome(tuple(added), tuple(removed))

    def _expire_removed_supports(self, removed: frozenset[Fact]) -> None:
        expired = {
            key
            for key, supports in self._fired_supports.items()
            if any(fact in removed for fact in supports)
        }
        self._fired.difference_update(expired)
        for key in expired:
            self._fired_supports.pop(key, None)

    def _reconcile_negative_refraction(
        self,
        added: tuple[Fact, ...],
    ) -> None:
        """Expire fired negative activations invalidated by fact additions."""

        oracle = IndexedInstantiationStrategy()
        facts = self._store.facts
        matcher = PatternMatcher()
        for group in self._groups.values():
            for rule in group.rules:
                fired_for_rule = {
                    key
                    for key in self._fired
                    if (
                        key.rule_group == group.name
                        and key.rule_name == rule.name
                    )
                }
                negative_dependencies = _negative_fact_premises(rule.premises)
                if (
                    not fired_for_rule
                    or not negative_dependencies
                    or not any(
                        premise.match(
                            fact,
                            EMPTY_SUBSTITUTION,
                            matcher,
                        )
                        is not None
                        for premise in negative_dependencies
                        for fact in added
                    )
                ):
                    continue
                active: set[ActivationKey] = set()
                for activation in oracle.instantiate(rule, facts):
                    active.add(
                        ActivationKey(
                            group.name,
                            rule.name,
                            activation.substitution.key,
                        )
                    )
                expired = fired_for_rule - active
                self._fired.difference_update(expired)
                for key in expired:
                    self._fired_supports.pop(key, None)

    def _group_result(
        self,
        group: RuleGroup,
        mode: GroupExecutionMode,
        start_derivation_count: int,
        start_event_count: int,
        start_fired_count: int,
        *,
        cycles: int,
        stop_reason: GroupStopReason,
    ) -> GroupRunResult:
        facts = self._store.facts
        events = tuple(self._events[start_event_count:])
        return GroupRunResult(
            group_name=group.name,
            mode=mode,
            facts=facts,
            added_facts=tuple(
                event.fact
                for event in events
                if event.kind is FactMutationKind.ADD
            ),
            derivations=tuple(self._derivations[start_derivation_count:]),
            cycles=cycles,
            fired_activation_count=(
                self._fired_activation_total - start_fired_count
            ),
            stop_reason=stop_reason,
            provenance=self._provenance,
            removed_facts=tuple(
                event.fact
                for event in events
                if event.kind is FactMutationKind.REMOVE
            ),
            events=events,
        )


class ForwardEngine:
    """Forward engine with semi-naïve instantiation and refraction by default."""

    def __init__(
        self,
        rules: tuple[Rule, ...],
        strategy: InstantiationStrategy | None = None,
        limits: EngineLimits | None = None,
    ) -> None:
        self.rules = tuple(rules)
        self.default_group = RuleGroup("default", self.rules)
        self.strategy = (
            strategy
            if strategy is not None
            else SemiNaiveInstantiationStrategy()
        )
        self.limits = limits or EngineLimits()

    def create_session(
        self,
        initial_facts: tuple[Fact, ...],
    ) -> InferenceSession:
        """Create a persistent session using this engine's strategy and limits."""

        return InferenceSession(initial_facts, self.strategy, self.limits)

    def run(self, initial_facts: tuple[Fact, ...]) -> RunResult:
        session = self.create_session(initial_facts)
        session.run_group(self.default_group)
        return session.snapshot()


@cache
def _negative_fact_premises(
    premises: tuple[Premise, ...],
    *,
    inside_negative: bool = False,
) -> tuple[FactPremise, ...]:
    dependencies: list[FactPremise] = []
    for premise in premises:
        if isinstance(premise, FactPremise):
            if inside_negative:
                dependencies.append(premise)
            continue
        if isinstance(premise, NotExistsPremise):
            dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=True,
                )
            )
            continue
        if isinstance(premise, ExistsPremise):
            dependencies.extend(
                _negative_fact_premises(
                    premise.premises,
                    inside_negative=inside_negative,
                )
            )
    return tuple(dependencies)
