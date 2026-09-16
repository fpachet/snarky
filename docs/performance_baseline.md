# Redesign performance baseline and comparison ledger

This is the performance companion to the [redesign plan](redesign_plan.md).
It defines fixed non-Bach workloads, reproducible measurements, and the evidence
required to accept future optimizations. Bach data, learning, and generation
experiments are outside this portfolio.

Correctness remains a separate prerequisite. Fast incorrect output is not an
optimization. This document tracks both implementation overhead and practical
solver performance without conflating them.

## Reference identity

The first baseline is the existing runtime at commit
`2fbdd9d0e70ad5dc45fbf4dc5472510f84365f5c`, before the redesign.
The measurement checkout contains uncommitted documentation and the new
collector; the JSON explicitly records a dirty working tree. Runtime and
workload sources have not been changed for this measurement.

The [collector](../benchmarks/redesign_baseline.py) records the commit, working
tree status, hash of tracked runtime/workload sources, its own source hash,
Python/platform information, hash seed, collection timestamps, and every timing
sample. The aggregate source hash excludes archived benchmark results; it covers
tracked files under the roots declared in the collector. It does not replace
inspection of untracked code or the working-tree diff.

Preserve this commit as the reference. For a future comparison, rerun the
reference and candidate under the same environment using the same collector
and workload definitions. Old absolute timings are a historical record, not a
substitute for a contemporaneous comparison.

## Fixed portfolio: `redesign_baseline_v1`

| Family | Fixed cases | What they exercise |
|---|---|---|
| Rules | Triangle closure, five-disk Hanoi, NEOPUS monkey-and-bananas; indexed and semi-naive matchers | Joins, recursive derivation, ordered actions, goal state and conflict handling |
| Incremental rules | Three-premise joins, 25 and 100 groups, width 8; cold and streamed modes | Initial saturation versus repeated fact insertion and closure; 1,600 and 6,400 expected outputs |
| Pure CSP | Magic squares of orders 3, 4, 5; reduced Latin squares of orders 5, 7 | Global all-different and sum propagation, choice construction, rollback and search |
| Pure/mixed pair | Sudoku p7 with constraints alone and with the existing complete technique sequence | Same solution oracle with distinct execution strategies; coordination cost and search reduction |

There are 17 measured cases. All inputs are tracked or deterministically
constructed. The CSP cases retain the current default heuristics, no magic-square
symmetry breaking, and no optional propagation probes. Record the exact source
and settings: changing a default is a search-policy change, even if the command
line stays the same.

Do not change these cases in place. New sizes or workloads form an additional
versioned portfolio; retain the original cases to detect regressions.

## Timing boundaries and validation

| Family | Included in measured time | Excluded | Current validation |
|---|---|---|---|
| Rulebase scenarios | Loading/parsing scenario data, engine/session creation, execution and result construction, loading expected facts | Python startup/imports; final missing-fact assertion | Expected facts are present; recorded fact/activation/work counters are stable across repetitions |
| Cold joins | One `run_group` closure, without result materialization | Fact construction, session creation, full-output validation | Exact expected output set, memory size, valid mutation events and stable counters |
| Streamed joins | Each insertion, closure, event retrieval/checking and output counting | Initial membership construction/saturation; final full-output validation | Exact expected output set, memory size, valid mutation events and stable counters |
| Classical CSP/Sudoku | Public solve operation, including its preparation, search, result extraction and existing validation | Python startup/imports; the classical runner's separate fact-count model construction | Solved status, stable nodes/failures; square invariants and exact Sudoku solution |

These are deliberately labeled different timing scopes. Do not compare their
absolute rates as if they measured the same operation. The Sudoku pair is a
practical formulation comparison, not a measurement of bridge overhead alone:
its search trees may differ.

The existing rulebase validator checks required facts, not complete absence of
spurious conclusions. The classical magic-square benchmark checks value coverage,
rows and columns but not diagonals independently. The redesign conformance phase
must strengthen those oracles and record any resulting harness change. These
timings do not replace the independent semantic tests.

## Collection protocol

Run from the repository root, with the existing development environment:

```sh
PYTHONHASHSEED=0 .venv/bin/python -m benchmarks.redesign_baseline \
  --repeat 7 \
  --output benchmarks/results/redesign_baseline_YYYY-MM-DD_LABEL.json
```

Replace the filename with a new date and label. The collector refuses to
overwrite an existing record. It executes cases sequentially, runs one discarded
warmup, then retains seven samples and their median/minimum/maximum. Each sample
uses fresh model/session state through the existing runner. Python caches may
remain warm; garbage collection stays enabled. Python process startup is not
timed. No statistical confidence interval is inferred from these seven samples.

