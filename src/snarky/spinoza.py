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
from .serialization import load_facts
from .terms import Status


@dataclass(frozen=True, slots=True)
class CaseResult:
    theorem_id: str
    case_id: str
    goals: tuple[Fact, ...]
    proved: bool
    proof_depths: tuple[int | None, ...]
    rule_names: tuple[str, ...]
    rule_origins: tuple[str, ...]
    forbidden_facts: tuple[Fact, ...]
    forbidden_violations: tuple[Fact, ...]
    initial_fact_count: int
    derived_fact_count: int
    total_fact_count: int
    derivation_count: int
    activated_rule_names: tuple[str, ...]


def load_historical_rules(root: Path) -> tuple[Rule, ...]:
    rules_path = root / "rules" / "historical.rules"
    return parse_rules(rules_path.read_text(encoding="utf-8"))


def _load_manifest_rules(root: Path, payload: dict[str, Any]) -> tuple[Rule, ...]:
    rule_files = payload.get("rule_files")
    if rule_files is None:
        return load_historical_rules(root)
    if not isinstance(rule_files, list) or not all(
        isinstance(item, str) for item in rule_files
    ):
        raise ValueError("rule_files must be a list of relative paths")
    rule_source = "\n".join(
        (root / relative_path).read_text(encoding="utf-8")
        for relative_path in rule_files
    )
    return parse_rules(rule_source)


def _load_manifest_fact(entry: Any) -> Fact:
    if isinstance(entry, str):
        return Fact(parse_term(entry), Status.VRAI)
    if not isinstance(entry, dict):
        raise ValueError("a theorem fact must be a string or a mapping")
    entity = entry.get("entity")
    status = entry.get("status", "VRAI")
    if not isinstance(entity, str) or not isinstance(status, str):
        raise ValueError("a theorem fact needs string entity and status values")
    return Fact(parse_term(entity), parse_term(status))


def _load_background_facts(root: Path, payload: dict[str, Any]) -> tuple[Fact, ...]:
    fact_files = payload.get("fact_files", [])
    if not isinstance(fact_files, list) or not all(
        isinstance(item, str) for item in fact_files
    ):
        raise ValueError("fact_files must be a list of relative paths")
    return tuple(
        fact
        for relative_path in fact_files
        for fact in load_facts(root / relative_path)
    )


def _load_rule_origins(
    root: Path,
    payload: dict[str, Any],
    active_rules: tuple[Rule, ...],
) -> dict[str, str]:
    catalog_path = payload.get("rule_catalog")
    if catalog_path is None:
        return {}
    if not isinstance(catalog_path, str):
        raise ValueError("rule_catalog must be a relative path")
    loaded: Any = yaml.safe_load((root / catalog_path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not isinstance(loaded.get("rules"), list):
        raise ValueError("rule_catalog must contain a rules list")
    origins: dict[str, str] = {}
    for entry in loaded["rules"]:
        if not isinstance(entry, dict):
            raise ValueError("each rule catalog entry must be a mapping")
        identifiers = entry.get("ids")
        origin = entry.get("origin")
        if not isinstance(identifiers, list) or not isinstance(origin, str):
            raise ValueError("each catalog entry needs ids and origin")
        for identifier in identifiers:
            if not isinstance(identifier, str) or identifier in origins:
                raise ValueError(f"invalid or duplicate catalog id: {identifier!r}")
            origins[identifier] = origin
    missing = {rule.name for rule in active_rules} - origins.keys()
    if missing:
        raise ValueError(f"rules missing from catalog: {sorted(missing)!r}")
    allowed = payload.get("allowed_rule_origins")
    if allowed is not None:
        if not isinstance(allowed, list) or not all(
            isinstance(item, str) for item in allowed
        ):
            raise ValueError("allowed_rule_origins must be a list of strings")
        disallowed = {
            rule.name: origins[rule.name]
            for rule in active_rules
            if origins[rule.name] not in allowed
        }
        if disallowed:
            raise ValueError(f"disallowed rule origins: {disallowed!r}")
    return origins


def run_case(
    root: Path,
    theorem_id: str,
    case_id: str,
    *,
    rules: tuple[Rule, ...] | None = None,
) -> CaseResult:
    manifest_directories = (
        ("definitions", "theorems")
        if theorem_id.startswith("E3DA")
        else ("theorems", "definitions")
    )
    theorem_path = next(
        (
            candidate
            for directory in manifest_directories
            if (candidate := root / directory / f"{theorem_id}.yaml").is_file()
        ),
        root / manifest_directories[0] / f"{theorem_id}.yaml",
    )
    loaded: Any = yaml.safe_load(theorem_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{theorem_path}: expected a theorem mapping")
    payload: dict[str, Any] = loaded
    cases = payload.get("cases", [])
    selected = next((case for case in cases if case.get("id") == case_id), None)
    if selected is None:
        raise ValueError(f"unknown case {theorem_id}/{case_id}")
    active_rules = rules if rules is not None else _load_manifest_rules(root, payload)
    rule_origins = _load_rule_origins(root, payload, active_rules)
    forbidden = set(payload.get("forbidden_rules", []))
    if any(rule.name in forbidden for rule in active_rules):
        raise ValueError(f"theorem {theorem_id} would be allowed to prove itself")
    initial_facts = (
        *_load_background_facts(root, payload),
        *(_load_manifest_fact(entry) for entry in selected["initial_facts"]),
    )
    goals = tuple(_load_manifest_fact(entry) for entry in selected["goals"])
    forbidden_facts = tuple(
        _load_manifest_fact(entry) for entry in selected.get("must_not_derive", [])
    )
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
        if goal in result.facts:
            visit_proof(goal)
    forbidden_violations = tuple(
        fact for fact in forbidden_facts if fact in result.facts
    )
    return CaseResult(
        theorem_id=theorem_id,
        case_id=case_id,
        goals=goals,
        proved=(
            all(goal in result.facts for goal in goals) and not forbidden_violations
        ),
        proof_depths=proof_depths,
        rule_names=tuple(used_rules),
        rule_origins=tuple(
            rule_origins.get(rule_name, "unclassified") for rule_name in used_rules
        ),
        forbidden_facts=forbidden_facts,
        forbidden_violations=forbidden_violations,
        initial_fact_count=len(frozenset(initial_facts)),
        derived_fact_count=len(result.derived_facts),
        total_fact_count=len(result.facts),
        derivation_count=len(result.derivations),
        activated_rule_names=tuple(
            dict.fromkeys(derivation.rule_name for derivation in result.derivations)
        ),
    )
