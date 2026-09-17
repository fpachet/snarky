# Compiled all-different masks — 17 September 2026

This follows the numeric-mask runtime at `a291ce7`. Native and mixed states now
compile all-different candidate/value coordinates once and filter domains directly
as masks. The legacy kernel remains the reference and resource-limit fallback.
The complete-assignment semantics and exact supported values are unchanged.

## Implementation

Each constraint receives stable value IDs based on its original alphabets. IDs
represent terms, not numeric magnitude, so symbols and huge signed integers use
the same representation. Per-variable mappings translate candidate masks into
constraint value masks. Consecutive IDs use shifts; irregular mappings update
from the XOR of the previous and current masks, including restored bits. Only
one previous mask is cached per column.

Matching uses integer variable/value arrays retained across calls. Current masks
invalidate removed matching edges before repair. Unmatched variables first take
an available free value; otherwise an iterative breadth-first augmenting path
repairs the matching. This replaces the reference's dictionary-based Hopcroft–Karp
implementation on compiled scopes; it is not a claim of better worst-case matching
complexity. The retained matching is a validated hint, never a domain consequence,
so it does not require a checkpoint trail.

The alternating value graph has an edge from each variable's matched value to
its candidates. A candidate has support if it is matched, belongs to the same
strong component as the matched value, or can reach a free value. This is the
same exact support criterion used by the reference kernel. Dense/small graphs
use the existing bitset component partitioning; sparse graphs use iterative
Kosaraju traversal to avoid repeated floods along long chains. Graph and reverse
graph arrays are rebuilt when input masks differ from the cached supported masks;
they are not an incremental residual graph.

A single cached tuple of previously filtered candidate masks skips graph work
when the exact same domains recur. Exact all-different support filtering is
idempotent. Other domain states validate the matching and recompute supports.
Both support-mask caches and column caches compare actual masks, preserving
sibling-branch and nested rollback behavior without a growing history cache.

Supported masks pass through ordinary `retain_mask`, preserving removal causes,
changed-variable events and trails. An inconsistent revision commits no domain
reductions. Guards are checked before lazy plan compilation, and the outer guard
name remains the cause. No branching or objective policy is changed.

## Limits and controls

Compilation admits at most 2,048 distinct original values per constraint and
262,144 candidate-to-value mapping entries across the state's compiled constraints.
Larger inputs retain the exact reference kernel. These are entry limits, not a
global byte budget or support for billion-value interval domains. Compiled mapping
and matching storage adds persistent memory; measured peaks are reported below.

`NativeState`, `MixedState`, and DFS `solve` accept `alldifferent_masks=False` to
select the reference path. Numeric masks remain independently configurable.
Inference queries keep their existing execution path. NValue's internal matching
and the legacy fact-backed CSP runtime retain their existing kernels.

The diagnostic worker instruments the new `AllDifferentConstraint:mask` hook
as well as the reference hook. Worker results record the selected mode. A
same-source on/off benchmark measures the combined compiled implementation;
it does not attribute gains separately to matching, caching and mask conversion.

## Protocol

Paired Python runs use runtime `a291ce7` and the candidate with the same worker,
FlatZinc input, native NValue, numeric masks, incumbent cuts and search policy.
There is one discarded warmup and three alternating repetitions, with a five-second
external process cap. Process time includes startup, preparation and search;
compilation and independent Gecode validation are outside the timed process.

A full Prune rerun and a fresh CLAIRE run are separate comparisons. Prune is
compiled Rust and uses whole-process timing. CLAIRE uses its bundled interpreter
and internal inference/search time excluding preparation. Different search and
model implementations remain part of these comparisons. No universal language
multiplier follows from them.

Correctness and package checks finish before latency runs. Instrumented CPU and
allocation runs follow latency collection. Background load and thermal conditions
are uncontrolled; three-sample medians are descriptive, not confidence intervals.

## Paired measurements

The [paired record](../benchmarks/results/csp_admask_2026-09-17/results.json) and
[summary](../benchmarks/results/csp_admask_2026-09-17/summary.json) retain all runs.
All mutually completed cases preserve normalized solutions, objectives, nodes,
failures and revisions. Values are median process seconds.

| Workload | Reference | Compiled masks | Reference / candidate |
| --- | ---: | ---: | ---: |
| magic_square_4 | 0.1579 | 0.1466 | 1.08× |
| magic_square_5 | >5 | >5 | — |
| magic_square_3 | 0.1261 | 0.1376 | 0.92× |
| queens_50 | 0.4723 | 0.2792 | 1.69× |
| queens_104 | >5 | >5 | — |
| queens_150 | >5 | >5 | — |
| jobshop_ft06_opt | 0.4335 | 0.4367 | 0.99× |
| all_different_incremental_10 | 0.1692 | 0.1471 | 1.15× |
| all_different_incremental_12 | 0.2224 | 0.1655 | 1.34× |
| all_different_incremental_16 | 0.4484 | 0.2559 | 1.75× |
| nvalue_permutation_16_sat | 0.1367 | 0.1375 | 0.99× |
| nvalue_pigeonhole_16_unsat | 0.1277 | 0.1284 | 1.00× |
| nvalue_queens_6_sat | 0.1354 | 0.1379 | 0.98× |
| nvalue_queens_7_sat | 0.1517 | 0.1494 | 1.02× |
| nvalue_queens_6_unsat | 0.1315 | 0.1316 | 1.00× |
| nvalue_queens_8_sat | 0.1839 | 0.1857 | 0.99× |

