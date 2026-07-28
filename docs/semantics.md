# Reference semantics

This document defines Snarky's executable semantic core. Where historical
sources do not establish BOOJUM behavior precisely, the design is a documented
modern extension rather than a claim of historical equivalence.

## Terms and facts

A term is an immutable `Atom`, `Number`, `Variable`, `Status`,
`FiniteSequence`, `FiniteSet`, `Triple`, or `Proposition`. Compound terms are
recursive. All terms are structurally comparable and hashable.

`FiniteSequence` is ordered and retains duplicates. `FiniteSet` removes
duplicates and compares independently of insertion order, while retaining its
first insertion order for deterministic rendering.

A stored `Fact` contains a ground entity and a ground status. Working memory
is multi-status: facts with the same entity and different statuses may
coexist. `VRAI`, `FAUX`, and `INEXISTANT` are explicit values. Absence from
working memory is not equivalent to any status.

## Substitution, matching, and unification

A `Substitution` maps variables to terms and applies recursively through
compound structures and variable chains.

Forward chaining uses one-way pattern matching from a rule premise to a ground
fact. An unbound variable accepts the corresponding term; an existing binding
requires structural equality. Matching includes all triple positions and the
fact status.

Bidirectional `Unifier` is separate. It composes substitutions and performs an
occurs check, but the forward engine does not use it for ordinary rule
instantiation.

## Premises

A fact premise without an explicit status matches `VRAI`. The textual
`entity ' status` form matches both components and may bind a status variable.

Premises are evaluated in textual order. Comparisons require ground operands
at the point where they occur. They do not search later premises for missing
bindings.

Correlated blocks see outer bindings but keep their own variables local:

- `EXISTS` requires at least one local solution;
- `NOT EXISTS` requires none;
- `COUNT` compares the number of local substitutions;
- `UNIQUE` requires exactly one;
- `COLLECT` projects distinct ground values into a `FiniteSet`.

Only the target of `COLLECT` escapes its block. Accepted local supports are
retained for provenance. `BIND` binds an already-ground structured term;
window and combination premises may produce multiple activations.

Computed premises call only explicitly registered pure `ComputedPredicate`
objects. Snarky never evaluates arbitrary source text.

## Learned factors

A `FactorDefinition` is a Boolean premise conjunction and a scope template.
A `FactorParameter` stores its learned finite log weight separately. Pairing
them creates a `WeightedFactor`; a `FactorGroup` is not a `RuleGroup`.

Factor evaluation takes an immutable fact snapshot and returns ground
`FactorActivation` values. It never fires actions and never adds activations
to working memory. Multiple witnesses resolving to the same
`(factor, scope)` are one grounding and contribute once:

```text
log_score = sum(log_weight of each active grounding)
```

Changing a parameter changes this score but not the activation vector.
Changing the learned factor structure changes the vector and is therefore a
separate, explicitly versioned learning operation.

Hard constraints remain propagators defining feasibility. Learned factors
define preferences among configurations; neither mechanism silently changes
the semantics of the other. Turning factor scores into conditionals and
sampling them is an inference-layer operation, not a factor side effect.

## Actions

Supported actions are `ADD`, `REMOVE`, `LET`, `FRESH`, `FOR EACH`, and
`CHOICE`.

An activation stages its action inputs before changing working memory, then
applies actions in textual order:

- `LET` evaluates deterministic numeric arithmetic and extends the activation
  substitution without asserting a fact;
- `FRESH` binds a collision-free, session-local atom deterministically;
- `ADD` inserts a ground fact if it is absent;
- `REMOVE` removes a ground fact if present and is otherwise a no-op;
- `FOR EACH` applies a nested action block to each finite value;
- `CHOICE` describes branch alternatives for explicit search.

Later actions observe bindings produced by earlier `LET`, `FRESH`, and choice
steps. Arithmetic uses `+`, `-`, `*`, `/`, and `%` with normal precedence.
Invalid operands and division by zero are explicit runtime errors.

A declarative choice:

