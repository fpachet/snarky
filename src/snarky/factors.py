"""Pure weighted factors evaluated over an immutable fact snapshot.

Factors deliberately have no actions.  They query facts, identify one or more
ground scopes, and contribute a learned log weight exactly once per grounding.
They are therefore separate from forward rules, hard constraints, and CHOICE.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .actions import AddFact
from .facts import Fact
from .instantiation import InstantiationStrategy, SemiNaiveInstantiationStrategy
from .premises import Premise, validate_premise_bindings
from .rules import Rule
from .terms import Atom, Term, is_ground, variables_in


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    """One side-effect-free Boolean predicate and its grounding scope."""

    name: str
    scope: Term
    premises: tuple[Premise, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a factor name cannot be empty")
        premises = tuple(self.premises)
        if not premises:
            raise ValueError(f"factor {self.name!r} must contain a premise")
        bound = validate_premise_bindings(
            premises,
            require_bound_comparisons=True,
        )
        missing = variables_in(self.scope) - bound
        if missing:
            names = ", ".join(
                f"${variable.name}"
                for variable in sorted(missing, key=lambda item: item.name)
            )
            raise ValueError(
                f"factor {self.name!r} scope uses unbound variables: {names}"
            )
        object.__setattr__(self, "premises", premises)


@dataclass(frozen=True, slots=True)
class FactorParameter:
    """A learned parameter kept separate from the factor predicate."""

    factor_name: str
    log_weight: float

    def __post_init__(self) -> None:
        if not self.factor_name:
            raise ValueError("a factor parameter needs a factor name")
        value = float(self.log_weight)
        if not math.isfinite(value):
            raise ValueError("a factor log weight must be finite")
        object.__setattr__(self, "log_weight", value)


@dataclass(frozen=True, slots=True)
class WeightedFactor:
    """A factor definition paired with one learned parameter."""

    definition: FactorDefinition
    parameter: FactorParameter

    def __post_init__(self) -> None:
        if self.definition.name != self.parameter.factor_name:
            raise ValueError("factor definition and parameter names must be identical")

    @property
    def name(self) -> str:
        return self.definition.name


@dataclass(frozen=True, slots=True)
class FactorGroup:
    """A closed set of learned factors, never a forward-chaining group."""

    name: str
    factors: tuple[WeightedFactor, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a factor group name cannot be empty")
        factors = tuple(self.factors)
        names = [factor.name for factor in factors]
        if len(names) != len(set(names)):
            raise ValueError(
                f"factor group {self.name!r} contains duplicate factor names"
            )
        object.__setattr__(self, "factors", factors)


@dataclass(frozen=True, slots=True)
class FactorModel:
    """An ordered collection of factor groups with globally unique names."""

    name: str
    groups: tuple[FactorGroup, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a factor model name cannot be empty")
        groups = tuple(self.groups)
        group_names = [group.name for group in groups]
        if len(group_names) != len(set(group_names)):
            raise ValueError("a factor model contains duplicate group names")
        factor_names = [factor.name for group in groups for factor in group.factors]
        if len(factor_names) != len(set(factor_names)):
            raise ValueError("a factor model contains duplicate factor names")
        object.__setattr__(self, "groups", groups)


@dataclass(frozen=True, slots=True)
class FactorActivation:
    """One true factor grounding and its immutable explanation."""

    factor_name: str
    group_name: str
    scope: Term
    log_weight: float
    support_facts: tuple[Fact, ...]
    witness_count: int = 1

    @property
    def contribution(self) -> float:
        return self.log_weight


@dataclass(frozen=True, slots=True)
class FactorEvaluation:
    """The complete activation vector and additive log score."""

    model_name: str
    activations: tuple[FactorActivation, ...]

    @property
    def log_score(self) -> float:
        return sum(activation.contribution for activation in self.activations)

    def for_scope(self, scope: Term) -> tuple[FactorActivation, ...]:
        return tuple(
            activation for activation in self.activations if activation.scope == scope
        )

    def score_for_scope(self, scope: Term) -> float:
        return sum(activation.contribution for activation in self.for_scope(scope))


def evaluate_factor_model(
    model: FactorModel,
    facts: Sequence[Fact],
    *,
    strategy: InstantiationStrategy | None = None,
) -> FactorEvaluation:
    """Evaluate a model without mutating facts or producing derived facts."""

    query_strategy = strategy or SemiNaiveInstantiationStrategy()
    snapshot = tuple(facts)
    activations: list[FactorActivation] = []
    for group in model.groups:
        for factor in group.factors:
            query = Rule(
                f"__factor_query__{group.name}__{factor.name}",
                factor.definition.premises,
                (AddFact(Atom("__factor_query_result__")),),
            )
            matches = query_strategy.instantiate(query, snapshot)
            grounded: dict[Term, tuple[list[Fact], int]] = {}
            for match in matches:
                scope = match.substitution.apply(factor.definition.scope)
                if not is_ground(scope):
                    raise ValueError(
                        f"factor {factor.name!r} produced a non-ground scope"
                    )
                support, count = grounded.setdefault(scope, ([], 0))
                for fact in match.premise_facts:
                    if fact not in support:
                        support.append(fact)
                grounded[scope] = (support, count + 1)
            for scope, (support, count) in grounded.items():
                activations.append(
                    FactorActivation(
                        factor_name=factor.name,
                        group_name=group.name,
                        scope=scope,
                        log_weight=factor.parameter.log_weight,
                        support_facts=tuple(support),
                        witness_count=count,
                    )
                )
    return FactorEvaluation(model.name, tuple(activations))


def factor(
    name: str,
    scope: Term,
    premises: tuple[Premise, ...],
    *,
    log_weight: float,
) -> WeightedFactor:
    """Construct one weighted factor while preserving parameter separation."""

    return WeightedFactor(
        FactorDefinition(name, scope, premises),
        FactorParameter(name, log_weight),
    )
