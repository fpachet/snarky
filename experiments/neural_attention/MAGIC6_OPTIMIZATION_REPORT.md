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

## Follow-up: restart portfolios and sparse support decoding, 12 October 2026

The 11×11 breakthrough uses `dom_wdeg`, independently shuffled complete value
alphabets, a shuffled variable tie order, seed 1, and the existing blank-square
symmetry restrictions. It solves in about 0.92 seconds over five repetitions,
with 258 nodes. This is a search setting, with no reference completion or extra
sum equations. Random variable ties use `Random(seed + 1000)`; value permutations
use `Random(seed)`. Saved settings now reproduce both permutations.

The same settings transfer to 12×12 and 16×16. A fixed sequential portfolio
first tries that configuration, then cycles seeded randomized `dom_wdeg`/MRV
settings with symmetry on/off and the earlier degree/middle-first control.
The first experiment allows ten seconds for transfer and four seconds for each
restart, with a sixty-second total budget per size. Model/state preparation,
failed attempts, validation, and recording count toward portfolio wall time.
Interpreter imports are excluded.

| Size | First successful settings | Discovery cost in this experiment |
|---|---|---:|
| 12 | transferred 11×11 settings | 1.37 s |
| 13 | randomized `dom_wdeg`, seed 0, symmetry off | 21.62 s |
| 16 | transferred 11×11 settings, longer attempt | 72.18 s |

The 16×16 discovery cost includes an unsuccessful sixty-second portfolio and a
12.17-second solve in the follow-up with fifteen-second attempts. Four-second
attempts often expire before a first failed branch at these sizes. The runner
therefore defaults to fifteen-second transfer/restart attempts from size 15;
smaller sizes retain the original limits. These revised defaults are tuned on
these observations, not evaluated on independent held-out puzzles. 15×15 remains
unsolved in the two sixty-second portfolios; subsequent seed controls and their
costs are retained in the evidence bundle.

Before the decoder optimization, three fresh repetitions confirm 12×12 at
1.346 seconds/182 nodes, 13×13 at 3.584 seconds/1,488 nodes, and 16×16 at
11.956 seconds/2,536 nodes. Every solution passes the original normal-square
validation. Repeated blank instances measure timing reproducibility, not
generalization across puzzles.

Separate wall attribution and CPU profiles agree on a propagation bottleneck.
For the first eighty nodes of the transferred 15×15/16×16 searches, sums account
for about 72% of wall time and all-different about 26%. Neither prefix is a
completed solve. On the complete 13×13 run, all-different takes about 46% and
sums 49%. The measured, uninstrumented, and CPU-profiled runs have identical
search signatures within each workload.

The profile identifies an avoidable scan in unordered all-different support
decoding. When at most eight global values are removed and they occupy at most
a quarter of the live domain, the decoder now translates just those removals
through its immutable tuple layout. Contiguous shifted layouts retain their
existing path; larger removals retain the full scan. This uses no new inverse
layout allocation and preserves exact support masks, including after rollback.

Three shuffled, sequential repetitions compare only the old and new decoder
on identical searches, including setup and excluding validation/imports:

| Size | Previous decoder | New decoder | Time reduction |
|---|---:|---:|---:|
| 8 | 0.175 s | 0.177 s | unchanged within timing variation |
| 11 | 0.904 s | 0.814 s | 10.0% |
| 12 | 1.371 s | 1.177 s | 14.2% |
| 13 | 3.601 s | 3.294 s | 8.5% |
| 16 | 11.978 s | 10.905 s | 9.0% |
| 15, first 80 nodes | 3.770 s | 3.227 s | 14.4% for this prefix |

All 36 comparison searches preserve nodes, failures, revisions, termination,
and returned squares. The new decoder does not change the search tree.
The non-slow redesign gate passes 1,210 tests, with four skips and 58 slow tests
deselected. The 37 ordering/path/helper tests also pass. Mypy checks all 103
runtime files, and lint/format checks pass. The slow release suite was not rerun.

