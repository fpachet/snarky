# Native NValue — 16 September 2026

This follows the [equality/cache slice](performance_csp_equality_2026-09-16.md)
at `e296d09`. It adds a native distinct-value constraint and replaces the Prune
adapter's Boolean/table decomposition by default. The old encoding remains
available for a controlled comparison. This changes both the representation and
propagation; identical dom/wdeg settings do not imply identical search trees.

The fresh full comparison completes **52/59 Snarky workloads**, up from the
previous 48/59, while **Prune completes 59/59**. Native NValue eliminates all four
Dominating Queens timeouts. Optimization proofs remain **3/5 versus 5/5**.

## Semantics and filtering

`NValueConstraint(name, scope, count, constants=())` requires the distinct values
assigned to `scope`, together with the literal `constants`, to number exactly
`count`. The count is a fixed integer or finite variable. Repeated references,
repeated constants, empty scopes and a count variable also in the scope have
explicit semantics. Both native and legacy CSP execution use the new kernel;
`MODEL` and fact-derived constraint templates expose it. This is separate from
the existing rule-matcher NValue premise.

The propagator combines:

- Mandatory values from literals and singletons, a greedy disjoint-domain lower
  bound and an independent cover-capacity lower bound.
- A maximum partial matching into values outside the mandatory set, providing
  an upper bound on the distinct count. The augmenting-path implementation is
  iterative.
- Count-domain filtering, unique occurrences when every possible value must
  occur, and intersection when only one additional value remains.
- Exact specializations for count one and for all scoped variables adding
  distinct values beyond the literals; the latter uses the existing Régin filter.
- A necessary at-most-count cover feasibility check. It uses integer incidence
  masks, dominated-column elimination, capacity pruning and memoized failures.

The cover check permits 2,000 search nodes per revision, at most 256 uncovered
domains/distinct incidence columns, and depth 16. Outside these limits, or when
the node budget expires, it returns unknown. Unknown never becomes a contradiction
or a removed candidate. A successful at-most cover is not an exact-count proof;
normal CSP search and the independent complete-assignment evaluator still apply.
These caps bound this check, not total solver memory or every propagator's work.

General domain consistency is **not promised**. Every reduction is sound and
complete assignments retain exact semantics. All scratch structures are local to
a revision, so there are no cover/matching caches to restore. Count aliases are
covered by exhaustive tests. Constant constraints with no variables are also
handled by chain objective bounds and the optional regular inference backend.

## Measurement protocol

All latency samples use fresh sequential processes, `PYTHONHASHSEED=0`, one
discarded warmup and three measured repetitions, with a five-second external cap.
Compilation and external Gecode validation are excluded. Raw records preserve
commands, all samples, machine/runtime details, source archives and hashes.
Background load and thermal state are uncontrolled; medians describe these runs,
not confidence intervals.

The recorded environment is macOS 15.7.7 on arm64 with Python 3.13.11. Prune is
the pinned release build at `d82c64c29e823513845e56a54e22e21606c0698c`, with its
binary hash retained. The candidate is a dirty working tree based on `e296d09`;
source hashes and archives, rather than that parent commit alone, identify the
measured implementation.

The encoding ablation uses the same current Python sources and diagnostic worker
for both encodings. It measures the complete representation/propagation change,
including its effect on search. Allocation diagnostics are separate instrumented
runs stopped after one entered node. They include model construction and root
propagation; they are neither latency measurements nor equal-revision comparisons.

The fresh Rust/Python comparison uses identical compiled FlatZinc JSON and the
pinned Prune release binary. Every Snarky assignment is independently evaluated
against original FlatZinc primitives. Reported first solutions and optimization
assignments are fixed in the original MiniZinc model and checked with Gecode;
complete enumeration sets and proof status are checked separately. A timeout
does not establish infeasibility or optimality.

## Fresh full comparison with Prune

The [raw comparison](../benchmarks/results/prune_nvalue_2026-09-16/results.json)
and [all 59 workload summaries](../benchmarks/results/prune_nvalue_2026-09-16/summary.csv)
record a new complete run, not a combination of historical timings. Completion
requires success in all three measured repetitions. The 54 available instances
produce 59 instance/mode workloads. The requested 20 CSPLib and 11 reserved
instances remain unavailable in the pinned upstream source. The two large-domain
chains are compiler-solved and still provide no evidence of native billion-value
domain support.

