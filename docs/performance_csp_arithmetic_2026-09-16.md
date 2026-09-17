# First CSP optimization slice — 16 September 2026

This implements the first diagnostic and arithmetic slice of the
[CSP roadmap](csp_optimization_roadmap_2026-09-16.md): opt-in search observations,
a slow-case diagnostic runner, exact faster arithmetic filtering and construction
of the search incident index in one pass over constraint scopes. Native NValue,
compact interval domains, stronger weighted equalities and search-policy changes
remain future work.

The measured comparison is **Python Snarky versus Python Snarky**, with unchanged
models and dom/wdeg/declared-value policies. The reference runtime is `88c366f`;
the candidate source snapshot records the uncommitted implementation precisely.
The earlier [Rust/Python Prune baseline](performance_prune_2026-09-16.md) remains
unchanged and is not presented as a new Prune measurement.

## Why these changes

The [before diagnostics](../benchmarks/results/csp_diagnostics_2026-09-16_before/results.json)
cover 16 slow cases, with a 200-node/two-second cooperative budget, separate
CPU profiles, and a ten-second external safety cap. Instrumentation changes
execution cost; these are diagnostic observations, not latency speedups.

- Magic sequence 20 completed its 32-node search, with about 1.05 s inside weighted
  linear filtering in the instrumented run. Its long equalities remain a target
  for the next slice.
- Magic sequence 40 spent about 2.28 s in search setup under profiling and reached
  zero nodes. Dominating Queens 8 similarly spent about 2.40 s in setup. Search
  was scanning every constraint for every variable and repeatedly constructing
  each constraint's scope. The profiles justified replacing this with a single
  pass over the scopes, preserving their order and membership semantics.
- In the queens-104 profile, linear filtering took about 0.76 s, all-different
  filtering 0.64 s, domain retention 0.30 s and domain value extraction 0.19 s.
  This supports arithmetic work now and domain/all-different investigations later.
- The knapsack diagnostic retained valid improving incumbents before its node
  limit. Limited runs now expose search progress rather than only a timeout.

The [after diagnostics](../benchmarks/results/csp_diagnostics_2026-09-16_after/results.json)
show that Dominating Queens 8 now reaches 21 nodes instead of zero under the
same two-second profiled budget, and FT06 optimization reaches 169 rather than
89. Magic sequence 40 reaches one node, but its long weighted equalities remain
expensive. These are progress observations on time-limited searches, not proofs
or matched-work latency ratios.

The profiles cover the direct Python finite solver; rule matching is not in the
pure-CSP execution path.

## Implementation and preserved semantics

For a weighted inequality, a candidate value has support exactly when its own
contribution plus the extremal contributions of the other variables satisfies
the inequality. The new filter uses that criterion directly, including negative
coefficients, holes and arbitrary-size integer arithmetic. It avoids reachable-sum
sets while preserving the previous supported domains. Equalities with three or
more variables retain the existing exact algorithm.

Unary equalities and binary affine equalities use direct contribution membership.
Binary order comparisons use extrema; disequality only needs singleton checks.
All are exact support filters on the admitted scopes. The shared kernels serve
both the direct and legacy CSP runtimes. Complete-assignment feasibility and
objective evaluation are unchanged.

The incident-index construction now visits each scope once. It preserves
constraint order and deduplicates repeated references exactly as the old membership
scan did. It does not change weighted-degree attribution or variable tie-breaking.

The optional `on_progress` callback exposes immutable search observations and
validated incumbents. Its root bound stays explicitly separate from the final
proof bound; only the final `QueryResult` provides completion/optimality status.
Exceptions unwind native and mixed checkpoints. The callback is disabled by
default and is not supported for partition/exact-sampling queries.

The diagnostic worker flushes JSON progress to stderr, so an external kill retains
complete earlier observations. The collector flags an incomplete final log line;
it cannot turn that fragment into a result. CPU profiling and allocation tracing
use separate runs. Expensive kernels still have cooperative rather than guaranteed
mid-call deadline checks; the parent process enforces the hard cap.

## Paired measurements

Both versions complete **47 of 59 instance/mode workloads** in every measured
repetition under the five-second cap. The same 12 workloads remain limited.
All 47 completed workloads have identical normalized solutions, node counts,
failure counts and revision counts across both versions and all repetitions.
Optimization proofs are retained. Selected process medians:

