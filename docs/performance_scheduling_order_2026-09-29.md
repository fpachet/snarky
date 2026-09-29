# Local improvement and exact scheduling order search

This follow-up builds on the [kernel comparison](performance_scheduling_improvements_2026-09-29.md).
**The new portfolio proves 16 of 18 cases within the common ten-second
heuristic-plus-search budget, up from 12 with the previous seeded method. All
18 returned schedules match the published optima.** The outcomes repeat across
three fresh processes per case/variant (162 runs). `j309_1` and `j3014_1` still
lack an optimality proof at ten seconds.
The fixed selection remains 12 J30 projects and FT06/LA01–LA05. Published
objectives are used only to evaluate completed workers.

## Results

| Method | Proven optimal / 18 | Feasible, unproved | Schedules matching known optimum |
| --- | ---: | ---: | ---: |
| Previous seeded method | 12 | 6 | 12 |
| Local improvement + general finite search | 13 | 5 | 15 |
| Local improvement + order-search portfolio | **16** | **2** | **18** |

Counts and final objectives agree in all three repetitions. There are no process
errors or reference contradictions. The newly proved cases are **LA01=666,
LA02=655, LA03=597 and LA04=590**. All job-shop cases in this selection are now
proved. LA01 closes because local improvement meets an elementary resource
bound. LA02–LA04 require order search. The J30 optima 83 and 50 are found by
local improvement, but search does not certify them in ten seconds.

The [main archive](../benchmarks/results/scheduling_next_2026-09-29.json) retains
all runs, phases, heuristic histories and witnesses. Its
[source snapshot](../benchmarks/results/scheduling_next_2026-09-29_sources.tar.gz)
preserves all 110 measured source/protocol files. The measured sources stayed
unchanged throughout the comparison.

In the table below, `objective / time` means proven optimal. Time is the median
of heuristic preparation, model construction and full solve-call times, excluding
input parsing and Python startup/imports. `feasible` means the budget expired.

| Case | Previous seeded | Local + finite | Order portfolio |
| --- | --- | --- | --- |
| j301_1 | 43 / 0.142 s | 43 / 2.144 s | 43 / 2.144 s |
| j305_1 | 53 / 2.358 s | 53 / 4.325 s | 53 / 4.327 s |
| j309_1 | 88 feasible | 83 feasible | 83 feasible |
| j3014_1 | 51 feasible | 50 feasible | 50 feasible |
| j3018_1 | 53 / 0.151 s | 53 / 2.146 s | 53 / 2.146 s |
| j3022_1 | 42 / 0.162 s | 42 / 2.163 s | 42 / 2.162 s |
| j3027_1 | 43 / 0.132 s | 43 / 0.132 s | 43 / 0.134 s |
| j3031_1 | 43 / 0.134 s | 43 / 0.135 s | 43 / 0.135 s |
| j3035_1 | 57 / 0.145 s | 57 / 0.149 s | 57 / 0.147 s |
| j3040_1 | 51 / 0.130 s | 51 / 0.130 s | 51 / 0.131 s |
| j3044_1 | 50 / 0.134 s | 50 / 0.134 s | 50 / 0.135 s |
| j3048_1 | 63 / 0.158 s | 63 / 0.157 s | 63 / 0.156 s |
| ft06 | 55 / 0.512 s | 55 / 1.396 s | 55 / 1.135 s |
| la01 | 696 feasible | 666 / 0.425 s | 666 / 0.396 s |
| la02 | 746 feasible | 658 feasible | 655 / 2.193 s |
| la03 | 669 feasible | 619 feasible | 597 / 2.801 s |
| la04 | 675 feasible | 598 feasible | 590 / 6.077 s |
| la05 | 593 / 0.416 s | 593 / 0.418 s | 593 / 0.390 s |

The fixed local-improvement phase adds about two seconds on `j301_1`, `j305_1`,
`j3018_1` and `j3022_1`, and also slows FT06. These regressions are retained;
the portfolio improves proof coverage, not every case's runtime. The original
finite solver remains available unchanged. An inexpensive proof attempt before
local improvement would be a useful follow-up to avoid spending the full local
budget on incumbents that were already optimal.

## Targeted diagnostics and longer runs

These are single fresh-process diagnostics, declared in the
[supplemental protocol](../benchmarks/data/scheduling_standard/NEXT_DIAGNOSTICS.md).
They are excluded from the main three-repeat aggregates. Their times are
individual observations, not stable timing estimates.

The [search diagnostics](../benchmarks/results/scheduling_next_2026-09-29_search_diagnostics.json)
and [budget controls](../benchmarks/results/scheduling_next_2026-09-29_diagnostic_control.json)
use six seconds including preparation. `objective / time` denotes a proof;
`feasible` denotes timeout.

