# Snarky benchmarks

Benchmarks are reproducible programs kept separate from correctness tests.
They compare implementations only after verifying equivalent logical outputs
and archive machine-readable JSON or CSV under [`history/`](history/).

They are not universal performance claims. Wall-clock values depend on Python,
hardware, operating system, background load, and benchmark parameters.
Algorithmic counters and output equivalence are usually more portable.

Use this page for the current overview and commands. The
[results archive](history/README.md) contains the dated evidence behind each
comparison; an archived experiment's defaults apply to its recorded version.

## Magic squares

This is the stable entry point for the current magic-square benchmark summary.

### Native SUM support kernel — 14 October 2026 (experimental)

An opt-in C kernel now computes the same exact equality supports as Python for
eligible `SUM`/`LINEAR_SUM` constraints. It preserves interval and dense-domain
certificates, fixed/one/two-active-variable cases, and the reflected forward/
backward reachability algorithm. It adds no stronger deductions or search
heuristics. Python continues applying reductions, recording causes, trailing
domains and controlling search. Paired runs preserve nodes, failures, revisions,
solutions, residual counters and ordered domain-reduction hashes.

Five paired shuffled whole-solve repetitions give:

| Size | Python CP | CP + C SUM | Reduction | Residual hybrid | Hybrid + C SUM | Reduction |
|---|---:|---:|---:|---:|---:|---:|
| 8×8 | 0.0848 s | 0.0629 s | 25.9% | 0.0401 s | 0.0319 s | 20.6% |
| 9×9 | 1.5667 s | 1.0183 s | 35.0% | 0.6298 s | 0.5557 s | 11.8% |
| 11×11 | 0.3038 s | 0.2156 s | 29.0% | 0.2076 s | 0.1320 s | 36.4% |
| 13×13 | 1.5309 s | 1.0460 s | 31.7% | 0.7746 s | 0.5097 s | 34.2% |
| 14×14 | 0.7304 s | 0.2887 s | 60.5% | 0.7381 s | 0.3035 s | 58.9% |
| 16×16 | 4.3182 s | 2.7855 s | 35.5% | 2.6664 s | 1.5464 s | 42.0% |

Times include model/state setup, lazy native-workspace creation, mask encoding/
decoding, propagation, residual work and fallback. Imports, library compilation/
loading, validation and reduction auditing are excluded. Audited passes are
separate from timing. Comparisons within each strategy use identical search;
CP and the residual hybrid still have different search trees as described below.

The first 30 nodes of 20×20 are slower with C SUM: 0.370 → 0.420 s for ordinary
CP (13.5% slower), mainly from setup. A separate three-pair, 1,000-node prefix
amortizes setup: ordinary CP takes 8.098 → 2.027 s (75.0% less time); hybrid
takes 8.051 → 2.047 s (74.6%). Prefix counters and reduction hashes match.
Neither prefix finds a solution. A subsequent 30-second hybrid+C-SUM attempt
reaches 34,530 nodes without a solution and never drops below 55 unfixed
variables; residual enumeration does not activate. This does not prove
infeasibility of 20×20.

Unlike residual enumeration, C SUM can run at **any search depth**. It supports
equality scopes of 3–64 variables, alphabets up to 4,096 candidates, and a total
original contribution span up to 16,384, subject to the existing Python plan
limits. Python normalizes contributions before conversion, preserving large
signed integers and translations when their span fits. Unsupported cases and
inequalities keep the Python implementation. One/two-variable constraint scopes
retain their existing Python fast paths. Native immutable tables and scratch
buffers are prepared once per numeric plan; the C support call allocates no
heap memory. The generic library uses the existing persistent compiler cache
under `generated/neural_attention/sum_kernel_cache/`.

The [report and frozen evidence](history/magic_sum_kernel_2026-10-14/report.json)
retain 264 audit/timing passes, the interrupted 20×20 attempt and all sources.
Its [read-only validator](history/magic_sum_kernel_2026-10-14/validate.py.txt)
checks 212 complete squares, 244,124 Python/C audited support calls, reduction
hashes, schedules, counters and medians. Fourteen SUM tests cover exhaustive
signed/holey support oracles, large translations, span and word boundaries,
certificates, fallback, causes, rollback and fixpoint caches. All 37 SUM/residual
tests pass; a standalone ASan/UBSan exhaustive driver passes 10,006 cases.

This remains a source-checkout experiment, with no change to public solver
defaults or installed-package dependencies. Use a local C11 compiler and fresh
output paths:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_sum_kernel timing \
  --repeats 5 --output generated/neural_attention/sum_native_NEW
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_sum_kernel audit \
  --output generated/neural_attention/sum_native_audit_NEW
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_sum_kernel timing \
  --sizes 20 --large-nodes 1000 --repeats 3 \
  --output generated/neural_attention/sum_native_20_NEW
python -m pytest experiments/neural_attention/test_sum_kernel.py
python benchmarks/history/magic_sum_kernel_2026-10-14/validate.py.txt
```

The experiment is enabled explicitly with `sum_kernel.enable(state.native, kernel)`
before the state's first propagation. `kernel` is the `SumKernel` instance
returned by `SumKernel.build(output_path)`; imports live under
`experiments.neural_attention`. The benchmark runner provides the complete
CP/residual comparisons and records compilation/cache metadata.

### Fresh solver profiles — 14 October 2026

Profiles regenerated at `8245d27` cover the current Python solver and mode-4
residual hybrid on 8, 9, 11, 13, 14 and 16 to completion, plus a 30-node
20×20 prefix. Three uninstrumented search runs per case establish timing;
wall attribution and cProfile use separate runs. All five passes preserve
nodes, failures, revisions, solutions, termination and residual counters.
Search timings exclude model/state setup, compilation and result validation.
Instrumented percentages below are search attribution, not whole-query gains.

| Hybrid workload | SUM revision | ALLDIFF revision | Residual call |
|---|---:|---:|---:|
| 9×9 | 18.2% | 8.2% | 59.4% |
| 13×13 | 43.0% | 22.2% | 14.6% |
| 14×14 | 76.5% | 11.4% | 0.5% |
| 16×16 | 52.0% | 23.2% | 5.1% |

These profiles prioritized **SUM equality-support computation first, then
ALLDIFF**, leading to the opt-in SUM experiment above. This revised the earlier
ALLDIFF-first suggestion:
the hybrid removes much of the work that previously favored that ordering.
In ordinary 16×16 CP, SUM and ALLDIFF still take 47.2% and 42.8% respectively.
cProfile points to `NumericPlan._equality_supports` and its candidate,
reachability and backward-support loops. Python bigint operations already run
natively, so the benefit of moving surrounding loops must be measured.

The first kernel boundary should accept compiled integer contributions and
current masks, and return supported masks or failure. Python should retain
domain updates, causes, rollback and search control. Exact support equivalence,
signed arithmetic, holes, fixed variables, representation limits and Python
fallback must be verified before claiming a speedup. These profiles implement
no new SUM or ALLDIFF kernel.

On hybrid 16×16, residual extraction/encoding take 6.7%/1.5%, while state
operations take 3.7%; those are lower priorities than SUM. On 9×9, much of the
remaining time is already in the residual call, so Python propagator kernels
have a smaller ceiling. The residual-call category includes ctypes and result
decoding. The short 20×20 prefix is dominated by lazy plan construction;
its propagation-other category should not be read as steady-state queue cost.
It establishes no complete 20×20 solution.

The [profile report](history/magic_native_profile_2026-10-14/report.json)
retains 70 primary passes, ten smoke-check passes, wall attribution, raw
cProfile files, text reports and frozen sources. Its
[read-only validator](history/magic_native_profile_2026-10-14/validate.py.txt)
checks source hashes, schedules, search equivalence, squares and attribution.
cProfile absolute times and the single-pass instrumented percentages are
diagnostic; current whole-solve benchmark medians remain below.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_residual_profile \
  --sizes 8 9 11 13 14 16 20 --repeats 3 \
  --output generated/neural_attention/magic_profile_NEW
python benchmarks/history/magic_native_profile_2026-10-14/validate.py.txt
```