| Workload | Reference (s) | Candidate (s) | Speedup |
| --- | ---: | ---: | ---: |
| `extended/jobshop_ft06_55` | 0.2706 | 0.1771 | 1.53× |
| `extended/jobshop_ft06_60` | 1.3409 | 0.7324 | 1.83× |
| `extended/missionaries_15` | 0.3282 | 0.1558 | 2.11× |
| `extended/bibd_9` | 0.3649 | 0.1926 | 1.89× |
| `extended/queens_50` | 1.2488 | 0.8737 | 1.43× |
| `optimization/jobshop_ft06_opt` | 2.5937 | 1.3816 | 1.88× |

Small regressions are also retained in the record. The original three-pair run
showed up to about 8.8% higher process latency on a completed small case. A
[seven-pair follow-up](../benchmarks/results/csp_startup_check_2026-09-16/summary.json)
rechecked six selected instances (seven modes), including a compiler-solved empty
model. It did not establish a uniform startup cost, but some overhead remains:

| Workload / mode | Process ms, before → after | Native solve ms, before → after |
| --- | ---: | ---: |
| `initial/latin_square` / first | 110.86 → 118.07 | 0.749 → 0.777 |
| `initial/latin_square` / all | 110.37 → 110.97 | 1.711 → 1.714 |
| `extended/magic_square_4` / first | 151.38 → 153.78 | 42.515 → 42.420 |
| `extended/sudoku_easy` / first | 117.18 → 116.52 | 6.750 → 5.970 |
| `optimization/golomb_opt_6` / first | 120.08 → 120.59 | 10.626 → 9.589 |
| `all_different/all_different_global_12` / first | 108.53 → 108.94 | 0.187 → 0.192 |
| `large_domains/large_domain_chain_2048` / first | 108.23 → 111.91 | 0.050 → 0.057 |

Latin-square first-solution process latency remains about 6.5% higher in this
follow-up, while its native solve difference is about 0.03 ms. These measurements
do not isolate the cause, so this is recorded as an unresolved small-case overhead,
not dismissed as noise. The compiler-solved chain measures overhead only; it
provides no evidence of support for billion-value native domains.

The [paired raw record](../benchmarks/results/csp_arithmetic_2026-09-16/results.json)
and [summary](../benchmarks/results/csp_arithmetic_2026-09-16/summary.json)
retain all warmups, measured runs, outputs, counters and timeout outcomes. Both
runtimes use the same worker and frozen FlatZinc JSON. One discarded warmup and
three alternating measured pairs use fresh processes and a five-second external
limit, with no concurrent test/profile jobs. Compilation and independent Gecode
checks are excluded; startup, construction, search and output are included.
Native phase times are also recorded. New returned solutions are checked against
the original primitives and independently fixed into the original MiniZinc model
for Gecode validation. Enumeration compares complete normalized solution sets.

Machine: Apple M1 Pro, 32 GiB RAM, Python 3.13.11. Background/thermal state is not
controlled. Three samples provide descriptive medians, not confidence intervals.
Every timeout is retained. No speedup is inferred between two censored runs.

## Compatibility controls and memory

The [control record](../benchmarks/results/csp_controls_2026-09-16/results.json)
contains three alternating pairs per workload, with warmup. These medians include
preparation and search but exclude process startup, unlike the table above.

| Control | Reference (s) | Candidate (s) |
| --- | ---: | ---: |
| `rules/small/triangle_closure:indexed` (rules) | 0.000986 | 0.000985 |
| `joins/25x8/streamed` (rules) | 0.108648 | 0.105993 |
| `magic4` (legacy) | 0.391340 | 0.391457 |
| `mixed_magic3` (mixed) | 0.002350 | 0.002349 |
| `markov33x8` (native) | 0.134176 | 0.134793 |
| `boulez` (auto) | 1.619739 | 1.622845 |

All observations and search counters match. Boulez Blues still returns the exact
published sequence and proves the same optimum, without seeding the search.
The controls show no material latency change in rules, legacy magic square,
mixed execution, the Markov case or Boulez at this sample size.

Separate allocation runs execute exactly 30 nodes per model and use the same
instrumentation in both runtimes. The memory reference is the archived
pre-arithmetic runtime with the observation hook, rather than bare `88c366f`.
Nodes, failures, revisions, bounds and returned assignments match. One sample per
case is a baseline observation, not a statistically established memory gain.

| Workload | Traced Python peak MiB, before → after | Whole-process peak RSS MiB, before → after |
| --- | ---: | ---: |
| `extended--queens_50` | 4.839 → 4.707 | 39.38 → 36.72 |
| `optimization--jobshop_ft06_opt` | 1.389 → 1.382 | 26.33 → 25.16 |
| `optimization--knapsack_20_opt` | 1.251 → 1.247 | 27.41 → 27.89 |