Use the same Python/dependencies, machine, power settings, hash seed and workload
inputs when comparing implementations. Avoid other heavy work while measuring.
Record CPU model, RAM, power mode and unusual background activity where available;
these are not all detected automatically. Run benchmarks sequentially, not in
parallel with each other or a test suite. Correctness tests run first.

The initial record has no peak-memory or separate preparation/solve measurements.
Those fields are unavailable, not zero. The collector does not establish a quiet
machine, sustained thermal state, or an isolated process environment.

## How to compare a change

1. Pass the relevant conformance tests and inspect output equivalence.
2. Identify the change as a kernel/runtime change, a search-policy change, or a
   model/formulation change. State which behavior is expected to remain equal.
3. Use identical harnesses and fixtures for both implementations. Run baseline
   and candidate sequentially in alternating order across at least three paired
   sessions, each with one warmup and seven measured repetitions.
4. Retain all raw records. For each case report baseline and candidate medians,
   ranges, work counters, and numerical/result equivalence. Report
   `speedup = baseline_seconds / candidate_seconds` and
   `time_change_percent = 100 * (candidate_seconds / baseline_seconds - 1)`.
5. Report regressions individually. Do not hide one behind a portfolio average or
   a faster unrelated workload. If repetitions are unstable, investigate and
   recollect before interpreting a ratio.
6. Append a ledger entry linking the change, raw evidence, validation, and decision.

A runtime-speed claim requires equivalent work at the relevant semantic level.
For fixed-search CSP comparisons, hold policy, seed, symmetry, solution target,
and limits constant and verify nodes/failures and solution behavior. Lower-level
work counters may improve. If the search tree changes, report it as a solver
improvement with nodes and failures beside time, not as a pure kernel speedup.

For new backends, compare projected solutions and objectives rather than private
event layouts. Existing operational APIs still owe their documented ordering and
explanation behavior. Never trade those away invisibly to improve a benchmark.

## Initial investigation thresholds

These thresholds are predeclared review triggers, not claims of statistical
significance or automatic CI failures:

- Investigate a per-case median slowdown exceeding both **15% and 2 ms**, reproduced
  in at least two of three paired sessions.
- Treat changed required outputs, false proof statuses, leaked branch state, or
  invalid bounds as correctness failures regardless of speed.
- Once per-case isolated memory measurements exist, investigate a reproduced
  peak-memory increase exceeding both **15% and 1 MiB**. Peak process RSS and
  Python allocation peaks must be labeled separately.
- Smaller changes may matter at scale. For sub-2-ms operations add a versioned
  batch/throughput case rather than claiming a microsecond win from noisy samples.

Do not silently waive a regression because another case improved. Record its
cause and an explicit decision, or fix it before promoting the replacement.
Threshold changes apply prospectively and are logged with a reason.

## Reusable optimization report

For each proposed optimization, append a ledger row and link a report using the
following fields. Use `not measured` for unavailable data, rather than leaving
an ambiguous empty cell.

- **Change:** implementation change and intended bottleneck; classify it as
  runtime/kernel, search policy, or formulation.
- **Identity:** reference and candidate commits, source hashes and working-tree
  diffs, collector hash, portfolio version, environment and exact commands.
- **Correctness:** conformance command/results and the facts, solution sets,
  scores, bounds and proof statuses compared.
- **Measurements:** all paired raw records, timing scope, repetition count,
  search settings and resource limits; link any separately instrumented profile.
- **Decision:** accept, investigate, or reject, with any regression and its cause.

| Case / paired session | Reference median [min–max] ms | Candidate median [min–max] ms | Speedup | Time change % | Work counters before → after | Result / proof agreement |
|---|---:|---:|---:|---:|---|---|
| Case identifier / session number | not measured | not measured | not measured | not measured | not measured | not checked |

For optimization workloads, add first-incumbent time, final incumbent, valid
global bound, time to proof and termination reason. State whether scores use
exact arithmetic or an approximation. For a minimization query, an absolute
gap is incumbent minus lower bound; for maximization it is upper bound minus
incumbent. A gap is unavailable if either endpoint is unavailable. For memory,
report preparation and search measurements separately when available, including
the measurement method and units.

## Coverage to add during redesign

