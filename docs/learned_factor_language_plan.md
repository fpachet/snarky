# Learned-factor language plan

Status: future work. This document is the canonical plan for turning Snarky's
experimental learned factors into a language-level facility. It separates
decisions that still require formalization from behavior already implemented
by the factor evaluator.

The Bach induction project is the most advanced case study, but it must not
define the core semantics. Small, exactly enumerable examples will establish
the language and learning contract before the Bach code is migrated onto it.

## Objective

Snarky should expose four distinct semantic layers:

| Layer | Responsibility | Changes working memory? | Learned? |
|---|---|---:|---:|
| `RULE` | derive facts and transform symbolic state to a fixed point | yes | not intrinsically |
| `CONSTRAINT` | define and propagate hard feasibility | domains only | no |
| `FACTOR` | observe a closed state and contribute finite log-energy | no | parameters and, optionally, structure |
| `CHOICE` | define and explore reversible alternatives | temporarily | no |

Learning is an orchestration layer over factors, examples, and inference. It
must not become an action executed by a factor, and it must not silently
change rule or constraint semantics.

The intended contribution is therefore not merely "rules plus weights." It is
the explicit composition of:

1. deterministic symbolic closure;
2. hard support defined by constraints;
3. pure, scoped feature observations with separately learned parameters;
4. reversible choice defining the configuration space;
5. one energy model used by both local conditionals and global sampling.

This separation should remain visible in the Python API, textual language,
serialized artifacts, explanations, tests, and publications.

## Scope and non-goals

The first supported learning path should be deliberately narrow:

- finite choices and finite training corpora;
- Boolean factor activations with explicit scopes;
- exact conditional likelihood when alternatives can be enumerated;
- an exact joint oracle for toy problems;
- approximate Gibbs expectations for larger global configurations;
- separate, versioned structure selection and parameter fitting.

The first milestone does not require neural predicates, automatic
differentiation through arbitrary Python, continuous latent variables, a
general probabilistic programming language, or a large catalogue of
optimizers. These can be considered only after the finite semantics is stable.

## Proposed formal semantics

The notation in this section is a specification target, not yet a claim about
all current execution paths.

### Configurations and closure

Let:

- \(c\) be an immutable context;
- \(x\) be a complete assignment to the explicit choices;
- \(W_0(c,x)\) be the initial fact snapshot containing the context and choice
  assumptions;
- \(R\) be the rule program;
- \(C\) be the persistent hard constraints.

For a feasible assignment, rule execution and constraint propagation produce
a deterministic joint closure:

\[
W^*(c,x) = \operatorname{lfp}_{R,C}(W_0(c,x)).
\]

The feasible configuration set is:

\[
\Omega_C(c) =
\{x \mid \operatorname{lfp}_{R,C}(W_0(c,x))\text{ is consistent}\}.
\]

The fixed point must not depend on rule scheduling. If a program uses
non-monotonic removal or conflict-resolution behavior for which this cannot
be guaranteed, factor scoring must either receive an explicitly selected
terminal state or reject the program. This boundary needs a design decision
before the semantics is declared stable.

### Factor activation and scope

A factor definition \(r\) contains a premise conjunction \(P_r\) and a scope
template \(S_r\). For a ground scope \(s\):

\[
F_{r,s}(x,c) =
\mathbb{1}\left[
\exists \sigma:
P_r\sigma \subseteq W^*(c,x)
\land S_r\sigma = s
\right].
\]

This definition captures the implemented witness-deduplication rule:
multiple substitutions proving the same `(factor, scope)` activation count
once. Distinct scopes count independently.

Any future count-valued, real-valued, or multiplicity-sensitive feature must
be a different explicit factor kind. It must not arise accidentally from join
multiplicity.

### Energy and probability

Each factor definition has a separately stored finite parameter \(\theta_r\).
The score of a feasible configuration is:

\[
S_\theta(x,c) =
\sum_r \sum_s \theta_r F_{r,s}(x,c).
\]

The conditional model is:

\[
P_\theta(x \mid c) =
\frac{
  \mathbb{1}[x \in \Omega_C(c)]\exp(S_\theta(x,c))
}{
  Z_\theta(c)
},
\qquad
Z_\theta(c) =
\sum_{x' \in \Omega_C(c)} \exp(S_\theta(x',c)).
\]

Hard constraints therefore assign zero support; they are not large negative
factor weights. Rules determine the facts observed by factors; they do not
themselves contribute energy. Choice weights used for search ordering remain
distinct from learned factor parameters.

For a single decision \(d\), the local conditional over its feasible
alternatives \(a\) uses the same score:

\[
P_\theta(d=a \mid c,x_{\setminus d}) =
\operatorname{softmax}_{a \in A_C}
S_\theta(x_{\setminus d},d=a,c).
\]

This equality is important: a local choice scorer and a global Gibbs sampler
must not implement different factor semantics.

### Branch evaluation protocol

The semantic evaluation order should be:

```text
context + reversible choice assumption
    -> joint rule/constraint fixed point
    -> reject inconsistent branch
    -> evaluate pure factors on the closed snapshot
    -> aggregate scoped activations and log-score
    -> retain explanation
    -> rollback branch state
```

Factor evaluation must be pure with respect to the session. Scoring one
alternative must not affect later alternatives, refraction, domains,
provenance, or random-number state other than through an explicit sampler.

### Properties to specify and test

The stable semantics should establish:

- rule-schedule independence for scoreable programs;
- factor-order and witness-order independence;
- idempotence of `(factor, scope)` activation;
- independence of activation vectors from parameter values;
- zero support for constraint-inconsistent configurations;
- rollback invariance across alternative scoring;
- equality between the local full conditional and the conditional induced by
  the global energy;
- deterministic explanations for deterministic contexts;
- explicit behavior for missing, `FAUX`, and `INEXISTANT` facts;
- explicit rejection of non-finite parameters and scores.

Open semantic questions should be resolved in an architecture decision record:

1. Do factors observe only the terminal fact snapshot, or may a declaration
   name a specific program step?
2. Which programs containing `REMOVE` are scoreable?
3. Are factor scopes required to be ground and hashable at evaluation time?
4. How are cyclic derivations and inconsistent terminal states reported?
5. Is a factor Boolean only, or should future numeric feature values receive
   a separate syntax and type?
6. Can parameters be shared by several factor definitions, and if so, how is
   that sharing declared and explained?

## Integrating learning without mixing concerns

Learning should be represented by three independent artifacts.

### 1. Model source

The model source defines factor structure and parameter names. The existing
`FACTOR_GROUP`, `FACTOR`, `SCOPE`, `LOG_WEIGHT`, and `WHEN` syntax is the
starting point. The final syntax should allow a parameter binding to be
distinguished from a literal initial value, for example:

```text
FACTOR_GROUP path_preferences
    PARAMETER endpoint_agreement INITIAL 0.0

    FACTOR same_endpoints
    SCOPE SEQ[path]
    PARAMETER endpoint_agreement
    WHEN
        (left color $color)
        (right color $color)
    END_FACTOR
END_FACTOR_GROUP
```

This proposed form is intentionally provisional. The formatter, validator,
AST, and Python API must agree before it is accepted.

### 2. Learning program

A learning declaration describes how named examples fit named parameters; it
does not embed a corpus in rule syntax and does not execute as an inference
action. A possible manifest syntax is:

```text
LEARNING_PROGRAM learn_path_preferences
    MODEL path_preferences
    DATASET path_corpus
    OBJECTIVE CONDITIONAL_LOG_LIKELIHOOD
    REGULARIZATION L2 0.01
    OPTIMIZER ADAM LEARNING_RATE 0.05
    TRAIN_SPLIT train
    VALIDATION_SPLIT validation
    TEST_SPLIT test
END_LEARNING_PROGRAM
```

`DATASET path_corpus` should resolve through a registered, typed dataset
adapter. Paths, CSV schemas, music-specific encodings, and arbitrary Python
callbacks do not belong in factor semantics.

