# Scheduling propagation and incumbent improvements

**With the new kernels and constructive incumbents, Snarky proves 12 of 18
cases optimal and returns a valid schedule for all 18. The archived baseline
proves 10 and returns no schedule for the other eight.** All final statuses and
objectives repeat across three fresh processes per variant: 216 runs in total.

The new proofs are `j305_1 = 53` (2.161 seconds with kernels alone) and
`la05 = 593` (0.425 seconds including constructive generation). Times are medians
including model construction and the full solve call, excluding imports.

This follow-up preserves the [initial assessment](performance_scheduling_standard_2026-09-29.md)
and its source archive. It compares four declared variants on the same 18 cases.
The [protocol](../benchmarks/data/scheduling_standard/IMPROVEMENTS.md) gives the
budget, settings and fixed constructive trial counts. No published objective
enters any search, horizon, seed or propagator.

## Results

The [complete raw archive](../benchmarks/results/scheduling_improvements_2026-09-29.json)
retains every run and incumbent, including constructive improvement histories,
bounds, gaps, search counters and source hashes. The
[source snapshot](../benchmarks/results/scheduling_improvements_2026-09-29_sources.tar.gz)
contains all 107 measured first-party source files. The archive confirms these
files stayed unchanged during the comparison. The separate pilot is excluded
from these aggregates.

| Variant | Proven cases / 18 | Feasible but unproved | No schedule |
| --- | ---: | ---: | ---: |
| Archived baseline | 10 | 0 | 8 |
| Kernels, original model | 11 | 0 | 7 |
| Kernels + incumbent (`seeded`) | 12 | 6 | 0 |
| Kernels + incumbent + compact model (`combined`) | 11 | 7 | 0 |

Each count is the same in all three repetitions. There were no process errors
or contradictions with published optima. In the table below, `objective / time`
means **proven optimal**, with median total algorithm time. `feasible` and
`no schedule` mean the ten-second heuristic-plus-search budget expired. Times
include preparation, model construction and solve-call overhead; comparisons
therefore charge seeded variants for their constructive portfolio.

| Instance | Baseline | Kernels | Seeded | Combined |
| --- | --- | --- | --- | --- |
| j301_1 | 43 / 0.137 s | 43 / 0.024 s | 43 / 0.141 s | 43 / 0.143 s |
| j305_1 | no schedule | 53 / 2.161 s | 53 / 2.306 s | feasible 55 |
| j309_1 | no schedule | no schedule | feasible 88 | feasible 87 |
| j3014_1 | no schedule | no schedule | feasible 51 | feasible 50 |
| j3018_1 | 53 / 0.122 s | 53 / 0.030 s | 53 / 0.144 s | 53 / 0.145 s |
| j3022_1 | 42 / 0.764 s | 42 / 0.053 s | 42 / 0.164 s | 42 / 0.162 s |
| j3027_1 | 43 / 0.338 s | 43 / 0.038 s | 43 / 0.132 s | 43 / 0.133 s |
| j3031_1 | 43 / 0.458 s | 43 / 0.028 s | 43 / 0.134 s | 43 / 0.133 s |
| j3035_1 | 57 / 0.043 s | 57 / 0.013 s | 57 / 0.148 s | 57 / 0.148 s |
| j3040_1 | 51 / 0.140 s | 51 / 0.020 s | 51 / 0.131 s | 51 / 0.130 s |
| j3044_1 | 50 / 0.257 s | 50 / 0.022 s | 50 / 0.134 s | 50 / 0.132 s |
| j3048_1 | 63 / 0.674 s | 63 / 0.030 s | 63 / 0.157 s | 63 / 0.155 s |
| ft06 | 55 / 0.990 s | 55 / 0.407 s | 55 / 0.498 s | 55 / 0.298 s |
| la01 | no schedule | no schedule | feasible 696 | feasible 696 |
| la02 | no schedule | no schedule | feasible 746 | feasible 746 |
| la03 | no schedule | no schedule | feasible 669 | feasible 669 |
| la04 | no schedule | no schedule | feasible 675 | feasible 675 |
| la05 | no schedule | no schedule | 593 / 0.425 s | 593 / 0.423 s |

The kernels improve median algorithm time on all ten cases already proved by
the baseline. Constructive generation is not free: for example, `j3035_1` takes
0.013 seconds with kernels alone and 0.148 seconds with the seed portfolio.
The compact model loses the new `j305_1` proof, although it improves incumbents
on `j309_1` and `j3014_1`. It therefore remains an explicit option.

### Which kernel accounts for the improvement?

The [supplemental archive](../benchmarks/results/scheduling_improvements_2026-09-29_ablations.json)
contains 45 fresh-process runs: three repetitions, three targeted cases and five
variants. These use a separate **one-second** search limit and the original model,
with no seed. Each isolated variant restores the other archived implementations.

| Variant | `j309_1`: median nodes at timeout | `j3031_1`: median proof time | LA01: median nodes at timeout |
| --- | ---: | ---: | ---: |
| Archived baseline | 41 | 0.450 s | 3 |
| Numeric disjunctions only | 41 | 0.458 s | 922 |
| Capacity only | 1,256 | 0.029 s | 3 |
| Objective ordering only | 41 | 0.457 s | 3 |
| All kernels | 1,262 | 0.028 s | 887 |

All variants prove `j3031_1 = 43` in 17 nodes. The other two cases remain unknown
without an incumbent in these short runs. Capacity filtering accounts for the
J30 gains; compiled disjunctions account for the job-shop gain. The ordering
shortcut removes redundant work but has no measurable benefit on these cases.
Node counts under a time limit describe work completed, not a speedup on a
finished proof; initialization and propagation costs are especially visible at
one second. These diagnostics are not included in the main proof counts.

## Changes

