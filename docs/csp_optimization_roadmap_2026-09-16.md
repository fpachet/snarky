# CSP optimization roadmap after the Prune baseline

Status: **in progress**, 16 September 2026. The
[first diagnostic/arithmetic slice](performance_csp_arithmetic_2026-09-16.md)
implements opt-in observations, profiles slow cases, improves exact inequality
and binary filtering, and removes a profiled incident-index setup cost. The
remaining phases below are planned. This is the active plan for the Python finite runtime,
based on the [Prune baseline](performance_prune_2026-09-16.md), source inspection
at `5f66b0b`, and the existing rule/CSP/mixed and Markov regression portfolios.
The earlier [solver plan](solver_optimization_plan.md) remains the history of
optimizing the legacy fact-backed CSP path.

The [second slice](performance_csp_equality_2026-09-16.md) adds shared exact
signed equality filtering with bounded bitsets/sparse fallback and mask-tagged
domain projections. The [third slice](performance_csp_nvalue_2026-09-16.md)
implements native NValue, bounded cover checks and a decomposition ablation.
The fresh full run reaches **52/59**, including all six NValue cases, while Prune
remains at **59/59**. Optimization remains **3/5 versus 5/5**.
A general propagation resource budget, search/objective improvements and compact
domains remain open.

The [fourth slice](performance_csp_alldiff_2026-09-16.md) promotes a measured P6
all-different hotspot: bounded bitset graphs preserve exact Régin filtering.
A P2 shortcut avoids rebuilding unchanged native domain masks. These reduce
work per revision without changing branching or introducing objective cuts.
P4's search/bounding work and P5's compact-domain contract remain open. Fresh
queens profiles still show numeric conversion, matching and domain materialization
as material costs. This identified immutable numeric/index views under P2 and
propagated improving objective cuts under P4 as follow-ups; faster graph traversal
alone did not remove the seven remaining timeouts.

The [fifth slice](performance_csp_objective_2026-09-17.md) implements P4's
propagated improving cuts for integer linear objectives, including mixed models
and rollback-safe incumbent handling. FT06's paired gain is about 1.10×; knapsack
and packing still time out at five seconds. The next investigation is incumbent
quality and variable/value ordering, measured separately from propagation cost.
P2 numeric/index views and P5 compact domains remain open.

## Objective and boundaries

Make Snarky's Python CSP and exact optimization engine materially more efficient,
add native NValue and genuine compact integer domains, and preserve the language's
rules/constraints/factors semantics. Prune is a compiled Rust reference for
capabilities and end-to-end performance. Absolute Rust speed parity is not an
acceptance condition; language overhead does not excuse avoidable algorithmic work.

Success means improved completion, incumbent quality, proof time and memory on
unchanged problems, backed by independent correctness checks. All constraints
retain exact complete-assignment semantics. A propagator's documented consistency
strength is a separate promise: weaker filtering must be explicit, never silently
substituted for an existing exact support algorithm.

The existing baseline remains frozen: 54 available instances, 59 workloads,
Prune 59/59 completed and Snarky 47/59 under five seconds, with three repetitions.
Optimization completion is 5/5 versus 3/5. The 20 CSPLib and 11 reserved instances
are still missing upstream; obtain their actual definitions and provenance.
Do not invent reserved parameters or tune against them. Work on the available
portfolio proceeds independently. Bach remains a separate project.

## What the evidence actually suggests

Process and native times below are measured medians; counters are from a recorded
Snarky sample. These are starting hypotheses, not profiler findings.

