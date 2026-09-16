# Second CSP optimization slice — 16 September 2026

This follows the [arithmetic/setup slice](performance_csp_arithmetic_2026-09-16.md)
at `d5f9a2d`. It improves exact integer equalities and avoids repeated domain-value
projection. Constraint definitions, search policy, objectives and complete-solution
semantics are unchanged. Native NValue, objective cuts and compact interval domains
remain separate roadmap stages.

## Exact equality filtering

SUM and weighted equality share one support algorithm. It first removes candidates
outside the exact necessary contribution bounds, subtracts per-variable minima,
and divides by the common divisor of contribution differences. Negative coefficients,
negative values, holes, fixed terms and arbitrary-size integer offsets are supported.
An indivisible target is infeasible. Targets nearer the maximum are reflected to
reduce the reachable range without changing assignments.

For a bounded normalized target, a Python integer represents reachable prefix sums.
A backward bitset represents the partial sums that the remaining suffix can complete.
A candidate contribution has support exactly when the shifted backward bitset
intersects its prefix. This avoids constructing every prefix/suffix sum pair.
Removing an unsupported candidate cannot invalidate a complete solution, so backward
construction may use the already-supported suffix values.

Dense tables are selected only below 262,144 target bits and a 32-million-bit
aggregate prefix budget. Intermediate shifts have at most twice the target width.
These limits bound the dense representation, not all solver memory. Wider inputs
use exact sparse reachable sets and membership support checks; no bounds-only
filter is substituted. Sparse fallback can still be expensive and remains subject
to the existing cooperative search deadline and external benchmark process cap.
A general configurable propagation resource budget remains future work.

Unary/binary weighted channels and inequality fast paths from the previous slice
remain unchanged. The legacy SUM helper remains an import-compatible entry point
into the shared exact algorithm.

## Domain projection cache

Finite domains already use reversible masks. They now retain one immutable value
tuple per variable, tagged with the mask that produced it. Repeated reads of an
unchanged mask reuse the tuple in declared order. A mask mismatch after narrowing
or rollback reconstructs it. The cache holds one entry per variable and does not
retain all visited search states or require extra trail entries.

This change affects native and mixed execution; it adds no forward chaining to
pure CSP. A separate equality-only runtime is archived for the cache ablation.

## Measurements

Reference `d5f9a2d` completes **47/59** workloads and the new
runtime **48/59**, requiring completion in all three measured repetitions.
All 47 mutually completed workloads preserve nodes, failures, revisions and
normalized solutions across all repetitions. These are Python/Python measurements
with identical models, dom/wdeg and declared value order; there is no search-policy
change. Timings include process startup, construction, search and output.

| Workload | Reference seconds | Candidate seconds | Speedup |
| --- | ---: | ---: | ---: |
| `extended/magic_square_4` | 0.1534 | 0.1483 | 1.03× |
| `extended/magic_sequence_10` | 0.1391 | 0.1364 | 1.02× |
| `extended/magic_sequence_20` | 1.0941 | 0.1741 | 6.28× |
| `extended/magic_sequence_40` | >5 (limit) | 0.3509 | — |
| `extended/jobshop_ft06_55` | 0.1795 | 0.1707 | 1.05× |
| `extended/jobshop_ft06_60` | 0.7355 | 0.6712 | 1.10× |
| `extended/bin_packing_40` | 1.8638 | 0.2567 | 7.26× |
| `extended/queens_50` | 0.8733 | 0.8163 | 1.07× |
| `optimization/jobshop_ft06_opt` | 1.3828 | 1.2434 | 1.11× |

The [raw comparison](../benchmarks/results/csp_equality_2026-09-16/results.json)
and [all 59 summary rows](../benchmarks/results/csp_equality_2026-09-16/summary.json)
retain warmups, repetitions, phase timings, counters, proofs and every limit.
One discarded warmup and three alternating fresh-process pairs use a five-second
external cap. Compilation and independent Gecode validation are excluded.
The machine is an Apple M1 Pro, 32 GiB RAM, Python 3.13.11. Timed jobs run
sequentially without overlapping test/profile jobs. Background and thermal state
are uncontrolled; three samples are descriptive medians, not confidence intervals.

Every returned assignment is checked against original FlatZinc primitives.
First-solution/optimization assignments are independently fixed into the original
MiniZinc model for Gecode validation; complete enumerations compare normalized
solution sets. Timeout is not infeasibility
or optimality. The two compiler-solved chains still do not measure native support
for billion-value domains. The unavailable 31 upstream instances remain excluded.

