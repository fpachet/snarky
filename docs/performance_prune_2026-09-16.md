# Prune / Snarky benchmark baseline — 16 September 2026

This portfolio runs the same FlatZinc JSON input through Prune and Snarky's native
finite CSP/optimization API. It exercises pure CSP without forward chaining.
The runtime is unchanged: this addition comprises fixtures, a strict benchmark
adapter, a measurement collector, correctness tests, and recorded evidence.

At the common five-second limit, **Prune completes 59/59 workloads; Snarky
completes 47/59**, in all three measured repetitions. Snarky proves three of five
optimization cases; Prune proves all five. Prune has lower median process time
on every mutually completed workload. Snarky's 12 remaining workloads time out;
none produces an incorrect result or an unsupported-input outcome in this run.

Python startup dominates the smallest Snarky runs (roughly 0.12 s versus
0.003–0.004 s for Prune), but it does not explain the larger gaps: FT06
optimization takes 2.739 s versus 0.0085 s, with 2.618 s spent inside Snarky's
native preparation/search alone. Queens 50 takes 1.315 s versus 0.0116 s;
queens 104/150 exceed Snarky's limit. This is a useful correctness and regression
baseline, but Snarky is not yet competitive with Prune on this general CSP portfolio.

## Coverage and provenance

Prune revision `d82c64c29e823513845e56a54e22e21606c0698c` contains **54 of the
85 requested instances**, corresponding to **59 instance/mode workloads**.
Five initial instances run in both first-solution and all-solutions modes.

| Requested family | Requested | Imported | Notes |
|---|---:|---:|---|
| CSPLib | 20 | 0 | All-interval 8/10/11/12/14; Langford 7/8/10/12/20; QG3 4–8; Schur (3,13)/(3,14)/(4,30)/(4,35)/(4,40): upstream definitions unavailable at this revision |
| Extended | 25 | 25 | Magic squares/sequences, Golomb, FT06, missionaries, packing, BIBD, Sudoku, queens |
| Optimization | 5 | 5 | Two Golomb, FT06, packing, knapsack |
| All-different | 9 | 9 | Six global/pairwise cases and three incremental Latin squares |
| NValue | 6 | 6 | Permutation, pigeonhole, four Dominating Queens cases |
| Large domains | 2 | 2 | Both fully solved by the compiler; no native domain-storage measurement |
| Initial | 7 | 7 | Twelve instance/mode workloads |
| Reserved validation | 11 | 0 | Parameters and models unavailable; not invented or used for tuning |

The pinned repository, its only available remote branch (`main`), and all 14
commits in its fetched history were checked.
The two absent suites require an additional revision or source bundle before a
complete 85-instance comparison is possible. Standard problem names alone do
not establish identical formulations, symmetry breaking or reserved parameters.

The [fixture snapshot](../benchmarks/data/prune_d82c64c/README.md) retains
unmodified models, parameters, manifests, MIT/Apache-2.0 licenses and file hashes.
A one-line MiniZinc syntax correction is applied only to temporary Dominating
Queens models and recorded in each result. Both engines receive the same
corrected compiled artifact.

## Protocol and semantic checks

- Apple M1 Pro, 32 GiB RAM, macOS; Python 3.13.11; Rust 1.88.0 release build
  (`cargo build --locked --release -p prune-flatzinc`); MiniZinc 2.9.7, Gecode 6.3.0.
- One discarded warmup, three measured fresh processes per engine/workload,
  alternating engine order, fixed `PYTHONHASHSEED=0`, five-second external wall
  limit. Runs are sequential; regression tests do not overlap final measurement.
  Background load, power mode and thermal state are not controlled. Three samples
  provide descriptive medians, not confidence intervals.
- Primary timing includes process startup/imports, JSON parsing, model preparation,
  search, rendering, and Snarky's original-primitive checks. Compilation, output
  normalization and external Gecode validation are outside the measured interval.
  Snarky's bridge-construction time and native solve time are recorded separately;
  native solve time includes native preparation. Neither is directly comparable
  with Prune's process time.