Allocation-instrumented timings are deliberately excluded from speedup claims.
Tracing changes costs substantially; for example, the knapsack trace takes
6.87 s before and 11.41 s after, despite similar search times in the separate
CPU-profile diagnostics without allocation tracing.
This deserves a separate investigation if traced execution matters to users;
it is not evidence that ordinary knapsack search improved.

Profiler per-family `removed`/`effective` counters describe filtering of temporary
scoped domains, including a failed revision whose reductions may not be committed.
They are not counts of permanently removed candidates. RSS is the whole-process
high-water mark, including imports; traced allocation is a separate Python-only
measurement. Neither is treated as a cross-language memory comparison.

## Validation

The non-Bach gate passed **991 tests, with three skips**, in 187.45 s. A subsequent
focused run covers the final additional alias, mixed-observer and truncated-log
cases. Arithmetic tests compare supported values with exhaustive assignments on
1,050 deterministic signed/holey cases, additional very large integers, all small
binary domain subsets, and repeated sibling rollback. Observer tests cover limit
statuses, validated seeds, exceptional exits, root-bound labeling and mixed-state
restoration. A Python 3.12 diagnostic smoke run proves Golomb 6 optimal at 17.

The final focused set passes all 33 tests. Lint (`ruff check .`) and static types
(`mypy src`, 93 source files) pass. Validation logs and exact commands are retained
in the [validation record](../benchmarks/results/csp_arithmetic_2026-09-16/validation.md).
Textual-source validation, Markdown links, both distribution builds, distribution
contents and isolated wheel installation with and without the CSP companion also
pass.

## Reproduction

From the repository root, extract the reference runtime without checking out over
current work:

```sh
mkdir /tmp/snarky-csp-reference-88c366f
git archive 88c366f src | tar -x -C /tmp/snarky-csp-reference-88c366f
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source /tmp/snarky-csp-reference-88c366f \
  --reference-ref 88c366f --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/csp_arithmetic_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup diagnose \
  --seconds 2 --nodes 200 --hard-seconds 10 \
  --output benchmarks/results/csp_diagnostics_NEW_LABEL
```

Run rule/mixed/Markov controls with:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_controls \
  --reference /tmp/snarky-csp-reference-88c366f \
  --output benchmarks/results/csp_controls_NEW_LABEL
