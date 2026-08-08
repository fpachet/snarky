# Probabilistic Constraint Learning and Exact Generation

Status: research specification and architecture proposal.

Compatibility boundary: this proposal extends the frozen
[Snarky Core 0.1 baseline](core_0_1_baseline.md). It does not alter the meaning
of existing rules, constraints, programs, or `CHOICE` weights. All syntax and
runtime components introduced here remain experimental until their semantic
challenge suite and differential conformance gates pass.

This document specifies a language-level model for learning interpretable
symbolic structure from a small corpus and generating new objects from the
learned style under additional user constraints. It connects Snarky's rules,
persistent finite-domain constraints, learned factors, reversible search, and
the exact variable-order Markov / regular-constraint algorithms implemented by
the sibling `vo_regular_bp` library.

The central decision is that the language defines one conditional probability
distribution, while propagation, regular belief propagation, and weighted
backtracking are alternative inference algorithms for that distribution. The
algorithms must not introduce competing meanings for a weight or a choice.

## 1. Target use case

The primary use case has five stages:

1. A corpus is available, but it is too small to justify an unconstrained
   high-capacity model such as a Transformer.
2. A structure-induction procedure proposes readable derivation rules, hard
   constraint candidates, and factor templates.
3. An expert may add, remove, or certify rules and constraints.
4. Maximum-likelihood estimation fits the parameters of the frozen factors.
5. The resulting model generates new objects in the corpus style, optionally
   conditioned by new user constraints, and explains both feasibility and
   preference.

The Bach chorale experiment is the motivating application, but the semantics
must remain domain-independent. A sequence may contain musical slices, words,
plans, layouts, or any other finite structured symbols.

## 2. Design commitments

The proposal makes the following commitments.

1. Rules, constraints, factors, learning, and inference have distinct roles.
2. Hard constraints define zero probability, not a large negative weight.
3. Factor parameters affect scores but never factor activation or working
   memory.
4. User constraints condition an already learned model; they do not silently
   refit it.
5. Search priorities are not probabilities.
6. Exact sampling uses total completion mass, not local factor scores.
7. The exact chain backend and the exact weighted-search oracle define the
   same distribution where both apply.
8. An `EXACT` query must fail closed when no exact backend supports the whole
   model.
9. Every learned structure and parameter has corpus, split, and algorithm
   provenance.
10. Explanations distinguish logical feasibility, statistical preference,
    and inference decisions.

## 3. Terminology

Two unrelated notions of variable order must remain distinct:

- **CSP variable ordering** selects which finite-domain decision variable to
  branch on, for example chronological order, MRV, or dom/wdeg.
- **Variable-order Markov modeling** selects the effective suffix-context
  length used to predict the next sequence symbol.

The former changes search efficiency. The latter changes the probability
model. Neither should be abbreviated to an ambiguous `variable_order` in a
public artifact.

The term **backtracking** also has two uses:

- ordinary feasibility search stops after finding a solution;
- weighted backtracking sums the mass of every feasible completion and can
  therefore support exact probabilities and samples.

Only the second is a probabilistically exact fallback for `SAMPLE EXACT`.

## 4. Formal model semantics

### 4.1 Context and configurations

Let:

- `c` be immutable observed context;
- `X = (X_1, ..., X_n)` be explicit finite decision variables;
- `D_i(c)` be the initial finite domain of `X_i`;
- `x` be one complete assignment in the Cartesian product of these domains;
- `W_0(c, x)` be the ground context and assignment facts.

For chorale harmonization, `c` may contain the imposed soprano, tonality,
meter, phrase boundaries, and requested length. A complete `x` contains the
unknown voices and any explicit harmonic variables.

### 4.2 Deterministic rule closure

A scoreable rule program `R` computes a deterministic closure:

\[
W_R(c,x) = \operatorname{lfp}_R(W_0(c,x)).
\]

Rules derive observable properties such as chord degree, inversion, melodic
motion, cadence type, or a diagnostic relation. They do not contribute energy
and do not make probabilistic choices.

The first supported scoreable fragment must be terminating and
schedule-independent. A program whose terminal facts depend on conflict
resolution, destructive action order, or an uncontrolled `REMOVE` is rejected
unless it declares a separately specified terminal-state semantics.

