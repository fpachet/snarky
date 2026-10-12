# Further native magic-square optimization

12 October 2026. A value-order change and a small general propagation shortcut
bring blank 7×7 first-solution time to **about 1.10 seconds**, compared with the
previous 1.47-second result. No neural model or additional constraints are used.
The five explicit blank-square symmetry inequalities remain enabled.

## Retained changes

For 7×7, keep MRV with row-major variable ties, but try the higher value first
when two values are equally close to the midpoint: `25, 26, 24, 27, 23, …`.
This changes declared value ordering only. It reduces the symmetry-restricted
search from 2,114 nodes/42,239 revisions to 1,628 nodes/32,667 revisions.
It remains an explicit experimental setting, not a generic search default.

The compiled n-ary equality propagator now skips fixed contributions in its
reachable-sum tables. With zero unfixed variables it checks the fixed sum; with
one it looks up the required value; with two it scans the smaller domain and
looks up complementary contributions. Three or more unfixed variables use the
existing exact prefix/suffix method, with tables built only for those variables.
All paths retain exact independent-variable supports, signed coefficients,
arbitrary-size translations, mask/target caching, rollback, and existing budgets.
The shortcut is enabled through the existing default numeric masks.

This is beneficial on the measured cases but smaller than the value-order gain.
The 6×6 setting should keep lower-first midpoint ties: higher-first raises its
search from 90 to 194 nodes. No single new value order is enabled for all sizes.

## Measurements

A 24-run pilot tests four value policies, three MRV tie orders, and symmetry
on/off, with a two-second limit. Degree-first ties and value orders based on
current line averages or other domains' midpoints fail to beat the existing
setting within that budget. Larger-first midpoint ties with row-major MRV and
symmetry finish in 1.176 seconds including setup. Three subsequent repetitions
give 1.137 seconds versus 1.473 seconds for the existing value order before the
kernel change. After the change, three repetitions give 1.122 and 1.421 seconds,
respectively. Those pilot-selected repetitions are exploratory, not held-out
problem tests.

A separate ablation shuffles five repetitions of each size/order/kernel
combination: **40 runs**. It temporarily swaps only `_equality_supports` between
the saved previous implementation and the current implementation in the
benchmark process. All other state, propagation, search, and model code is the
same, with a fresh state per solve. Every run completes within its ten-second
allowance. Times include model construction, ordering, symmetry construction,
state setup, propagation, and search; validation/imports are excluded.

| Size and midpoint tie | Previous kernel | Current kernel | Runtime reduction |
|---|---:|---:|---:|
| 6×6 lower-first | 0.0636 s | **0.0621 s** | 2.3% |
| 6×6 higher-first | 0.1270 s | 0.1216 s | 4.2% |
| 7×7 lower-first | 1.5168 s | 1.4556 s | 4.0% |
| 7×7 higher-first | 1.1528 s | **1.0953 s** | 5.0% |

These are medians of five runs. Previous and current kernels return identical
solutions, node counts, and revision counts for each size/order combination.
The existing and revised 7×7 settings differ in both value order and kernel:
the same ablation measures 1.517 versus 1.095 seconds, about 28% less time.
Against the historical 1.47-second result, the new roughly 1.10-second time is
about 25% lower. Millisecond changes and small percentages remain sensitive to
machine load; the larger value-order effect also reduces search counters.

Every square passes the original-model validator and separate integer range,
distinctness, row/column, and diagonal checks. The run uses `PYTHONHASHSEED=0`
and sequential timing, with no concurrent CPU tests. Source hashes and settings
are frozen before measurements. There are only two blank problems here;
repetitions do not establish a population advantage on clued squares or other
CSPs, and the adaptive policies' short timeouts do not establish their eventual
solve times.

## Verification and evidence

**325 focused solver/experiment tests pass, one skipped.** New tests enumerate
all 3×3 solutions under each ordering adapter, check symmetry representatives,
confirm rankings do not mutate domains, and verify restoration after search.
The numeric suite includes exhaustive support oracles for all 64 fixed-variable
patterns of a signed six-variable equality, plus its previous random, sparse,
huge-integer, budget, target-cache, and rollback cases. Mypy checks all 103 runtime
source files; Ruff and Markdown links pass. The full repository application and
release suite was not run.

Raw evidence is under `generated/neural_attention/magic7_tuning/`: `pilot/`,
`before/`, `after/`, `ablation/`, combined `summary.json`, a saved previous
`numeric_before.py`, `baseline.prof`, and `active_arity.json`. The arity diagnostic
counts 5,321 of 33,357 equality-table calls with at most two unfixed variables;
most other calls have only three to five unfixed variables rather than seven.
The saved kernel's hash matches the before-run source hash. After/ablation source
hashes are checked unchanged after timing.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_search_tuning \
  --size 7 --orders middle_high --ties row_major --symmetry only \
  --repeats 5 --limit 10 \
  --output generated/neural_attention/magic7_tuned_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_kernel_ablation \
  --before experiments/neural_attention/fixtures/numeric_before_fixed_terms.py \
  --output generated/neural_attention/magic7_ablation_NEW
```

Output directories must be fresh. The committed fixture contains the unchanged
equality method extracted from the retained local source snapshot; the ablation
records its hash. Generated timing evidence stays local and is not versioned. These scripts do not change the solver's stored defaults
or transfer symmetry constraints to clued puzzles.
