# Finite-CSP solver optimization plan

This plan keeps Snarky a clear, extensible rule-and-constraint runtime rather
than turning it into a specialized competitive CSP solver. Optimizations must
preserve the architecture:

```text
candidate facts
→ persistent constraint closure
→ affected forward-rule closures
→ joint fixed point
→ goal, contradiction, or explicit CHOICE
→ checkpointed propagation and rollback
```

Constraints remain deterministic filters. Rules remain ordinary forward
chaining. Only `CHOICE` creates alternatives.

## Acceptance rules

Every solver optimization must satisfy all of the following:

1. compare complete solutions with an independent problem oracle;
2. differentially test each propagator against exhaustive tuples on small
   domains;
3. preserve event, rollback, and fixed-point semantics;
4. report search nodes and failed branches beside time;
5. compare timings only when problem data and search counters are equivalent;
6. retain a conservative path for unsupported dependency shapes.

A faster run with different search counters may be a useful solver
improvement, but it is not a pure implementation-speed comparison.

## Measured starting point

A profile of the order-7 magic square, limited to 100 search nodes, showed
that orchestration cost was larger than the propagators themselves:

| Area | Profile time |
|---|---:|
| Forward rule groups | 12.1 s |
| Choice production | 4.79 s |
| Persistent constraint layer | 3.81 s |
| Actual constraint revisions | 2.31 s |
| `ALL_DIFFERENT` revision | 1.22 s |
| `SUM` revision | 1.03 s |
| Branch cloning/trailing | 1.76 s |

These figures are diagnostic samples, not stable performance claims. They
justify optimizing scheduling and fact projection before implementing more
complex incremental matching or flow algorithms.

## Phase 1: remove avoidable orchestration

Status: implemented.

`JointFixedPointScheduler` compiles relation dependencies from the factual
premises of each rule group. Persistent propagators declare the relations
they observe. After a component changes facts, only components watching those
relations are queued again. Dynamic relation positions and unannotated
propagators use a conservative wildcard.

Each rule group still saturates internally, so the scheduler changes only
which already-stable groups are revisited. Net-zero add/remove event pairs do
not trigger work.

Global-only models now select only the generic choice, domain, and problem
groups. They do not execute the extensional binary-constraint group when the
model contains no such constraints.

## Phase 2: improve practical propagator kernels

Status: implemented for the measured `SUM` and `ALL_DIFFERENT` costs.

`SUM` uses exact prefix and suffix reachable-sum bitsets for bounded
non-negative integer domains. This retains domain consistency while replacing
large Python sets of sums with integer bit operations. Negative or very large
sum ranges use the transparent set-based reference path. Prefix/suffix
bitsets are convolved once per variable, rather than repeating a support scan
for every candidate.

`ALL_DIFFERENT` retains a valid matching between revisions and repairs it only
when a matched edge disappears. Matching state also survives a session
rollback when it remains valid in the restored wider domains.

Current global propagators deliberately favor inspectable algorithms:

- `ALL_DIFFERENT`: Hopcroft–Karp matching plus Régin alternating-graph
  filtering;
- `GCC`: lower-bounded flow feasibility with per-candidate support checks;
- `TABLE`: active-tuple projection;
- `SUM`: exact prefix/suffix support.
- `LINEAR_SUM`: exact weighted reachable-sum support for equality and bounds;
- `LESS_EQUAL`, `LESS_THAN`, and `NOT_EQUAL`: binary GAC;
- `ELEMENT`: exact one-based index/value support for distinct variables;
- `COUNT`: exact mandatory/possible occurrence support.

The next kernel optimizations should be accepted only after profiles identify
them as dominant:

1. reversible matching reuse for `ALL_DIFFERENT`;
2. residual-network reuse for `GCC`;
3. maintained tuple supports for `TABLE`;
4. min/max bounds before exact `SUM` support on wide ranges.

## Phase 3: reduce domain and choice materialization

Status: implemented for the canonical finite-CSP vocabulary.

