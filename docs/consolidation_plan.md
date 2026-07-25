# Snarky consolidation plan

## Objective

Turn the current research prototype into a stable, testable, and publishable
scientific software package without changing its observable inference
semantics.

The consolidation target is a public research library:

- the semantic core must remain small and independently installable;
- historical reconstruction, applications, and optional integrations remain
  outside the mandatory runtime dependencies;
- optimizations must stay comparable with a simple semantic oracle;
- explanations, determinism, and reproducible experiments take precedence
  over adding new mechanisms.

## Frozen baseline

The baseline was recorded on 2026-07-25 at commit `50aeef0`, after the first
tonal harmonizer prototype:

- 420 tests pass and 2 optional MuSES tests are skipped;
- Ruff reports no issue;
- mypy strict mode validates the 39 modules under `src`;
- Python 3.12 or later and PyYAML are the only core requirements.

`docs/Shal.doc` is a local, untracked source document and is outside the
consolidation scope.

## Non-negotiable invariants

Every consolidation change must preserve, unless an explicit versioned
semantic decision says otherwise:

1. deterministic fact and activation ordering;
2. equality of naïve and optimized fixed points;
3. provenance and proof depths;
4. explicit distinction between absence, `FAUX`, and `INEXISTANT`;
5. refraction behavior after additions and removals;
6. exact restoration of facts, indexes, provenance, events, and fresh names
   after rollback;
7. isolation of caller sessions during search;
8. optionality of CSP backends and MuSES;
9. immutable terms and fact snapshots at application boundaries.

## Work streams

### C0 - Reproducible baseline and continuous integration

- Run tests, Ruff, and mypy on every change.
- Build a wheel in CI to detect packaging regressions.
- Record benchmark commands separately from correctness checks.
- Keep generated benchmark results dated and machine-qualified.

Acceptance: a clean checkout reproduces the baseline with one documented
command, and the same checks run on GitHub.

### C1 - Explicit strategy lifecycle

- Replace concrete-type checks in search with a structural branch lifecycle
  contract.
- Specify fresh, forked, query-only, invalidated, and reversible strategy
  states.
- Keep a safe fallback for third-party strategies implementing only the
  original instantiation protocol.

Acceptance: built-in and custom strategies branch without search knowing
their concrete classes, with differential tests against the previous paths.
The detailed contract is recorded in
[`strategy_lifecycle.md`](strategy_lifecycle.md).

### C2 - Mutable-state robustness

- Generate small rule programs and sequences of additions and removals.
- Compare naïve, indexed, semi-naïve, and constraint-aware execution.
- Exercise nested checkpoints, rollback reuse, truth maintenance, negative
  premises, and refraction.
- Add Hypothesis only after deterministic generated cases define the oracle
  and failure representation.

Acceptance: every generated sequence produces identical observable facts and
derivations across supported strategies, or documents an intentional
strategy-specific metric difference.

### C3 - Internal decomposition

Refactor without semantic changes, in this order:

1. split session state, checkpoint state, and agenda execution out of
   `engine/forward.py`;
2. split choice production, frontier management, and traversal out of
   `choice.py`;
3. split fact indexing, existential-query memory, and semi-naïve joins out of
   `instantiation/indexed.py`;
4. split domain planning, propagators, compact tables, and adaptive selection
   out of `instantiation/domain_filter.py`;
5. split lexical analysis, term parsing, premise parsing, and action parsing
   out of `parser.py`.

Acceptance: each extraction is independently reviewable, keeps the public
imports compatible, and passes the full differential suite.

### C4 - Public API and release boundaries

- Classify exports as stable core, advanced, integration, or experimental.
- Reduce the top-level namespace while keeping a deprecation path.
- Define semantic-versioning rules for the Python API, rule DSL, and
  serialization formats.
- Add package metadata, project URLs, release notes, and a license only after
  the corresponding legal decisions are explicit.
- Test installation and imports from the built wheel.

Acceptance: a new user can identify the supported API without reading the
implementation, and compatibility promises are written down.

### C5 - Documentation and language policy

English is the publication language for:

- the root README and package metadata;
- core architecture, API, semantics, benchmarks, CSP, Sudoku, and harmonizer
  documentation;
- code identifiers, docstrings, comments, and diagnostics.

French remains the primary language for the Spinoza corpus, its formalization,
reports, and atlas. A later English overview may describe that case study
without translating or replacing the French source material.

Each document has one primary language. Historical quotations and primary
sources remain in their original language and carry explicit provenance.
Terminology is normalized before translation; mixed-language mechanical
translation is not accepted.

