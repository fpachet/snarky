# Magic-square benchmarks

Recorded on **13 October 2026**, comparing the previous sum-propagation kernel
with the exact dense-sum fast paths added in commit `39e8709`.

The largest completed square in this comparison is **16×16**, solved in
**6.94 seconds**, versus **11.11 seconds** before the optimization. Most tested
sizes improve; 9×9 is about 2% slower.

## Completed solves

Times are median seconds over **three runs per version**, including model setup
and search. Search settings are fixed for each size and identical between
versions. A speedup greater than 1 means faster.

| Square | Before | After | Speedup | Search nodes |
|---|---:|---:|---:|---:|
| 6×6 | 0.063 s | 0.061 s | 1.03× | 90 |
| 8×8 | 0.171 s | 0.126 s | 1.36× | 161 |
| 9×9 | 2.272 s | 2.314 s | 0.98× | 2,962 |
| 10×10 | 0.457 s | 0.277 s | 1.65× | 246 |
| 11×11 | 0.813 s | 0.474 s | 1.71× | 258 |
| 12×12 | 1.179 s | 0.563 s | 2.10× | 182 |
| 13×13 | 3.388 s | 2.390 s | 1.42× | 1,488 |
| 14×14 | 2.759 s | 1.224 s | 2.25× | 219 |
| 16×16 | 11.108 s | 6.938 s | 1.60× | 2,536 |

All versions return the same square and explore the same nodes for each size.
The improvement comes from cheaper propagation. Times include failed branches
within each search, but exclude the earlier work of discovering its settings.

## Larger searches: bounded measurements

These rows measure a fixed beginning of the search. **They are not solution
times, and no solution was returned in these runs.**

| Square | Nodes measured | Before | After | Speedup |
|---|---:|---:|---:|---:|
| 15×15 | First 80 | 3.272 s | 0.699 s | 4.68× |
| 18×18 | First 30 | 4.137 s | 0.786 s | 5.26× |
| 20×20 | First 30 | 8.535 s | 1.206 s | 7.08× |

## Model and optimization

A blank normal `n×n` magic square uses every integer from `1` through `n²`
exactly once. Every row, column, and both main diagonals must sum to
`n(n² + 1)/2`. The model has one global all-different constraint and `2n + 2`
sum constraints. Some saved search settings also use explicit blank-square
symmetry restrictions.

The new sum kernel has two fast paths:

- Consecutive integer contribution domains use exact interval filtering.
- A conservative arithmetic certificate can prove that all candidates in holey
  domains have sum support, avoiding reachable-sum tables.

Other cases use the existing exact bitset algorithm. The comparison changes
only `NumericPlan._equality_supports`; it uses the same all-different kernel,
search heuristics, value orders, and seeds on both sides. No learned constraints
or reference completion are used.

9×9 benefits little because the fast paths succeed on only **1.7%** of eligible
sum revisions, versus **47%** for 12×12. It usually pays for the preliminary
checks and then runs the original algorithm. These separate diagnostic counts
are excluded from the timing measurements.

## Evidence and source files

| File | Contents |
|---|---|
| [summary.json](summary.json) | Medians, speedups, node budgets, and validation summary |
| [runs.jsonl](runs.jsonl) | All 72 individual runs, settings, counters, and returned squares |
| [presets.json](presets.json) | Exact search settings used for this comparison |
| [frozen.json](frozen.json) | Source hashes and measurement schedule |
| [outcome_counts_9_12.json](outcome_counts_9_12.json) | Fast-path success counts explaining the 9×9 result |
| [profile_after/summary.json](profile_after/summary.json) | Separate wall-time and CPU profiling of the first 80 nodes of 15×15 and 16×16 |
| [numeric_before.py](numeric_before.py) | Previous numeric source, from commit `3309951` |
| [numeric_after.py.txt](numeric_after.py.txt) | Exact optimized numeric source snapshot |
| [runner_snapshot.py.txt](runner_snapshot.py.txt) | Exact measurement-runner snapshot |

The live [model and validator](../../alice_magic.py),
[comparison runner](../../../experiments/neural_attention/magic_alldifferent_benchmark.py),
and [detailed research report](../../../experiments/neural_attention/MAGIC6_OPTIMIZATION_REPORT.md)
provide the implementation and mathematical justification.

## Run the benchmarks

Run these commands from the repository root with the development environment
installed. Use a fresh output directory for every run. The recorded optimized
implementation is commit `39e8709`; later solver changes can change the results.

Compare both sum kernels with the archived settings:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_alldifferent_benchmark \
  --kernel sum \
  --before benchmarks/results/magic_sum_dense_2026-10-13/numeric_before.py \
  --presets benchmarks/results/magic_sum_dense_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 --repeats 3 \
  --output generated/neural_attention/magic_sum_dense_NEW
```

Run only the current solver with its saved best settings:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_scaling \
  --sizes 8 11 12 13 14 16 --repeats 3 --limit 30 \
  --output generated/neural_attention/magic_squares_NEW
```

The comparison runner supports both sum and all-different kernels; select
`--kernel sum` for the results described here.

## Validation and interpretation

All **72 comparison runs** preserve nodes, failures, constraint revisions,
termination, and returned squares. All **54 returned squares** were independently
validated. The non-slow core suite passed **1,219 tests**; 37 experiment tests,
type checking, lint, and documentation-link checks also passed. The 58 slow tests
were excluded from that core run.

Runs are sequential and timing excludes interpreter imports and validation.
Hardware and system load affect wall time. Repeating one blank square measures
timing reproducibility, not performance across independent or clued puzzles.

On the profiled 15×15/16×16 prefixes, sum propagation now takes about 6–11% of
search time, while all-different takes about 80–82%. Those percentages describe
the prefixes only.

## Earlier experiments

- [Restart portfolios and all-different optimization, 12 October](../magic_portfolio_2026-10-12/summary.json): includes failed-attempt costs and discovery of settings for 12×12, 13×13, and 16×16.
- [11×11 breakthrough, 12 October](../magic11_2026-10-12/summary.json): saved seeded search settings and five repeat solves.
- [Numeric masks and larger compiled spans, 12 October](../magic_numeric_2026-10-12/summary.json): the preceding numeric-kernel comparison.
