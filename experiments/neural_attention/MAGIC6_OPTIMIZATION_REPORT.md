# Faster first solutions for blank 6×6 magic squares

12 October 2026. This follow-up separates value ordering, propagation cost, and
symmetry constraints. It uses the same blank model as the previous experiment:
36 cells with values 1–36, one global all-different, and fourteen sums of 111.
Every returned solution is checked against that original model. No transformer,
learned constraints, reference completion, or solution hint is used.

## Changes

**Value order:** MRV still chooses the cell with the smallest remaining domain,
with the existing row-major tie order. The middle-first variant changes each
original declared value order to `18, 19, 17, 20, …, 1, 36`. It retains every
candidate and hence the complete solution set. This static order is an
experimental magic-square setting; generic solver value-order defaults are
unchanged. The random control independently shuffles each cell's complete
alphabet using a declared seed.

**Compiled sums:** `src/snarky/finite/numeric.py` now handles bounded-span n-ary
integer equalities directly in domain-mask coordinates, avoiding the repeated
term/set/dictionary conversion of the reference sum kernel. Reachable prefixes
and reflected suffixes compute exact independent-variable supports. Current
minima normalize signed contributions and arbitrarily large translations;
near-upper targets are reflected. Support caches check actual masks and targets
after rollback. This changes representation and cost, not filtering strength.

The compiled equality path is bounded by a 4,096 original contribution span,
1,048,576 total prefix bits, and existing column/entry budgets. Larger spans and
noninteger original alphabets use the original exact fallback, including its
sparse and GCD-normalized paths. The existing `numeric_masks=False` diagnostic
switch disables the compiled path. This optimization is enabled with the
existing default numeric masks in both native and mixed states.

**Symmetry:** an explicit blank-square option adds five inequalities: top-left
less than each other corner, top-right less than bottom-left, and top-left at
most 18. Rotation/reflection puts the smallest corner at top-left and the smaller
adjacent corner at top-right; complementing all values with `37 - value` permits
a smallest corner at most 18. These operations preserve the original magic-square
constraints, so every symmetry orbit retains a representative. These are
symmetry restrictions, rather than implied constraints preserving every solution.
The helper rejects clue domains or changed constraint models and is not enabled
automatically. It must not be applied to arbitrary clued puzzles.

## Measurement protocol

- A three-second pilot on the original runtime compares middle-first, alternating
  ends, and random seeds 0–9, with and without symmetry: 24 runs. All ten random
  runs without symmetry finish in 0.120–1.531 seconds. Middle-first without
  symmetry finishes in 0.138 seconds; with symmetry, 0.097 seconds. Symmetry also
  causes three random runs and the alternating-ends run to time out. These pilot
  observations select middle-first for repetition; they are not held-out tests.
- A separate three-second profile of original ascending MRV attributes about
  1.58 of 3.00 instrumented seconds to the reference sum revisions. Profiling
  overhead means those durations are diagnostic, not ordinary solve timings.
- Three shuffled repetitions of ascending and middle-first MRV without symmetry
  establish the original-runtime baseline with a 45-second limit.
- After exactness tests, three shuffled repetitions per combination compare
  ascending/middle-first MRV and symmetry on/off with the compiled runtime.
  The 45-second budget is fixed before these measurements.
- Every timing includes solver setup, propagation, and search. Total timings
  additionally include original model construction, value reordering, and any
  symmetry construction. Validation and interpreter imports are excluded.
- `PYTHONHASHSEED=0`, Python 3.13, one sequential timing process, no concurrent
  CPU tests or benchmarks. Each run set freezes source hashes and configuration.
  No preprocessing based on a previously found solution is performed.

## Results

All rows below use MRV. Times are medians of three runs, including model
construction and any value/symmetry preparation.

| Runtime and configuration | Finished | Total seconds | Nodes per finished run |
|---|---:|---:|---:|
| Original sums, ascending values | 3/3 | 34.145 | 44,193 |
| Original sums, middle-first values | 3/3 | 0.139 | 153 |
| Compiled sums, ascending values | 3/3 | 18.259 | 44,193 |
| Compiled sums, middle-first values | 3/3 | **0.0845** | **153** |
| Compiled sums, middle-first + symmetry | 3/3 | **0.0628** | **90** |
| Compiled sums, ascending + symmetry | 0/3 | >45 | — |

