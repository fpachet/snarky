# Instantiation strategy lifecycle

Instantiation strategies are stateful execution components. They may retain
fact indexes, partial joins, existential witnesses, domain tables, adaptive
decisions, and metrics between rule evaluations. Search and read-only choice
queries therefore need explicit isolation rules.

## Core contract

Every strategy implements `InstantiationStrategy`:

- `instantiate(rule, facts, delta)` returns deterministic activations;
- `invalidate(removed)` updates indexes after known removals;
- `invalidate()` discards state when the precise mutation is unavailable;
- `metrics` exposes work counters but never changes semantics.

This original protocol remains sufficient for forward chaining and for
third-party strategies.

## Optional branch contract

`BranchableInstantiationStrategy` adds:

```python
def fork_for_branch(self) -> InstantiationStrategy: ...
```

The result must be isolated from subsequent mutations of the parent strategy.
It may reuse immutable definitions and clone indexes already populated for the
current fact snapshot. Search uses this method structurally and does not check
the concrete strategy class.

Built-in behavior:

| Strategy | Branch behavior |
|---|---|
| `NaiveInstantiationStrategy` | creates a fresh stateless strategy |
| `IndexedInstantiationStrategy` | clones the populated fact index |
| `SemiNaiveInstantiationStrategy` | clones the index and preserves semi-naïve and event-handler configuration |
| `ConstraintInstantiationStrategy` | preserves configuration and branch-local filter state |
| `AdaptiveInstantiationStrategy` | preserves its concrete type, configuration, and adaptive state |

If a third-party strategy does not implement this optional contract,
`InferenceSession.fork()` keeps the compatibility behavior and deep-copies
the strategy.

An explicit `branch_strategy_factory` remains authoritative when configured
for the root branch. It allows callers to replace rather than clone a
strategy.

## Optional query contract

`QueryableInstantiationStrategy` adds:

```python
def query_view(self) -> InstantiationStrategy: ...
```

The returned view is used to evaluate declarative `CHOICE` rules without
polluting the session strategy's query witnesses or rule memories. A view may
share the immutable fact index for the current snapshot, but query-local
caches must remain isolated.

If the session strategy does not provide a query view, choice production uses
a fresh `IndexedInstantiationStrategy`. This preserves the behavior available
before the lifecycle contract.

## Rollback boundary

Session checkpoints restore observable inference state. Strategy internals are
not part of `SessionCheckpoint`; rollback either invalidates the current
strategy or replaces it with an isolated branch template maintained by the
search driver.

This separation is intentional:

- checkpoints describe semantic session state;
- strategies are derived execution caches;
- invalidation may discard optimization state but must not change results.

Tests must compare facts, derivations, mutation events, activation counts, and
search traces across reversible and forked execution. Metrics may differ.

Factorized event plans themselves are immutable products of rule compilation
and can be shared. Their indexes belong to the strategy instance and therefore
follow the normal fork and invalidation rules. The
`use_factorized_event_rules` option is preserved by `fork_for_branch()`; it
can be disabled for differential benchmarks without changing semantics.
