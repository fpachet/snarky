# Compiled numeric masks — 17 September 2026

The [aggregate comparison](performance_solver_averages_2026-09-17.md) calculates
the Prune averages from this record and adds a fresh CLAIRE run on the updated
runtime, with separate timing boundaries and explicit timeout exclusions.

This follows objective propagation at `32842b5`. The native and mixed runtimes
now use compiled candidate-index arithmetic for integer inequalities and
unary/binary equalities. This reduces repeated representation work; it does not
weaken consistency, change branching or introduce new bounds.

## Representation and filtering

Each state lazily shares a numeric column for a `(variable, coefficient)` pair:
weighted integer contributions and a contribution-to-candidate-index map. Masks
refer to the original candidate order, never integer magnitudes. Huge signed
values and coefficients therefore do not become huge numeric-index bitsets.
Columns are shared between constraints using the same pair, including changing
objective-cut targets. The scope/operator plan is reused when only the target
changes; different coefficients or operators replace the plan.

`FiniteDomains.mask()` and `alphabet()` provide current masks and immutable
candidate coordinates. `retain_mask()` intersects supports directly and records
the same removals, causes, trail and changed-variable events as `retain()`.
Only removed bits are decoded into symbolic terms for explanations. Unchanged
masks avoid set/tuple/dictionary reconstruction and trail entries.

For each inequality, extrema are cached by actual masks. A plan updates its
aggregate extremum when a scoped mask changes, including after rollback. It still
checks all scoped masks per revision; this is not an O(number-of-changes) queue.
Monotone contribution order permits extrema from the first/last active bit and
threshold filtering with binary search plus a prefix/suffix mask. Holes remain
represented exactly. Unordered alphabets use a mask scan, with extrema cached.
Each candidate has support precisely when the other variables' extremal
contributions satisfy the inequality, preserving the existing exact support rule.

Unary equality uses a contribution lookup. Binary equality traverses the smaller
current domain and finds complementary contributions through the compiled index,
producing both support masks before any domain is changed. An inconsistent
revision commits no reductions, matching the reference kernel's behavior.

## Scope, fallback and memory

The fast path covers `LinearSumConstraint` inequalities and unary/binary
`LinearSumConstraint`/`SumConstraint` equalities. General equalities retain their
existing normalized bitset/sparse exact algorithms. Other constraints retain their
current kernels. This is a first compiled numeric path, not a new domain system.

Compilation permits at most 4,096 original candidates per column and 262,144
compiled contribution entries per state. Larger inputs use the reference kernels.
These caps bound entry counts, not bytes, the explicit domain store or the cost
of fallback propagation. Integer bit length still affects storage and arithmetic.
Columns and lookup maps add memory; allocation measurements below report that
trade-off. Cache entries retain only the latest masks/extrema, not all historical
search states. No cache trail is needed because every reuse checks actual masks.

Compilation is lazy, after guard activation. A noninteger original alphabet
selects fallback without raising a new early error, even if offending candidates
were already removed. Existing validation behavior is preserved. The default is
`numeric_masks=True`; `NativeState`, `MixedState`, and DFS `solve` accept
`numeric_masks=False` for the reference path. Legacy fact-backed CSP keeps the
reference kernels. Numeric mask filtering has its own private diagnostic hook;
the benchmark worker instruments both paths and records the selected mode.

## Measurement protocol

Paired runs use `32842b5` and the current runtime with the same worker, FlatZinc
inputs, native NValue, incumbent cuts, dom/wdeg and declared value order. Each has
one discarded warmup and three alternating repetitions, with a five-second
external process cap. A same-source on/off ablation checks the combined numeric
path; it does not isolate the contribution cache, mask operations and incremental
extrema as three independent interventions.

Times include startup, preparation, search and output. Compilation and independent
Gecode validation are outside the timed process. Correctness/package jobs finish
before latency collection; CPU/allocation instrumentation runs separately.
Background load and thermal state are uncontrolled. Three samples provide
descriptive medians, not confidence intervals.

## Paired performance

The [raw record](../benchmarks/results/csp_numeric_2026-09-17/results.json) and
[summary](../benchmarks/results/csp_numeric_2026-09-17/summary.json) preserve all
samples and source hashes. Every mutually completed case retains identical
solutions, objectives, nodes, failures and revisions.