### Reusable residual kernels — 14 October 2026 (experimental)

The residual prototype now offers arithmetic candidate filtering and bitset
iteration in one reusable C library. Before enumerating a variable, it
intersects the intervals allowed by its incident sums. An equality with only
that variable left determines its required value directly. Domain and occupied
value masks then skip holes, consumed values and values outside the interval
using 64-bit operations. Working data uses native arrays; there are no heap
allocations or Python calls inside the search. Remaining-variable bounds stay
static: this is lightweight filtering, without a propagation queue, matching
or exported domain reductions. SIMD and stronger used-value-aware future
bounds have not been implemented.

Five shuffled runs per variant give these whole-solve medians, using the same
switch at 20 unfixed variables and a 200,000-candidate budget:

| Size | Native CP | Previous hybrid | New bitset hybrid | Reduction vs previous hybrid |
|---|---:|---:|---:|---:|
| 8×8 | 0.085710 s | 0.050958 s | 0.042846 s | 15.9% |
| 9×9 | 1.604722 s | 1.126988 s | 0.632822 s | 43.8% |
| 11×11 | 0.310682 s | 0.251269 s | 0.201176 s | 19.9% |
| 13×13 | 1.531026 s | 0.976557 s | 0.784602 s | 19.7% |
| 14×14 | 0.713324 s | 0.717986 s | 0.734019 s | **−2.2%** |
| 16×16 | 4.332252 s | 3.177631 s | 2.646668 s | 16.7% |

The new hybrid improves five sizes and is slightly slower on 14×14. Timings
include setup, extraction, ctypes encoding, native work and fallback, but
exclude imports, compilation/loading and independent result validation.
These are algorithm comparisons: bitsets enumerate in ascending numeric order
and the new budget counts candidates after interval/occupied filtering; the
previous budget counts raw candidate attempts. Search trees and native visit
counts can therefore differ. The earlier aggregate-failure weighting and
first-solution query restrictions still apply. No additional 20×20 experiment
or benefit is established.

A separate replay controls for representation: with identical numeric order,
filtering and budgets, array and bitset versions return identical statuses,
visits, leaves, solution counts and witnesses on all 75 captured states.
Summed median kernel times show bitsets about 1.4–2.0× faster than array
scanning. This is an isolated kernel comparison, not an additional whole-solve
speedup. The original mode-2 visitor also retains exactly the old replay results.

The library is loaded once and reused across residuals and square sizes. A
persistent cache keys binaries by C source, compiler identity, flags, platform
and relevant environment, with SHA-256 integrity checks. Source changes trigger
recompilation. The measured cold build/load takes 139 ms (121 ms compilation);
a fresh-process cache hit takes 29 ms with zero compilation. Those startup
measurements include compiler identity lookup, loading and an output copy, but
exclude Python process startup/imports. Keeping the loaded kernel requires no
further build or cache lookup during search.

The [report and archive](history/magic_residual_reuse_2026-10-14/report.json)
retain both earlier variants, all 312 whole-solve runs, three 75-state replays,
cache evidence and frozen sources. The
[read-only validator](history/magic_residual_reuse_2026-10-14/validate.py.txt)
checks recorded squares, deterministic repeats, counters, medians and hashes.
All 23 experimental tests pass, including exhaustive signed arithmetic,
word boundaries, holes, bounded fallback, equivalent array/bitset searches,
cross-process cache reuse and source invalidation. This remains an opt-in
experiment; the production solver is unchanged.

**Retention decision:** keep the tested prototype on main as an opt-in baseline
for further native-solver experiments. It is not selected by `snarky.finite.solve`,
does not change default solving, and is not shipped in the Python wheel. Run it
from the repository root with Python 3.12+ and a local `cc` compiler supporting
C11/shared libraries (tested locally with Clang; CI uses Linux). Python calls
the loaded library through `ctypes`; only compilation invokes a subprocess.

The switch runs before ordinary propagation when at most 20 variables remain
unfixed. A native witness is checked by ordinary propagation; an exhausted
search rejects the branch; reaching the candidate budget falls back without
changing domains. In the five repeats, fallback counts per solve were 0/1
(8×8), 76/452 (9×9), 0/9 (11×11), 10/350 (13×13), 1/2 (14×14) and 5/1,017
(16×16). The cap is a work budget, not a wall-clock deadline.

Cached libraries live in `generated/neural_attention/residual_kernel_cache/`
and are not committed. Removing that directory while no experiment is running
forces a rebuild on the next invocation. Each benchmark output directory
contains compiler/cache metadata and source snapshots; use a fresh path for
every run.

Reproduce the new hybrid with a C compiler and a fresh output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_residual_evaluation hybrid \
  --sizes 8 9 11 13 14 16 --remaining 20 --mode 4 --work-limit 200000 --repeats 5 \
  --output generated/neural_attention/magic_residual_bitset_replay
