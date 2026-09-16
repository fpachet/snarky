# Markov constraints implementation progress

Updated 2026-09-16. This records the first fixed-order application slice of the
[action plan](markov_constraints_plan.md); it does not mark the full plan complete.

## Completed in this slice

- Committed the completed native-runtime redesign as `01a0061`, after rerunning
  the non-Bach portfolio: 825 passed, three optional integrations skipped.
- Audited the user-supplied 22 LSDB references, all already in C. Every XML hash,
  root/pitch-class transposition and half-bar boundary passed validation.
- Built source-faithful and proposed paper-style variants with explicit weighting,
  provenance and a review map. The latter changes 31 half-bar positions in nine
  references. Both datasets remain research fixtures outside Python distributions.
- Checked the two concrete corpus examples in the paper: Back Home Blues matches
  after notation normalization; Blues for Alice matches after the proposed
  first-bar major-to-dominant change. Identity of the other historical references
  is not established. No musical correction was silently inferred.
- Added exact rational-product objectives to native branch-and-bound and the
  exhaustive reference. Zero weights, defaults, near-ties, min/max, bounds,
  interruptions and rollback have dedicated tests. Probability measures remain
  separate from optimization objectives.
- Added a first-order MLE trainer, an independent exact DP with an optional count,
  and three native CSP applications: ordinary, exotic, and Boulez Blues.
- Corrected Boulez generation after the user's clarification: 24 symbols from
  dominant seventh/minor families, each used once. At the user's request, version 2
  also reduces training to these families before counting; the explicit review map
  changes 34 half-bars in nine references. Earlier wider-alphabet and intermediate
  generation-only Boulez records are superseded for the headline experiment.
- Added bounded chain compilation and max-product completion bounds. Including
  a small equality count closes the exotic Blues proof in 22 nodes, where the
  initial count-relaxed implementation remained unproved at five seconds.

The importer and its validator use LSDB's structured root, quality, timing and
source fields directly. MuSES is not needed to reconstruct those objects, so no
new music-library dependency was introduced.

## Evidence and limitations

- [Corpus, simplification map and provenance](../benchmarks/data/omnibook_blues_v2/README.md)
- [Performance and raw records](performance_blues_2026-09-16.md)
- [Numeric/API contract](finite_model_contract.md#exact-rational-product-optimization-blues-follow-on)
- [Independent product tests](../tests/test_product_objective.py)
- [Corpus/training/DP tests](../tests/test_blues_markov.py)

Ordinary and exotic Blues have independently confirmed exact optima in both
original variants and the added two-family control. Boulez Blues has independently checked feasible solutions, but no
optimality proof within the five-second baseline budget. The original corpus and
rounding conventions are not fully recovered; scores are not claimed to reproduce
all published numbers. The simplification map is a proposed reviewable variant.

The four-mode reference specification and variable-order implementations are
still pending; completing the fixed-order slice does not close plan stages 2–3
in full. Python rational objectives are available; parsed rational-objective syntax,
product explanation objects and automatic direct-DP dispatch remain future work.
The independent DP solves the two tractable cases much faster than native search:
this is evidence for dispatching supported models directly or reusing its witness,
not evidence that the general CSP path has achieved that speed.

The [published-paper review](markov_paper_review.md) also validates Table 5 under
our current model at log score -46.921592. Our five-second two-family incumbent
was -63.195230: incumbent quality, as well as proof time, needs improvement. This
external feasible witness is recorded separately and has not been presented as a
solver-generated improvement or an optimum for our corpus.

## Next actions

1. Complete the independent four-mode scorer and edge-case specification.
2. Apply the planned linear-inequality optimization with exhaustive support tests.
3. Validate warm starts, reuse DP witnesses/messages, and profile Boulez incumbent
   discovery and proof separately against the known published witness.
4. Add incremental table supports and variable-order controls against the reference.
5. Proceed with measured GCC, equality-sum and all-different improvements.
6. Close the full reproduction gates, including headline Boulez optimality proof,
   broad performance regression comparisons and documented numerical guarantees.

Validation and commit details for this slice are recorded in the performance
report. No source changes were made to LSDB.
