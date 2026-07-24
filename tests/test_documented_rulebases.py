from pathlib import Path

import pytest
import yaml

from rulebases.runner import RULEBASE_ROOT, render_trace, run_scenario
from snarky import (
    Atom,
    Fact,
    ForwardEngine,
    Triple,
    parse_rule_groups,
    parse_term,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "rulebases" / "catalog.yaml"


SCENARIOS = (
    "small/fibonacci_explicit",
    "small/factorial_explicit",
    "thesis/equality_transitivity",
    "thesis/tomorrow_date",
    "thesis/petri_net",
    "thesis/geometry",
    "thesis/monkey_bananas/simple",
    "thesis/monkey_bananas/neopus_mea",
    "thesis/muses",
    "thesis/four_queens",
    "thesis/hanoi",
)


@pytest.mark.parametrize("relative_path", SCENARIOS)
def test_documented_rulebase_reaches_its_oracle(relative_path: str) -> None:
    result = run_scenario(relative_path)

    assert result.expected_facts
    assert result.missing_expected_facts == ()


def test_catalog_covers_every_documented_scenario() -> None:
    payload = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog_paths = {
        entry["path"] for entry in payload["rulebases"]
    }

    assert catalog_paths == set(SCENARIOS)

    for relative_path in catalog_paths:
        root = RULEBASE_ROOT / relative_path
        assert (root / "README.md").is_file()
        assert (root / "scenario.yaml").is_file()
        assert (root / "initial_facts.yaml").is_file()
        assert (root / "expected_facts.yaml").is_file()


def test_hanoi_is_solved_by_rules_in_recursive_execution_order() -> None:
    result = run_scenario("thesis/hanoi").result
    moves = tuple(
        entity.object
        for event in result.events
        if isinstance((entity := event.fact.entity), Triple)
        and entity.relation == Atom("move")
    )

    assert moves == tuple(
        parse_term(text)
        for text in (
            "SEQ[a c]",
            "SEQ[a b]",
            "SEQ[c b]",
            "SEQ[a c]",
            "SEQ[b a]",
            "SEQ[b c]",
            "SEQ[a c]",
        )
    )
    assert Fact(parse_term("(hanoi-root state done)")) in result.facts


def test_direct_and_incremental_queen_rules_find_the_same_two_solutions() -> None:
    result = run_scenario("thesis/four_queens").result

    def solutions(method: str) -> frozenset[object]:
        return frozenset(
            entity.subject
            for fact in result.facts
            if isinstance((entity := fact.entity), Triple)
            and entity.relation == Atom("queens_solution")
            and entity.object == Atom(method)
        )

    expected = frozenset(
        (
            parse_term(
                "SEQ[(2 cell 1) (4 cell 2) (1 cell 3) (3 cell 4)]"
            ),
            parse_term(
                "SEQ[(3 cell 1) (1 cell 2) (4 cell 3) (2 cell 4)]"
            ),
        )
    )

    assert solutions("direct") == expected
    assert solutions("incremental") == expected


def test_incremental_queen_rules_are_not_specialized_to_four() -> None:
    rules_path = RULEBASE_ROOT / "thesis/four_queens/rules.rules"
    groups = {
        group.name: group
        for group in parse_rule_groups(rules_path.read_text(encoding="utf-8"))
    }
    session = ForwardEngine(()).create_session(
        tuple(
            Fact(parse_term(text))
            for text in (
                "(board size 1)",
                "(row conflict_axis true)",
                "(column conflict_axis true)",
                "(diagonal_up conflict_axis true)",
                "(diagonal_down conflict_axis true)",
            )
        )
    )
    for name in ("build_board", "derive_attacks", "solve_n_queens"):
        session.run_group(groups[name])

    solution_candidates = {
        entity.subject
        for fact in session.facts
        if isinstance((entity := fact.entity), Triple)
        and entity.relation == Atom("state")
        and entity.object == Atom("solution")
    }

    assert len(solution_candidates) == 1
    (candidate,) = solution_candidates
    assert Fact(
        Triple(candidate, Atom("contains"), parse_term("(1 cell 1)"))
    ) in session.facts


@pytest.mark.parametrize(
    ("year", "expected"),
    ((1900, False), (2000, True), (2023, False), (2024, True)),
)
def test_tomorrow_rules_apply_the_gregorian_leap_year_rule(
    year: int,
    expected: bool,
) -> None:
    rules_path = RULEBASE_ROOT / "thesis/tomorrow_date/rules.rules"
    classify_year = parse_rule_groups(
        rules_path.read_text(encoding="utf-8")
    )[0]
    session = ForwardEngine(()).create_session(
        (Fact(parse_term(f"(current year {year})")),)
    )

    session.run_group(classify_year)

    expected_atom = str(expected).lower()
    assert Fact(parse_term(f"({year} leap {expected_atom})")) in session.facts


def test_neopus_monkey_builds_and_solves_a_depth_first_goal_tree() -> None:
    result = run_scenario("thesis/monkey_bananas/neopus_mea").result
    trace = render_trace(result)

    assert "[001] MEA" in trace
    assert "generate_move_climbable_below_ceiling_object" in trace
    assert "+ (goal-2 status active)" in trace
    assert "[012] MEA" in trace
    assert [
        selection.rule_name for selection in result.agenda_selections
    ] == [
        "generate_move_climbable_below_ceiling_object",
        "generate_get_down_before_transport",
        "satisfy_on_floor_by_getting_down",
        "generate_hold_object_before_transport",
        "satisfy_holds_floor_object_by_picking_up",
        "satisfy_at_object_by_carrying",
        "generate_climb_below_ceiling_object",
        "generate_empty_hands_before_climbing",
        "satisfy_holds_nothing_by_dropping",
        "satisfy_on_climbable_by_climbing",
        "satisfy_holds_ceiling_object",
        "finish_when_root_goal_is_satisfied",
    ]
    for parent, child in (
        ("goal-1", "goal-2"),
        ("goal-2", "goal-3"),
        ("goal-2", "goal-4"),
        ("goal-1", "goal-5"),
        ("goal-5", "goal-6"),
    ):
        assert Fact(parse_term(f"({child} parent {parent})")) in result.facts
    assert not any(
        fact.entity == parse_term(f"({goal} status active)")
        for goal in (
            "goal-1",
            "goal-2",
            "goal-3",
            "goal-4",
            "goal-5",
            "goal-6",
        )
        for fact in result.facts
    )