```

Run correctness and archived-evidence checks separately from timing runs:

```sh
PYTHONPATH=src:. python -m pytest experiments/neural_attention/test_magic_residual_enumeration.py
python benchmarks/history/magic_residual_enumeration_2026-10-14/validate.py.txt
python benchmarks/history/magic_residual_reuse_2026-10-14/validate.py.txt
```

For the full CP/previous-hybrid/array/bitset comparison, use
`python -m experiments.neural_attention.magic_residual_reuse whole --repeats 5 --output generated/neural_attention/residual_comparison_NEW`.
That module also offers `replay` for captured states and `cache` for cold,
same-process and fresh-process library reuse. Defaults and frozen sources for
the historical study remain in the linked archive.

### Residual enumeration study — 14 October 2026 (experimental)

A separate prototype switches from ordinary CP to a bounded native residual
solver when at most 20 variables remain unfixed. The kernel uses a fixed
variable order, distinctness checks and static arithmetic bounds; it maintains
no propagated domains or matching/SCC structures. After 200,000 attempted
values without a result, it falls back to ordinary CP. A witness is checked by
the ordinary propagators and the independent magic-square validator.

Five shuffled runs per variant confirm the following whole-solve medians with
one shared switching policy. Times include model/state setup, Python residual
extraction, ctypes encoding, native work and fallbacks. Imports, compilation
and independent result validation are excluded.

| Size | Native CP | Experimental hybrid | Time reduction |
|---|---:|---:|---:|
| 8×8 | 0.091235 s | 0.052395 s | 42.6% |
| 9×9 | 1.585776 s | 1.126383 s | 29.0% |
| 13×13 | 1.559506 s | 1.020433 s | 34.6% |
| 16×16 | 4.359086 s | 3.329851 s | 23.6% |

Two additional sizes were tested unchanged after choosing the policy, with
three runs per variant: 11×11 improves 12.7% (0.305 → 0.267 s), while 14×14 is
effectively flat (0.715 → 0.709 s). These are complete first-solution searches;
whole-query enumeration, objectives, predicates and mixed fact inference are
outside this prototype. Joint failure proofs use an aggregate cause and change
`dom_wdeg` weight updates, so search trees and solutions can differ. Ordinary
DFS-node counts exclude the native candidate visits recorded separately.

Plain enumeration is insufficient: at the tested budget it finishes none of
the 12 sampled 13×13 or 12 sampled 16×16 residuals. Early constraint checks
and cheap bounds finish most of them. A switch based only on a small Cartesian
product would miss the useful cases. The observed 10-second blank 20×20 search
never gets below 55 unfixed variables, so this study establishes no gain there.

The enumeration engine is compiled once; the measured confirmation build took
0.078 s. Separately, five residuals were translated to unrolled C programs and
compiled locally. Their kernels run about 1.5–2.7× faster, but compilation takes
88–109 ms. Even ignoring code generation and loading, that requires roughly
320–730 identical calls to break even. All 2,310 observed 16×16 residuals with
at most 24 unfixed variables were distinct; even ignoring values and targets,
the most frequent tested shapes occur only 9–11 times. The evidence supports
reusing compiled kernels, without compiling each encountered state.
These measurements cover a local C compiler; a lower-latency in-memory JIT
has not been evaluated. For these five kernels, one-shot specialization would
need to cost less than roughly 0.1–0.3 ms to recover its cost immediately.

The [study report](history/magic_residual_enumeration_2026-10-14/report.json)
and its archive retain all pilots, 140 whole-solve timing runs, 75
replayed states, full trace data, generated C, compiler timings and frozen
sources. Its [read-only validator](history/magic_residual_enumeration_2026-10-14/validate.py.txt)
checks witnesses and recorded evidence. Eleven experimental tests cover native
solution counts against exhaustive signed-arithmetic oracles, bounded fallback,
hybrid first-solution correctness and generated programs. Lint, type checks
and C warning checks passed. The production solver is unchanged by this study.

Reproduce the confirmation with a C compiler available and a fresh directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_residual_evaluation hybrid \
  --sizes 8 9 13 16 --remaining 20 --mode 2 --work-limit 200000 --repeats 5 \
  --output generated/neural_attention/magic_residual_replay
```

### ALLDIFF matching repair — 14 October 2026

The latest production change collects unmatched variables while validating
retained matching edges, then sorts only those repair starts. An intact
matching returns before occupied-value construction or sorting. Stable sorting
preserves the same repair order; augmenting paths, filtering and branching
are unchanged. The earlier identity-layout shortcut is enabled in both versions.

The final kernel's whole-solve medians include model and state setup. The
14×14 and 16×16 rows use a dedicated five-pair confirmation; other rows use
three pairs from the final multi-size batch.

| Size | Pairs | Before | After | Time reduction |
|---|---:|---:|---:|---:|
| 8×8 | 3 | 0.092624 s | 0.084885 s | 8.4% |
| 9×9 | 3 | 1.641654 s | 1.590257 s | 3.1% |
| 11×11 | 3 | 0.311229 s | 0.309861 s | 0.4% |
| 13×13 | 3 | 1.606674 s | 1.548799 s | 3.6% |
| 14×14 | **5** | **0.742487 s** | **0.723370 s** | **2.6%** |
| 16×16 | **5** | **4.459444 s** | **4.299802 s** | **3.6%** |

All pairs preserve nodes, failures, revisions, solutions and ordered
solution-reduction hashes. An untimed 16×16 differential audit additionally
compares every matching and owner list against the baseline: all 6,799 calls
agree, including failures. Sort-key evaluations fall from 1,409,536 to 13,585
(99.0% fewer); this is separate from the whole-solve time reduction.

Gains vary by batch: the final kernel's first 16×16 batch improved 2.3%, while
14×14 was flat (-0.3%). Its 20×20 diagnostic stops after 30 nodes and was slower
(0.334 → 0.350 s); no completed 20×20 solve or gain is claimed. An alternative
that also built occupied values during every validation scan gave a 4.6% slower
14×14 confirmation and was not selected. All variants and raw samples remain
in the [summary and archive](history/magic_matching_repairs_2026-10-14/summary.json),
with frozen sources, two differential audits and a
[read-only validator](history/magic_matching_repairs_2026-10-14/validate.py.txt).
Validation passed 24 ALLDIFF tests, including stable ties, augmenting paths,
failure recovery, exhaustive supports and rollback. Lint and type checks passed.

Reproduce the confirmation with a fresh output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_alldifferent_benchmark \
  --before benchmarks/history/magic_matching_repairs_2026-10-14/before.py.txt \
  --kernel matching --sizes 14 16 --repeats 5 --audit-reductions \
  --output generated/neural_attention/magic_matching_replay