The initial generic Python surface should contain concepts equivalent to:

```python
FactorExample(context_facts, choices, observed_configuration)
FactorDataset(examples, split_metadata)
FactorObjective
FactorLearner.fit(model, dataset, objective, optimizer)
LearningResult(parameters, history, diagnostics, manifest)
```

Exact class names remain an API design decision.

### 3. Trained artifact

A fitted model is a reproducible data artifact, not modified source text. Its
manifest should record:

- model and factor-grammar versions;
- selected factor-definition identifiers;
- parameter values and initialization;
- corpus, split, and preprocessing digests;
- objective, regularization, optimizer, stopping criterion, and random seeds;
- train and validation metrics;
- whether the structure was fixed or selected during the run;
- parent artifact and promotion status;
- whether a sealed test split has been opened.

Loading a trained artifact should bind parameters to an independently parsed
model and fail loudly on missing or changed factor identifiers.

### Parameter learning

The first objective should be exact conditional log-likelihood over a finite
set of alternatives. Its gradient is the observed activation vector minus
the model expectation:

\[
\nabla_{\theta_r}\log P_\theta(x^* \mid c)
=
F_r(x^*,c)
-
\mathbb{E}_{P_\theta(X\mid c)}[F_r(X,c)].
\]

The exact implementation is both useful and an oracle for approximate
learners. It should use stable log-sum-exp calculations and expose per-factor
gradient diagnostics.

Global generative fitting can then use:

\[
\nabla_{\theta_r}\mathcal{L}
=
\mathbb{E}_{\text{corpus}}[F_r]
-
\mathbb{E}_{P_\theta}[F_r],
\]

with exact enumeration on toys and Gibbs estimates on larger models. The
result must identify whether expectations were exact, contrastive,
persistent, or obtained by another approximation.

### Structure learning

Generating/selecting factors and fitting their parameters are separate
operations:

```text
FactorGrammar
    -> CandidateGenerator
    -> FactorSelector
    -> frozen factor structure
    -> ParameterLearner
    -> trained artifact
```

A parameter refit must never silently add or remove factor clauses. A
structure-learning run must report the candidate universe, selection rule,
controls, and final frozen identifiers. This preserves the distinction already
made in the Bach V6 experiment.

## Generic inference integration

The current application-specific factor-to-choice bridge should eventually be
replaced by two generic services:

- `FactorScorer`: closes and scores one complete or locally completed
  configuration, returning activations and an explanation;
- `FactorGuidedChoicePolicy`: enumerates feasible alternatives, batch-scores
  them with a `FactorScorer`, and orders or samples them using normalized
  scores.

The policy must filter by hard feasibility before normalization. It must keep
search heuristics, temperature, random seeds, and beam limits outside the
learned model. The same scorer should be reusable by exact enumeration,
conditional training, greedy decoding, reversible search, and Gibbs sampling.

Batch scoring and caching may optimize shared closures, but every optimized
path must remain differentially tested against independent branch evaluation.

## Exact learning oracle

### Categorical preference

One object chooses among three values. Three unary factors are learned from a
tiny count table.

Purpose:

- introduce factor declarations, parameters, scores, softmax, and training;
- recover empirical log-odds up to the expected additive constant;
- provide a finite-difference gradient and artifact round-trip test.

This case intentionally has no rule or constraint interaction. It is the
smallest mathematical diagnostic for the learning layer and must be presented
as a test oracle, not as a Snarky language example.

## Toy example ladder

Every example called a Snarky toy must exercise the complete path:

```text
versioned corpus
    -> declared learning objective
    -> learned factor parameters
    -> reversible choices
    -> hard constraint filtering
    -> rule closure
    -> pure factor evaluation
    -> prediction or generation
```

The examples should be executable, documented in the textual language and
Python, and small enough to verify by enumeration. Rules and constraints must
have observable roles: removing either must change a documented result. Each
example has a distinct pedagogical purpose.

### Toy 1: weather-aware lunch choice

