# Persistent finite-domain constraints

Persistent constraints are declarations, not rules. They remain active across
the complete choice search and filter the same `candidate` facts that ordinary
rules inspect.

## Execution semantics

At each root or branch node, `SessionChoiceSearch` computes:

```text
constraint propagation
→ forward-rule saturation
→ repeat until the visible fact state is stable
→ goal/contradiction test
→ CHOICE when the problem remains unresolved
```

The initial candidate facts define fixed base domains. Constraints and rules
may narrow those domains. Adding candidate values during inference is outside
this first semantics because it requires widening and dependency-directed
recomputation.

Constraint propagation is deterministic and never branches. `CHOICE` remains
the sole source of alternatives. A session checkpoint restores decisions,
constraint reductions, and rule conclusions together.

## Fact-derived templates

A template is grounded once against the root fact set. `SCOPE` queries select
the finite-domain variables. `FOR EACH SEQ[...]` declares the context key used
to produce multiple constraint instances.

The magic-square all-different declaration is independent of the order of the
square:

```text
CONSTRAINT magic_cells_all_different
KIND ALL_DIFFERENT
SCOPE $cell
FROM
    ($cell kind magic_cell)
END_SCOPE
END
```

One template creates a sum constraint for every fact-defined line:

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

`FOR EACH` premises may contain auxiliary variables. Only the terms in its
`SEQ[...]` key determine grouping. This permits Sudoku to enumerate unit names
through an arbitrary anchor cell while creating only one constraint per row,
column, or box.

## Supported constraints

### `ALL_DIFFERENT`

```text
KIND ALL_DIFFERENT
```

The propagator establishes generalized arc consistency. It computes a complete
variable/value matching with Hopcroft–Karp and applies Régin-style alternating
graph filtering through strongly connected components and paths to free
values.

### `SUM`

```text
KIND SUM
...
TARGET $integer
```

The propagator computes exact reachable prefix and suffix sums. A candidate is
retained only when the remaining variables can reach the complementary sum.

### `GCC`

```text
CONSTRAINT staffing
KIND GCC
SCOPE $slot
FROM
    ($slot kind staffing_slot)
END_SCOPE
BOUNDS SEQ[$value $lower $upper]
FROM
    ($bound kind occurrence_bound)
    ($bound value $value)
    ($bound lower $lower)
    ($bound upper $upper)
END_BOUNDS
END
```

The global cardinality constraint bounds the number of occurrences of each
listed value. Feasibility is expressed as a lower-bounded flow circulation;
candidate support tests therefore establish GAC. The present implementation
rechecks the flow for each candidate and is the correctness baseline for a
future incremental residual-network implementation.

### `TABLE`

```text
CONSTRAINT allowed_transition
KIND TABLE
SCOPE $variable ORDER BY $position
FROM
    ($transition scope SEQ[$position $variable])
END_SCOPE
TUPLES $tuple
FROM
    ($relation allows $tuple)
END_TUPLES
END
```

An allowed table tuple is active when every component remains in the
corresponding domain. Each domain is intersected with the projections of the
active tuples.

## Scheduling and rollback

The propagator compiles a variable-to-constraint adjacency graph. A removal
schedules only incident constraints. The surrounding joint fixed-point
scheduler separately compiles the fact relations read by each rule group and
propagator. A fact mutation therefore revisits only affected components;
dynamic relation premises use a conservative wildcard.

Each inference session has an isolated domain projection. A rollback-aware
event cursor records its journal generation and the rollback origin. The
projection reverses its own delta trail to that origin and applies the sibling
events, avoiding a complete visible-fact scan even when two branches happen
to have the same event count.

This is rollback-aware but not yet the final incremental architecture.
Matching and flow objects can subsequently acquire their own reversible trails
without changing the declaration or fixed-point semantics.

The canonical finite-CSP choice and classification rules use this projection
for compiled eligibility lookup. Original rule activations still pass through
normal refraction, mutation, event, and provenance machinery. See the
[solver optimization plan](solver_optimization_plan.md).

## Correctness protocol

Each propagator should be differentially tested on small domains against a
brute-force tuple oracle:

1. every removed value has no support;
2. every retained value has a support when GAC is claimed;
3. a second propagation is idempotent;
4. fair scheduling orders reach the same closure;
5. propagate, choose, and rollback restore the exact preceding state.

## References

- Jean-Charles Régin, [*A Filtering Algorithm for Constraints of Difference
  in CSPs*](https://m.aaai.org/Library/AAAI/1994/aaai94-055.php), AAAI 1994.
- Jean-Charles Régin, [*Generalized Arc Consistency for Global Cardinality
  Constraint*](https://cs.bme.hu/~szeredi/nlp/Generalized_Arc_Consistency_for_Global_Cardinality.pdf),
  AAAI 1996.
