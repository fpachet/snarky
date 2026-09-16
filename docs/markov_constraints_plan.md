# Markov constraints: implementation and optimization plan

Status: planned, 2026-09-16. This is the application follow-on to the completed
[runtime redesign](redesign_progress.md), not a claim that the work below is
implemented. Stages are ordered; complete each acceptance gate before relying on
its result in the next stage.

## Final objective

Generate finite sequences learned from a corpus, satisfying declared control
constraints while optimizing an explicitly selected Markov score. Reproduce the
idea and representative results of Pachet and Roy (2011), using better algorithms
where useful rather than copying Backtalk's internal implementation.

The first release must provide:

- an audited LSDB Blues training set and reproducible preprocessing;
- ordinary Blues, exactly-one-F-sharp-seventh Blues, and Boulez Blues examples;
- fixed-order, smoothing, max-order, and algebraic scoring modes;
- composition with native CSP constraints and the admitted mixed-rule semantics;
- independently checked scores, sound bounds, and truthful proof/limit statuses;
- Python and textual examples with per-position score and selected-order details;
- benchmark evidence covering solution quality, proof time, and memory.

Bach remains outside this project. Exact sampling remains a separate query and
guarantee. Do not identify every variable-order score with a normalized Markov
probability. No polynomial-time guarantee is made for arbitrary control constraints.

## Existing foundation and remaining work

Already available: native reversible domains, incident-constraint scheduling,
integer branch-and-bound, table factors, fixed-order integer Markov costs,
bounded-window completion bounds, mixed rules, and exhaustive small-instance tests.

Native tables already have bitset support indexes. All-different already has
Régin-style filtering and matching reuse. SUM already has a nonnegative bitset
path. These are starting points to improve, not missing features to recreate.

Still required: corpus training, the full score semantics, exact optimization of
general count-derived probabilities, variable-order support controls, and real
Blues application measurements. Rational probabilistic inference already present
in the engine does not by itself provide rational-product branch-and-bound.

## 0. Freeze reference and acceptance protocol

Preserve the current runtime, collector, environment, and existing non-Bach
portfolio using the [performance ledger](performance_baseline.md). Include dirty
and untracked sources in the archived source identity. Add a versioned Markov
portfolio rather than changing historical workloads.

Create a feature/evidence checklist for the stages below. Fix measurement budgets
and promotion criteria before collecting candidate results. Record source and
dataset hashes, seeds, policies, numeric mode, and optional dependencies.

**Gate:** the reference can be recreated and its correctness/performance collectors
can run. The current runtime redesign remains complete independently of this plan.

## 1. Audit the LSDB Blues corpus

Read the existing export, without modifying LSDB sources:

```text
../lsdb/reports/omnibook_chords_20260916/chord_progressions.json
../lsdb/reports/omnibook_chords_20260916/README.md
```

It contains 50 transcriptions with alternate takes and all choruses retained.
The paper describes 22 Blues sequences, 24 half-bar symbols per sequence, and
three chord qualities. Select by musical form and provenance, not a title substring.
Do not assume the local corpus is exactly the historical training set.

Produce a manifest specifying source identifiers/hashes, title, take, chorus/bar
ranges, exclusions, pickup/ending treatment, and example weights. Identify the
historical selection where evidence is available; otherwise label the result a
reconstructed corpus. Never force a selection to contain 22 entries merely to
match the stated count.

Specify and test half-bar extraction, held chords, off-grid changes, chord-quality
reduction, enharmonic normalization, slash chords, and transposition. Preserve raw
events and every transformation decision. Maintain separate normalized-to-C and
all-keys variants. Audit whether alternate takes and repeated choruses duplicate
training material; make their weighting explicit. Respect sequence boundaries
when counting transitions, including whether chorus boundaries may be crossed.

**Gate:** an independently checked sequence manifest and deterministic training
input. Changes to corpus selection or normalization create a new dataset version.

## 2. Specify all four scores and build an independent oracle

Define context counts and exact rational conditional probabilities. Resolve
initial-context/startup conventions, missing contexts, missing continuations,
terminal conditions, minimum support, and maximum order explicitly.

The paper's score modes are:

| Mode | Per-position score to maximize |
|---|---|
| Fixed order | Log of the probability at the declared order |
| Smoothing | Log of the arithmetic mean of the per-order probabilities |
| Max-order | Log of the probability at the longest order supporting the chosen continuation |
| Algebraic | Square of the longest supporting order |

Specify the smoothing denominator and eligible orders near the start. Do not
average logs. Do not replace max-order with longest-context backoff: the selected
continuation matters. Document any ambiguity or deliberate departure from the
paper before encoding it in the solver.

