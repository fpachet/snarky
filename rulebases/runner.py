"""Run one documented rule-base scenario and verify its expected facts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from snarky import (
    Fact,
    FactMutationKind,
    ForwardEngine,
    InstantiationStrategy,
    MEAConflictStrategy,
    RunResult,
    Status,
    Triple,
    parse_rule_groups,
    parse_rules,
    render_term,
)
from snarky.serialization.yaml_format import load_facts

RULEBASE_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    """Result and oracle information for one documented scenario."""

    path: Path
    result: RunResult
    expected_facts: tuple[Fact, ...]

    @property
    def missing_expected_facts(self) -> tuple[Fact, ...]:
        facts = frozenset(self.result.facts)
        return tuple(fact for fact in self.expected_facts if fact not in facts)


def run_scenario(
    relative_path: str | Path,
    *,
    strategy: InstantiationStrategy | None = None,
) -> ScenarioResult:
    """Execute the scenario rooted at *relative_path*."""

    path = (RULEBASE_ROOT / relative_path).resolve()
    if RULEBASE_ROOT not in path.parents:
        raise ValueError("scenario path must stay inside rulebases/")
    payload = _load_scenario(path / "scenario.yaml")
    initial_facts = load_facts(path / payload["facts"])
    rules_text = (path / payload["rules"]).read_text(encoding="utf-8")
    conflict_strategy = (
        MEAConflictStrategy()
        if payload.get("conflict_strategy") == "mea"
        else None
    )

    if payload["kind"] == "rules":
        result = ForwardEngine(
            parse_rules(rules_text),
            strategy=strategy,
            conflict_strategy=conflict_strategy,
        ).run(initial_facts)
    else:
        groups = {
            group.name: group for group in parse_rule_groups(rules_text)
        }
        order = payload["group_order"]
        unknown = [name for name in order if name not in groups]
        if unknown:
            raise ValueError(f"unknown groups in scenario: {unknown}")
        session = ForwardEngine(
            (),
            strategy=strategy,
            conflict_strategy=conflict_strategy,
        ).create_session(initial_facts)
        for _ in range(payload["max_rounds"]):
            event_count = len(session.events)
            for name in order:
                session.run_group(groups[name])
            if len(session.events) == event_count:
                break
        else:
            raise RuntimeError("scenario did not reach a fixed point")
        result = session.snapshot()

    return ScenarioResult(
        path=path,
        result=result,
        expected_facts=load_facts(path / payload["expected_facts"]),
    )


def _load_scenario(path: Path) -> dict[str, Any]:
    payload: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"{path}: expected schema_version: 1")
    kind = payload.get("kind")
    if kind not in {"rules", "groups"}:
        raise ValueError(f"{path}: kind must be rules or groups")
    for key in ("rules", "facts", "expected_facts"):
        if not isinstance(payload.get(key), str):
            raise ValueError(f"{path}: {key} must be a path")
    if kind == "groups":
        group_order = payload.get("group_order")
        if not isinstance(group_order, list) or not all(
            isinstance(name, str) for name in group_order
        ):
            raise ValueError(f"{path}: group_order must be a list of names")
        max_rounds = payload.get("max_rounds", 20)
        if not isinstance(max_rounds, int) or max_rounds < 1:
            raise ValueError(f"{path}: max_rounds must be positive")
        payload["max_rounds"] = max_rounds
    conflict_strategy = payload.get("conflict_strategy")
    if conflict_strategy not in {None, "mea"}:
        raise ValueError(
            f"{path}: conflict_strategy must be omitted or mea"
        )
    return payload


def render_trace(result: RunResult) -> str:
    """Render agenda choices and their working-memory mutations."""

    lines: list[str] = []
    if not result.agenda_selections:
        for event in result.events:
            marker = "+" if event.kind is FactMutationKind.ADD else "-"
            lines.append(
                f"[{event.sequence:03d}] {marker} {_render_fact(event.fact)} "
                f"({event.rule_name})"
            )
        return "\n".join(lines)

    parent_by_goal = _goal_parents(result.facts)
    events_by_cycle: dict[int, list[str]] = {}
    for event in result.events:
        marker = "+" if event.kind is FactMutationKind.ADD else "-"
        events_by_cycle.setdefault(event.cycle, []).append(
            f"{marker} {_render_fact(event.fact)}"
        )
    for selection in result.agenda_selections:
        focus = (
            _render_fact(selection.focus_fact)
            if selection.focus_fact is not None
            else "<no factual focus>"
        )
        indentation = "  " * _goal_depth(
            selection.focus_fact,
            parent_by_goal,
        )
        lines.append(
            f"[{selection.sequence:03d}] {indentation}"
            f"{selection.strategy_name.upper()} "
            f"t={selection.focus_time_tag} "
            f"{selection.rule_name} <- {focus}"
        )
        lines.extend(
            f"      {indentation}{event}"
            for event in events_by_cycle.get(selection.cycle, ())
        )
    return "\n".join(lines)


def _render_fact(fact: Fact) -> str:
    entity = render_term(fact.entity)
    if fact.status is Status.VRAI:
        return entity
    return f"{entity} ' {render_term(fact.status)}"


def _goal_parents(facts: tuple[Fact, ...]) -> dict[object, object]:
    parents: dict[object, object] = {}
    for fact in facts:
        entity = fact.entity
        if (
            fact.status is Status.VRAI
            and isinstance(entity, Triple)
            and render_term(entity.relation) == "parent"
        ):
            parents[entity.subject] = entity.object
    return parents


def _goal_depth(
    focus_fact: Fact | None,
    parent_by_goal: dict[object, object],
) -> int:
    if focus_fact is None or not isinstance(focus_fact.entity, Triple):
        return 0
    entity = focus_fact.entity
    if render_term(entity.relation) != "status":
        return 0
    depth = 0
    goal: object = entity.subject
    seen: set[object] = set()
    while goal in parent_by_goal and goal not in seen:
        seen.add(goal)
        goal = parent_by_goal[goal]
        depth += 1
    return depth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", help="path relative to rulebases/")
    parser.add_argument(
        "--trace",
        action="store_true",
        help="print agenda choices and working-memory mutations",
    )
    arguments = parser.parse_args()
    result = run_scenario(arguments.scenario)
    missing = result.missing_expected_facts
    print(
        f"{arguments.scenario}: {len(result.result.facts)} facts, "
        f"{result.result.fired_activation_count} activations, "
        f"{result.result.cycles} cycles"
    )
    if missing:
        for fact in missing:
            print(f"missing: {fact}")
        raise SystemExit(1)
    print(f"oracle: {len(result.expected_facts)} expected facts found")
    if arguments.trace:
        print(render_trace(result.result))


if __name__ == "__main__":
    main()