| Suite | Workloads | Prune completed | Snarky completed |
| --- | ---: | ---: | ---: |
| Initial | 12 | 12 | 11 |
| Extended | 25 | 25 | 22 |
| Optimization | 5 | 5 | 3 |
| All-different global/pairwise | 6 | 6 | 5 |
| Incremental Latin/all-different | 3 | 3 | 3 |
| NValue | 6 | 6 | 6 |
| Large domains, compiler-solved | 2 | 2 | 2 |
| **Total** | **59** | **59** | **52** |

| Workload | Prune process seconds | Snarky process seconds | Snarky / Prune |
| --- | ---: | ---: | ---: |
| NValue permutation 16 | 0.0054 | 0.1329 | 24.7× |
| NValue pigeonhole 16 UNSAT | 0.0041 | 0.1216 | 29.6× |
| Dominating Queens 6 SAT | 0.0053 | 0.1351 | 25.4× |
| Dominating Queens 7 SAT | 0.0258 | 0.1482 | 5.7× |
| Dominating Queens 6 UNSAT | 0.0051 | 0.1235 | 24.4× |
| Dominating Queens 8 SAT | 0.0538 | 0.1893 | 3.5× |
| Magic sequence 40 | 0.0094 | 0.3746 | 39.9× |
| Bin packing 40 feasibility | 0.0052 | 0.2820 | 54.6× |
| Queens 50 | 0.0117 | 0.8711 | 74.2× |
| FT06 optimization, optimum 55 proved | 0.0089 | 1.3416 | 151.5× |

Prune remains faster. These compare complete Rust/Python implementations with
different search policies and propagators; they do not isolate language overhead
or rank algorithms. The separate ablation below uses a different worker with
additional diagnostic imports, so its process medians should not be mixed with
this table. Native phase timings are retained separately in both records.

Seven Snarky workloads still time out: queens 104 in both the initial and extended
suites, extended queens 150, magic square 5, pairwise pigeonhole 10, knapsack 20
optimization and bin packing 20 optimization. All have three recorded timeouts.
The next performance targets remain all-different/propagation costs for larger
queens and stronger objective bounds/cuts for the two unproved optima. Compact
domains remain a separate capability project.

## Same-runtime encoding ablation

All six native cases complete in every repetition. The four Dominating Queens
cases exceed five seconds in every decomposed repetition, including warmups.
The [raw record](../benchmarks/results/csp_nvalue_ablation_2026-09-16/results.json)
and [summary](../benchmarks/results/csp_nvalue_ablation_2026-09-16/summary.json)
retain all timings, counters and independently checked outputs.

| Case | Decomposed process seconds | Native process seconds | Native search seconds | Native nodes / revisions |
| --- | ---: | ---: | ---: | ---: |
| Permutation 16 | 0.1356 | 0.1389 | 0.01104 | 16 / 31 |
| Pigeonhole 16 UNSAT | 0.1315 | 0.1302 | 0.00034 | 1 / 1 |
| Dominating Queens 6 SAT | >5 | 0.1400 | 0.01067 | 25 / 26 |
| Dominating Queens 7 SAT | >5 | 0.1535 | 0.02377 | 41 / 42 |
| Dominating Queens 6 UNSAT | >5 | 0.1297 | 0.00109 | 1 / 1 |
| Dominating Queens 8 SAT | >5 | 0.1936 | 0.06173 | 79 / 80 |

The four timeout transitions imply process speedup lower bounds of approximately
26–39×, not measured exact ratios. Python startup/imports dominate several native
cases. Native search times above exclude startup and model construction; the
same-worker process times include them. Search counts are stable across native
repetitions. They are not comparable work units across the two encodings. The
permutation case's process median increases about 2.4%; it already had a direct
all-different encoding and does not benefit from removing a Boolean network.
Its native search phase rises from 6.63 to 11.04 milliseconds: the new constraint
computes general bounds before its all-different specialization. This overhead is
visible even though startup makes its process-level percentage much smaller.

## Representation and root allocation

The [decomposed record](../benchmarks/results/csp_nvalue_decomposed_memory_2026-09-16/results.json)
and [native record](../benchmarks/results/csp_nvalue_native_memory_2026-09-16/results.json)
contain one separate allocation-instrumented sample per case. Both stop after one
entered node; propagation may still prove infeasibility there. These runs overlapped
the correctness gate, so their timings are not used as latency evidence. Traced
Python peak covers construction/preparation/search; RSS is a process high-water
mark including imports, and neither is compared with Rust memory.