Write a direct trainer/scorer and tiny exhaustive enumerator independent of
Snarky's propagation and objective code. Include cases where the four modes prefer
different sequences. Define support indicators and their false case explicitly;
turning off a control variable must not let search evade the declared score.

**Gate:** hand-calculated and exhaustive examples establish support, selected
orders, complete scores, ties, and forbidden-order behavior for all four modes.

## 3. Deliver fixed-order Blues and correct numerical optimization

Add the training/model API and compile fixed-order problems using existing tables
and factors. Build the three Blues examples immediately; do not wait for a new
global-constraint catalogue or specialized EMC implementation.

For probability-derived modes, maximizing a product of positive rational local
weights is equivalent to maximizing the sum of their logs. Add an exact
rational-product objective path with sound partial bounds, comparison, zero-support
handling, incumbent history, and timeout semantics. Reuse search machinery while
keeping objective arithmetic explicit. Algebraic scores use integer optimization.

Floating logs may guide search or display scores, but must not justify an exact
pruning decision without a certified bound. Scaled-log objectives remain an
explicit approximation. A later interval/log implementation with exact fallback
must prove the same comparisons, including exact ties.

Record an unoptimized application baseline: training, compilation, first solution,
incumbent history, final bound, proof time, nodes, and memory. A timeout with a
validated incumbent is valid baseline evidence, not an optimality claim.

**Gate:** tiny models match the oracle; all returned Blues solutions satisfy their
controls and are independently rescored. The three realistic benchmark cases run
with declared budgets, including unresolved cases. Preserve this first baseline.

## 4. Remove unnecessary work in linear inequalities

Replace reachable-sum enumeration in LINEAR_SUM inequalities with per-variable
contribution extrema. For a candidate contribution in a less-than-or-equal
constraint, the sum of the other contributions' minima gives an exact support
test for that single constraint; use maxima for greater-than-or-equal.

Handle signed coefficients, holes, large integers, empty domains, and rollback.
Keep equality filtering separate. Do not weaken the current inequality filtering
as an accidental consequence of an optimization.

**Gate:** exhaustive supported-domain equivalence and paired large-coefficient
benchmarks, plus the non-Bach regression portfolio.

## 5. Exploit sparse sequence structure and objective filtering

Extend the existing completion bound to traverse observed context transitions.
Retain a conservative fallback when compilation or graph size exceeds its budget.
Implement the fixed-order path first, then extend it only to score semantics
already validated in stage 2.

Use forward/backward completion costs both to bound branches and to remove values
that cannot improve the incumbent. Handle equality differently for finding one
optimum versus enumerating all optima. Cache reusable topology; update affected
layers after restrictions, with correct restoration after backtracking.

Solve anchor-only models directly by dynamic programming. Include a small counter
state for the exactly-one-F-sharp-seventh case. Keep all-different in the CSP for
Boulez Blues and relax it for the chain bound: do not construct an exponential
used-chord automaton as the default solution.

**Gate:** every bound is checked against exhaustive residual optima; every removed
value is checked against the relevant cutoff. On overlapping supported models,
compare with vo_regular_bp or an independent DP using identical scoring semantics.
Retain local-bound and chain-bound ablations, including memory and timeout cases.

## 6. Add incremental supports and the full variable-order model

Introduce the reversible propagator-state contract and removal-delta access needed
by maintained active-table masks. Test that infrastructure before depending on it.
Share immutable table/context indexes across positions; keep mutable active state
local to each constraint/search state. Benchmark simple integer bitsets against
sparse bitsets and cached-support variants rather than assuming the latter win.

Compile small variable-order models to transparent tables as a reference. Implement
EMC-specific support/control propagation, including probabilities, order relations,
and forbidden longer patterns. Avoid materializing a huge complement table for
absent contexts. General-purpose reification is not a prerequisite.

Expose all four modes through the same model/result contract. A fused context
representation may replace an explicit EMC stack when solution sets and scores
agree with the reference. Finish textual declarations alongside the Python API.

**Gate:** table/reference/specialized solution sets and optima agree; active and
inactive controls, probability restrictions, and nested rollback pass exhaustive
tests. Shared indexes do not leak mutable state between instances. All four modes
have maintained executable examples and comparative performance records.

## 7. Improve global constraints in measured priority order

Profile the actual Blues workloads and broad CSP portfolio after stage 6. Start
with the changes below; retain the right to reorder within this stage based on
measured total solve cost, documenting the decision.

