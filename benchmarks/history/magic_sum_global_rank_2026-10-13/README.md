# Whole residual sum systems: exact rank diagnostic

Recorded on **13 October 2026**. The production solver remains unchanged.

**Finding:** removing the eight-variable limit does not uncover larger uniquely
solvable residual systems in these magic-square searches. After native
propagation finishes, sizes 4×4 and above have no individual variable forced by
the complete collection of linear sum equations. The 3×3 case is an exception:
elimination forces its center to 5 and finds additional partial deductions.

This is stronger than the [small-system experiment](../magic_sum_systems_2026-10-13/README.md):
if any closed subset of sum equations uniquely determined some unresolved
variables, the entire system would also force those variables. Therefore no such
subset, of any size, remains at the observed fixpoints for squares 4×4 and above.
This statement concerns exact linear implications of the sums. It does not rule
out pruning obtained by combining equations with finite-domain restrictions or
all-different.

## What was measured

The diagnostic records every search node **before** native propagation and every
successful propagation fixpoint **afterward**, including branches that are later
abandoned. It does not apply deductions, change search choices, or add constraints.
An uninstrumented control confirms identical nodes, failures, revisions,
termination, and returned squares for each size.

The collection contains **8,393 before states** and **3,058 after states** across
14 sizes. Eleven after states are completed solutions; the other **3,047** still
have unresolved variables. All 22 returned boards from the control and captured
searches are independently validated.

All unconditional integer sum equalities participate simultaneously. Fixed
values are substituted into their targets. Exact sparse integer Gauss-Jordan
elimination computes rank and detects rows fixing individual variables, even
when other variables remain free. Every useful row has a checked integer linear
combination certificate. No floating-point rank estimate is used.

Coefficient elimination is performed offline once per actual unresolved-variable
mask, across 1,525 distinct masks. Right-hand sides and domain membership are
recomputed for every captured state, including sibling branches. This is an
immutable structural reuse mechanism, not a witness/support cache in the solver.

## After propagation: how close are we to a unique solution?

For each completed size, the table shows one observed nonterminal state having
the smallest remaining linear freedom. Freedom is `unresolved variables − rank`.
Different states can attain the same minimum with different variable counts.

| Square | Unresolved variables | Exact rank | Remaining freedom | Extra linearly forced variables in any after state |
|---|---:|---:|---:|---:|
| 3×3 | 8 | 7 | 1 | Yes |
| 4×4 | 11 | 8 | 3 | None |
| 6×6 | 13 | 8 | 5 | None |
| 8×8 | 11 | 8 | 3 | None |
| 9×9 | 12 | 7 | 5 | None |
| 10×10 | 4 | 3 | 1 | None |
| 11×11 | 15 | 8 | 7 | None |
| 12×12 | 11 | 6 | 5 | None |
| 13×13 | 14 | 8 | 6 | None |
| 14×14 | 14 | 7 | 7 | None |
| 16×16 | 16 | 9 | 7 | None |

No nonterminal after state has full column rank. Even the almost determined
10×10 state leaves one free parameter, and no individual remaining variable is
independent of that parameter.

15×15 uses only the first 80 nodes; 18×18 and 20×20 use the first 30. These are
**bounded searches, not completed solves**. Their minimum observed after-state
freedoms are 115, 258, and 330 respectively, with no forced variables.

## Before propagation: opportunities already handled by native constraints

The earlier observation point does find partial deductions, but most are already
direct consequences of a sum containing one unresolved variable. The table also
counts states where elimination forces a variable that no single original
residual sum directly fixes. Chained native propagation can still find these.