Acceptance: the English README offers a short path from installation to a
minimal rule, then points to focused guides. Research history and benchmark
chronology no longer dominate onboarding.

### C6 - Repository and publication hygiene

- Audit the redistribution status of every document and third-party corpus.
- Keep sources with unclear rights out of public releases until resolved.
- Add contribution, security, citation, and release guidance appropriate for
  a scientific package.
- Separate source data, generated artifacts, and reproducible build outputs.

Acceptance: every distributed external artifact has recorded provenance and
an explicit redistribution decision.

## Execution order

1. C0 and C1 establish automated and architectural guardrails.
2. C2 validates the mutable core before internal extraction.
3. C3 proceeds in small behavior-preserving changes.
4. C4 defines the first stable release boundary.
5. C5 migrates publication-facing documentation against that stable boundary.
6. C6 is completed before a public tagged release.

New inference features, advanced Sudoku techniques, full ATMS, reflective
meta-rules, parallel search, and additional harmony profiles remain outside
this consolidation plan. They stay in the feature roadmaps and must not delay
the stabilization work.

## Progress

The first consolidation tranche establishes:

- the `Quality` GitHub workflow for linting, strict typing, tests, and wheel
  construction;
- typed-package metadata and a PEP 561 marker in the built wheel;
- structural branch and query lifecycle contracts without concrete strategy
  checks in search;
- compatibility fallback for third-party strategies;
- deterministic and Hypothesis-generated mutation and truth-maintenance
  sequences across naïve, indexed, and semi-naïve execution;
- the first C3 extraction: checkpoints, rollback, time-tag trails, snapshots,
  and isolated forks now live in `engine/session_state.py`, while incremental
  agenda memory, dependency tracking, delta reduction, and conflict-set
  materialization live in `engine/agenda.py`;
- rule-group modes, limits, results, and execution coordination now live in
  `engine/group_execution.py`, leaving `InferenceSession.run_group()` as the
  stable public facade;
- external assumptions and retractions, action staging, activation mutations,
  fresh-name reservation, and grounded truth-maintenance cascades now live in
  `engine/mutations.py`, with `InferenceSession` retaining compatibility
  delegates;
- negative-premise dependency planning, support expiry, and refraction
  reconciliation now live in `engine/refraction.py`;
- traversal modes and stable DFS, BFS, and best-first pending storage now live
  in `choice_frontier.py`, with `ChoiceTraversal` re-exported from its
  historical public module;
- declarative choice models, `RuleChoiceProvider`, query isolation, and
  sequential `CHOICE` production now live in `choice_production.py`.

Historical public import paths remain compatible and are covered by identity
tests.

The internal decomposition is also guarded against performance regressions.
An interleaved comparison of baseline commit `50aeef0` and post-extraction
commit `2da2902`, using the same Python 3.13.11 process environment on macOS
ARM64, produced:

| Workload | Baseline | Extracted modules | Difference |
|---|---:|---:|---:|
| indexed explicit Fibonacci, F(12) | 393.63 ms | 393.79 ms | +0.04% |
| four queens choice search | 14.24 ms | 14.30 ms | +0.37% |
| two-position choice harmonizer | 34.07 ms | 34.16 ms | +0.28% |
| four-position choice harmonizer | 496.54 ms | 499.60 ms | +0.62% |
| tonal harmonizer, symbolic input | 838.26 ms | 835.65 ms | -0.31% |
| tonal harmonizer, object round trip | 851.76 ms | 850.11 ms | -0.19% |

Each value is the mean of two independently measured medians, in
baseline-current-current-baseline order, with 9 repetitions for the engine
and choice workloads and 7 for the tonal workloads. Logical counters are
identical in both versions. These sub-percent differences are measurement
noise rather than a material regression. Raw medians, commands, environment,
and counters are recorded in
[`consolidation_refactor_2026-07-25.json`](../benchmarks/results/consolidation_refactor_2026-07-25.json).

After the policy and traversal extractions, commit `ae2358b` was checked
again against the post-baseline reference. The four-position search changed
by -0.37%, the tonal symbolic path by -0.05%, and the object round trip by
+0.39%, with identical search counters. The choice decomposition therefore
has no material measured runtime cost.

The `engine/forward.py` decomposition target is complete for C3. The next
choice decomposition target is also complete: production, policies, frontier
management, and traversal live in focused modules, while `choice.py` is a
26-line compatibility facade preserving every historical public import
identity. The next tranche starts the decomposition of
`instantiation/indexed.py`, beginning with fact indexing and protected by the
same differential and performance suites.