Portable evidence, source snapshots, raw attempts, repeat runs, profiles, and
comparison timings are saved in
[`benchmarks/results/magic_portfolio_2026-10-12/`](../../benchmarks/results/magic_portfolio_2026-10-12/summary.json).
Archived runner snapshots use `.py.txt` text fixtures, preserving their exact
historical contents and recorded source hashes.
Discovery and initial repeats describe the runtime before sparse decoding;
`decode_comparison` measures both versions. Full CPU profile binaries remain
under `generated/neural_attention/`. The attempt outcomes and elapsed costs
provide labels for a future settings selector; four blank sizes are insufficient
to train and validate one reliably.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_portfolio \
  --sizes 12 13 15 16 --budget 60 \
  --output generated/neural_attention/magic_portfolio_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_alldifferent_benchmark \
  --before benchmarks/results/magic_portfolio_2026-10-12/alldifferent_before.py \
  --presets benchmarks/results/magic_portfolio_2026-10-12/decode_presets.json \
  --output generated/neural_attention/magic_decode_NEW
```

Use `magic_scaling --sizes 12 13 16 --repeats 3 --limit 30` to repeat the saved
winning settings. Every output directory must be fresh. To reproduce the initial
short portfolio, explicitly pass `--transfer-limit 10 --slice 4`.

## Follow-up: exact dense-sum fast paths, 13 October 2026

Two arithmetic fast paths now precede reachable-sum table construction for
compiled equalities with at least three unfixed variables. Contiguous current
integer contribution domains use interval bounds, which give exact supports.
Holey domains can use a sufficient certificate that every current candidate has
support. Uncertified cases retain the original exact prefix/backward bitsets.
Direct one/two-variable supports, compilation budgets, declared candidate order,
and the reference fallback remain in place. No persistent reachability cache or
extra model constraints are introduced.

The certificate uses a small amount of arithmetic on current masks and extrema.
Normalize each domain to minimum zero, let its width be its maximum, and count
the missing integers inside that range. Two domains of widths `a,b` with `h`
holes in total support every sum in `[h,a+b-h]` when `h <= min(a,b)`:
each such sum has at least `h+1` possible integer pairs and at most `h` can be
blocked by holes. Adding another domain extends a certified interval across its
extrema if that interval's width is at least the added domain's hole count.

Three anchor domains leave a pair after excluding any one variable. Conservative
common bounds on their hole counts and widths establish an interior interval
for every sum of the other variables. If every possible residual for the excluded
variable lies inside that interval, all its candidates have witnesses. The fast
path returns the current masks only when those checks succeed. This proves exact
sum support in isolation; the normal propagation queue handles interactions with
other constraints. Current-mask checks and existing tagged caches handle rollback.

A frozen before/after comparison changes only `NumericPlan._equality_supports`.
Both variants use the current all-different decoder and the same saved search
settings. Three sequential repetitions per variant include model/state setup
and search, excluding interpreter imports and solution validation. All 72 runs
have identical nodes, failures, revisions, termination, and returned squares for
their workload; all 54 returned squares pass independent original-model checks.

| Size | Previous sum kernel | New sum kernel | Speedup |
|---|---:|---:|---:|
| 6 | 0.063 s | 0.061 s | 1.03× |
| 8 | 0.171 s | 0.126 s | 1.36× |
| 9 | 2.272 s | 2.314 s | 0.98× |
| 10 | 0.457 s | 0.277 s | 1.65× |
| 11 | 0.813 s | 0.474 s | 1.71× |
| 12 | 1.179 s | 0.563 s | 2.10× |
| 13 | 3.388 s | 2.390 s | 1.42× |
| 14 | 2.759 s | 1.224 s | 2.25× |
| 16 | 11.108 s | 6.938 s | 1.60× |
| 15, first 80 nodes | 3.272 s | 0.699 s | 4.68× |
| 18, first 30 nodes | 4.137 s | 0.786 s | 5.26× |
| 20, first 30 nodes | 8.535 s | 1.206 s | 7.08× |

The bounded-prefix rows are not completed solves. 9×9 shows no useful gain
and its median is about 1.9% slower; the checks add overhead when they cannot
avoid table construction. These results concern individual blank squares and
do not establish generalization to clued puzzles or other CSPs.
Separate outcome counting finds that the new fast paths succeed on 589 of
35,058 eligible revisions for 9×9 (1.7%), versus 1,396 of 2,973 for 12×12 (47%).
The archived counts are diagnostic runs, excluded from latency measurements.

Fresh wall attribution on the optimized first eighty nodes of 15×15 and 16×16
puts sum revisions at about 6% and 11% of search time. All-different now accounts
for about 82% and 80% respectively. Uninstrumented, wall-timed, and CPU-profiled
runs preserve the same search signatures. These percentages apply to those
prefixes, not the complete 16×16 solve or arbitrary search states.

The non-slow redesign gate passes 1,219 tests, with four skips and 58 slow tests
deselected; the 37 experiment helper/path tests also pass. New independent
enumeration checks cover interval filtering, missing values near the extrema,
parity holes, narrow anchors mixed with very sparse wide domains, negative
coefficients, huge translations, target changes, and sibling rollback between
certified and fallback states. Mypy checks all 103 runtime files. The slow release
suite was not rerun for this change.

Portable evidence is in
[`benchmarks/results/magic_sum_dense_2026-10-13/`](../../benchmarks/results/magic_sum_dense_2026-10-13/summary.json),
including both source snapshots, raw runs, frozen hashes, presets, and the new
profiles. The executable baseline snapshot is the numeric source at `3309951`;
historical runner and optimized source snapshots are retained as text fixtures.
The existing comparison tool now accepts `--kernel sum` as well as its default
all-different decoder comparison:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_alldifferent_benchmark \
  --kernel sum \
  --before benchmarks/results/magic_sum_dense_2026-10-13/numeric_before.py \
  --presets benchmarks/results/magic_sum_dense_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 --repeats 3 \
  --output generated/neural_attention/magic_sum_dense_NEW
```