```

### ALLDIFF layout shortcut — 14 October 2026

The previous production change skips ALLDIFF input-mask translation when every
compiled column already uses the graph's value positions. Eligibility is
computed once from immutable layouts, so rollback needs no extra bookkeeping.
Matching, graph filtering, output decoding and branching are unchanged.

Two separate shuffled five-pair batches show a modest gain for eligible solved
presets. The table uses the second batch's whole-solve medians, including model
and state setup:

| Size | Before | After | Time reduction |
|---|---:|---:|---:|
| 8×8 | 0.090411 s | 0.086257 s | 4.6% |
| 9×9 | 1.669329 s | 1.618139 s | 3.1% |
| 14×14 | 0.730522 s | 0.720285 s | 1.4% |

The first batch measured 3.7%, 3.2% and 2.4%, respectively. Within each batch,
every pair has identical nodes, failures, revisions, solutions and ordered
solution-reduction hashes. The 11×11 and 16×16 presets have randomized layouts
and cannot use the shortcut; their small timing changes establish no gain.
The eligible 20×20 case stops after 30 nodes (0.356 → 0.348 s), so this does
not establish an improvement in completed solving time.

The [summary](history/magic_identity_layout_2026-10-14/summary.json) retains both
batches. The [archive](history/magic_identity_layout_2026-10-14/notes.json)
includes all 90 runs, layouts, source snapshots, checksums and a
[read-only validator](history/magic_identity_layout_2026-10-14/validate.py.txt).
Validation passed 22 ALLDIFF tests, including exhaustive support checks after
random reductions and rollback for aligned, shifted, shuffled and sparse
layouts. Lint and type checks passed. Both timing variants share the new
plan-construction flag; only the `supports` method is swapped.

Reproduce the confirmation with a fresh output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_alldifferent_benchmark \
  --before benchmarks/history/magic_identity_layout_2026-10-14/before.py.txt \
  --kernel alldifferent_supports --sizes 8 9 14 --repeats 5 --audit-reductions \
  --output generated/neural_attention/magic_identity_replay
```

### SUM boundary processing — 13 October 2026

The preceding production change reduces work in exact SUM/LINEAR_SUM equality
filtering. It combines candidate enumeration with prefix construction, checks
the final domain directly, and skips the unused first backward table. The two
largest domains occupy these cheaper arithmetic boundaries; returned masks
keep their original scope order. Variable/value branching is unchanged.

The [paired measurements](history/magic_sum_boundaries_2026-10-13/summary.json)
swap only `NumericPlan._equality_supports`, retaining the earlier ALLDIFF
optimization in both versions. Native medians include model and state setup.
The 16×16 row uses a dedicated five-pair confirmation; other rows use three
pairs from the multi-size comparison.

| Size | Pairs | Before | After | Time reduction |
|---|---:|---:|---:|---:|
| 8×8 | 3 | 0.098257 s | 0.089237 s | 9.2% |
| 9×9 | 3 | 1.682819 s | 1.674495 s | 0.5% |
| 11×11 | 3 | 0.321472 s | 0.317943 s | 1.1% |
| 13×13 | 3 | 1.583678 s | 1.563625 s | 1.3% |
| 14×14 | 3 | 0.750585 s | 0.728673 s | 2.9% |
| 16×16 | **5** | **4.574959 s** | **4.461806 s** | **2.5%** |

Every pair preserves nodes, failures, revisions, solutions and ordered
solution-reduction hashes. Both 16×16 versions visit 2,536 nodes. Its initial
three-pair batch measured 4.639 → 4.381 s (5.5%); the longer confirmation gives
the more conservative headline above. Other sizes mostly changed little.
The 20×20 diagnostic stops after 30 nodes: 0.345 → 0.351 s, with no completed
square or demonstrated gain. No extra inference, probe or witness cache is added.

Candidate selection used [5,005 sampled equality calls](history/magic_sum_boundaries_2026-10-13/replay/summary.json)
from a real 16×16 solve. Six kernels were replayed three times with exact output
checks; the selected kernel was about 6.6% faster in that sampled workload.
Those kernel timings are separate from whole-solve results. The archive retains
all preliminary variants, [multi-size runs](history/magic_sum_boundaries_2026-10-13/comparison/runs.jsonl),
[five-pair confirmation](history/magic_sum_boundaries_2026-10-13/confirmation16/runs.jsonl),
frozen source snapshots and a
[read-only validator](history/magic_sum_boundaries_2026-10-13/validate.py.txt).
Validation passed 1,312 regression tests and 104 experimental compatibility
tests, including numeric oracles for signed coefficients, huge translations,
reflected targets and reordered scopes. Lint and type checks passed.

Reproduce the confirmation with a fresh output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_alldifferent_benchmark \
  --before benchmarks/history/magic_sum_boundaries_2026-10-13/before.py.txt \
  --kernel sum --sizes 16 --repeats 5 --audit-reductions \
  --output generated/neural_attention/magic_sum_boundaries_replay