| Method at six seconds | LA02 | LA03 | LA04 |
| --- | --- | --- | --- |
| Portfolio | 655 / 2.091 s | 597 / 2.726 s | 590 feasible |
| First conflict only | 655 / 2.213 s | 597 / 2.852 s | 590 feasible |
| Critical conflict only | 658 feasible | 619 feasible | 590 / 5.127 s |
| Portfolio + energy windows | 655 / 2.138 s | 597 / 3.645 s | 590 feasible |
| Portfolio + not-first/not-last | 655 / 2.157 s | 603 feasible | 590 feasible |

The conflict policies have complementary strengths. The six-second portfolio
still misses LA04's proof, whereas the main ten-second portfolio proves it in
all three repetitions. Energy checks leave LA03's first-phase node count at
3,661 while adding time in this diagnostic. Not-first/not-last filtering also
fails to improve coverage. These filters therefore remain opt-in.

The [model diagnostics](../benchmarks/results/scheduling_next_2026-09-29_model_diagnostics.json)
try derived conflicts and a compact finite-model phase on the two remaining J30
cases. All four ten-second runs retain the optimum schedules but time out before
proof. Adding redundant conflicts is sound, but it is not automatically faster.

The [60-second runs](../benchmarks/results/scheduling_next_2026-09-29_extended.json)
keep the same preparation and initial phase limits and spend the extra time in
order search:

| Case | Incumbent | Reported root bound | Entered nodes across phases | Outcome |
| --- | ---: | ---: | ---: | --- |
| j309_1 | 83 | 58 | 204,548 | Feasible, unproved |
| j3014_1 | 50 | 43 | 220,080 | Feasible, unproved |

Thus this work completes proofs for the selected job shops, but **does not
complete all 18 proofs**, even in the longer runs. More incumbent improvement
cannot help these two cases because their incumbent values are already optimal.
Further work needs stronger cumulative-resource bounds or a search that avoids
more equivalent failures. Cumulative overloads can involve more than two tasks,
which makes the current pair-separation branching overlap. Exact-state memoizing
only removes some of that duplication; general conflict learning is not included.
These observations concern this implementation and these budgets, not an
intrinsic limit on what a small scheduling solver can prove.

## What changed

### Local improvement

The [local improvement helper](../benchmarks/scheduling_local.py) starts from a
validated constructive schedule. Project moves insert activities at different
positions in a priority list and rebuild a capacity-feasible schedule. Job-shop
moves swap adjacent machine operations on a critical path. Longest-path
calculations reject cyclic machine orders; tabu restrictions and deterministic
restarts help leave local minima. Every improved incumbent is checked against
the original instance constraints. Finding a schedule is never treated as an
optimality proof unless a sound lower bound or exhaustive search closes the gap.

Trials use a fixed random seed. The budget permits up to 5,000 local iterations
and two seconds after the previous constructive portfolio. Elementary bounds
computed from the input can end local improvement early. The fixed local budget
can add time on easy cases whose incumbents were already optimal.

### Derived conflicts and shared incumbents

`build_model(..., conflicts=True)` adds `NoOverlap` when two project activities'
combined demand exceeds any capacity, unless the original precedence graph
already orders them. All original capacity constraints remain. This is an
optional equivalent strengthening, not a symmetry assumption.

The main portfolio gives projects up to 2.5 seconds of search in the original
finite model, then passes the best incumbent to order search. For both families,
order search first spends up to two seconds on the first available conflict,
then uses the remaining time on conflicts with larger path bounds. Each phase
shares its improved schedule with the next. A proof ends the run. Phase budgets
are chosen by family, never by instance name or reference objective.

The `shared` diagnostic instead starts with a compact finite model and derived
conflicts for up to two seconds. It tests whether a different formulation can
supply useful incumbents to order search.

### An explicit exact scheduling solver

The new [scheduling search module](../src/snarky/finite/scheduling_search.py) is a
separate, opt-in native Python solver for mandatory tasks with fixed integer
durations, precedence arcs and fixed renewable-resource demands. It has no
external optimizer dependency. The general finite solver and its existing
`solve` API are unchanged. Optional tasks, calendars, resource choices and mixed
rules are outside the new solver's contract.

A search state is a precedence graph. Longest paths provide earliest starts and
minimum remaining durations. For a resource with capacity `c`, tasks with
`head >= a` and `tail >= b` must execute all their work between `a` and `C-b`.
Consequently `C >= a + ceil(sum(duration*demand)/c) + b`. The solver checks these
subset bounds and abandons a node as soon as it cannot improve the incumbent.
For incompatible pairs it also forces an order when the opposite order's path
bound cannot fit below the incumbent.