```text
CHOICE ($object value $value) WEIGHT $weight
FROM
    ($object candidate $value)
    ($object choice_weight SEQ[$value $weight])
END_CHOICE
```

turns each `FROM` solution into one possible fact assertion. Choice weights
order or sample feasible alternatives; they never change feasibility.
`RuleChoiceProvider` keeps choice-producing rules out of ordinary forward
execution.

## Instantiation

The naive strategy is the executable reference: it joins fact premises by
backtracking in source order, evaluates non-factual premises when reached, and
returns complete substitutions with their supporting facts.

Optimized strategies must produce the same observable activations:

- indexed instantiation maintains exact fact buckets and compiled patterns;
- semi-naive instantiation evaluates only joins containing a newly added fact;
- safe factorized event instantiation anchors a positive conjunction on an
  added fact and retrieves its remaining supports through exact indexes;
- constraint instantiation narrows finite domains and compact premise tables
  before exact matching;
- adaptive instantiation selects constraint filtering only when its estimated
  setup cost is likely to be recovered.

The default `ForwardEngine` strategy is semi-naive. The naive implementation
remains available for diagnostics and differential testing.

`FactDelta` reports revisioned net additions and removals. Persistent indexes,
existential witnesses, aggregate counts, and domain tables update from this
delta. Removing a support invalidates the corresponding memories; adding
facts causes any potentially broadened constraint component to be safely
reconsidered.

Factorized event instantiation does not change source-order comparison
semantics. It is available only when every comparison operand was already
bound by preceding textual fact premises and at least one later fact premise
exists. Rules containing `FOCUS`, queries, aggregates, binding or combination
premises are excluded. Addition deltas use the specialized plan; removals and
mixed deltas fall back to complete or memory-backed evaluation.

Constraint filtering is monotone during one evaluation and cannot remove a
valid activation. Exact ground matching remains the final oracle.
Specializations include equality, inequality, numeric order, divisibility,
binary arithmetic, `NVALUE`, and `ALL_DIFFERENT`. Unsupported or complex
premise shapes fall back to semi-naive matching.

This premise-local filtering is distinct from the persistent finite-domain
constraints used by `FiniteCSP`. A `SessionChoiceSearch` may receive
deterministic session propagators. At every search node it alternates those
propagators with its forward-rule groups until the complete fact state is
stable. Goal and contradiction tests, rule-based choice production, and MRV
therefore all observe the filtered state.

The first persistent CSP layer is narrowing-only:

- initial `candidate` facts define fixed base domains;
- `AllDifferentConstraint`, `SumConstraint`, `LinearSumConstraint`,
  `BinaryComparisonConstraint`, `ElementConstraint`, `CountConstraint`,
  `GlobalCardinalityConstraint`, `TableConstraint`, and
  `LexLessEqualConstraint` retract candidates without branching;
- ordinary rules can observe those retractions and derive other facts;
- `CHOICE` adds a branch decision, after which propagation restarts;
- rollback restores the decision, constraint reductions, and rule
  consequences together.

Rules that add candidate values require a different widening and
recomputation semantics and are not part of this layer.

Persistent constraint templates are grounded once from root facts. Domain
removals schedule incident constraints through a compiled adjacency graph.
The joint fixed-point scheduler compiles relation watches from factual rule
premises and revisits only components affected by net fact changes. Unknown or
dynamic dependencies use a wildcard, preserving conservative behavior. The
finite-domain projection consumes rollback-aware event cursors and reverses
its delta trail to the restored journal origin before applying sibling events.
See [persistent finite-domain constraints](persistent_constraints.md) for the
syntax and propagator contracts.

For persistent-constraint models, the default point selection is dom/wdeg:
domain size is divided by the accumulated weights of incident active
constraints, and a constraint's weight increases when it explains a failed
branch. Value order uses impacts learned from real propagated branches;
there is no speculative propagation. These policies change search order, not
logical feasibility.

## Fixed points and refraction

Within a persistent session, an activation identity consists of its group,
rule, and premise substitution. Local action bindings do not alter that
identity.