| Milestone | Additional fixed workloads | Required metrics |
|---|---|---|
| Baseline/conformance | Car sequencing, curriculum, balanced coloring; infeasible and full-enumeration CSPs; mutations and nested rollback | Complete outputs/solution counts, nodes, failures, revisions, candidate removals, elapsed time |
| Domain extraction | Identical CSPs through legacy candidate facts and native domains; fixed-search workloads | Preparation and search separately, domain operations, fact/event materialization, isolated peak memory |
| Mixed runtime | Non-musical scheduling/allocation; rules derive properties that trigger further restrictions | Closure rounds, rule activations, propagator revisions, rollback work; full output/score equality |
| Optimization | Known-optimum Golomb/allocation instances; satisfiable, infeasible, tied and interrupted cases | Time to first incumbent, incumbent trajectory, time to proof, valid global bound, gap and termination reason |
| Markov optimization | Synthetic fixed-seed models scaled by length, alphabet, order, table density and cost range | Table/support work, objective value, nodes, first incumbent/proof times, memory; enumeration oracle on small cases |
| Factors | Synthetic duplicate-witness and many-grounding models; factors activated by derived properties | Activation/score equality, evaluator time, support allocation and cache invalidation |
| Backend integration | The same small regular models through generic inference and BP | Preparation and query time separately, partition and marginal agreement, conditional-mass agreement, model size |

These rows are planned measurements, not existing baseline results. The six-model
temporary Markov probe is a correctness demonstration and is too small to support
scalability claims. Larger time-limited cases must retain their timeout and best
known result rather than disappearing from the report. Never compute a completed
proof speedup against a run that only found an incumbent.

Use separate instrumented runs for profiling and allocation tracing, since they
alter timing. Preserve explainability settings in the result metadata. Reuse the
[existing benchmark catalogue](../benchmarks/README.md) instead of duplicating
workloads unnecessarily.

## Measured baseline and ledger

Initial raw record:
[redesign_baseline_2026-09-16.json](../benchmarks/results/redesign_baseline_2026-09-16.json).
This is a first local reference, not a paired optimization comparison.

Recorded on Python 3.13.11, macOS 15.7.7 ARM64, 10 logical CPUs,
PyYAML 6.0.3, `PYTHONHASHSEED=0`; seven samples after one warmup.
CPU model, RAM and power mode were not captured. Times below are milliseconds.

| Case | Median ms | Min–max ms | Work |
|---|---:|---:|---|
| `rules/small/triangle_closure/indexed` | 1.355 | 1.223–1.627 | 2 activations |
| `rules/small/triangle_closure/semi-naive` | 1.249 | 1.198–1.776 | 2 activations |
| `rules/thesis/hanoi/indexed` | 39.802 | 38.813–40.614 | 61 activations |
| `rules/thesis/hanoi/semi-naive` | 41.592 | 40.971–41.943 | 61 activations |
| `rules/thesis/monkey_bananas/neopus_mea/indexed` | 22.475 | 21.382–24.022 | 12 activations |
| `rules/thesis/monkey_bananas/neopus_mea/semi-naive` | 21.313 | 20.892–22.332 | 12 activations |
| `joins/25x8/cold` | 36.905 | 35.283–38.290 | 1,600 outputs |
| `joins/25x8/streamed` | 110.306 | 109.198–134.417 | 1,600 outputs |
| `joins/100x8/cold` | 186.926 | 145.570–194.993 | 6,400 outputs |
| `joins/100x8/streamed` | 458.701 | 450.297–512.739 | 6,400 outputs |
| `magic_square_3` | 11.541 | 11.094–12.038 | 9 nodes / 5 failures |
| `magic_square_4` | 331.252 | 326.554–342.728 | 175 nodes / 134 failures |
| `magic_square_5` | 77.630 | 75.457–91.573 | 14 nodes / 2 failures |
| `latin_square_5` | 9.113 | 8.862–9.271 | 4 nodes / 0 failures |
| `latin_square_7` | 46.292 | 44.623–58.912 | 15 nodes / 0 failures |
| `sudoku_p7_constraints_only` | 89.097 | 87.152–107.929 | 2 nodes / 0 failures |
| `sudoku_p7_constraints_and_rules` | 457.578 | 445.937–465.416 | 1 nodes / 0 failures |

Some cases show noticeable timing spread, particularly the 100-group cold join.
Retain that uncertainty: this first collection establishes a reference and does
not justify claims about small performance differences.

| Date / change | Reference and candidate | Validation / raw records | Decision |
|---|---|---|---|
| 2026-09-16: initial collection | Runtime `2fbdd9d`; no runtime candidate | [17-case raw record](../benchmarks/results/redesign_baseline_2026-09-16.json); existing per-case validators | Establish local baseline; strengthen oracles and add missing metrics before redesign promotion |