| Square | Before states | States with a forced value beyond direct singleton sums | Full-column-rank states |
|---|---:|---:|---:|
| 3×3 | 12 | 12 | 9 |
| 4×4 | 99 | 65 | 0 |
| 6×6 | 90 | 5 | 0 |
| 8×8 | 161 | 2 | 0 |
| 9×9 | 2,962 | 0 | 0 |
| 10×10 | 246 | 1 | 1 |
| 11×11 | 258 | 0 | 0 |
| 12×12 | 182 | 0 | 0 |
| 13×13 | 1,488 | 8 | 0 |
| 14×14 | 219 | 0 | 0 |
| 16×16 | 2,536 | 0 | 0 |

In 10×10, the full-rank system occurs at node 246 with **three unknowns and rank
three**. Native propagation solves it on that same node. The maximum full-rank
residual size anywhere in the traces is seven variables, in 3×3. There are no
full-rank residual systems larger than the earlier eight-variable limit.

For 3×3, the initial nine-variable system has rank seven and two degrees of
freedom, yet already forces the center to 5. After native propagation, three
observed nonterminal states contain five forced-value occurrences in total.
One state is inconsistent with its current domains. These are additional linear
deductions the native fixpoint has not made. No deductions were applied in this
study, so there is no measured solve-time improvement to report.

Full column rank is a coefficient property, not a guarantee of an integer/domain
feasible solution. The raw data separately records rational inconsistency,
nonintegral forced values, and values absent from current domains.

## Interpretation and limits

The eight-variable discovery cap was not hiding a useful larger uniquely
solvable system at these search points. Existing finite-domain propagation has
usually already resolved the determined parts before reaching its fixpoint.
The remaining linear solution space retains freedom, while domain restrictions
and all-different supply information outside the linear system.

These observations support keeping global rank solving out of production for
the measured blank-square settings. They do not establish performance for other
search orders, clued puzzles, or different models. They also do not test filtering
domains with short derived relations between still-free variables.

Offline analysis of all captured states takes about 1.09 seconds total in this
run, including structural grouping reuse and proof checks. **This is not the
cost of an online propagator and is not a speedup measurement.** Search, snapshot
capture, serialization, and imports are outside that timer. A production version
would need its own cost and benefit measurements.

## Validation and evidence

Ten diagnostic tests pass, including 400 random matrices compared with a separate
exact rational RREF implementation. Tests verify every sparse integer row proof,
partial forcing in an underdetermined system, a uniquely solvable nine-variable
system, rational versus integer inconsistency, current targets across sibling
branches, initial magic-square ranks, and unconstrained variables remaining free.
The earlier 15 small-system tests also pass.

The runtime is unchanged at `edfe3c9`. The full core suite was not rerun for this
diagnostic. Both new experimental Python files pass Ruff.

- [Per-size summaries](summary.json)
- [Frozen sources, settings, and scope](frozen.json)
- [Validation counts and source snapshot hashes](validation.json)
- [Raw-evidence checksums](manifest.json)
- [Archived analyzer](sum_global_rank.py.txt) and [tests](test_sum_global_rank.py.txt)
- [Live analyzer](../../../experiments/neural_attention/sum_global_rank.py)
  and [tests](../../../experiments/neural_attention/test_sum_global_rank.py)
- Example complete state records: [3×3](magic3.json.gz), [10×10](magic10.json.gz),
  and [16×16](magic16.json.gz)

Each `magicN.json.gz` is a lossless compressed JSON record containing original
equations, variable order, captured domain masks, every rank result, forced-value
proofs, and the returned board. Reconstruct each alphabet from the frozen model
and saved settings using `prepare`; bit positions refer to that alphabet order.
The manifest records compressed and uncompressed SHA-256 hashes.

Run from the repository root with a fresh output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.sum_global_rank \
  --sizes 3 4 6 8 9 10 11 12 13 14 15 16 18 20 \
  --presets benchmarks/history/magic_sum_global_rank_2026-10-13/presets.json \
  --output generated/neural_attention/sum_global_rank_NEW

.venv/bin/pytest experiments/neural_attention/test_sum_global_rank.py \
  experiments/neural_attention/test_sum_systems.py
```
