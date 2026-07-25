"""Declarative finite-CSP project built on Snarky choices."""

from .constraint_syntax import (
    PersistentConstraintKind,
    PersistentConstraintTemplate,
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from .persistent_constraints import (
    AllDifferentConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    PersistentConstraint,
    PersistentConstraintPropagator,
    SumConstraint,
    TableConstraint,
)
from .solver import (
    BinaryCSP,
    FiniteCSP,
    FiniteCSPRuleLibrary,
    assignment_from_solution,
    binary_constraint_facts,
    constraint_dom_wdeg_policy,
    constraint_propagation_guided_policy,
    finite_csp_rule_library,
    solve_binary_csp,
    solve_finite_csp,
)

__all__ = [
    "AllDifferentConstraint",
    "BinaryCSP",
    "FiniteCSP",
    "FiniteCSPRuleLibrary",
    "GlobalCardinalityConstraint",
    "LexLessEqualConstraint",
    "PersistentConstraint",
    "PersistentConstraintKind",
    "PersistentConstraintPropagator",
    "PersistentConstraintTemplate",
    "SumConstraint",
    "TableConstraint",
    "assignment_from_solution",
    "binary_constraint_facts",
    "constraint_dom_wdeg_policy",
    "constraint_propagation_guided_policy",
    "finite_csp_rule_library",
    "instantiate_constraint_templates",
    "parse_constraint_templates",
    "solve_binary_csp",
    "solve_finite_csp",
]
