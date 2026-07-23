"""Human-style Sudoku case study for Snarky."""

from .domain import (
    SudokuPuzzle,
    SudokuValidationError,
    candidates_from_facts,
    grid_from_facts,
    initial_facts,
    load_puzzle,
    validate_complete_grid,
)
from .rulebase import SudokuRuleBase, load_rulebase
from .solver import (
    SudokuSolveResult,
    SudokuStep,
    replay_events,
    solve_level,
    solve_puzzle,
)

__all__ = [
    "SudokuPuzzle",
    "SudokuRuleBase",
    "SudokuSolveResult",
    "SudokuStep",
    "SudokuValidationError",
    "candidates_from_facts",
    "grid_from_facts",
    "initial_facts",
    "load_puzzle",
    "load_rulebase",
    "replay_events",
    "solve_level",
    "solve_puzzle",
    "validate_complete_grid",
]
