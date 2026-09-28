# Interchangeable workforce scheduling — 28 September 2026

## Result and scope

The 32-task population POC needs four emergency assignments, costing 400. A new
explicit symmetry helper and faster workload propagation prove that optimum on
its monolithic model within the ten-second budget. Both changes are reusable:

- `interchangeable_task_constraints` constructs a reduced optimization model for
  mandatory tasks whose interchangeability the caller explicitly certifies.
- Workload filtering updates candidate contribution bounds through the affected
  task relations. It preserves the previous filtering semantics, including shared
  variables and clipped working-time windows.

The [implementation plan](scheduling_optimization_plan.md) records the scope.
The POC, its results, IATP and MaxEnt were not modified. No network/API call,
external solver, oracle-selected assignment or oracle-supplied bound was used.

## Diagnosis

The [original profile](../benchmarks/results/scheduling_symmetry_2026-09-28_profile_original.txt)
attributes 9.805 seconds of a 10.002-second profiled solve to workload filtering.
Profiling adds substantial overhead: that run entered nine nodes and found no
incumbent, so these timings are diagnostic and are not latency comparisons.
The POC posts every worker's workload constraint over all tasks. The former
kernel recomputed each task's contribution extrema for every candidate of every
variable. Tasks that could never use that worker were repeatedly scanned too.

The new kernel builds the same per-task contribution relations, totals their
minimum/maximum loads, and indexes the relations by variable. A candidate only
replaces the contributions of relations containing that variable. Domain
reductions update those relations before the next candidate variable is checked.
Constant contributions stay in the totals but require no candidate checks. All
caches are local to a revision, so rollback cannot expose stale cached state.

This preserves the independent-task sum relaxation. It does not add stronger
scheduling consistency or an allocation objective bound. Unary emergency-cost
factors still select a zero-width table objective relaxation; competition for
workers is mainly exposed through propagation and branching. Faster propagation
alone improves throughput but leaves redundant permutations to search. Explicit
resource ordering eliminates enough of those permutations to complete the proof.

## Measurement protocol

The [collector](../benchmarks/scheduling_symmetry.py) uses the
[archived fixture](../benchmarks/data/scheduling_symmetry/inputs.json). It retains
all original tasks, variables, availability, pair constraints, worker workload
limits and unary emergency costs. The helper emits the same strict resource-order
relations as the POC's handwritten tables, with explicit private alternatives.

Four variants isolate the changes: original workload filtering, symmetry only,
new workload filtering only, and both changes. For the first two, the harness
loads the original `revise_workload` from commit `f8c82b5`; all other runtime code
is identical. This reference selection exists only in the benchmark harness.
The archive embeds the full historical kernel and fingerprints current runtime
sources, the collector and the input file.

Each variant runs in a fresh process three times, interleaved with reversed
order on the second repetition. `PYTHONHASHSEED=0` is fixed. Solve timings include
objective-bound compilation and exclude imports and model construction, which
is reported separately. First-incumbent times, histories, proof times, revisions,
bounds, termination and complete schedules are archived. Profiles are separate
runs and are not included in the latency medians.

Each variant also runs as four skill components, solved sequentially without
proof caching. Independence is certified by this fixture's disjoint eligible
workers and additive costs. Each solve has ten seconds; a decomposed run can
therefore use up to forty seconds. These totals are not a comparison under equal
global deadlines. Every incumbent and assembled schedule is checked independently.
Only proven component optima establish a composed optimum.

The matching oracle runs after solving. Its exactness relies on two-hour tasks
and a two-hour workload cap: each internal worker can cover at most one task.
It is a validation tool for this benchmark family, not a general scheduling oracle.

## Measurements

The [raw archive](../benchmarks/results/scheduling_symmetry_2026-09-28.json)
contains all repeated runs. These measurements used Python 3.13.11 on macOS
15.7.7 arm64. Medians of three fresh processes:

| Variant | Monolithic solve | Nodes | Final bound | Status | Four-component total | Status |
|---|---:|---:|---:|---|---:|---|
| Original | 10.001 s | 134 | 200 | Feasible, time limit | 10.118 s | Feasible, unproved component |
| Symmetry only | 3.397 s | 40 | 400 | Optimal | 0.106 s | Optimal |
| Propagation only | 10.001 s | 1,618 | 200 | Feasible, time limit | 10.030 s | Feasible, unproved component |
| Both | **0.148 s** | **40** | **400** | **Optimal** | **0.032 s** | **Optimal** |

Every incumbent costs 400 and passes independent validation. The original and
propagation-only runs retain root bound 200; they do not prove optimality within
the limit. The independent oracle verifies that their incumbents are optimal,
but this is not reported as a Snarky proof.

With symmetry held fixed, workload optimization reduces median proof time by
**22.9×**, preserving all 40 nodes and 1,455 constraint revisions. The combined
monolithic range is 0.148–0.151 seconds. Its median construction time is 0.004
seconds. Without symmetry, the first incumbent improves from 7.535 to 0.209
seconds, but faster search alone does not close the proof gap.

For the four-component runs with symmetry, both kernels enter 43 nodes and make
927 revisions in total. Workload optimization reduces median total solve time
from 0.106 to 0.032 seconds. These are synthetic single-machine results; there is
no measured speedup ratio against an original monolithic completed proof.

Separate profiles of the same ordered model show workload filtering falling
from 8.765 to 0.216 seconds under instrumentation, with 769 workload revisions
in each. The original full-model profile and these matched profiles agree that
repeated workload scans dominated the earlier implementation.

