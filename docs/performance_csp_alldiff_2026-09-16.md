# All-different graph and propagation costs — 16 September 2026

This follows native NValue at `ae1f4e6`. The changes reduce work per propagation
revision while retaining exact supported values, the existing matching algorithm,
search policy, objective semantics and domain rollback behavior.

Paired process medians improve **1.55× for queens 50**, **1.77× for incremental
Latin 16**, and **1.28× for FT06 optimization**. Completion remains **52/59**
against Prune's **59/59**; optimization proofs remain **3/5 versus 5/5**.

## Implementation

Small or sufficiently dense all-different scopes now use compact integer IDs
and bitset adjacency rows for the alternating value graph. The bit path requires
at most 2,048 distinct candidate values, and either at most 64 values or at least
four domain entries per distinct value. Larger sparse graphs retain the existing
sparse traversal. This is a structural dispatch heuristic, not a problem-specific
recognizer, and it does not change consistency strength.
IDs represent actual candidates, never the numeric magnitude of a candidate.
Symbolic values, holes and huge integers therefore retain the same semantics.
Hopcroft–Karp matching and validation of previously cached matching hints remain
unchanged. Both native and legacy CSP execution use this shared kernel.

Reverse reachability from free values is computed first. Values reaching a free
value already have alternating-path support. The remaining vertices are partitioned
into strongly connected components by iterative forward/backward bitset floods.
For a pivot, the vertices both reachable from it and able to reach it are exactly
its component; no component crosses the forward-reachable partition. The algorithm
then processes the two remaining partitions without Python recursion.

An edge is retained exactly when it is matched, lies on an alternating cycle, or
leads to a free value. This preserves Régin generalized arc consistency; it is
not a weaker Hall-set approximation. If every value reaches a free value, no
filtering is needed. Unchanged domain sets are not rebuilt during filtering.

The bitset graph path has bounded quadratic graph storage (about one MiB for the
two adjacency payloads at the cap, excluding other structures). Its SCC partition
algorithm can make quadratically many vertex visits in the worst case; it does
not improve Tarjan's asymptotic bound on arbitrary sparse graphs. The density
guard avoids a measured sparse-chain regression from unconditional bit floods;
alphabets above the cap also use the existing sparse graph implementation.
Graph scratch data is local to a revision, so rollback requires no graph-cache
repair. This representation does not implement compact billion-value domains.

Separately, native propagation now avoids `retain()` when a revised domain has
the same cardinality as the original. Each built-in revision kernel receives a
copy of the current domain and only removes values, so equal cardinality proves
that the set is unchanged. This skips rebuilding and intersecting an identical
domain mask. Changed domains still follow the ordinary trail, removal-explanation
and scheduling paths. No revisions are skipped and no search heuristic changes.

## Measurement protocol

Latency runs are sequential, with no overlapping correctness/profile jobs. The
paired Python comparison uses the same worker, `PYTHONHASHSEED=0`, one discarded
warmup and three alternating measured repetitions, each with a five-second
external cap. The reference is `ae1f4e6`. Both runtimes use native NValue.
The separate shortcut ablation compares bitset graphs alone with bitset graphs
plus the unchanged-domain shortcut. Archives and source hashes identify each
implementation; reference labels alone are not a substitute for those hashes.

The full Prune comparison uses its pinned Rust release binary and identical
FlatZinc JSON, independently checking original primitives, original MiniZinc
models with Gecode, complete enumeration sets and claimed optimality. Timings
include process startup, preparation, search and output, excluding compilation
and external validation. Three samples provide descriptive medians, not confidence
intervals. Background load and thermal state remain uncontrolled.

## Paired Python results

The [paired record](../benchmarks/results/csp_alldiff_2026-09-16/results.json)
and [summary](../benchmarks/results/csp_alldiff_2026-09-16/summary.json) compare
`ae1f4e6` with the candidate. All seven mutually completed workloads retain
identical nodes, failures, revisions and normalized solutions in every repetition.
Queens 104 and 150 time out in both versions in all measured repetitions.

| Workload | Before seconds | After seconds | Speedup |
| --- | ---: | ---: | ---: |
| Magic square 4 | 0.1667 | 0.1594 | 1.05× |
| Queens 50 | 0.8873 | 0.5713 | 1.55× |
| Queens 104 | >5 | >5 | — |
| Queens 150 | >5 | >5 | — |
| FT06 optimization | 1.3449 | 1.0547 | 1.28× |
| Incremental Latin 10 | 0.1993 | 0.1675 | 1.19× |
| Incremental Latin 12 | 0.2907 | 0.2183 | 1.33× |
| Incremental Latin 16 | 0.7912 | 0.4462 | 1.77× |
| NValue permutation 16 | 0.1389 | 0.1361 | 1.02× |