`InferenceEventCursor` identifies a position, session, rollback generation,
and generation origin. `FiniteDomainProjection` consumes ordinary deltas and
reverses its own trail to the generation origin after rollback. This avoids
rescanning all visible facts at every propagation entry while remaining safe
when a sibling branch has the same event count as the branch it replaced.

`FiniteDomainChoiceProvider` projects the canonical `choose_csp_value` rule
from that maintained view. Differential tests compare its point names,
alternatives, weights, substitutions, supports, and ordering with
`RuleChoiceProvider`, including after rollback.

The canonical decision, singleton, empty-domain, and solved-state rules also
have compiled eligibility lookup. Their original rule objects still fire
through normal refraction, mutation, event, and provenance machinery. Custom
choice rules or incomplete canonical group compositions automatically retain
the generic rule provider.

This compiled path reduced the current classical benchmark without changing
any search counters:

| Case | Previous median | Incremental median | Ratio |
|---|---:|---:|---:|
| Magic 4×4 | 2.393 s | 0.442 s | 5.4× |
| Magic 5×5 | 4.333 s | 0.758 s | 5.7× |
| Latin 7×7 | 0.253 s | 0.045 s | 5.7× |
| Sudoku p7, constraints only | 0.155 s | 0.106 s | 1.5× |

At the end of phase 3, the complete 6×6 magic square retained 5,358 nodes and
4,236 failures. Its
three-run median is 19.179 seconds, compared with the earlier 131.25-second
single run: approximately 6.8× faster with the same search tree.

An instrumented confirmation run recorded 5,357 branch decisions, maximum
depth 20, solution depth 18, 5,358 persistent-propagator invocations, 111,140
individual constraint revisions, and 333,440 constraint-driven candidate
removals. The revisions comprise 13,777 global `ALL_DIFFERENT` revisions and
97,363 `SUM` revisions. The model uses MRV/first-fail with deterministic
fixed-order ties and no explicit symmetry breaking.

## Phase 4: search policy, symmetry, and explanations

Status: implemented and measured.

Search order often matters more than another low-level percentage. Generic
extensions may include degree or impact tie-breakers, value ordering, and
restart/nogood policies. Symmetry breaking belongs in declarative model facts,
rules, or constraints and must be reported as a search change.

Static degree and numeric ascending/descending prototypes were slightly worse
than deterministic MRV over the same first 300 order-6 nodes. The implemented
policy instead uses dynamic weighted degree. A failed branch increments the
weight of its reported `violated_constraint`; an empty domain without that
fact credits its incident constraints. Persistent-constraint models now use
dom/wdeg by default, while models without such constraints retain MRV.

The search-order comparison is deliberately separate from the kernel
benchmark:

| Formulation | Median | Nodes | Failures |
|---|---:|---:|---:|
| Magic 6, MRV, no symmetry | 19.179 s | 5,358 | 4,236 |
| Magic 6, dom/wdeg, no symmetry | 2.308 s | 575 | 445 |
| Magic 6, dom/wdeg + LCV probes | 2.329 s | 217 | 159 |
| Magic 6, dom/wdeg + lex symmetry | 0.513 s | 73 | 40 |
| Magic 7, dom/wdeg, no symmetry | 2.507 s | 431 | 266 |
| Magic 7, dom/wdeg + LCV probes | 3.116 s | 160 | 89 |

The bounded propagation-guided wrapper probes at most eight alternatives and
tries the least-constraining non-contradictory value first. It substantially
reduces nodes here, but duplicate propagation offsets the saving, so it
remains opt-in.

`LEX_LESS_EQUAL` is a generic persistent constraint whose paired ordered scope
can contain aliased variables. The magic-square model can use seven such
fact-derived lex leaders to choose one representative under rotations and
reflections. This is also opt-in: it is excellent for order 6, whereas order
7 reached the 1,000-node limit in 10.087 s instead of solving in 431 nodes
without symmetry. Symmetry changes the search tree and is not a propagator
kernel speedup.