| Cases | Observed evidence | First investigation |
|---|---|---|
| Magic sequence 20/40 | Size 20: 1.168 s process, 1.042 s native, 32 nodes; size 40 times out | Weighted equality propagation and domain materialization; inspect work per node before changing search |
| Packing 40 | 1.961 s process, 1.837 s native, 275 nodes, zero failures | Cost of large weighted sums and repeated revisions |
| Queens 50/104/150 | Size 50: 1.315 s process, 52 nodes, 6,867 revisions; larger cases time out | Linear channels, all-different graph work, queueing/copying; then search |
| Incremental Latin 16 | 0.810 s process, 150 nodes, zero failures | All-different revision cost and redundant domain conversion |
| FT06 optimization | 2.739 s process, 615 nodes, 74,994 revisions, optimum 55 proved | Linear inequalities, scheduling, objective cuts and branching |
| Magic square 5; pairwise pigeonhole 10 | Both time out | Obtain partial traces; distinguish search explosion from propagation cost |
| Knapsack and packing optimization | Both time out; no retained partial counters/incumbents in this run | Observe first incumbent, bound progress and proof work before choosing a remedy |
| Four Dominating Queens cases | All time out with Snarky's NValue decomposition | Native NValue filtering, representation size and search policy |
| Billion-domain chains | Both compile to zero variables and zero constraints | Add genuine runtime domain benchmarks; these timings reveal no storage capability |

Source inspection already identifies actionable candidates:

- [Weighted sums](../src/snarky/finite/kernels.py) construct reachable-sum sets
  even for inequalities, then use only the minimum or maximum remaining sum.
- [Propagation](../src/snarky/finite/propagation.py) converts each scoped domain
  to a Python set and retains it back into the store on every revision.
- [Domains](../src/snarky/finite/domains.py) use reversible masks over explicitly
  enumerated values; removals and snapshots materialize values. They are compact
  for a small alphabet, not for an interval containing a billion integers.
- [Search](../src/snarky/finite/search.py) materializes branch values and objective
  snapshots. At the baseline, integer branch-and-bound checked bounds without
  propagating an improving cut. The fifth slice now supplies that mechanism for
  integer linear objectives; stronger bounds and ordering remain open.
- Matching reuse for all-different, table support bitsets, incident scheduling,
  and the nonnegative SUM bitset path already exist. Improve those implementations;
  do not schedule them as missing features. GCC still repeats flow support checks.

## Ordered delivery plan

| Order | Deliverable | Primary targets | Dependency |
|---|---|---|---|
| P0 | Reproducible diagnostics and controlled comparisons | All slow/limited cases | Frozen baseline |
| P1 | Cheap exact arithmetic propagation | FT06, queens, sums, packing | P0 correctness/counter tools |
| P2 | Lower Python propagation overhead | Broad finite and mixed workloads | P0 profiles; retain P1 ablation |
| P3 | Native NValue | All six NValue cases | P0 oracles, P2 domain/event interface |
| P4 | Search and optimization improvements | Magic 5, pigeonhole, knapsack, packing, FT06 | P0 diagnostics; measure after P1–P3 |
| P5 | Genuine compact integer domains | New large-domain runtime tests | Design during P0; implement after P2 interface stabilizes |
| P6 | Remaining globals and stronger modeling | All-different, GCC, tables, scheduling | Profile evidence; P5 for wide-domain paths |
| P7 | Validation, release evidence and missing suites | Full portfolio and applications | Each candidate frozen before validation |

Each phase is a separate reviewable change, with its own baseline/candidate
record. P5 interface design starts early so P2 does not hard-code another
explicit-value-only interface. Its migration is isolated from the initial
arithmetic and NValue work. Optional P6 items are promoted only by evidence.

### P0 — make slow runs explain themselves

Keep the original fresh-process five-second measurements and add separately
labeled diagnostic runs. Collect bounded node traces and longer, declared time
budgets; a result at 30 seconds must not replace a historical five-second timeout.

Record construction, root propagation, search and output costs separately;
per-constraint-family revisions, effective revisions, values removed, queue events,
materializations, nodes/failures, depth and bound calls. On optimization record
first feasible solution, every incumbent, time to the known target, proof time,
and valid bounds. A known target is an external validation oracle, never an
undisclosed search hint. Golomb's supplied whole-ruler lower bounds remain explicit.

Add opt-in, flushed progress records so an external kill does not discard every
counter and incumbent. Keep cooperative limits and an external hard safety cap;
check expensive kernels for safe interruption points. A limit or interrupted
revision must unwind safely and must never produce a proof status. Distinguish
a root bound from a valid bound over the remaining search frontier.

