"""Deterministic forward chaining, persistent sessions, and rule groups."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ..actions import AddFact, Let
from ..facts import Fact
from ..instantiation import (
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from ..matching import PatternMatcher
from ..premises import FactPremise
from ..rules import Rule, RuleGroup
from ..stores.naive import NaiveFactStore
from ..substitutions import EMPTY_SUBSTITUTION, Substitution
from ..terms import Term
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
        self._derivations: list[Derivation] = []
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
            fired_activation_count=len(self._fired),
            provenance=self._provenance,
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

        start_fact_count = len(self._store)
        start_derivation_count = len(self._derivations)
        start_fired_count = len(self._fired)
        if until is not None and until(self):
            return self._group_result(
                group,
                mode,
                start_fact_count,
                start_derivation_count,
                start_fired_count,
                cycles=0,
                stop_reason=GroupStopReason.CONDITION_MET,
            )

        for local_cycle in range(1, self.limits.max_cycles + 1):
            self._cycles += 1
            added_this_cycle = 0
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
                    key = ActivationKey(
                        group.name,
                        rule.name,
                        activation.substitution.key,
                    )
                    if key in self._fired:
                        continue
                    self._fired.add(key)
                    activation_added = self._fire_activation(
                        group,
                        rule,
                        activation.substitution,
                        activation.premise_facts,
                    )
                    added_this_cycle += activation_added

                    if until is not None and until(self):
                        return self._group_result(
                            group,
                            mode,
                            start_fact_count,
                            start_derivation_count,
                            start_fired_count,
                            cycles=local_cycle,
                            stop_reason=GroupStopReason.CONDITION_MET,
                        )
                    if (
                        mode is GroupExecutionMode.FIRST_CHANGE
                        and activation_added
                    ):
                        return self._group_result(
                            group,
                            mode,
                            start_fact_count,
                            start_derivation_count,
                            start_fired_count,
                            cycles=local_cycle,
                            stop_reason=GroupStopReason.FIRST_CHANGE,
                        )

            if mode is GroupExecutionMode.ONE_CYCLE:
                return self._group_result(
                    group,
                    mode,
                    start_fact_count,
                    start_derivation_count,
                    start_fired_count,
                    cycles=local_cycle,
                    stop_reason=GroupStopReason.ONE_CYCLE,
                )
            if added_this_cycle == 0:
                return self._group_result(
                    group,
                    mode,
                    start_fact_count,
                    start_derivation_count,
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
    ) -> int:
        action_substitution = substitution
        added = 0
        for action in rule.actions:
            if isinstance(action, Let):
                action_substitution = action.apply(action_substitution)
                continue
            if not isinstance(action, AddFact):
                raise TypeError(f"unsupported action: {action!r}")
            fact = action.instantiate(action_substitution)
            derivation = self._provenance.record(
                fact,
                rule.name,
                action_substitution,
                premise_facts,
                self._cycles,
                rule_group=group.name,
            )
            self._derivations.append(derivation)
            if self._store.add(fact):
                added += 1
                if len(self._store) > self.limits.max_facts:
                    raise InferenceLimitError(
                        f"maximum fact count ({self.limits.max_facts}) exceeded"
                    )
        return added

    def _group_result(
        self,
        group: RuleGroup,
        mode: GroupExecutionMode,
        start_fact_count: int,
        start_derivation_count: int,
        start_fired_count: int,
        *,
        cycles: int,
        stop_reason: GroupStopReason,
    ) -> GroupRunResult:
        facts = self._store.facts
        return GroupRunResult(
            group_name=group.name,
            mode=mode,
            facts=facts,
            added_facts=facts[start_fact_count:],
            derivations=tuple(self._derivations[start_derivation_count:]),
            cycles=cycles,
            fired_activation_count=len(self._fired) - start_fired_count,
            stop_reason=stop_reason,
            provenance=self._provenance,
        )


class ForwardEngine:
    """Monotone engine with semi-naïve instantiation and refraction by default."""

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