### Cache ablation

The [ablation](../benchmarks/results/csp_projection_ablation_2026-09-16/summary.json)
compares the archived equality-only runtime with equality plus the domain cache.
Each case has one warmup and three alternating measured pairs. All search counts
and normalized solutions match. This isolates the cache contribution from the
larger equality improvement.

| Workload | Equality only seconds | With cache seconds | Speedup |
| --- | ---: | ---: | ---: |
| `extended/magic_square_4` | 0.1471 | 0.1471 | 1.00× |
| `extended/magic_sequence_40` | 0.3588 | 0.3486 | 1.03× |
| `extended/queens_50` | 0.8691 | 0.8129 | 1.07× |
| `optimization/jobshop_ft06_opt` | 1.3915 | 1.2455 | 1.12× |
| `incremental_all_different/all_different_incremental_10` | 0.1768 | 0.1748 | 1.01× |
| `incremental_all_different/all_different_incremental_12` | 0.2672 | 0.2632 | 1.02× |
| `incremental_all_different/all_different_incremental_16` | 0.7476 | 0.7207 | 1.04× |

### Regressions retained

The primary record includes the following process-median regressions above 3%.
They remain part of the comparison; small timings should not be treated as a
precise measure of propagation throughput.

| Workload / mode | Reference seconds | Candidate seconds | Change |
| --- | ---: | ---: | ---: |
| `initial/latin_square` / first | 0.1098 | 0.1138 | +3.6% |
| `initial/magic_square` / first | 0.1114 | 0.1153 | +3.5% |
| `initial/queens` / first | 0.1108 | 0.1165 | +5.2% |
| `extended/missionaries_13` / first | 0.1473 | 0.1522 | +3.3% |
| `extended/bibd_7` / first | 0.1238 | 0.1328 | +7.3% |
| `extended/sudoku_easy` / first | 0.1155 | 0.1243 | +7.6% |
| `extended/sudoku_medium` / first | 0.1135 | 0.1190 | +4.8% |
| `optimization/golomb_opt_6` / first | 0.1189 | 0.1228 | +3.3% |
| `all_different/all_different_global_12` / first | 0.1091 | 0.1126 | +3.1% |
| `all_different/all_different_global_16` / first | 0.1095 | 0.1153 | +5.2% |
| `large_domains/large_domain_chain_2048` / first | 0.1088 | 0.1164 | +7.0% |

## Compatibility, memory and validation

The [after profiles](../benchmarks/results/csp_equality_profiles_2026-09-16/results.json)
use separate CPU-instrumented runs with a 200-node/two-second cooperative budget
and a ten-second process cap. They are not latency samples. Magic sequence 40
completes at 62 nodes; knapsack reaches the same 200-node limit with valid
incumbents but no proof. On queens 104 and 150, all-different accounts for about
1.02–1.08 s of each two-second search profile. On incremental Latin 16 it accounts
for about 1.53 s. In the four Dominating Queens profiles, table filtering takes
about 0.62–0.71 s, versus 0.21–0.28 s for linear filtering; domain/scheduling and
other overhead make up much of the remainder.

These observations support native NValue to replace the large decomposition,
then focused all-different/propagation overhead work and stronger objective bounds.
The remaining eleven timeouts and the 3/5 optimization completion count are
unchanged except for the newly completed magic sequence 40. Compact domains and
a complete propagation resource-budget API remain separate work.

The [control record](../benchmarks/results/csp_equality_controls_2026-09-16/results.json)
contains three alternating pairs with warmup. These times include preparation and
search but exclude process startup. All observations/counters match, including
Boulez's exact published sequence, proved optimum and unseeded search.

| Control | Reference seconds | Candidate seconds |
| --- | ---: | ---: |
| `rules/small/triangle_closure:indexed` / rules | 0.000994 | 0.001009 |
| `joins/25x8/streamed` / rules | 0.109369 | 0.107988 |
| `magic4` / legacy | 0.390822 | 0.407638 |
| `mixed_magic3` / mixed | 0.002344 | 0.002404 |
| `markov33x8` / native | 0.134732 | 0.136995 |
| `boulez` / auto | 1.624216 | 1.610898 |

Separate allocation runs compare the same 30 entered nodes, with identical
failures, revisions, bounds and outputs, against the same `d5f9a2d` reference.
Each is one instrumented sample; no latency claim uses its traced timings.
RSS includes imports and is a whole-process high-water mark. Python traced peaks
cover a different scope and are not a cross-language memory comparison.