### 4.3 Hard constraints

Each hard constraint `C_j` denotes a Boolean predicate over a complete closed
configuration:

\[
C_j(W_R(c,x)) \in \{0,1\}.
\]

The feasible set is:

\[
\Omega_C(c) = \{x \mid \prod_j C_j(W_R(c,x)) = 1\}.
\]

Propagation is not part of this denotation. It is an implementation that
soundly removes unsupported partial values. A propagator may be incomplete,
but it must never remove a value occurring in a feasible completion. Complete
assignments are checked against the declarative constraint predicate.

Regular, positional, arithmetic, table, and `ALL_DIFFERENT` constraints share
this Boolean semantics. They differ only in compilation and propagation.

### 4.4 Pure factors

A factor definition provides a finite real feature value for a ground scope:

\[
F_{k,s}(W_R(c,x)) \in \mathbb{R}.
\]

The first implementation may retain Boolean activations, but the semantic
model explicitly admits Boolean, count-valued, and real-valued features. The
kind must be declared; witness multiplicity must never turn a Boolean feature
into a count accidentally.

Factor parameters are finite real values `theta_k`. The log-energy is:

\[
S_\theta(x,c) = \sum_k \sum_s \theta_k F_{k,s}(W_R(c,x)).
\]

Factor evaluation observes an immutable closed snapshot. It cannot add or
remove facts, trigger rules, restrict domains, or choose alternatives.

### 4.5 Optional base measure

The model may declare an explicit non-negative base measure `mu_phi(x | c)`.
If omitted, it is uniform over the finite configuration space.

A variable-order Markov source is one possible base measure. It is not an
implicit second factor system: the model declaration must say whether its
parameters `phi` are fixed, fitted separately, or optimized jointly with
`theta`.

Using a Markov model fitted on the same corpus as a fixed base measure and then
fitting residual log-linear factors is valid, but it defines a combined model.
The artifact must record this choice to avoid accidental double counting.

### 4.6 Conditional distribution

The language denotes exactly one conditional distribution:

\[
P_{\theta,\phi}(x \mid c) =
\frac{
  \mathbf{1}[x \in \Omega_C(c)]
  \mu_\phi(x \mid c)
  \exp(S_\theta(x,c))
}{Z_{\theta,\phi}(c)},
\]

where:

\[
Z_{\theta,\phi}(c) =
\sum_{x' \in \Omega_C(c)}
\mu_\phi(x' \mid c)\exp(S_\theta(x',c)).
\]

This equation is the normative semantics for learning, scoring, MAP,
marginals, and exact sampling.

## 5. Knowledge status and induction

The language must not confuse a regularity observed in a finite corpus with a
certified universal prohibition. Every induced object has an explicit status.

| Object | Runtime meaning | Typical origin |
|---|---|---|
| derived rule | deterministic fact derivation | expert or induced definition |
| factor template | measurable preference feature | factor grammar and selection |
| candidate constraint | reported empirical near-invariant | structure induction |
| certified constraint | zero-probability support restriction | expert or promotion policy |
| user constraint | query-local support restriction | generation request |

A proposed induction pipeline is:

```text
typed corpus
    -> normalized contexts and configurations
    -> factor/rule grammar
    -> candidate generation
    -> train-only support and counterfactual evaluation
    -> complexity-aware structure selection
    -> frozen readable structure
    -> parameter estimation
    -> validation and optional constraint certification
    -> immutable trained artifact
```

Structure induction and parameter fitting are separate operations. A parameter
refit cannot add clauses. A structure-selection run cannot claim to be a mere
weight refit.

Candidate constraints should normally begin as factors. Promotion to a hard
constraint requires an explicit policy, such as expert certification or a
pre-registered statistical criterion stable across held-out pieces. The
promotion decision and its evidence belong in the artifact.

## 6. Maximum-likelihood learning

### 6.1 Conditional MLE

For observed examples `(c_i, x_i*)`, conditional log-likelihood is:

\[
\mathcal{L}(\theta) = \sum_i
\left[
  \log \mu_\phi(x_i^* \mid c_i)
  + S_\theta(x_i^*,c_i)
  - \log Z_{\theta,\phi}(c_i)
\right].
\]

