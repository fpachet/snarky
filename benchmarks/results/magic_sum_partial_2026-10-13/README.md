# Partial sum certification experiment

**Decision: keep the existing production kernel.** Both prototypes preserve exact
supports, but neither gives a consistent improvement on the tested magic squares.
The code is retained here for explicit experimental use.

This study follows the [dense-sum optimization](../magic_sum_dense_2026-10-13/README.md).
It does not replace those production results.

## What was tried

1. **Skip individual support checks.** Certify an interior range of candidates,
   check the rest exactly, and keep all candidates in the full reachable-sum
   tables. This saves some checks but retains most table-building work.
2. **Compute only uncertain edges.** Use the same interior certificate and build
   exact reachable-sum tables only for the small lower and upper edge bands.
   Any assignment reaching an edge sum can use only nonnegative normalized
   offsets within that band, so the truncation is exact.

Certified values remain available in reachability calculations. Neither version
uses witness caches or persistent partial-support state. Both recompute from the
current masks and retain the existing exact fallback when the certificate fails.

The prototypes require at least four unfixed variables and 64 candidate entries;
they also require at least 64 certified entries to use the partial result. The
edge version additionally checks an estimated table-work budget. These are
experimental cost gates, not correctness assumptions or validated optimal thresholds.

## Magic-square timings

Median seconds from three sequential repetitions per version. This table compares
the production kernel with the second, edge-band prototype. Setup and search are
included; imports, validation, and diagnostic instrumentation are excluded.

| Square | Production | Edge-band prototype | Measurement |
|---|---:|---:|---|
| 6×6 | 0.057 s | 0.054 s | Complete solve |
| 8×8 | 0.130 s | 0.131 s | Complete solve |
| 9×9 | 2.272 s | 2.303 s | Complete solve |
| 10×10 | 0.274 s | 0.275 s | Complete solve |
| 11×11 | 0.466 s | 0.483 s | Complete solve |
| 12×12 | 0.559 s | 0.558 s | Complete solve |
| 13×13 | 2.341 s | 2.368 s | Complete solve |
| 14×14 | 1.206 s | 1.226 s | Complete solve |
| 16×16 | 6.994 s | 7.003 s | Complete solve |
| 15×15 | 0.688 s | 0.701 s | First 80 nodes only |
| 18×18 | 0.786 s | 0.781 s | First 30 nodes only |
| 20×20 | 1.235 s | 1.191 s | First 30 nodes only |

The small improvements and regressions are inconsistent across workloads and
often overlap the observed timing spread. They do not justify adding this code
to the default solver. The first prototype likewise shows no consistent gain;
its individual measurements are retained separately.

All **144 comparison runs** preserve nodes, failures, revisions, termination,
and returned squares, including between prototypes. All **108 returned squares**
were independently validated. The bounded rows do not measure completed solves.

## Why the gains are limited

Separate outcome-counting runs show that the edge-band shortcut is rarely used:

| Square | Sum-kernel calls | Partial results used |
|---|---:|---:|
| 9×9 | 40,680 | 0 |
| 12×12 | 3,139 | 1 |
| 13×13 | 19,603 | 0 |
| 16×16 | 40,047 | 3 |

The existing full-domain certificate already handles many favorable states.
The remaining states rarely meet the partial certificate and cost gates, while
checking eligibility adds overhead. These counts are excluded from the timings.

A deliberately favorable synthetic equality shows that the edge method itself
can help: four domains `0..w` with `1` removed, and target `w`.

| Width `w` | Previous kernel | Edge-band kernel | Speedup |
|---|---:|---:|---:|
| 30 | 36.2 µs | 16.0 µs | 2.26× |
| 120 | 161.3 µs | 18.4 µs | 8.78× |

These are direct **uncached support-kernel** measurements. They exclude setup,
bypass unchanged-query caching, and are not complete solve timings or evidence
of generalization to other CSPs.

## Files and validation

- [summary.json](summary.json): decision, both timing comparisons, diagnostic counts, and validation details.
- [comparison_backward/runs.jsonl](comparison_backward/runs.jsonl): 72 runs of the first prototype.
- [comparison_edges/runs.jsonl](comparison_edges/runs.jsonl): 72 runs of the edge-band prototype.
- [usage_counts.json](usage_counts.json) and [synthetic_micro.json](synthetic_micro.json): separate diagnostic and synthetic measurements.
- [numeric_before.py](numeric_before.py), [candidate_backward.py](candidate_backward.py), and [candidate_edges.py](candidate_edges.py): exact source snapshots.
- [runner_snapshot.py.txt](runner_snapshot.py.txt), [diagnose_snapshot.py.txt](diagnose_snapshot.py.txt), and [tests_candidate.py.txt](tests_candidate.py.txt): historical execution and test snapshots. The diagnostic snapshot records the prototype execution context; it is not a standalone command against the restored production source.
- [Experimental tests](../../../experiments/neural_attention/test_sum_partial.py): explicitly load the edge prototype and compare it with the production kernel and independent oracles.

Before restoring production, the edge prototype passed **1,225 non-slow core
tests**, with four skips and 58 slow tests deselected, plus type checking of 103
runtime files. After restoring production byte for byte, 12 explicit
baseline/candidate experimental cases and 37 existing experiment tests pass.
Tests cover boundary holes, certified values supporting uncertain values, zero
certificate margin, signed contributions, huge translations, and sibling rollback.

## Reproduce

Run from the repository root, with a fresh output directory. The runner applies
the experimental method only within the benchmark and restores the original
method afterward; the production source file is not changed.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_alldifferent_benchmark \
  --kernel sum \
  --before benchmarks/results/magic_sum_partial_2026-10-13/numeric_before.py \
  --candidate benchmarks/results/magic_sum_partial_2026-10-13/candidate_edges.py \
  --presets benchmarks/results/magic_sum_dense_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 --repeats 3 \
  --output generated/neural_attention/magic_sum_partial_NEW
```

Use `candidate_backward.py` to compare the first prototype. Run the isolated
correctness checks with:

```sh
PYTHONPATH=src:. .venv/bin/python -m pytest \
  experiments/neural_attention/test_sum_partial.py
```
