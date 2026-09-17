# Declarative finite model contract

Status: implemented opt-in, pre-1.0 interface, 16 September 2026. This records
the semantic and architectural decisions of the [redesign](redesign_plan.md),
without changing the frozen operational Core language.

## Current executable surface

`snarky.finite` exposes immutable `FiniteModel`, `FiniteVariable`, `Query`,
`Solution`, and `QueryResult` objects. It does not add names to the frozen
top-level wildcard API. Existing persistent constraint classes now live in
`snarky.finite.constraints`; `csp_solver.persistent_constraints` reexports the
same objects. Existing CSP search remains available as the legacy implementation.

`enumerate_model` is the independent reference. It enumerates the Cartesian
product, computes deterministic closure, checks complete constraint predicates,
and evaluates the explicit objective. It performs no constraint propagation or
objective-bound pruning. The native `solve` uses domain bit masks, an incident
propagation queue, reversible iterative DFS, and exact integer or rational-product
branch-and-bound.

The native backend supports pure finite CSPs and mixed models. Pure CSPs use no
inference session. Mixed models coordinate the existing incremental matcher with
the native domain store. The enumerator supports the same declarative fragment.
`PARTITION` and `SAMPLE_EXACT` now use generic finite inference; an optional
`regular_bp` backend compiles its supported bounded-window fragment. Unsupported
backend capabilities produce explicit `UNSUPPORTED` results.

## Meaning of a model

A decision variable has an atom identifier and an ordered finite domain of
ground terms. Empty domains denote infeasibility. A zero-variable model has one
empty assignment. Duplicate identifiers are invalid; duplicate domain values
are normalized without changing order.

An assignment produces `(variable value chosen)` facts. Context cannot forge
these value facts for declared decision variables. A complete configuration is
the deterministic closure of context and assignment facts. Constraints are
predicates over that configuration. Propagation is an implementation of pruning,
not the definition of feasibility; native solutions are independently checked.

Existing all-different, sum, linear sum, comparison, element, count, NValue, GCC, table,
and lexicographic constraints have direct complete-assignment evaluators in
`finite/predicates.py`. `FactConstraint` requires or forbids ground closed facts.
`PredicateConstraint` admits a named, trusted Python callback over an immutable
assignment restricted to its declared scope and an immutable closed fact set.
`GuardedConstraint` activates an existing constraint when a declared positive
ground fact is present. The coordinator alternates propagation and positive rule
closure to a joint fixed point. Checkpoints cover both stores, so facts,
derivations, domain reductions and their reasons roll back together. A forbidden
fact can reject a partial branch; a required fact is checked only on completion.