If the earliest schedule overloads a resource, the solver selects a minimal
overloaded set. Every feasible schedule must separate some pair in that set:
intervals that overlap pairwise have a common intersection, which would overload
the resource. Branching on both orders of every pair therefore covers every
feasible completion, even when every pair individually fits capacity. Each
branch adds a precedence. Cycles fail; a resource-feasible earliest schedule is
a validated incumbent. Exhausting the branches proves optimality.

Branches can overlap. A memo keyed by transitive closure merges graphs that
represent identical orders despite different redundant arcs. It stores at most
50,000 keys; reaching that cap disables further insertion, not further search.
This is repeated-state detection, not conflict-clause learning. The DFS stack
and graph storage have their own memory costs.

Two stronger optional filters are included:

- Energy-window checks count unavoidable partial execution inside windows
  anchored at release times and completion deadlines. This is a sound subset
  of energetic reasoning, not a complete energetic propagator.
- Unary not-first/not-last checks infer earliest-start or remaining-duration
  bounds when a task cannot precede or follow an entire set of machine tasks.
  This is not full edge finding.

They are disabled by default because extra propagation can cost more than it
saves in search. Timeout bounds are root relaxation bounds; they do not describe
the remaining search frontier. Timeout always retains the validated incumbent.

## API example

```python
from snarky.finite.scheduling_search import SchedulingProblem, solve_schedule

problem = SchedulingProblem(
    durations=(2, 2, 2),
    successors=((), (), ()),
    demands=((1,), (1,), (1,)),
    capacities=(2,),
)
result = solve_schedule(problem, incumbent=(0, 2, 4), seconds=10)
assert result.status == "optimal"
assert result.objective == result.bound == 4
```

The incumbent must cover every task and satisfy the original constraints.
Zero-duration, zero-demand dummies are supported. Starts are nonnegative
integers; resource intervals are half-open. Results report status, objective,
starts, bound, entered nodes, elapsed time and improving incumbent history.
`conflict_policy="first"` is the standalone default; `"critical"` is available
explicitly. `energetic=True` and `not_first_last=True` enable the optional filters.
The benchmark portfolio's phase switching is implemented in its driver.

## Measurement

The [protocol](../benchmarks/data/scheduling_standard/NEXT.md) compares the
archived `bda7b5e` runtime and previous seeded method (`previous`), the same
finite solver with local improvement (`local`), and the new portfolio (`order`).
The original constructor's default formulation is unchanged; archived runtime
hashes and all current driver/source hashes are recorded.

Each case/variant runs in three fresh processes with hash seed zero. Complete
pair order reverses on alternate repetitions. The ten-second budget includes
constructive generation, local improvement and search. Model construction is
recorded separately and included in algorithm totals. The finite API initializes
native state outside its search clock, and solve-call totals include that
additional overhead. The new order solver starts timing before validating its
incumbent and building search structures. Whole-process times include imports.

```sh
python -m benchmarks.scheduling_next --repeat 3 --seconds 10 \
  --output generated/scheduling_next_new.json
python -m benchmarks.scheduling_verify \
  benchmarks/results/scheduling_next_2026-09-29.json
```

## Validation

Tests compare exact optima against independent enumeration of integer schedules
on 100 random cumulative-resource models and independent machine-order
permutations on 30 random job shops. Both conflict policies and combinations of
optional propagation are exercised. Tests also cover overloaded sets larger than
two tasks, zero-duration dummies, arbitrary task indices, invalid inputs,
callbacks, interruption and resuming from the retained schedule.

Another 150 random bounded-window models directly check that energy and
not-first/not-last deductions preserve every independently enumerated feasible
assignment. Local improvement is checked for reproducibility and feasibility. Tiny fixtures
enumerate all solutions with and without derived conflicts under both original
and compact formulations. Benchmark replay independently checks every saved
solver incumbent and constructive/local improvement record against original
instance semantics.

Independent replay validated **1,446 stored schedule records in the 162 main
runs**, plus 497 records across 21 diagnostic/extended runs. Records include
repeated schedules in different roles and repetitions. All 183 workers completed
without process errors or contradictions with the reference objectives. All
five archives confirm unchanged sources and share the same 110 source hashes.
The source snapshot and current workspace match every recorded hash.

The complete non-Bach redesign gate passed: **1,240 passed, 6 skipped in
207.14 seconds**. Ruff, formatting of the solver/harness/tests, strict mypy
(102 source files), DSL syntax/format checks (305 files), Markdown links and
whitespace checks pass. The wheel and source distribution build, distribution
content audit and isolated installation/import/inference/console checks pass.
The installed-wheel check explicitly exercises the new order solver. See the
[validation log](../benchmarks/results/scheduling_next_2026-09-29_validation.txt).