- Snarky uses `dom_wdeg` and declared ascending values; it does not translate
  FlatZinc search annotations. Prune retains its annotations/default automatic
  portfolio. These are solver comparisons with different search policies, not
  measurements of identical search trees or of Python versus Rust alone.
- Gecode solves each original MiniZinc instance independently. Returned first
  solutions and optimization solutions are fixed back into that original model
  and checked. All-solutions cases compare complete normalized solution sets.
  Unsatisfiability must match Gecode. Optimization requires completion and the
  manifest's certified target: Golomb 17/25, FT06 55, packing 6, knapsack 111.
- The upstream Golomb optimization models include certified sub-ruler lower
  bounds, including **17/25 for the whole ruler**. Finding a ruler at that bound
  closes the proof. These cases measure optimization with a supplied strong
  bound, not independent discovery of the classical Golomb optima.
- A timeout is neither infeasibility nor an optimality proof. The hard cap kills
  the process group; no incumbent is assumed when buffered output is lost.
  Unsupported bridge constructs are a separate outcome. Ratios are emitted only
  when every repetition finishes for both solvers. CSV PAR2 assigns twice the cap
  to timeouts and excludes unsupported outcomes.

The [bridge](../benchmarks/prune_bridge.py) supports the exact primitive subset
encountered here and rejects unknown predicates. Native sums, comparisons and
all-different are used directly. NValue is an explicit incidence-table/Boolean
sum decomposition; the exact distinct-count-equals-variable-count case specializes
to all-different. Thus Dominating Queens compares Prune's native NValue against a
Snarky decomposition. It is not evidence of a native Snarky NValue propagator.

Explicit domain limits prevent allocations above 10,000 values per variable or
1,000,000 in total, and generic table lowering is capped at 250,000 candidate
tuples. A unit test confirms rejection of a raw billion-value domain. Both
upstream large-domain chains have **zero variables and zero constraints after
MiniZinc compilation** because all values follow from the anchored chain; their
successful runs cannot establish billion-domain support for either solver.

## Results

All counts below require completion in **all three measured repetitions**.

| Suite | Workloads | Prune completed | Snarky completed |
|---|---:|---:|---:|
| initial | 12 | 12 | 11 |
| extended | 25 | 25 | 21 |
| optimization | 5 | 5 | 3 |
| all_different | 6 | 6 | 5 |
| incremental_all_different | 3 | 3 | 3 |
| nvalue | 6 | 6 | 2 |
| large_domains | 2 | 2 | 2 |
| **Total** | **59** | **59** | **47** |

These counts include the two compiler-solved chains and repeated parameters in
different suite entries; they are workload counts, not independent problem families.

**Every workload** is retained below. Times are median seconds. Snarky native
time excludes Python startup and bridge construction but includes native model
preparation and search. It is a diagnostic column, not the denominator of a
Prune speedup claim. The full CSV also retains bridge preparation times.