Use separate CPU profiles, allocation traces and process-RSS measurements.
Instrumentation remains off in primary timing runs. Add an in-process repeated-solve
measurement for library use, alongside the existing process measurement; never
compare Snarky internal time directly with Prune whole-process time.

Implement a controlled policy mode where supported: explicit variable/value
ordering, matching branch partitions, symmetry and bounds. Record unsupported
annotations instead of pretending to honor them. Reconcile node/failure meanings;
propagation counts are not interchangeable across engines. Use domain-state replay
for propagator comparisons even when search trees cannot be matched.

**Gate:** every slow family has a reproducible diagnostic artifact and a stated
hypothesis; timeout records remain truthful; instrumentation overhead is measured.

### P1 — arithmetic improvements with exact support

1. For signed linear inequalities, use per-variable contribution extrema and
   exclusion totals instead of reachable-sum enumeration. On explicit independent
   domains this can preserve the current supported values exactly. Handle signed
   coefficients, holes, fixed variables, large integers and repeated-term
   normalization; use exact integer arithmetic and correct signed rounding.
2. Add direct binary affine equality/order channels where applicable. Optimize
   disequality with singleton tests instead of repeated pairwise support scans.
   These are generic verified patterns, not benchmark-name special cases.
3. For weighted equalities, add an inexpensive bound prefilter, normalize signed
   contributions, and select sparse sets or offset bitsets by reachable span and
   density. Cap work by explicit budgets. Retain the exact reference fallback;
   if no exact path fits the budget, report a resource limit. Expose any
   bounds-only mode separately with weaker consistency documented.
4. Measure Boolean sums/cardinality patterns before introducing specialized kernels.
   Keep SUM and LINEAR_SUM decisions consistent where their semantics coincide.

**Gate:** identical supported domains to exhaustive oracles on small signed/holey
cases, rollback equivalence, and paired gains on weighted sums/FT06/queens without
hiding regressions. Fixed-work speedups and changes to propagation/search order
are reported separately.

### P2 — remove repeated Python work

Profile first, then introduce read-only domain views, domain version stamps and
change summaries so propagators need not rebuild every set/tuple on every call.
Cache immutable numeric/index mappings. Provide a compatible adapter for the
shared reference kernels and the legacy fact-backed runtime.

Optimize queue scheduling only for demonstrated redundant work. Test duplicate
suppression, deterministic ordering and wake conditions. Cache extrema and domain
cardinality where useful; invalidate them on narrowing and rollback. Avoid full
objective snapshots when a bounded scope suffices. Make removal explanations lazy
or compressed while preserving required provenance and contradiction attribution.

Keep rule consequences, domain changes and propagator caches synchronized across
nested checkpoints, failed branches and sibling branches. A valid matching may be
reused only after its validity is checked in the restored domains.

**Gate:** the fixed point and solution ordering required by each API are preserved;
fixed-policy runs retain comparable work; allocation/RSS and timing both improve
or any explicit tradeoff is justified. Pure CSP uses no rule engine; mixed rules
and legacy callers remain covered by the regression gate.

### P3 — native NValue as a first-class constraint

**Implemented first version:** native and legacy APIs, both textual surfaces,
independent exact evaluation, matching/disjoint-domain/cover bounds, tight-count
specializations and budgeted cover feasibility. The historical encoding remains
selectable. See the [implementation and measurements](performance_csp_nvalue_2026-09-16.md).
Scratch state is rebuilt per revision. Connected-component decomposition and
incremental support/matching reuse remain possible follow-ups, subject to profiles.
The scope below records the original plan; it does not imply general GAC.

Add `NValueConstraint` with an exact evaluator for
`k = |{x1, ..., xn}|`, where k may be a constant or finite variable. Cover empty
scopes, constants, repeated references, holes and k sharing a scoped variable.
Define those semantics before optimization. Expose it in the finite API, textual
language and supported persistent vocabulary, with rollback and failure causes.
The benchmark importer selects native NValue; retain the old decomposition as an
explicit ablation so results remain interpretable.