The cache trades a small amount of persistent per-variable storage for fewer
conversions. In these samples, Python traced peak rises by about 28 KiB on queens
and 22 KiB on FT06; knapsack's new equality algorithm reduces its peak substantially.
The legacy magic-square control is about 4.3% slower, and mixed/Markov controls
also show small increases. These are retained regressions, not claims that every
path benefits; Boulez's exact result and proof remain unchanged.

| Workload | Python traced peak MiB, before → after | Process RSS MiB, before → after |
| --- | ---: | ---: |
| `extended--queens_50` | 4.707 → 4.735 | 37.55 → 36.30 |
| `optimization--jobshop_ft06_opt` | 1.383 → 1.404 | 25.31 → 25.36 |
| `optimization--knapsack_20_opt` | 1.247 → 0.188 | 27.92 → 23.22 |

The full non-Bach gate passes **1,008 tests, three skips**, in 185.93 s. New tests
check 1,200 deterministic weighted/SUM support problems across dense and forced
sparse paths against complete assignments, plus huge offsets/common divisors,
wide sparse spans, infeasible targets, representation-budget fallback and nested
rollback. Cache tests repeatedly narrow, fail and restore sibling/nested branches,
checking current values, declared order and removal restoration. Existing rule,
legacy CSP, mixed and Markov regressions also pass. Ruff and mypy (93 source files)
pass; commands and logs are retained in the
[validation record](../benchmarks/results/csp_equality_2026-09-16/validation.md).
Textual sources, Markdown links, both distribution builds, distribution contents
and isolated wheel-install checks also pass. A Python 3.12 worker completes
magic sequence 40 in the same 62 nodes with a validated assignment.

## Fresh focused comparison with Prune

A new six-case interleaved comparison uses the original Prune collector, pinned
Rust release binary and unchanged frozen models. It is separate from the
Python/Python worker above, with its own startup/rendering path. One warmup and
three measured repetitions use the same five-second cap and independent Gecode
checks. The [raw record](../benchmarks/results/prune_equality_focus_2026-09-16/results.json)
and [summary](../benchmarks/results/prune_equality_focus_2026-09-16/summary.csv)
retain source/binary hashes and all samples.

| Workload | Prune seconds | Snarky seconds | Snarky / Prune |
| --- | ---: | ---: | ---: |
| `extended/magic_sequence_20` | 0.0050 | 0.1781 | 35.8× |
| `extended/magic_sequence_40` | 0.0089 | 0.3519 | 39.5× |
| `extended/bin_packing_40` | 0.0041 | 0.2631 | 64.2× |
| `extended/queens_50` | 0.0105 | 0.8253 | 78.6× |
| `optimization/jobshop_ft06_opt` | 0.0081 | 1.2493 | 153.4× |
| `nvalue/nvalue_queens_6_unsat` | 0.0038 | >5 (limit) | — |

Prune remains substantially faster. Different branching policies and constraint
encodings remain, especially native NValue versus decomposition; these ratios
compare whole Rust/Python implementations, not equivalent search trees or language
execution alone. This focused run is not a new full Prune portfolio measurement.
The complete historical Prune baseline remains 59/59; Snarky's new full run is
48/59, with 3/5 optimization proofs.

## Reproduction

```sh
mkdir /tmp/snarky-csp-reference-d5f9a2d
git archive d5f9a2d src | tar -x -C /tmp/snarky-csp-reference-d5f9a2d
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source /tmp/snarky-csp-reference-d5f9a2d --reference-ref d5f9a2d \
  --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/csp_equality_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_controls \
  --reference /tmp/snarky-csp-reference-d5f9a2d --reference-ref d5f9a2d \
  --memory-reference /tmp/snarky-csp-reference-d5f9a2d \
  --output benchmarks/results/csp_equality_controls_NEW_LABEL
```

For the cache ablation, extract `reference.tar.gz` from the ablation record to a
new directory and use it as `--reference-source`; it contains the equality-only
runtime. The source hashes, original commands, inputs and all repetitions are
retained. Output directories are never overwritten.

The after-profile command is `benchmarks.csp_followup diagnose --seconds 2 --nodes
200 --hard-seconds 10 --output NEW_DIRECTORY`. Reproduce the focused Prune run
with the original `benchmarks.prune_comparison` command from the
[Prune baseline](performance_prune_2026-09-16.md), adding one `--only` filter for
each of the six full workload identifiers in the table above. Exact worker
commands and parameters are retained in each record.