For fixed `phi`, the factor gradient is:

\[
\nabla_{\theta_k}\mathcal{L} = \sum_i
\left[
  F_k(x_i^*,c_i)
  - \mathbb{E}_{P_{\theta,\phi}(X\mid c_i)}F_k(X,c_i)
\right].
\]

The inference backend used during fitting must therefore provide the partition
function and factor expectations, not merely a locally normalized choice.

### 6.2 Objectives must be named precisely

The initial language should distinguish:

- `GLOBAL_CONDITIONAL_MLE`: uses the globally normalized distribution above;
- `PSEUDOLIKELIHOOD`: sums full conditionals for individual variables;
- `LOCAL_CONDITIONAL_MLE`: normalizes over an explicitly declared finite
  alternative set;
- `EM`: supports declared latent variables;
- `APPROXIMATE_MLE`: names the expectation approximation explicitly.

Pseudo-likelihood is useful and may be statistically appropriate, but it must
not be reported as exact joint maximum likelihood.

### 6.3 Exact expectation engines

Two exact engines are required:

1. a small generic weighted-enumeration/backtracking oracle;
2. a regular-chain forward/backward engine.

Both should return a common result containing at least:

- `log_partition`;
- exact or approximate status;
- factor expectations;
- variable or scope marginals;
- diagnostics and an inference certificate.

Finite-difference gradients on tiny models are the independent learning oracle.

### 6.4 Trained artifact

A trained artifact binds parameters to a frozen model and records:

- model and language versions;
- rule, constraint, and factor identifiers;
- parameter names and values;
- corpus and split digests;
- preprocessing and transposition policy;
- structure-selection method;
- objective and normalization scope;
- inference backend and exactness status;
- optimizer, regularization, stopping criterion, and seed;
- train and validation diagnostics;
- all promoted constraints and their justification.

Loading fails if the parsed model structure no longer matches the artifact.

## 7. User constraints as conditioning

Let `U` be constraints added to one generation request. They define:

\[
P_{\theta,\phi}(x \mid c,U) =
\frac{
P_{\theta,\phi}(x \mid c)\mathbf{1}[U(x)]
}{P_{\theta,\phi}(U\mid c)}.
\]

The learned parameters do not change. The new constraints restrict and
renormalize the learned distribution.

Examples include:

- a symbol or chord at a specified position;
- an imposed prefix or suffix;
- a final cadence;
- a forbidden substring;
- a meter or duration total;
- `ALL_DIFFERENT` over selected variables;
- a maximum count or other finite global constraint.

An infeasible query returns `UNSAT`, not a low-quality unconstrained sample.
Where available, the result includes a minimal or reduced conflicting set of
user and model constraints.

## 8. Inference semantics

### 8.1 Query kinds

The model is independent of the requested calculation. Initial query kinds
should be:

- `CHECK`: test a complete configuration;
- `SOLVE`: return any feasible configuration;
- `ENUMERATE`: enumerate feasible configurations under a declared limit;
- `MAP`: maximize total log-weight;
- `PARTITION`: compute `Z`;
- `MARGINAL`: compute declared marginals;
- `EXPECTATION`: compute declared factor expectations;
- `SAMPLE_EXACT`: draw from the normalized constrained distribution;
- `SAMPLE_APPROXIMATE`: use a named approximate algorithm.

`SOLVE` may use ordinary backtracking and ignore factor weights. `SAMPLE_EXACT`
cannot.

### 8.2 Propagation and rollback

At each generic search node:

1. add the branch assumption;
2. alternate persistent constraint propagation and deterministic rule closure
   to a joint fixed point;
3. reject a contradiction;
4. select the next branch variable if unresolved;
5. checkpoint before each alternative;
6. rollback facts, domains, provenance, and propagator state together.

Propagation affects efficiency but not the probability definition.

### 8.3 Exact weighted backtracking

For a residual branch state `b`, define its completion mass:

\[
Z(b) = \sum_{x \supseteq b,\ x\in\Omega_C(c)}
\mu_\phi(x\mid c)\exp(S_\theta(x,c)).
\]

The reference recurrence is:

