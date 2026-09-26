# Workforce scheduling

Scheduling uses `snarky.finite` variables, propagation, rules, factors, search,
rollback and provenance. Time is discrete; positive constant durations form
half-open intervals `[start, start + duration)`. Touching endpoints do not overlap.

## Architecture and reuse

| Requirement | Implementation |
|---|---|
| Task metadata | Immutable `Task`; fields reference ordinary finite variables |
| Precedence, release/deadline, rest | Helpers compose existing integer linear inequalities |
| AND / OR | `AllOfConstraint` / `AnyOfConstraint` compose ordinary persistent constraints |
| Optional task | Ordinary `Number(0/1)` variable; scheduling helpers condition on presence |
| Alternative tasks | `ExactlyOne` uses an existing linear sum of presence variables |
| Availability | A small native constraint filters start/resource/presence jointly |
| Capacity | Basic candidate filtering against fixed intervals, using endpoint events |
| Staffing / resource capacity | `ResourceLoadConstraint` bounds load over time |
| Working time | `WorkloadConstraint` bounds assigned duration, optionally clipped to a window |
| Persona preferences | Existing positive rules, `IntegerFactor`, `TableFactor`, `FactorObjective` |
| Dynamic hard activation | Existing `GuardedConstraint` and positive rule-derived facts |
| Explanations | Existing removal causes, rule derivations and factor support facts |

The existing `finite.examples.scheduling_model` demonstrates distinct unit slots,
a guarded table and overtime scores. These additions extend the same path with
durations, windows and loads. The older `FiniteConstraint`/`PredicateConstraint`
callbacks only check assignments; scheduling primitives propagate before complete
assignment. The finite model has no symbolic expression object for an end time:
use `start + duration` when displaying it, or an ordinary linear equality if an
explicit end variable is required. Operational `CHOICE` weights remain separate
from model objectives.

## Core API

```python
from snarky import Atom, Number
from snarky.finite import (
    Capacity, FiniteModel, FiniteVariable, NoOverlap, Precedence, Task,
    availability_constraints, solve,
)

sa, sb, wa, wb = map(Atom, ("a_start", "b_start", "a_worker", "b_worker"))
alice, bob = Atom("alice"), Atom("bob")
a = Task("a", sa, duration=3, resource=wa)
b = Task("b", sb, duration=2, resource=wb)
model = FiniteModel(
    "two_tasks",
    variables=(
        FiniteVariable(sa, tuple(map(Number, range(8, 13)))),
        FiniteVariable(sb, tuple(map(Number, range(9, 21)))),
        FiniteVariable(wa, (alice, bob)),
        FiniteVariable(wb, (alice, bob)),
    ),
    constraints=(
        Precedence(a, b, min_lag=1, max_lag=6),
        NoOverlap(a, b, when_same_resource=True, min_gap=1),
        Capacity((a, b), capacity=2, demands=(1, 2)),
        *availability_constraints(a, {alice: ((8, 12), (14, 18)), bob: (9, 20)}),
        *availability_constraints(b, {alice: ((8, 12), (14, 18)), bob: (9, 20)}),
    ),
)
result = solve(model)
```

Creating a task posts nothing. Declare all referenced variables in the model.
Start domains contain integer `Number` terms; fixed starts/workers use singleton
domains. Scheduling helpers accept `name=Atom(...)` for readable causes. Default
names derive from tasks or windows; explicitly name multiple constraints with the
same default name in one model.

### Temporal windows, rest and alternatives

- `Precedence(a, b, min_lag=0, max_lag=None)` bounds the gap between `end(a)` and
  `start(b)`. Both bounds propagate in both directions. Lags are nonnegative.
- `StartWindow(task, earliest, latest_end)` enforces release time and deadline.
- `NoOverlap(a, b, when_same_resource=True, min_gap=1)` leaves one slot of rest
  between the two tasks if their workers coincide. The default gap is zero.
