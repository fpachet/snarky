# Unified Snarky redesign plan

Status: implemented and locally validated, 16 September 2026. See the
[implementation evidence](redesign_progress.md) and
[performance acceptance report](performance_comparison_2026-09-16.md), including the
explicit completion-cache memory tradeoff. The final objectives below remain
unchanged. This is an opt-in pre-1.0 addition, not a public release.

## Purpose and relationship to existing specifications

Deliver one language and project for efficient symbolic inference, finite-domain
constraint solving and optimization, and pure factor scoring, with explicit
semantics and interchangeable execution backends.

This plan consolidates the execution work implied by the
[reference semantics](semantics.md), [Core 0.1 compatibility contract](core_0_1_baseline.md),
[learned-factor plan](learned_factor_language_plan.md), and
[probabilistic specification](probabilistic_constraint_learning_spec.md).
Those documents retain their normative roles. This plan does not silently
reinterpret existing programs or promote research syntax to stable status.

The redesign is incremental. Keep the existing implementation runnable as a
reference until each replacement passes its acceptance gates. Do not begin
with a wholesale rewrite of the matcher, parser, or applications.

Scope clarification: Bach corpus processing, learning, generation experiments,
and their migration are excluded from this redesign. They will belong to a
separate project. Engine validation must be sufficient without Bach data,
trained artifacts, or research-test dependencies. Generic factors and Markov
models remain in scope and use small independent fixtures.

## Final objectives

1. **Efficient rules:** preserve the expressive Core rule language, indexed and
   incremental matching, mutation, conflict resolution, and explanations.
2. **Independent CSP execution:** solve finite-domain models without requiring
   candidate facts, rule matching, or a forward-inference session internally.
3. **Native optimization:** minimize or maximize an explicit objective in one
   search, retain incumbents, use sound bounds, and distinguish feasible results
   from proved optima and interrupted searches.
4. **Clear composition:** rules derive properties, constraints define feasible
   configurations, factors supply pure scores, and search chooses how to explore.
   Propagation and branching cannot change a model's declared meaning.
5. **One model, multiple queries and backends:** share validated model objects
   between feasibility, optimization, and supported probabilistic queries.
   A backend must report unsupported features instead of dropping them.
6. **Compatibility and explanations:** existing Core programs retain documented
   observable behavior; new results distinguish derivation, constraint pruning,
   score contributions, and optimization evidence.
7. **Measured performance:** publish reproducible before/after results for rule,
   CSP, mixed, and Markov workloads, including preparation, solve time, peak
   memory, and work counters. Do not claim efficiency from toy timings alone.

The constraint target is the complete existing persistent vocabulary plus a
documented extension interface. It is not a promise to implement every published
global constraint or solve arbitrary CSPs efficiently. Exact search can remain
exponential. New constraints enter with a complete-assignment predicate and may
add stronger propagation, explanations, and specialized compilation later.

## Semantic contract

### Two compatible execution modes

**Operational Core programs** keep their existing deterministic execution
semantics, including ordered actions, destructive updates, and conflict policies.

**Declarative finite models** define explicit variables, initial domains,
immutable context, deterministic derived properties, hard constraints, and pure
scores independently of the search strategy. For the initial scoreable rule
fragment, use finite positive derivation with no destructive actions or fresh
object creation inside closure. Context preparation may use existing operational
programs before freezing the model. Additional rule fragments require explicit
validation and their own semantic tests before admission.

Do not claim that arbitrary legacy rule programs have a schedule-independent
fixed point. An unsupported rule fragment is rejected for declarative queries
while remaining usable through the operational API.

### Feasibility, objectives, and probability

A hard constraint is a predicate on a complete configuration and its declared
derived properties. Propagation is a sound partial-state implementation of that
predicate; complete solutions must pass final validation. Initial domains are
fixed during search, with reductions reversed by rollback. Domain construction
and widening belong to preparation or a new model revision.

General optimization accepts an explicit objective, initially a scalar integer
linear objective or a declared sum of factor contributions. Optional bounding
implementations must be admissible. A factor with no useful bound may still be
evaluated at complete assignments; the search must not invent a pruning bound.