```

For the original multi-size matrix, use `--sizes 8 9 11 13 14 16 20 --repeats 3`.
The previous [ALLDIFF singleton measurements](history/magic_alldiff_singletons_2026-10-13/summary.json)
preserve the earlier 16×16 gain of 5.468 → 4.655 s with identical search work.
The [graph comparison](history/magic_scheduler_graph_2026-10-13/README.md) covers
row aggregation and the optional joint SUM+ALLDIFF filters. The
[history index](history/README.md) links earlier optimization stages.

### Scaling toward 20×20 — 13 October 2026

The largest completed unrestricted square remains **16×16**. A new search
fills the previous 15×15 gap, but does not complete 17×17–20×20. These trials
use the same blank normal-square model, with no constructed completion or
solution hint. Optional symmetry and the tested joint filters are recorded
per attempt.

| Size | Outcome | Recorded discovery time | Attempts |
|---|---|---:|---:|
| 15×15 | Solved; three fresh replays: **1.135 s median**, 291 nodes each | 36.227 s | 7 |
| 17×17 | Unresolved | 141.067 s | 15 |
| 18×18 | Unresolved | 141.087 s | 15 |
| 19×19 | Unresolved | 141.112 s | 15 |
| 20×20 | Unresolved | 405.169 s | 28 |

Discovery time includes the preceding failed attempts, setup, validation and
recording across the sequential portfolios; it excludes interpreter imports
and the later timing replays. Individual attempts range from about 5 to 60
seconds. Timeouts establish no infeasibility and are not completed solve times.
The recorded 20×20 work includes native search, the optional exact joint filter,
its alternative pair-budget gate, balanced-line value ordering and fresh seeds.

The saved 15×15 setting is randomized `dom_wdeg`, value and tie seed 1, with
symmetry disabled. The [scaling summary](history/magic_large_2026-10-13/summary.json),
[all discovery attempts](history/magic_large_2026-10-13/runs.jsonl) and
[three timing replays](history/magic_large_2026-10-13/repeats/summary.json) preserve
the witnesses, settings, failures and actual budgets. Source snapshots and
per-stage `frozen.json` files are in the same directory. All 80 discovery
attempts are retained: one solved and 79 timed out.

Reproduce discovery with `python -m experiments.neural_attention.magic_large_search`;
pass `--settings` with an archived settings JSON, `--mode native`, `exact` or
`pairs`, and a fresh `--output` directory. For the confirmed preset, run
`PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_scaling --sizes 15 --repeats 3 --limit 5 --output generated/neural_attention/magic15_replay`.

The [archive validator](history/magic_large_2026-10-13/validate_discovery.py.txt)
checks source identities and independently rechecks every completed square.

### Complete-solver comparison — 13 October 2026

**Gecode completes 20×20 in 1.617 s median over three runs.** Snarky's largest
completed square remains 16×16. This compares complete search implementations
on the same blank normal-square constraints, without constructed completions,
solution hints or machine learning. All runs are sequential and single-threaded.
Installed versions are Gecode 6.3.0, Chuffed 0.13.2 and MiniZinc 2.9.7.
This cross-solver table predates the latest native optimizations above;
its source snapshots and timings remain frozen.

The table uses the selected settings with a nominal 10 s search cutoff. Every
completed entry is a three-run median with fresh solver states. Times exclude
model preparation/MiniZinc compilation; external process startup and output are
included. “Unknown” means no solution within the cutoff, not infeasibility.

| Size | Snarky native | Gecode | Chuffed |
|---|---:|---:|---:|
| 8×8 | 0.1084 s | 0.0176 s | 0.1121 s |
| 11×11 | 0.3666 s | 0.0472 s | 0.4545 s |
| 16×16 | 5.4957 s | 0.4622 s | Unknown at 10 s |
| 20×20 | Unknown at 10 s | 1.6166 s | Unknown at 10 s |

The global ALLDIFF, every row/column sum and both diagonal sums are identical.
For 8, 11 and 16, all solvers also receive the same five D4/complement symmetry
restrictions; symmetry is disabled for all three at 20. Snarky uses its saved
size-specific settings. Gecode uses the same `dom_w_deg` / `indomain_random`
annotations, seed 1, and domain-consistent ALLDIFF at every size. Chuffed uses
`first_fail` / `indomain_median`, seed 1, domain-consistent ALLDIFF requested,
and free search (`-f`) to alternate annotated and activity-based search.
Propagation algorithms, branching alternatives, learning and search trees differ.

Preparation matters for small instances: adding the measured compilation/model
preparation gives 8×8 totals of 0.1183 s (Snarky), 0.1408 s (Gecode) and
0.2329 s (Chuffed). Gecode's 20×20 total is 1.7387 s. External compilation is
measured once per case and reused for the three solves; these totals do not
represent three independently repeated compilations. Cutoff semantics also
differ slightly: Chuffed adds initialization time to its search cutoff, while
Snarky charges initialization. Actual process and backend timings are retained.

This is an exploratory comparison of implementations, not a state-of-the-art
ranking or a held-out evaluation. Settings were selected after short pilots;
Snarky's size presets had already been tuned. The initial common MRV/ascending
pilot timed out at 8, 11, 16 and 20 for all three solvers under a 5 s cutoff.
Early Chuffed `dom_w_deg` trials fell back to input-order search, and its random
value annotation is unsupported; those warnings and adapter failures are
preserved separately from the supported settings used above.

The [comparison summary](history/magic_solver_comparison_2026-10-13/summary.json)
and [all 85 measured runs](history/magic_solver_comparison_2026-10-13/runs.jsonl)
retain discovery failures, settings, statistics and 38 validated witness records.
The same archive contains MiniZinc/FlatZinc models, raw solver output, source
snapshots and checksums. Its
[read-only validator](history/magic_solver_comparison_2026-10-13/validate.py.txt)
checks every witness, stage summary and archived source identity.

Reproduce the Gecode settings with a fresh output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.magic_solver_comparison \
  --sizes 8 11 16 20 --tracks preset --solvers gecode --external-values indomain_random \
  --alldiff-domain --limit 10 --repeats 3 --output generated/neural_attention/gecode_replay
```

Use `--solvers snarky` for the saved native presets. For Chuffed, use
`--solvers chuffed --external-values indomain_median --alldiff-domain --free-search`.
The runner uses the installed MiniZincIDE bundle and rejects unsupported
Chuffed search annotations before running.

For the September 2026 redesign baseline and acceptance protocol, use the
[performance baseline and comparison ledger](../docs/performance_baseline.md).
It defines a fixed non-Bach portfolio
collected by `python -m benchmarks.redesign_baseline`, with raw samples and
explicit timing boundaries.

## Reproduction protocol

Run benchmarks from the repository root in a clean environment:

```sh
uv sync --extra dev
uv run pytest
uv run python -m benchmarks.rulebase_suite --repeat 7
```

For an optimization comparison:

1. record the exact commit, Python version, platform, and command;
2. warm up both implementations;
3. alternate baseline and candidate measurements when the script supports it;
4. report the median and retain individual samples;
5. verify facts, solutions, ordering, events, and relevant search counters;
6. store the raw result file rather than copying only a headline number.

Machine-readable results must also record whether each measured Git checkout
was dirty. A commit hash alone is not sufficient provenance when uncommitted
engine changes may affect the timing.

Do not combine results produced for different problem definitions. For
example, a two-position fixed-chord harmonizer and a four-position
chord-generating harmonizer measure different workloads.

## Benchmark catalogue

The [Prune comparison](../docs/performance_prune_2026-09-16.md) imports 54 upstream
CSP/optimization instances (59 instance/mode workloads), runs both engines on
identical FlatZinc JSON, and checks results independently with Gecode. It records
timeouts, startup overhead, the NValue decomposition, and compiler-solved cases.
The requested CSPLib and reserved validation suites (31 more instances) are not
present in the pinned upstream revision and remain explicitly unfilled.

Prune is compiled Rust and Snarky's finite solver is Python. The process timings
compare those complete implementations, including their different search policies
and, in the original baseline, native NValue versus decomposition. They establish
observed completion and
latency, but do not isolate language overhead or rank the underlying algorithms.
Use matched branching and comparable node/failure definitions to investigate search
effectiveness; use controlled domain reductions to compare propagation strength.
Profile Python preparation, propagation, allocation/copying and scheduling separately
before selecting optimizations. Preserve the original measurements when adding
these controlled comparisons.

The [active optimization roadmap](../docs/csp_optimization_roadmap_2026-09-16.md)
defines the diagnostic workloads, phase order, new runtime large-domain probes,
native NValue ablation and regression gates. The
[first implemented slice](../docs/performance_csp_arithmetic_2026-09-16.md)
adds separate diagnostic and paired Python/Python records. The original Prune
comparison remains frozen; compact domains remain planned.
The [second slice](../docs/performance_csp_equality_2026-09-16.md) records exact
weighted-equality filtering and domain-projection reuse, including an equality-only
cache ablation and separate allocation runs.
The [third slice](../docs/performance_csp_nvalue_2026-09-16.md) adds native NValue
and a fresh full Prune comparison. To isolate the encoding change on the same
runtime, use `benchmarks.csp_followup compare --reference-source . --only nvalue/`
with `--reference-nvalue decomposed --candidate-nvalue native`. The bridge also
accepts `--nvalue decomposed` directly. Keep encoding choices in measurement
records: changing them can change variables, constraints, search trees and counters.
The [all-different slice](../docs/performance_csp_alldiff_2026-09-16.md) adds exact
bitset graph filtering and avoids rebuilding unchanged domain masks. Its paired
comparison keeps both NValue encodings native; a separate ablation isolates the
mask shortcut. The [CLAIRE refresh](../docs/performance_claire_2026-09-16.md)
retains the historical rule protocols and labels the native-global queens model
as a different formulation.