Native `NValueConstraint` counts distinct assigned scope values plus optional
literal constants. Its count may be fixed or variable, including a variable also
in the scope. Repeated references do not add multiplicity; empty scopes are valid.
The finite text form uses `KIND NVALUE`, `SCOPE SEQ[...]`, `TARGET k` (or an integer)
and optional `CONSTANTS SEQ[...]`. Its bounded propagator is sound but does not
promise general domain consistency; complete-assignment semantics remain exact.
See [the persistent vocabulary](persistent_constraints.md#nvalue) for details.

Callbacks must return a Boolean and obey the documented purity contract; no
arbitrary Python is parsed from the model language. A callback without a
propagator is checked at complete assignments, not guessed at partial states.

## Initial scoreable rule fragment

Admit function-free, positive, range-restricted rules over flat triples with
scalar components. Positive fact premises and already-bound scalar comparisons
are supported. Actions only add flat triples, using a fixed relation other than
the reserved assignment relation `value`. Every head variable is bound by a
positive premise. Context and decision values are scalar when rules are present.

Reject negative/aggregate/computed premises, focused matching, destructive actions,
fresh values, arithmetic constructors, unbound head variables, and recursive term
construction. The active scalar vocabulary is finite, so the set of possible
triples/statuses is finite and positive closure is schedule independent. Merely
banning `FRESH` would not ensure termination: nested term construction can also
generate an infinite universe.

All rejected constructs retain their existing operational Core meaning. They
have not been removed from the parser or old inference engine. Broader declarative
fragments require a separate semantic decision and tests.

## Objective and search contracts

`LinearObjective` has integer coefficients and a constant offset. Repeated terms
are combined. Evaluation uses Python integer arithmetic without float conversion;
bounds are obtained from attainable extrema of each independent current domain.
These bounds remain valid with negative coefficients and arbitrary-size integers.

Optimization counts all objective variables, including propagation-fixed values.
Branching weights are not objective terms. The native controller retains its
incumbent outside reversible state, prunes with admissible bounds, and restores
the caller's domain state on exhaustion, early solution, limits, or exceptions.
MRV and dom/wdeg select variables; an explicit variable order or reversed value
order changes traversal without changing the model.

For a nonconstant `LinearObjective`, `solve` and `search` also propagate a strict
improving cut after an incumbent is found (or an initial assignment is validated).
Minimization uses `sum(terms) <= incumbent - offset - 1`; maximization uses
`sum(terms) >= incumbent - offset + 1`. Integer arithmetic handles signed
coefficients and arbitrary-size offsets exactly. Repeated objective terms have
already been combined by the model contract.

The cut enters the ordinary incident queue before existing constraints and is
rescheduled when its variables change. Cost-variable reductions therefore reach
defining sums, tables, other constraints and the mixed rule/domain fixed point.
The controller retains the latest cut across backtracking and supplies it on each
propagation call; domain reductions and derived facts remain reversible. The
immutable model is unchanged, and search restores the caller's state on every exit.
The cut has a unique synthetic explanation name, `__objective_cut` with underscores
added if necessary. Cut failures count as failed branches and cut revisions count
as constraint revisions; they do not increase an original constraint's search weight.

`objective_propagation=False` selects the former bound-check-only behavior for
controlled ablations. Feasibility/enumeration queries are unaffected. Constant
objectives use existing bound termination, without an empty linear constraint.
Factor and rational-product objectives retain their existing admissible bound
checks; this option does not synthesize cost variables or translate those objectives.
A strict cut seeks one optimal witness and does not enumerate all tied optima.
Custom `SearchState` implementations must accept the optional `objective_cut`
argument when enabling this feature; the provided native and mixed states do so.

`bounding="auto"` compiles an admissible min/max chain relaxation for table
objectives whose scopes span at most two preceding model variables and whose
initial edge-volume estimate is at most 100,000. It includes unconditional hard
constraints fitting that window and relaxes the others. Dynamic programming uses
the current branch domains; cached local edge costs depend only on the immutable
model. Other objectives fall back to local bounds. `bounding="local"` selects
that fallback explicitly. `value_policy="objective"` optionally orders candidate
values by their completion bounds. Neither option changes feasibility or scores.
Reaching a valid root bound proves optimality without traversing remaining branches.
The chain computation cooperatively respects the search deadline.

The current interrupted-search global bound is the bound from the propagated root,
not a falsely global version of the last visited branch's bound. It can be loose.
Completion reports the optimal objective as the bound. Incumbent objective history,
node, failure, pruning, and constraint-revision counters are returned separately.

`SOLVE` finds one feasible assignment; `ENUMERATE` can finish or stop at an explicit
limit. `MINIMIZE` and `MAXIMIZE` require an objective. Termination reason and result
status are distinct: no solution before a limit is `UNKNOWN`; an incumbent before
a limit is `FEASIBLE`; only a completed proof is `OPTIMAL` or `INFEASIBLE`.

The enumerator's nodes are complete assignments examined; native nodes are search
states entered. Do not compare these counts as equal units of work. Time checks
occur at safe boundaries and are cooperative, not preemptive thread cancellation.
The native time budget covers search; immutable model/table preparation occurs
before that timer and is measured separately in performance comparisons.

## Observing search progress

`solve(..., on_progress=callback)` and `finite.search.search(...,
on_progress=callback)` optionally deliver frozen `SearchProgress` observations.
The type lives in `snarky.finite.search`. Events are `start`, `node`, `bound`,
`incumbent` and `finished`; they expose entered-node, failure, pruning and revision
counts, depth, elapsed time, an incumbent if available, and the propagated root
objective bound. A node event precedes propagation, so its entered node may still
be unfinished. Incumbent events follow complete feasibility and objective checks.

`root_objective_bound` stays the root bound even when the final result proves a
tighter optimum. Only `progress.result` on `finished` carries a `QueryResult` and
its completion status. Earlier observations are not proofs or remaining-frontier
bounds. The observer is disabled by default; its time counts when enabled.
Callbacks are trusted code, must not mutate search state, and exceptions unwind
native or mixed checkpoints. Partition and exact-sampling queries reject this
DFS-specific observation option.

The [diagnostic worker](../benchmarks/csp_diagnostics.py) flushes progress records
and validated optimization incumbents before completion. Its collector preserves
partial logs on an external kill and flags a truncated final JSON line. CPU and
allocation instrumentation are separate from normal latency runs; see the
[first optimization report](performance_csp_arithmetic_2026-09-16.md).

## Compatibility and migration

`csp_solver.native.native_model` explicitly translates initial legacy candidate
facts and persistent constraints into the new representation. It rejects active
decision/value facts, legacy application rules, and implicit binary-constraint
facts that require separate compilation. Legacy weights remain search priorities;
they are not silently converted into objective or probability factors.

The shared filtering kernels were extracted without algorithm changes. The native
table filter adds immutable per-value row masks rather than scanning every allowed
tuple on every revision. Native domain checkpoints restore masks and removal
reasons; matching reuse is validated against current domains after rollback.

The [finite language](finite_language.md) compiles `.model` documents directly to
these Python objects. `snarky run` executes named queries and returns JSON;
`--explain` includes separate derivations, reductions and factor contributions.
Five examples ship as package resources, covering rules, CSP, linear optimization,
mixed scheduling and probability. The existing `.rules`, `.constraints` and
`.program` formats retain their behavior. Performance evidence and promotion
decisions are tracked separately in the [comparison ledger](performance_baseline.md).


## Pure integer factors

`FactorObjective` declares an integer offset and a sum of named factors.
`TableFactor` is a total integer function over explicit decision variables:
missing rows receive its declared default, **not zero support**. A separate
`TableConstraint` supplies hard support. Its domain bounds are local minima and
maxima over compatible rows, including the default exactly when some compatible
row is absent; adding per-factor bounds is sound even with overlapping scopes.

`IntegerFactor` pairs the existing `FactorDefinition` with an exact integer
parameter. Its pure premises observe a complete closed fact snapshot. Every
unique `(factor, ground scope)` contributes once. Multiple witnesses contribute
support and a witness count, not repeated energy. Different scopes contribute
separately. Python integers remain exact, including weights above float precision.
The older floating-point factor API retains its behavior unchanged.

General premise factors currently have no partial bound. Their presence disables
objective pruning, while feasibility propagation and exhaustive optimization
remain available. An interrupted query reports no objective bound in that case.
This is deliberate: lack of a bound cannot justify an invented pruning rule.

Solutions include separate immutable factor contributions, supporting facts and
witness counts, alongside rule derivations and domain reductions. Scoring neither
mutates the state nor consumes search weights. The reference enumerator uses naive
matching for factor observations; native search uses the incremental matcher on a
fresh snapshot. There is no cross-branch score cache to invalidate yet.

## Fixed-order Markov cost models

`MarkovCosts` declares an alphabet, order `k`, integer costs for initial `k`-symbol
blocks and subsequent `(k+1)`-symbol windows, and an optional terminal `k`-block
table. Missing rows have zero support. No smoothing or backoff is implicit.
`markov_model` compiles this to ordinary hard tables and table objective factors,
so users can add nonregular constraints and positive rules without a separate
search engine. An entirely empty support table makes the model infeasible.

Initial and terminal costs each contribute once. Transition costs contribute
once for each position after the initial block, including when propagation fixed
the symbols. Order zero uses the empty initial block (normally cost zero) and one
unary transition factor per position. Lengths shorter than `k` are rejected;
constructing a shorter marginal is not inferred from the source. For order zero,
the empty sequence has its declared initial plus terminal cost.

These are **cost models**, not automatically normalized probability models.
For the maintained six-model probe the costs are exact negative log2 values:
uniform initial probabilities and rows that permute `(1/2, 1/4, 1/8, 1/8)`.
Minimizing those costs is exactly Markov MAP under the hard constraints. Rounded
log-costs for general probabilities instead optimize the declared rounded
objective. Variable-order, smoothing and algebraic objectives remain separate
extensions with no implicit semantics.

Installed, corpus-independent examples run with:

```sh
python -m snarky.finite.examples
```

The scheduling example combines all-different, a rule-derived overtime property,
a guarded delivery constraint, and an integer preference score. The Markov example
combines pairwise transition costs, all-different on the first four symbols and
return-to-start equality. Both report their proved optimum and bound.


## Declared probability measure and common inference

`Measure` declares a product of nonnegative `WeightTable` base factors, multiplied
by `exp(score)` from optional integer table log-scores and the existing pure
floating-point `FactorModel`. Its meaning is exactly the probability specification:
hard feasibility times base measure times exponentiated score, normalized over
complete assignments. An omitted measure is uniform on hard-feasible assignments.
An optimization objective never becomes a probability weight implicitly.

Base-table entries become exact `Fraction` values; pass `Fraction(1, 3)` for one
third. A float input denotes its actual binary rational value, not a reconstructed
decimal intent. Missing rows receive the explicit default, zero by default.
`negative_log2_measure` explicitly converts an integer table-cost objective into
rational dyadic weights. It preserves the original Markov probe's probability
model; it cannot recover unrounded probabilities from rounded log-costs.

`infer(model, query, backend=...)` supports:

| Backend | Algorithm and capability | Arithmetic |
|---|---|---|
| `enumeration` | Independent complete-assignment enumeration and reference closure | Rational without log factors; float log-space otherwise |
| `weighted_search` | Native CSP/mixed enumeration followed by complete mass accumulation | Same arithmetic as enumeration |
| `regular_bp` | Public `vo_regular_bp` product BP; pure bounded-window hard constraints, base tables and table log factors | Floating point, including log partition values |

`solve` routes probability queries to weighted search; `enumerate_model` routes
them to reference enumeration. All consume the same `FiniteModel`. The common
inference result exposes partition and log partition, marginals, unnormalized
completion mass for partial assignments, conditional probabilities, factor
expectations and sampling. Expectations count Boolean factor scopes once;
table log-factor expectations refer to their declared numerical feature values.

Certificates identify `EXACT_ENUMERATION`, `EXACT_WEIGHTED_BACKTRACK` or
`EXACT_REGULAR_BP`. Here exact describes the complete inference algorithm, with
no beam, MCMC or truncated normalization. `arithmetic="rational"` additionally
guarantees exact arithmetic and uses integer random draws for sampling.
`arithmetic="float64_log"` explicitly allows floating-point rounding and underflow;
it is not a certificate of exact real arithmetic. Use `log_partition` when the
ordinary float mass underflows or overflows. Differential tests use absolute and
relative tolerances appropriate to their fixtures, including 1e-12 for log-mass
agreement. General numerical-error bounds are not claimed.

A limit reached before completing inference returns `UNKNOWN`, no normalized
partial distribution, and no allegedly exact sample. `ZERO_MASS` distinguishes
an unnormalizable distribution from ordinary hard infeasibility: a feasible
assignment can still have zero declared base mass. The generic implementation
materializes feasible configurations and is intended as a small exact reference
and general fallback; it has exponential time and memory in the worst case.

The regular adapter rejects rules, fact/callback/guarded constraints, premise
factors, and scopes requiring a larger memory window than configured. It defaults
to four preceding positions. Supported existing persistent constraints compile
through their independent complete-assignment predicates. It reports numerical
ranges it cannot encode as finite positive local edge weights; it does not replace
such an exact request with an approximation. Model variables determine sequence
order. The adapter adds forward marginal and feature-expectation accumulation over
the library's public backward-corrected transition masses, without copying its BP
algorithm. Arbitrary partial evidence is summed through those transitions.

Install the optional independent library from a checkout, for example:

```sh
python -m pip install /path/to/vo_regular_bp
```

The validated reference is `vo_regular_bp` 0.1.1, commit
`2f172dd4d6985f2ca21bdb978a870700d1535169`. The dedicated CI job pins that source;
normal core installations do not require it. Backend agreement tests cover the
six Markov models, all complete path masses, conditional branch masses, table
scores, marginals and expectations, resource limits, unsupported fragments, and
a 120-position independent chain that does not enumerate configurations.

Example sharing an optimization model with an explicit probability declaration:

```python
from dataclasses import replace
from snarky.finite import Query, QueryKind, infer, negative_log2_measure
from snarky.finite.examples import markov_probe_model

costs = markov_probe_model()
model = replace(costs, measure=negative_log2_measure(costs.objective))
reference = infer(model, backend="enumeration")
regular = infer(model, backend="regular_bp")
sampled = infer(model, Query(QueryKind.SAMPLE_EXACT, sample_count=10, seed=7))
```

## Exact rational-product optimization (Blues follow-on)

The Python API also accepts `RationalProductObjective(tuple_of_WeightTable)`.
It multiplies nonnegative exact rational table weights, independently of any
sampling measure or search decisions. An empty product is one. Zero objective
weight remains feasible unless a hard constraint forbids that assignment.
Missing table rows receive the declared default. Prefer `Fraction` inputs for
count-derived probabilities; floating inputs retain their exact binary value.

Both native search and exhaustive enumeration support minimization and
maximization. Their values, bounds and incumbent histories use `Fraction` and
report `arithmetic="rational_product"`. JSON result projection renders fractions
as numerator/denominator strings. Integer objective results are unchanged.
The parsed MODEL objective syntax remains integer-based; rational-product
objectives currently require the Python API. Additive factor contribution
explanations are not generated for products; the Blues benchmark records each
local probability separately.

Local bounds multiply factor extrema. For unary and adjacent-pair factors under
an explicit preparation budget, auto bounding compiles a max-product chain
relaxation and optionally includes one equality COUNT with target 0 through 4.
All other hard constraints are relaxed, while current variable domains are
respected. Its upper bound is exact for that relaxation, including the selected
count; its lower bound is conservatively zero. A zero upper bound never implies
hard infeasibility. Wider factors fall back to independent bounds. Compilation
and message-passing timeouts return UNKNOWN or an existing incumbent and restore
caller state. Messages are recomputed, not yet maintained incrementally.

See the [Blues corpus audit](../benchmarks/data/omnibook_blues_v1/README.md) and
[Markov implementation progress](markov_constraints_progress.md) for the initial
application and the remaining variable-order work.

### Permutation-chain product bounds and warm starts

For a rational-product objective with only unary/adjacent-pair factors, automatic
bounding now recognizes a hard all-different constraint covering every variable,
an alphabet with exactly as many values as variables (at most 64), and fixed
distinct first and last values. Larger instances retain the existing fallback. It uses a successor/predecessor assignment relaxation. Each edge
receives its greatest compatible positional weight; disconnected cycles and other
hard constraints are relaxed. The initial factor and constants are included once.
Thus every feasible path induces a matching with at least its objective value.
A multiplicative Hungarian algorithm computes the maximum matching product using
rational arithmetic only. Zero denotes absence of a positive-weight matching, not
hard infeasibility. The conservative lower bound remains zero for minimization.

`bounding="chain"` disables this recognition and selects the prior chain relaxation
(subject to the same size/scope fallback). `bounding="local"` still selects local
bounds. Objective value ordering now also omits candidates whose completion bound
cannot strictly improve the incumbent; optimization returns one optimum.

`solve(..., initial_assignment={variable: value, ...})` and `search` accept a complete
warm start for minimization/maximization. Every value must belong to the current
domains. The controller temporarily installs the assignment, propagates rules and
constraints, validates all complete constraints, and computes the objective itself.
Invalid seeds raise `ValueError` with branch state restored. A valid seed survives
later search limits; a timeout before its validation finishes cannot produce an
accepted seed. Seed validation shares the query's time budget. Its incumbent
history entry has node count zero; seed propagation is included in revision counts.

The assignment alone is supplied, never trusted objective values or derived facts.
Seed provenance is the caller's responsibility and must be reported in benchmarks.
These additions are Python API features; textual warm-start declarations are not
part of this change.
