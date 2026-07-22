"""Deterministic recursive forward chaining to a fixed point."""

from __future__ import annotations

from dataclasses import dataclass

from ..facts import Fact
from ..instantiation.naive_join import NaiveInstantiationStrategy
from ..rules import Rule
from ..stores.naive import NaiveFactStore
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
    rule_name: str
    substitution: tuple[tuple[str, Term], ...]


@dataclass(frozen=True, slots=True)
class RunResult:
    facts: tuple[Fact, ...]
    derived_facts: tuple[Fact, ...]
    derivations: tuple[Derivation, ...]
    cycles: int
    fired_activation_count: int
    provenance: Provenance


class ForwardEngine:
    """Reference monotone engine using naïve instantiation and refraction."""

    def __init__(
        self,
        rules: tuple[Rule, ...],
        strategy: NaiveInstantiationStrategy | None = None,
        limits: EngineLimits | None = None,
    ) -> None:
        self.rules = tuple(rules)
        self.strategy = strategy or NaiveInstantiationStrategy()
        self.limits = limits or EngineLimits()

    def run(self, initial_facts: tuple[Fact, ...]) -> RunResult:
        store = NaiveFactStore(initial_facts)
        provenance = Provenance(store.facts)
        initial_set = frozenset(store.facts)
        fired: set[ActivationKey] = set()
        derivations: list[Derivation] = []

        for cycle in range(1, self.limits.max_cycles + 1):
            added_this_cycle = 0
            for rule in self.rules:
                facts_snapshot = store.facts
                for activation in self.strategy.instantiate(rule, facts_snapshot):
                    key = ActivationKey(rule.name, activation.substitution.key)
                    if key in fired:
                        continue
                    fired.add(key)
                    for action in rule.actions:
                        fact = action.instantiate(activation.substitution)
                        derivation = provenance.record(
                            fact,
                            rule.name,
                            activation.substitution,
                            activation.premise_facts,
                            cycle,
                        )
                        derivations.append(derivation)
                        if store.add(fact):
                            added_this_cycle += 1
                            if len(store) > self.limits.max_facts:
                                raise InferenceLimitError(
                                    "maximum fact count "
                                    f"({self.limits.max_facts}) exceeded"
                                )
            if added_this_cycle == 0:
                derived = tuple(fact for fact in store if fact not in initial_set)
                return RunResult(
                    store.facts,
                    derived,
                    tuple(derivations),
                    cycle,
                    len(fired),
                    provenance,
                )
        raise InferenceLimitError(
            f"fixed point not reached after {self.limits.max_cycles} cycles"
        )