| Case | Variables, decomposed → native | Constraints, decomposed → native | Python peak MiB, decomposed → native |
| --- | ---: | ---: | ---: |
| Permutation 16 | 16 → 16 | 1 → 1 | 0.105 → 0.115 |
| Pigeonhole 16 | 17 → 16 | 0 → 1 | 0.057 → 0.092 |
| Dominating Queens 6 SAT | 688 → 36 | 689 → 1 | 4.143 → 0.252 |
| Dominating Queens 7 SAT | 1,099 → 49 | 1,100 → 1 | 7.071 → 0.442 |
| Dominating Queens 6 UNSAT | 688 → 36 | 689 → 1 | 4.143 → 0.252 |
| Dominating Queens 8 SAT | 1,648 → 64 | 1,649 → 1 | 12.283 → 0.634 |

Dominating Queens' traced peaks fall approximately 16–19×. Whole-process RSS
falls from 35.3–54.8 MiB to 24.6–26.5 MiB across those four cases. Native filtering
proves the 6×6 UNSAT case at root; the decomposition remains unresolved there.
The permutation/pigeonhole cases are explicit small allocation regressions: the
old importer already specialized the former to all-different and recognized the
latter as impossible during construction. Native NValue preserves their results
but adds general bounds machinery. No blanket claim that every case uses less
memory is made.

## Rule, legacy, mixed and Markov controls

The [paired controls](../benchmarks/results/csp_nvalue_controls_2026-09-16/results.json)
compare `e296d09` with the candidate using the same worker and workload definitions,
three alternating pairs and warmups. All recorded outputs and search counters
match. Boulez again reproduces the published sequence with the same exact optimum
and completed proof, without a supplied incumbent.

These medians include preparation and search but exclude process startup:

| Control | Reference seconds | Candidate seconds |
| --- | ---: | ---: |
| Rule triangle closure | 0.001109 | 0.001157 |
| Streamed joins 25×8 | 0.114127 | 0.112915 |
| Legacy magic square 4 | 0.444240 | 0.442459 |
| Mixed magic square 3 | 0.002569 | 0.002793 |
| Markov 33×8 | 0.139961 | 0.139851 |
| Boulez, exact optimization | 1.691307 | 1.689487 |

The small rule control is about 4.3% slower and mixed control about 8.7% slower
(roughly 0.048 and 0.224 milliseconds respectively). They are retained rather
than described as improvements. Three samples do not establish whether these
small differences are stable overhead or environmental variation. The larger
controls are essentially unchanged; no general rule/Markov speedup is claimed.

## Correctness and distribution checks

The full non-Bach gate passes **1,075 tests, three skips**. New tests check 1,000
deterministic filtering problems against independent exhaustive supports with
normal and zero cover budgets, including 200 complete solution-set comparisons.
There are separate matching/cover oracles, native/legacy rollback and explanation
checks, both bridge encodings, count aliases, constants, empty scopes, guarded
mixed rules, observer exceptions, objective optimization and exact inference.

Ruff, mypy (94 source files), textual-source validation (305 files), distribution
contents checks and isolated core/companion installation checks pass. The installed
wheel explicitly exercises NValue optimization. The
[validation record](../benchmarks/results/csp_nvalue_ablation_2026-09-16/validation.md)
retains commands and logs. Bach remains outside this portfolio.
A Python 3.12 worker also solves Dominating Queens 8 in the same 79 nodes and
80 revisions with a validated assignment; the full regression gate used Python 3.13.

## Reproduction

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source . --reference-ref same-source-decomposition-ablation \
  --reference-nvalue decomposed --candidate-nvalue native --only nvalue/ \
  --hard-seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/csp_nvalue_ablation_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.prune_comparison \
  --prune /path/to/prune-fzn --seconds 5 --warmups 1 --repeats 3 \
  --output benchmarks/results/prune_nvalue_NEW_LABEL
```

For separate root allocation records, use `benchmarks.csp_followup diagnose
--only nvalue/ --allocation --nodes 1 --seconds 20 --hard-seconds 30`, once with
`--candidate-nvalue decomposed` and once with `--candidate-nvalue native`, each
writing to a new output directory. The reference encoding defaults to decomposed
so archived runtimes predating native NValue remain usable. The candidate defaults
to native. Direct bridge workers accept `--nvalue native|decomposed`.