## Follow-up: partial certification experiment, 13 October 2026

Two conservative prototypes extend the interior-support certificate to retain
certified candidates and check only uncertain ones. The first still builds full
sum tables. The second computes exact lower/upper edge bands, keeping every
current value that can contribute to those edges. It introduces no witness cache
or persistent partial-support state. Signed, translated, reflected, and rollback
cases preserve exact supports.

Neither prototype gives a consistent improvement on the magic-square workloads.
The edge version is used once in 3,139 sum-kernel calls for 12×12 and three times
in 40,047 calls for 16×16; it is unused in the measured 9×9 and 13×13 searches.
Its two favorable synthetic kernel probes improve by 2.26× and 8.78×, but those
uncached microbenchmarks do not translate to an end-to-end magic-square gain.

The production numeric source was therefore restored byte for byte. Both
prototypes, their 144 comparison runs, 108 validated boards, source hashes,
diagnostic counts, and explicit correctness tests are retained as an opt-in
[experiment with a readable results table](../../benchmarks/results/magic_sum_partial_2026-10-13/README.md).
The edge prototype passed 1,225 non-slow core tests before restoration. Twelve
explicit baseline/candidate experimental cases and the existing 37 experiment
tests pass after restoration. The comparison tool now accepts `--candidate` to
load an archived method temporarily without changing production source files.

## Follow-up: indexed residual sum systems, 13 October 2026

An opt-in `SumSystemState` builds variable/equality incidence bitsets and updates
residual scopes when variables become fixed or are restored after rollback.
Bounded connected-group discovery selects small closed systems, then exact
rational elimination checks rank, integer feasibility, and domain membership.
Targets are recomputed from current branch values; structural plans never cache
domain support. Ordinary domain updates and backtracking remain native.

Across 72 main blank-square runs, limits of four equations/variables produce no
extra assignments or contradictions. A wider eight-variable/equation diagnostic
also gains no deductions. The one closed system found in 10×10 is dependent.
Every paired search preserves work counters and the returned board. Discovery
is cheap, but total time generally increases slightly without search savings.

