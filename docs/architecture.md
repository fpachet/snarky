# Architecture

Snarky separates immutable language objects, inference state, instantiation
strategies, search control, integrations, and application rulebases. The
separation keeps one executable semantic reference while allowing optimized
components to evolve independently.

## Layers

```text
application rulebases and orchestration
                |
      explicit search / programs
                |
      inference sessions and groups
                |
 agenda, mutation, refraction, provenance
                |
       instantiation strategies
                |
 terms, facts, matching, substitutions
```

### Language model

`terms.py`, `facts.py`, `substitutions.py`, `matching.py`, `premises.py`,
`actions.py`, and `rules.py` define immutable symbolic objects and exact
matching behavior. They do not own mutable inference state.

The textual DSL is parsed through focused lexical, term, arithmetic, premise,
and action modules. `parser.py` is the public facade and group/rule
orchestrator.

### Inference engine

The `engine` package owns mutable execution:

- `session_state.py` stores working memory, indexes, time tags, and checkpoint
  snapshots;
- `mutations.py` applies staged fact changes;
- `refraction.py` tracks continuously valid activations;
- `provenance.py` records derivations and proof depth;
- `agenda.py` and `conflict.py` support optional conflict resolution;
- `group_execution.py` implements group modes and stop conditions;
- `forward.py` provides `InferenceSession` and `ForwardEngine`.

Application code interacts with sessions rather than these internal modules.

### Instantiation

The `instantiation` package implements interchangeable strategies:

- `base.py` defines the lifecycle contract and metrics;
- `naive_join.py` is the semantic reference;
- `fact_index.py`, `query_memory.py`, and `semi_naive_join.py` support
  persistent optimized matching;
- `event_rules.py` compiles simple and safe factorized multi-premise delta
  handlers;
- `indexed.py` composes indexed and semi-naive strategies;
- domain planning, compact tables, propagators, and adaptive selection provide
  optional finite-domain filtering.

Strategies receive net fact deltas, may retain state between calls, and must
implement isolation when a session forks. Differential tests enforce logical
equivalence with the naive strategy.

Factorized event plans are immutable, rule-keyed compiled definitions. For
an addition-only delta they match the added fact against a statically filtered
anchor position, then follow exact fact-index lookups for the other positive
premises. Compilation requires comparisons to have been bound at their
original textual position and excludes `FOCUS`; every unsupported shape and
every removal follows the existing general path.

### Search and control

Forward inference is deterministic and does not branch implicitly.

`choice_production.py` extracts declarative choice points.
`choice_policies.py` selects among them. `choice_frontier.py` owns DFS, BFS,
and best-first frontier mechanics. `choice_search.py` coordinates branch
checkpoints, goals, contradictions, and solutions. `choice.py` remains a
compatibility facade.

`programs.py`, `plans.py`, and `group_templates.py` provide explicit,
inspectable orchestration above rule groups.

### Integrations and applications

`snarky.integrations` converts external object graphs to immutable fact
snapshots and back. Integrations are optional boundaries; the inference core
does not depend on MuSES or application packages.

The `csp_solver`, `sudoku`, `harmonizer`, `rulebases`, and `spinoza`
directories contain domain knowledge, orchestration, fixtures, and
application tests. Generic behavior belongs in `src/snarky`; domain shortcuts
do not.

## State and isolation

An inference session is the unit of mutable state. It owns facts and insertion
order, strategy state, refraction, provenance, events, fresh-name counters,
and checkpoint trails.

`fork()` creates a branch-isolated session. A checkpoint restores the same
session in place. Search policies choose the mechanism appropriate to their
frontier while preserving caller isolation.

Instantiation strategies are stateful collaborators of the session. Their
clone and reset behavior is part of the lifecycle contract described in
[strategy_lifecycle.md](strategy_lifecycle.md).

## Dependency rules

- terms and matching must not depend on the engine;
- optimized strategies must not change semantic ordering or results;
- the forward engine must not contain domain-specific CSP, Sudoku, or music
  knowledge;
- search remains explicit above forward inference;
- optional integrations must not become core dependencies;
- compatibility facades may preserve imports but new internals should depend
  on focused modules.

## Verification

The quality workflow runs lint, strict typing, the complete test suite, wheel
construction, and an isolated installed-wheel smoke test.

Behavioral validation combines:

- direct unit contracts;
- naive-versus-optimized differential tests;
- property-generated mutation and lifecycle sequences;
- application oracles;
- A/B benchmarks with machine-readable raw output.

See [reference semantics](semantics.md), [API stability](api_stability.md),
and the [benchmark guide](../benchmarks/README.md).
