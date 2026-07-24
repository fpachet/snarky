"""Loading and ordering of the native Sudoku rule groups."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from snarky import RuleGroup, parse_rule_groups

RULE_ROOT = Path(__file__).resolve().parent / "rules"
RULE_FILES = (
    "topology.rules",
    "singles.rules",
    "locked_candidates.rules",
    "pairs.rules",
    "x_wing.rules",
    "validation.rules",
)
TECHNIQUE_ORDER = (
    "naked_singles",
    "hidden_singles",
    "locked_candidates_single_line",
    "locked_candidates_multiple_lines",
    "naked_pairs",
    "hidden_pairs",
    "x_wing",
)


@dataclass(frozen=True, slots=True)
class SudokuRuleBase:
    """Named groups and their human-technique execution order."""

    groups: Mapping[str, RuleGroup]
    techniques: tuple[RuleGroup, ...]
    derive_solved_cells: RuleGroup
    validate_state: RuleGroup


def load_rulebase() -> SudokuRuleBase:
    """Parse every native rule file and validate the expected group inventory."""

    parsed: list[RuleGroup] = []
    for filename in RULE_FILES:
        parsed.extend(
            parse_rule_groups(
                (RULE_ROOT / filename).read_text(encoding="utf-8")
            )
        )
    groups = {group.name: group for group in parsed}
    if len(groups) != len(parsed):
        raise ValueError("duplicate Sudoku rule-group name")
    expected = {
        "derive_solved_cells",
        *TECHNIQUE_ORDER,
        "validate_state",
    }
    if groups.keys() != expected:
        missing = sorted(expected - groups.keys())
        extra = sorted(groups.keys() - expected)
        raise ValueError(
            f"unexpected Sudoku rule groups; missing={missing}, extra={extra}"
        )
    return SudokuRuleBase(
        groups=MappingProxyType(groups),
        techniques=tuple(groups[name] for name in TECHNIQUE_ORDER),
        derive_solved_cells=groups["derive_solved_cells"],
        validate_state=groups["validate_state"],
    )
