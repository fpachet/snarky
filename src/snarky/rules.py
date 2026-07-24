"""Rule model and public premise helper."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .actions import Action, Choice, ForEach, Fresh, Let
from .expressions import variables_in_arithmetic
from .premises import (
    CollectPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
    validate_premise_bindings,
)
from .terms import Status, Term, Variable, variables_in


@dataclass(frozen=True, slots=True)
class Rule:
    """An ordered set of premises followed by working-memory actions."""

    name: str
    premises: tuple[Premise, ...]
    actions: tuple[Action, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule name cannot be empty")
        if not self.premises:
            raise ValueError(f"rule {self.name!r} must contain a premise")
        if not self.actions:
            raise ValueError(f"rule {self.name!r} must contain an action")
        premises = tuple(self.premises)
        focused = [
            premise
            for premise in premises
            if isinstance(premise, FactPremise) and premise.focused
        ]
        if len(focused) > 1:
            raise ValueError(
                f"rule {self.name!r} may declare at most one FOCUS premise"
            )
        if any(_nested_focus(premise) for premise in premises):
            raise ValueError(
                f"rule {self.name!r} may only FOCUS a top-level premise"
            )
        bound = validate_premise_bindings(premises)
        _validate_choice_bindings(tuple(self.actions), bound)
        object.__setattr__(self, "premises", premises)
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class RuleGroup:
    """A named set of rules that can be executed as one control unit."""

    name: str
    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a rule group name cannot be empty")
        rules = tuple(self.rules)
        names = [rule.name for rule in rules]
        if len(set(names)) != len(names):
            raise ValueError(f"rule group {self.name!r} contains duplicate rule names")
        object.__setattr__(self, "rules", rules)


def when(entity: Term, status: Term = Status.VRAI) -> FactPremise:
    """Public convenience constructor for a positive fact premise."""

    return FactPremise(entity, status)


def _nested_focus(premise: Premise) -> bool:
    if not isinstance(
        premise,
        (
            ExistsPremise,
            NotExistsPremise,
            CountPremise,
            UniquePremise,
            CollectPremise,
        ),
    ):
        return False
    return any(
        (
            isinstance(item, FactPremise)
            and item.focused
            or _nested_focus(item)
        )
        for item in premise.premises
    )


def _validate_choice_bindings(
    actions: tuple[Action, ...],
    initially_bound: frozenset[Variable],
) -> frozenset[Variable]:
    bound = set(initially_bound)
    for action in actions:
        if isinstance(action, Let):
            missing = variables_in_arithmetic(action.expression) - bound
            if missing:
                raise ValueError(
                    "LET before CHOICE uses unbound variables: "
                    + _variable_names(missing)
                )
            bound.add(action.variable)
            continue
        if isinstance(action, Fresh):
            bound.add(action.variable)
            continue
        if isinstance(action, Choice):
            nested_bound = validate_premise_bindings(
                action.premises,
                frozenset(bound),
                require_bound_comparisons=True,
            )
            required = (
                variables_in(action.entity)
                | variables_in(action.status)
                | variables_in(action.weight)
            )
            missing = required - nested_bound
            if missing:
                raise ValueError(
                    "CHOICE target or weight uses unbound variables: "
                    + _variable_names(missing)
                )
            bound.update(nested_bound)
            continue
        if isinstance(action, ForEach):
            loop_bound = set(bound)
            loop_bound.add(action.variable)
            _validate_choice_bindings(
                action.actions,
                frozenset(loop_bound),
            )
    return frozenset(bound)


def _variable_names(variables: set[Variable] | frozenset[Variable]) -> str:
    return ", ".join(
        f"${variable.name}"
        for variable in sorted(variables, key=lambda item: item.name)
    )
