# First-order Blues baseline — 2026-09-16

These are initial application measurements, not a controlled cross-version speedup
study. Each final case has three fresh-state runs, a five-second search budget,
MRV variable selection, objective value ordering, and exact rational arithmetic.
Times include native preparation and search; corpus training and model construction
are recorded separately. This baseline has no isolated memory measurements yet.

## Corrected Boulez alphabet

Boulez training and generation now both use 12 roots × two families (dominant
seventh and minor). All-different on 24 positions requires every chord exactly
once. As requested by the user, the version 2 corpus reduces chord families before
counting transitions. The explicit proposed map sends major to dominant seventh
and diminished/half-diminished to minor, preserving roots. It changes 34 half-bars
in nine references. No historical equivalence of this map is claimed.

The original preflight and count-aware records allowed 60 or 36 generated symbols.
Their Boulez rows are **superseded modeling results**, not valid measurements of
the intended Boulez problem. An intermediate 24-symbol generation-only experiment
retained the larger training alphabets; it is superseded by the requested training
reduction. All records remain archived for traceability. Ordinary and exotic
results remain valid for their respective corpora. These changes are not a solver
speedup claim, and scores from different trained models cannot be compared as
algorithmic improvements.

| Corpus | Control | Median preparation + search | Nodes | Result | Best log score |
|---|---|---:|---:|---|---:|
| Source-faithful | ordinary | 0.965 s | 22 | Proved optimal | -20.536927 |
| Source-faithful | exotic | 1.802 s | 22 | Proved optimal | -28.051704 |
| Three-family proposed | ordinary | 0.650 s | 22 | Proved optimal | -20.428036 |
| Three-family proposed | exotic | 1.200 s | 22 | Proved optimal | -28.191003 |
| Two-family proposed | ordinary | 0.586 s | 22 | Proved optimal | -20.428036 |
| Two-family proposed | exotic | 1.131 s | 22 | Proved optimal | -28.213666 |
| Two-family proposed | boulez | 5.006 s | 6486–6578 | Feasible; time limit, unproved | -63.195230 |

Log scores use natural logarithms for display only. All objective comparisons and
proofs use exact rational products. Corpus variants define different statistical
models: their scores do not establish that one algorithm or corpus is better.

## Independent checks

Each returned sequence is rescored outside the objective implementation and checked
for its anchors, exact count or complete 24-chord Boulez permutation. Native
optima for ordinary and exotic Blues equal an independent exact dynamic program. That DP relaxes
all-different for Boulez Blues and provides only an upper bound for that case.
The DP reference took roughly 7–24 ms for the two tractable cases; the native
controller still has considerable opportunity to reuse a DP witness and messages.

## Earlier bound improvement

The preserved preflight omitted count from its chain relaxation. At five seconds,
both exotic cases were feasible but unproved, after about 6,000 nodes. Adding one
small equality-count state gives proved optima in 22 nodes in all three count-aware runs.
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
- [Earlier three-run count-aware baseline (Boulez superseded)](../benchmarks/results/blues_first_order_2026-09-16_counter.json)
- [Count-aware source snapshot](../benchmarks/results/blues_first_order_2026-09-16_counter.source.tar.gz)
- [Intermediate generation-only experiment (superseded)](../benchmarks/results/blues_first_order_2026-09-16_boulez24.json)
- [Generation-only source snapshot](../benchmarks/results/blues_first_order_2026-09-16_boulez24.source.tar.gz)
- [Two-family training and generation baseline](../benchmarks/results/blues_first_order_2026-09-16_boulez_training24.json)
- [Two-family training source snapshot](../benchmarks/results/blues_first_order_2026-09-16_boulez_training24.source.tar.gz)
- [Corpus audit and proposed simplification](../benchmarks/data/omnibook_blues_v2/README.md)

These records extend the [performance ledger](performance_baseline.md). They do
not replace the frozen rule/CSP/mixed portfolio or establish general performance
promotion. Variable-order scoring and a proved Boulez optimum remain open.

## Validation of this application slice

Before the alphabet correction, the [validation record](../tests/fixtures/blues_validation_2026-09-16.json) reported:
844 non-Bach tests passed, three optional integrations skipped, in 208.17 seconds
on Python 3.13. The 54 focused native/product/corpus/bound tests also passed on
Python 3.12. Ruff, mypy (90 modules), textual formatting, local Markdown links,
distribution-content checks, and isolated wheel/companion checks on both Python
versions passed. These checks include the new rational-product installed example.

The correction changes corpus preparation, application domains and validation;
no engine code changes. The focused product and Blues suite passed 22 tests on
Python 3.13 and Python 3.12, including rejection of both historical out-of-alphabet
incumbents, preservation of the original corpus variants and pooling counts before
training. All 21 fresh benchmark runs passed independent sequence and objective
validation. Ruff and local Markdown link checks also passed. The full suite was
not rerun for this application-only correction.

## Published witness cross-check

Reading Table 5 of the supplied published paper exposed a stronger feasible
sequence under the current two-family model: log score -46.921592, versus
-63.195230 from our five-second search. All 24 symbols, anchors and positive
transitions were independently checked. The [rescoring record](../benchmarks/results/blues_published_witness_2026-09-16.json)
contains exact products and local probabilities for all three corpus variants.
This is an external feasible witness, not a new solver run or proof of optimality.
The measured search has a substantial incumbent-quality gap in addition to its
unresolved proof. Future warm-start runs must be labeled separately. See the
[paper review](markov_paper_review.md) for semantics and validation implications.

The subsequent [Boulez optimization report](performance_boulez_2026-09-16.md)
closes this gap: unseeded search regenerates Table 5 and proves it optimal for the
current two-family corpus. The tables above remain the original baseline.