Probabilistic queries use the distribution in the probabilistic specification:
hard feasibility times an optional base measure times exponentiated factor score,
normalized over complete assignments. A Markov model can supply the base measure.
Each factor is counted according to its declared scope and multiplicity, whether
variables were decided by search or fixed by propagation. Search priorities and
legacy `CHOICE` weights are not probability factors.

General CSP objectives need not be probabilities. Minimum-cost generation and
maximum-probability generation are distinct declared queries when their models
differ. Preserve room for explicit variable-order, smoothing, and other Markov
objectives without choosing their semantics implicitly.

### Results and numerical guarantees

Result objects separately record termination reason, whether a solution exists,
whether enumeration or proof completed, objective value, incumbent, valid bound
when available, backend, and numerical representation. Interrupted search with
no solution is unknown, not infeasible. Interrupted search with an incumbent is
feasible, not optimal unless an independent valid bound closes the gap.

Keep global incumbents across sibling rollback; restore branch-local objective,
domain, fact, and propagation state together. Report bound scope correctly: a
bound on one branch is not automatically a bound on all unexplored work.

Exact combinatorial optimization is initially guaranteed for integer objectives.
Rounded log-costs optimize the rounded objective. Floating-point probabilistic
inference must state its arithmetic and tolerances; exhaustive search alone does
not certify a real-valued optimum under unsafe rounding. Never silently substitute
approximate sampling for an exact request.

## Target architecture

The Python API and textual language compile to the same immutable model
representations: variables/domains, rules, hard constraints, factors, objective,
and query. Model validation and backend capability analysis are explicit stages.

Use specialized state representations behind small protocols:

- **Fact store and matcher:** retain relational indexes and incremental matching.
- **Domain store:** own compact finite domains, reductions, and reversible trails.
- **Propagators:** read domains, emit justified reductions, and declare dependencies.
- **Coordinator:** exchange relevant fact/domain events and establish joint closure
  before inspecting choices or accepting a solution.
- **Search controller:** depend on a reversible problem-state protocol, not directly
  on `InferenceSession`; own branching, limits, incumbents, and proof accounting.
- **Factor evaluator:** observe declared closed states without side effects; use
  cached or incremental scoring only with tested dependency invalidation.
- **Backend adapters:** compile supported fragments and preserve model identifiers,
  solution projection, objective meaning, and explanation references.

A common checkpoint boundary coordinates independent component trails. Immutable
compiled definitions can be shared; branch state cannot leak between alternatives.
Legacy candidate-fact models use an adapter with explicit ownership and direction
of updates, preventing duplicate facts, feedback loops, and domain divergence.

Rule-only execution does not instantiate CSP state. CSP-only execution does not
instantiate the rule engine. Mixed execution pays for the required communication.
Implementation module and class names are chosen during extraction, not frozen here.

## Phased implementation and acceptance gates