This is the minimal end-to-end tutorial: one contextual decision, three
alternatives, a tiny corpus, one objective, a few rules, one hard constraint,
and three learned parameters.

The context contains a temperature and whether the diner is gluten-free. The
choice is `soup`, `salad`, or `sandwich`.

Rules derive:

```text
temperature < 12                  -> cold_day
temperature >= 12                 -> warm_day
cold_day AND chosen(soup)         -> comforting_match
warm_day AND chosen(salad)        -> fresh_match
```

The hard constraint is:

```text
gluten_free -> chosen meal must not be sandwich
```

Factors observe `comforting_match`, `fresh_match`, and `chosen(sandwich)`.
Their structure is declared in the model; only their log weights are learned.

The complete training corpus can initially fit on one page:

| Example | Temperature | Gluten-free | Observed meal |
|---|---:|---:|---|
| `l01` | 5 | no | soup |
| `l02` | 8 | no | soup |
| `l03` | 10 | no | sandwich |
| `l04` | 16 | no | sandwich |
| `l05` | 18 | no | salad |
| `l06` | 23 | no | salad |
| `l07` | 7 | yes | soup |
| `l08` | 20 | yes | salad |

The declared objective is exact conditional log-likelihood:

```text
OBJECTIVE CONDITIONAL_LOG_LIKELIHOOD
TARGET chosen_meal
CONDITIONED_ON temperature gluten_free
```

For each row, training enumerates the three meals, removes constraint-invalid
alternatives, computes rule closure, evaluates the factor vector, applies a
softmax, and updates the three parameters. The final report must show:

- learned parameters and per-example factor explanations;
- `P(sandwich) = 0` for every gluten-free context;
- a higher soup probability on cold days than on warm days;
- a higher salad probability on warm days than on cold days;
- exact NLL before and after training;
- identical results from the Python and textual-language forms.

The entire example should run with one command and produce both a prediction
table and a few seeded meal samples. This is the "corpus + objective + a few
rules, then learn" example that should appear first in the user guide.

### Toy 2: three-node path coloring

Three nodes choose among three colors. Adjacent nodes must have different
colors. A rule derives whether the two endpoints agree; a learned factor
captures the corpus preference for endpoint agreement. The versioned corpus
contains complete valid colorings, and the declared objective is exact joint
maximum likelihood under full enumeration.

State space: \(3^3=27\) raw configurations, small enough for exact
normalization.

Purpose:

- exercise all four semantic layers;
- demonstrate that invalid adjacent colors have zero probability;
- demonstrate a non-local factor induced by a rule-derived fact;
- compare exact joint probabilities, Gibbs full conditionals, and learned
  expectations.

This should become the primary global-model tutorial because it is visual,
domain-neutral, and hand-checkable.

### Toy 3: three-task scheduling

Three tasks choose three time slots. Hard constraints prevent overlap and
enforce a deadline. Rules derive `morning`, `adjacent`, and `idle_gap`
properties. Factors learn corpus preferences for early urgent work and
compact schedules. The corpus contains complete schedules with task metadata;
the initial objective is exact joint maximum likelihood, with conditional
pseudo-likelihood reported as a comparison rather than silently substituted.

Purpose:

- separate expert feasibility from corpus preference;
- show multiple scopes and parameter sharing;
- demonstrate explanations that identify which scoped factors favor an
  alternative;
- expose collinearity or non-identifiability diagnostics on a tiny corpus.

### Toy 4: four-note melody

Four positions choose pitches from a five-pitch range. Hard constraints
enforce range and a fixed final pitch. Rules derive signed intervals and
cadential position. Factors learn stepwise motion, repetition, and approach
to the final note from a synthetic corpus. The declared first objective is
exact joint maximum likelihood; local conditional likelihood is then fitted
as an explicit ablation using the same corpus and factor structure.

State space: at most \(5^4=625\) raw configurations.

Purpose:

- bridge the generic language to Bach without SATB-specific machinery;
- compare local conditional training with a joint generative refit;
- show how a factor grammar creates candidates while parameters remain
  separate;