Append one row per assessed optimization. Include unsuccessful changes and
regressions when they informed the architecture. Keep raw records immutable.

Historical July and September measurements remain available through the
[results index](../benchmarks/results/README.md). They have different commits,
harnesses or environments and are context, not a direct speedup denominator.


## Native Markov scaling record

The additional portfolio `finite_markov_v1` is defined in
[`benchmarks/finite_markov.py`](../benchmarks/finite_markov.py). It varies length,
alphabet, order, transition density and integer cost range, with all-different on
an initial block and return-to-start equality. This is synthetic scaling evidence;
it does not replace a realistic application benchmark or a paired comparison.

```sh
PYTHONHASHSEED=0 .venv/bin/python -m benchmarks.finite_markov \
  --repeat 7 --output benchmarks/results/finite_markov_YYYY-MM-DD_LABEL.json
```

The [initial record](../benchmarks/results/finite_markov_2026-09-16.json) retains
42 timing samples and six separate subprocess memory runs. Timings exclude
validation; preparation includes source/model construction and state compilation.
Search includes propagation, scoring, result construction and rollback. Memory is
`tracemalloc`'s Python-allocation peak, **not RSS**; the search peak includes live
preparation allocations. Instrumented runtimes are not used as timing samples.
The source hash includes untracked runtime sources, which matter during redesign.

| Case | Prepare median ms | Search median ms | Nodes | Incumbent / bound | Termination | Search peak KiB |
|---|---:|---:|---:|---:|---|---:|
| `short_dense` | 0.30 | 12.38 | 133 | 8 / 8 | exhausted | 211.0 |
| `medium_sparse` | 0.44 | 123.68 | 1000 | 46 / 2 | node_limit | 148.4 |
| `long_sparse` | 0.77 | 220.64 | 1000 | 126 / 2 | node_limit | 267.5 |
| `wide_sparse` | 1.22 | 363.15 | 1000 | 20 / 2 | node_limit | 311.0 |
| `second_order` | 1.45 | 394.25 | 1000 | 27 / 1 | node_limit | 183.1 |
| `large_costs` | 0.41 | 40.45 | 308 | 359835 / 359835 | exhausted | 196.2 |

Only `short_dense` and `large_costs` prove an optimum in this record. The other
four stop at the declared 1,000-node limit. The archive retains first-incumbent
and proof times separately, all improvements, search counters, and an independently
computed chain-relaxation optimum. The wide remaining gaps show that independent
local table bounds are often weak; future chain-relaxation bounds should be
compared on these same cases. Cost-range cases also change individual costs and
thus their search trees; their relative timings are not kernel speedups.

## Paired redesign portfolio: `redesign_promotion_v1`

The additional collector is [`redesign_comparison.py`](../benchmarks/redesign_comparison.py).
It freezes reference and candidate runtime/workload sources into adjacent tarballs,
including untracked implementation files, hashes them, and checks that neither
source tree changes during collection. The same worker runs against both roots.
It retains all per-run observations, three alternating paired sessions with seven
samples each, and separate subprocess allocation measurements.

This version contains 30 comparisons:

- Six rulebase/matcher pairs and four cold/streamed joins from the original sizes.
- Three compatibility workloads through the unchanged public solver: magic5 and
  Sudoku p7 with/without techniques. These retain their original solver defaults.
- Four native-versus-legacy CSP pairs: magic3, magic4, latin5, latin7. They use
  matched MRV and lexical variable/value order, and require identical assignments,
  nodes and failures. Fixture creation/adaptation is excluded; state preparation
  and search are separate. These settings differ from the initial CSP baseline.
- Native magic3 with and without a positive reporting rule. This deliberately
  measures additional inference work on the same CSP/search tree.
- Three dense dyadic Markov ring models of length/alphabet 25/4, 33/8 and 129/8.
  They enforce a distinct initial block and equal endpoints. A preferred cycle
  attains the independently known minimum edge-cost sum. Native optimization uses
  completion bounds and objective-guided values; legacy optimization repeats
  feasibility with stricter cost cuts. This is a solver/formulation comparison.
- Nine native bound comparisons: the six unchanged `finite_markov_v1` models plus
  a 64-symbol, eight-state, second-order sparse model; a 64-symbol tied-cost model;
  and a provably infeasible distinct-prefix model. Both sides use dom/wdeg and
  declared value order, with local versus automatic completion bounds.