The compiled sums reduce original-order runtime by **1.87×**, preserving exactly
44,193 nodes, 815,193 revisions, and the returned square on every completed run.
With middle-first order, compiled versus original sums improve total time by
1.64×, preserving 153 nodes, 2,801 revisions, and the returned square.
The main gain is the changed search tree: middle-first alone makes the original
runtime about 246× faster. Combined value ordering and propagation make the
blank solve about **404× faster** than the repeated original baseline, without
any additional constraints. Adding the explicit symmetry option brings this to
about **544×**, but symmetry with ascending values times out in all three runs.

Solve-only medians, excluding model/value/symmetry construction, are 34.144,
0.137, 18.258, 0.0831, and 0.0601 seconds respectively for the completed rows.
The middle-first combined runtime range is 0.0825–0.0850 seconds without symmetry
and 0.0600–0.0603 seconds with it. Millisecond timing differences remain sensitive
to system load; search counters and original-model validation support the large
first-solution improvement. Three repetitions of one blank problem do not form
three independent problem instances or justify population confidence intervals.

The practical setting for this blank model is **MRV + middle-first values**,
with the compiled sums enabled by default. Symmetry can be added explicitly for
this first-solution task. This gives a much stronger cheap baseline for future
neural experiments: collection, training, verification, and added propagation
must now compete with a solve costing roughly 60–85 ms on this machine.

## Correctness and scope

The focused solver and experiment suite passes **306 tests with one skip**.
New checks compare 500 random
signed, holey, shuffled n-ary equalities against exhaustive support enumeration
and the reference kernel, including sibling rollback and huge translations.
Additional checks cover representation-budget fallback, empty domains, changing
targets, and complete enumeration with matching outputs and search counters.
Value reordering preserves all eight 3×3 solutions. Symmetry retains one 3×3
representative, and sampled board orbits at sizes 3–6 check representative coverage.
Lint, type checking of all 103 runtime source files, and Markdown links pass.
The full repository application/release suite was not run.

This is optimization for the first solution of the blank square. Middle-first
and symmetry gains are sensitive to the search tree and do not establish gains
for arbitrary clues or other CSPs. The compiled sum optimization is general and
exact, but performance on other workloads still needs separate measurement.
Earlier reports describe their recorded runtime hashes; their timings should
not be relabeled as measurements of this changed runtime.

## Evidence and reproduction

Generated evidence is under `generated/neural_attention/`:
`magic6_order_pilot/`, `magic6_order_baseline/`, and `magic6_order_compiled/`.
Each contains frozen configuration/source hashes and validated raw runs.
The pilot also contains `baseline.prof`; the combined machine-readable summary
is `generated/neural_attention/magic6_optimization_summary.json`. The 42 timed
searches and separate profile are retained. Output directories must be fresh.
The compiled run set also retains its exact runner as `runner_snapshot.py`;
after measurement the current helper additionally rejects reordered model
variables so its corner interpretation cannot be applied to an altered layout.
That guard does not change the measured original row-major cases.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.optimize_magic6 \
  --orders middle --symmetry none --repeats 3 --limit 45 \
  --output generated/neural_attention/magic6_middle_NEW
