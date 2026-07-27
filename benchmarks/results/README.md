# Archived benchmark results

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