The separate [shortcut ablation](../benchmarks/results/csp_alldiff_retain_ablation_2026-09-16/summary.json)
compares bitset graphs alone with bitset graphs plus the unchanged-domain shortcut.
All three cases retain identical search counters and normalized solutions.

| Workload | Bit graphs only seconds | With shortcut seconds | Additional speedup |
| --- | ---: | ---: | ---: |
| Queens 50 | 0.6675 | 0.5673 | 1.18× |
| FT06 optimization | 1.3424 | 1.0579 | 1.27× |
| Incremental Latin 16 | 0.5211 | 0.4652 | 1.12× |

FT06 benefits from avoiding domain-mask work; this compiled scheduling model has
no all-different constraint. The ablation prevents attributing that gain to graph
filtering. Small process timings, especially the NValue permutation, remain
dominated by startup and should not be read as propagation-throughput ratios.

## Graph-selection stress check

The [kernel-only record](../benchmarks/results/csp_alldiff_graphs_2026-09-16/results.json)
uses one warmup and seven alternating repetitions per strategy, with the same
valid cached matching and exact supported values. These times exclude domain
copying, validation and the rest of the solver.

| Graph shape | Adaptive ms | Forced sparse ms | Forced bits ms |
| --- | ---: | ---: | ---: |
| Dense 50 | 0.460 | 1.538 | 0.463 |
| Dense 150 | 3.965 | 13.917 | 3.918 |
| Free 150 | 7.727 | 27.112 | 7.807 |
| Chain 100 | 0.318 | 0.317 | 1.198 |
| Chain 300 | 0.934 | 1.020 | 10.438 |
| Chain 600 | 2.107 | 2.112 | 45.436 |

The 600-variable chain demonstrates why bitsets are conditional: unrestricted
bit floods cost roughly 45 ms, while the adaptive and sparse paths take about
2.1 ms. Dense graphs benefit from processing adjacency rows as bitsets. This
stress set justifies a conservative default; it is not evidence that the density
heuristic chooses the fastest path on every possible graph.

## Fresh full Prune comparison

The [new full record](../benchmarks/results/prune_alldiff_2026-09-16/results.json)
and [59-workload summary](../benchmarks/results/prune_alldiff_2026-09-16/summary.csv)
retain every repetition. Snarky completes **52/59** and Prune **59/59** within the
five-second cap in all three measured repetitions. Optimization proofs remain
**3/5 versus 5/5**. This slice reduces execution costs without changing which
workloads finish under that limit.

| Workload | Prune process seconds | Snarky process seconds | Snarky / Prune |
| --- | ---: | ---: | ---: |
| Queens 50 | 0.0121 | 0.5769 | 47.5× |
| Incremental Latin 16 | 0.0171 | 0.4764 | 27.8× |
| FT06 optimization, optimum 55 proved | 0.0098 | 1.0558 | 107.8× |
| Magic sequence 40 | 0.0099 | 0.3651 | 36.9× |
| Dominating Queens 8 | 0.0557 | 0.1855 | 3.3× |

These timings compare complete Rust/Python implementations with different
propagators and branching policies. They do not isolate language overhead. This
collector has a different worker/import path from the paired Python experiment,
so its process medians must not be combined with that experiment's speedup ratios.

A separate [parity audit](../benchmarks/results/prune_alldiff_2026-09-16/parity_with_nvalue.json)
checks the previous full NValue record: all 54 compiled inputs have identical
hashes, and all **52 mutually completed workloads preserve nodes, failures,
revisions, objectives, model sizes, lowerings and normalized solutions** across
all old/new samples. This is a search/output comparison, not a paired latency
measurement of all 59 workloads.

The same seven workloads still time out: queens 104 in two suites, queens 150,
magic square 5, pairwise pigeonhole 10, knapsack 20 optimization and bin packing 20
optimization. The two billion-span chain instances are still compiler-solved;
they do not establish native compact-domain support. The 31 requested CSPLib and
reserved instances remain unavailable upstream. The next distinct work is
stronger objective bounds/cuts and search effectiveness, plus the planned compact
domain representation. Faster exact filtering alone has not removed those gaps.

## Compatibility and allocation controls

The [separate controls](../benchmarks/results/csp_alldiff_controls_2026-09-16/results.json)
use the same worker and models with alternating reference/candidate runs. All six
retain identical observations, including applicable search counts. Boulez runs
without a supplied incumbent, proves optimality and recovers the published sequence.
These medians cover preparation and search/inference, excluding process startup.

