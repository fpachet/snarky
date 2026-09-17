# Runtime boundary tutorials

Run the [executable examples](../rulebases/projects/runtime_boundaries.py):

```sh
python -m rulebases.projects.runtime_boundaries
```

They exercise three contracts that matter when extending the engine.

## Custom propagation

`propagation_example()` supplies a deterministic filter that removes only one
fact per invocation. Search calls it until stable, then checks the goal.
The branch ends with `a`; the caller's session still has `a`, `b`, and `c`.

A propagator may declare `watched_relations` to limit rescheduling. Its own
changes to those relations also schedule another call. Omit this metadata if
the dependency set is unknown. A filter that never stabilizes raises a
bounded-iteration error instead of exposing an unfinished state to choices.

## Saving explanations

`snapshot_example()` derives a conclusion at depth one and saves the result.
Assuming that same conclusion makes its current proof depth zero. Rolling
back removes the conclusion from the session while the saved result retains
its original explanation and depth one.

Snapshots and group results own isolated provenance copies. The session's
`provenance` property remains its live working view. Historical `Derivation`
records retain their depths at firing time; `depth()` and
`minimal_derivation()` reflect shorter proofs currently known. A new
assumption also shortens dependent minimum depths, and rollback reverses
those changes.

When a caller needs only the session mutation, `run_group(group,
materialize_result=False)` avoids constructing a saved result.

## Feasibility, choice priorities, and factor scores

`preferences_example()` gives a forbidden alternative a high local choice
weight. The contradiction condition still rejects it, and search returns the
feasible alternative. A separate pure factor evaluation gives that result a
score of two without changing facts, events, or the solution's choice weight.

Persistent constraints and contradiction conditions determine feasibility.
`CHOICE` weights guide local ordering or sampling. Factor log weights score
groundings. This example does not implement globally normalized sampling;
the [probabilistic extension](probabilistic_constraint_learning_spec.md)
defines that separate research objective.

## Installed console validation

From the checkout, install both local distributions:

```sh
python -m pip install -e .
python -m pip install ./csp_solver
snarky check --syntax-only --format .
```

The installed console can now parse constraints outside the checkout. Without
the companion, rule and program validation remain available and constraint
validation explains how to install it. During development,
`python -m snarky check --syntax-only --format .` uses the current checkout
directly. See [language tooling](language_tooling.md) for diagnostics.