The factor-support microbenchmark compares one committed evaluator with the
working tree using the same current matcher, alternating measurement order
and checking every score, witness count, and ordered support list:

```sh
python -m benchmarks.factor_supports --baseline-ref 1a453ad \
  --output benchmarks/history/factor_supports_review_2026-09-08.json
```

The [recorded review comparison](history/factor_supports_review_2026-09-08.json)
reduces the 4,000-witness median from 1.467 s to 0.00937 s for this synthetic
shared-scope case. This is an evaluator microbenchmark, not an end-to-end
harmonization speedup. The record includes raw samples, source hash, commit,
environment, and dirty-checkout status.

### Applications and search

The [bounded Boulez sampling probe](../docs/research/boulez_exact_sampling_probe_2026-09-17.md)
measures exact completion counting, sampling, and exact MDD state reduction on
the existing 24-chord instance. Its standalone C++ kernel and Python runner retain
small exhaustive oracles and raw records; it does not modify the solver runtime.

| Module | Comparison |
|---|---|
| `alice_magic` | [ALICE-inspired sum cancellation and exact elimination](../docs/performance_alice_magic_2026-09-17.md) on 4×4/5×5 magic squares, with default and MRV search controls |
| `prune_comparison` | Prune/Snarky same-model pure CSP and optimization, with independent Gecode validation |
| `csp_followup` | Frozen Prune models: separate CPU/allocation diagnostics and paired Python runtime measurements |
| `csp_controls` | Same-worker rule, legacy CSP, mixed, Markov and Boulez compatibility/performance controls |
| `all_different_graphs` | Dense/free/sparse graph stress cases for adaptive, forced sparse and forced bitset filtering |
| `claire_n_queens` | normalized N-Queens comparison with CLAIRE4 |
| `claire_refresh` | alternating fresh-worker CLAIRE controls plus a separate native-global queens variant |
| `claire_talarian_filter` | normalized Talarian rule-filter comparison with CLAIRE4 |
| `claire_triangle_closure` | streamed multi-premise triangle closure with CLAIRE4 |
| `incremental_conjunctions` | cold and streamed three-premise joins |
| `choice_search` | CSP and harmonizer integration across search traversals |
| `choice_trail` | lazy forked DFS versus reversible-trail DFS on N-queens |
| `choice_formulations` | extensional versus intensional N-queens and harmony transitions |
| `finite_markov` | native fixed-order Markov optimization scaling, limits, separate preparation/search and allocation tracing |
| `classical_csp` | magic squares, Latin squares, and constraints-only versus hybrid Sudoku |
| `csp_harmonizer_next` | generic Sudoku search and note-variable harmonizer |
| `muses_harmonizer` | symbolic harmony core versus complete MuSES object bridge |
| `sudoku_rules` | p1, p6, and p7 human-technique workloads |
| `fibonacci_explicit` | explicit recursive Fibonacci rulebase |
| `rulebase_suite` | documented rulebases across instantiation strategies |

Representative commands:

```sh
uv run python -m benchmarks.claire_n_queens \
  --sizes 8 10 12 14 --repeat 3
uv run python -m benchmarks.claire_talarian_filter \
  --sizes 100 1000 5000 --repeat 3
uv run python -m benchmarks.claire_talarian_filter \
  --engine snarky --sizes 100 1000 5000 --repeat 5 \
  --disable-event-rules
uv run python -m benchmarks.claire_triangle_closure \
  --groups 2 5 10 25 33 50 100 --repeat 5
uv run python -m benchmarks.claire_triangle_closure \
  --engine snarky --groups 2 5 10 25 --repeat 3 \
  --disable-factorized-event-rules
uv run python -m benchmarks.claire_triangle_closure \
  --engine snarky --groups 2 5 10 25 --repeat 3 \
  --disable-factorized-event-rules \
  --disable-partial-join-memory
uv run python -m benchmarks.incremental_conjunctions \
  --groups 25 100 250 --width 8 --repeat 5
uv run python -m benchmarks.incremental_conjunctions \
  --groups 25 100 250 --barrier-groups 2 5 10 25 \
  --width 8 --repeat 3
uv run python -m benchmarks.choice_search --repeat 5
uv run python -m benchmarks.choice_trail --repeat 3
uv run python -m benchmarks.choice_formulations --repeat 3
uv run python -m benchmarks.classical_csp --repeat 3
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 --only-magic --repeat 3
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 --only-magic --repeat 3 \
  --magic-symmetry-breaking
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-propagation-guided
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-dom-wdeg-only
uv run python -m benchmarks.csp_harmonizer_next --repeat 5
uv run python -m benchmarks.sudoku_rules \
  --levels 1 2 3 4 5 6 7 --repeat 5
uv run python -m benchmarks.fibonacci_explicit --repeat 7
```

`claire_n_queens` expects a CLAIRE4 checkout in the sibling directory
`../CLAIRE4`, or at the path named by `CLAIRE4_ROOT`. It uses CLAIRE's bundled
platform interpreter and does not include process startup or model
construction in CLAIRE's measured search time. Snarky prepares its inference
session separately, reports that preparation time, and uses only
`SessionChoiceSearch.solve()` as its primary search timing. The JSON records
these timing scopes explicitly and deliberately publishes no automatic speedup
ratio. The shared protocol finds the first solution with
minimum-remaining-values selection, numeric column and row tie-breaking,
singleton propagation, and no symmetry breaking. The runner specializes
CLAIRE's reversible tables to each requested board size before loading the
source. It requires both engines to select the same first solution.
Engine-specific search and propagation counters are retained because their
definitions are not interchangeable.

`claire_talarian_filter` adapts CLAIRE4's historical Talarian filter test to
a common ten-rule workload. Each of `N` prepared frames receives ten positive
inputs, causing exactly `10N` independent rule firings and `10N` observable
outputs; both runners validate those counts and a `40N` checksum. Primary
timings exclude source/rule parsing and process startup. For each input,
Snarky times `InferenceSession.assume()` followed by `run_group()` to a fixed
point with `materialize_result=False`, matching CLAIRE's immediately
rule-triggering slot update without copying the complete fact memory after
each input. Per-update outputs are read from the event journal. Preparation is
reported separately (input-fact construction plus an empty session for
Snarky, object construction for CLAIRE). The semantic workload and incremental
scheduling are normalized, but the engines' storage models differ, so the
runner reports inference throughput without calculating a cross-engine
speedup ratio. In particular, CLAIRE compiles these rules as event demons:
the slot update binds the object and value, then the remaining comparison is a
direct Boolean test. This benchmark therefore does not measure a general
multi-relation join or a RETE-style partial-match network.
Snarky's event-rule specialization is enabled by default;
`--disable-event-rules` runs the same workload through the generic
semi-naïve path for a direct A/B comparison.

