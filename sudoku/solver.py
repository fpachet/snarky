"""Human-style Sudoku orchestration over native Snarky rule groups."""

from __future__ import annotations

from dataclasses import dataclass

from snarky import (
    Atom,
    Fact,
    FactExists,
    FactMutationKind,
    GroupExecutionMode,
    GroupRunResult,
    IndexedInstantiationStrategy,
    InferenceEvent,
    InferenceSession,
    InstantiationStrategy,
    RunResult,
    TechniquePlan,
    TechniquePlanResult,
    TechniquePlanStatus,
    Triple,
    Variable,
    render_term,
    when,
)

from .domain import (
    Grid,
    SudokuPuzzle,
    grid_from_facts,
    initial_facts,
    load_puzzle,
    validate_complete_grid,
)
from .rulebase import TECHNIQUE_ORDER, load_rulebase

TECHNIQUE_LABELS = {
    "naked_singles": "Naked Single",
    "hidden_singles": "Hidden Single",
    "locked_candidates_single_line": "Locked Candidate Single Line",
    "locked_candidates_multiple_lines": "Locked Candidate Multiple Lines",
    "naked_pairs": "Naked Pairs",
    "hidden_pairs": "Hidden Pairs",
    "x_wing": "X Wing",
}


@dataclass(frozen=True, slots=True)
class SudokuStep:
    """One effective human-technique invocation."""

    number: int
    technique: str
    group_name: str
    events: tuple[InferenceEvent, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class SudokuSolveResult:
    """Solved or blocked Sudoku state with a replayable explanation trace."""

    puzzle: SudokuPuzzle
    status: TechniquePlanStatus
    grid: Grid | None
    steps: tuple[SudokuStep, ...]
    techniques_used: tuple[str, ...]
    plan_result: TechniquePlanResult
    inference: RunResult


def solve_level(
    level: int,
    *,
    max_technique: str | None = None,
    strategy: InstantiationStrategy | None = None,
) -> SudokuSolveResult:
    """Load and solve one supported official Sudoku level."""

    return solve_puzzle(
        load_puzzle(level),
        max_technique=max_technique,
        strategy=strategy,
    )


def solve_puzzle(
    puzzle: SudokuPuzzle,
    *,
    max_technique: str | None = None,
    strategy: InstantiationStrategy | None = None,
) -> SudokuSolveResult:
    """Solve a native puzzle with ordered, restart-on-progress techniques."""

    rulebase = load_rulebase()
    techniques = rulebase.techniques
    if max_technique is not None:
        try:
            last = TECHNIQUE_ORDER.index(max_technique)
        except ValueError as error:
            raise ValueError(f"unknown Sudoku technique {max_technique!r}") from error
        techniques = techniques[: last + 1]

    session = InferenceSession(
        initial_facts(puzzle),
        strategy=strategy or IndexedInstantiationStrategy(),
    )
    plan = TechniquePlan(
        techniques=techniques,
        maintenance=(
            rulebase.derive_solved_cells,
            rulebase.validate_state,
        ),
        execution_mode=GroupExecutionMode.SATURATE,
    )
    plan_result = plan.solve(
        session,
        solved=_state_condition("solved"),
        inconsistent=_state_condition("inconsistent"),
    )
    grid = (
        grid_from_facts(session.facts)
        if plan_result.status is TechniquePlanStatus.SOLVED
        else None
    )
    if grid is not None:
        validate_complete_grid(grid, clues=puzzle.grid)

    steps = _make_steps(plan_result.effective_steps)
    techniques_used = tuple(dict.fromkeys(step.technique for step in steps))
    return SudokuSolveResult(
        puzzle=puzzle,
        status=plan_result.status,
        grid=grid,
        steps=steps,
        techniques_used=techniques_used,
        plan_result=plan_result,
        inference=session.snapshot(),
    )


def replay_events(
    initial: tuple[Fact, ...],
    events: tuple[InferenceEvent, ...],
) -> tuple[Fact, ...]:
    """Replay effective mutations independently of the inference engine."""

    memory = dict.fromkeys(initial)
    for event in events:
        if event.kind.value == "add":
            memory[event.fact] = None
        else:
            memory.pop(event.fact, None)
    return tuple(memory)


def _state_condition(value: str) -> FactExists:
    return FactExists(
        when(Triple(Atom("sudoku"), Atom("state"), Atom(value)))
    )


def _make_steps(results: tuple[GroupRunResult, ...]) -> tuple[SudokuStep, ...]:
    steps: list[SudokuStep] = []
    for result in results:
        technique = TECHNIQUE_LABELS[result.group_name]
        for event in result.events:
            if event.kind is not FactMutationKind.REMOVE:
                continue
            steps.append(
                SudokuStep(
                    number=len(steps) + 1,
                    technique=technique,
                    group_name=result.group_name,
                    events=(event,),
                    explanation=_explain(event, result.group_name, technique),
                )
            )
    return tuple(steps)


def _explain(
    event: InferenceEvent,
    group_name: str,
    technique: str,
) -> str:
    removed = event.fact.entity
    if not isinstance(removed, Triple):
        return f"{technique}: working-memory update."
    cell = removed.subject
    discarded = removed.object
    rendered_cell = render_term(cell)
    rendered_discarded = render_term(discarded)
    substitution = event.substitution
    if group_name == "naked_singles":
        support = next(
            (
                premise.entity.subject
                for premise in event.premises
                if isinstance(premise.entity, Triple)
                and premise.entity.relation == Atom("solved")
            ),
            Atom("a solved cell"),
        )
        return (
            f"{technique}: remove {rendered_discarded} from {rendered_cell} "
            f"because {render_term(support)} already has that value in the "
            "same unit."
        )
    if group_name == "hidden_singles":
        value = substitution[Variable("value")]
        unit = substitution[Variable("unit")]
        return (
            f"{technique}: {render_term(value)} occurs only in "
            f"{rendered_cell} within {render_term(unit)}; remove "
            f"{rendered_discarded} from that cell."
        )
    if group_name.startswith("locked_candidates"):
        value = substitution[Variable("value")]
        return (
            f"{technique}: candidate {render_term(value)} is locked to an "
            f"intersection; remove it from {rendered_cell}."
        )
    if group_name == "x_wing":
        value = substitution[Variable("value")]
        return (
            f"{technique}: candidate {render_term(value)} is restricted to "
            "the same two rows or columns; remove it from "
            f"{rendered_cell} outside the rectangle."
        )
    first = substitution[Variable("first_value")]
    second = substitution[Variable("second_value")]
    unit = substitution[Variable("unit")]
    return (
        f"{technique}: pair {{{render_term(first)}, {render_term(second)}}} "
        f"is confined within {render_term(unit)}; remove "
        f"{rendered_discarded} from {rendered_cell}."
    )