```

Use `--symmetry only` for the explicit symmetry-restricted formulation, and
`--orders ascending middle --symmetry both` for the full comparison.
`--reference --symmetry none` selects the original reference sum kernel on this
model, while retaining compiled all-different. The runner's full original model
is reconstructed for every run; only value order and the explicit symmetry
option differ.

## Follow-up: numeric ordering and larger compiled spans, 12 October 2026

The measurements above describe the earlier runtime. A subsequent profile of the
complete 14×14 solve attributed about 80% of search time to numeric revisions and
18% to all-different. Two further optimizations now apply to native and mixed
numeric propagation:

- Unordered contribution columns maintain a separate numeric-rank mask. Extrema
  update from changed candidate bits, or rebuild from the surviving domain when
  that is smaller. Inequality thresholds use numeric ranks too. Declared domain
  order, value choices, removal explanations, and checkpoint behavior are intact.
- The original contribution-span limit increases from 4,096 to 16,384, keeping
  the independent 1,048,576-bit prefix budget, 4,096-candidate column limit, and
  262,144 logical contribution-entry limit. The 17×17–20×20 line sums therefore
  use compiled masks rather than the reference set/dictionary kernel. Very wide
  or noninteger alphabets and exhausted budgets still select exact fallback.

Identical contribution layouts share their read-only values, lookup indexes, and
numeric-rank tables. Variable-specific masks and extrema caches remain separate.
This avoids duplicating large tables for every magic-square cell; entry budgets
still count logical columns conservatively, irrespective of sharing.

The following are medians of three sequential runs per version, with randomized
run order. They include model and state setup, excluding imports and validation.
All 54 searches preserve nodes, failures, revisions, termination, and any returned
square against the saved pre-change numeric implementation. The 36 returned
squares are validated against their original models. The larger unfinished cases
use fixed node budgets so profiler or deadline effects cannot change the work.

| Workload | Before (s) | After (s) | Speedup |
|---|---:|---:|---:|
| 6×6, complete | 0.0618 | 0.0591 | 1.05× |
| 7×7, complete | 1.1204 | 1.0832 | 1.03× |
| 8×8, complete | 0.1823 | 0.1713 | 1.06× |
| 9×9, complete | 2.4145 | 2.2975 | 1.05× |
| 10×10, complete | 0.5055 | 0.4718 | 1.07× |
| 11×11, first 1,500 nodes | 2.8888 | 2.6910 | 1.07× |
| 14×14, complete | 3.1924 | 2.7920 | 1.14× |
| 18×18, first 30 nodes | 7.1681 | 4.3411 | 1.65× |
| 20×20, first 30 nodes | 14.1548 | 8.6928 | 1.63× |

The 14×14 solve still uses 219 nodes, 50 failures, and 5,002 revisions. The 18×18
prefix has 30 nodes and 1,238 revisions; the 20×20 prefix has 30 nodes and 1,358
revisions. Their results do not establish complete solve times. Small timing
differences remain sensitive to system load, and repetitions are of deterministic
blank instances rather than independent test puzzles.

Separate root-only allocation measurements, covering native state construction
and root propagation but excluding model construction and imports, show traced
peaks of 6.86→4.40 MB for 14×14 and 20.15→19.62 MB for 20×20 (decimal MB). These
are Python traced allocations at the root, not whole-process RSS or whole-search
memory guarantees. Sharing removes the memory increase seen in the initial
unshared implementation while retaining the faster arithmetic.

Evidence is under `generated/neural_attention/magic_numeric_optimization/`:
`comparison_final/` contains frozen hashes, raw runs and summary medians;
`memory_root_final.json` records the separate allocation check. Intermediate
`comparison/` and `ablations/` describe the version before layout sharing and
must not be relabeled as final-runtime measurements. Source snapshots are retained
as `numeric_before.py` and `numeric_rank_unshared.py`.

Portable final evidence is also committed under
[`benchmarks/results/magic_numeric_2026-10-12/`](../../benchmarks/results/magic_numeric_2026-10-12/summary.json):
summary medians, all 54 raw timed runs, normalized source hashes, and the earlier
profiling and 11×11–20×20 scaling results. The latter two archives explicitly
identify the pre-optimization runtime. The saved settings are in
[`magic_best_parameters.json`](magic_best_parameters.json).

The related command-line tools are `magic_scaling` (saved settings, increasing
sizes, exact validation), `magic_profile` (separate wall attribution and CPU
profiles), and `magic_solution_paths` (successful-path extraction and static
replay controls). Each is a module under `experiments.neural_attention` and
accepts `--output` for a fresh evidence directory; use `--help` for its options.

The comparison can be repeated with a fresh output directory:

```sh
git show 894d2bd:src/snarky/finite/numeric.py > /tmp/snarky-numeric-before.py
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_numeric_benchmark \
  --before /tmp/snarky-numeric-before.py \
  --output generated/neural_attention/magic_numeric_optimization_NEW
```

The runner also accepts `--variants baseline rank_only span_only optimized` for
isolated comparisons. Correctness checks cover shuffled rank masks, shrinks and
restores, signed newly compiled spans, enormous translations, full enumeration,
fallback above the new limit, and independent caches for shared layouts under
equalities and both inequality directions.

Final validation: the non-slow redesign gate passes 1,209 tests, with four skips
and 58 slow tests deselected. The ordering, successful-path, and original
magic-square helper suites pass another 28 tests. Mypy checks all 103 runtime
source files; Ruff, formatting, diff whitespace checks, and first-party Markdown
links pass. The slow application/release suite was not rerun for this follow-up.