| Phase | Deliverable | Exit criteria |
|---|---|---|
| 0. Baseline | Versioned conformance manifest, reference checkout, strengthened example oracles, reproducible benchmark inputs | Explicit non-Bach core/application suite passes; exclusions and skips documented; complete-result comparisons for selected rulebases; benchmark commands and acceptance thresholds fixed before changes |
| 1. Semantic model | Architecture decision record, typed model/query/result interfaces, validators, tiny independent enumerator | Rule-only, CSP-only, mixed, and scored toy models have explicit meanings; unsupported scoreable rules fail clearly; legacy behavior is unchanged |
| 2. Domain kernel | Standalone trailed domains, propagation queue, constraint protocol; migrate existing persistent propagators | Every current constraint passes independent support/soundness and rollback oracles; CSP feasibility runs without an inference session; candidate-fact adapter agrees with legacy results |
| 3. Runtime composition | Fact/domain bridge, shared checkpoint coordination, dependency scheduling | Mixed closure and nested rollback match reference observables; generated event sequences reveal no stale caches, lost derivations, or sibling leakage |
| 4. Search and optimization | Generic search-state interface, heuristics, native branch-and-bound, limits and proof statuses | Tiny CSP solution sets and optima match enumeration; valid bounds never exceed/minimize past true residual optima; interrupted, unsatisfiable, tied, root-solved, and negative-cost cases behave correctly |
| 5. Factors and Markov application | Pure objective scoring; fixed-order Markov tables and explicit initial/terminal conventions; user hard constraints | Total scores are independent of branching and propagation; realistic Markov optimization benchmarks run; the six-model probe becomes a maintained test; each supported additional Markov objective has its own specification and oracle |
| 6. Common inference backends | Exact finite enumeration/weighted-search reference and regular-BP adapter | On overlapping supported models, full scores, partition values, marginals, and conditional branch masses agree within declared arithmetic; unsupported exact requests and exhausted resource limits remain explicit |
| 7. Language and migration | Textual model/query syntax, formatter, Python parity, compatibility facades, tutorials and migrated examples | Text and Python models have identical validated meaning; rule, CSP, mixed, optimization, and probability examples run from installed packages; existing Core programs still pass conformance |
| 8. Performance and promotion | Profile-directed kernel improvements, comparison report, final API boundary | Correctness gates pass; workload-specific performance budgets met; known limitations documented; remove replaced internals only after equivalent paths and packaging have been validated |

Phases 2 and 3 are developed as small extractions with adapters, not as a
flag-day state migration. Start language examples and performance measurement in
Phase 1; their later phases complete and validate them. Each phase ends with a
reviewable working system. Phases 0–5 deliver the primary rules/CSP/optimization
redesign; phases 6–8 complete its shared probabilistic surface and promotion.

## Verification strategy

The current checkout collects 676 core/application tests and 233 research tests.
This inventory is a starting point, not proof of future correctness. The audit
ran 71 focused tests successfully; it did not rerun the full suite.
These are pre-separation counts, not the size of the future redesign gate. Phase 0
must identify Bach-dependent tests even where they currently live under `tests/`,
and publish an explicit non-Bach test manifest. The 233 research tests are not a
required redesign gate. No existing tests or CI jobs are removed by this plan.

Use four kinds of evidence:

1. **Independent semantics:** brute-force predicates, complete objective evaluation,
   and finite probability sums on small models. Preserve simple implementations
   independent of optimized kernels.
2. **Differential compatibility:** old/new matching, legacy/native CSP, forked/trailed
   search, Python/text models, and generic/regular inference on shared fragments.
3. **Generated interaction tests:** add/retract, multiple supports, negative premises
   in operational mode, nested checkpoints, domain reductions, failed branches,
   tied solutions, and parameter or model changes invalidating caches.
4. **Real applications:** documented rulebases, Spinoza, Sudoku, CSP examples,
   and maintained corpus-independent Markov models. Check complete relevant outputs and
   forbidden outputs rather than only the presence of a few expected facts.

### Non-Bach validation portfolio

| Family | Existing executable problems | Required strengthening |
|---|---|---|
| Rules | Fifteen catalogued rulebases, including Hanoi, monkey-and-bananas, Petri nets, geometry, dates, recursive arithmetic, and triangle closure; Spinoza reasoning | Complete observable outputs for representative cases; forbidden conclusions; matcher parity and mutation/rollback sequences |
| Pure CSP | Queens, magic and Latin squares, Sudoku, SEND+MORE=MONEY, Golomb rulers, car sequencing, curriculum scheduling, balanced coloring | Satisfiable and infeasible variants; complete small solution sets; all existing constraints checked against independent predicates |
| Mixed rules and CSP | Curriculum and coloring with rule-derived reports; hybrid Sudoku; rules observing propagated singleton domains; staged search across rule groups | Bidirectional rule/domain interaction through multiple closure rounds; failure after derivation; nested and sibling rollback with provenance |
| Factors and optimization | Pure-factor fixtures; temporary six-model Markov optimization probe | Maintained non-musical allocation/scheduling example with preferences; exact integer objectives; score invariance; admissible bounds and honest interruption/proof statuses |
| Probabilistic backend agreement | Finite fixtures to be added using small synthetic Markov models | Complete scores, partition mass and conditional masses from independent enumeration versus generic inference and regular BP |

