"""Declarative finite-CSP project built on Snarky choices."""

from .solver import (
    BinaryCSP,
    FiniteCSP,
    FiniteCSPRuleLibrary,
    assignment_from_solution,
    binary_constraint_facts,
    finite_csp_rule_library,
    solve_binary_csp,
    solve_finite_csp,
)

__all__ = [
    "BinaryCSP",
    "FiniteCSP",
    "FiniteCSPRuleLibrary",
    "assignment_from_solution",
    "binary_constraint_facts",
    "finite_csp_rule_library",
    "solve_binary_csp",
    "solve_finite_csp",
]
