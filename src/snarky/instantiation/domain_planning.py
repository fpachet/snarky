"""Compilation and graph analysis for finite-domain plans."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache

from ..premises import (
    ComparisonPremise,
    variables_in_comparison_operand,
)
from ..rules import Rule
from ..terms import Variable, variables_in
from .compiled import (
    CompiledComparisonPremise,
    CompiledFactPremise,
    compile_rule,
)


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
    ordered_variables = tuple(
        sorted(all_variables, key=lambda variable: variable.name)
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
        ordered_variables,
        tuple(
            (variable, tuple(incidence[variable]))
            for variable in ordered_variables
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
        if not scope:
            continue
        root, *connected = scope
        neighbors[root].update(connected)
        for variable in connected:
            neighbors[variable].add(root)
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