Ring queries have a 5,000-node budget; scaling queries have 1,000. All Markov
comparisons additionally have a three-second search budget, declared after the
long legacy preflight exposed expensive reachable-sum filtering. Legacy search
has no cooperative timer: the POSIX harness interrupts an unfinished feasibility
call and retains the last completed incumbent. Its interrupted node/failure
counters exclude the unfinished call and are explicitly labeled incomplete.
Its reported lower bound comes from the analytic test model, not a legacy API.
Native deadlines are cooperative. No proof-speed ratio is reported when either
side fails to complete the proof in any retained sample.

Preparation includes parsing/session construction for rulebases; join fixtures
are prebuilt and preparation creates their session (plus initial streamed closure).
Join execution excludes result fingerprinting and final oracle checks. This
split timing differs from the initial join collector's event-reading scope.
Compatibility workloads expose only public solve, so their preparation is within
execution. Allocation peaks use `tracemalloc`, not RSS; search includes live
preparation allocations but excludes prebuilt immutable fixtures. Instrumented
runs have the same limits and may complete less work, so memory comparisons must
also inspect their recorded outcome. No machine isolation or thermal control is
claimed; CPU model/RAM were unavailable to this sandboxed collector.

Run after correctness checks, without concurrent benchmarks or tests:

```sh
PYTHONHASHSEED=0 .venv/bin/python benchmarks/redesign_comparison.py \
  --reference /tmp/snarky-redesign-reference-2fbdd9d \
  --repeat 7 --pairs 3 \
  --output benchmarks/results/redesign_comparison_DATE_LABEL.json
.venv/bin/python -m benchmarks.report_redesign \
  benchmarks/results/redesign_comparison_DATE_LABEL.json \
  --output docs/performance_comparison_DATE_LABEL.md
```

Recreate the original reference directory with `git archive` at the reference
commit, or extract the preserved reference tarball. For exact candidate
reproduction, extract its tarball into a separate directory and use the same
Python environment and archived collector. Partial JSON checkpoints are recovery
artifacts; only a record with `finished_at` and successful final source-hash checks
is a completed comparison. Retain interrupted cases and unsuccessful preflights.

The diagnostic 25/4 preflight initially found native local bounds inadequate:
5,000 nodes retained cost 34 while repeated feasibility proved cost 26 in 1,009
nodes. That prompted the bounded-window min/max completion bound and explicit
objective value ordering, verified against exhaustive residual optima. This is
why both the useful structured cases and the harder random cases remain in the
new portfolio. The redesign does not promise polynomial search or uniformly
faster optimization across all models.

The first paired collection stopped at the mixed fixture because unused legacy
bookkeeping contained nested context terms outside the admitted positive-rule
fragment. Its [partial record](../benchmarks/results/redesign_comparison_2026-09-16.partial.json)
and source archives are retained, but it is not a completed promotion record.
The corrected fixture removes this unused context from **both** native sides and
checks identical assignments, nodes and failures. The corrected collection uses
a new filename and recollects all cases under one preserved collector snapshot.

## Completed redesign comparison and decision

The [comparison report](performance_comparison_2026-09-16.md) contains the final
30-case assessment and detailed per-session tables. The
[completed raw record](../benchmarks/results/redesign_comparison_2026-09-16_corrected.json)
retains 1,260 timing samples and 60 separate allocation samples. Reference and
candidate sources are preserved in adjacent tarballs; a separate
[memory investigation](../benchmarks/results/redesign_memory_investigation_2026-09-16.json)
retains two additional isolated pairs and compiled-cache counts.

| Date / change | Reference and candidate | Validation / evidence | Decision |
|---|---|---|---|
| 2026-09-16: native finite runtime, shared kernels and completion bounds | `2fbdd9d` versus archived candidate; local versus auto bound ablation on the same candidate | [825-test gate](../tests/fixtures/redesign_final_validation.json), [paired report](performance_comparison_2026-09-16.md), source archives and raw samples | Accept additive runtime: rule budgets preserved, fixed-search CSP 2.01–3.08× faster, useful proved Markov optimization; explicitly accept the reproduced bounded-cache memory tradeoff on the large second-order case |

This is the reference for subsequent optimizations. Do not replace its timed-out
or node-limited outcomes with only successful runs. Further cache compression,
cheaper value ranking, stronger relaxations, propagator improvements and backend
work should add their own paired records and correctness evidence.

The [Markov constraints action plan](markov_constraints_plan.md) defines the next
application portfolio and optimization order. Its Blues measurements will form a
separate versioned portfolio; no new application timings are claimed by that plan.
