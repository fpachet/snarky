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

## Persistent constraints and rules

`FiniteCSP.constraints` holds deterministic constraints that remain active for
the whole search. The initial practical constraint set is:

```python
AllDifferentConstraint(Atom("name"), variables)
SumConstraint(Atom("name"), variables, target)
LinearSumConstraint(Atom("name"), weighted_terms, operator, target)
BinaryComparisonConstraint(Atom("name"), left, right, operator)
ElementConstraint(Atom("name"), index, array, value)
CountConstraint(Atom("name"), variables, value, operator, target)
GlobalCardinalityConstraint(Atom("name"), variables, bounds)
TableConstraint(Atom("name"), variables, allowed_tuples)
LexLessEqualConstraint(Atom("name"), left_sequence, right_sequence)
```

They can also be created from N-independent `.constraints` declarations.
`SCOPE ... FROM` selects variables from facts, while
`FOR EACH SEQ[...]` groups those facts into multiple constraint instances.
The complete syntax is documented in
[the textual syntax reference](../docs/syntax.md) and
[persistent finite-domain constraints](../docs/persistent_constraints.md).

At every search node, Snarky computes:

```text
persistent-constraint closure
→ forward-rule closure
→ repeat until the visible fact state is stable
→ expose CHOICE points
```

Constraint reductions are materialized by retracting unsupported `candidate`
facts. Ordinary rules and `CHOICE ... FROM` therefore inspect the filtered
domains without mentioning constraints in their premises. A choice adds a
branch-local `decision`; the generic rule restricts that variable's candidate
facts, after which all persistent constraints run again. The complete session
checkpoint restores constraint reductions, rule conclusions, and the decision
on backtracking.

This is deliberately the narrowing-only model. Initial candidate facts define
fixed base domains. Rules may derive ordinary facts and may impose additional
restrictions, but adding candidate values during inference is not part of this
semantics; that operation would require domain widening and recomputation.

## Historical lineage

This cooperation between finite-domain constraints, rules, choices, and
backtracking converges toward Yves Caseau's LAURE and later CLAIRE work; Snarky
does not claim the general combination as novel. LAURE is the closest
precedent for rules and constraints cooperating on shared objects during
hypothesis-driven search. CLAIRE continued the lineage through a tight
integration of sets, compiled rules, and search.

See the [LORE, LAURE, CLAIRE, and Snarky comparison](../docs/caseau_rules_constraints.md)
for primary references and a point-by-point operational comparison.

## Constraint-vocabulary examples

Five executable models exercise the practical persistent constraints in
recognizable combinations. Every model validates its projected solution
independently of the solver.

### SEND + MORE = MONEY

```sh
uv run python -m csp_solver.send_more_money
```

[`send_more_money.py`](send_more_money.py) combines one global
`ALL_DIFFERENT` with the weighted equality

```text
1000*S + 91*E - 90*N + D - 9000*M - 900*O + 10*R - Y = 0
```

declared by [`send_more_money.constraints`](send_more_money.constraints).
This is the smallest complete `LINEAR_SUM` example; exact propagation solves
the default model without a choice.

### Golomb ruler

```sh
uv run python -m csp_solver.golomb_ruler 5 11
```

[`golomb_ruler.py`](golomb_ruler.py) orders the marks with persistent
`LESS_THAN`, defines every distance by a three-term `LINEAR_SUM`, and applies
one `ALL_DIFFERENT` to all distances. The second argument is a feasibility
bound on the final mark; optimization can be performed by decreasing that
bound across runs.

### Car sequencing

```sh
uv run python -m csp_solver.car_sequencing
```

[`car_sequencing.py`](car_sequencing.py) implements the standard ten-car,
six-class instance. `GCC` enforces exact class demands, `ELEMENT` channels
each selected class through each option table, and overlapping `COUNT`
constraints impose every option's sliding-window capacity.

### Balanced curriculum

```sh
uv run python -m csp_solver.balanced_curriculum
```

[`balanced_curriculum.py`](balanced_curriculum.py) uses `LESS_THAN` for
prerequisites, `COUNT` for the number of courses per period, `ELEMENT` to
channel period assignments into Boolean membership variables, and weighted
`LINEAR_SUM` bounds for credit load. Forward rules then derive
`scheduled_in` and satisfied-prerequisite report facts from the filtered
assignments.