| Workload | Before seconds | After seconds | Before / after |
| --- | ---: | ---: | ---: |
| magic_square_4 | 0.1592 | 0.1549 | 1.03× |
| magic_sequence_40 | 0.3595 | 0.3562 | 1.01× |
| bin_packing_40 | 0.2758 | 0.2769 | 1.00× |
| queens_50 | 0.5564 | 0.4638 | 1.20× |
| queens_104 | >5 | >5 | — |
| queens_150 | >5 | >5 | — |
| golomb_opt_6 | 0.1302 | 0.1384 | 0.94× |
| golomb_opt_7 | 0.2267 | 0.2197 | 1.03× |
| jobshop_ft06_opt | 0.9545 | 0.4279 | 2.23× |
| knapsack_20_opt | >5 | >5 | — |
| bin_packing_20_opt | >5 | >5 | — |
| all_different_incremental_16 | 0.4476 | 0.4523 | 0.99× |

FT06 proves optimum 55 with the same 615 nodes, 386 failures and 68,529 revisions.
Its native search median falls from 0.8264 to 0.2974 seconds (2.78×); the 2.23×
process gain includes startup and preparation. Queens 50 keeps 52 nodes and 6,867
revisions; native search falls from 0.4228 to 0.3282 seconds (1.29×). These are
implementation gains on unchanged search work.

Wider-equality workloads remain essentially unchanged. Golomb 6 has an 8 ms
process regression with nearly unchanged native time; incremental Latin 16 and
packing 40 retain small regressions too. Three repetitions cannot distinguish
such small differences from noise. All timeout observations remain in the record.

## Same-source on/off check

The [ablation](../benchmarks/results/csp_numeric_ablation_2026-09-17/results.json)
uses the current source for both paths with only `numeric_masks` changed. All
completed cases preserve counters and outputs.

| Workload | Masks off seconds | Masks on seconds | Off / on |
| --- | ---: | ---: | ---: |
| magic_sequence_40 | 0.3618 | 0.3656 | 0.99× |
| queens_50 | 0.5671 | 0.4683 | 1.21× |
| jobshop_ft06_opt | 0.9654 | 0.4343 | 2.22× |

## Fresh Prune comparison

The [full record](../benchmarks/results/prune_numeric_2026-09-17/results.json) and
[summary](../benchmarks/results/prune_numeric_2026-09-17/summary.csv) cover 54
available inputs and 59 mode workloads. Prune is the same pinned compiled Rust
binary; Snarky remains Python. Both receive identical FlatZinc inputs. Returned
assignments and claimed optima are checked independently against original
FlatZinc primitives and original MiniZinc models with Gecode.

| Engine | Completed in each of three repetitions | Optimization proofs |
| --- | ---: | ---: |
| Snarky | 52/59 | 3/5 |
| Prune | 59/59 | 5/5 |

| Workload | Snarky process seconds | Prune process seconds |
| --- | ---: | ---: |
| queens_50 | 0.4708 | 0.0118 |
| golomb_opt_6 | 0.1301 | 0.0040 |
| golomb_opt_7 | 0.2279 | 0.0046 |
| jobshop_ft06_opt | 0.4336 | 0.0099 |
| knapsack_20_opt | >5 | 0.0185 |
| bin_packing_20_opt | >5 | 4.8060 |

The fresh FT06 process gap is about 44× and queens 50 about 40×. These compare
complete implementations, not isolated language or algorithm costs. The full
comparison uses a different worker/import path from the paired Python runs.
Prune's bin-packing samples all finish in this run; the previous run's single
near-cap timeout remains in its historical record.

Snarky's seven timeouts are initial queens 104, extended queens 104 and 150,
magic square 5, pairwise pigeonhole 10, knapsack optimization and packing
optimization. No timeout becomes a proof. The upstream CSPLib/reserved coverage
gaps remain; the two billion-domain chains still compile away and do not test
compact runtime domains. The [audit](../benchmarks/results/prune_numeric_2026-09-17/audit.json)
confirms all 54 input hashes, the unchanged Prune binary, and unchanged counters,
objectives and normalized outputs for all 52 completed Snarky workloads against
the preceding full run.

## Compatibility and memory

The [controls](../benchmarks/results/csp_numeric_controls_2026-09-17/results.json)
preserve observations for rules, joins, legacy CSP, mixed CSP, Markov and the
exact Boulez result. These medians exclude startup and are separate from the
process times above.

