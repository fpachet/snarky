# Refreshed CLAIRE comparisons — 16 September 2026

This historical record is preserved. The
[17 September refresh and averages](performance_solver_averages_2026-09-17.md)
measure the current numeric-mask runtime and retain new raw samples separately.

This refresh preserves the existing CLAIRE4 workloads and adds an explicitly
separate Snarky native-global queens formulation. Historical July measurements
remain unchanged. The current collector is
[`benchmarks.claire_refresh`](../benchmarks/claire_refresh.py).

## What is compared

The historical queens comparison finds a first solution with minimum-remaining
values, numeric column/row tie-breaking, singleton propagation and no symmetry
breaking. Snarky uses its rule/choice engine; CLAIRE uses the bundled interpreter
with reversible tables specialized to the board size. Their first solutions must
match. Search counters are retained under engine-specific names because a CLAIRE
branch attempt is not the same observation as a Snarky explored node.

The native Snarky variant models the same valid chessboards with three exact
all-different constraints (rows and both diagonals) and affine channels between
queen rows and diagonal variables. It uses MRV and ascending values, declaring
queen variables before auxiliaries. This has stronger propagation and a different
representation from the historical singleton-rule formulation. Its valid first
solution need not match the other two. It is a practical native-CSP comparison,
not a claim of identical solver work or a measurement of rule-matcher speed.

The rule controls retain their existing semantics:

- **Talarian:** ten independent event rules per frame, with exact firing/output
  counts and checksum validation. This measures direct event filtering, not a
  general multi-relation join. Snarky's event specialization is enabled.
- **Triangle closure:** streamed closing edges in independent groups of width
  eight, with matching output/firing counts and checksums. Snarky uses indexed,
  factorized event matching; the CLAIRE formulation scans hubs after an edge
  update. Those different algorithms are part of what the workload compares.

## Protocol and limits

Each case has one discarded warmup and three measured repetitions, with fresh
workers and alternating engine order. Runs are sequential and do not overlap
CSP benchmarks or tests. Timings cover internal search/inference; startup and
source loading are excluded. Preparation is reported separately. Native queens
also reports construction time separately. Model construction boundaries differ
between engines, so these are not end-to-end application latency comparisons.

Every sample is independently checked by the existing workload validators.
Results and counters must remain stable across repetitions. The native-global
queens model also passes exhaustive board-set tests for sizes one through five,
including unsatisfiable cases and projection uniqueness.

The record includes the CLAIRE checkout revision and dirty flag, the executed
binary's SHA-256, the exact `.cl` templates, Snarky source archive/hash, all worker
commands and all samples. CLAIRE is run **interpreted**; these timings do not
establish the performance of a compiled CLAIRE program. They also do not isolate
Python overhead or support a universal ranking of the two languages. Three-sample
medians are descriptive; background load and thermal conditions are uncontrolled.

## Results

The [complete record](../benchmarks/results/claire_refresh_2026-09-16/results.json)
contains all samples and engine-specific counters. Times below are medians of
three internal measurements, in milliseconds; smaller is better.

| Queens size | Snarky rule/choice ms | CLAIRE interpreted ms | Snarky native globals ms |
| --- | ---: | ---: | ---: |
| 8 | 258.89 | 1.68 | 21.40 |
| 10 | 289.02 | 1.04 | 13.31 |
| 12 | 1359.03 | 4.31 | 46.37 |
| 14 | 1499.68 | 4.26 | 45.44 |

Native globals solve these queens models substantially faster than Snarky's
historical rule/choice formulation, but CLAIRE's specialized interpreted model
remains faster in every case. This is a comparison of current formulations;
it does not measure the incremental all-different patch against an older Snarky
runtime. That question is answered by the
[paired CSP experiment](performance_csp_alldiff_2026-09-16.md).

| Rule workload | Snarky ms | CLAIRE interpreted ms | Snarky / CLAIRE |
| --- | ---: | ---: | ---: |
| Talarian frames 100 | 37.46 | 1.71 | 21.9× |
| Talarian frames 1000 | 382.73 | 16.89 | 22.7× |
| Triangle groups 25 | 88.69 | 12.40 | 7.2× |
| Triangle groups 100 | 361.02 | 161.64 | 2.2× |

CLAIRE also leads both rule workloads here. The gap narrows on the larger
triangle case, whose implementations use different matching algorithms. The
result does not imply equal general-purpose rule performance.

Executed CLAIRE checkout: `25b14968e1eef80269d56af418eda7d2ccd88cbf` (dirty: `false`).
The bundled interpreter's SHA-256 is
`1620feffa26215999a1f38fa1d1cc5d116a150cfa813d7f895b2f9fd1fdded78`.
The checkout was clean. The executed binary and workload-template hashes
provide the concrete measurement identity alongside that revision.

## Reproduction

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.claire_refresh \
  --claire-root ../CLAIRE4 --repeats 3 \
  --output benchmarks/results/claire_refresh_NEW_LABEL
```

Output directories must be new. The original `claire_n_queens`,
`claire_talarian_filter`, and `claire_triangle_closure` runners remain available
unchanged for their historical protocols.