Native search medians, excluding startup/preparation:

- queens_50: 0.3329 → 0.1443 s (2.31×), with 52 nodes and 6,867 revisions.
- all_different_incremental_16: 0.3187 → 0.1235 s (2.58×), with 150 nodes and 2,817 revisions.

Magic square 3 has an approximately 11 ms process regression; this includes
startup and compilation, and three samples do not isolate their causes. FT06
and NValue are essentially unchanged. Queens 104/150 and magic square 5 still
time out. Lower propagation cost does not by itself establish a better completion
score or solve the remaining search difficulties.

## Same-source ablation

The [on/off record](../benchmarks/results/csp_admask_ablation_2026-09-17/results.json)
uses identical current sources with `alldifferent_masks` disabled/enabled. Both
keep numeric masks and the same search policy. Outputs and counters match.

| Workload | Masks off seconds | Masks on seconds | Off / on |
| --- | ---: | ---: | ---: |
| magic_square_4 | 0.1625 | 0.1503 | 1.08× |
| queens_50 | 0.4775 | 0.2829 | 1.69× |
| all_different_incremental_16 | 0.4606 | 0.2564 | 1.80× |

## Fresh external comparisons

The [Prune record](../benchmarks/results/prune_admask_2026-09-17/results.json)
and [summary](../benchmarks/results/prune_admask_2026-09-17/summary.csv) cover
54 inputs and 59 mode workloads. Snarky completes **52/59 in every repetition**;
Prune completes **59/59**. Optimization remains **3/5 versus 5/5**. The seven
Snarky timeouts remain: initial queens 104, extended queens 104/150, magic square 5,
pairwise pigeonhole 10, and knapsack/packing optimization. The upstream missing
CSPLib/reserved inputs remain outside this portfolio; compiler-eliminated large
chains still do not exercise compact runtime domains.

The [audit](../benchmarks/results/prune_admask_2026-09-17/audit.json) confirms
identical FlatZinc hashes for all 54 inputs, the unchanged Prune binary and identical
outputs, objectives and counters on all 52 completed Snarky workloads against the
preceding full run. Candidate runtime/worker hashes and control digests match the
archived source. Returned assignments and claimed optima pass the existing
independent FlatZinc and Gecode checks.

### Updated averages

Take the median of three runs for each workload, then the arithmetic mean of
those medians with equal weight per workload. Ratios below divide those means;
they are not means of individual ratios. See the
[computed aggregates](../benchmarks/results/csp_admask_2026-09-17/comparison_averages.json).

| Comparison | Workloads | Snarky average ms | Other solver average ms | Snarky / other |
| --- | ---: | ---: | ---: | ---: |
| Prune: jointly completed workloads | 52 | 165.76 | 6.29 | 26.37× |
| CLAIRE: native queens | 4 | 12.22 | 2.83 | 4.31× |
| CLAIRE: Talarian rules | 2 | 202.36 | 9.09 | 22.26× |
| CLAIRE: triangle rules | 2 | 223.72 | 84.82 | 2.64× |
| CLAIRE: historical rule/choice queens | 4 | 834.25 | 2.83 | 294.27× |

The Prune average excludes all seven Snarky timeouts and includes the two
compiler-solved chain cases; it describes the completed subset, not the whole
portfolio. Prune times include startup; CLAIRE times exclude startup and preparation.
Do not combine these rows into one overall speed ratio. The
[preceding averages](performance_solver_averages_2026-09-17.md) remain unchanged as
historical evidence. Their cross-run differences are descriptive; the paired and
same-source experiments above are the controlled evidence for this optimization.

### Fresh CLAIRE measurements

The [new CLAIRE record](../benchmarks/results/claire_admask_2026-09-17/results.json)
uses the same bundled interpreter and workload templates as the previous record,
one warmup and three alternating repetitions. It archives sources, commands,
checksums and all samples. CLAIRE checkout `25b14968e1eef80269d56af418eda7d2ccd88cbf`
is clean; its binary SHA-256 remains
`1620feffa26215999a1f38fa1d1cc5d116a150cfa813d7f895b2f9fd1fdded78`.

| Queens size | Snarky rule/choice ms | CLAIRE interpreted ms | Snarky native CSP ms |
| --- | ---: | ---: | ---: |
| 8 | 254.41 | 1.78 | 7.93 |
| 10 | 292.46 | 1.13 | 4.63 |
| 12 | 1290.09 | 4.43 | 18.11 |
| 14 | 1500.05 | 4.00 | 18.20 |