`claire_triangle_closure` exercises a genuinely combinatorial rule. Each
group contains one hub, eight left nodes, and eight right nodes. Membership
relations are prepared first; the timed phase streams all 64 left-to-right
edges per group, with one saturation after every edge. A result exists only
when the hub-to-left, hub-to-right, and left-to-right premises agree. Both
implementations validate the exact firing count, output count, and checksum
of the owning hubs.

The natural CLAIRE formulation attaches a demon to additions in each left
node's `outgoing` set, then scans the instantiated hubs to test the other two
premises. Snarky keeps the rule declarative and compiles the arriving edge as
a factorized join anchor: fixed relation fields select the edge premise, then
two exact index lookups retrieve the hub memberships. It materializes no
left/right prefix product and is independent of `partial_join_limit`.

Consequently this comparison is useful precisely because the storage
strategies differ: CLAIRE has lower per-event overhead but scans all hubs,
while Snarky performs a constant number of indexed matches per edge. The
runner reports no automatic cross-engine speedup ratio.
`--disable-factorized-event-rules` restores the bounded partial-memory path;
adding `--disable-partial-join-memory` selects the generic semi-naïve witness.
Counters distinguish `factorized_event_evaluations`, added candidates, exact
lookups, partial-memory builds, and bypasses.

The archived common run extends to 100 groups. At 33 groups the old retained
prefix exceeds its default budget and falls back to the generic join, so a
separate one-run cliff record is retained rather than hiding that behavior in
an extrapolation.

`incremental_conjunctions --barrier-groups ...` reports all three Snarky
paths for the same comparison-barrier rule: `factorized`, `memory`, and
`generic`. Cold and ordinary streamed conjunctions remain guards for rule
shapes outside the new specialization.

### Constraint filtering and propagation

| Module | Comparison |
|---|---|
| `constraint_instantiation` | indexed joins versus safe domain filtering |
| `constraint_propagation` | strategies on the binary-constraint rulebase |
| `constraint_scaling` | declarative propagation as domains and chains grow |
| `constraint_support_churn` | residual existential witnesses during removal |
| `arithmetic_constraints` | specialized arithmetic filtering before joins |
| `global_constraints` | `NVALUE`, `ALL_DIFFERENT`, and persistent domains |
| `compact_tables` | scanned tables, bitset filters, and direct compact joins |
| `propagation_trail` | reversible trails versus full-state snapshots |
| `constraint_branching` | cloning a populated adaptive strategy |
| `domain_planning` | compilation of wide finite-domain plans |

Representative commands:

```sh
uv run python -m benchmarks.constraint_instantiation \
  --sizes 32 64 96 --repeat 7
uv run python -m benchmarks.constraint_propagation \
  --sizes 16 32 64 --repeat 7
uv run python -m benchmarks.global_constraints --size 200 --repeat 7
uv run python -m benchmarks.compact_tables \
  --levels 1 6 7 --repeat 7
uv run python -m benchmarks.propagation_trail \
  --variables 200 --branches 100 --repeat 7
```

Constraint benchmarks report metrics such as candidate facts, domain
reductions, propagator revisions, active table rows, exact matcher attempts,
and activations. A faster result is accepted only if these counters are
consistent with the intended algorithm and the final inference result is
unchanged.

### Engine and parser internals

| Module | Comparison |
|---|---|
| `agenda_incremental` | cold MEA agenda construction versus incremental update |
| `parser_lexing` | term and arithmetic tokenization |
| `parser_terms` | recursive parsing of representative term shapes |
| `parser_premises` | ordinary, aggregate, and nested premise blocks |
| `parser_actions` | ordinary and nested action blocks plus a real rulebase |

```sh
uv run python -m benchmarks.agenda_incremental --rules 200 --repeat 20
uv run python -m benchmarks.parser_lexing --repeat 11
uv run python -m benchmarks.parser_terms --repeat 11
uv run python -m benchmarks.parser_premises --repeat 11
uv run python -m benchmarks.parser_actions --repeat 11
```

Parser refactors compare both public parsing and the extracted internal
component. The real-rulebase case verifies group/rule counts so a speedup
cannot hide missing input.

## Result archive

The archive is chronological evidence, not a single current leaderboard.
File names include the feature and date:

```text
history/
├── classical_csp_2026-07-25.json
├── classical_csp_dom_wdeg_2026-07-25.json
├── classical_csp_learned_impact_2026-07-25.json
├── classical_csp_incremental_2026-07-25.json
├── classical_csp_optimized_2026-07-25.json
├── choice_search_2026-07-25.json
├── compact_tables_2026-07-24.csv
├── parser_actions_2026-07-25.json
├── rulebase_suite_2026-07-24.csv
└── ...
```

Important consolidation comparisons include:

- `fact_index_extraction_2026-07-25.json`;
- `query_memory_extraction_2026-07-25.json`;
- `semi_naive_compiled_delta_2026-07-25.json`;
- `domain_tables_extraction_2026-07-25.json`;
- `comparison_propagators_extraction_2026-07-25.json`;
- `domain_planning_2026-07-25.json`;
- `parser_lexer_2026-07-25.json`;
- `parser_terms_2026-07-25.json`;
- `parser_premises_2026-07-25.json`;
- `parser_actions_2026-07-25.json`.

These A/B runs were used as non-regression evidence while decomposing the
engine. The current implementation and environment may produce different
absolute timings.

## Interpretation

Snarky retains a naive deterministic strategy as an executable semantic
oracle. Indexed and semi-naive strategies remove repeated work. Constraint
strategies can additionally filter finite domains and compact premise tables
before exact matching. The adaptive strategy selects filtering only when its
estimated setup cost is likely to be amortized.

Consequently, no one strategy must win every microbenchmark:

- tiny rulebases can favor lower setup cost;
- append-only recursion favors semi-naive deltas;
- selective finite constraints can favor domain filtering;
- highly mutable workloads stress index and witness maintenance;
- application runs include orchestration and trace costs absent from isolated
  joins.

Optimization work should target a measured bottleneck, retain a differential
oracle, and avoid application-specific shortcuts in the generic engine. The
[finite-CSP solver optimization plan](../docs/solver_optimization_plan.md)
records the current profile, completed dependency scheduling and `SUM` bitset
work, and the acceptance boundary for future incremental state.

The [paired redesign collector](redesign_comparison.py) compares preserved
reference and candidate sources, matched-search CSPs, mixed overhead and bounded
Markov optimization. See the [comparison report](../docs/performance_comparison_2026-09-16.md)
for the measured decision, full timing scopes and memory tradeoff. Generate the
base tables for a new record with `python -m benchmarks.report_redesign RECORD.json
--output REPORT.md`, then append the correctness evidence and acceptance decision.

## LSDB Blues: exact first-order optimization