```text
mass(branch):
    close rules and propagate constraints
    if contradiction: return 0
    if complete: return base_measure * exp(factor_score)
    choose one unresolved variable d
    return sum(mass(branch + d=value) for value in domain(d))
```

Exact sampling first obtains the child masses, selects a child proportionally
to them, and recurses. Sampling by a local `CHOICE WEIGHT` followed by retry or
backtracking is not equivalent and is forbidden for an `EXACT` query.

Memoization turns repeated residual states into an AND/OR weighted model
counter. This engine is exponential in the worst case but provides a universal
finite oracle and a fallback for small general models.

### 8.4 Regular variable-order BP

The sibling `vo_regular_bp` library implements a specialized exact recurrence
on the reachable product of a variable-order context graph and a deterministic
acceptor.

For time `t`, Markov context `h`, acceptor state `q`, and emitted symbol `a`:

\[
\beta_t(h,q) = \sum_a
p_\phi(a\mid h)\,
\psi_\theta(t,h,q,a)\,
\beta_{t+1}(h',q').
\]

Here:

- a rejected hard transition has `psi = 0`;
- a feasible hard transition contributes a Boolean factor of `1`;
- soft finite-state factors contribute `exp(theta * feature_value)`;
- `beta` is the exact total downstream mass.

The exact sequential sampling conditional is:

\[
P(a_t=a\mid a_{<t},c,U)=
\frac{
p_\phi(a\mid h)\psi_\theta(t,h,q,a)\beta_{t+1}(h',q')
}{\beta_t(h,q)}.
\]

This is the precise meaning of backward propagation from a final cadence. A
candidate with no accepting continuation has zero mass. A candidate with only
unlikely continuations remains feasible but receives lower posterior mass.

No search backtrack is needed during sampling when the complete model has been
compiled into this product: the backward pass has already summed all future
branches.

### 8.5 Factors and regular compilation

A hard bounded-window constraint can be compiled into a DFA by retaining the
necessary suffix in its state. A K3 rule needs at most the relevant two-symbol
history before reading the third symbol.

A bounded-window factor can similarly be compiled into a weighted transition
potential. In the unified language, this remains a `FACTOR`, not a "soft
constraint", even if `vo_regular_bp` represents it internally through a
weighted acceptor transition.

Several acceptors are intersected in a product. State growth must be reported,
and compilation may be refused when a declared bound is exceeded.

### 8.6 Positional constraints

Position-specific domains should remain masks when possible rather than
inflating automaton state. A final `V-I` cadence, for example, can often be
represented as two final masks plus any transition-specific cadence checks.

### 8.7 `ALL_DIFFERENT` and other global constraints

Over a finite horizon and finite alphabet, `ALL_DIFFERENT` is technically a
regular property: a DFA may remember the set of values already used. This may
require exponentially many states, so a dedicated global propagator is often
the correct operational implementation.

If a global constraint remains outside the regular product, the BP marginals
alone are not the exact conditionals of the whole model. Exact execution must
then either:

1. compile the constraint into the dynamic-programming state;
2. use a more general exact decomposition;
3. fall back to exact weighted backtracking/model counting; or
4. reject `EXACT` and require an explicitly approximate query.

### 8.8 Safe hybridization

BP may be used as a sound zero-mass propagator or as a search heuristic inside
generic backtracking. This does not by itself make the final sampler exact.

An exact hybrid must compute branch masses with respect to every remaining
constraint. It may call a cached BP backend for a compiled residual chain, but
the outer weighted search must still sum branches whose non-chain constraints
are unresolved.

The compiler must never label a heuristic composition as exact.

## 9. The role of `CHOICE`

Current Snarky `CHOICE` declarations expose reversible alternatives to
`SessionChoiceSearch`. Their weights order or locally sample alternatives; they
do not define a globally normalized probability model.

The probabilistic model must therefore not interpret `CHOICE WEIGHT` as a
factor parameter or an exact marginal.

The Core 0.1 compatibility decision is to retain `CHOICE WEIGHT` unchanged.
The probabilistic layer may introduce an additive experimental
`BRANCH ... PRIORITY ...` form if an explicit search-priority declaration is
needed, while probabilistic sampling remains an inference query.

For `SAMPLE_EXACT`, the inference backend may internally expose a branch point,
but its alternative weights are computed completion masses or BP-corrected
conditionals. They are results of inference, not declarations in the model.

