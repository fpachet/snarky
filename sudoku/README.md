# Sudoku case study

The Sudoku project tests progressive, explainable symbolic solving on standard
9×9 grids. Domain knowledge remains in declarative rule groups; Python knows
only group order, stopping conditions, and the general notion of progress.

## Supported human techniques

The native rulebase solves the seven reference levels p1–p7 without exhaustive
search or an external solver:

| Level | Newly required technique |
|---|---|
| p1 | Naked Single |
| p2 | Hidden Single |
| p3 | Locked Candidate, single line |
| p4 | Locked Candidate, multiple lines |
| p5 | Naked Pairs |
| p6 | Hidden Pairs |
| p7 | X-Wing |

Each final value is supported by a replayable sequence of eliminations. The
engine features exercised by the model include persistent sessions, named
rule groups, correlated negative premises, incremental aggregates, reversible
removals, provenance, and `TechniquePlan`.

Triples, Swordfish, coloring, chains, and unique rectangles remain future
rulebase work; they are not part of the current acceptance baseline.

## Representation

Cells and candidates are ordinary facts:

```text
(r1c1 row 1)
(r1c1 column 1)
(r1c1 box 1)
(r1c1 candidate 5)
```

A clue has one initial candidate; an empty cell has nine. Technique groups
remove candidates and derive values. After any effective group, orchestration
restarts at the simplest technique. Execution ends as `SOLVED`, `STUCK`,
`INCONSISTENT`, or `LIMIT_REACHED`.

## Layout

```text
sudoku/
├── domain.py                 # fixture loading and validation
├── rulebase.py               # declarative group loading
├── solver.py                 # progressive orchestration
├── search.py                 # optional generic CSP search
├── fixtures/                 # native p1-p7 inputs and oracles
├── rules/                    # rule modules and catalogue
├── docs/implementation_plan.md
└── tests/
```

The unchanged CLIPS source oracle lives under
`third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku`.
Redistribution status is recorded in the repository's
[third-party audit](../THIRD_PARTY.md). Snarky compares results and required
techniques; it does not reproduce CLIPS agenda or salience behavior.

## Run

From the repository root:

```sh
uv run python -c \
  'from sudoku import solve_level; print(solve_level(7).techniques_used)'
```

The full event sequence can be replayed independently of the engine and the
final grid is checked against the reference oracle.

Run the representative benchmark:

```sh
uv run python -m benchmarks.sudoku_rules --levels 1 6 7 --repeat 5
```

## Explicit search

Human techniques remain the preferred p1–p7 path. A second mode validates
hybrid propagation and search:

```python
from sudoku import load_puzzle, solve_puzzle_with_search

result = solve_puzzle_with_search(
    load_puzzle(2),
    techniques=("naked_singles",),
)
```

Allowed techniques saturate after each decision. If they are insufficient,
the generic finite-CSP rules choose a candidate by MRV and restore the session
after contradiction. No Python Sudoku search algorithm is involved.

Global `ALL_DIFFERENT` propagation is available to the engine, but the p1–p7
rulebase intentionally retains explicit human techniques so that its
domain-level trace remains meaningful.

See the [implementation plan](docs/implementation_plan.md), the
[finite-CSP case study](../csp_solver/README.md), and the
[benchmark guide](../benchmarks/README.md).
