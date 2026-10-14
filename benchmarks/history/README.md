# Benchmark history

This is an evidence index. For current summaries and commands, use the
[benchmark guide](../README.md). Dated records preserve the code and decisions
of their experiment; they are not all active solver features.

This directory was renamed from `benchmarks/results/`. Frozen JSON records,
source snapshots, patches and source archives retain their original bytes,
including recorded paths with the former name. Current links and benchmark
tools use `benchmarks/history/`; those old paths are provenance, not current
output locations. Validate the recent magic-square evidence with
`python scripts/check_benchmark_history.py` from the repository root. The checker
uses archived source content and checksums rather than requiring today's solver
to match every historical version.

## Magic-square experiment history

**Current overview:** [Magic squares](../README.md#magic-squares).
**Latest profiling:** [Current CP and residual-hybrid profiles](magic_native_profile_2026-10-14/report.json).
Fresh complete searches at `8245d27` prioritize a SUM support kernel before
ALLDIFF: hybrid 16×16 spends 52%/23% in their revisions; 14×14 spends 77%/11%.
The archive separates uninstrumented timings, wall attribution and cProfile,
and includes a startup-heavy 20×20 prefix with no complete solution.

**Latest experiment:** [Exact native SUM supports](magic_sum_kernel_2026-10-14/report.json).
The opt-in kernel preserves exact support masks and search behavior, reducing
16×16 time 35.5% in ordinary CP and 42.0% in the residual hybrid; 14×14 improves
60.5%/58.9%. A 1,000-node 20×20 prefix is about four times faster, but a
30-second solve attempt remains incomplete. The short startup prefix regresses;
the [overview](../README.md#magic-squares) records all timings and limits.

The preceding [reusable residual kernels](magic_residual_reuse_2026-10-14/report.json)
established bitset enumeration and persistent library caching.
Arithmetic candidate filtering and bitsets reduce time a further 16–44% on
five of six tested sizes compared with the previous hybrid; 14×14 is 2% slower.
A controlled replay isolates a 1.4–2.0× bitset kernel speedup at identical work
and results. A persistent C library cache avoids recompilation across runs.
The [current overview](../README.md#magic-squares) records all six five-run
medians, build costs, changed ordering/budgets and experimental query limits.

The preceding [residual enumeration and local compilation study](magic_residual_enumeration_2026-10-14/report.json)
established the initial hybrid's benefits.
A bounded native residual solver cuts first-solution time 24–43% on the four
confirmation sizes; additional 11×11 improves 13%, while 14×14 is flat.
Per-state unrolled programs execute faster but local compilation fails to
amortize on the observed residuals. The prototype remains outside production;
the current overview records its changed search trees, query limits, build cost
and absence of a demonstrated 20×20 benefit.

**Latest native optimization:** [ALLDIFF matching repair](magic_matching_repairs_2026-10-14/summary.json).
Collect unmatched variables during validation and sort only repair starts,
preserving the intact-matching early return. A five-pair 16×16 confirmation
gives 4.459 → 4.300 s (3.6%) with identical search. An untimed audit checks all
6,799 matching transitions against the baseline; sort-key evaluations fall
99.0%. The [current overview](../README.md#magic-squares) also records small
or mixed gains elsewhere, a slower 20×20 prefix and the rejected full-scan
prototype. All 194 timing runs and both differential audits are retained.

The previous [ALLDIFF identity-layout shortcut](magic_identity_layout_2026-10-14/summary.json)
skips input-mask translation when compiled value positions already agree.
Two five-pair batches show modest gains for eligible 8×8, 9×9 and 14×14
presets; confirmation medians improve by 4.6%, 3.1% and 1.4%. Randomized
11×11/16×16 layouts cannot use the shortcut. Both batches preserve exact
search work and reduction hashes; the 20×20 measurement is a 30-node prefix.

The preceding [SUM boundary processing](magic_sum_boundaries_2026-10-13/summary.json)
reduces exact equality-filter overhead.
A dedicated five-pair 16×16 confirmation gives 4.575 → 4.462 s (2.5%), with
identical work and reduction hashes. The initial three-pair estimate was 5.5%;
both datasets and all preliminary kernels are retained. The
[current overview](../README.md#magic-squares) separates whole-solve and replay
timings, including the 20×20 prefix with no demonstrated gain.

The previous [ALLDIFF singleton exclusion](magic_alldiff_singletons_2026-10-13/summary.json)
records 5.468 → 4.655 s at 16×16. The
[graph comparison](magic_scheduler_graph_2026-10-13/README.md) remains the
detailed record of row aggregation and the earlier opt-in filters.

**Latest scaling trial:** [Search toward 20×20](magic_large_2026-10-13/summary.json).
15×15 now solves in 1.135 s over three fresh timing replays. The largest
completed size remains 16×16; 17×17–20×20 remain unresolved in the recorded
portfolios. The [current overview](../README.md#magic-squares)
separates discovery cost, replay timings and timeouts.

**Latest complete-solver comparison:**
[Snarky / Gecode / Chuffed](magic_solver_comparison_2026-10-13/summary.json).
Gecode solves 20×20 in 1.617 s median over three runs with the same logical
model and symmetry choice as Snarky. The
[current comparison](../README.md#complete-solver-comparison--13-october-2026)
records timing boundaries, selected branching settings and limitations;
85 measured runs and independently validated witnesses are archived.

The table follows the optimization sequence. “Opt-in” means experimental code
that must be selected explicitly, not a default native-solver feature.

| Stage | What was learned or changed | Decision |
|---|---|---|
| [Dense-domain SUM](magic_sum_dense_2026-10-13/README.md) | Exact fast paths avoid unnecessary reachable-sum tables | Enabled |
| [Partial sum certification](magic_sum_partial_2026-10-13/README.md) | Exact prototypes gave no consistent timing gain | Archived experiment |
| [Small residual sum systems](magic_sum_systems_2026-10-13/README.md) | Useful on suitable systems, no extra deductions on measured blank squares | Opt-in |
| [Whole-system rank diagnostic](magic_sum_global_rank_2026-10-13/README.md) | Removing the size cap did not reveal uniquely solvable larger residual systems | Diagnostic only |
| [Joint SUM + ALLDIFF](magic_sum_distinct_2026-10-13/README.md) | Selective distinct-value filtering helps some presets | Opt-in |
| [Joint-filter cost reduction](magic_sum_distinct_cost_2026-10-13/README.md) | Cheaper detection and bounded three-variable filtering | Opt-in prototype refinement |
| [Exact three-variable joint filter](magic_sum_distinct_exact_2026-10-13/README.md) | Stronger local supports help several presets | Opt-in |
| [Lookup, pair budget and matching](magic_sum_lookup_matching_2026-10-13/README.md) | Compiled lookups and expanded eligibility; validated matching fast path | Matching enabled; joint filtering opt-in |
| [Domain storage and propagation](magic_domain_ops_2026-10-13/README.md) | Lazy explanations, integer IDs, changed-mask application and queue flags | Enabled |
| [Weighted degrees, batching and graph construction](magic_scheduler_graph_2026-10-13/README.md) | Selective aggregation of repeated ALLDIFF rows gives a consistent gain | Graph aggregation enabled; other variants experimental |
| [Singleton SCC exclusion](magic_alldiff_singletons_2026-10-13/summary.json) | Skip fixed-value components without changing filtering; lower cost per node on completed magic-square searches | Enabled |
| [SUM boundary processing](magic_sum_boundaries_2026-10-13/summary.json) | Avoid redundant prefix/backward work while preserving exact supports; modest additional per-node gain | Enabled |
| [ALLDIFF identity layouts](magic_identity_layout_2026-10-14/summary.json) | Skip input-mask translation for aligned layouts; small gain on eligible magic-square presets | Enabled |
| [ALLDIFF matching repair](magic_matching_repairs_2026-10-14/summary.json) | Sort only unmatched rows while preserving repair order and the intact-matching fast path | Enabled |
| [Exact native SUM supports](magic_sum_kernel_2026-10-14/report.json) | Identical-search gains on all six completed sizes; larger 20×20 prefix improves, but no solution within 30 seconds | Opt-in exact propagator experiment |
| [Fresh CP/hybrid profiles](magic_native_profile_2026-10-14/report.json) | SUM support computation is the next native-kernel priority on most completed hybrid workloads | Diagnostic profiles; no new propagator kernel |
| [Reusable residual kernels](magic_residual_reuse_2026-10-14/report.json) | Bitset candidate filtering helps five sizes; persistent library caching removes repeat compilation | Experimental first-solution prototype |
| [Residual enumeration and local compilation](magic_residual_enumeration_2026-10-14/report.json) | Native bounded residual solving helps several sizes; compiling each state costs too much on the observed traces | Experimental first-solution prototype |

Each report links raw runs, source snapshots and reproduction commands. Times
from different stages are not automatically comparable: check their source
versions, settings, hash seed and whether the run solved the square or stopped
at a node limit.

## Other benchmark records

Workforce task symmetry and workload propagation:
[scheduling_symmetry_2026-09-28.json](scheduling_symmetry_2026-09-28.json) records
24 fresh-process runs across four ablations and two model sizes, plus separate
profiles. The [candidate patch](scheduling_symmetry_2026-09-28_candidate.patch)
reconstructs the measured runtime and collector over `f8c82b5`; the
[original profile](scheduling_symmetry_2026-09-28_profile_original.txt) identifies
the initial bottleneck. See the [report](../../docs/performance_scheduling_2026-09-28.md).

[scheduling_tests_2026-09-28.json](scheduling_tests_2026-09-28.json) records five
interleaved repetitions per workload kernel of the same 40 existing scheduling
and factor-bound tests, with outcomes and per-test durations. It measures the
effect on regression-test execution separately from the 32-task benchmark.

These JSON and CSV files are immutable raw records produced by benchmark
programs. They are tracked as scientific evidence because they document A/B
decisions, but they are not runtime source and are excluded from Python
distributions.

New records should include the benchmark name and ISO date in the filename,
plus commit, Python, platform, parameters, logical-equivalence checks, medians,
and individual samples where the format supports them.

Do not overwrite a historical record with results from another environment.
Create a new dated file and interpret it through
[`../README.md`](../README.md).

## Redesign baseline — 2026-09-16

[`redesign_baseline_2026-09-16.json`](redesign_baseline_2026-09-16.json)
records 17 non-Bach rule, incremental-join, CSP, and mixed Sudoku cases against
runtime commit `2fbdd9d`. Each has one discarded warmup and seven retained
samples, with stable work counters. The checkout was dirty with documentation
and the new collector; runtime sources were unchanged. Source and collector
hashes are recorded. This is an initial local baseline, not a paired comparison.

The [performance document](../../docs/performance_baseline.md) gives the timing
boundaries, full table, validation limitations, comparison protocol, and ledger.

## Dependency-scheduler baseline — 2026-07-27

The complete baseline before event-handler specialization uses Python 3.13.11
on macOS ARM64. The scheduler itself is commit `84f7b57`; commit `ccce61b`
only adds the shared clean/dirty provenance fields used by the broader
application runners.

Primary optimization measurements:

- [`claire_talarian_filter_dependency_scheduler_2026-07-27.json`](claire_talarian_filter_dependency_scheduler_2026-07-27.json)
  — five runs for 100, 1,000, and 5,000 frames;
- [`incremental_conjunctions_dependency_scheduler_2026-07-27.json`](incremental_conjunctions_dependency_scheduler_2026-07-27.json)
  — five cold and streamed runs for 25, 100, and 250 groups.

Application and search guards:

- [`claire_n_queens_dependency_scheduler_2026-07-27.json`](claire_n_queens_dependency_scheduler_2026-07-27.json)
  — three runs for N=8, 10, 12, and 14;
- [`rulebase_suite_dependency_scheduler_2026-07-27.json`](rulebase_suite_dependency_scheduler_2026-07-27.json)
  — seven runs for every documented rulebase and primary strategy;
- [`sudoku_rules_dependency_scheduler_2026-07-27.json`](sudoku_rules_dependency_scheduler_2026-07-27.json)
  — five runs for p1–p7 and each primary strategy;
- [`choice_search_dependency_scheduler_2026-07-27.json`](choice_search_dependency_scheduler_2026-07-27.json),
  [`choice_trail_dependency_scheduler_2026-07-27.json`](choice_trail_dependency_scheduler_2026-07-27.json),
  and
  [`choice_formulations_dependency_scheduler_2026-07-27.json`](choice_formulations_dependency_scheduler_2026-07-27.json);
- [`classical_csp_dependency_scheduler_2026-07-27.json`](classical_csp_dependency_scheduler_2026-07-27.json)
  — magic squares, Latin squares, and Sudoku p7;
- [`csp_harmonizer_next_dependency_scheduler_2026-07-27.json`](csp_harmonizer_next_dependency_scheduler_2026-07-27.json)
  and
  [`muses_harmonizer_dependency_scheduler_2026-07-27.json`](muses_harmonizer_dependency_scheduler_2026-07-27.json);
- [`fibonacci_explicit_dependency_scheduler_2026-07-27.json`](fibonacci_explicit_dependency_scheduler_2026-07-27.json)
  — seven runs for all four instantiation strategies.

Every payload records its exact commit and `snarky_dirty=false`. Each runner
also checks its logical outputs or stable search counters before emitting the
timings.

## Simple event-rule specialization — 2026-07-27

The direct A/B comparison uses commit `02ac84e`, Python 3.13.11, a clean
checkout, and five runs for 100, 1,000, and 5,000 Talarian frames:

- [`claire_talarian_filter_event_rules_2026-07-27.json`](claire_talarian_filter_event_rules_2026-07-27.json)
  — specialization enabled;
- [`claire_talarian_filter_event_rules_disabled_2026-07-27.json`](claire_talarian_filter_event_rules_disabled_2026-07-27.json)
  — identical Snarky workload through the generic semi-naïve path.

Both records retain identical firings, outputs, checksums, rule evaluations,
and skips. The specialization improves median inference time by ×1.49,
×1.46, and ×1.47 respectively.

## Bounded partial-join memory — 2026-07-27

[`incremental_conjunctions_partial_memory_2026-07-27.json`](incremental_conjunctions_partial_memory_2026-07-27.json)
uses commit `1d1dc5e`, Python 3.13.11, a clean checkout, and three runs per
case. It contains:

- the original cold and streamed conjunction guards at 25, 100, and 250
  groups, where the new memory deliberately remains inactive;
- a direct memory/generic A/B at 2, 5, 10, and 25 groups for a bound
  comparison that prevents the last fact premise from being reordered.

The A/B retains identical facts, firings, outputs, rule evaluations, and
skips. Median speedups are ×12.6, ×30.6, ×60.9, and ×132.9. At 25 groups,
match attempts fall from 2,881,600 to 6,598.

## Common CLAIRE triangle closure — 2026-07-27

The common three-premise workload is archived in:

- [`claire_triangle_closure_2026-07-27.json`](claire_triangle_closure_2026-07-27.json)
  — five clean runs of both Snarky and interpreted CLAIRE4;
- [`claire_triangle_closure_partial_memory_disabled_2026-07-27.json`](claire_triangle_closure_partial_memory_disabled_2026-07-27.json)
  — three clean Snarky runs through the generic semi-naïve path.

Every group prepares 16 membership relations, then streams 64 closing edges.
Both engines validate 64 rule firings and outputs per group plus the same hub
checksum. With partial memory, Snarky's median is 0.0081, 0.0214, 0.0467, and
0.1431 seconds for 2, 5, 10, and 25 groups. Interpreted CLAIRE4 takes 0.000345,
0.001059, 0.002920, and 0.013240 seconds, so the observed cross-engine gap
narrows from ×23.4 to ×10.8 as the combinatorial workload grows.

Disabling partial memory raises Snarky's corresponding medians to 0.1089,
0.6423, 2.5315, and 16.2327 seconds. At 25 groups, the optimization therefore
gives a ×113.5 internal gain and reduces match attempts from 2,881,600 to
6,598. The CLAIRE rule is a natural event-demon formulation that scans the
instantiated hubs; this is a language-level comparison, not a claim that both
runtimes use the same physical join strategy.

## Factorized multi-premise events — 2026-07-27

The engine implementation is commit `4b433e8`; every primary record below
uses Python 3.13.11 on macOS ARM64 with `snarky_dirty=false`:

- [`claire_triangle_closure_factorized_events_2026-07-27.json`](claire_triangle_closure_factorized_events_2026-07-27.json)
  — five runs of factorized Snarky and interpreted CLAIRE4 through 100 groups;
- [`claire_triangle_closure_partial_memory_2026-07-27.json`](claire_triangle_closure_partial_memory_2026-07-27.json)
  — three runs with only the previous bounded prefix memory;
- [`claire_triangle_closure_generic_2026-07-27.json`](claire_triangle_closure_generic_2026-07-27.json)
  — three runs with both specializations disabled;
- [`claire_triangle_closure_budget_cliff_2026-07-27.json`](claire_triangle_closure_budget_cliff_2026-07-27.json)
  — the one-run 33-group boundary where bounded memory falls back;
- [`incremental_conjunctions_factorized_events_2026-07-27.json`](incremental_conjunctions_factorized_events_2026-07-27.json)
  — cold/streamed guards plus the three-way factorized/memory/generic A/B.

The common-language result is:

| Groups | Snarky | Interpreted CLAIRE4 | Observed gap |
| ---: | ---: | ---: | ---: |
| 2 | 0.00750 s | 0.000343 s | ×21.9 |
| 5 | 0.01864 s | 0.001191 s | ×15.7 |
| 10 | 0.03782 s | 0.002892 s | ×13.1 |
| 25 | 0.09495 s | 0.013004 s | ×7.30 |
| 33 | 0.12486 s | 0.020969 s | ×5.95 |
| 50 | 0.19238 s | 0.044907 s | ×4.28 |
| 100 | 0.42016 s | 0.165307 s | ×2.54 |

Snarky performs exactly three matches and two indexed support lookups per
closing edge: 19,200 matches and 12,800 lookups for 6,400 outputs at 100
groups. Its factorized path is ×1.20–×1.31 faster than bounded prefix memory
through 25 groups and ×14.5–×166.3 faster than the generic join. The
asymptotic result is more important: at 33 groups bounded memory exceeds its
2,048-state budget and takes 27.5449 seconds, while factorized execution takes
0.12486 seconds, a ×220.6 difference.

The independent conjunction runner retains identical outputs, facts,
activations, evaluations, and skips. At 25 barrier groups its medians are
0.08727 seconds factorized, 0.11927 seconds with prefix memory, and 15.88971
seconds generic. Match attempts are respectively 4,800, 6,598, and 2,881,600.

[`rulebase_suite_factorized_events_2026-07-27.json`](rulebase_suite_factorized_events_2026-07-27.json)
uses follow-up commit `570f54d`, three clean runs, all 12 documented
rulebases, and the three primary strategies. Every application oracle passes;
the semi-naive four-queens scenario exercises two factorized event
evaluations, while focused MEA rules deliberately remain unspecialized.


Native Markov redesign scaling: [finite_markov_2026-09-16.json](finite_markov_2026-09-16.json)
contains six synthetic cases, seven samples per case, incumbent/proof evidence and
isolated Python-allocation measurements. Four runs hit the node limit; they are
retained explicitly. See the [performance document](../../docs/performance_baseline.md).

Unified redesign comparison:
[redesign_comparison_2026-09-16_corrected.json](redesign_comparison_2026-09-16_corrected.json)
contains 30 comparisons, three alternating paired sessions, seven samples per
side/session and 60 isolated allocation samples. Adjacent
[reference](redesign_comparison_2026-09-16_corrected.reference.tar.gz) and
[candidate](redesign_comparison_2026-09-16_corrected.candidate.tar.gz) source archives
preserve the measured code. The [report](../../docs/performance_comparison_2026-09-16.md)
records acceptance, incomplete proofs and the reproduced
[completion-cache memory tradeoff](redesign_memory_investigation_2026-09-16.json).
The earlier `redesign_comparison_2026-09-16.partial.json` is an interrupted harness
record, retained for provenance, not a completed comparison.

Established scheduling assessment:
[scheduling_standard_2026-09-29.json](scheduling_standard_2026-09-29.json)
records three fresh processes for each of 12 fixed PSPLIB J30 instances and
FT06/LA01–LA05, with a common ten-second search budget. It retains every timeout
and failure, all incumbent witnesses and source/data checksums. External inputs
are fetched to an ignored cache using the pinned manifest. See the
[assessment](../../docs/performance_scheduling_standard_2026-09-29.md).

The adjacent [source snapshot](scheduling_standard_2026-09-29_sources.tar.gz),
[separate profiles](scheduling_standard_2026-09-29_profiles.json),
[smoke result](scheduling_standard_2026-09-29_smoke.json) and
[validation log](scheduling_standard_2026-09-29_validation.txt) preserve the
measurement context. The source snapshot contains only first-party files.

Scheduling optimization comparison:
[scheduling_improvements_2026-09-29.json](scheduling_improvements_2026-09-29.json)
compares four variants on the same 18 cases, with three fresh processes per
case/variant. The ten-second budget includes constructive generation and search.
The [source snapshot](scheduling_improvements_2026-09-29_sources.tar.gz) preserves
the measured implementation. The
[report](../../docs/performance_scheduling_improvements_2026-09-29.md) separates
proofs, feasible schedules, timeouts and regressions. The adjacent pilot is
exploratory evidence and is excluded from the complete comparison's aggregates.
The [kernel ablations](scheduling_improvements_2026-09-29_ablations.json) retain
45 separate one-second diagnostic runs; their outcomes are not mixed with the
main ten-second assessment.
The [validation log](scheduling_improvements_2026-09-29_validation.txt) records
1,233 passed tests, six skips, witness replay and package checks.

Scheduling local improvement and order search:
[scheduling_next_2026-09-29.json](scheduling_next_2026-09-29.json) compares the
previous seeded method, local improvement with finite search, and a portfolio
that shares incumbents with an explicit order solver. The
[source snapshot](scheduling_next_2026-09-29_sources.tar.gz) preserves all measured
runtime and driver files. See the
[report](../../docs/performance_scheduling_order_2026-09-29.md) for scope, proof
semantics and separate diagnostics.
The [search diagnostics](scheduling_next_2026-09-29_search_diagnostics.json),
[six-second controls](scheduling_next_2026-09-29_diagnostic_control.json),
[model diagnostics](scheduling_next_2026-09-29_model_diagnostics.json) and
[60-second runs](scheduling_next_2026-09-29_extended.json) retain all supplemental
outcomes. They are excluded from the main three-repeat aggregates.
The [validation log](scheduling_next_2026-09-29_validation.txt) records 1,240
passed tests, six skips, independent witness replay and installed-package checks.

Scheduling proof search:
[scheduling_proofs_2026-09-29.json](scheduling_proofs_2026-09-29.json) compares
the archived `80abc15` order portfolio with clique resources and domain probing.
The [ablations](scheduling_proofs_2026-09-29_ablations.json) remove the window
phase, clique resources or root probes on the two formerly unproved cases.
The [source snapshot](scheduling_proofs_2026-09-29_sources.tar.gz) preserves the
measured runtime and drivers. The
[report](../../docs/performance_scheduling_proofs_2026-09-29.md) explains the
proofs, scope, timing boundaries and independent checks; the
[validation log](scheduling_proofs_2026-09-29_validation.txt) records 1,245
passed tests, six skips, package checks and 1,263 validated schedule records.