### Balanced graph coloring

```sh
uv run python -m csp_solver.balanced_graph_coloring
```

[`balanced_graph_coloring.py`](balanced_graph_coloring.py) applies
`NOT_EQUAL` to each edge and `GCC` to color-class sizes. Its forward rules
derive explicit vertex-color and satisfied-edge facts. This is the smallest
example in which persistent constraints establish the domains while
application rules describe the resulting solution.

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

## Magic square

A normal order-\(N\) magic square is another classic CSP:

- the \(N^2\) cells have domain `1..N²`;
- all cells have different values;
- every row, column, and the two diagonals sum to
  \(N(N^2 + 1)/2\).

[`magic_square.py`](magic_square.py) represents each cell as the same
`csp_variable`/`candidate` facts used by N-queens and Sudoku. The
N-independent [`magic_square.constraints`](magic_square.constraints) declares
one persistent global constraint over all cells:

```text
CONSTRAINT magic_cells_all_different
KIND ALL_DIFFERENT
SCOPE $cell
FROM
    ($cell kind magic_cell)
END_SCOPE
END
```

and one global sum template for every row, column, and diagonal:

```text
CONSTRAINT magic_line_sum
KIND SUM
FOR EACH SEQ[$line]
    ($line kind magic_line)
    ($line target $target)
END_FOR_EACH
SCOPE $cell ORDER BY $position
FROM
    ($line cell SEQ[$position $cell])
END_SCOPE
TARGET $target
END
```

The same persistent layer also provides weighted arithmetic, comparisons,
indexing, and occurrence counting. For example:

```text
CONSTRAINT resource_capacity
KIND LINEAR_SUM
SCOPE SEQ[$coefficient $variable] ORDER BY $position
FROM
    ($resource term SEQ[$position $coefficient $variable])
END_SCOPE
OPERATOR LESS_EQUAL
TARGET 40
END
```

`LINEAR_SUM` generalizes `SUM` with signed, non-zero integer coefficients and
the operators `EQUAL`, `LESS_EQUAL`, and `GREATER_EQUAL`. Binary
`LESS_EQUAL`, `LESS_THAN`, and `NOT_EQUAL` constraints use an ordered
two-variable scope. `ELEMENT` enforces a one-based array lookup, and `COUNT`
compares the occurrences of one value with a fixed integer target. The full
grammar is specified in [the syntax reference](../docs/syntax.md), with
propagation contracts in
[persistent constraints](../docs/persistent_constraints.md).

There are no magic-square propagation rules. The reusable forward rules
classify singleton domains, detect solved or contradictory problems, and
produce explicit choices. Thus the model cleanly demonstrates the division of
labour: constraints filter domains; rules observe the filtered facts and
control search.

Run the default 3×3 example (the order is also an explicit CLI parameter):

```sh
uv run python -m csp_solver.magic_square
uv run python -m csp_solver.magic_square 3
uv run python -m csp_solver.magic_square 5
uv run python -m csp_solver.magic_square 6 --symmetry-breaking
uv run python -m csp_solver.magic_square 7 --propagation-guided
uv run python -m csp_solver.magic_square 7 --dom-wdeg-only
```

The representation accepts any positive `N` (and correctly exhausts the
impossible 2×2 case). The 5×5 example is solved by the same model and rule
library; only the grounded cells, scopes, domains, and target differ.

Persistent-constraint models use failure-attributed dom/wdeg point selection
and learned-impact value ordering by default. The impact policy learns only
from real branches. `--propagation-guided` instead probes choice points of at
most eight values; `--dom-wdeg-only` disables both value-ordering extensions
for controlled comparisons.

`--symmetry-breaking` grounds seven instances of this N-independent
lex-leader template:

```text
CONSTRAINT magic_lex_leader
KIND LEX_LESS_EQUAL
FOR EACH SEQ[$symmetry]
    ($symmetry kind magic_symmetry)
END_FOR_EACH
SCOPE SEQ[$left $right] ORDER BY $position
FROM
    ($symmetry pair SEQ[$position $left $right])
END_SCOPE
END
```