Build filtering in steps:

- Distinct fixed values and other sound lower bounds; union/cardinality upper
  bounds; empty-domain detection and feasible bounds on k.
- Exact k=1 intersection and k=number-of-distinct-scoped-variables all-different
  specializations when their preconditions hold, including constants and aliases.
- Connected-component reasoning, matching bounds on the maximum distinct count,
  and sound disjoint-domain/cover lower bounds on the minimum count. Every
  bound or pruning rule requires its own justification and exhaustive tests.
- Incremental occurrences/supports and selective stronger filtering only when
  profiling demonstrates benefit. Any exact cover/support search is budgeted;
  exhausting its budget leaves unproved values in place.

Do not promise general domain consistency from these bounds. Report the achieved
filtering strength. NValue's internal Boolean channels need exact equivalence;
a positive-fact guard is not a substitute for Boolean reification.

**Gate:** exact complete solutions match the old decomposition and independent
oracles, including variable k and aliases; all six cases get new time/node/memory
records. Eliminating the four Dominating Queens timeouts is a performance target,
not a correctness assumption or guaranteed outcome.

### P4 — search effectiveness and optimization proofs

Use P0 evidence to separate finding a good solution from proving it optimal.
Compare current dom/wdeg, controlled annotation-compatible branching and optional
value ordering on frozen training cases. Existing learned-impact behavior in the
legacy solver must not be assumed to exist in the direct finite solver. Promote
policies by portfolio evidence, not one favorable puzzle.

**Implemented in the fifth slice:** integer linear objectives propagate an
improving incumbent cut:
minimize f with f <= incumbent-1; maximize f with f >= incumbent+1. Include offsets
and signed terms exactly. Manage the global incumbent independently from reversible
branch state; apply the current cut after rollback without retaining stale branch
consequences. Keep rational-product Markov objectives on their valid exact path.

Investigate admissible problem bounds only for explicitly declared or verified
structures: a fractional-knapsack relaxation under its stated coefficient
conditions, packing capacity bounds, and scheduling resource/precedence bounds.
Publish recognition conditions and safe fallbacks. Never insert the benchmark's
known optimum as an invented model constraint.

For pairwise pigeonhole, distinguish cheap disequality propagation from the global
reasoning needed to prove infeasibility. Any clique-to-all-different recognition is
an explicit compiler/model variant; preserve the original decomposed benchmark.
Nogoods, restarts and conflict-directed search are later options if profiles show
repeated search, with an explanation and rollback design before implementation.

**Gate:** small optimization oracles validate every bound and cut, seeded/unseeded
runs are separate, and limits preserve feasible/unknown/optimal distinctions.
Report both incumbent progress and proof effort for knapsack, packing and FT06.

### P5 — compact domains that survive beyond compilation

This is a domain/model/search contract change, not removal of the importer's size
limit. Preserve ordered explicit symbolic domains. Add compact integer interval
and interval-set domains, choosing explicit/bitset storage only for affordable
spans. A bit per integer across a billion-value span is not an acceptable solution.

Define membership, cardinality, extrema, singleton access, intersection, bound
updates, value/range removal and trailed rollback without enumeration. Represent
large removals as intervals or deltas; do not expand them for diagnostics. Adapt
`FiniteVariable`, snapshots, numeric objectives, predicates and propagation views.
Make materialization an explicitly budgeted operation.

Add interval splitting/bound branching so search never constructs a billion-value
choice tuple. Keep declared ordering for existing explicit domains and label the
new branching policy. Ensure partitioned branches are disjoint and exhaustive.
Wide-domain comparisons/linear bounds must work without expanding domains;
all-different, GCC, tables, factors or inference backends that need explicit values
must use a documented supported path or return an explicit capability limit.
The mixed-rule adapter must not silently emit a billion candidate facts.

Add a separate versioned runtime suite, bypassing compiler elimination:

- Unanchored billion-span chains with known feasible assignments and remaining
  freedom; assert nonempty solver variables/constraints after compilation.