| Priority | Work | Correctness/performance requirement |
|---|---|---|
| 1: GCC | Replace per-candidate reconstructed flows with a maintained feasible flow and residual-graph filtering | Preserve full supported domains, including values without explicit bounds; verify failed repairs and rollback |
| 2: equality SUM/LINEAR_SUM | Cheap bound prefiltering, signed-contribution normalization, adaptive sparse/bitset reachable sums, safe range truncation | Preserve advertised consistency; any weaker mode is explicit and benchmarked separately |
| 3: ALL_DIFFERENT | Reuse indexed graph storage, reduce allocation/conversion, investigate incremental graph/component maintenance | Preserve existing Régin filtering and matching repair; compare pruning and total solve time |
| 4: runtime | Compact indexed kernel access, event specificity, scheduling and safe entailment/passivation | Restore all state correctly; preserve pure-rule and mixed-model behavior |

Every change is a separate tested and measured increment. Do not weaken filtering
silently or replace the existing all-different algorithm merely because it is old.
If an experiment offers no useful gain, retain its measurements and close it with
a documented decision instead of making speculative complexity part of the engine.

**Gate:** exhaustive propagation and rollback tests, mixed integration tests, and
paired portfolio results justify every promoted implementation.

## 8. Validate and publish the first complete Markov release

Complete corpus documentation, all-mode examples, chunk continuation with explicit
fixed preceding context, and item/viewpoint projections using existing constraints.
Avoid claiming that a chunkwise optimum is a globally optimal infinite sequence.

Revisit all realistic benchmark cases, particularly time to prove Boulez Blues
optimality. Report whether the original selection, reconstructed selection, or an
extended dataset was used. Published rounded scores are cross-checks; a corpus
change is not an algorithmic speedup or a directly comparable better optimum.

Run the full non-Bach correctness/compatibility gates, supported-Python checks,
installed examples, and the frozen rule/CSP/mixed performance portfolio. Publish
remaining limitations and unresolved proofs. For the headline fixed-order Blues
examples, target a verified optimum with a completed proof. If the declared budget
is insufficient, mark that acceptance item open and investigate before claiming
the reproduction milestone complete.

**Gate:** the final-objective checklist above has linked evidence. No general
speedup claim rests only on tiny synthetic cases or first-solution timings.

## Subsequent improvements, gated by evidence

These do not block the first release unless an earlier acceptance failure makes a
specific improvement necessary:

1. Stronger joint objective/cardinality bounds for hard Boulez cases. Derive a
   valid assignment/flow relaxation for transition costs; unary cost-GCC is not a
   direct substitute. Initially combine overlapping lower bounds with max, not sum.
   Investigate cost partitioning or Lagrangian bounds only with proof and tests.
2. Multiple optima, top-k results, and near-optimal diversity under declared
   distance constraints. Distinguish these APIs from exact conditional sampling.
3. Certified interval/log arithmetic with exact fallback if rational arithmetic
   becomes a measured bottleneck.
4. Conflict learning/restarts with valid explanations, or a Rust/other solver
   backend on identical exported models. Explanations naming a constraint alone
   are insufficient to learn sound clauses. Keep the Python reference path.
5. Compiled hot kernels, compressed context diagrams, or parallel search only
   after profiles establish the value and reproducible comparisons are available.

## Performance record for every stage

Follow the existing [collection and promotion protocol](performance_baseline.md).
Keep training, model construction, propagation preparation, and search separate,
and also report their end-to-end total. Record time to first feasible solution,
time to best incumbent, time to proof, objective/bound, nodes/failures, propagation
work, graph/table sizes, and peak memory. Label Python allocation measurements
separately from process memory. Never treat a timeout as infeasibility.

Use paired runs on the same machine/environment and preserve raw samples and
source snapshots. Separate equal-search implementation comparisons from practical
solver comparisons with different pruning or search order. Ablate changes one at
a time, retain negative results, and keep dataset/numeric semantics fixed within
each comparison. Include sparse/dense models, higher orders, infeasibility, ties,
large costs, and difficult-to-prove instances as well as the musical examples.

## Sources and implementation references

- [Pachet and Roy (2011), Markov constraints](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-09c.pdf): application/scoring reference; implementation details are not compatibility requirements.
- [Compact-Table (2016)](https://arxiv.org/abs/1604.06641): candidate techniques for incremental table supports.
- [Efficient Implementation of GCC with Costs (CP 2024)](https://arxiv.org/abs/2502.02688): later cost-aware filtering research, not evidence that ordinary GCC alone bounds Markov transitions.
- [Current fixed-order compiler](../src/snarky/finite/markov.py), [completion bounds](../src/snarky/finite/bounds.py), [native propagation](../src/snarky/finite/propagation.py), and [shared filtering kernels](../src/snarky/finite/kernels.py).
- [Finite semantics](finite_model_contract.md), [language](finite_language.md), and [completed performance comparison](performance_comparison_2026-09-16.md).