The raw runs are archived as
[`magic_square_dom_wdeg_2026-07-25.json`](../benchmarks/results/magic_square_dom_wdeg_2026-07-25.json),
[`magic_square_dom_wdeg_lcv_2026-07-25.json`](../benchmarks/results/magic_square_dom_wdeg_lcv_2026-07-25.json),
and
[`magic_square_dom_wdeg_symmetry_2026-07-25.json`](../benchmarks/results/magic_square_dom_wdeg_symmetry_2026-07-25.json).

## Phase 5: explanation-backed learned impacts

Status: implemented.

The persistent propagator now records which constraint removes each candidate.
These branch-local explanations are kept outside working memory and are
invalidated on a session journal-generation change, so causes from a rolled
back branch cannot leak into its sibling. Direct constraint contradictions
still expose the exact `violated_constraint`; domain wipeouts can additionally
consult the retained removal causes.

`LearnedImpactChoicePolicy` observes only real search branches. It measures
the logarithmic domain-volume change across fixed-point propagation and keeps
a running mean per variable/value. Contradictions have impact 1, solutions
impact 0, and lower-impact values are tried first. It therefore captures much
of the node reduction sought by LCV probing without creating and propagating
speculative sessions.

The three-run comparison on the same final implementation is:

| Formulation | Median | Nodes | Failures |
|---|---:|---:|---:|
| Magic 6, plain dom/wdeg | 2.060 s | 575 | 445 |
| Magic 6, learned impact | 1.352 s | 387 | 297 |
| Magic 7, plain dom/wdeg | 2.132 s | 431 | 266 |
| Magic 7, learned impact | 1.826 s | 368 | 223 |

Learned impact is consequently the default value ordering for persistent
CSPs, wrapping dom/wdeg point selection. Plain dom/wdeg remains available for
A/B runs. The raw comparison is archived in
[`magic_square_dom_wdeg_only_2026-07-25.json`](../benchmarks/results/magic_square_dom_wdeg_only_2026-07-25.json)
and
[`magic_square_learned_impact_2026-07-25.json`](../benchmarks/results/magic_square_learned_impact_2026-07-25.json).

## Benchmark protocol

Run:

```sh
uv run python -m benchmarks.classical_csp --repeat 3
```

The benchmark validates magic-square, Latin-square, and Sudoku solutions
before reporting time. Raw JSON belongs under `benchmarks/results/`. For a
pure scheduler or kernel optimization, require identical node and failure
counters. For stronger filtering or changed search policy, archive it as a
separate formulation and do not present its timing as a direct speedup.

The current three-run archive is
[`classical_csp_learned_impact_2026-07-25.json`](../benchmarks/results/classical_csp_learned_impact_2026-07-25.json).
The preceding search-policy archive is
[`classical_csp_dom_wdeg_2026-07-25.json`](../benchmarks/results/classical_csp_dom_wdeg_2026-07-25.json).
The preceding implementation-speed archive is
[`classical_csp_incremental_2026-07-25.json`](../benchmarks/results/classical_csp_incremental_2026-07-25.json).
The separate
[`magic_square_6_incremental_2026-07-25.json`](../benchmarks/results/magic_square_6_incremental_2026-07-25.json)
records the larger three-run case.

## Phase 6: practical constraint vocabulary

Status: implemented.

The persistent layer now covers the small reusable vocabulary needed by many
classical CSP models without forcing decompositions into rules:

- signed integer `LINEAR_SUM` with equality and two bound operators;
- binary numeric order and generic disequality;
- one-based `ELEMENT`;
- fixed-value `COUNT`.

These propagators retain the same narrowing-only, deterministic contract and
participate in the existing adjacency scheduler, removal explanations,
checkpoint rollback, dom/wdeg attribution, and learned-impact search. Small
domain differential tests compare their consistency result and every
surviving candidate with exhaustive assignment oracles. This phase extends
modeling coverage; it does not alter the magic-square search tree or replace
the profiling rule that kernel complexity must be justified by measurements.
