"""Small, deterministic runner for the Ethics III theorem manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .engine import ForwardEngine
from .facts import Fact
from .parser import parse_rules, parse_term
from .rules import Rule
from .terms import Status


@dataclass(frozen=True, slots=True)
class CaseResult:
    theorem_id: str
    case_id: str
    goals: tuple[Fact, ...]
    proved: bool
    proof_depths: tuple[int | None, ...]
    rule_names: tuple[str, ...]


def load_historical_rules(root: Path) -> tuple[Rule, ...]:
    rules_path = root / "rules" / "historical.rules"
    return parse_rules(rules_path.read_text(encoding="utf-8"))


def run_case(
    root: Path,
    theorem_id: str,
    case_id: str,
    *,
    rules: tuple[Rule, ...] | None = None,
) -> CaseResult:
    theorem_path = root / "theorems" / f"{theorem_id}.yaml"
    payload: Any = yaml.safe_load(theorem_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    selected = next((case for case in cases if case.get("id") == case_id), None)
    if selected is None:
        raise ValueError(f"unknown case {theorem_id}/{case_id}")
    active_rules = rules if rules is not None else load_historical_rules(root)
    forbidden = set(payload.get("forbidden_rules", []))
    if any(rule.name in forbidden for rule in active_rules):
        raise ValueError(f"theorem {theorem_id} would be allowed to prove itself")
    initial_facts = tuple(
        Fact(parse_term(entity), Status.VRAI) for entity in selected["initial_facts"]
    )
    goals = tuple(Fact(parse_term(entity), Status.VRAI) for entity in selected["goals"])
    result = ForwardEngine(active_rules).run(initial_facts)
    proof_depths = tuple(
        result.provenance.depth(goal) if goal in result.facts else None
        for goal in goals
    )
    used_rules: list[str] = []
    visiting: set[Fact] = set()

    def visit_proof(fact: Fact) -> None:
        if result.provenance.depth(fact) == 0 or fact in visiting:
            return
        visiting.add(fact)
        derivation = result.provenance.minimal_derivation(fact)
        if derivation is None:
            visiting.remove(fact)
            return
        for premise in derivation.premises:
            visit_proof(premise)
        if derivation.rule_name not in used_rules:
            used_rules.append(derivation.rule_name)
        visiting.remove(fact)

    for goal in goals:
        visit_proof(goal)
    return CaseResult(
        theorem_id=theorem_id,
        case_id=case_id,
        goals=goals,
        proved=all(goal in result.facts for goal in goals),
        proof_depths=proof_depths,
        rule_names=tuple(used_rules),
    )
