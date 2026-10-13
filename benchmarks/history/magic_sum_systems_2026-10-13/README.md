# Small residual sum systems: experiment, 13 October 2026

**Decision: keep this opt-in. The production solver is unchanged.**

The incidence index is inexpensive, and exact elimination can avoid substantial
search on suitable equations. In the measured blank magic-square searches,
however, it makes no additional assignments or contradictions. A clued-square
diagnostic saves some nodes but takes longer. These results do not justify
enabling the experiment by default.

## What was tested

The experimental `SumSystemState` subclasses the existing native solver without
patching its implementation or adding constraints to the immutable model.

- Build an immutable variable-to-equality incidence index.
- Represent each equation's unresolved variables as a bitset.
- After ordinary propagation reaches a fixpoint, update only scopes incident
  to variables whose fixed/unresolved status changed.
- Starting with short residual sums, explore connected groups with a bounded
  breadth-first search. Prefer extensions that introduce fewer new variables.
- Consider groups with at least as many equations as unresolved variables.
- Compile exact rational elimination and check its row-operation certificate.
  Full-rank systems force values or reject nonintegral/out-of-domain solutions.
  Dependent systems can reject inconsistent right-hand sides.
- Apply assignments through normal domain updates, then resume native
  propagation. Partial deductions from underdetermined systems are not enabled.

Only unconditional integer sum equalities participate. Inequalities, guarded or
nested constraints, and noninteger alphabets are excluded. All terms of each
selected equation are accounted for; fixed terms are subtracted from its target.

The main limit is **four equations and four variables**, with 128 discovery
operations per topology change. A separate diagnostic permits eight of each,
with a budget of 2,048. Discovery seeds, extensions, and processed groups consume
the budget. No blank-square measurement exhausts either budget.

Structural plans are retained only for the actual unresolved-variable mask.
Scopes are updated on both fixation and restoration after rollback. Targets are
recomputed from current singleton values at every evaluation, including sibling
branches with the same fixed-variable pattern. There is no cached witness or
cached domain-support decision.

## Blank magic squares: main comparison

Median seconds over three repetitions per variant. Runs are shuffled and
sequential; model setup, index construction, and discovery are included. Imports
and independent solution validation are excluded. Each size uses its saved
search settings, identical across variants. Results are paired measurements from
this experiment; compare these columns rather than timings in older archives.

| Square | Existing solver | Experimental systems | Nodes, both |
|---|---:|---:|---:|
| 6×6 | 0.056059 | 0.056571 | 90 |
| 8×8 | 0.126071 | 0.131014 | 161 |
| 9×9 | 2.243388 | 2.275848 | 2,962 |
| 10×10 | 0.276558 | 0.273594 | 246 |
| 11×11 | 0.468306 | 0.477255 | 258 |
| 12×12 | 0.559019 | 0.557763 | 182 |
| 13×13 | 2.316114 | 2.385920 | 1,488 |
| 14×14 | 1.170900 | 1.205522 | 219 |
| 16×16 | 6.727786 | 6.881971 | 2,536 |

The following are search prefixes, **not completed solves**:

| Square | Nodes measured | Existing solver | Experimental systems |
|---|---:|---:|---:|
| 15×15 | First 80 | 0.574616 | 0.590932 |
| 18×18 | First 30 | 0.653246 | 0.640743 |
| 20×20 | First 30 | 0.987793 | 0.980762 |

Every paired run preserves nodes, failures, native revisions, termination, and
the returned square. There are **zero extra assignments and zero extra
contradictions**. The only candidate reaching elimination is one dependent
system per 10×10 solve. None has full rank. Small apparent timing improvements
cannot be attributed to reduced search; timing variation remains present.

The discovery timer includes scope updates, candidate enumeration, elimination,
and certificate checks, but excludes the scan for fixed-variable status and
index construction. It costs about 0.7 ms for 6×6, 12 ms for 9×9, and 25 ms for
16×16. End-to-end timing includes all experimental overhead.

## Wider discovery and clued squares

Increasing the limits to eight variables/equations on 8×8, 9×9, 10×10, 12×12,
and 16×16 still finds no full-rank system and produces no deductions. The search
work remains identical. Discovery costs about 67 ms for 9×9 and 99 ms for 16×16.
These are single-run diagnostics, not repeated timing estimates.

A separate study uses **41 clued 4×4 instances**: one corner rectangle and 40
deterministic random clue masks leaving 4, 6, 8, 10, or 12 cells unresolved. The
reference board supplies clues only; it never guides candidate discovery or
elimination. Both solvers return independently validated squares respecting
every clue. Search uses MRV, ascending values, and no symmetry restrictions.