| Instance | Mode | Prune process | Snarky process | Snarky native | Snarky outcome |
|---|---|---:|---:|---:|---|
| initial/booleans | first | 0.0035 | 0.1190 | 0.0002 | satisfiable |
| initial/booleans | all | 0.0031 | 0.1197 | 0.0003 | complete |
| initial/latin_square | first | 0.0034 | 0.1228 | 0.0009 | satisfiable |
| initial/latin_square | all | 0.0033 | 0.1196 | 0.0018 | complete |
| initial/linear | first | 0.0033 | 0.1201 | 0.0003 | satisfiable |
| initial/linear | all | 0.0034 | 0.1180 | 0.0003 | complete |
| initial/magic_square | first | 0.0034 | 0.1275 | 0.0029 | satisfiable |
| initial/magic_square | all | 0.0035 | 0.1296 | 0.0100 | complete |
| initial/pigeonhole | all | 0.0036 | 0.1253 | 0.0001 | unsat |
| initial/queens | first | 0.0033 | 0.1289 | 0.0028 | satisfiable |
| initial/queens | all | 0.0038 | 0.1333 | 0.0089 | complete |
| initial/queens_104 | first | 0.0150 | >5 s (timeout) | — | timeout |
| extended/magic_square_4 | first | 0.0037 | 0.1640 | 0.0448 | satisfiable |
| extended/magic_square_5 | first | 0.0038 | >5 s (timeout) | — | timeout |
| extended/magic_square_3 | first | 0.0035 | 0.1233 | 0.0032 | satisfiable |
| extended/magic_sequence_10 | first | 0.0037 | 0.1584 | 0.0331 | satisfiable |
| extended/magic_sequence_20 | first | 0.0049 | 1.1680 | 1.0415 | satisfiable |
| extended/magic_sequence_40 | first | 0.0095 | >5 s (timeout) | — | timeout |
| extended/golomb_6 | first | 0.0037 | 0.1312 | 0.0059 | satisfiable |
| extended/golomb_7 | first | 0.0039 | 0.2071 | 0.0843 | satisfiable |
| extended/golomb_8 | first | 0.0073 | 0.6484 | 0.5303 | satisfiable |
| extended/jobshop_ft06_55 | first | 0.0042 | 0.2844 | 0.1609 | satisfiable |
| extended/jobshop_ft06_60 | first | 0.0041 | 1.4152 | 1.2941 | satisfiable |
| extended/missionaries_11 | first | 0.0048 | 0.2490 | 0.1233 | satisfiable |
| extended/missionaries_13 | first | 0.0052 | 0.2992 | 0.1683 | satisfiable |
| extended/missionaries_15 | first | 0.0057 | 0.3569 | 0.2229 | satisfiable |
| extended/bin_packing_20 | first | 0.0036 | 0.2418 | 0.1182 | satisfiable |
| extended/bin_packing_30 | first | 0.0043 | 0.6967 | 0.5736 | satisfiable |
| extended/bin_packing_40 | first | 0.0048 | 1.9612 | 1.8371 | satisfiable |
| extended/bibd_7 | first | 0.0044 | 0.1640 | 0.0310 | satisfiable |
| extended/bibd_9 | first | 0.0060 | 0.3857 | 0.2553 | satisfiable |
| extended/sudoku_easy | first | 0.0038 | 0.1310 | 0.0072 | satisfiable |
| extended/sudoku_medium | first | 0.0041 | 0.1274 | 0.0054 | satisfiable |
| extended/sudoku_hard | first | 0.0040 | 0.1859 | 0.0560 | satisfiable |
| extended/queens_50 | first | 0.0116 | 1.3150 | 1.1895 | satisfiable |
| extended/queens_104 | first | 0.0144 | >5 s (timeout) | — | timeout |
| extended/queens_150 | first | 0.0296 | >5 s (timeout) | — | timeout |
| optimization/golomb_opt_6 | first | 0.0037 | 0.1310 | 0.0116 | optimal |
| optimization/golomb_opt_7 | first | 0.0043 | 0.2707 | 0.1466 | optimal |
| optimization/jobshop_ft06_opt | first | 0.0085 | 2.7389 | 2.6178 | optimal |
| optimization/knapsack_20_opt | first | 0.0185 | >5 s (timeout) | — | timeout |
| optimization/bin_packing_20_opt | first | 4.7690 | >5 s (timeout) | — | timeout |
| all_different/all_different_global_10 | first | 0.0041 | 0.1217 | 0.0002 | unsat |
| all_different/all_different_global_12 | first | 0.0041 | 0.1288 | 0.0002 | unsat |
| all_different/all_different_global_16 | first | 0.0037 | 0.1190 | 0.0004 | unsat |
| all_different/all_different_pairwise_10 | first | 0.1018 | >5 s (timeout) | — | timeout |
| all_different/all_different_permutation_global_16 | first | 0.0042 | 0.1286 | 0.0068 | satisfiable |
| all_different/all_different_permutation_pairwise_16 | first | 0.0039 | 0.1453 | 0.0209 | satisfiable |
| incremental_all_different/all_different_incremental_10 | first | 0.0045 | 0.2019 | 0.0738 | satisfiable |
| incremental_all_different/all_different_incremental_12 | first | 0.0082 | 0.3038 | 0.1707 | satisfiable |
| incremental_all_different/all_different_incremental_16 | first | 0.0166 | 0.8103 | 0.6859 | satisfiable |
| nvalue/nvalue_permutation_16_sat | first | 0.0058 | 0.1280 | 0.0069 | satisfiable |
| nvalue/nvalue_pigeonhole_16_unsat | first | 0.0039 | 0.1287 | 0.0001 | unsat |
| nvalue/nvalue_queens_6_sat | first | 0.0059 | >5 s (timeout) | — | timeout |
| nvalue/nvalue_queens_7_sat | first | 0.0271 | >5 s (timeout) | — | timeout |
| nvalue/nvalue_queens_6_unsat | first | 0.0048 | >5 s (timeout) | — | timeout |
| nvalue/nvalue_queens_8_sat | first | 0.0544 | >5 s (timeout) | — | timeout |
| large_domains/large_domain_chain_256 | first | 0.0039 | 0.1226 | 0.0000 | satisfiable |
| large_domains/large_domain_chain_2048 | first | 0.0040 | 0.1276 | 0.0001 | satisfiable |