- `OptionalTask(task, present)` returns updated metadata; build subsequent
  constraints with that returned task. `Task(..., present=present)` is equivalent.
- `ExactlyOne(tasks)` requires exactly one present alternative. Mandatory tasks
  count as present; repeated presence references are combined in the sum.

Presence domains must contain only integer `Number(0/1)`. Pairwise precedence and
non-overlap are disabled if either task is absent. Absent tasks do not consume
capacity, coverage or workload. Their start/resource variables still have values;
custom preferences should include presence to avoid charging absent tasks.

### Multiple availability windows

`availability_constraints(task, windows)` returns a one-element tuple, preserving
the original unpacking convention. Each resource maps to either `(open, close)`
or a sequence of such windows. Overlapping and touching windows are merged.
A present task must fit in the resulting union; it cannot cross a gap such as a
lunch break. Missing resources have no availability.

Filtering is now joint: an impossible worker can be removed before the worker
is assigned, and unsupported start/presence values are removed too. The predicate
has at most three distinct variables and handles shared references correctly.
A named `GuardedConstraint` can still wrap it for rule-driven activation.

### Capacity, coverage and multiple pools

```python
from snarky.finite import Coverage, Workload, resource_capacity_constraints

coverage = Coverage(tasks, window=(8, 12), minimum=2, resources=(alice, bob))
hours = Workload(tasks, alice, maximum=8, minimum=2, window=(0, 24))
pools = resource_capacity_constraints(tasks, {alice: 1, bob: 2})
```

`tasks`, `alice` and `bob` here stand for the application's tasks and resource
values. For skill coverage, select the qualified workers with `resources=...`,
or pass only tasks whose resource domains already enforce the required skill.

- `Capacity(tasks, capacity, demands=None)` represents one shared pool, ignoring
  task resource assignments. Demands default to one and must be nonnegative.
- `resource_capacity_constraints(tasks, capacities, demands=None)` creates one
  load constraint for each selected resource value. Only tasks actually assigned
  to that value contribute. Unlisted resource values are unconstrained.
- `Coverage(tasks, window, minimum, resources=None)` requires enough active tasks
  at every slot in the window. It counts **tasks**, not distinct workers; combine
  it with worker non-overlap when modeling headcount.
- `ResourceLoadConstraint` also exposes combined lower/upper bounds, weighted
  demands, optional resource selection and an optional window. A positive lower
  bound requires a finite window.
- `Workload(tasks, resource, maximum, minimum=0, window=None)` sums assigned
  durations. With a window, each task contributes only its overlap with that
  window. Without one, it does not depend on start variables. Combine with
  non-overlap if overlapping assignments should be forbidden.

Workload filtering uses small per-task relations and sum bounds, avoiding a
Cartesian product over the workforce or additional hours variables. The older
formulation—table channels to hours variables plus a linear sum—remains useful
when those hours also participate in a soft fairness objective.

These propagators provide sound filtering, not complete consistency across
correlated tasks. Capacity considers fixed intervals for lower-bound loads;
coverage sums each task's possible contribution for an upper bound. Candidate
restrictions apply to every shared variable reference. Some infeasibility still
requires search. There is no mandatory-part timetable, energetic reasoning or
edge finding. Endpoint checks avoid allocating a dense calendar.

### Avoiding unnecessary pairs

```python
from snarky.finite import no_overlap_constraints

pairs = no_overlap_constraints(tasks, model.domains, min_gap=1)
```

This helper omits pairs with disjoint possible resources or provably separated
time ranges. Supply the model's full declared domains. **Rebuild these constraints
if you widen domains**, because the omitted pairs relied on those bounds.
Otherwise posting every pair with `NoOverlap` remains correct.

## Preferences and optimization

A `TableFactor` can score `(worker, start)` tuples, with zero default for all
other assignments. Rules can instead derive `(task penalty early)` facts from
commute, family or transport attributes. An `IntegerFactor` queries those facts
and contributes once per ground task scope, regardless of witness multiplicity.
Use an integer multiplier for `operational_cost + weight * human_preference_cost`.

