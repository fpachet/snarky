# Markov constraints: steerable generation and optimization

Markov-constrained music generation is a Snarky research application. It combines
learned local continuation probabilities with explicit musical constraints and
optimizes the complete sequence. The examples revisit Pachet and Roy's 2011
*Markov constraints: steerable generation of Markov sequences* using the current
finite-domain engine and exact objectives.

## Implemented examples

| Application | Controls and objective | Verified result |
|---|---|---|
| Ordinary Blues | 24 half-bar chords, C7/F7/G7 anchors, first-order probability | Exact optimum agrees with independent DP |
| Exotic Blues | Ordinary controls plus exactly one F-sharp seventh | Exact optimum agrees with count-aware DP |
| Boulez Blues | Anchors and all-different over 24 seventh/minor chords | Exact sequence from Table 5 regenerated without a seed and proved optimal |
| Di Meola melodies | Anchored 17-note sequences; fixed-order, smoothing, highest-order and algebraic objectives | All four printed melodies verified optimal under the documented formulas |
| Melody controls | Forbid observed six-note windows, guide pitch contour, continue from fixed context | Exact reference checks, including chunk boundaries and mixed rules/constraints |

The Boulez proof takes a median **1.732 seconds and 209 nodes** in the archived
experiment. Variable-order melody DP takes approximately **53–62 milliseconds**;
unseeded native CSP proves all four melody optima in under half a second in the
recorded runs. These are workload-specific measurements on the documented host,
not general engine or historical Backtalk speedup claims.

The Boulez corpus is explicitly reconstructed: the recovered sequence is identical
to the published one, but its log score is **−46.921592**, versus the historical
**−46.74**. The melody guide likewise preserves discrepancies in Table 6. Exact
search optimality is distinguished from identity of historical training data and
from exact sampling. Sequential chunk optima need not optimize the full stream.

## Results, code and reproduction

- [Blues paper handoff](research/blues_villani_2026-09-16/README.md): corpus,
  generated sequences, exact local probabilities, LaTeX tables and source archives.
- [Boulez performance and proof](performance_boulez_2026-09-16.md): assignment
  bounds, seeded/unseeded ablations, validation and regression controls.
- [Melody examples and API](markov_melody_examples.md): four-mode semantics,
  contour controls, continuation and compilation into ordinary CSP models.
- [Melody performance](performance_melody_2026-09-16.md): independent reference
  comparisons, search statistics and archived timing samples.
- [Blues benchmark](../benchmarks/blues_markov.py) and
  [melody benchmark](../benchmarks/melody_examples.py): executable reproductions.
- [Application plan](markov_constraints_plan.md): remaining library and language work.

These examples exercise the same finite runtime used for other Snarky CSP
applications. Direct DP handles supported local controls; native reversible search
handles additional global constraints and rules. Rational-product or integer
objectives account for every factor independently of branching decisions.

The Bach learning experiment is a separate side project with its own data,
evaluation protocols and research results.
