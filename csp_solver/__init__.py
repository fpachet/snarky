"""Declarative finite-CSP project built on Snarky choices."""

from .solver import (
    BinaryCSP,
    FiniteCSP,
    assignment_from_solution,
    binary_constraint_facts,
    solve_binary_csp,
    solve_finite_csp,
)

__all__ = [
    "BinaryCSP",
    "FiniteCSP",
    "assignment_from_solution",
    "binary_constraint_facts",
    "solve_binary_csp",
    "solve_finite_csp",
]