## 10. Proposed language organization

One language family should expose separate top-level blocks for model,
learning, and inference.

### 10.1 Model declaration

```text
MODEL bach_chorale
    CONTEXT
        INPUT soprano
        INPUT tonality
        INPUT meter
    END_CONTEXT

    SEQUENCE harmony LENGTH $length
        VARIABLE $slice[$time]
        DOMAIN satb_slice_candidates($soprano $time)
    END_SEQUENCE

    PROJECT chord_state
        FROM $slice
        VALUE SEQ[
            degree($slice)
            quality($slice)
            inversion($slice)
        ]
    END_PROJECT

    RULE_PROGRAM musical_analysis
        USE chorale_observables
    END_RULE_PROGRAM

    CONSTRAINT_GROUP certified_harmony
        USE voice_ranges
        USE no_crossing
        USE no_parallel_perfect_intervals
    END_CONSTRAINT_GROUP

    BASE_MEASURE bach_vomm
        VARIABLE_ORDER_MARKOV OVER chord_state
        PARAMETERS bach_vomm_parameters
    END_BASE_MEASURE

    FACTOR_GROUP bach_style
        PARAMETER degree_transition INITIAL 0.0
        PARAMETER bass_step INITIAL 0.0

        FACTOR preferred_degree_transition
            SCOPE SEQ[$left $right]
            VALUE 1
            PARAMETER degree_transition
            WHEN
                ADJACENT $left $right IN harmony
                ($left degree V)
                ($right degree I)
        END_FACTOR

        FACTOR conjunct_bass_motion
            SCOPE SEQ[$left $right bass]
            VALUE 1
            PARAMETER bass_step
            WHEN
                ADJACENT $left $right IN harmony
                ($left bass_pitch $p1)
                ($right bass_pitch $p2)
                ABS($p2 - $p1) <= 2
        END_FACTOR
    END_FACTOR_GROUP
END_MODEL
```

This syntax is illustrative. Parser and AST decisions require a dedicated
language proposal. The semantic distinctions are normative.

### 10.2 Learning declaration

```text
LEARNING_PROGRAM learn_bach_chorale
    MODEL bach_chorale
    DATASET bach_corpus
    SPLIT BY piece TRAIN 0.8 VALIDATION 0.1 TEST 0.1

    INDUCE_STRUCTURE
        GRAMMAR bach_readable_factor_grammar
        MAX_WINDOW 3
        MAX_CLAUSES 3
        COMPLEXITY_PENALTY 0.1
        PROMOTE_CONSTRAINTS NEVER
    END_INDUCE_STRUCTURE

    FIT_PARAMETERS
        OBJECTIVE GLOBAL_CONDITIONAL_MLE
        REGULARIZATION L2 0.01
        INFERENCE AUTO_EXACT
        OPTIMIZER LBFGS
    END_FIT_PARAMETERS
END_LEARNING_PROGRAM
```

The corpus is resolved through a typed dataset adapter. Corpus paths and music
parsing callbacks do not belong in rule or factor semantics.

### 10.3 Generation declaration

```text
INFERENCE_PROGRAM harmonize_soprano
    MODEL bach_chorale
    PARAMETERS learned_bach_chorale

    OBSERVE soprano FROM input_piece
    OBSERVE tonality FROM input_piece

    ADD_CONSTRAINT final_cadence
        POSITIONAL chord_state AT -2 MATCHES SEQ[V major_or_minor root]
        POSITIONAL chord_state AT -1 MATCHES SEQ[I major_or_minor root]
    END_CONSTRAINT

    ADD_CONSTRAINT user_bass_variety
        ALL_DIFFERENT SEQ[$bass_1 $bass_2 $bass_3]
    END_CONSTRAINT

    QUERY SAMPLE_EXACT COUNT 1
    INFERENCE AUTO_EXACT
END_INFERENCE_PROGRAM
```

The compiler may select regular BP, a global propagator plus weighted search,
or another exact backend. The query result records the selection.

## 11. Compiler and runtime architecture

The language should compile through explicit intermediate representations.