In 41 clued 4×4 diagnostics, one instance saves ten nodes through three earlier
contradictions, but compilation overhead outweighs the saving. A deliberately
favorable three-equation example improves from 402 nodes to one and about
150 ms to 5.5 ms, showing that usefulness depends on the residual structure.

The production solver is unchanged. Fifteen focused tests pass, including 200
random exhaustive-oracle cases and preservation of all eight 3×3 solutions.
The [readable experiment report](../../benchmarks/results/magic_sum_systems_2026-10-13/README.md)
contains timing tables, limitations, raw data, frozen sources, and reproduction
commands. This experiment runs after native fixpoints; earlier invocation and
partial deductions from underdetermined systems remain unmeasured.

## Follow-up: exact rank of the entire residual system, 13 October 2026

Offline integer Gauss-Jordan elimination now examines the entire set of sums at
every search node before native propagation and every successful fixpoint.
Instrumentation preserves nodes, failures, native revisions, termination, and
boards against an uninstrumented control. Across 14 sizes, the diagnostic
captures 8,393 before states and 3,058 after states; 15×15, 18×18, and 20×20 remain
bounded prefixes. No deductions are applied to search.

After native propagation, squares 4×4 and above have neither a fully determined
nonterminal residual system nor any individual variable forced by the linear
equations. This rules out a uniquely solvable closed subset of any size at those
observed fixpoints. The closest 10×10 state has four unknowns and rank three;
16×16 has a state with 16 unknowns and rank nine. Before propagation, 10×10 has
one full-rank system of three unknowns, solved immediately by native propagation.
No full-rank residual system larger than eight variables occurs in the traces.

The 3×3 case does have additional partial deductions: its initial system forces
the center to five, despite retaining two degrees of freedom. Larger measured
sizes have no such extra forced values after native propagation. This conclusion
concerns exact linear forcing, not finite-domain filtering of derived relations.

Ten diagnostic tests pass, including 400 random matrices checked against a
separate exact rational RREF implementation. The production runtime is unchanged.
The [full diagnostic report](../../benchmarks/results/magic_sum_global_rank_2026-10-13/README.md)
contains rank tables, before/after counts, compressed full state records, exact
proofs for useful rows, source snapshots, limitations, and reproduction commands.

## Follow-up: selective SUM + ALLDIFF bounds, 13 October 2026

An opt-in `DistinctSumState` adds conservative distinct-value sum bounds inside
the native numeric revision hook, only when an unconditional ALLDIFF covers
the entire unit-coefficient sum. The full union of other current domains supplies
the extrema, excluding fixed and tested values. This is a relaxation of variable
assignment, not exact joint domain consistency. No witness/support cache is added.

A specialized residual two-variable rule removes `R/2` from both domains in
`x+y=R, x!=y`. Direct numeric lookup avoids scanning domains. The main selective
variant adds general bounds only for three active variables with at most 24
candidates in total. Original models, seeds, symmetries, and heuristic settings
are retained; joint failures do not increment arbitrary original dom_wdeg weights.

Across 108 main runs, the selective variant reduces median 13×13 time from
2.356629 s to 0.918941 s (1,488 to 343 nodes), and 16×16 from 6.722612 s to
6.385560 s (2,536 to 2,204 nodes). 9×9 and 10×10 improve by about 4.3%; 6×6 and
11×11 regress by about 1.3% and 1.6%. The two-variable-only variant is also useful
on some presets, but regresses on 11×11. Broad bounds in the preliminary pilot
cost too much and can increase search through changed heuristic choices.

All 113 boards returned across 140 main/exploratory runs are independently valid.
Twenty-two tests pass, including 400 exhaustive support checks, 60 random search
models in five configurations, preservation of all eight 3×3 solutions, guarded
scope exclusions, huge signed translations, and sibling rollback. The production
runtime and saved search parameters remain unchanged. The full core suite was
not rerun for these opt-in files.