Each fact-defined scope compares the row-major square with one rotation or
reflection. This option reduces order 6 to 73 nodes in the recorded run, but
is not universally favorable and therefore is not the default.

## Latin squares

[`latin_square.py`](latin_square.py) uses one fact-derived
`ALL_DIFFERENT` template for every row and column:

```sh
uv run python -m csp_solver.latin_square 5
uv run python -m csp_solver.latin_square 7
```

The default reduced formulation fixes the first row and column to remove
symmetries; the constraint declaration itself remains independent of the
order.

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

Twenty-seven persistent `ALL_DIFFERENT` constraints cover rows, columns, and
boxes. Existing forward rules still express human techniques such as locked
candidates, pairs, and X-wings. When those rules cannot finish, the generic CSP
search uses dom/wdeg point selection and learned-impact value ordering.

The first recorded p7 run illustrated the hybrid's purpose: constraints alone
used 242 nodes and 190 failed branches; constraints plus the complete
forward-rule library used 2 nodes and no failed branch. The current
dependency-scheduled implementation solves the same validated fixture in 2
nodes with constraints only and at the root with the complete rule library.
Because the counters differ, the two archives document solver evolution and
must not be interpreted as a pure timing comparison. Reproduce all classical
cases with:

```sh
uv run python -m benchmarks.classical_csp --repeat 3
```

The [initial](../benchmarks/results/classical_csp_2026-07-25.json) and
[dependency-scheduled](../benchmarks/results/classical_csp_optimized_2026-07-25.json)
results are retained alongside the current
[incremental-domain](../benchmarks/results/classical_csp_incremental_2026-07-25.json)
measurements and the
[dom/wdeg search-policy run](../benchmarks/results/classical_csp_dom_wdeg_2026-07-25.json).
The current complete run is
[learned impact](../benchmarks/results/classical_csp_learned_impact_2026-07-25.json).

The historical MRV order-6 run has a three-run median of 19.179 seconds at
5,358 nodes and 4,236 failed branches. Plain dom/wdeg now takes 2.060 seconds
at 575 nodes and 445 failures. Default learned-impact ordering reduces that
to 1.352 seconds, 387 nodes, and 297 failures. Reproduce the larger case:

```sh
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 --only-magic --repeat 3

uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-dom-wdeg-only

uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 --only-magic --repeat 3 \
  --magic-symmetry-breaking

uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-propagation-guided
```

The corresponding raw archives are
[dom/wdeg](../benchmarks/results/magic_square_dom_wdeg_2026-07-25.json),
[current plain dom/wdeg](../benchmarks/results/magic_square_dom_wdeg_only_2026-07-25.json),
[learned impact](../benchmarks/results/magic_square_learned_impact_2026-07-25.json),
[dom/wdeg with bounded probes](../benchmarks/results/magic_square_dom_wdeg_lcv_2026-07-25.json),
and
[dom/wdeg with lex symmetry](../benchmarks/results/magic_square_dom_wdeg_symmetry_2026-07-25.json).

The historical MRV raw result remains
[archived separately](../benchmarks/results/magic_square_6_incremental_2026-07-25.json).

The earlier MRV deterministic search profile was:

| Measure | Order-6 result |
|---|---:|
| Explored nodes | 5,358 |
| Branch decisions | 5,357 |
| Failed branches | 4,236 |
| Maximum explored depth | 20 |
| Successful solution depth | 18 |
| Persistent-propagator invocations | 5,358 |
| Individual constraint revisions | 111,140 |
| `ALL_DIFFERENT` revisions | 13,777 |
| `SUM` revisions | 97,363 |
| Constraint candidate removals | 333,440 |

The model uses one global Régin-style `ALL_DIFFERENT`, not a decomposition
into pairwise inequalities. Default search now uses explanation-backed
dom/wdeg with learned-impact value ordering. Declarative lexicographic
symmetry breaking, plain dom/wdeg, and bounded propagation-guided ordering are
explicit options.

See [rule programs](../docs/rule_programs.md) for explicit group composition
and [the benchmark guide](../benchmarks/README.md) for current protocols. The
[solver optimization plan](../docs/solver_optimization_plan.md) records the
measured bottlenecks, implemented scheduling/kernel work, and the criteria for
future incremental optimizations.