The [corpus audit](data/omnibook_blues_v2/README.md) describes the source-faithful
and proposed three-family/two-family variants and the exact training conventions. Run:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.blues_markov \
  --repeat 3 --seconds 5 --output /tmp/blues_new_record.json
```

This compares native rational-product optimization to an independent DP for
ordinary and exactly-one-F-sharp-seventh Blues. For Boulez Blues the DP omits
all-different and is only an upper bound. Its training and generation both use the
24-symbol two-family corpus. See the
[initial performance report](../docs/performance_blues_2026-09-16.md) for results,
source snapshots and remaining work. The research corpus is not packaged with
Snarky; no LSDB installation is needed to run the committed compact fixture.

### Boulez assignment-bound comparison

The [paired collector](boulez_optimization.py) compares the frozen pre-optimization
source, the new controller with its chain bound, and automatic assignment bounds
with and without the published Table 5 warm start. It records independent sequence
validation, exact scores, first-solution/target/proof times, and separate traced
allocation runs. Existing rule/CSP/mixed control workloads are run on both sources.

```sh
mkdir -p /tmp/snarky-boulez-reference-e5e25cf
git archive e5e25cf src csp_solver sudoku rulebases benchmarks pyproject.toml \
  third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku/puzzles/grid3x3-p7.clp | \
  tar -x -C /tmp/snarky-boulez-reference-e5e25cf
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.boulez_optimization \
  --repeat 3 --seconds 5 --output /tmp/boulez_new_comparison.json
```

Use a fresh output path. The collector archives both source states, including dirty
candidate files, and checks their hashes remain unchanged. The output embeds the
published-witness record needed by the worker; when reproducing an archive alone,
restore it as `benchmarks/history/blues_published_witness_2026-09-16.json`.
Restore the embedded Sudoku input to its recorded path as well.

### Workforce scheduling

Run `python -m benchmarks.workforce_scheduling` for the basic preference tradeoff,
or `python -m benchmarks.workforce_scheduling_extended` for breaks, rest, coverage
and optional alternatives. The [scheduling guide](../docs/scheduling.md) explains
the API, limitations and repeated A/B measurements.

`python -m benchmarks.scheduling_comparison --baseline /path/to/snapshot --output
generated/scheduling_comparison.json` compares a previous source snapshot with
the current runtime in fresh processes. See the [raw records](history/scheduling_2026-09-26.json)
and [reference patch](history/scheduling_2026-09-26_before.patch).

The [32-task collector](scheduling_symmetry.py) ports the population POC's archived
inputs and model without its API dependency. Run:

```sh
python -m benchmarks.scheduling_symmetry --repeat 3 --seconds 10 \
  --output generated/scheduling_symmetry_new.json
```

It compares the original workload kernel from `f8c82b5`, symmetry alone, optimized
workload propagation alone and both changes. Each variant runs monolithically
and as four independently solved skill groups. The ten-second limit is per solve;
decomposed totals may therefore exceed ten seconds. Profiles run separately from
latency measurements. No cache reuses component proofs. Every incumbent is
independently checked; a matching oracle is called only after each solve.
The output refuses to overwrite an existing record and embeds the reference
kernel, inputs and current source hashes. See the
[report](../docs/performance_scheduling_2026-09-28.md) and
[raw archive](history/scheduling_symmetry_2026-09-28.json).

To measure the effect on the 40 existing scheduling and factor-bound tests:

```sh
python -m benchmarks.scheduling_test_comparison --repeat 5 \
  --output generated/scheduling_tests_new.json
```

This uses the same historical workload kernel and current tests in fresh
processes, with no added symmetry constraints. It records whole pytest invocation
time and individual test-call durations; no timing is an assertion. See the
[test timing archive](history/scheduling_tests_2026-09-28.json) and the
[interpretation](../docs/performance_scheduling_2026-09-28.md#effect-on-existing-scheduling-tests).

## Established scheduling: PSPLIB J30 and OR-Library job shop

```sh
python -m benchmarks.scheduling_standard --fetch
python -m benchmarks.scheduling_standard --repeat 3 --seconds 10 \
  --output generated/scheduling_standard_new.json
pytest tests/test_scheduling_standard.py
```

Run from an installed source checkout. Fetch verifies the pinned hashes and caches
upstream data under ignored `generated/`; normal runs are offline. A changed
upstream download fails verification and requires a reviewed manifest update.
Outputs refuse overwriting. Each case uses a fresh process, with case order
reversed on alternate repetitions. No published objective enters a model.

The [fixed selection and protocol](data/scheduling_standard/README.md) include
12 J30 projects and FT06/LA01–LA05. The
[importers, models and validators](scheduling_instances.py) preserve original
precedences, integer durations, resource demands and makespan minimization.
The [report](../docs/performance_scheduling_standard_2026-09-29.md) explains the
zero-duration encoding and domain bounds. The
[raw results](history/scheduling_standard_2026-09-29.json) retain every timeout,
all incumbent start vectors, independently checked witnesses, search counters,
construction/first-feasible/proof timings, bounds, gaps and source hashes.

To revalidate saved witnesses without rerunning search:

```sh
python -m benchmarks.scheduling_verify \
  benchmarks/history/scheduling_standard_2026-09-29.json
```

The [optimization follow-up](../docs/performance_scheduling_improvements_2026-09-29.md)
uses the archived runtime as a reference and compares kernel changes, constructive
incumbents and compact models on the same cases:

```sh
python -m benchmarks.scheduling_improvements --repeat 3 --seconds 10 \
  --output generated/scheduling_improvements_new.json
python -m benchmarks.scheduling_verify \
  benchmarks/history/scheduling_improvements_2026-09-29.json
```

The [comparison protocol](data/scheduling_standard/IMPROVEMENTS.md) includes
heuristic generation in the ten-second budget. The witness verifier also checks
the saved constructive improvement history.

The [order-search follow-up](../docs/performance_scheduling_order_2026-09-29.md)
adds deterministic local improvement and an explicit scheduling search over
precedence graphs. The [protocol](data/scheduling_standard/NEXT.md) includes
incumbent sharing and phase budgets; optional propagation and longer runs remain
separate diagnostics.

```sh
python -m benchmarks.scheduling_next --repeat 3 --seconds 10 \
  --output generated/scheduling_next_new.json
python -m benchmarks.scheduling_verify \
  benchmarks/history/scheduling_next_2026-09-29.json
```

The [optimality follow-up](../docs/performance_scheduling_proofs_2026-09-29.md)
adds conflict-clique resources and root probing of start domains. The
[protocol](data/scheduling_standard/PROOFS.md) compares the new portfolio with
the archived `80abc15` runtime and separately removes each improvement.

```sh
python -m benchmarks.scheduling_proofs --repeat 3 --seconds 10 \
  --output generated/scheduling_proofs_new.json
python -m benchmarks.scheduling_verify \
  benchmarks/history/scheduling_proofs_2026-09-29.json
```
