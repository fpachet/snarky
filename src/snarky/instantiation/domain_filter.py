"""Safe finite-domain filtering with compact extensional-table joins."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, MutableMapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, fields
from functools import cache
from itertools import combinations, product
from time import perf_counter
from typing import Protocol

from ..expressions import (
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    DistinctCountExpression,
    UnaryArithmeticExpression,
)
from ..facts import Fact
from ..premises import (
    ComparisonOperand,
    ComparisonOperator,
    ComparisonPremise,
    variables_in_comparison_operand,
)
from ..propagation import (
    DomainStore,
    PropagationReason,
    PropagationResult,
)
from ..rules import Rule
from ..substitutions import BindingFrame
from ..terms import Number, Term, Variable, is_ground, variables_in
from .base import Activation, FactDelta, InstantiationMetrics
from .compiled import (
    CompiledComparisonPremise,
    CompiledFactPremise,
    compile_rule,
)
from .domain_tables import (
    _add_row_projection,
    _CompactTableDefinition,
    _CompactTableState,
    _DomainRow,
    _remove_row_projection,
)
from .indexed import FactIndex, SemiNaiveInstantiationStrategy


@dataclass(frozen=True, slots=True)
class _TablePlan:
    position: int
    premise: CompiledFactPremise
    variables: tuple[Variable, ...]


@dataclass(frozen=True, slots=True)
class _ComparisonPlan:
    premise: ComparisonPremise
    variables: tuple[Variable, ...]


type _ConstraintKey = tuple[str, int]


@dataclass(frozen=True, slots=True)
class _DomainPlan:
    tables: tuple[_TablePlan, ...]
    comparisons: tuple[_ComparisonPlan, ...]
    variables: tuple[Variable, ...]
    incidence: tuple[tuple[Variable, tuple[_ConstraintKey, ...]], ...]
    components: tuple[tuple[Variable, frozenset[Variable]], ...]
    cyclic: bool
    applicable: bool


@dataclass(slots=True)
class _DomainMemory:
    tables: dict[int, _CompactTableDefinition]
    table_states: dict[int, _CompactTableState]
    value_counts: dict[Variable, dict[Term, int]]
    base_domains: dict[Variable, set[Term]]
    filtered_domains: dict[Variable, frozenset[Term]] | None = None
    cached_result: _FilteringResult | None = None
    additions: frozenset[Variable] = frozenset()
    delta_masks: dict[int, int] | None = None


@dataclass(frozen=True, slots=True)
class _FilteringResult:
    domains: Mapping[Variable, frozenset[Term]]
    candidates: Mapping[int, tuple[Fact, ...]]
    candidate_sets: Mapping[int, frozenset[Fact]]
    consistent: bool
    propagation: PropagationResult


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


class ConstraintInstantiationStrategy(SemiNaiveInstantiationStrategy):
    """Filter positive-rule domains, then join the surviving table rows.

    Unsupported rules fall back to :class:`SemiNaiveInstantiationStrategy`.
    Extensional tables and projected value counts are retained per rule and
    updated from fact deltas. Removals resume from the previous fixed point;
    additions reset only the connected domain components they can widen.
    """

    def __init__(
        self,
        *,
        comparison_product_limit: int = 4_096,
        adaptive: bool = False,
        minimum_domain_rows: int = 128,
        minimum_bucket_ratio: float = 8.0,
        minimum_candidate_reduction: float = 0.10,
        minimum_observed_speedup: float = 1.05,
        cost_probe_reduction_ceiling: float = 0.75,
        minimum_cost_probe_uses: int = 8,
        use_propagation_queue: bool = True,
        use_specialized_comparisons: bool = True,
        use_incremental_domains: bool = True,
        use_compact_tables: bool = True,
        use_compact_join: bool = True,
        maximum_hall_size: int = 3,
        propagators: Sequence[DomainPropagator] = (),
    ) -> None:
        if comparison_product_limit < 1:
            raise ValueError("comparison_product_limit must be positive")
        if minimum_domain_rows < 1:
            raise ValueError("minimum_domain_rows must be positive")
        if minimum_bucket_ratio < 1:
            raise ValueError("minimum_bucket_ratio must be at least one")
        if not 0 <= minimum_candidate_reduction <= 1:
            raise ValueError(
                "minimum_candidate_reduction must be between zero and one"
            )
        if minimum_observed_speedup <= 0:
            raise ValueError("minimum_observed_speedup must be positive")
        if not 0 <= cost_probe_reduction_ceiling <= 1:
            raise ValueError(
                "cost_probe_reduction_ceiling must be between zero and one"
            )
        if minimum_cost_probe_uses < 1:
            raise ValueError("minimum_cost_probe_uses must be positive")
        if maximum_hall_size < 1:
            raise ValueError("maximum_hall_size must be positive")
        super().__init__()
        self.comparison_product_limit = comparison_product_limit
        self.adaptive = adaptive
        self.minimum_domain_rows = minimum_domain_rows
        self.minimum_bucket_ratio = minimum_bucket_ratio
        self.minimum_candidate_reduction = minimum_candidate_reduction
        self.minimum_observed_speedup = minimum_observed_speedup
        self.cost_probe_reduction_ceiling = cost_probe_reduction_ceiling
        self.minimum_cost_probe_uses = minimum_cost_probe_uses
        self.use_propagation_queue = use_propagation_queue
        self.use_specialized_comparisons = use_specialized_comparisons
        self.use_incremental_domains = use_incremental_domains
        self.use_compact_tables = use_compact_tables
        self.use_compact_join = use_compact_join
        self.propagators = (
            *tuple(propagators),
            _NValuePropagator(maximum_hall_size),
            _SimpleComparisonPropagator(),
            _BinaryArithmeticPropagator(),
        )
        self._domain_memories: dict[Rule, _DomainMemory] = {}
        self._filter_decisions: dict[Rule, bool] = {}
        self._filter_cost_ratios: dict[Rule, float] = {}
        self._filter_use_counts: dict[Rule, int] = {}
        self.last_propagation_results: dict[Rule, PropagationResult] = {}

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        changes = _normalize_delta(delta)
        plan = _compile_domain_plan(rule)
        if not plan.applicable:
            self.metrics.domain_filter_fallbacks += 1
            return super().instantiate(rule, facts, changes)

        decision = self._filter_decisions.get(rule)
        if self.adaptive and decision is False:
            self.metrics.domain_filter_fallbacks += 1
            return super().instantiate(rule, facts, changes)
        if (
            self.adaptive
            and decision is None
            and (
                (
                    bool(plan.comparisons)
                    and not all(
                        self._has_propagator(comparison.premise)
                        for comparison in plan.comparisons
                    )
                )
                or (
                    not plan.comparisons
                    and (len(plan.tables) < 3 or not plan.cyclic)
                )
                or len(facts) * len(plan.tables)
                < self.minimum_domain_rows
            )
        ):
            self._filter_decisions[rule] = False
            self.metrics.domain_filter_rejections += 1
            self.metrics.domain_filter_fallbacks += 1
            return super().instantiate(rule, facts, changes)

        index = self._index_for(rule, facts, changes)
        if (
            self.adaptive
            and decision is None
            and not self._static_filter_candidate(plan, index)
        ):
            self._filter_decisions[rule] = False
            self.metrics.domain_filter_rejections += 1
            self.metrics.domain_filter_fallbacks += 1
            return super().instantiate(rule, facts, changes)

        filter_started = perf_counter()
        probe_observed_cost = False
        memory = self._domain_memory(rule, plan, index, changes)
        filtered = self._filter_domains(plan, memory)
        self.last_propagation_results[rule] = filtered.propagation
        self.metrics.domain_filter_runs += 1
        if self.adaptive and decision is None:
            row_count = sum(
                len(rows) for rows in memory.tables.values()
            )
            retained = sum(
                len(candidates)
                for candidates in filtered.candidates.values()
            )
            reduction = (
                1 - retained / row_count if row_count else 0.0
            )
            if not filtered.consistent:
                self._filter_decisions[rule] = True
                self.metrics.domain_filter_selections += 1
                return ()
            if reduction < self.minimum_candidate_reduction:
                self._filter_decisions[rule] = False
                self.metrics.domain_filter_rejections += 1
                self.metrics.domain_filter_fallbacks += 1
                return super().instantiate(rule, facts, changes)
            if reduction >= self.cost_probe_reduction_ceiling:
                self._filter_decisions[rule] = True
                self.metrics.domain_filter_selections += 1
                decision = True
            else:
                uses = self._filter_use_counts.get(rule, 0) + 1
                self._filter_use_counts[rule] = uses
                if uses >= self.minimum_cost_probe_uses:
                    probe_observed_cost = True
                else:
                    self.metrics.domain_cost_probe_deferrals += 1
        if not filtered.consistent:
            return ()

        activations = self._join_filtered(
            rule,
            index,
            plan,
            memory,
            filtered.candidates,
            filtered.candidate_sets,
        )
        filter_elapsed = perf_counter() - filter_started
        if probe_observed_cost:
            fallback, fallback_elapsed = self._probe_fallback(
                rule,
                facts,
                changes,
            )
            observed_speedup = (
                fallback_elapsed / filter_elapsed
                if filter_elapsed
                else float("inf")
            )
            self._filter_cost_ratios[rule] = observed_speedup
            self.metrics.domain_cost_probes += 1
            self.metrics.domain_filter_probe_seconds += filter_elapsed
            self.metrics.domain_fallback_probe_seconds += fallback_elapsed
            selected = observed_speedup >= self.minimum_observed_speedup
            self._filter_decisions[rule] = selected
            if selected:
                self.metrics.domain_filter_selections += 1
            else:
                self.metrics.domain_cost_probe_rejections += 1
                self.metrics.domain_filter_rejections += 1
                self.metrics.domain_filter_fallbacks += 1
                self.metrics.activations_produced += len(fallback)
                return fallback
        self.metrics.activations_produced += len(activations)
        return tuple(activations)

    def _probe_fallback(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        changes: FactDelta | None,
    ) -> tuple[tuple[Activation, ...], float]:
        snapshot = {
            field.name: getattr(self.metrics, field.name)
            for field in fields(InstantiationMetrics)
        }
        started = perf_counter()
        activations = super().instantiate(rule, facts, changes)
        elapsed = perf_counter() - started
        for name, value in snapshot.items():
            setattr(self.metrics, name, value)
        return activations, elapsed

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        super().invalidate(removed)
        if not removed:
            self._domain_memories.clear()
            self._filter_decisions.clear()
            self._filter_cost_ratios.clear()
            self._filter_use_counts.clear()
            self.last_propagation_results.clear()

    def fork_for_branch(self) -> ConstraintInstantiationStrategy:
        """Preserve constraint configuration and branch-local filter state."""

        return deepcopy(self)

    def _static_filter_candidate(
        self,
        plan: _DomainPlan,
        index: FactIndex,
    ) -> bool:
        frame = BindingFrame()
        sizes = tuple(
            len(index.candidates_compiled(table.premise, frame))
            for table in plan.tables
        )
        if not sizes or sum(sizes) < self.minimum_domain_rows:
            return False
        if any(size == 0 for size in sizes):
            return True
        if plan.comparisons:
            return all(
                self._has_propagator(comparison.premise)
                for comparison in plan.comparisons
            )
        return (
            len(sizes) >= 3
            and plan.cyclic
            and max(sizes) / min(sizes) >= self.minimum_bucket_ratio
        )

    def _has_propagator(self, premise: ComparisonPremise) -> bool:
        return any(
            propagator.accepts(premise)
            for propagator in self.propagators
        )

    def _domain_memory(
        self,
        rule: Rule,
        plan: _DomainPlan,
        index: FactIndex,
        delta: FactDelta | None,
    ) -> _DomainMemory:
        memory = self._domain_memories.get(rule)
        if memory is None or delta is None:
            tables = {
                table.position: _CompactTableDefinition.build(
                    self._build_table(table, index),
                    table.variables,
                )
                for table in plan.tables
            }
            table_states = {
                position: _CompactTableState.initial(definition)
                for position, definition in tables.items()
            }
            value_counts: dict[Variable, dict[Term, int]] = {
                variable: {} for variable in plan.variables
            }
            for table_memory in tables.values():
                for row in table_memory.rows.values():
                    _add_row_projection(row, value_counts)
            memory = _DomainMemory(
                tables,
                table_states,
                value_counts,
                {
                    variable: set(counts)
                    for variable, counts in value_counts.items()
                },
            )
            self._domain_memories[rule] = memory
            self.metrics.domain_table_rebuilds += 1
            row_count = sum(len(table) for table in tables.values())
            self.metrics.domain_rows += row_count
            self.metrics.domain_projection_rows_examined += row_count
            if self.use_compact_tables:
                self.metrics.domain_bitset_builds += len(tables)
            return memory

        memory.delta_masks = None if delta.removed else {}
        if not delta.changed:
            return memory
        changed = False
        added_variables: set[Variable] = set()
        for table in plan.tables:
            table_memory = memory.tables[table.position]
            table_state = memory.table_states[table.position]
            for fact in delta.removed:
                removed = table_memory.remove(fact)
                if removed is None:
                    continue
                removed_row, removed_bit = removed
                table_state.active_mask &= ~removed_bit
                _remove_row_projection(
                    removed_row,
                    memory.value_counts,
                    memory.base_domains,
                )
                changed = True
                self.metrics.domain_projection_updates += 1
                if self.use_compact_tables:
                    self.metrics.domain_bitset_updates += 1
            for fact in delta.added:
                added_row = self._match_row(table, fact)
                added_bit = (
                    None
                    if added_row is None
                    else table_memory.add(added_row)
                )
                if added_row is not None and added_bit is not None:
                    table_state.active_mask |= added_bit
                    if memory.delta_masks is not None:
                        memory.delta_masks[table.position] = (
                            memory.delta_masks.get(table.position, 0)
                            | added_bit
                        )
                    _add_row_projection(
                        added_row,
                        memory.value_counts,
                        memory.base_domains,
                    )
                    added_variables.update(table.variables)
                    self.metrics.domain_rows += 1
                    self.metrics.domain_projection_updates += 1
                    if self.use_compact_tables:
                        self.metrics.domain_bitset_updates += 1
                    changed = True
        if changed:
            self.metrics.domain_table_updates += 1
            memory.cached_result = None
            memory.additions = frozenset(added_variables)
        return memory

    def _build_table(
        self,
        table: _TablePlan,
        index: FactIndex,
    ) -> dict[Fact, _DomainRow]:
        frame = BindingFrame()
        candidates = index.candidates_compiled(table.premise, frame)
        self.metrics.domain_candidate_facts += len(candidates)
        rows: dict[Fact, _DomainRow] = {}
        for fact in candidates:
            row = self._match_row(table, fact)
            if row is not None:
                rows[fact] = row
        return rows

    def _match_row(
        self,
        table: _TablePlan,
        fact: Fact,
    ) -> _DomainRow | None:
        self.metrics.domain_match_attempts += 1
        frame = BindingFrame()
        if not table.premise.match(fact.entity, fact.status, frame):
            return None
        bindings: list[tuple[Variable, Term]] = []
        for variable in table.variables:
            value = frame.value(variable)
            if value is None:
                raise AssertionError(
                    f"compiled match did not bind ${variable.name}"
                )
            bindings.append((variable, value))
        return _DomainRow(fact, tuple(bindings))

    def _filter_domains(
        self,
        plan: _DomainPlan,
        memory: _DomainMemory,
    ) -> _FilteringResult:
        if self.use_incremental_domains and memory.cached_result is not None:
            self.metrics.domain_state_reuses += 1
            return memory.cached_result
        self.metrics.domain_input_rows += sum(
            len(memory.tables[table.position]) for table in plan.tables
        )
        if self.use_incremental_domains:
            initial_domains = self._starting_domains(plan, memory)
        else:
            initial_domains = {
                variable: set[Term]() for variable in plan.variables
            }
            for table in plan.tables:
                rows = memory.tables[table.position].rows.values()
                self.metrics.domain_projection_rows_examined += len(
                    memory.tables[table.position]
                )
                for row in rows:
                    for variable, value in row.bindings:
                        initial_domains[variable].add(value)
            if self.use_compact_tables:
                for position, definition in memory.tables.items():
                    memory.table_states[position].reset(definition)
        domains = DomainStore(initial_domains, record_trail=False)
        initial_size = sum(len(domain) for domain in domains.values())
        if any(not domain for domain in domains.values()):
            return self._remember_filtering_result(
                memory,
                domains,
                {},
                False,
            )

        consistent = (
            self._propagate_queue(plan, memory, domains)
            if self.use_propagation_queue
            else self._propagate_full_scan(plan, memory, domains)
        )
        if not consistent:
            return self._remember_filtering_result(
                memory,
                domains,
                {},
                False,
            )

        candidates: dict[int, tuple[Fact, ...]] = {}
        retained_count = 0
        total_count = 0
        for table in plan.tables:
            table_memory = memory.tables[table.position]
            table_state = memory.table_states[table.position]
            total_count += len(table_memory)
            active_facts = (
                table_memory.facts(table_state.active_mask)
                if self.use_compact_tables
                else tuple(
                    row.fact
                    for row in table_memory.rows.values()
                    if row.compatible(domains)
                )
            )
            retained_count += len(active_facts)
            candidates[table.position] = active_facts
        self.metrics.domain_values_removed += initial_size - sum(
            len(domain) for domain in domains.values()
        )
        self.metrics.domain_candidates_removed += total_count - retained_count
        return self._remember_filtering_result(
            memory,
            domains,
            candidates,
            True,
        )

    def _starting_domains(
        self,
        plan: _DomainPlan,
        memory: _DomainMemory,
    ) -> dict[Variable, set[Term]]:
        previous = memory.filtered_domains
        if previous is None:
            if self.use_compact_tables:
                for position, definition in memory.tables.items():
                    memory.table_states[position].reset(definition)
            return {
                variable: set(memory.base_domains[variable])
                for variable in plan.variables
            }
        affected: set[Variable] = set()
        if memory.additions:
            components = dict(plan.components)
            for variable in memory.additions:
                affected.update(components[variable])
            self.metrics.domain_component_resets += len(
                {
                    components[variable]
                    for variable in memory.additions
                }
            )
            if self.use_compact_tables:
                for table in plan.tables:
                    if any(
                        variable in affected
                        for variable in table.variables
                    ):
                        memory.table_states[table.position].reset(
                            memory.tables[table.position]
                        )
                        self.metrics.domain_bitset_resets += 1
        return {
            variable: (
                set(memory.base_domains[variable])
                if variable in affected
                else (
                    set(previous[variable])
                    & memory.base_domains[variable]
                )
            )
            for variable in plan.variables
        }

    def _remember_filtering_result(
        self,
        memory: _DomainMemory,
        domains: DomainStore,
        candidates: Mapping[int, tuple[Fact, ...]],
        consistent: bool,
    ) -> _FilteringResult:
        if not consistent and domains.contradiction is None:
            domains.fail(
                PropagationReason("fixed-point"),
                "propagation reached an inconsistent table",
            )
        propagation = domains.result()
        frozen_domains = dict(propagation.domains)
        result = _FilteringResult(
            frozen_domains,
            candidates,
            {
                position: frozenset(facts)
                for position, facts in candidates.items()
            },
            consistent,
            propagation,
        )
        memory.filtered_domains = frozen_domains
        memory.cached_result = (
            result if self.use_incremental_domains else None
        )
        if not self.use_incremental_domains:
            memory.filtered_domains = None
        memory.additions = frozenset()
        return result

    def _propagate_queue(
        self,
        plan: _DomainPlan,
        memory: _DomainMemory,
        domains: DomainStore,
    ) -> bool:
        table_by_position = {table.position: table for table in plan.tables}
        incidence = dict(plan.incidence)
        initial_queue = (
            *(("table", table.position) for table in plan.tables),
            *(("comparison", index) for index in range(len(plan.comparisons))),
        )
        queue = deque(initial_queue)
        queued = set(initial_queue)
        self.metrics.domain_queue_pushes += len(initial_queue)
        while queue:
            constraint = queue.popleft()
            queued.remove(constraint)
            self.metrics.domain_propagator_revisions += 1
            kind, identifier = constraint
            if kind == "table":
                consistent, changed_variables = self._revise_table(
                    table_by_position[identifier],
                    memory,
                    domains,
                )
                if not consistent:
                    domains.fail(
                        PropagationReason(
                            "table",
                            f"premise {identifier}",
                        ),
                        f"premise {identifier} has no active row",
                    )
                    return False
            else:
                changed_variables = self._revise_comparison(
                    plan.comparisons[identifier],
                    domains,
                )
            if any(not domain for domain in domains.values()):
                return False
            for variable in changed_variables:
                for neighbor in incidence[variable]:
                    if neighbor in queued:
                        continue
                    queue.append(neighbor)
                    queued.add(neighbor)
                    self.metrics.domain_queue_pushes += 1
        return True

    def _propagate_full_scan(
        self,
        plan: _DomainPlan,
        memory: _DomainMemory,
        domains: DomainStore,
    ) -> bool:
        while True:
            changed = False
            for table in plan.tables:
                self.metrics.domain_propagator_revisions += 1
                consistent, changed_variables = self._revise_table(
                    table,
                    memory,
                    domains,
                )
                if not consistent:
                    domains.fail(
                        PropagationReason(
                            "table",
                            f"premise {table.position}",
                        ),
                        f"premise {table.position} has no active row",
                    )
                    return False
                changed = bool(changed_variables) or changed
            for comparison in plan.comparisons:
                self.metrics.domain_propagator_revisions += 1
                changed = bool(
                    self._revise_comparison(comparison, domains)
                ) or changed
            if any(not domain for domain in domains.values()):
                return False
            if not changed:
                return True

    def _revise_table(
        self,
        table: _TablePlan,
        memory: _DomainMemory,
        domains: DomainStore,
    ) -> tuple[bool, set[Variable]]:
        previous_reason = domains.default_reason
        domains.default_reason = PropagationReason(
            "table",
            f"premise {table.position}",
        )
        try:
            if self.use_compact_tables:
                return self._revise_compact_table(
                    table,
                    memory.tables[table.position],
                    memory.table_states[table.position],
                    domains,
                )
            rows = memory.tables[table.position].rows.values()
            self.metrics.domain_rows_examined += len(
                memory.tables[table.position]
            )
            active = tuple(row for row in rows if row.compatible(domains))
            if not active:
                return False, set()
            changed: set[Variable] = set()
            for variable in table.variables:
                supported = {row.value(variable) for row in active}
                reduced = domains[variable] & supported
                if reduced != domains[variable]:
                    domains[variable] = reduced
                    self.metrics.domain_revisions += 1
                    changed.add(variable)
            return True, changed
        finally:
            domains.default_reason = previous_reason

    def _revise_compact_table(
        self,
        table: _TablePlan,
        table_memory: _CompactTableDefinition,
        table_state: _CompactTableState,
        domains: DomainStore,
    ) -> tuple[bool, set[Variable]]:
        active = table_state.active_mask
        for variable in table.variables:
            support_masks = table_memory.support_masks[variable]
            previous = table_state.applied_domains.get(variable)
            removed_values = (
                support_masks.keys() - domains[variable]
                if previous is None
                else (previous - domains[variable]) & support_masks.keys()
            )
            for value in removed_values:
                active &= ~support_masks[value]
                self.metrics.domain_bitset_value_events += 1
                self.metrics.domain_bitset_intersections += 1
                if not active:
                    table_state.active_mask = 0
                    return False, set()
            table_state.applied_domains[variable] = frozenset(
                domains[variable]
            )
        table_state.active_mask = active

        changed: set[Variable] = set()
        for variable in table.variables:
            support_masks = table_memory.support_masks[variable]
            supported: set[Term] = set()
            for value in domains[variable]:
                self.metrics.domain_bitset_support_checks += 1
                self.metrics.domain_bitset_intersections += 1
                if active & support_masks.get(value, 0):
                    supported.add(value)
            if supported != domains[variable]:
                domains[variable] = supported
                self.metrics.domain_revisions += 1
                changed.add(variable)
        return True, changed

    def _revise_comparison(
        self,
        comparison: _ComparisonPlan,
        domains: DomainStore,
    ) -> set[Variable]:
        previous_reason = domains.default_reason
        domains.default_reason = PropagationReason(
            "comparison",
            repr(comparison.premise),
        )
        try:
            if self.use_specialized_comparisons:
                for propagator in self.propagators:
                    if not propagator.accepts(comparison.premise):
                        continue
                    specialized = propagator.revise(
                        comparison.premise,
                        domains,
                        self.metrics,
                    )
                    if specialized is None:
                        continue
                    self.metrics.domain_specialized_revisions += 1
                    if isinstance(propagator, _NValuePropagator):
                        self.metrics.domain_global_revisions += 1
                    self.metrics.domain_revisions += len(specialized)
                    return specialized
            if not comparison.variables:
                return set()
            combinations = 1
            for variable in comparison.variables:
                combinations *= len(domains[variable])
                if combinations > self.comparison_product_limit:
                    return set()
            supports = {
                variable: set[Term]()
                for variable in comparison.variables
            }
            value_lists = tuple(
                tuple(domains[variable])
                for variable in comparison.variables
            )
            for values in product(*value_lists):
                self.metrics.domain_combinations_tested += 1
                frame = BindingFrame(
                    zip(comparison.variables, values, strict=True)
                )
                try:
                    accepted = comparison.premise.evaluate(frame)
                except (TypeError, ValueError):
                    # The Cartesian approximation can contain combinations
                    # that no factual join can reach. Preserve exact matcher
                    # timing.
                    return set()
                if accepted:
                    for variable, value in zip(
                        comparison.variables,
                        values,
                        strict=True,
                    ):
                        supports[variable].add(value)
            changed: set[Variable] = set()
            for variable in comparison.variables:
                reduced = domains[variable] & supports[variable]
                if reduced != domains[variable]:
                    domains[variable] = reduced
                    self.metrics.domain_revisions += 1
                    changed.add(variable)
            return changed
        finally:
            domains.default_reason = previous_reason

    def _join_filtered(
        self,
        rule: Rule,
        index: FactIndex,
        plan: _DomainPlan,
        memory: _DomainMemory,
        filtered_candidates: Mapping[int, tuple[Fact, ...]],
        filtered_candidate_sets: Mapping[int, frozenset[Fact]],
    ) -> list[Activation]:
        block = compile_rule(rule).block
        table_plans = {table.position: table for table in plan.tables}
        delta_masks = memory.delta_masks
        anchors: tuple[int | None, ...] = (
            (None,)
            if delta_masks is None
            else tuple(
                position
                for position in sorted(delta_masks)
                if delta_masks[position]
            )
        )
        if not anchors:
            self.metrics.domain_delta_join_skips += 1
            return []
        if anchors != (None,):
            self.metrics.domain_delta_join_variants += len(anchors)
        empty_delta_facts: frozenset[Fact] = frozenset()
        delta_fact_sets = (
            {}
            if delta_masks is None
            else {
                position: frozenset(
                    memory.tables[position].facts(mask)
                )
                for position, mask in delta_masks.items()
                if mask
            }
        )

        unique: dict[
            tuple[tuple[tuple[str, Term], ...], tuple[Fact, ...]],
            Activation,
        ] = {}

        def join_anchor(anchor: int | None) -> None:
            frame = BindingFrame()

            def extend(position: int, supports: list[Fact]) -> None:
                if position == len(block.premises):
                    activation = Activation(
                        frame.freeze(),
                        tuple(supports),
                    )
                    key = (
                        activation.substitution.key,
                        activation.premise_facts,
                    )
                    unique.setdefault(key, activation)
                    return
                premise = block.premises[position]
                if isinstance(premise, CompiledComparisonPremise):
                    if premise.source.evaluate(frame):
                        extend(position + 1, supports)
                    return
                if not isinstance(premise, CompiledFactPremise):
                    raise AssertionError(
                        "domain plan accepted an unsupported premise"
                    )
                table_memory = memory.tables[position]
                delta_mask = (
                    0 if delta_masks is None else delta_masks.get(position, 0)
                )
                if self.use_compact_tables and self.use_compact_join:
                    table_plan = table_plans[position]
                    mask, intersections = table_memory.mask_for_frame(
                        memory.table_states[position].active_mask,
                        table_plan.variables,
                        frame,
                    )
                    if anchor is not None:
                        if position == anchor:
                            mask &= delta_mask
                            self.metrics.domain_bitset_intersections += 1
                        elif position < anchor:
                            mask &= ~delta_mask
                            self.metrics.domain_bitset_intersections += 1
                    self.metrics.domain_bitset_intersections += intersections
                    self.metrics.candidate_facts += mask.bit_count()
                    for row in table_memory.rows_for_mask(mask):
                        self.metrics.match_attempts += 1
                        self.metrics.domain_compact_join_rows += 1
                        checkpoint = frame.checkpoint()
                        for variable, value in row.bindings:
                            if not frame.bind_ground(variable, value):
                                raise AssertionError(
                                    "compact row mask admitted conflicting "
                                    "binding"
                                )
                        supports.append(row.fact)
                        extend(position + 1, supports)
                        supports.pop()
                        frame.rollback(checkpoint)
                    return
                indexed = index.candidates_compiled(premise, frame)
                filtered = filtered_candidates[position]
                candidates: Sequence[Fact] = (
                    filtered
                    if len(filtered) < len(indexed)
                    else tuple(
                        fact
                        for fact in indexed
                        if fact in filtered_candidate_sets[position]
                    )
                )
                if anchor is not None:
                    delta_facts = delta_fact_sets.get(
                        position,
                        empty_delta_facts,
                    )
                    candidates = tuple(
                        fact
                        for fact in candidates
                        if (
                            fact in delta_facts
                            if position == anchor
                            else (
                                fact not in delta_facts
                                if position < anchor
                                else True
                            )
                        )
                    )
                self.metrics.candidate_facts += len(candidates)
                for fact in candidates:
                    self.metrics.match_attempts += 1
                    checkpoint = frame.checkpoint()
                    if premise.match(fact.entity, fact.status, frame):
                        supports.append(fact)
                        extend(position + 1, supports)
                        supports.pop()
                    frame.rollback(checkpoint)

            extend(0, [])

        for anchor in anchors:
            join_anchor(anchor)
        return sorted(unique.values(), key=index.activation_order)


@cache
def _compile_domain_plan(rule: Rule) -> _DomainPlan:
    block = compile_rule(rule).block
    tables: list[_TablePlan] = []
    comparisons: list[_ComparisonPlan] = []
    occurrences: dict[Variable, int] = {}
    fact_variables: set[Variable] = set()
    supported = True
    all_variables: set[Variable] = set()
    for position, premise in enumerate(block.premises):
        if isinstance(premise, CompiledFactPremise):
            variables = tuple(
                sorted(
                    variables_in(premise.source.entity)
                    | variables_in(premise.source.status),
                    key=lambda variable: variable.name,
                )
            )
            tables.append(_TablePlan(position, premise, variables))
            for variable in variables:
                occurrences[variable] = occurrences.get(variable, 0) + 1
                fact_variables.add(variable)
                all_variables.add(variable)
        elif isinstance(premise, CompiledComparisonPremise):
            variables = tuple(
                sorted(
                    variables_in_comparison_operand(premise.source.left)
                    | variables_in_comparison_operand(premise.source.right),
                    key=lambda variable: variable.name,
                )
            )
            comparisons.append(_ComparisonPlan(premise.source, variables))
            all_variables.update(variables)
        else:
            supported = False
    constrained = any(count > 1 for count in occurrences.values()) or bool(
        comparisons
    )
    applicable = (
        supported
        and bool(tables)
        and constrained
        and all_variables <= fact_variables
    )
    incidence: dict[Variable, list[_ConstraintKey]] = {
        variable: [] for variable in all_variables
    }
    for table in tables:
        for variable in table.variables:
            incidence[variable].append(("table", table.position))
    for index, comparison in enumerate(comparisons):
        for variable in comparison.variables:
            incidence[variable].append(("comparison", index))
    return _DomainPlan(
        tuple(tables),
        tuple(comparisons),
        tuple(sorted(all_variables, key=lambda variable: variable.name)),
        tuple(
            (variable, tuple(incidence[variable]))
            for variable in sorted(
                all_variables,
                key=lambda variable: variable.name,
            )
        ),
        _constraint_components(tables, comparisons, all_variables),
        _has_constraint_cycle(tables, comparisons),
        applicable,
    )


def _constraint_components(
    tables: Sequence[_TablePlan],
    comparisons: Sequence[_ComparisonPlan],
    variables: set[Variable],
) -> tuple[tuple[Variable, frozenset[Variable]], ...]:
    neighbors = {variable: set[Variable]() for variable in variables}
    scopes = (
        *(table.variables for table in tables),
        *(comparison.variables for comparison in comparisons),
    )
    for scope in scopes:
        scope_set = set(scope)
        for variable in scope:
            neighbors[variable].update(scope_set - {variable})
    component_by_variable: dict[Variable, frozenset[Variable]] = {}
    remaining = set(variables)
    while remaining:
        root = next(iter(remaining))
        component: set[Variable] = set()
        pending = [root]
        while pending:
            variable = pending.pop()
            if variable in component:
                continue
            component.add(variable)
            pending.extend(neighbors[variable] - component)
        frozen = frozenset(component)
        for variable in component:
            component_by_variable[variable] = frozen
        remaining.difference_update(component)
    return tuple(
        (variable, component_by_variable[variable])
        for variable in sorted(variables, key=lambda item: item.name)
    )


def _has_constraint_cycle(
    tables: Sequence[_TablePlan],
    comparisons: Sequence[_ComparisonPlan],
) -> bool:
    parent: dict[object, object] = {}

    def find(node: object) -> object:
        root = parent.setdefault(node, node)
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def connect(left: object, right: object) -> bool:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return True
        parent[right_root] = left_root
        return False

    constraints = (
        *(
            (("table", table.position), table.variables)
            for table in tables
        ),
        *(
            (("comparison", index), comparison.variables)
            for index, comparison in enumerate(comparisons)
        ),
    )
    for constraint, variables in constraints:
        constraint_node = ("constraint", constraint)
        for variable in variables:
            if connect(constraint_node, ("variable", variable)):
                return True
    return False


def _normalize_delta(
    delta: FactDelta | tuple[Fact, ...] | None,
) -> FactDelta | None:
    if delta is None or isinstance(delta, FactDelta):
        return delta
    return FactDelta(added=delta)


class AdaptiveInstantiationStrategy(ConstraintInstantiationStrategy):
    """Select domain filtering only for rules likely to amortize it."""

    def __init__(
        self,
        *,
        comparison_product_limit: int = 4_096,
        minimum_domain_rows: int = 128,
        minimum_bucket_ratio: float = 8.0,
        minimum_candidate_reduction: float = 0.10,
        minimum_observed_speedup: float = 1.05,
        cost_probe_reduction_ceiling: float = 0.75,
        minimum_cost_probe_uses: int = 8,
        use_compact_tables: bool = True,
        use_compact_join: bool = True,
        maximum_hall_size: int = 3,
        propagators: Sequence[DomainPropagator] = (),
    ) -> None:
        super().__init__(
            comparison_product_limit=comparison_product_limit,
            adaptive=True,
            minimum_domain_rows=minimum_domain_rows,
            minimum_bucket_ratio=minimum_bucket_ratio,
            minimum_candidate_reduction=minimum_candidate_reduction,
            minimum_observed_speedup=minimum_observed_speedup,
            cost_probe_reduction_ceiling=cost_probe_reduction_ceiling,
            minimum_cost_probe_uses=minimum_cost_probe_uses,
            use_compact_tables=use_compact_tables,
            use_compact_join=use_compact_join,
            maximum_hall_size=maximum_hall_size,
            propagators=propagators,
        )