```text
parsed model
    -> deterministic rule IR
    -> finite variables and domain IR
    -> hard constraint IR
    -> pure factor IR
    -> dependency and sequence analysis
    -> backend-specific exact plan
```

### 11.1 Deterministic preparation

Context-only rules and candidate constructors run before probabilistic
inference. They build finite domains, static relations, projections, and
provenance.

Assignment-dependent derivations must either be:

- evaluated reversibly by generic search; or
- compiled into local tables/automata for a sequence backend.

### 11.2 Backend capability analysis

The compiler classifies each constraint and factor by:

- scope variables;
- temporal span;
- finite-state memory requirement;
- positional dependence;
- whether it is hard or weighted;
- whether it can be evaluated incrementally;
- whether it supports exact expectations and explanations.

The backend selection result is part of the output, not an invisible
optimization.

### 11.3 Exactness contract

An inference certificate should state one of:

- `EXACT_ENUMERATION`;
- `EXACT_WEIGHTED_BACKTRACK`;
- `EXACT_REGULAR_BP`;
- `EXACT_DECOMPOSITION`;
- `APPROXIMATE_PSEUDOLIKELIHOOD`;
- `APPROXIMATE_MCMC`;
- another explicitly named method.

`AUTO_EXACT` may change algorithms but not denotation. If no exact plan is
available within declared resource limits, it returns `UNSUPPORTED_EXACT`, not
an approximate answer.

## 12. Integration with `vo_regular_bp`

The sibling library already provides:

- sparse variable-order context graphs;
- deterministic and weighted acceptors;
- positional masks and meter constraints;
- intersections of regular constraints;
- backward beta computation;
- partition mass and exact conditional sampling;
- reusable prefix-independent plans.

It should remain an independent generic library. Snarky should depend on its
public API through an adapter rather than copying the algorithm.

The unified specification requires several capabilities beyond its current
public result surface.

### 12.1 Forward messages and expectations

MLE needs factor expectations. The adapter or library must expose forward
messages and expected transition/feature counts, or support an expectation
semiring. Backward beta values and samples alone are insufficient for efficient
gradient computation.

### 12.2 Parameterized weighted factors

Weighted acceptors currently provide scalar transition weights. Learning
requires stable factor identifiers and transition feature vectors so that:

\[
\log \psi_\theta(e) = \theta^\top f(e)
\]

and expected feature counts can be attributed back to readable factors.

### 12.3 Time-indexed structured-slice lattices

The current library naturally emits symbols from a learned source alphabet.
A chorale position instead has a time-dependent set of SATB slice candidates
conditioned on the imposed soprano. Exact joint inference may therefore need a
sparse time-indexed weighted lattice whose edges carry:

- a concrete slice candidate;
- a projected Markov symbol such as chord state;
- local factor features;
- the next Markov and acceptor states.

Collapsing a whole SATB slice into a symbol is semantically valid but may not
fit the current fixed source-alphabet interface efficiently. The preferred
extension is a transition-provider abstraction, not a music-specific fork.

### 12.4 Projection and joint generation

Sampling a chord-state chain first and solving the voices afterward is not
joint exact sampling unless chord probabilities include the partition mass of
all compatible voice realizations. The adapter must therefore either:

- include complete slice candidates in the same dynamic program; or
- analytically sum the compatible realization mass for each harmonic edge.

This prevents the reintroduction of an imposed harmonic skeleton through an
implementation shortcut.

## 13. Bach chorale mapping

For note-by-note homorhythmic harmonization, define a time slice:

```text
slice[t] = (
    soprano[t],
    alto[t],
    tenor[t],
    bass[t],
    chord[t],
    degree[t],
    inversion[t]
)
```

The soprano component is observed. The remaining components are joint decision
variables or one reified finite slice candidate.

### 13.1 Derived rules

Rules derive, among other properties:

- chord pitch classes, root, quality, degree, and inversion;
- melodic intervals by voice;
- relative and contrary motion;
- repeated attacks;
- perfect intervals between voice pairs;
- leading-tone and seventh resolution status;
- cadence and phrase-position status.

### 13.2 Hard constraints

Initially certified constraints may cover:

- voice ranges, ordering, and spacing;
- chord membership and completeness;
- prohibited melodic intervals;
- parallel and direct perfect intervals;
- mandatory resolutions;
- a requested final cadence;
- user-imposed notes or harmonic conditions.

