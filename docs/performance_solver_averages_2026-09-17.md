# Current Prune and CLAIRE averages — 17 September 2026

This record predates compiled all-different masks and is preserved. The
[newer measurements](performance_csp_alldifferent_masks_2026-09-17.md#updated-averages)
record updated averages and a separate CLAIRE rerun after that optimization.

Snarky remains slower on these recorded workloads. The latest numeric changes
reduce arithmetic propagation cost, but they do not remove the seven outstanding
Prune-portfolio timeouts. This report records the aggregate comparison and a fresh
CLAIRE rerun against clean Snarky commit `690d8b8`, including the numeric-mask change.

## Average times

For each workload, take the median of three measured runs, excluding the warmup.
Then take the arithmetic mean of those medians, giving each workload equal weight.
The multiplier below is the ratio of the two averages, not the arithmetic mean
of individual workload ratios. All displayed times are milliseconds.

| Comparison | Workloads | Snarky average ms | Other solver average ms | Snarky / other |
| --- | ---: | ---: | ---: | ---: |
| Prune: jointly completed CSP workloads | 52 | 179.61 | 6.34 | 28.34× |
| CLAIRE: queens, native CSP | 4 | 26.52 | 2.79 | 9.51× |
| CLAIRE: Talarian rules | 2 | 203.67 | 9.12 | 22.34× |
| CLAIRE: triangle closure | 2 | 221.00 | 83.99 | 2.63× |
| CLAIRE: queens, historical rule/choice | 4 | 825.24 | 2.79 | 296.08× |

**Prune:** the average includes only the 52 workloads both engines complete in all
three repetitions. Snarky completes **52/59**, Prune **59/59**; optimization proofs
are **3/5 versus 5/5**. The seven Snarky timeouts are excluded, not counted as
five-second solutions. This completed-subset average therefore does not represent
the whole portfolio. It includes the two compiler-solved chain cases; excluding
them gives 181.91 ms versus 6.44 ms, a 28.24× ratio over 50 workloads.

Prune times include process startup, preparation, search and output. Prune is
compiled Rust. Python startup is substantial on the small Snarky cases; these
numbers do not isolate language cost or algorithm quality. The same-input models,
validation and coverage limits are described in the
[numeric report](performance_csp_numeric_2026-09-17.md).

**CLAIRE:** times cover internal search/inference, excluding startup and preparation.
CLAIRE runs through its bundled interpreter. Queens uses sizes 8, 10, 12 and 14;
Talarian uses 100 and 1,000 frames; triangle closure uses 25 and 100 groups.
Native Snarky queens uses stronger global constraints than the historical
rule/choice and specialized CLAIRE formulations. The rule workloads also use
different matching algorithms. These are comparisons of the implemented
formulations, not controlled language benchmarks. Do not combine the Prune and
CLAIRE rows into one overall average: their workloads and timing boundaries differ.

## Fresh CLAIRE details

One discarded warmup and three repetitions use fresh workers, alternating engine
order, sequentially. Every sample passes the existing independent validators;
results and counters remain stable across repetitions. Historical rule/choice
queens solutions match CLAIRE; the native-global formulation is validated as a
chessboard independently. No solver source changed during collection, and its
source digest still matched when the records were moved into the repository.

| Queens size | Snarky rule/choice ms | CLAIRE interpreted ms | Snarky native CSP ms |
| --- | ---: | ---: | ---: |
| 8 | 252.23 | 1.72 | 18.18 |
| 10 | 290.67 | 1.05 | 10.99 |
| 12 | 1291.57 | 4.24 | 38.98 |
| 14 | 1466.49 | 4.15 | 37.91 |

| Rule workload | Snarky ms | CLAIRE interpreted ms | Snarky / CLAIRE |
| --- | ---: | ---: | ---: |
| talarian 100 | 34.08 | 1.67 | 20.46× |
| talarian 1000 | 373.27 | 16.56 | 22.53× |
| triangles 25 | 88.54 | 12.14 | 7.29× |
| triangles 100 | 353.45 | 155.84 | 2.27× |

CLAIRE checkout: `25b14968e1eef80269d56af418eda7d2ccd88cbf`, clean.
The interpreter SHA-256 is
`1620feffa26215999a1f38fa1d1cc5d116a150cfa813d7f895b2f9fd1fdded78`, unchanged
from the preceding comparison. The [16 September report](performance_claire_2026-09-16.md)
remains a historical record. These are descriptive three-run measurements on
this machine, without confidence intervals or controlled background load.

## Evidence and reproduction

- [Prune samples and validation](../benchmarks/results/prune_numeric_2026-09-17/results.json)
- [Prune per-workload medians](../benchmarks/results/prune_numeric_2026-09-17/summary.csv)
- [Fresh CLAIRE samples, commands, environment and binary hashes](../benchmarks/results/claire_numeric_2026-09-17/results.json)
- [CLAIRE-run Snarky source archive](../benchmarks/results/claire_numeric_2026-09-17/snarky_sources.tar.gz)
- [Machine-readable averages and input hashes](../benchmarks/results/claire_numeric_2026-09-17/averages.json)

The records were collected under `/tmp` and then copied unchanged into the
repository; recorded output command paths retain their original locations.
No runtime code changed for this documentation update, so no new full regression
suite was required. The measurement collector checked outputs and source/binary
stability; the aggregates were calculated from the saved records.

To refresh CLAIRE, use a new output directory:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.claire_refresh \
  --claire-root ../CLAIRE4 --repeats 3 \
  --output benchmarks/results/claire_refresh_NEW_LABEL
```

For the averages, group Prune CSV rows by `(instance, mode)`, retain groups where
both engines finish all three repetitions, and average `median_process_seconds`
by engine. For CLAIRE, group `cases` by `family` and average `median_seconds` for
the selected Snarky formulation and `claire`. The JSON summary records both means
and their ratio at full precision.
