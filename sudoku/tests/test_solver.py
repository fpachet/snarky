import pytest

from snarky import Fact, TechniquePlanStatus, parse_term
from sudoku import initial_facts, replay_events, solve_level

PREVIOUS_TECHNIQUE = {
    2: "naked_singles",
    3: "hidden_singles",
    4: "locked_candidates_single_line",
    5: "locked_candidates_multiple_lines",
    6: "naked_pairs",
}


@pytest.mark.parametrize("level", range(1, 7))
def test_p1_to_p6_are_solved_with_exactly_the_expected_techniques(
    level: int,
) -> None:
    result = solve_level(level)

    assert result.status is TechniquePlanStatus.SOLVED
    assert result.grid == result.puzzle.solution
    assert result.techniques_used == result.puzzle.techniques
    assert result.steps
    assert all(step.explanation for step in result.steps)

    replayed = replay_events(
        initial_facts(result.puzzle),
        result.inference.events,
    )
    assert replayed == result.inference.facts

    for row in range(1, 10):
        for column in range(1, 10):
            value = result.puzzle.solution[row - 1][column - 1]
            solved = Fact(parse_term(f"(r{row}c{column} solved {value})"))
            derivation = result.inference.provenance.minimal_derivation(solved)
            assert derivation is not None
            assert derivation.rule_group == "derive_solved_cells"


@pytest.mark.parametrize("level", range(2, 7))
def test_disabling_the_required_last_technique_leaves_the_grid_stuck(
    level: int,
) -> None:
    result = solve_level(level, max_technique=PREVIOUS_TECHNIQUE[level])

    assert result.status is TechniquePlanStatus.STUCK
    assert result.grid is None
    assert result.puzzle.techniques[-1] not in result.techniques_used


def test_event_trace_contains_every_candidate_elimination() -> None:
    result = solve_level(1)
    removed_candidates = [
        event
        for event in result.inference.events
        if event.kind.value == "remove"
    ]

    assert len(result.steps) == len(removed_candidates)
    assert {step.technique for step in result.steps} == {"Naked Single"}