| Control | Reference seconds | Candidate seconds | Reference / candidate |
| --- | ---: | ---: | ---: |
| rules/small/triangle_closure:indexed | 0.0010 | 0.0010 | 0.99× |
| joins/25x8/streamed | 0.1154 | 0.1163 | 0.99× |
| magic4 | 0.4129 | 0.4117 | 1.00× |
| mixed_magic3 | 0.0024 | 0.0024 | 0.98× |
| markov33x8 | 0.1416 | 0.1409 | 1.00× |
| boulez | 1.6469 | 1.6291 | 1.01× |

Allocation traces use a **30-node limit**, one sample per engine, with identical
work in each pair. They are not full-search memory claims. Tracemalloc peaks cover
construction/preparation/search; RSS is the whole-process high-water mark including
imports. All memory numbers below use MiB (2²⁰ bytes).

| Workload | Traced peak before → after | Increase | Process RSS before → after |
| --- | ---: | ---: | ---: |
| extended--queens_50 | 4.815 → 5.256 | 9.2% | 35.25 → 35.34 |
| optimization--jobshop_ft06_opt | 1.412 → 1.917 | 35.7% | 27.62 → 27.81 |
| optimization--knapsack_20_opt | 0.188 → 0.222 | 18.0% | 24.89 → 25.78 |

The extra persistent contribution/index data buys lower repeated conversion and
allocation work; peak live memory increases. The entry limits protect compilation
size, not a universal memory ceiling. Unordered numeric alphabets also retain the
scan fallback inside compiled columns.

## Remaining optimization opportunities

The [separate profiles](../benchmarks/results/csp_numeric_profiles_2026-09-17/results.json)
use two seconds and at most 200 nodes with instrumentation. They must not be read
as production latency or compared directly with older profiles at different work.

- Queens 104/150 spend about 1.01/1.04 s inside all-different revisions and
  0.41/0.37 s inside numeric mask revisions within roughly two instrumented seconds.
  Matching/filtering and domain conversion remain material. Binary channel scans
  remain proportional to the smaller active domain; exact affine views or
  compatible index masks are potential separate improvements.
- FT06's 200-node prefix makes 26,488 mask revisions, spending about 0.36 s inside
  those revision hooks. Queue/domain lookup overhead still matters. Cached extrema
  currently require a scope-mask scan; an event/delta interface could reduce it.
- Knapsack's 200-node prefix spends about 0.061 s in general equality revisions
  and 0.020 s in compiled inequality revisions. It finds value 109 without proof;
  307 is the recorded root bound, not a tightened frontier bound. The full
  five-second run still times out. Wider equality views and stronger admissible
  bounds/value ordering address different costs and should be measured separately.

These are profiler-supported next investigations, not predicted speedups. GCC
and compact integer domains remain separate work. This change does not alter
NValue or all-different filtering strength.

## Validation

The new oracle tests compare 650 deterministic signed/holey problems over four
rollback/restoration visits each, checking exact supported values against complete
enumeration and the existing set kernels. They compare failure names, revisions,
removal explanations and restored domains. Other checks cover direct-mask versus
set retention, minimization/maximization and changing incumbent targets, state
reuse, budget fallback, wider equality fallback, guarded validation timing and
binary SUM. Existing mixed-rule, factor/product, optimization, rollback and
application tests remain in the full regression gate.

The full workspace gate reports **1,106 passed, 3 skipped**, including two
pre-existing Alice tests outside this change. Mypy, Ruff, textual validation,
core/companion builds and isolated installation checks pass. A Python 3.12 FT06
smoke independently preserves optimum 55 and all search counters. See the
[validation record](../benchmarks/results/csp_numeric_2026-09-17/validation.md)
for logs and commands. Candidate source hashes were checked after collection.

## Reproduction

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source /path/to/32842b5 --reference-ref 32842b5 \
  --reference-nvalue native --only optimization/ --only extended/queens_ \
  --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/numeric_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source . --reference-ref same-source-numeric-masks-off \
  --reference-nvalue native --reference-numeric-masks off --candidate-numeric-masks on \
  --only optimization/jobshop_ft06_opt --only extended/queens_50 \
  --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/numeric_ablation_NEW_LABEL
```