Refraction prevents a continuously valid activation from firing twice. It
expires when a positive support is removed or a correlated negative premise
becomes invalid. The engine continues applying newly eligible activations
until one cycle adds and removes no facts. Explicit cycle and fact limits
protect execution.

Deterministic ordering is observable. Optimized joins may choose selective
internal buckets, but supporting facts and activations are restored to the
same order as the reference strategy.

## Sessions, groups, and checkpoints

A `RuleGroup` is a named set of uniquely named rules. An `InferenceSession`
retains working memory, indexes, refraction, time tags, events, and provenance
across group calls.

Group execution modes are:

- `SATURATE`: run to a fixed point;
- `ONE_CYCLE`: perform one ordered rule pass;
- `FIRST_CHANGE`: stop after the first complete activation that mutates facts;
- `UNTIL`: stop on a declared condition or fixed point.

No mode interrupts an activation between actions. A rule later in a group can
see facts added earlier in the same cycle. Reusing a group name requires the
same definition.

`checkpoint()`, `rollback()`, and `release()` operate in LIFO order.
Rollback restores facts and their order, provenance, refraction, events, time
tags, indexes, and fresh-symbol state. `fork()` creates an isolated session
with equivalent logical state.

`ForwardEngine(rules).run(facts)` is the convenience form that creates a fresh
session and saturates an implicit `default` group.

## Explicit search

Forward chaining never introduces implicit problem-level backtracking.
`SessionChoiceSearch` is a separate controller:

1. obtain a `ChoicePoint`;
2. select an alternative through an explicit policy;
3. assert it in an isolated or checkpointed branch;
4. saturate configured rule groups;
5. reject contradictions, accept goals, or continue with another choice.

Depth-first search reuses a reversible session after one root fork. Breadth-
first and best-first search keep lazy branch descriptors and fork only when a
frontier item is expanded. MRV, weights, random seed, traversal, and limits
are explicit inputs.

`HypothesisSearch` similarly explores explicit asserted hypotheses.
Independent finite and SAT constraint solvers can return assignments as facts,
but do not mutate an inference session implicitly.

### Sequential rule-program steps

A `RuleProgram` may partition choice production into ordered `RuleStep`
objects. Each step contains ordinary rule groups and may contain named
session propagators. `SessionChoiceSearch` gives a staged program this
operational semantics:

1. saturate the common groups and the current step's groups/constraints;
2. reject a contradiction or accept a goal in that stable state;
3. expose only the current step's `CHOICE` actions;
4. branch normally when a choice exists;
5. otherwise advance to the next step without discarding earlier choice
   frames;
6. treat “no choice and no goal” as a dead end only in the final step.

The step index is branch-local and part of duplicate-state detection.
Rollback restores the session state and returns through step boundaries in
the same way that it returns through any other later inference. Steps
therefore guide the order in which an object is constructed; they do not
weaken constraints, make deterministic propagation branch, or commit a
partial solution.

## Conflict resolution

Without a conflict strategy, rules and activations execute deterministically
in source order.

With `MEAConflictStrategy`, the engine maintains a conflict set and fires one
selected activation. Selection considers the time tag of a `FOCUS` support,
then lexicographic recency, specificity, and source order. This remains
forward chaining; it does not create hypotheses or search branches.

## Provenance and truth maintenance

Initial facts have proof depth zero. A derivation records its group, rule,
substitution, premise facts, cycle, and proof depth. Multiple derivations may
support one fact, and `proof_depth` returns the shortest known proof.

Every effective addition or removal also produces a chronological
`InferenceEvent`. Events remain available after later removals so a
transformation can be replayed.

Optional truth maintenance retracts facts no longer reachable from retained
initial or hypothetical supports, including unsupported cycles. It does not
maintain alternative environments or nogoods and is therefore not a complete
ATMS.

## Compatibility

The Python surface, textual language, and future serialization formats follow
[versioning.md](versioning.md). Public stability categories are in
[api_stability.md](api_stability.md). Focused guides provide syntax and
examples for rule groups, mutations, search, arithmetic, global constraints,
and reversible propagation.