### 13.3 Learned factors

Readable factors may include:

- exact degree/quality/inversion transitions;
- K3 harmonic succession patterns;
- bass trajectories;
- inner-voice step and repetition profiles;
- doubling preferences;
- metric dependence;
- boundary and cadence preferences;
- controlled chromatic events.

Root-motion interval alone is insufficient because it discards tonal function.
The observable chord-state projection must retain tonic-relative degree and
quality whenever a factor claims to describe harmonic syntax.

### 13.4 No imposed harmonic skeleton

An explicit chord variable does not imply a predetermined progression. Chord
state and voices may be inferred jointly. A final cadence is a boundary
condition; it does not prescribe the intervening chord sequence.

Regular backward messages can propagate the ability to reach the cadence
through every preceding slice, while learned factors distribute probability
among the feasible paths.

## 14. Explanation contract

A generated result must separate four kinds of explanation.

### 14.1 Feasibility explanation

- final values and domains;
- all hard constraints checked;
- values removed by each propagator;
- branch contradictions and rollback causes;
- optional unsatisfiable core.

### 14.2 Statistical explanation

- active factor and scope identifiers;
- feature values;
- learned parameter values;
- signed log-score contributions;
- total score and, when available, normalized probability;
- relevant marginal or completion mass at each sampled decision.

### 14.3 Learning provenance

- corpus support and counterexamples;
- split membership policy;
- structure-selection decision;
- parameter-estimation objective;
- validation stability;
- learned, expert, or user origin.

### 14.4 Inference explanation

- selected backend;
- exactness certificate;
- product-state or search diagnostics;
- partition function or branch masses;
- random seed;
- resource bounds and any approximation declaration.

An explanation must never present a search priority as a model probability or
a propagated domain value as a statistically preferred value.

## 15. Reference prototype

The language design should be validated before returning to full chorales.

### 15.1 Toy domain

Use a short sequence over:

```text
{I, ii, IV, V, vi}
```

with:

- a small variable-order Markov base measure;
- a hard final `V-I` cadence;
- one forbidden substring;
- one positional constraint;
- two readable weighted factors;
- one optional `ALL_DIFFERENT` query constraint.

### 15.2 Independent computations

For every parameter vector in a small test grid, compare:

1. exhaustive enumeration;
2. exact weighted backtracking;
3. regular product BP when only regular constraints are enabled;
4. numerical finite-difference gradients;
5. empirical frequencies from exact samples.

Required equalities, within numerical tolerance, are:

- partition functions;
- complete-sequence probabilities;
- declared marginals;
- expected factor counts;
- analytic and finite-difference gradients;
- sample frequencies and exact probabilities within statistical confidence.

Adding `ALL_DIFFERENT` must either select an exact supported backend or produce
`UNSUPPORTED_EXACT`; it must never silently fall back to local weighted choice.

## 16. Implementation milestones

### Milestone 0: architecture decision record

- freeze the formal distribution;
- define exactness and artifact terminology;
- decide the scoreable rule fragment;
- state the relationship between `CHOICE` and probabilistic queries.

### Milestone 1: exact weighted-search oracle

- evaluate complete factor scores through existing pure factors;
- add recursive branch mass computation;
- memoize residual states;
- expose partition, marginals, expectations, and exact samples;
- validate rollback invariance.

### Milestone 2: regular-BP adapter

- compile positional and regular hard constraints;
- compile bounded-window factors as attributed weighted transitions;
- compare all outputs with the oracle;
- preserve factor and constraint provenance.

### Milestone 3: exact MLE

- add factor expectation results;
- implement stable log-likelihood and gradient evaluation;
- validate with finite differences;
- add L2 regularization and a deterministic optimizer;
- serialize the trained artifact.

### Milestone 4: language surface

- add `MODEL`, `LEARNING_PROGRAM`, and `INFERENCE_PROGRAM` ASTs;
- add static type and scope validation;
- add backend capability diagnostics;
- reject unsupported exact queries;
- format and round-trip every declaration.

### Milestone 5: structured slice lattice

- represent time-indexed SATB candidates;
- retain chord-state projections;
- compile vertical and adjacent voice-leading relations;
- run exact eight-position experiments;
- compare reified and decomposed representations.

