"""Native Sudoku facts, fixtures, and independent validation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from snarky import Atom, Fact, Number, Triple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
GRID_SIZE = 9

type Grid = tuple[tuple[int, ...], ...]
type Cell = tuple[int, int]


class SudokuValidationError(ValueError):
    """Raised when a fixture or completed grid violates Sudoku constraints."""


@dataclass(frozen=True, slots=True)
class SudokuPuzzle:
    """One native puzzle and its independent solution oracle."""

    puzzle_id: str
    grid: Grid
    solution: Grid
    techniques: tuple[str, ...]
    source: str
    source_sha256: str


def load_puzzle(level: int, *, verify_source: bool = True) -> SudokuPuzzle:
    """Load one native p1–p6 fixture and optionally verify its CLIPS source."""

    path = FIXTURE_ROOT / f"grid3x3-p{level}.yaml"
    if not path.is_file():
        raise ValueError(f"unsupported Sudoku level p{level}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    puzzle = SudokuPuzzle(
        puzzle_id=str(data["id"]),
        grid=_parse_grid(data["grid"]),
        solution=_parse_grid(data["solution"]),
        techniques=tuple(str(item) for item in data["techniques"]),
        source=str(data["source"]),
        source_sha256=str(data["source_sha256"]),
    )
    validate_complete_grid(puzzle.solution, clues=puzzle.grid)
    if verify_source:
        source_path = PROJECT_ROOT / puzzle.source
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if digest != puzzle.source_sha256:
            raise SudokuValidationError(
                f"source checksum mismatch for {puzzle.puzzle_id}"
            )
    return puzzle


def initial_facts(puzzle: SudokuPuzzle) -> tuple[Fact, ...]:
    """Expand a puzzle into topology and candidate facts."""

    facts: list[Fact] = [
        Fact(Triple(Atom("sudoku"), Atom("state"), Atom("active")))
    ]
    for row in range(1, GRID_SIZE + 1):
        for column in range(1, GRID_SIZE + 1):
            cell = cell_atom(row, column)
            box = box_number(row, column)
            index = (row - 1) * GRID_SIZE + column
            facts.extend(
                (
                    _triple_fact(cell, "row", Number(row)),
                    _triple_fact(cell, "column", Number(column)),
                    _triple_fact(cell, "box", Number(box)),
                    _triple_fact(cell, "index", Number(index)),
                    _triple_fact(cell, "unit", Atom(f"row-{row}")),
                    _triple_fact(cell, "unit", Atom(f"column-{column}")),
                    _triple_fact(cell, "unit", Atom(f"box-{box}")),
                )
            )
            clue = puzzle.grid[row - 1][column - 1]
            values = (clue,) if clue else range(1, GRID_SIZE + 1)
            facts.extend(
                _triple_fact(cell, "candidate", Number(value))
                for value in values
            )
    return tuple(facts)


def candidates_from_facts(
    facts: tuple[Fact, ...],
) -> dict[Cell, frozenset[int]]:
    """Extract current candidate sets from a Snarky fact snapshot."""

    candidates: dict[Cell, set[int]] = {
        (row, column): set()
        for row in range(1, GRID_SIZE + 1)
        for column in range(1, GRID_SIZE + 1)
    }
    for fact in facts:
        entity = fact.entity
        if (
            isinstance(entity, Triple)
            and entity.relation == Atom("candidate")
            and isinstance(entity.subject, Atom)
            and isinstance(entity.object, Number)
            and isinstance(entity.object.value, int)
        ):
            cell = parse_cell_atom(entity.subject)
            candidates[cell].add(entity.object.value)
    return {cell: frozenset(values) for cell, values in candidates.items()}


def grid_from_facts(facts: tuple[Fact, ...]) -> Grid:
    """Return a complete grid or raise if any cell is not singleton."""

    candidates = candidates_from_facts(facts)
    rows: list[tuple[int, ...]] = []
    for row in range(1, GRID_SIZE + 1):
        values: list[int] = []
        for column in range(1, GRID_SIZE + 1):
            cell_values = candidates[(row, column)]
            if len(cell_values) != 1:
                raise SudokuValidationError(
                    f"cell r{row}c{column} has {len(cell_values)} candidates"
                )
            values.append(next(iter(cell_values)))
        rows.append(tuple(values))
    return tuple(rows)


def validate_complete_grid(grid: Grid, *, clues: Grid | None = None) -> None:
    """Validate shape, clues, and every row, column, and box."""

    if len(grid) != GRID_SIZE or any(
        len(row) != GRID_SIZE for row in grid
    ):
        raise SudokuValidationError("a Sudoku grid must be 9x9")
    expected = set(range(1, GRID_SIZE + 1))
    for index, row_values in enumerate(grid, start=1):
        if set(row_values) != expected:
            raise SudokuValidationError(f"row {index} is invalid")
    for column in range(GRID_SIZE):
        values = {
            grid[row_index][column] for row_index in range(GRID_SIZE)
        }
        if values != expected:
            raise SudokuValidationError(f"column {column + 1} is invalid")
    for box_row in range(0, GRID_SIZE, 3):
        for box_column in range(0, GRID_SIZE, 3):
            values = {
                grid[row_index][column]
                for row_index in range(box_row, box_row + 3)
                for column in range(box_column, box_column + 3)
            }
            if values != expected:
                box = (box_row // 3) * 3 + box_column // 3 + 1
                raise SudokuValidationError(f"box {box} is invalid")
    if clues is not None:
        for row_index in range(GRID_SIZE):
            for column in range(GRID_SIZE):
                clue = clues[row_index][column]
                if clue and grid[row_index][column] != clue:
                    raise SudokuValidationError(
                        f"solution violates clue r{row_index + 1}c{column + 1}"
                    )


def cell_atom(row: int, column: int) -> Atom:
    """Return the stable atom identifying one cell."""

    return Atom(f"r{row}c{column}")


def parse_cell_atom(atom: Atom) -> Cell:
    """Decode a cell atom generated by :func:`cell_atom`."""

    name = atom.name
    if len(name) != 4 or name[0] != "r" or name[2] != "c":
        raise SudokuValidationError(f"invalid cell atom {name!r}")
    row = int(name[1])
    column = int(name[3])
    if not 1 <= row <= GRID_SIZE or not 1 <= column <= GRID_SIZE:
        raise SudokuValidationError(f"invalid cell atom {name!r}")
    return row, column


def box_number(row: int, column: int) -> int:
    """Return the 1-based 3×3 box number for a cell."""

    return ((row - 1) // 3) * 3 + (column - 1) // 3 + 1


def _parse_grid(rows: object) -> Grid:
    if not isinstance(rows, list) or len(rows) != GRID_SIZE:
        raise SudokuValidationError("fixture grid must contain nine rows")
    parsed: list[tuple[int, ...]] = []
    for row in rows:
        if not isinstance(row, str) or len(row) != GRID_SIZE:
            raise SudokuValidationError(
                "each fixture row must be a nine-character string"
            )
        values = tuple(int(character) for character in row)
        if any(not 0 <= value <= GRID_SIZE for value in values):
            raise SudokuValidationError("fixture values must be between 0 and 9")
        parsed.append(values)
    return tuple(parsed)


def _triple_fact(subject: Atom, relation: str, object_: Atom | Number) -> Fact:
    return Fact(Triple(subject, Atom(relation), object_))
