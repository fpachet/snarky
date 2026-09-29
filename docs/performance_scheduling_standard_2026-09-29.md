# Initial assessment on established scheduling benchmarks

**Snarky proved nine of 12 selected J30 projects and FT06 optimal within ten
seconds. Three J30 cases and LA01–LA05 found no feasible schedule within that
budget.** All outcomes repeated across three fresh processes per instance; every
reported witness passed independent validation. The main observed limitation on
unresolved cases is finding a first schedule.

## Scope and reproducibility

Baseline: `48abc8ad7ef7ac33a71cea4778c045519f01b775` (2026-09-29).
Only benchmark code, tests and documentation were added; no production solver
change or workforce symmetry constraint was used. The logistics_synth_pop POC
and its evidence were left unchanged.

The [protocol](../benchmarks/data/scheduling_standard/README.md) fixed the
selection before running Snarky: J30 groups 1, 5, 9, 14, 18, 22, 27, 31, 35, 40,
44 and 48, replicate 1 in every group; plus FT06 and LA01–LA05. The group indices
span the full 1–48 range with gaps of four or five. This avoids selecting by
observed solver outcome, but is neither a random sample nor complete factorial
coverage. Conclusions apply to this subset and formulation.

Each instance gets three sequential fresh Python processes and ten seconds of
search. Case order alternates forward/reverse between repetitions.
`PYTHONHASHSEED=0`, native backend, `policy="dom_wdeg"`,
`value_policy="objective"`, `bounding="auto"`, objective propagation and numeric
masks enabled; no warm start, symmetry or reference-objective constraint.
The worker uses a 70-second process watchdog, separate from the solver deadline.
Construction, import and whole-process times are separate fields. First feasible,
best-incumbent and proof times are measured from the solve call; the solver's
internal search time excludes native-state initialization. Validation callbacks
run inside the search budget and their time is recorded separately. Timeouts
retain bounds and incumbents rather than being omitted from summaries. A timeout
bound is the root relaxation bound, not a continuously updated bound over the
remaining frontier. Absolute gap is `incumbent - bound`; relative gap divides
that by `max(1, abs(incumbent))`. Without an incumbent, both gaps are null.
Reference gap separately divides `incumbent - published optimum` by the published
optimum. These two gaps must not be confused.

Run from a source checkout with Snarky and development dependencies installed:

```sh
python -m benchmarks.scheduling_standard --fetch
python -m benchmarks.scheduling_standard --repeat 3 --seconds 10 \
  --output generated/scheduling_standard_new.json
pytest tests/test_scheduling_standard.py
```

The [raw archive](../benchmarks/results/scheduling_standard_2026-09-29.json)
contains settings, interpreter/platform, Git revision, every Python runtime source
hash, measured harness hashes, input manifest, every repetition and every
incumbent start vector. A [first-party source snapshot](../benchmarks/results/scheduling_standard_2026-09-29_sources.tar.gz)
preserves every file named in the source hashes; it contains no external dataset.
File order is the original PSPLIB activity order or
job-major/operation-major order for job shop. New output paths are required.
A separate [one-second J30 smoke test](../benchmarks/results/scheduling_standard_2026-09-29_smoke.json)
preceded the repetitions and is excluded from aggregates. Development import
errors were corrected before that test; no production solver fix was needed.
No timing threshold is a CI assertion. To revalidate all stored start vectors:

```sh
python -m benchmarks.scheduling_verify \
  benchmarks/results/scheduling_standard_2026-09-29.json
```

## Sources, objective references and rights

Downloads were verified on 2026-09-29. The
[manifest](../benchmarks/data/scheduling_standard/manifest.json) pins SHA-256 hashes
for the complete J30 ZIP, individual selected members, optimum table and complete
OR-Library file. No archive extraction writes arbitrary upstream paths.

