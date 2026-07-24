"""Parameterized rule groups and bounded recursive group procedures."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .actions import Action, AddFact, ForEach, Fresh, Let, RemoveFact
from .computed import ComputedPremise
from .engine import (
    GroupExecutionMode,
    GroupRunResult,
    InferenceSession,
    StopCondition,
)
from .expressions import (
    BinaryArithmeticExpression,
    DistinctCountExpression,
    NumericExpression,
    UnaryArithmeticExpression,
)
from .premises import (
    BindPremise,
    CollectPremise,
    CombinationsPremise,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from .rules import Rule, RuleGroup
from .substitutions import EMPTY_SUBSTITUTION, Substitution
from .terms import Number, Term, Variable, is_ground, render_term


@dataclass(frozen=True, slots=True)
class RuleGroupTemplate:
    """A rule group whose declared variables are construction parameters."""

    name: str
    parameters: tuple[Variable, ...]
    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        parameters = tuple(self.parameters)
        if len(set(parameters)) != len(parameters):
            raise ValueError("rule-group template parameters must be unique")
        object.__setattr__(self, "parameters", parameters)
        object.__setattr__(self, "rules", tuple(self.rules))

    def instantiate(
        self,
        *arguments: Term,
        name: str | None = None,
    ) -> RuleGroup:
        """Specialize every occurrence of each parameter in the template."""

        if len(arguments) != len(self.parameters):
            raise ValueError(
                f"template {self.name!r} expects {len(self.parameters)} "
                f"arguments, got {len(arguments)}"
            )
        if not all(is_ground(argument) for argument in arguments):
            raise ValueError("rule-group template arguments must be ground")
        substitution = EMPTY_SUBSTITUTION
        for parameter, argument in zip(
            self.parameters,
            arguments,
            strict=True,
        ):
            substitution = substitution.bind(parameter, argument)
        rules = tuple(
            _specialize_rule(rule, substitution, frozenset(self.parameters))
            for rule in self.rules
        )
        rendered_arguments = ",".join(render_term(argument) for argument in arguments)
        return RuleGroup(name or f"{self.name}({rendered_arguments})", rules)


@dataclass(frozen=True, slots=True)
class GroupCall:
    """One invocation in a group procedure."""

    template: RuleGroupTemplate
    arguments: tuple[Term, ...]
    mode: GroupExecutionMode = GroupExecutionMode.SATURATE
    until: StopCondition | None = None

    def group(self) -> RuleGroup:
        return self.template.instantiate(*self.arguments)


class GroupTraversal(StrEnum):
    DEPTH_FIRST = "depth_first"
    BREADTH_FIRST = "breadth_first"


type GroupExpander = Callable[
    [GroupCall, GroupRunResult, InferenceSession],
    tuple[GroupCall, ...],
]


@dataclass(frozen=True, slots=True)
class GroupProcedureResult:
    """Observable result of a bounded parameterized group procedure."""

    runs: tuple[GroupRunResult, ...]
    calls: tuple[GroupCall, ...]


@dataclass(frozen=True, slots=True)
class RecursiveGroupProcedure:
    """Execute dynamically generated group calls with an explicit bound.

    Recursion lives in the control layer, not in rule actions. This keeps a
    rule firing atomic and makes call order and termination inspectable.
    """

    root: GroupCall
    expand: GroupExpander
    traversal: GroupTraversal = GroupTraversal.DEPTH_FIRST
    max_calls: int = 1_000

    def __post_init__(self) -> None:
        if self.max_calls < 1:
            raise ValueError("max_calls must be positive")

    def run(self, session: InferenceSession) -> GroupProcedureResult:
        pending = [self.root]
        calls: list[GroupCall] = []
        runs: list[GroupRunResult] = []
        while pending:
            if len(calls) >= self.max_calls:
                raise RuntimeError("recursive group procedure call limit reached")
            call = (
                pending.pop()
                if self.traversal is GroupTraversal.DEPTH_FIRST
                else pending.pop(0)
            )
            result = session.run_group(
                call.group(),
                mode=call.mode,
                until=call.until,
            )
            calls.append(call)
            runs.append(result)
            children = list(self.expand(call, result, session))
            if self.traversal is GroupTraversal.DEPTH_FIRST:
                pending.extend(reversed(children))
            else:
                pending.extend(children)
        return GroupProcedureResult(tuple(runs), tuple(calls))


def _specialize_rule(
    rule: Rule,
    substitution: Substitution,
    parameters: frozenset[Variable],
) -> Rule:
    return Rule(
        rule.name,
        tuple(
            _specialize_premise(premise, substitution, parameters)
            for premise in rule.premises
        ),
        tuple(
            _specialize_action(action, substitution, parameters)
            for action in rule.actions
        ),
        metadata=rule.metadata,
    )


def _specialize_premise(
    premise: Premise,
    substitution: Substitution,
    parameters: frozenset[Variable],
) -> Premise:
    if isinstance(premise, FactPremise):
        return FactPremise(
            substitution.apply(premise.entity),
            substitution.apply(premise.status),
            focused=premise.focused,
        )
    if isinstance(premise, ComparisonPremise):
        return ComparisonPremise(
            _specialize_comparison_operand(premise.left, substitution),
            premise.operator,
            _specialize_comparison_operand(premise.right, substitution),
        )
    if isinstance(premise, BindPremise):
        _require_local_binder(premise.target, parameters, "BIND")
        return BindPremise(premise.target, substitution.apply(premise.value))
    if isinstance(premise, CombinationsPremise):
        _require_local_binder(premise.target, parameters, "COMBINATIONS")
        return CombinationsPremise(
            premise.target,
            substitution.apply(premise.source),
            premise.size,
        )
    if isinstance(premise, ComputedPremise):
        if premise.target is not None:
            _require_local_binder(
                premise.target,
                parameters,
                "computed predicate",
            )
        return ComputedPremise(
            premise.predicate,
            tuple(
                substitution.apply(argument)
                for argument in premise.arguments
            ),
            premise.target,
        )
    if isinstance(premise, CollectPremise):
        _require_local_binder(premise.target, parameters, "COLLECT")
        return CollectPremise(
            premise.target,
            substitution.apply(premise.projection),
            tuple(
                _specialize_premise(item, substitution, parameters)
                for item in premise.premises
            ),
        )
    nested = tuple(
        _specialize_premise(item, substitution, parameters)
        for item in premise.premises
    )
    if isinstance(premise, ExistsPremise):
        return ExistsPremise(nested)
    if isinstance(premise, NotExistsPremise):
        return NotExistsPremise(nested)
    if isinstance(premise, CountPremise):
        return CountPremise(nested, premise.operator, premise.expected)
    if isinstance(premise, UniquePremise):
        return UniquePremise(nested)
    raise TypeError(f"unsupported premise: {premise!r}")


def _specialize_action(
    action: Action,
    substitution: Substitution,
    parameters: frozenset[Variable],
) -> Action:
    if isinstance(action, AddFact):
        return AddFact(
            substitution.apply(action.entity),
            substitution.apply(action.status),
        )
    if isinstance(action, RemoveFact):
        return RemoveFact(
            substitution.apply(action.entity),
            substitution.apply(action.status),
        )
    if isinstance(action, Let):
        _require_local_binder(action.variable, parameters, "LET")
        return Let(
            action.variable,
            _specialize_expression(action.expression, substitution),
        )
    if isinstance(action, Fresh):
        _require_local_binder(action.variable, parameters, "FRESH")
        return action
    if isinstance(action, ForEach):
        _require_local_binder(action.variable, parameters, "FOR EACH")
        return ForEach(
            action.variable,
            substitution.apply(action.collection),
            tuple(
                _specialize_action(item, substitution, parameters)
                for item in action.actions
            ),
        )
    raise TypeError(f"unsupported action: {action!r}")


def _specialize_expression(
    expression: NumericExpression,
    substitution: Substitution,
) -> NumericExpression:
    if isinstance(expression, Number):
        return expression
    if isinstance(expression, Variable):
        value = substitution.apply(expression)
        if not isinstance(value, (Number, Variable)):
            raise TypeError("arithmetic group parameters must be numeric")
        return value
    if isinstance(expression, UnaryArithmeticExpression):
        return UnaryArithmeticExpression(
            expression.operator,
            _specialize_expression(expression.operand, substitution),
        )
    if isinstance(expression, BinaryArithmeticExpression):
        return BinaryArithmeticExpression(
            _specialize_expression(expression.left, substitution),
            expression.operator,
            _specialize_expression(expression.right, substitution),
        )
    if isinstance(expression, DistinctCountExpression):
        return DistinctCountExpression(
            tuple(
                substitution.apply(value)
                for value in expression.values
            )
        )
    raise TypeError(f"unsupported expression: {expression!r}")


def _specialize_comparison_operand(
    operand: (
        Term
        | BinaryArithmeticExpression
        | UnaryArithmeticExpression
        | DistinctCountExpression
    ),
    substitution: Substitution,
) -> (
    Term
    | BinaryArithmeticExpression
    | UnaryArithmeticExpression
    | DistinctCountExpression
):
    if isinstance(
        operand,
        (
            BinaryArithmeticExpression,
            UnaryArithmeticExpression,
            DistinctCountExpression,
        ),
    ):
        return _specialize_expression(operand, substitution)
    return substitution.apply(operand)


def _require_local_binder(
    variable: Variable,
    parameters: frozenset[Variable],
    construct: str,
) -> None:
    if variable in parameters:
        raise ValueError(
            f"{construct} target ${variable.name} cannot be a group parameter"
        )