The [readable results report](../../benchmarks/results/magic_sum_distinct_2026-10-13/README.md)
contains complete timings, nodes, regressions, source snapshots, counters,
limitations, and reproduction commands. Cost-based matching bounds and clued
puzzle generalization remain untested.

## Follow-up: detection and three-variable cost, 13 October 2026

The experimental coupler now stops eligibility scanning once a size/candidate
limit excludes filtering, preserving the fast pair rule's priority. Three active
variables use temporary normalized value bitsets, requiring only three extrema
per side. Immutable alphabet extrema supply the normalization bounds; spans above
4,096 use the previous general algorithm. No support/witness cache or branch-local
logical state is introduced. The original two-variable arithmetic is unchanged.

Forty-four experimental tests pass, including 5,000 exact helper/counter parity
cases, span-boundary fallbacks, and 864 full reduction/rollback trace comparisons
(48 models, nine configurations, two policies). The 194 benchmark and pilot runs
return 158 independently validated squares. Before/after nodes, failures,
revisions, terminations, boards, and all non-time filtering counters agree.

On 9×9, the main filtering timer falls from 168.992 ms to 151.027 ms; on 16×16,
162.822 ms to 150.649 ms. Whole-solve effects are small and mixed. An additional
seven-repeat series measures 8×8 +1.1%, 9×9 -0.7%, and 14×14 -1.8%; the larger
apparent regressions in the initial series do not recur at the same magnitude.
The prototype retains the changes, while production and saved presets remain
unchanged. No uniform end-to-end speedup is claimed.

The [complete cost report](../../benchmarks/results/magic_sum_distinct_cost_2026-10-13/README.md)
contains the before/after sources, raw runs, equivalence checks, repeated
measurements, limitations, and reproduction commands.

## Follow-up: exact three-variable SUM + ALLDIFF, 13 October 2026

The opt-in `exact` variant replaces distinct-union bounds with exact local joint
supports when three variables remain and their domains contain at most 24
candidates in total. It enumerates the two smallest domains and looks up the
required third value, rejecting equal or fixed values: at most 64 pair checks.
The native solver and saved search settings remain unchanged.

Across three repetitions with the saved presets, 16×16 drops from 6.559401 s
with `tiny` bounds to 5.447669 s with exact filtering (2,204 → 1,688 nodes).
13×13 drops from 0.922902 s to 0.824180 s (343 → 228 nodes); 9×9 from 2.156573 s
to 2.035361 s (2,535 → 2,268 nodes). 8×8 has fewer nodes but essentially unchanged
time. These are whole-search comparisons, not equal-work kernel measurements.

Two additional random seeds test 11×11, 12×12, 13×13 and 16×16 with a 1,000-node
cap. The three completed size/seed pairs have fewer nodes and shorter times;
five pairs remain unresolved at the cap, and several prefixes become slower.
The saved 16×16 improvement therefore does not establish a universal gain.

The archive contains 174 executions, 117 independently validated squares,
57 node-limited prefixes and no timeouts. All 61 coupling tests pass, including
17 new tests: 5,000 exact-mask oracle comparisons, complete enumeration of
150 small models under two search policies, overlapping sums, rollback, huge
integers, eligibility and budget boundaries. The combined SUM experiment suite
has 98 passing tests. Existing non-exact modes preserve their archived behavior.

Keep the exact filter optional. See the [readable experiment and reproduction
commands](../../benchmarks/results/magic_sum_distinct_exact_2026-10-13/README.md).

## Follow-up: compiled lookup, pair budget and matching, 13 October 2026

The exact three-variable prototype can now use compiled immutable numeric maps
instead of building a temporary third-domain lookup. It enumerates the two
smallest current domains and consults the third map plus its current mask.
Fixed values are excluded; no branch-local cache or witness is introduced.
Support masks and deduction counts are preserved, while the actual number of
pairs checked may differ when fixed exclusions change domain-size ordering.