## Reproduction and archived evidence

[results.json](../benchmarks/results/prune_comparison_2026-09-16/results.json)
contains every measured and warmup sample, normalized solutions, Gecode checks,
compiled input hashes, solver commands, native counters and environment metadata.
[summary.csv](../benchmarks/results/prune_comparison_2026-09-16/summary.csv) is the
complete per-workload summary. The adjacent `artifacts/` directory retains the
compiled inputs and output specifications; `sources.tar.gz` freezes the Snarky
runtime, adapter, collector and fixture snapshot actually measured. The record
identifies the parent commit and dirty checkout; archived source hashes identify
the new uncommitted harness precisely. The Prune binary hash is also recorded.

```sh
git clone git@github.com:ynosound-dev/prune.git /tmp/prune-comparison
git -C /tmp/prune-comparison checkout d82c64c29e823513845e56a54e22e21606c0698c
cargo build --locked --release --manifest-path /tmp/prune-comparison/Cargo.toml -p prune-flatzinc
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.prune_comparison \
  --prune /tmp/prune-comparison/target/release/prune-fzn \
  --minizinc /Applications/MiniZincIDE.app/Contents/Resources/minizinc \
  --output benchmarks/results/prune_comparison_NEW_LABEL \
  --seconds 5 --warmups 1 --repeats 3 \
  --machine-notes 'Record CPU, RAM, power and background conditions here'
```

The collector refuses to overwrite a result directory. Use `--only optimization/`
or another ID substring for a focused rerun. The common five-second protocol
intentionally differs from some upstream manifest defaults (often 30 seconds);
these measurements must not be silently combined with upstream timing tables.

## Validation and next measurements

The non-Bach regression run passed **966 tests, with three skips**, in 219.15 s.
The final focused bridge/collector suite passed **47 tests**, including exhaustive
primitive/decomposition oracles, aliasing, constants, Boolean channeling, NValue,
optimization, budget rejection, provenance hashes and rejection of false or
incomplete proofs. Ruff passes. A Python 3.12 magic-square smoke run also passed;
the full pytest suite was run under Python 3.13, not 3.12.
Commands and outcomes are retained in the
[validation record](../benchmarks/results/prune_comparison_2026-09-16/validation.json)
and adjacent regression log.

The first follow-up should profile native preparation, propagation and search
separately on the cases that miss the cap. Then compare bounded linear filtering,
native NValue, compact domains, cheaper all-different updates, and search-policy
changes as separate candidates. Scheduling and packing may benefit from stronger
problem-specific globals rather than only faster linear decompositions. Do not
attribute a timeout to one propagator without profiling and ablation.

Preserve this baseline and the original rule/CSP/mixed regression portfolios.
Freeze each candidate before running the missing reserved validation suite when
its definitions become available. Keep compiler-solved and startup-dominated
cases visible, but do not use them as evidence of native large-domain capacity
or propagator throughput. No generic runtime optimization is bundled into this
baseline addition.
