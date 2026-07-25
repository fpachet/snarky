"""Specialized finite-domain propagators for comparison premises."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Protocol

from ..expressions import (
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    DistinctCountExpression,
    UnaryArithmeticExpression,
)
from ..premises import (
    ComparisonOperand,
    ComparisonOperator,
    ComparisonPremise,
)
from ..terms import Number, Term, Variable, is_ground
from .base import InstantiationMetrics

type MutableTermDomains = MutableMapping[Variable, set[Term]]


class DomainPropagator(Protocol):
    """Extension point for one safe finite-domain comparison propagator."""

    def accepts(self, premise: ComparisonPremise) -> bool: ...

    def revise(
        self,
        premise: ComparisonPremise,
        domains: MutableTermDomains,
        metrics: InstantiationMetrics,
    ) -> set[Variable] | None: ...


@dataclass(frozen=True, slots=True)
class _SimpleComparisonPropagator:
    def accepts(self, premise: ComparisonPremise) -> bool:
        return (
            _is_simple_comparison_operand(premise.left)
            and _is_simple_comparison_operand(premise.right)
        )

    def revise(
        self,
        premise: ComparisonPremise,
        domains: MutableTermDomains,
        metrics: InstantiationMetrics,
    ) -> set[Variable] | None:
        return _revise_simple_comparison(premise, domains, metrics)


@dataclass(frozen=True, slots=True)
class _BinaryArithmeticPropagator:
    def accepts(self, premise: ComparisonPremise) -> bool:
        return _binary_equality_shape(premise) is not None

    def revise(
        self,
        premise: ComparisonPremise,
        domains: MutableTermDomains,
        metrics: InstantiationMetrics,
    ) -> set[Variable] | None:
        return _revise_binary_arithmetic_equality(
            premise,
            domains,
            metrics,
        )


@dataclass(frozen=True, slots=True)
class _NValuePropagator:
    maximum_hall_size: int = 3

    def accepts(self, premise: ComparisonPremise) -> bool:
        return _nvalue_shape(premise) is not None

    def revise(
        self,
        premise: ComparisonPremise,
        domains: MutableTermDomains,
        metrics: InstantiationMetrics,
    ) -> set[Variable] | None:
        return _revise_nvalue(
            premise,
            domains,
            metrics,
            maximum_hall_size=self.maximum_hall_size,
        )


def _is_simple_comparison_operand(operand: ComparisonOperand) -> bool:
    return not isinstance(
        operand,
        (
            BinaryArithmeticExpression,
            UnaryArithmeticExpression,
            DistinctCountExpression,
        ),
    ) and (isinstance(operand, Variable) or is_ground(operand))


def _simple_operand_domain(
    operand: ComparisonOperand,
    domains: Mapping[Variable, set[Term]],
) -> tuple[Variable | None, set[Term]] | None:
    if isinstance(operand, Variable):
        return operand, domains[operand]
    if not isinstance(
        operand,
        (
            BinaryArithmeticExpression,
            UnaryArithmeticExpression,
            DistinctCountExpression,
        ),
    ) and is_ground(operand):
        return None, {operand}
    return None


def _revise_simple_comparison(
    premise: ComparisonPremise,
    domains: MutableTermDomains,
    metrics: InstantiationMetrics,
) -> set[Variable] | None:
    left_operand = _simple_operand_domain(premise.left, domains)
    right_operand = _simple_operand_domain(premise.right, domains)
    if left_operand is None or right_operand is None:
        return None
    left_variable, left = left_operand
    right_variable, right = right_operand
    operator = premise.operator

    if operator in {
        ComparisonOperator.LT,
        ComparisonOperator.LE,
        ComparisonOperator.GT,
        ComparisonOperator.GE,
    } and not all(isinstance(value, Number) for value in (*left, *right)):
        return None
    if operator is ComparisonOperator.DIVISIBLE and (
        not all(
            isinstance(value, Number) and isinstance(value.value, int)
            for value in (*left, *right)
        )
        or any(
            isinstance(value, Number) and value.value == 0
            for value in right
        )
    ):
        return None

    left_supported: set[Term]
    right_supported: set[Term]
    if operator is ComparisonOperator.EQ:
        common = left & right
        left_supported = common
        right_supported = common
        metrics.domain_specialized_value_checks += len(left) + len(right)
    elif operator is ComparisonOperator.NE:
        left_supported = (
            left - right if len(right) == 1 else set(left)
        )
        right_supported = (
            right - left if len(left) == 1 else set(right)
        )
        metrics.domain_specialized_value_checks += len(left) + len(right)
    elif operator in {
        ComparisonOperator.LT,
        ComparisonOperator.LE,
        ComparisonOperator.GT,
        ComparisonOperator.GE,
    }:
        left_numbers = {
            value for value in left if isinstance(value, Number)
        }
        right_numbers = {
            value for value in right if isinstance(value, Number)
        }
        if not left_numbers or not right_numbers:
            left_supported = set()
            right_supported = set()
        else:
            minimum_left = min(value.value for value in left_numbers)
            maximum_left = max(value.value for value in left_numbers)
            minimum_right = min(value.value for value in right_numbers)
            maximum_right = max(value.value for value in right_numbers)
            if operator is ComparisonOperator.LT:
                left_supported = {
                    value
                    for value in left_numbers
                    if value.value < maximum_right
                }
                right_supported = {
                    value
                    for value in right_numbers
                    if value.value > minimum_left
                }
            elif operator is ComparisonOperator.LE:
                left_supported = {
                    value
                    for value in left_numbers
                    if value.value <= maximum_right
                }
                right_supported = {
                    value
                    for value in right_numbers
                    if value.value >= minimum_left
                }
            elif operator is ComparisonOperator.GT:
                left_supported = {
                    value
                    for value in left_numbers
                    if value.value > minimum_right
                }
                right_supported = {
                    value
                    for value in right_numbers
                    if value.value < maximum_left
                }
            else:
                left_supported = {
                    value
                    for value in left_numbers
                    if value.value >= minimum_right
                }
                right_supported = {
                    value
                    for value in right_numbers
                    if value.value <= maximum_left
                }
        metrics.domain_specialized_value_checks += len(left) + len(right)
    else:
        left_supported = set()
        right_supported = set()
        for left_value in left:
            assert isinstance(left_value, Number)
            for right_value in right:
                assert isinstance(right_value, Number)
                metrics.domain_specialized_value_checks += 1
                if left_value.value % right_value.value == 0:
                    left_supported.add(left_value)
                    right_supported.add(right_value)

    changed: set[Variable] = set()
    _retain_supported(
        left_variable,
        left_supported,
        domains,
        changed,
    )
    _retain_supported(
        right_variable,
        right_supported,
        domains,
        changed,
    )
    return changed


def _retain_supported(
    variable: Variable | None,
    supported: set[Term],
    domains: MutableTermDomains,
    changed: set[Variable],
) -> None:
    if variable is None:
        return
    reduced = domains[variable] & supported
    if reduced != domains[variable]:
        domains[variable] = reduced
        changed.add(variable)


def _binary_equality_shape(
    premise: ComparisonPremise,
) -> tuple[
    BinaryArithmeticExpression,
    Number | Variable,
] | None:
    if premise.operator is not ComparisonOperator.EQ:
        return None
    expression: BinaryArithmeticExpression
    target: ComparisonOperand
    if isinstance(premise.left, BinaryArithmeticExpression):
        expression = premise.left
        target = premise.right
    elif isinstance(premise.right, BinaryArithmeticExpression):
        expression = premise.right
        target = premise.left
    else:
        return None
    if not isinstance(expression.left, (Number, Variable)):
        return None
    if not isinstance(expression.right, (Number, Variable)):
        return None
    if not isinstance(target, (Number, Variable)):
        return None
    variables = tuple(
        operand
        for operand in (expression.left, expression.right, target)
        if isinstance(operand, Variable)
    )
    if len(set(variables)) != len(variables):
        return None
    return expression, target


def _revise_binary_arithmetic_equality(
    premise: ComparisonPremise,
    domains: MutableTermDomains,
    metrics: InstantiationMetrics,
) -> set[Variable] | None:
    shape = _binary_equality_shape(premise)
    if shape is None:
        return None
    expression, target = shape
    assert isinstance(expression.left, (Number, Variable))
    assert isinstance(expression.right, (Number, Variable))
    left_operand = _numeric_operand_domain(expression.left, domains)
    right_operand = _numeric_operand_domain(expression.right, domains)
    target_operand = _numeric_operand_domain(target, domains)
    if (
        left_operand is None
        or right_operand is None
        or target_operand is None
    ):
        return None
    left_variable, left_values = left_operand
    right_variable, right_values = right_operand
    target_variable, target_values = target_operand
    if expression.operator in {
        BinaryArithmeticOperator.DIVIDE,
        BinaryArithmeticOperator.MODULO,
    } and any(value.value == 0 for value in right_values):
        return None
    if (
        expression.operator is BinaryArithmeticOperator.MODULO
        and not all(
            isinstance(value.value, int)
            for value in (*left_values, *right_values)
        )
    ):
        return None

    supported_left: set[Term] = set()
    supported_right: set[Term] = set()
    supported_target: set[Term] = set()
    if expression.operator in {
        BinaryArithmeticOperator.ADD,
        BinaryArithmeticOperator.SUBTRACT,
    }:
        solutions = _additive_solutions(
            expression.operator,
            left_values,
            right_values,
            target_values,
        )
        metrics.domain_specialized_value_checks += min(
            len(left_values) * len(right_values),
            len(left_values) * len(target_values),
            len(right_values) * len(target_values),
        )
        for left, right, result in solutions:
            supported_left.add(left)
            supported_right.add(right)
            supported_target.add(result)
    else:
        for left in left_values:
            for right in right_values:
                metrics.domain_specialized_value_checks += 1
                result = _apply_binary_arithmetic(
                    expression.operator,
                    left,
                    right,
                )
                if result in target_values:
                    supported_left.add(left)
                    supported_right.add(right)
                    supported_target.add(result)

    changed: set[Variable] = set()
    _retain_supported(left_variable, supported_left, domains, changed)
    _retain_supported(right_variable, supported_right, domains, changed)
    _retain_supported(target_variable, supported_target, domains, changed)
    return changed


def _numeric_operand_domain(
    operand: Number | Variable,
    domains: Mapping[Variable, set[Term]],
) -> tuple[Variable | None, set[Number]] | None:
    if isinstance(operand, Number):
        return None, {operand}
    values = domains[operand]
    if not all(isinstance(value, Number) for value in values):
        return None
    return operand, {
        value for value in values if isinstance(value, Number)
    }


def _apply_binary_arithmetic(
    operator: BinaryArithmeticOperator,
    left: Number,
    right: Number,
) -> Number:
    if operator is BinaryArithmeticOperator.ADD:
        return Number(left.value + right.value)
    if operator is BinaryArithmeticOperator.SUBTRACT:
        return Number(left.value - right.value)
    if operator is BinaryArithmeticOperator.MULTIPLY:
        return Number(left.value * right.value)
    if operator is BinaryArithmeticOperator.DIVIDE:
        return Number(left.value / right.value)
    if operator is BinaryArithmeticOperator.MODULO:
        if not isinstance(left.value, int) or not isinstance(right.value, int):
            raise TypeError("modulo constraint requires integer operands")
        return Number(left.value % right.value)
    raise ValueError(f"unsupported arithmetic operator: {operator}")


def _additive_solutions(
    operator: BinaryArithmeticOperator,
    left_values: set[Number],
    right_values: set[Number],
    target_values: set[Number],
) -> tuple[tuple[Number, Number, Number], ...]:
    pair = min(
        ("left-right", len(left_values) * len(right_values)),
        ("left-target", len(left_values) * len(target_values)),
        ("right-target", len(right_values) * len(target_values)),
        key=lambda item: item[1],
    )[0]
    solutions: list[tuple[Number, Number, Number]] = []
    if pair == "left-right":
        for left in left_values:
            for right in right_values:
                target = Number(
                    left.value + right.value
                    if operator is BinaryArithmeticOperator.ADD
                    else left.value - right.value
                )
                if target in target_values:
                    solutions.append((left, right, target))
    elif pair == "left-target":
        for left in left_values:
            for target in target_values:
                right = Number(
                    target.value - left.value
                    if operator is BinaryArithmeticOperator.ADD
                    else left.value - target.value
                )
                if right in right_values:
                    solutions.append((left, right, target))
    else:
        for right in right_values:
            for target in target_values:
                left = Number(
                    target.value - right.value
                    if operator is BinaryArithmeticOperator.ADD
                    else target.value + right.value
                )
                if left in left_values:
                    solutions.append((left, right, target))
    return tuple(solutions)


def _nvalue_shape(
    premise: ComparisonPremise,
) -> tuple[DistinctCountExpression, Number | Variable] | None:
    if premise.operator is not ComparisonOperator.EQ:
        return None
    if isinstance(premise.left, DistinctCountExpression) and isinstance(
        premise.right,
        (Number, Variable),
    ):
        return premise.left, premise.right
    if isinstance(premise.right, DistinctCountExpression) and isinstance(
        premise.left,
        (Number, Variable),
    ):
        return premise.right, premise.left
    return None


def _revise_nvalue(
    premise: ComparisonPremise,
    domains: MutableTermDomains,
    metrics: InstantiationMetrics,
    *,
    maximum_hall_size: int,
) -> set[Variable] | None:
    shape = _nvalue_shape(premise)
    if shape is None:
        return None
    expression, count_operand = shape
    item_scopes: list[tuple[Variable | None, set[Term]]] = []
    for item in expression.values:
        if isinstance(item, Variable):
            item_scopes.append((item, set(domains[item])))
        elif is_ground(item):
            item_scopes.append((None, {item}))
        else:
            return None
    count_scope = _integer_count_domain(count_operand, domains)
    if count_scope is None:
        return None
    count_variable, count_values = count_scope
    if any(not values for _, values in item_scopes) or not count_values:
        return _empty_one_domain(
            tuple(variable for variable, _ in item_scopes),
            count_variable,
            domains,
        )

    union = set().union(*(values for _, values in item_scopes))
    mandatory = {
        next(iter(values))
        for _, values in item_scopes
        if len(values) == 1
    }
    lower = max(1, len(mandatory))
    upper = min(len(item_scopes), len(union))
    supported_counts = {
        value
        for value in count_values
        if lower <= value.value <= upper
    }
    metrics.domain_global_value_checks += (
        len(count_values) + sum(len(values) for _, values in item_scopes)
    )
    changed: set[Variable] = set()
    _retain_supported(
        count_variable,
        set(supported_counts),
        domains,
        changed,
    )
    if not supported_counts:
        return _empty_one_domain(
            tuple(variable for variable, _ in item_scopes),
            count_variable,
            domains,
            changed,
        )

    fixed_count = (
        next(iter(supported_counts)).value
        if len(supported_counts) == 1
        else None
    )
    if fixed_count == len(item_scopes):
        changed.update(
            _revise_all_different(
                item_scopes,
                domains,
                metrics,
                maximum_hall_size=maximum_hall_size,
            )
        )
        return changed
    if fixed_count == 1:
        common = set.intersection(
            *(set(values) for _, values in item_scopes)
        )
        for variable, _ in item_scopes:
            _retain_supported(variable, common, domains, changed)
        return changed
    if fixed_count == lower and mandatory:
        for variable, values in item_scopes:
            if len(values) > 1:
                _retain_supported(
                    variable,
                    mandatory,
                    domains,
                    changed,
                )
    return changed


def _integer_count_domain(
    operand: Number | Variable,
    domains: Mapping[Variable, set[Term]],
) -> tuple[Variable | None, set[Number]] | None:
    if isinstance(operand, Number):
        if isinstance(operand.value, int):
            return None, {operand}
        return None
    values = domains[operand]
    if not all(
        isinstance(value, Number) and isinstance(value.value, int)
        for value in values
    ):
        return None
    return operand, {
        value
        for value in values
        if isinstance(value, Number) and isinstance(value.value, int)
    }


def _empty_one_domain(
    item_variables: tuple[Variable | None, ...],
    count_variable: Variable | None,
    domains: MutableTermDomains,
    changed: set[Variable] | None = None,
) -> set[Variable]:
    output = changed if changed is not None else set()
    variable = count_variable or next(
        (candidate for candidate in item_variables if candidate is not None),
        None,
    )
    if variable is not None and domains[variable]:
        domains[variable] = set()
        output.add(variable)
    return output


def _revise_all_different(
    item_scopes: Sequence[tuple[Variable | None, set[Term]]],
    domains: MutableTermDomains,
    metrics: InstantiationMetrics,
    *,
    maximum_hall_size: int,
) -> set[Variable]:
    variables = tuple(
        variable for variable, _ in item_scopes if variable is not None
    )
    if len(set(variables)) != len(variables):
        return _empty_one_domain(
            tuple(variables),
            None,
            domains,
        )
    work = {variable: set(domains[variable]) for variable in variables}
    constants = tuple(
        next(iter(values))
        for variable, values in item_scopes
        if variable is None
    )
    if len(set(constants)) != len(constants):
        return _empty_one_domain(
            tuple(variables),
            None,
            domains,
        )

    changed_locally = True
    while changed_locally:
        changed_locally = False
        scopes = tuple(
            (variable, work[variable])
            if variable is not None
            else (None, values)
            for variable, values in item_scopes
        )
        singleton_owners: dict[Term, Variable | None] = {}
        missing_owner = object()
        for variable, values in scopes:
            if len(values) != 1:
                continue
            value = next(iter(values))
            owner = singleton_owners.get(value, missing_owner)
            if owner is not missing_owner:
                return _empty_one_domain(
                    tuple(variables),
                    None,
                    domains,
                )
            singleton_owners[value] = variable
        for variable in variables:
            removable = {
                value
                for value, owner in singleton_owners.items()
                if owner != variable
            }
            reduced = work[variable] - removable
            metrics.domain_global_value_checks += len(work[variable])
            if not reduced:
                domains[variable] = set()
                return {variable}
            if reduced != work[variable]:
                work[variable] = reduced
                changed_locally = True

        scopes = tuple(
            (variable, work[variable])
            if variable is not None
            else (None, values)
            for variable, values in item_scopes
        )
        maximum = min(maximum_hall_size, len(scopes) - 1)
        for size in range(2, maximum + 1):
            for indices in combinations(range(len(scopes)), size):
                hall_values = set().union(
                    *(scopes[index][1] for index in indices)
                )
                metrics.domain_global_value_checks += sum(
                    len(scopes[index][1]) for index in indices
                )
                if len(hall_values) < size:
                    return _empty_one_domain(
                        tuple(variables),
                        None,
                        domains,
                    )
                if len(hall_values) != size:
                    continue
                selected = set(indices)
                for index, (variable, _) in enumerate(scopes):
                    if index in selected or variable is None:
                        continue
                    reduced = work[variable] - hall_values
                    if not reduced:
                        domains[variable] = set()
                        return {variable}
                    if reduced != work[variable]:
                        work[variable] = reduced
                        changed_locally = True

    changed: set[Variable] = set()
    for variable, supported in work.items():
        _retain_supported(variable, supported, domains, changed)
    return changed
