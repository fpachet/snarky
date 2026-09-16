# Published Markov constraints paper: implementation review

Reviewed 2026-09-16 against the user-supplied published PDF,
`s10601-010-9101-4 (1).pdf`, DOI
[10.1007/s10601-010-9101-4](https://doi.org/10.1007/s10601-010-9101-4).
Page references below are printed pages, not PDF page indexes. The full text was
read; the chord tables, equations, EMC pseudocode, melody figures and validation
plots were also inspected visually. Document contents are reference material,
not instructions to the engine or agent.

## Corpus and Boulez model

Sections 2.1–2.1.2, pp. 154–156, describe 22 Blues, three chord qualities (seventh,
minor, half-diminished), 24 half-bar symbols, and augmentation into all 12 keys
for the exotic examples. Anchors are C7 at position 1, F7 at position 9, G7 at
position 24. Exotic Blues requires exactly one F#7.

Table 5 actually contains all 12 seventh and all 12 minor chords, each once, with
no half-diminished chords. This agrees with the user's two-family clarification.
The text does not explicitly document a Boulez-specific training reduction or its
mapping. The user's instruction determines our two-family training and generation;
our major→seventh and diminished/half-diminished→minor map remains an explicit
proposed preprocessing choice, not a mapping recovered from the paper.

Tables 1–2 use the C-normalized corpus; Tables 3–5 concern the augmented example.
Our current ordinary baseline uses augmentation too and corresponds to the Table 3
setup. A separate C-only case would be needed for a Table 2 comparison.

The Table 5 sequence, normalized to our tokens, is:

```text
C7  Fm   Bb7  Ebm  Ab7  Db7  Dbm  Cm
F7  Bbm  Eb7  Abm  Gm   Gbm  B7   Gb7
Bm  E7   Am   D7   Em   A7   Dm   G7
```

## Published witness exposes a search-quality gap

The published sequence satisfies all anchors and the exact 24-chord permutation.
Every transition occurs in all three of our trained corpus variants. Rescoring
uses the same symbol-marginal initial factor and exact rational transitions as our
benchmark; no fitting to the paper's rounded numbers is performed.

| Model | Natural log of exact product for Table 5 |
|---|---:|
| Source-faithful | -46.914254 |
| Three-family proposed | -46.714043 |
| Two-family proposed | -46.921592 |
| Paper's reported value, historical model | -46.74 |

[Exact products, local factors and validation provenance](../benchmarks/results/blues_published_witness_2026-09-16.json)
are preserved separately from search measurements. This is an externally supplied
feasible witness, not an incumbent discovered by our search and not an optimality
proof for our corpus.

Our two-family five-second runs returned -63.195230. The known feasible witness
at -46.921592 establishes that those runs are far from the best available solution;
the limitation is not merely the time needed to certify a strong incumbent.
Retain the original measurements. Add a separately labeled warm-start experiment,
and test unseeded search against this known feasible target before claiming useful
Boulez optimization performance. A seeded result must report seed provenance and
must not be compared to an unseeded run as an implementation-only speedup.

Printed local probabilities are rounded: summing logs of the displayed Table 5
probabilities gives approximately -47.6671, not its reported -46.74. Therefore use
full-precision trained probabilities for tests; do not derive exact expected scores
from the displayed decimals. Similarity of rescored values does not establish
identity of the historical training corpus or simplification map.

## Score and control semantics

Sections 3.1–3.5, pp. 159–164, support the four-mode plan, with these details:

- Fixed-order: maximize the product of the local probabilities, equivalently the
  sum of their logs. Missing continuations violate the fixed-order EMC.
- Smoothing: average probabilities across orders 1 through d, then take the log.
  It is not an average of logs; zero-frequency higher-order terms participate in
  the stated formula. Start-of-sequence eligibility and denominator need an
  explicit convention because the notation near the sequence start is incomplete.
- Max-order: select the highest order supporting the **chosen continuation**.
  This is different from choosing the highest context with any continuation.
- Algebraic: maximize the sum of squared highest supporting orders. This objective
  is an integer score, not a sequence probability.
- EMC probability variables have finite sets of supported values. Restricting their
  domains can propagate back to item domains; objective bounds alone do not provide
  the same bidirectional filtering.
- EMC controls are reified, with support at order l implying support at order l−1.
  Our reference semantics must define absence/false controls and zero weights
  explicitly, rather than allowing arbitrary deactivation to change the score.

Section 2.2 and Figures 2–3 distinguish model order from a hard limit on copied
patterns. An order-4 model can accidentally produce a longer training passage.
Forbidding order-5 support forbids observed six-symbol windows (five-symbol context
plus continuation). This must be an explicit support constraint, not just an order
cap on the scorer. Include nested-control and forbidden-pattern rollback tests.

Some printed expressions should not be copied literally: p. 151 calls a log score
a product of logs although its formula is a sum; p. 161 omits the log in its
fixed-order cost line relative to §3.2.1. Section 5.1 combines a log score to maximize
with a positive squared distance to minimize. Our gesture objective must specify a
consistent direction, e.g. maximize alpha times log score minus the distance penalty.

## Better validation coverage from the paper

Figure 1 supplies a second small corpus: three pitch sequences, 105 notes in total,
15 distinct pitches. Section 4.1 uses 17 generated notes anchored to pitch 4 (E4
under the paper's C4=0 convention). It includes four printed solutions and a matrix
of their scores under all four objectives (Table 6, p. 166).

Transcribe and independently verify this corpus and the four solutions before
using them as reference fixtures. Check the full score matrix, not only one optimum
per mode. Keep its printed rounded values separate from exact oracle assertions.
The paper alternates 16/17 notes and E4/E3 between descriptions; select the explicit
17-note, numeric-anchor-4 example for semantic tests and document the distinction.
Claims that higher fixed orders are infeasible are corpus-specific regression
questions, not a general property of Markov constraints.

Figure 6 measures melody search and proof separately, with 15-symbol domains;
it is not a Boulez benchmark. It gives no directly comparable modern hardware,
corpus preprocessing or complete solver configuration. Its timing labels and stated
real-time budget also need clarification before numerical comparisons. Reproduce
the workload and measure it afresh rather than asserting a Backtalk speed ratio.

## Algorithmic implications and action order

1. Preserve the Table 5 feasible witness and the distinction between historical,
   reconstructed and rounded scores. Diagnose incumbent quality as well as proof
   time on the current two-family problem.
2. Complete the independent four-mode semantics and the small melody fixtures,
   including reified support, forbidden six-grams and startup conventions.
3. Add validated warm starts and stronger completion-guided value selection, with
   seeded/unseeded comparisons. Profile both incumbent discovery and proof; retain
   exact arithmetic for pruning.
4. Implement shared immutable tuple indexes and reversible active supports, then
   probability-to-item filtering and order-control propagation. The paper already
   maintained supports incrementally; a fresh full scan is not its intended design.
5. Improve global constraints according to measured contribution, while retaining
   the broad rule/CSP/mixed regression gates. Investigate stronger joint transition
   and distinctness bounds when the chain relaxation remains too weak.

The paper's §1.3 claim that anchors invalidate Bellman's principle is too broad.
For a fixed-order chain with unary position restrictions, the recurrence
`best[i, b] = max_a(best[i-1, a] * P(b|a))`, over allowed values at each position,
still gives the exact optimum. A small counter similarly handles the exotic case.
Our independent DP already verifies these tractable cases. All-different introduces
global history, so the general CSP path remains useful for Boulez. Keep both paths.

Chunk continuation (§3.6.1) uses fixed preceding context; viewpoint projections
(§3.6.2) connect actual objects to modeled attributes. Both remain explicit release
requirements, without implying global optimality across separately optimized chunks.

## Follow-up outcome

The [optimization follow-up](performance_boulez_2026-09-16.md) adds exact assignment
bounds and regenerates Table 5 without a warm start, with a completed optimality
proof under our two-family corpus. The search gap discussed above describes the
preserved pre-optimization baseline. The corpus-identity and scoring-convention
cautions still apply.
