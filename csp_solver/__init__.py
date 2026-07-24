"""Declarative binary-CSP project built on Snarky choices."""

from .solver import (
    BinaryCSP,
    assignment_from_solution,
    binary_constraint_facts,
    solve_binary_csp,
)

__all__ = [
    "BinaryCSP",
    "assignment_from_solution",
    "binary_constraint_facts",
    "solve_binary_csp",
]