- [PSPLIB single-mode data](https://www.om-db.wi.tum.de/psplib/getdata.php?mode=sm)
  labels all 480 J30 objectives proven optimal. We use its OPT table, credited to
  E. Demeulemeester and W. Herroelen (June 1995), not HRS best-known values.
  [PSPLIB's notice](https://www.om-db.wi.tum.de/psplib/library.php) permits evaluation
  and downloading. Redistribution permission was not established, so inputs and
  reference tables remain in an ignored cache.
- [OR-Library job-shop information](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/jobshopinfo.html)
  identifies the [instance file](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/jobshop1.txt).
  It credits Fisher/Thompson and Lawrence for these families. Its
  [legal notice](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/legal.html) applies
  MIT; this assessment still caches the inputs rather than bundling them.
- Job-shop references are FT06=55, LA01=666, LA02=655, LA03=597, LA04=590,
  LA05=593. [Piroozfard, Wong and Hassan (2016), Table 2](https://doi.org/10.1155/2016/7319036)
  lists these values and marks them as optimal in its footnote. The table's
  general BKS label alone would not establish optimality; the explicit optimal
  labels support the classification here. This assessment does not reproduce
  historical proof certificates.

Reference lookup and comparison occur after each worker returns. Reference
metadata never enters lower bounds, cutoffs, domain endpoints or initial assignments.
See [THIRD_PARTY.md](../THIRD_PARTY.md#established-scheduling-benchmark-data).

## Equivalent models and sound bounds

Both formulations use nonnegative integer starts and unbroken half-open intervals
`[s, s+d)`. No calendar, setup, staffing or interchangeability assumptions are
added. Original durations, machines, demands and arcs are retained.

**RCPSP.** Every activity, including both zero-duration dummies, has an ordinary
start variable. Source start is fixed to zero. The sink start is the ordinary
makespan variable. Only positive-duration real activities become `Task` objects.
Every original arc is posted: real-to-real arcs use `Precedence`; arcs involving
a dummy use the equivalent linear inequality `s_i + d_i <= s_j`. Zero-demand,
zero-duration dummies need no capacity interval. Each renewable pool uses
weighted `Capacity`, omitting only activities with zero demand on that pool.
Import requires one zero-release project, only renewable resources, one mode,
zero-duration/zero-demand source and sink, positive real durations and a DAG in
which every activity lies on a source-to-sink path. Unsupported variants fail
explicitly. PSPLIB due-date/tardiness metadata is not a deadline in RCPSP
makespan minimization.

**Job shop.** Each operation is a `Task` with its original fixed machine and
positive duration. Consecutive operations in each job use `Precedence`. Every
pair on the same machine uses `NoOverlap` with zero gap. There is no resource
choice variable: fixed machine membership determines which pairs constrain each
other. The importer checks exactly one visit per machine per job, as in the
selected OR-Library instances.

**Objective.** A linear inequality requires every real task end to be at most
makespan. Minimizing this ordinary variable is equivalent to minimizing maximum
completion: any feasible assignment can lower makespan to its latest end without
violating a constraint. The sink has no outgoing arcs. The epigraph can represent
slack makespan values during general enumeration; those cannot improve an
optimum. Reported witnesses are checked for exact equality to maximum real
completion, as well as all original scheduling constraints.

**Domains.** Let `H` be the sum of positive durations. Executing all tasks
serially in topological order is feasible because every individual demand fits
capacity, so at least one optimum lies within `H`. The input J30 horizon is
checked to be at least this bound. Longest-path predecessor durations give each
start's lower bound; longest-path successor durations give
`start <= H - duration - tail`. A lower bound for makespan is the maximum of the
precedence critical path and each `ceil(sum(duration*demand)/capacity)` (RCPSP),
or total duration on each machine (job shop). These calculations use inputs only.
They preserve an optimum, though they deliberately omit schedules that finish
later than the known serial feasible bound.

**Independent validation.** RCPSP validation reads the original arcs and computes
resource usage independently at every integer time slot. Job-shop validation
checks original job order and pairwise machine intervals. Neither calls Snarky
constraints, propagation or feasibility helpers. Every emitted incumbent is
validated and retained; invalid schedules fail visibly. Small exhaustive tests
also compare the formulation and native enumeration to these validators.

## Results

**10 of 18 instances were proved optimal in every repetition:** nine J30 cases
and FT06. The remaining three J30 cases and all five LA cases reached the search
time limit **without a feasible incumbent** in every repetition. There were no
invalid witnesses, process failures, watchdog terminations or contradictions with
published optima. All 30 emitted witnesses passed independent validation, including
a separate replay after the benchmark. All 54 runs are retained.

The host ran Python 3.13.11 (Anaconda/Clang 20.1.8), macOS 15.7.7 on ARM64,
with 10 logical CPUs. Workers ran sequentially; diagnostics and regression tests
ran after the timed experiment. This is a single-host assessment, not a comparison
with another solver or historical hardware. Total subprocess wall time was
260.2 seconds.

Construction, first feasible, proof and revisions are medians of three runs.
Solve-call time and entered nodes are min–max ranges. A dash means no incumbent
or proof, not a zero value. Solved rows have zero solver and reference gap;
unresolved rows have undefined gaps because no upper bound was found by search.
Published values and root bounds are listed separately to expose that distinction.

| Instance | Published optimum | Best | Final bound | Build ms | First feasible s | Proof s | Solve-call s range | Nodes range | Revisions median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| j301_1 | 43 | 43 | 43 | 2.51 | 0.127 | 0.130 | 0.130–0.131 | 237–237 | 3,248 |
| j305_1 | 53 | — | 41 | 2.52 | — | — | 10.001–10.001 | 2687–2697 | 91,625 |
| j309_1 | 83 | — | 58 | 2.46 | — | — | 10.001–10.001 | 639–645 | 28,821 |
| j3014_1 | 50 | — | 43 | 2.17 | — | — | 10.001–10.001 | 1131–1139 | 31,374 |
| j3018_1 | 53 | 53 | 53 | 2.47 | 0.112 | 0.115 | 0.115–0.116 | 285–285 | 3,570 |
| j3022_1 | 42 | 42 | 42 | 2.33 | 0.734 | 0.737 | 0.736–0.738 | 543–543 | 12,541 |
| j3027_1 | 43 | 43 | 43 | 2.29 | 0.318 | 0.319 | 0.318–0.325 | 62–62 | 1,518 |
| j3031_1 | 43 | 43 | 43 | 2.30 | 0.438 | 0.439 | 0.438–0.439 | 17–17 | 721 |
| j3035_1 | 57 | 57 | 57 | 2.60 | 0.039 | 0.040 | 0.040–0.040 | 25–25 | 756 |
| j3040_1 | 51 | 51 | 51 | 2.77 | 0.131 | 0.132 | 0.131–0.132 | 20–20 | 834 |
| j3044_1 | 50 | 50 | 50 | 2.29 | 0.248 | 0.248 | 0.248–0.250 | 21–21 | 738 |
| j3048_1 | 63 | 63 | 63 | 2.04 | 0.647 | 0.648 | 0.647–0.652 | 20–20 | 799 |
| ft06 | 55 | 55 | 55 | 4.56 | 0.951 | 0.955 | 0.952–0.955 | 1175–1175 | 82,403 |
| la01 | 666 | — | 666 | 77.96 | — | — | 10.021–10.022 | 374–375 | 88,119 |
| la02 | 655 | — | 635 | 72.74 | — | — | 10.019–10.020 | 181–182 | 66,880 |
| la03 | 597 | — | 588 | 65.59 | — | — | 10.017–10.017 | 279–280 | 67,001 |
| la04 | 590 | — | 537 | 69.23 | — | — | 10.018–10.019 | 564–586 | 85,316 |
| la05 | 593 | — | 593 | 64.92 | — | — | 10.016–10.017 | 1507–1560 | 131,540 |

### Reproducibility and limits

All completed searches had identical node and revision counts across repeats,
and every case had identical status, objective and final bound. Runtime variation
was small on this host; timed-out node counts varied because wall-clock stopping
can interrupt different propagation work. Solver deadlines are cooperative:
whole solve-call time includes initialization and can slightly exceed ten seconds.
None reached the external watchdog.

Each completed search emitted one incumbent, already at the published optimum;
proof followed within a few milliseconds. On the eight unresolved cases, the
initial feasible-schedule search itself stalled. Describing these only as slow
optimality proofs would hide the principal limitation of this configuration.

LA01 and LA05 already have input-derived bounds of 666 and 593, equal to the
published optima. Stronger numeric makespan bounds alone therefore cannot explain
or fix their lack of an incumbent. The other unresolved bounds remain below the
reference objectives: J30 5/1 41 vs 53, 9/1 58 vs 83, 14/1 43 vs 50; LA02
635 vs 655, LA03 588 vs 597 and LA04 537 vs 590.

The selection spans groups but does not estimate whole-library success rates.
Three repetitions test process-level consistency on one host; they are not enough
for statistical claims about machines, solver strategies or broader scheduling
families. The ten-second results do not establish how long unresolved cases need.
A longer-budget study must retain this baseline and use a declared protocol.


## Separate diagnostic profiles

After timing and regression tests, one ten-second cProfile run each examined
J30 9/1 and LA01. These cases were chosen to diagnose failures, not to revise the
fixed sample. The [profile archive](../benchmarks/results/scheduling_standard_2026-09-29_profiles.json)
contains the profiling harness source, measured source hashes, counters and top
35 cumulative-time entries. They are excluded from latency aggregates; the two
profiled calls share a process and profiling substantially reduces node throughput.

- J30 9/1 spent 9.71 seconds inside `revise_capacity`, including 9.14 seconds
  inside its per-candidate `possible` checks. Only 149 nodes were entered under
  profiling, versus 639–645 in the unprofiled runs. This identifies capacity
  candidate scanning as the immediate runtime cost in this case.
- LA01 spent 8.11 seconds inside generic `_revise_linear_sum` during a roughly
  ten-second search, including 8.28 million integer-candidate calls. It entered
  42 nodes under profiling versus 374–375 unprofiled. The pairwise disjunction
  path revises its linear alternatives without compiled numeric filtering.

These measurements support investigating repeated fixed-load reconstruction and
numeric filtering inside disjunctions before broad solver optimization. They do
not establish the speedup or search reduction of a proposed replacement.

## Improvements justified for a follow-up

1. **Separate finding a schedule from proving it.** Add a declared, input-only
   constructive list-scheduling baseline and measure both its own cost and a
   separate seeded Snarky variant. Preserve these cold-search results. The eight
   failures here have no incumbent, and two already have an optimal lower bound.
2. **Reduce start-domain width using a validated feasible horizon.** The serial
   horizons are 2,283–2,849 for the LA cases, versus reference optima 590–666.
   A schedule computed from the input can give a sound smaller upper bound;
   published optima must remain evaluation-only. This is a formulation ablation
   to measure, not evidence that the present solver would then succeed.
3. **Evaluate scheduling-specific propagation and decisions.** The present
   capacity filter uses fixed intervals rather than mandatory-part timetables;
   job-shop resources use pairwise disjunctions. Mandatory-part propagation,
   resource ordering decisions and stronger disjunctive propagation are plausible
   next experiments. Their correctness needs independent small-case oracles,
   including half-open endpoints and rollback, before performance claims.
4. **Improve proof reporting when longer runs find incumbents.** A remaining-frontier
   bound would distinguish progress beyond the root relaxation. Longer common
   budgets can then show whether proofs or feasible-schedule construction dominate.

These are proposed experiments, not implemented optimizations. This assessment
makes no claim about certified workforce interchangeability transferring to these
instances. Nurse rostering and broader MiniZinc families remain follow-ups.

## Validation

The full configured **redesign gate passed 1,224 tests, with 6 skipped**, in
192.17 seconds, including the existing scheduling, symmetry, objective,
objective-propagation, factor-bound, search-progress and application suites.
This includes **49 new tests** for the scheduling assessment. See the
[validation log](../benchmarks/results/scheduling_standard_2026-09-29_validation.txt).

The new tests use first-party tiny instances and exhaustive start assignments,
compare full feasible sets and optimal values, exercise weighted capacity on
multiple resources and non-numeric topological order, check touching endpoints,
and reject malformed dimensions, modes, cycles, disconnected dummies, unsupported
resource/release variants, bad durations/demands/machines and corrupt cache bytes.
No upstream data or network access is needed for these tests.

Ruff passed; strict mypy passed on 101 source files; all 305 textual models passed
syntax/format validation; first-party Markdown links passed. Source and wheel
builds, distribution-content checks and isolated wheel inference/CLI checks
passed. Both original upstream datasets were reproduced by the fetch command in
a fresh ignored cache. Every file in the source snapshot matches its recorded
hash. Production solver files and prior workforce input/evidence have no Git diff.
No solver correctness fix or optimization was introduced.