### Compiled numeric alternatives

A two-alternative numeric disjunction over the same two variables now uses
compiled candidate masks, including ordinary mandatory fixed-machine `NoOverlap`.
Each alternative computes supports against the original domains. Their supports
are unioned before changing a domain. Failed alternatives contribute empty masks.
The generic path remains available when scopes differ, terms are unsupported,
optional/resource alternatives are present, or the compilation budget is exceeded.
Cache keys include domain masks, so rollback does not retain child-branch pruning.

Linear objective ordering now skips variables absent from the objective: every
candidate would have received the same score. Other objective types retain the
existing ordering implementation.

### Capacity profiles and overload checks

For mandatory tasks with distinct start variables, `Capacity` builds an endpoint
load profile once per revision. A task's compulsory interval is
`[latest_start, earliest_start + duration)`, when nonempty. This includes fixed
intervals as a special case. Each task is checked against the shared profile after
subtracting its own compulsory contribution. Overloaded segments become forbidden
integer start ranges; half-open endpoint semantics are preserved. No time-slot
array is allocated by the propagator, including for huge durations or time offsets.

A second check detects task sets whose full execution envelopes lie inside a
resource window and whose total `duration * demand` exceeds the available energy.
It checks windows using earliest starts and latest completions in quadratic time.
This is sound overload detection, not complete energetic reasoning or edge finding.
Optional tasks and shared start variables retain the previous fixed-interval path.
All profiles are local to a revision. Changed domains trigger another revision,
so newly created compulsory parts are included without persistent cache/trail state.

### Constructive incumbents and model options

The benchmark portfolio generates original schedules from instance inputs only.
Project trials choose eligible activities by fixed or seeded priorities and place
them at the first feasible resource slot. Job-shop trials choose from ready
operations conflicting with the earliest completion. Every trial is independently
validated; only the best schedule is passed to the existing warm-start API.

The validated makespan supplies a sound horizon. The optional compact formulation
omits real-task end links implied by paths to the project sink, or by later
operations in the same job. It preserves every original precedence. Job-shop
machines also get a redundant capacity-one constraint, allowing resource-window
reasoning beyond pairwise non-overlap. These options are explicit and leave the
original benchmark formulation available.

## Measurement

The archived runtime is reconstructed only from hash-verified first-party source
files. External benchmark data remains in the ignored, verified download cache.
Each worker uses a fresh process, with variants interleaved and order reversed
between repetitions. The ten-second budget includes heuristic generation and
search; model construction is recorded separately. End-to-end algorithm timings
include construction, and whole-process timings additionally include imports.
As in the baseline API, native-state initialization precedes the search timer;
it is included in solve-call and algorithm timings, so a timed-out call can exceed
ten seconds slightly. Reported timeout bounds are root relaxation bounds, not
continuously updated bounds over the remaining search frontier.

Reproduce the comparison:

```sh
python -m benchmarks.scheduling_standard --fetch
python -m benchmarks.scheduling_improvements --repeat 3 --seconds 10 \
  --output generated/scheduling_improvements_new.json
```

## Interpretation and limits

Keep the kernel changes enabled in the native solver. Constructive schedules and
tighter horizons are explicit benchmark options using the existing warm-start
API; they are useful when obtaining any incumbent is difficult, but their fixed
portfolio adds preparation time to easy instances.

Keep the compact formulation optional. Removing implied constraints changes
dom/wdeg's variable choices, even when the feasible set is unchanged. Extra
machine-capacity constraints likewise change propagation cost and search order.
There is no general rule that fewer constraints or stronger propagation will
reduce proof time on every instance.

LA05 illustrates a short optimality certificate: the constructed schedule meets
the existing input-derived lower bound of 593, so the solver can close the gap
without branching. This does not establish that search now solves every Lawrence
instance efficiently. Reaching a published objective is also insufficient by
itself: `j3014_1` reaches 50 with the compact model but retains a solver bound of
43 at timeout.

The remaining bottlenecks need better incumbents, stronger disjunctive/resource
bounds, or different branching. This change does not add edge finding, full
energetic reasoning, local search or nogood learning. Measurements cover this
fixed subset and formulation; they do not establish performance across PSPLIB
or OR-Library as a whole.

## Validation

The new tests compare binary disjunction supports against exhaustive Cartesian
oracles on 300 random models, including signed coefficients, holey domains,
large offsets, disabled numeric masks, compilation-budget fallback and rollback.
Guard activation/deactivation is checked separately. Another 250 random capacity
models are checked against independent time-slot enumeration; all feasible
supports must survive pruning. Selected cases enumerate the complete solution
set. Dedicated cases cover compulsory parts, overload without compulsory parts,
huge durations and timeout/resume.

Small project and job-shop fixtures compare the original, compact and bounded
models' complete feasible sets. Constructive schedules are reproducible and
validated before warm-start use. The saved-witness verifier also rejects invalid
or non-improving constructive histories.

Independent replay checked **792 schedule records across the 216 main runs**:
192 solver incumbents, 108 final constructive schedules and 492 constructive
history entries. These counts include repeated schedules in different records.
The 15 diagnostic witnesses and all 30 original baseline witnesses also passed.

Ruff, formatting of changed Python files, strict mypy (101 source files), DSL
syntax/format validation (305 files), Markdown links and whitespace checks pass.
The source distribution and wheel build, distribution-content audit and isolated
wheel installation/import/inference/console checks pass. Both source snapshots
match every recorded hash; main and diagnostic runs report unchanged sources.

The complete non-Bach redesign gate passed: **1,233 passed, 6 skipped in
216.94 seconds**. See the [validation log](../benchmarks/results/scheduling_improvements_2026-09-29_validation.txt).
The earlier assessment and its archived runtime/results remain intact; no
workforce instance or POC evidence was changed.
