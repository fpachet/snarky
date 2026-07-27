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