Native queens uses three global all-different constraints and affine channels;
CLAIRE and historical Snarky queens use their specialized singleton formulations.
The models have different propagation strength. Each returned board is validated;
historical Snarky/CLAIRE first solutions match. Talarian and triangle measurements
retain different matching implementations and show essentially unchanged gaps.
These runs do not benchmark compiled CLAIRE or isolate language costs.

## Compatibility controls

The [same-worker controls](../benchmarks/results/csp_admask_controls_2026-09-17/results.json)
preserve every checked observation, including exact Boulez optimality/witness and
search work. Times below exclude process startup.

| Control | Reference seconds | Candidate seconds | Reference / candidate |
| --- | ---: | ---: | ---: |
| rules/small/triangle_closure:indexed | 0.00104 | 0.00114 | 0.91× |
| joins/25x8/streamed | 0.11509 | 0.11474 | 1.00× |
| magic4 | 0.40948 | 0.40729 | 1.01× |
| mixed_magic3 | 0.00217 | 0.00175 | 1.24× |
| markov33x8 | 0.14046 | 0.13909 | 1.01× |
| boulez | 1.61777 | 1.55443 | 1.04× |

The tiny triangle-closure control has a roughly 0.10 ms regression. Boulez's
measured gain is modest (about 4%); do not extrapolate the queens gain to every
all-different model. Three repetitions do not establish significance for small
differences.

## Memory at identical work

The control record and [additional allocation runs](../benchmarks/results/csp_admask_memory_2026-09-17/results.json)
use a 30-node limit and one sample per engine, separately from latency collection.
Each pair preserves status, nodes, failures, revisions, objective and flat output.
Traced peaks cover construction/preparation/search; RSS is the process high-water
mark including imports. MiB means 2²⁰ bytes. These are search-prefix measurements,
not full-search memory bounds.

| Workload | Traced peak before → after MiB | Change | RSS before → after MiB |
| --- | ---: | ---: | ---: |
| extended--queens_50 | 5.256 → 4.143 | -21.2% | 35.75 → 32.62 |
| optimization--jobshop_ft06_opt | 1.917 → 1.917 | +0.0% | 28.12 → 28.73 |
| optimization--knapsack_20_opt | 0.222 → 0.223 | +0.5% | 24.72 → 24.84 |
| extended--queens_104 | 17.763 → 14.417 | -18.8% | 75.62 → 55.62 |
| incremental_all_different--all_different_incremental_16 | 2.494 → 1.838 | -26.3% | 28.94 → 28.19 |

Compiled mappings add persistent storage, but avoiding temporary term sets and
matching dictionaries can reduce the observed peak. Resource caps bound compiled
entries, not bytes or all memory retained by the model and fallback kernels.

## Remaining costs

The [CPU profiles](../benchmarks/results/csp_admask_profiles_2026-09-17/results.json)
use at most two instrumented seconds/200 nodes and are not latency samples.
Queens 104 reaches 35 nodes and queens 150 reaches 13, both without a solution.
All-different hooks consume about 0.66/0.61 s, while numeric channel hooks consume
about 1.05/1.12 s. Do not compare these component times directly with the previous
profiles: the faster implementation performs more search work within the limit.

Affine channels and binary support scans are now a stronger next target on these
queens formulations. Exact affine views could eliminate repeated translations and
auxiliary work, but require alias, explanation and rollback semantics before
implementation. Search/relaxation bounds for knapsack and packing remain separate
priorities for improving the completion score. This patch does not implement them.

## Validation

Seven new tests cover 700 deterministic small symbolic/signed/holey models against
exhaustive supported-value enumeration and the set-based kernel, with nested
restoration and sibling failures. Sixty larger irregular sparse models compare
against the reference kernel through three restored visits each. Explicit
700-variable chains/cycles check iterative sparse traversal. Other cases cover
Hall sets, free values, matching repair, guard activation/failure causes, both
compilation limits, and complete search outputs and counters.

Existing mixed-rule, factor, NValue, optimization, Markov and rollback tests
remain in the full non-Bach regression gate. The reference kernel is unchanged.

The full gate passes **1,113 tests, with 3 skipped**, in 228.95 seconds. The
121-test focused group, Ruff, mypy (96 source files), textual validation,
core/companion builds and isolated installation checks also pass. A Python 3.12
queens-50 smoke preserves 52 nodes and 6,867 revisions. See the
[validation record and logs](../benchmarks/results/csp_admask_2026-09-17/validation.md).

## Reproduction

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source /path/to/a291ce7 --reference-ref a291ce7 \
  --reference-nvalue native --only extended/queens_ --only incremental_all_different/ \
  --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/alldifferent_masks_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source . --reference-ref same-source-alldifferent-masks-off \
  --reference-nvalue native --reference-alldifferent-masks off \
  --candidate-alldifferent-masks on --only extended/queens_50 \
  --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/alldifferent_masks_ablation_NEW_LABEL
```