With the wider limits, one case detects three contradictions earlier, reducing
its search from **25 to 15 nodes**. However, its measured time increases from
3.66 ms to 20.69 ms. Across all 41 instances, nodes fall from 109 to 99, while
single-pass total time increases from 35.8 ms to 138.5 ms. The timings are
diagnostic only: baseline runs precede experimental runs for each instance,
and these very short solves were not repeated. Most factored systems are
dependent; compiling overlapping groups dominates the useful savings.

## Positive control: three equations

These deliberately favorable instances use ascending domains from `0` to `20s`:

```text
x + y = 10s
x + z = 12s
y + z = 14s
```

Exact elimination forces `(x, y, z) = (4s, 6s, 8s)` at the root. Three shuffled
repetitions per variant include state construction and search, excluding model
creation and validation. This is a constructed test, not a magic-square speedup.

| Scale s | Existing nodes | Experimental nodes | Existing median | Experimental median |
|---|---:|---:|---:|---:|
| 1 | 6 | 1 | 0.195 ms | 0.261 ms |
| 10 | 42 | 1 | 2.164 ms | 0.604 ms |
| 100 | 402 | 1 | 149.595 ms | 5.481 ms |

The largest case improves by about **27×**. This demonstrates that the method
can pay off when a useful closed system exists and individual propagation leaves
enough search. It does not establish how often that happens in other models.

## Validation and limits

Fifteen experimental tests pass, including 200 random models checked against an
independent exhaustive assignment oracle, fractional solutions, domain holes,
negative coefficients, huge integer translations, dependent/inconsistent
systems, bounded discovery, deadlines, and rollback. A dedicated test reuses the
same structural plan across sibling branches with different target values.
Enumeration preserves all eight normal 3×3 magic squares at both size limits.

The 94 blank-square runs include 72 main comparisons, 10 wider diagnostic runs,
and 12 preliminary discovery-only/control runs. All 76 returned blank boards and
82 returned clued boards were independently validated. Eighteen constructed
triangle solves return the exact expected solution.

The main runtime remains commit `edfe3c9`; no file under `src/snarky` changed.
The full core suite was not rerun for this experiment. Ruff checks all four new
experimental Python files.

This prototype runs **after native propagation fixpoints**. It does not establish
whether invoking elimination during propagation would help, whether larger
systems would pay off, or whether underdetermined systems yield useful short
derived constraints. The blank-square searches share saved configurations and
are not independent samples of general CSP problems.

Derived failures use an experimental cause outside the original dom_wdeg
constraint weights. This can change heuristic feedback if deductions occur.
There are none in the blank comparisons; clued and constructed controls use MRV.
Native revision counts exclude experimental evaluations, which have separate
counters in each raw record.

## Evidence and reproduction

- [Summary and validation counts](summary.json)
- [Main raw runs](comparison4/runs.jsonl), [medians](comparison4/summary.json),
  and [frozen source hashes and schedule](comparison4/frozen.json)
- [Wider raw runs](comparison8/runs.jsonl) and [summary](comparison8/summary.json)
- [Preliminary discovery-only controls](pilot/runs.jsonl)
- [Constructed and clued diagnostics](diagnostics/diagnostics.json)
- [Archived prototype](sum_systems.py.txt), [runner](magic_sum_system_benchmark.py.txt),
  [diagnostics](sum_system_diagnostics.py.txt), and [tests](test_sum_systems.py.txt)
- [Live prototype](../../../experiments/neural_attention/sum_systems.py)
  and [tests](../../../experiments/neural_attention/test_sum_systems.py)

Snapshots inside each comparison directory preserve the exact collector and
prototype used for those runs. The preliminary pilot predates a refinement to
budget-hit reporting; its budgets were not exhausted. All files are opt-in
research evidence, not production imports.

From the repository root, use fresh output directories:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_system_benchmark \
  --presets benchmarks/history/magic_sum_systems_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 \
  --variants baseline exact --repeats 3 \
  --output generated/neural_attention/sum_systems_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_system_benchmark \
  --sizes 8 9 10 12 16 --variants baseline exact --repeats 1 \
  --max-variables 8 --max-equations 8 --budget 2048 \
  --output generated/neural_attention/sum_systems_wide_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.sum_system_diagnostics \
  --output generated/neural_attention/sum_systems_diagnostics_NEW

.venv/bin/pytest experiments/neural_attention/test_sum_systems.py
```