The [candidate patch](../benchmarks/results/scheduling_symmetry_2026-09-28_candidate.patch)
reconstructs the measured runtime, fixture and collector on top of `f8c82b5`.
Apply it in a separate checkout of that commit, then run the collector command
from the [benchmark guide](../benchmarks/README.md#workforce-scheduling). The
archive embeds the historical kernel as well as current source hashes. A fresh
reconstruction matched all 103 recorded hashes and independently reproduced the
combined optimum of 400 in 40 nodes.

## Validation

### Effect on existing scheduling tests

A separate [collector](../benchmarks/scheduling_test_comparison.py) runs the
same 40 existing scheduling and factor-bound tests with the historical and
optimized workload kernels. It adds no symmetry constraints. Five repetitions
per variant run in fresh processes, with interleaved order and a fixed hash seed.
All 40 tests passed in all ten runs. The
[raw results](../benchmarks/results/scheduling_tests_2026-09-28.json) include
per-test durations, outcomes, source hashes and environment details.

| Measurement | Historical filter | Optimized filter | Time reduction |
|---|---:|---:|---:|
| Pytest invocation, 40 existing tests | 1.557 s | 1.503 s | 3.5% |
| Basic scheduling module, test bodies | 0.930 s | 0.921 s | 1.0% |
| Extended scheduling module, test bodies | 0.419 s | 0.382 s | 8.9% |
| Factor-bound module, test bodies | 0.134 s | 0.132 s | 1.6% |

The invocation timing includes collection and fixture work but excludes process
startup, imports performed before pytest, and historical-kernel loading.
Module figures sum test-call durations, excluding setup and teardown, before
taking the median. The basic workforce integration test remains about 0.693 s;
the extended workforce integration test improves from 0.278 to 0.267 s. The
seeded load-oracle test improves from 0.139 to 0.113 s.

The existing suite gains modestly because it also spends time in independent
oracles, enumeration and other kernels. The five invocation ranges overlap
(historical 1.545–1.598 s, current 1.495–1.613 s), so these small differences are
descriptive local measurements, not a statistical significance claim. The
22.9× proof improvement applies to the workload-heavy 32-task benchmark above.

### Correctness and packaging

The full configured suite passed **1,189 tests, with 6 skipped**, in 210.69
seconds. This includes 34 new symmetry and workload tests. Ruff, strict mypy
(101 source files), syntax/format validation (305 DSL files), Markdown links,
package builds, distribution contents and isolated wheel installation checks
passed. The original POC input/evidence hash remains unchanged.

Small cases compare all feasible original schedules against a separate exhaustive
checker and compare optimum values with independent matching. They include early,
late and flexible starts, scarce workers, no workers, zero emergency cost, reversed
and renamed identities, minimization and maximization. Every enumerated witness
is checked against original hard semantics. The reference finite enumerator and
native enumeration also agree.

Other tests verify shared-resource reuse, repeated private-emergency ranks and
structural rejection of unequal eligibility, start domains, durations, optional
tasks, aliases, unknown resource values and malformed private mappings. Deliberately
false certifications with asymmetric costs, task restrictions and precedence
show that equal metadata is insufficient and can lose the optimum. No automatic
grouping is attempted. Constructing helper constraints without adding them leaves
original enumeration, partition masses and seeded sampling unchanged.

The workload filter is compared with an independent slow min/max implementation
on 350 seeded models and three domain snapshots per model. Cases include shared
start/resource/presence variables, optional tasks, constant contributions,
minimum/maximum loads and clipped or empty windows. Successful domain reductions
match exactly; infeasibility results agree. Existing scheduling tests cover mixed
activation, provenance, rollback and timeout resumption.

## Migrating the POC

In `scheduler.py`, keep the current explicit `symmetry_breaking` option and group
construction. Replace the `ranks`, `emergency_rank`, pair-loop and handwritten
`TableConstraint` construction with:

```python
from snarky.finite import interchangeable_task_constraints

for group in groups.values():
    constraints.extend(
        interchangeable_task_constraints(
            group,
            domains,
            resource_order=tuple(Atom(w.name) for w in workers),
            private_resources={
                task.name: Atom(f"emergency_{task.name}") for task in group
            },
            certified=True,
            distinct_resources=True,
        )
    )
```

Keep the POC's check that all tasks have duration two and all workers have a
workload cap of two. Together they justify strict ordering within each group.
Its identical job costs, skill eligibility and availability semantics justify
permuting jobs together with their private emergencies. The helper validates
structural prerequisites, not these global facts. Reassess certification whenever
adding task-specific costs, constraints or rules.

Default `distinct_resources=False` permits repeated worker assignments for other
models. Optional tasks are currently rejected. Use the returned constraints only
in the reduced model used for optimization; ordinary constraint objects cannot
prevent later enumeration or sampling from that reduced model. Preserve the
original model for counts and distributions. See the complete
[API contract](scheduling.md#interchangeable-tasks).

## Remaining work

- Stronger resource-allocation bounds could address the proof gap when tasks
  are not interchangeable. The current result does not establish which bound
  would pay for its compilation and evaluation costs on broader models.
- Workload scopes still include tasks with identically zero contributions.
  Narrowing static incidence could reduce queue work further, but it requires
  careful handling of declared domains and shared references.
- Objective-bound construction repeatedly reads constraint scopes; the new
  ordered-model profile spends 0.128 seconds there under instrumentation.
  Caching immutable scopes is a separate potential optimization to measure.
- Generic component decomposition is not implemented. The POC's workload
  constraints syntactically mention all tasks, even when most contributions are
  always zero, so graph-based decomposition needs semantic simplification first.
- Availability, optional-task symmetry, task-dependent setup times and larger
  mixed-rule workloads need their own evidence. The measured gains apply to
  this restricted synthetic scheduling family.