The opt-in `pairs` variant allows exact filtering when the product of the two
smallest current domain sizes is at most 64, rather than limiting the total
candidates to 24. This admits more unbalanced domains. Some saved presets use
fewer nodes, but the extra filtering does not establish a consistent timing gain.

A separate native ALLDIFF change returns from matching repair immediately when
all retained edges validate and the matching is complete. Occupied-value
construction and sorting are skipped. Graph filtering still runs when domains
change, so new Hall sets are not missed. Repair behavior for incomplete matchings
is unchanged. Saved search parameters and default SUM behavior are unchanged.

The non-slow core gate passes 1,221 tests; the slow gate passes 56 tests, with
skips reported separately. All 111 SUM experiment tests pass, including 5,000
new compiled-support oracle cases, complete-solution checks for the expanded
budget, and exact-mask search/rollback trace comparisons with the archived
three-variable filter. Two additional core tests cover a retained matching with
a new Hall set and repair across failed siblings and widening.

See the [benchmark tables, source snapshots and reproduction commands](../../benchmarks/results/magic_sum_lookup_matching_2026-10-13/README.md).
The SUM + ALLDIFF changes remain experimental; end-to-end effects of these
refinements are small and mixed.

## Follow-up: basic domain and propagation operations, 13 October 2026

The native solver now records removed bits and decodes public explanations on
demand, retaining the already decoded prefix across subsequent observations.
Domain masks, sizes and immutable alphabets use stable variable IDs; compiled
SUM/ALLDIFF plans read by index only in their original store. Empty/complete
checks use maintained counters, and decisions retain a singleton bit directly.
The mixed coordinator checks the reduction count without decoding its history.

SUM/ALLDIFF apply only changed support masks. Queue membership uses byte flags
and variable incidence lists use integer IDs, while preserving event order,
off-scope guard scheduling and objective-cut priority. The optional joint filter
also skips unchanged masks; its arithmetic and eligibility are unchanged.

All 1,297 core tests and 111 SUM experiment tests pass across the separate
non-slow, slow and experimental gates. Twenty new regression tests compare
random domain histories and full search traces against the archived baseline,
including sibling rollback, explanations, mixed rules, guards and objectives.

See the [timing tables, component tradeoffs, source snapshots and reproduction
commands](../../benchmarks/results/magic_domain_ops_2026-10-13/README.md).

## Follow-up: variable scores, propagation order and ALLDIFF graph, 13 October 2026

Three isolated experiments compare cached dom/wdeg totals, running ordinary
constraints before ALLDIFF, and building the ALLDIFF reverse graph with repeated
domain rows aggregated. Dense complementary-edge emission is tested separately.
All variants start from `b8e06c1`, with fixed `PYTHONHASHSEED=0` and saved presets.

Only selective reverse-graph aggregation is enabled in production. Rows with
at most eight candidates emit their edges directly; larger identical rows
combine their matching-source bits before emitting destinations. Each revision
rebuilds this temporary structure from current masks. Matching, SCC filtering,
search order, explanations and saved settings remain unchanged.

Three-repeat native medians improve 8×8 from 0.110352 s to 0.097281 s, 11×11
from 0.426527 s to 0.337799 s, and 16×16 from 6.171570 s to 5.320453 s. 9×9
improves by only about 1%. With the optional exact joint filter, 13×13 drops
from 0.755692 s to 0.523022 s and 16×16 from 5.074033 s to 4.116761 s. Every
paired comparison retains identical search counts, solutions and explanations.

Cached weighted-degree totals add little in repeated timings. Two-queue
scheduling has mixed effects: the 13×13 pilot grows from 1,488 to 5,011 nodes
and from 2.118 s to 5.530 s. These variants remain archived experiments. Larger
15–20×20 node-limited prefixes become substantially cheaper with graph
aggregation, but they remain unresolved prefixes, not full-solve timings.

See the [readable report, raw runs, profiles, source snapshots and reproduction
commands](../../benchmarks/results/magic_scheduler_graph_2026-10-13/README.md).