```

To reproduce allocation comparisons, extract `candidate.tar.gz` from the before
record to a separate directory and pass it as `--memory-reference PATH` to the
control runner. The archived pre-arithmetic source includes the observation hook.
The small-case repeat uses `compare --repeats 7` with the six `--only` filters
corresponding to the table above; every exact subprocess command is in its record.

Use `--only jobshop_ft06_opt` to select a case, or `--allocation` for a separate
traced-allocation run instead of a CPU profile. Output directories are never
overwritten. Source archives and hashes accompany the records. The process worker
can also run independently via `benchmarks/csp_diagnostics.py --model INPUT.fzn.json
--diagnostic --nodes 200 --seconds 2`.

This slice does not claim that the entire P0/P1 roadmap is complete. Matched Prune
branching, additional queue/materialization instrumentation, weighted-equality
improvements and the larger domain API remain separate follow-ups. The remaining
31 upstream instances are still unavailable; the existing coverage limitation is
unchanged.

## All primary workload outcomes

Process medians in seconds; `limit` means all three samples hit the five-second
external cap. Ratios are reported only when both versions completed all samples.
The two compiler-solved large-domain entries remain coverage gaps for native
large-domain solving.

| Workload | Mode | Reference | Candidate | Speedup |
| --- | --- | ---: | ---: | ---: |
| `initial/booleans` | first | 0.1174 | 0.1145 | 1.03× |
| `initial/booleans` | all | 0.1301 | 0.1171 | 1.11× |
| `initial/latin_square` | first | 0.1178 | 0.1253 | 0.94× |
| `initial/latin_square` | all | 0.1212 | 0.1168 | 1.04× |
| `initial/linear` | first | 0.1224 | 0.1276 | 0.96× |
| `initial/linear` | all | 0.1217 | 0.1178 | 1.03× |
| `initial/magic_square` | first | 0.1296 | 0.1244 | 1.04× |
| `initial/magic_square` | all | 0.1331 | 0.1253 | 1.06× |
| `initial/pigeonhole` | all | 0.1160 | 0.1257 | 0.92× |
| `initial/queens` | first | 0.1190 | 0.1295 | 0.92× |
| `initial/queens` | all | 0.1253 | 0.1269 | 0.99× |
| `initial/queens_104` | first | limit | limit | — |
| `extended/magic_square_4` | first | 0.1617 | 0.1718 | 0.94× |
| `extended/magic_square_5` | first | limit | limit | — |
| `extended/magic_square_3` | first | 0.1322 | 0.1177 | 1.12× |
| `extended/magic_sequence_10` | first | 0.1513 | 0.1529 | 0.99× |
| `extended/magic_sequence_20` | first | 1.1627 | 1.1332 | 1.03× |
| `extended/magic_sequence_40` | first | limit | limit | — |
| `extended/golomb_6` | first | 0.1139 | 0.1139 | 1.00× |
| `extended/golomb_7` | first | 0.1910 | 0.1823 | 1.05× |
| `extended/golomb_8` | first | 0.6093 | 0.5675 | 1.07× |
| `extended/jobshop_ft06_55` | first | 0.2706 | 0.1771 | 1.53× |
| `extended/jobshop_ft06_60` | first | 1.3409 | 0.7324 | 1.83× |
| `extended/missionaries_11` | first | 0.2384 | 0.1438 | 1.66× |
| `extended/missionaries_13` | first | 0.2853 | 0.1481 | 1.93× |
| `extended/missionaries_15` | first | 0.3282 | 0.1558 | 2.11× |
| `extended/bin_packing_20` | first | 0.2277 | 0.2199 | 1.04× |
| `extended/bin_packing_30` | first | 0.6572 | 0.6531 | 1.01× |
| `extended/bin_packing_40` | first | 1.8671 | 1.8650 | 1.00× |
| `extended/bibd_7` | first | 0.1405 | 0.1264 | 1.11× |
| `extended/bibd_9` | first | 0.3649 | 0.1926 | 1.89× |
| `extended/sudoku_easy` | first | 0.1158 | 0.1249 | 0.93× |
| `extended/sudoku_medium` | first | 0.1142 | 0.1229 | 0.93× |
| `extended/sudoku_hard` | first | 0.1645 | 0.1616 | 1.02× |
| `extended/queens_50` | first | 1.2488 | 0.8737 | 1.43× |
| `extended/queens_104` | first | limit | limit | — |
| `extended/queens_150` | first | limit | limit | — |
| `optimization/golomb_opt_6` | first | 0.1190 | 0.1260 | 0.94× |
| `optimization/golomb_opt_7` | first | 0.2488 | 0.2379 | 1.05× |
| `optimization/jobshop_ft06_opt` | first | 2.5937 | 1.3816 | 1.88× |
| `optimization/knapsack_20_opt` | first | limit | limit | — |
| `optimization/bin_packing_20_opt` | first | limit | limit | — |
| `all_different/all_different_global_10` | first | 0.1081 | 0.1086 | 1.00× |
| `all_different/all_different_global_12` | first | 0.1086 | 0.1145 | 0.95× |
| `all_different/all_different_global_16` | first | 0.1085 | 0.1140 | 0.95× |
| `all_different/all_different_pairwise_10` | first | limit | limit | — |
| `all_different/all_different_permutation_global_16` | first | 0.1143 | 0.1155 | 0.99× |
| `all_different/all_different_permutation_pairwise_16` | first | 0.1317 | 0.1265 | 1.04× |
| `incremental_all_different/all_different_incremental_10` | first | 0.1834 | 0.1767 | 1.04× |
| `incremental_all_different/all_different_incremental_12` | first | 0.2833 | 0.2687 | 1.05× |
| `incremental_all_different/all_different_incremental_16` | first | 0.7471 | 0.7427 | 1.01× |
| `nvalue/nvalue_permutation_16_sat` | first | 0.1149 | 0.1234 | 0.93× |
| `nvalue/nvalue_pigeonhole_16_unsat` | first | 0.1087 | 0.1126 | 0.97× |
| `nvalue/nvalue_queens_6_sat` | first | limit | limit | — |
| `nvalue/nvalue_queens_7_sat` | first | limit | limit | — |
| `nvalue/nvalue_queens_6_unsat` | first | limit | limit | — |
| `nvalue/nvalue_queens_8_sat` | first | limit | limit | — |
| `large_domains/large_domain_chain_256` | first | 0.1107 | 0.1099 | 1.01× |
| `large_domains/large_domain_chain_2048` | first | 0.1092 | 0.1125 | 0.97× |