Default `solve(..., bounding="auto")` now compiles safe bounds for factors whose
premises contain only positive facts and comparisons:

1. Ground positive rule implications over all declared candidate value facts.
2. Close singleton value facts to obtain facts true in every completion.
3. Close all remaining candidate facts to obtain a superset of possible facts.
4. Bound the number of matching ground scopes, reversing endpoints for negative
   weights; add the existing table-factor bounds.

Simultaneous alternative values are a relaxation, not a feasible assignment.
Repeated witnesses are deduplicated per scope. Recursive positive rules and
alternative derivations are supported. Scores and explanations are still computed
by the existing engine; the bounds never replace their contributions.

Compilation is capped at 100,000 counted operations and 4,096 facts by default;
closure caches hold at most 256 snapshots. Unsupported factor premises or an
exceeded compilation budget retain the prior safe bound fallback. Deadlines
remain query deadlines. `bounding="local"` disables this compilation for A/B
comparisons. `value_policy="objective"` uses bounds to order candidate values;
it is opt-in and is used by both workforce demos.

For unsupported factors, complete scoring remains available even when no useful
partial objective bound is known. This is still finite search, so broad domains
and tightly coupled rules may remain expensive.

## Examples and measurements

```sh
python -m benchmarks.workforce_scheduling
python -m benchmarks.workforce_scheduling_extended
pytest tests/test_finite_scheduling.py tests/test_finite_scheduling_extended.py
pytest tests/test_finite_factor_bounds.py
```

The [basic demo](../benchmarks/workforce_scheduling.py) has five fictional workers
and ten tasks. The first feasible schedule has operational cost 0 and human
penalty 24. The combined optimum has operational cost 6 and penalty 6. An
exhaustive A/B check retained all 32 schedules and their scores after optimization.

The [extended demo](../benchmarks/workforce_scheduling_extended.py) has five
workers and twelve tasks: ten mandatory tasks and two optional alternatives.
It combines lunch breaks, rest gaps, bounded precedence gaps, morning/afternoon
coverage, working-time bounds and presence-aware persona preferences. Its tested
optimum is 8 (operational cost 2, human penalty 6). It reports termination and
has a ten-second limit rather than assuming every instance finishes.

Measured solve-time medians over three fresh processes, on the recorded machine:

| Case | Before | Current default bounds | Current bounds + objective ordering |
|---|---:|---:|---:|
| Basic demo | 100 ms, 63 nodes | 37 ms, 37 nodes | 18 ms, 15 nodes |
| Every start has 13 choices | 5 s limit, feasible only | 286 ms, 321 nodes | 89 ms, 87 nodes |

Imports and model construction are excluded; bound compilation is included.
The wide case is a synthetic flexibility probe with existing zero-default cost
tables. The timeouts do not establish a speedup ratio or an optimum for the old
solver. The [raw interleaved measurements](../benchmarks/results/scheduling_2026-09-26.json)
include all runs, source hashes and exhaustive demo equivalence. The
[comparison runner](../benchmarks/scheduling_comparison.py) supports a source
snapshot, and the [before-source patch](../benchmarks/results/scheduling_2026-09-26_before.patch)
reconstructs that snapshot over commit `d86e035`.

## Provenance and limits

Domain removals retain their outer constraint name. Compound constraints do not
add a branch-level proof tree. Integer-factor supports retain penalty facts;
existing rule derivations link them to persona and assignment facts. Positive
rules activate predeclared constraints/factors through facts; they do not mutate
the immutable model with new constraint objects during search.

The extension is a Python finite API. It adds no `.model` grammar or legacy CSP
syntax. Durations remain positive constants; there are no zero-length milestones,
calendars, time zones, routing, inventory flow or sequence-dependent travel/setup
times. No IATP adapter or feedback loop is implemented; the examples use fictional
persona facts. Re-optimization can use a new model context or weights and the
existing validated `initial_assignment` option when that schedule is still feasible.
