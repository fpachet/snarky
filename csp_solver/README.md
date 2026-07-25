# Declarative finite CSP solver

This project exercises Snarky's generic choice and backtracking machinery
without delegating the problem to `BacktrackingConstraintSolver`.

`FiniteCSP` is the public model. `BinaryCSP` remains a compatible alias:
extensional binary relations are one supported representation, but model rule
groups may also provide intensional, n-ary, global, or domain-specific
propagation.

## Model

A finite problem is represented as ordinary Snarky facts:

```text
(problem variable x)
(x candidate red)
(constraint kind binary_constraint)
(relation allows SEQ[red blue])
```

The generic rule library:

1. produces decisions with `CHOICE ... FROM`;
2. applies a decision by removing other candidates;
3. propagates unsupported binary pairs with `NOT EXISTS` and `REMOVE`;
4. recognizes singleton domains;
5. derives `solved` or `contradiction`.

The decision itself is declarative:

```text
RULE choose_csp_value
WHEN
    ($problem kind csp_problem)
    ($problem variable $variable)
    NOT EXISTS ($variable value $assigned)
THEN
    CHOICE ($variable decision $chosen) WEIGHT $weight
    FROM
        ($variable candidate $chosen)
        ($variable choice_weight SEQ[$chosen $weight])
    END_CHOICE
END
```

`SessionChoiceSearch` selects a minimum-remaining-values choice point, creates
a checkpoint, asserts an alternative, saturates the configured groups, and
restores the checkpoint for a failed or sibling branch. The caller's session
is isolated by one root fork.

`CHOICE` is a general Snarky primitive, not a CSP-specific operation. This
project supplies a reusable vocabulary and rules for finite-domain variables.
`finite_csp_rule_library()` exposes the `choices`, `binary_constraints`,
`domains`, and `problems` groups separately. `solve_finite_csp()` accepts an
explicit group composition.

## N-queens

Run the four-queens oracle from the repository root:

```sh
uv run python -m csp_solver.four_queens
```

It finds the two expected solutions. The Python driver does not construct
domain choices; it only executes the generic rules.

Two larger formulations are available:

- `solve_n_queens(size)` materializes compatible row pairs for each column
  pair. This extensional O(n⁴) representation is the binary-CSP oracle.
- `solve_n_queens_intensional(size)` stores only candidates and uses
  [`n_queens_intensional.rules`](n_queens_intensional.rules) to remove values
  without support for row and diagonal constraints.

The intensional version still uses Snarky for support queries, fixed-point
filtering, choices, and rollback; no problem-specific Python solver is called.

Reproduce the comparison with:

```sh
uv run python benchmarks/choice_formulations.py --repeat 3
```

Machine-readable historical results are stored under
[`../benchmarks/results`](../benchmarks/results). Compare logical solutions
and search counters before interpreting wall-clock differences.

## Sudoku reuse

[`sudoku/search.py`](../sudoku/search.py) adds the generic CSP metadata to the
native 81-cell model, then reuses its rule groups directly:

```python
from sudoku import load_puzzle, solve_puzzle_with_search

result = solve_puzzle_with_search(
    load_puzzle(2),
    techniques=("naked_singles",),
)
```

When the selected human techniques cannot finish, the generic CSP rule chooses
a candidate by MRV. The final grid is checked against the same oracle as the
human-technique solver. This demonstrates that `FiniteCSP` contains no
N-queens or Sudoku knowledge.

See [rule programs](../docs/rule_programs.md) for explicit group composition
and [the benchmark guide](../benchmarks/README.md) for current protocols.