- generate complete, inspectable samples.

The synthetic corpus should be generated from known parameters before any
hand-authored corpus is used. Recovery of those parameters and moments makes
the example a scientific test, not only a demo.

### Common acceptance criteria

Every toy example must include:

- `.rules`, `.constraints`, and `.factors` sources;
- a tiny versioned dataset and split manifest;
- a declared target, conditioning set, and learning objective;
- an executable training command;
- an exact enumeration report containing partition function, NLL, activation
  moments, and learned parameters;
- a generation or prediction command with deterministic seed support;
- per-alternative factor explanations;
- Python/textual-language parity tests;
- a README explaining which concern belongs to each language layer.

For each toy, an ablation must show that removing the rules changes the factor
observations, removing the constraints changes the support, and replacing
learned parameters with zero changes the learned prediction or generation.
The examples should fail if a hard constraint is replaced by a soft factor or
if a factor attempts to mutate working memory. This makes the separation of
concerns observable rather than rhetorical.

## Bach migration

The Bach experiment should migrate only after the toy semantics and exact
learner are stable.

Migration steps:

1. wrap existing decision records as generic `FactorExample` values;
2. replace the application-specific choice bridge with `FactorScorer`;
3. reproduce all V6 activation vectors and scores before retraining;
4. express the frozen 30-factor structure as a generic model artifact;
5. reproduce the conditional NLL and generative moment reports;
6. move corpus-specific feature extraction behind a registered adapter;
7. preserve the sealed test policy and existing manifests.

Numerical parity should be checked before deleting or simplifying any Bach
adapter. The initial target is identical factor scopes and scores, not an
immediate improvement in musical quality.

## Phased action plan

### Phase 0 — semantic design record

Deliver:

- a normative definition of closure, feasibility, scopes, energy, local
  conditionals, and rollback;
- decisions for the six open semantic questions above;
- type and error behavior for parameters and dataset bindings;
- examples of valid and invalid programs.

Exit criterion: the categorical oracle, lunch choice, and path-coloring models
have an unambiguous paper-and-pencil interpretation.

### Phase 1 — exact finite learner

Deliver:

- generic examples, datasets, objectives, and learning results;
- exact alternative enumeration and stable conditional NLL;
- analytic and finite-difference gradients;
- the categorical-preference oracle.

Exit criterion: synthetic parameters or equivalent probabilities are
recovered within documented tolerance.

### Phase 2 — generic factor-guided choices

Deliver:

- `FactorScorer` and `FactorGuidedChoicePolicy`;
- batch alternative scoring and explanations;
- weather-aware lunch and path-coloring examples;
- differential rollback and local/global-conditional tests.

Exit criterion: local conditional scores match the exact joint oracle.

### Phase 3 — language and artifact integration

Deliver:

- final parameter-binding and learning-program syntax;
- parser, formatter, validator, and diagnostics;
- versioned trained-artifact schema and loader;
- CLI commands for validation, fitting, evaluation, and explanation.

Exit criterion: a model can be trained and replayed without application
Python other than a registered dataset adapter.

### Phase 4 — structure-learning boundary

Deliver:

- explicit candidate grammar, generator, selector, and frozen-structure
  artifact interfaces;
- scheduling and four-note-melody examples;
- permutation controls and identifiability diagnostics.

Exit criterion: a structure refit and a parameter-only refit produce visibly
different manifests and cannot be confused by tooling.

### Phase 5 — Bach migration and scale

Deliver:

- Bach V6 parity on generic services;
- exact-versus-approximate expectation diagnostics on retained small slices;
- batched and cached scoring benchmarks;
- a promotion report based on frozen validation criteria.

Exit criterion: the generic implementation reproduces the frozen V6 baseline
before any new Bach result is claimed.

### Phase 6 — publication evaluation

Deliver:

- rule-only, constraint-only, hand-weighted, conditionally learned, and
  generatively refitted ablations;
- at least two non-musical examples;
- comparisons with a plain feature matrix or logistic baseline and a relevant
  probabilistic rule system;