- Wide-domain bound narrowing, holes, contradictions and nested/sibling rollback.
- Small equivalents compared exhaustively against the explicit-domain backend.
- 256/2,048-variable memory and preparation scaling, varying span independently
  of variable/interval count. Check bounded memory scaling rather than one timing.

Keep the two compiler-solved upstream cases unchanged and labeled. Add raw bridge
inputs to prove acceptance without materialization, and interval-branch search
cases with known answers; do not claim arbitrary huge-domain search is easy.

**Gate:** memory/preparation scale with stored intervals and variables rather than
numeric span; no hidden enumeration in accepted paths; exact bounds and branching
pass differential tests. Unsupported operations fail before allocation.

### P6 — profile-driven global and modeling improvements

| Candidate | Existing foundation and proposed extension | Evidence required |
|---|---|---|
| All-different | Matching repair and Régin filtering already exist. Reduce graph rebuilding and repeated SCC/reachability work; consider bounds filtering for huge integer intervals as an explicit consistency mode. | Latin/queens and support-oracle traces, failed repair and rollback; no replacement justified merely by algorithm age |
| GCC | Replace repeated per-value flow reconstruction with reusable feasible flow/residual reasoning where justified. | Add native GCC tests/benchmarks: the current compiled portfolio does not establish GCC coverage; include unspecified-value semantics and reversible capacities |
| Tables | Existing per-value row masks are the baseline. Evaluate incremental active tuples, residues and sparse masks. | Markov and generic table workloads with sparse/dense supports, deletions and rollback |
| Affine views | Avoid materialized x+offset auxiliaries where exact views preserve semantics. | Queens channels, objective/constraint alias tests; label internal representation changes |
| Scheduling/packing globals | Add disjunctive/no-overlap, cumulative or packing filtering only for a demonstrated modeling need. | Explicit model variants against the original linear formulations, feasibility and optimality oracles |
| Reification | Design full Boolean equivalence and implication as distinct contracts when needed by these models. | Truth-table, variable-alias, fixed-point and rollback tests; preserve existing positive-fact guard semantics |

These are separate changes, not a commitment to implement every candidate before
shipping useful improvements. A Rust backend or native extension can be evaluated
later behind the finite-model boundary if Python profiles justify it; it is not
the first response to the Rust/Python timing difference.

## Acceptance, reporting and first implementation slice

For each phase retain code/input hashes, settings, raw samples, source snapshot,
independent checks, counters, time and memory scope. Use the existing
[performance ledger](performance_baseline.md) for paired same-machine candidate
comparisons. Keep the five-second portfolio score and timeout list, and publish
longer-budget outcomes separately. Reaching 59/59 is a useful aspiration, not a
substitute for correctness, generalization or memory evidence.

Run focused exhaustive/rollback tests first, then the non-Bach gate and relevant
rule/mixed workloads before accepting runtime changes. Shared-kernel changes must
also cover legacy CSP callers. Protect exact Boulez optimality and the melody/factor
results, including sampling/counting semantics if shared representations change.
Use independent Gecode validation for the Prune models. Freeze each candidate
before using newly supplied reserved instances; once their results influence a
revision, record that exposure and stop treating them as untouched validation.

Every accepted change gets a short report separating implementation speed,
filtering strength, policy changes and model variants, including regressions.
Do not rerun expensive suites for documentation-only changes.

**First implementation slice:** P0 observability and the slow-case dossier, followed
by P1 signed linear inequalities and direct binary channels with exhaustive support
oracles. Then tackle equality-sum and domain-materialization costs identified by
those profiles, and introduce native NValue. Start the compact-domain contract
review during P0 so that its later implementation fits the same reversible store.

The [first-slice report](performance_csp_arithmetic_2026-09-16.md) records its
implemented subset and paired evidence. The second slice implements P1 exact
weighted equalities and a P2 domain-projection cache; the third implements the
first P3 native NValue version. P0 matched-policy comparisons, general P2 domain
views, P4 search/objective improvements and P5 compact domains remain open.
These measured improvements do not imply completion of every item in those phases.
