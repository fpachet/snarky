# First-order Blues baseline — 2026-09-16

These are initial application measurements, not a controlled cross-version speedup
study. Each final case has three fresh-state runs, a five-second search budget,
MRV variable selection, objective value ordering, and exact rational arithmetic.
Times include native preparation and search; corpus training and model construction
are recorded separately. This baseline has no isolated memory measurements yet.

| Corpus | Control | Median preparation + search | Nodes | Result | Best log score |
|---|---|---:|---:|---|---:|
| Source-faithful | ordinary | 1.058 s | 22 | Proved optimal | -20.536927 |
| Source-faithful | exotic | 1.787 s | 22 | Proved optimal | -28.051704 |
| Source-faithful | boulez | 5.009 s | 4572–4603 | Feasible; time limit, unproved | -54.155994 |
| Proposed paper-style | ordinary | 0.661 s | 22 | Proved optimal | -20.428036 |
| Proposed paper-style | exotic | 1.201 s | 22 | Proved optimal | -28.191003 |
| Proposed paper-style | boulez | 5.006 s | 5995–6052 | Feasible; time limit, unproved | -56.526924 |

Log scores use natural logarithms for display only. All objective comparisons and
proofs use exact rational products. Corpus variants define different statistical
models: their scores do not establish that one algorithm or corpus is better.

## Independent checks

Each returned sequence is rescored outside the objective implementation and checked
for its anchors, exact count or all-different property. Native optima for ordinary
and exotic Blues equal an independent exact dynamic program. That DP relaxes
all-different for Boulez Blues and provides only an upper bound for that case.
The DP reference took roughly 7–24 ms for the two tractable cases; the native
controller still has considerable opportunity to reuse a DP witness and messages.

## First bound improvement

The preserved preflight omitted count from its chain relaxation. At five seconds,
both exotic cases were feasible but unproved, after about 6,000 nodes. Adding one
small equality-count state gives proved optima in 22 nodes in all three final runs.
The initial preflight has one sample per case and no fixed hash seed; therefore
we report the changed proof outcome and work counts, not a timing speedup factor.
Boulez remains limited because the chain relaxation omits distinctness.

## Reproduction and raw evidence

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.blues_markov \
  --repeat 3 --seconds 5 --output /tmp/blues_new_record.json
```

The collector refuses to overwrite records. It records source hashes, corpus hash,
environment, commit/dirty state, full incumbent histories, bounds, local probabilities
and sequences. The final collector checks its sources did not change during the run.

- [Initial preflight](../benchmarks/results/blues_first_order_2026-09-16_pre_counter.json)
- [Preflight source snapshot](../benchmarks/results/blues_first_order_2026-09-16_pre_counter.source.tar.gz)
- [Three-run count-aware baseline](../benchmarks/results/blues_first_order_2026-09-16_counter.json)
- [Count-aware source snapshot](../benchmarks/results/blues_first_order_2026-09-16_counter.source.tar.gz)
- [Corpus audit and proposed simplification](../benchmarks/data/omnibook_blues_v1/README.md)

These records extend the [performance ledger](performance_baseline.md). They do
not replace the frozen rule/CSP/mixed portfolio or establish general performance
promotion. Variable-order scoring and a proved Boulez optimum remain open.

## Validation of this application slice

[Validation record](../tests/fixtures/blues_validation_2026-09-16.json):
844 non-Bach tests passed, three optional integrations skipped, in 208.17 seconds
on Python 3.13. The 54 focused native/product/corpus/bound tests also passed on
Python 3.12. Ruff, mypy (90 modules), textual formatting, local Markdown links,
distribution-content checks, and isolated wheel/companion checks on both Python
versions passed. These checks include the new rational-product installed example.