- runtime, sample quality, calibration, moment, and explanation metrics;
- a final preregistered opening of any still-sealed test set.

Exit criterion: the claims are supported independently of the Bach case study.

## Verification matrix

| Concern | Required oracle or test |
|---|---|
| parsing and formatting | parse-format-parse structural equality |
| factor purity | fact snapshot, refraction, and domains unchanged |
| scope semantics | duplicate witnesses produce one scoped activation |
| hard support | infeasible configurations have exactly zero probability |
| gradients | analytic result matches finite differences |
| normalization | probabilities sum to one under exact enumeration |
| local/global parity | Gibbs full conditional matches joint-energy ratio |
| rollback | alternative order does not change scores or state |
| API parity | Python and textual models produce identical activations |
| artifact replay | saved and reloaded parameters reproduce metrics |
| optimized scoring | differential equality with independent branch scoring |
| data hygiene | split and corpus digests checked before training |

Performance benchmarks should separately measure factor matching, closure per
alternative, batch scoring, exact enumeration, gradient throughput, Gibbs
mixing/effective sample size, and explanation overhead. Semantic tests must
not depend on benchmark timing.

## Publication path

Two papers are more defensible than one overloaded claim:

1. a language/systems paper about the four-layer semantics, implementation,
   exact toy oracles, reversible inference, and generic learning interface;
2. a music paper about inducing an explainable factor language from the Bach
   corpus and comparing conditional and global objectives.

The language paper should not claim novelty for weighted logical rules or
log-linear factors alone. It should position the contribution relative to
Markov Logic Networks, Probabilistic Soft Logic, CHRiSM, Dyna, Scallop,
DeepProbLog, TensorLog, and related neuro-symbolic or probabilistic logic
systems. The comparison should focus on the precise interaction of mutable
rule closure, hard propagated support, pure scoped factors, and reversible
choice.

The music paper should compare with both symbolic harmonizers and learned
systems such as DeepBach. Its strongest claim is explainable structure and the
ability to inspect corpus/model moment mismatch, not state-of-the-art
generation merely from a favorable conditional NLL.

Before submission:

- freeze claims, factor grammar, metrics, and split policy;
- run permutation and random-feature controls;
- report the conditional-versus-generative trade-off, including regressions;
- perform the ablations listed above;
- resolve source and artifact redistribution licensing;
- open a sealed test split only after the evaluation manifest is frozen.

## Risks and safeguards

- **Semantic circularity:** learning from facts whose derivation depends on
  learned choices can be valid, but closure and conditioning must be explicit.
- **Constraint leakage:** encoding preferences as hard constraints can inflate
  metrics. Every restriction needs an expert/corpus provenance label.
- **Witness multiplicity:** accidental join counts can change a model.
  Boolean scoped activation remains the default.
- **Choice-weight confusion:** search order, proposal probability, and model
  probability must use different types and names.
- **Unidentifiable factors:** shared or collinear features require reference
  parameters, regularization, and diagnostics.
- **Approximate-gradient ambiguity:** every result must state how model
  expectations were estimated.
- **Data leakage:** corpus and split digests are required in artifacts and
  reports.
- **Premature DSL breadth:** implement one exact objective end to end before
  adding optimizer and objective variants.
- **Music-specific core:** no pitch, voice, chord, or chorale concept belongs
  in the generic factor or learning APIs.

## Immediate next actions

The recommended implementation order is:

1. write the Phase 0 architecture decision record;
2. implement the exact finite conditional learner;
3. build categorical preference as the mathematical oracle;
4. build lunch choice as the minimal complete language tutorial;
5. introduce the generic scorer and factor-guided choice policy;
6. add path coloring, scheduling, and four-note melody;
7. finalize learning and artifact syntax from those examples;
8. migrate Bach V6 with strict numerical parity;
9. run ablations and publication comparisons.

This order keeps the semantic and learning contracts testable on tiny state
spaces before performance and musical complexity make errors difficult to
diagnose.