| Control | Before seconds | After seconds | Before / after |
| --- | ---: | ---: | ---: |
| Small rule closure | 0.001059 | 0.001229 | 0.86× |
| Streamed joins 25×8 | 0.116092 | 0.120103 | 0.97× |
| Legacy magic square 4 | 0.456745 | 0.423303 | 1.08× |
| Mixed magic square 3 | 0.002812 | 0.002389 | 1.18× |
| Markov 33×8 | 0.143500 | 0.140594 | 1.02× |
| Boulez | 1.759121 | 1.670895 | 1.05× |

The rule-only measurements are slightly slower in this run (about 0.17 ms for
the small closure, 4 ms for streamed joins). Their implementation is unchanged;
these samples do not establish a causal regression or a rule-matcher speedup.
The full table is retained rather than claiming improvement on every control.

Separate allocation-instrumented runs stop at 30 nodes and assert identical work.
Queens 50's traced peak changes from 4.86 to 4.75 MiB; FT06 stays at 1.40 MiB,
and knapsack at 0.187 MiB. Whole-process RSS is also recorded, separately from
Python allocations: FT06 rises from 26.64 to 28.41 MiB in the single samples.
These are bounded-run observations, not full-search or statistically established
memory improvements. Instrumented timings are excluded from speedup claims.

## Remaining profile evidence

Separate [CPU profiles](../benchmarks/results/csp_alldiff_profiles_2026-09-16/results.json)
use a two-second cooperative search limit and a 200-node ceiling. They are not
latency runs or matched-work before/after comparisons. Queens 104 and 150 stop
with unknown status; Latin 16 completes and is validated.

For queens 104, linear filtering consumes 0.741 s cumulative and all-different
0.630 s; for queens 150 they consume 0.720 s and 0.714 s. Within these totals,
integer-candidate conversion, matching and graph construction remain visible.
Domain materialization, hashing and changed-domain retention also remain costly.
Nested cumulative times must not be added together.

This supports the next P2 investigation: cache immutable numeric/index views
and reduce changed-scope conversions while preserving domain versions and rollback.
P4's propagated improving objective cuts and measured branching experiments are
still needed for knapsack, packing and the remaining search-heavy cases. Genuine
compact integer intervals remain P5; this patch does not address that gap.

## Validation

New tests compare 1,400 all-different filtering cases across bitset and forced
sparse paths with exhaustive supported values, including 70 complete solution-set
comparisons. They cover empty domains, symbolic values, huge integer offsets,
holes and invalid/repeated matching hints. Separate graph tests compare component
masks with independent reachability on 250 random graphs and exercise 1,200-vertex
chains and dense graphs without recursive SCC traversal. Nested failure/rollback
tests restore widened domains while reusing matching hints. The alphabet-cap test
checks that large alphabets use the exact sparse fallback.

The refreshed CLAIRE comparison's native-global queens formulation is checked
against independently enumerated valid boards for sizes one through five,
including unsatisfiable cases and uniqueness of projected solutions.

A dedicated sparse-chain regression test verifies the sparse dispatch and exact
Hall support. The separate `benchmarks.all_different_graphs` experiment compares
adaptive selection, forced sparse traversal and forced bit floods on dense,
free-value and sparse-chain shapes. Matching hints and retained supports are
identical; domain copying and validation are outside its kernel-only timings.

The full non-Bach gate passes **1,089 tests, three skips**. Ruff, mypy (94 source
files), textual-source validation (305 files), both distribution builds, contents
checks and isolated core/companion installation checks pass. Commands and logs
are retained in the [validation record](../benchmarks/results/csp_alldiff_2026-09-16/validation.md).

## Reproduction

```sh
mkdir -p /tmp/snarky-csp-full-ae1f4e6
git archive ae1f4e6 src csp_solver sudoku rulebases benchmarks pyproject.toml uv.lock \
  | tar -x -C /tmp/snarky-csp-full-ae1f4e6
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source /tmp/snarky-csp-full-ae1f4e6 --reference-ref ae1f4e6 \
  --reference-nvalue native --candidate-nvalue native \
  --only extended/queens_ --only incremental_all_different/ \
  --only optimization/jobshop_ft06_opt --only extended/magic_square_4 \
  --only nvalue/nvalue_permutation_16_sat --hard-seconds 5 \
  --warmups 1 --repeats 3 --output benchmarks/results/csp_alldiff_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.prune_comparison \
  --prune /path/to/prune-fzn --seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/prune_alldiff_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.claire_refresh \
  --output benchmarks/results/claire_refresh_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.all_different_graphs \
  --output benchmarks/results/csp_alldiff_graphs_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_controls \
  --reference /tmp/snarky-csp-full-ae1f4e6 --reference-ref ae1f4e6 \
  --memory-reference /tmp/snarky-csp-full-ae1f4e6 \
  --output benchmarks/results/csp_alldiff_controls_NEW_LABEL
```