### Milestone 6: Bach study

- freeze train/validation/test splits by piece;
- induce readable factor structures on train only;
- fit weights with the declared objective;
- add certified manual constraints;
- condition on soprano and final cadence;
- generate and explain held-out chorales;
- compare with authentic Bach, DeepBach, and manual-rule baselines.

## 17. Acceptance criteria

The first stable version requires:

1. one normative probability formula shared by every backend;
2. exact oracle agreement on all toy configurations;
3. exact BP agreement for regular subsets;
4. correct analytic MLE gradients;
5. reversible propagation and factor evaluation under backtracking;
6. user constraints that condition without refitting;
7. explicit refusal of unsupported exact inference;
8. deterministic, factor-level explanations;
9. complete training and inference provenance;
10. no application-specific Bach code in the semantic core.

## 18. Discussion

### Why one language makes sense

One language ensures that training and generation refer to the same rules,
support, features, and parameters. It also lets an expert add a constraint
without translating the model into a second solver and losing explanations.

### Why one runtime algorithm does not

Regular BP is exceptionally effective for sparse finite-state sequence
structure. Global propagators and backtracking are more appropriate for many
non-chain finite-domain constraints. Forcing every problem into one algorithm
would either sacrifice exactness, lose propagation strength, or cause severe
state explosion.

The unification belongs in denotation, compilation, result types, and
explanations. Backend plurality is intentional.

### Relation to probabilistic logic languages

PRISM and CHRiSM combine logic, probabilistic choices, and parameter learning;
ProbLog uses knowledge compilation and weighted model counting; Markov Logic
combines hard and weighted formulas; Dyna expresses weighted dynamic programs.
The proposed Snarky extension should acknowledge these precedents.

Its narrower contribution is the explicit combination of:

- deterministic rule closure;
- persistent finite-domain propagation and rollback;
- pure readable factor activations;
- exact MLE expectations;
- exact regular-constrained variable-order generation;
- exact weighted backtracking as a common oracle;
- user constraints and explanations under one model contract.

### Principal risk

The principal scientific risk is not parser complexity. It is tractability.
Readable rules may compile into large relations, regular products may explode,
and exact weighted backtracking is exponential in general. The language must
therefore make complexity and exactness visible rather than hiding them behind
an automatic mode.

The principal semantic risk is accidental duplication of probability: local
`CHOICE` weights, a Markov source, and learned factors must not each claim to be
the model. Only the normalized distribution in Section 4.6 has probabilistic
meaning.

## 19. Open decisions

1. Which rule actions are admitted in scoreable deterministic closure?
2. Are count-valued factors part of the first language release?
3. Is a variable-order Markov source a core declaration or a generic imported
   base-measure provider?
4. Should the exact weighted-search oracle use ordinary recursion, an
   expectation semiring, or an explicit algebra interface?
5. Which residual-state key is safe for weighted-search memoization?
6. Should `CHOICE WEIGHT` be deprecated, renamed, or retained as an explicitly
   non-probabilistic search hint?
7. What automaton/product-state size triggers compilation refusal?
8. How are learned constraint candidates promoted and later revoked?
9. How are factor structures shared across transpositions and modes without
   erasing tonal function?
10. Should the structured-slice backend live in `vo_regular_bp` or in a generic
    sparse-lattice companion package?

## 20. Related project documents

- [`semantics.md`](semantics.md) defines the current executable Snarky core.
- [`learned_factor_language_plan.md`](learned_factor_language_plan.md) defines
  the existing pure-factor and learning plan.
- [`persistent_constraints.md`](persistent_constraints.md) specifies
  rollback-aware finite-domain constraints.
- [`choice_search.md`](choice_search.md) and
  [`choice_backtracking_and_applications.md`](choice_backtracking_and_applications.md)
  document explicit search.
- [`global_constraints.md`](global_constraints.md) documents the existing
  global-constraint layer.
- [`../harmonizer/bach_rule_induction/PLAN.md`](../harmonizer/bach_rule_induction/PLAN.md)
  records the Bach induction research program.
- The sibling `vo_regular_bp` repository provides the current exact
  variable-order Markov / regular-product implementation.