The existing mixed application reports demonstrate composition, but are not a
substitute for tests where rule consequences change subsequent propagation.
Add tiny exhaustive mixed models before replacing the coordinator. Examples
should exercise constraints -> derived properties -> further restrictions ->
factor score, with branch failures and rollback at each boundary. These are
new acceptance fixtures, not claims about coverage already present.

Add specific optimization assertions: objective invariance under variable/value
ordering; propagation-fixed values counted; bounds checked against enumerated
completions; incumbents preserved on limits; no false infeasibility or optimality;
constant offsets, negative coefficients, ties, and numerical representation.

For deterministic operational programs compare documented ordering, statuses,
facts, and explanation behavior. For declarative models compare feasible sets
and scores, allowing search order and work counters to improve. An old/new match
alone cannot establish correctness if both share a defective implementation.

Keep redesign CI split into fast tests and expensive non-Bach integrations;
run performance suites separately. Bach research validation belongs to its
separate project. Vendored external rule corpora are not counted
as passing tests until adapters and semantic compatibility have been established.

## Performance acceptance

The [performance baseline and comparison ledger](performance_baseline.md) fixes
the initial non-Bach workloads, collection protocol, investigation thresholds,
and measurements to add as the redesign proceeds.

Phase 0 freezes case sizes, seeds, environments, metrics, and per-workload budgets.
Use paired runs against the reference with raw samples; separate model preparation
from propagation/search and report peak memory. Do not choose a favorable case
after seeing results or impose fragile millisecond thresholds on ordinary CI.

The performance objectives are:

- preserve rule-only throughput and memory within predeclared measurement tolerance;
- reduce pure-CSP orchestration cost on fixed-search workloads by eliminating
  fact/provenance materialization that the model does not request;
- measure mixed-model bridge overhead explicitly;
- demonstrate useful native optimization against repeated-feasibility baselines,
  reporting time to first incumbent and time to proof separately;
- scale Markov tests over length, alphabet, order, table density, constraint
  combinations, and cost range, including infeasible and difficult-to-prove cases.

Prioritize maintained table supports, cheap bounds for linear inequalities,
incremental domain scheduling, and reduced choice materialization if profiles
confirm their importance. More elaborate GCC or matching optimizations follow
evidence. A failed budget requires investigation and a documented scope decision;
it must not be hidden behind a correctness pass or a changed benchmark.

## Explicit follow-on scope

Exact MLE, structure learning, richer scoreable rule fragments, additional global
constraint families, a Rust solver adapter, parallel search, and advanced
memoization remain separately gated extensions. Preserve interfaces for them,
but do not require them all to finish the runtime redesign. Bach learning and
generation are outside this project scope and are not acceptance gates. Future
generic learning features retain the statistical acceptance criteria in the
probabilistic and learned-factor specifications.

The first Markov application does not by itself claim a complete reproduction of
Pachet and Roy (2011). Variable-order activation, smoothing, highest-order and
algebraic objectives require a separate scope and semantic comparison.

That follow-on work is now ordered in the
[Markov constraints action plan](markov_constraints_plan.md), including the LSDB
Blues corpus, complete scoring semantics, and measured propagator improvements.

## Completion checklist

- Existing operational programs retain documented behavior and explanations.
- Pure CSP models execute independently of the rule engine.
- Every existing persistent constraint is available through the new core.
- Optimization returns independently verified objectives and honest proof statuses.
- Mixed rules, constraints, and factors pass exhaustive interaction tests.
- Generic and specialized inference agree wherever their capabilities overlap.
- Textual and Python interfaces share one validated model and result contract.
- Installed examples and compatibility checks pass on supported Python versions.
- Published benchmark evidence meets the budgets fixed before implementation.
- Documentation distinguishes implemented guarantees from proposed extensions.

The current implementation and next gates are tracked in
[redesign progress](redesign_progress.md). The original completion checklist above
continues to govern promotion; working components do not by themselves establish
completion of the whole redesign.
