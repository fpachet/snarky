# Closing the selected scheduling benchmark set

**Snarky now proves all 18 selected cases in each of three repetitions, within
a budget of ten seconds for heuristic preparation and search.**

This follow-up investigates the two remaining proofs from the
[order-search comparison](performance_scheduling_order_2026-09-29.md):
`j309_1` and `j3014_1`. Their incumbents already matched the published optima,
83 and 50. The missing work was proving that schedules of length at most 82
and 49 do not exist. The solver derives those cutoffs from its own incumbents;
it does not receive the published values.

Two additions close these cases: redundant unary resources for groups of
mutually incompatible tasks, and failed-domain probing with timetable
propagation. Both run inside native Python Snarky, with no external optimizer.
The fixed selection remains 12 PSPLIB J30 projects and FT06/LA01–LA05;
completing this selection does not mean completing all of PSPLIB or OR-Library.

## Results

The [main archive](../benchmarks/results/scheduling_proofs_2026-09-29.json)
compares the previous portfolio reconstructed from commit `80abc15` with the new
portfolio. The [protocol](../benchmarks/data/scheduling_standard/PROOFS.md)
specifies three sequential fresh processes for every case and variant, a shared
ten-second heuristic-plus-search budget, and independent validation of schedules.
Construction is recorded separately and included in algorithm totals. Published
objectives are consulted only after workers finish.

The previous portfolio proves 16 cases per repetition. All 108 runs finish without
a process error or
a contradiction with published results. The largest new-portfolio algorithm
total is below the ten-second budget.

| Method | Proven optimal per repetition | Feasible, unproved |
| --- | ---: | ---: |
| Previous portfolio | 16 / 18 | 2 |
| Clique resources + root probing | **18 / 18** | **0** |

Median total algorithm times include heuristic preparation, model construction
and full solver calls, excluding Python startup and input parsing. An old timeout
does not supply an exact old proof time or a speedup ratio.

| Case | Previous total | New total |
| --- | ---: | ---: |
| j301_1 | 2.143 s | 2.142 s |
| j305_1 | 4.313 s | 2.405 s |
| j309_1 | 10.006 s (unproved) | 7.133 s |
| j3014_1 | 10.007 s (unproved) | 2.521 s |
| j3018_1 | 2.144 s | 2.143 s |
| j3022_1 | 2.162 s | 2.148 s |
| j3027_1 | 0.133 s | 0.132 s |
| j3031_1 | 0.134 s | 0.132 s |
| j3035_1 | 0.148 s | 0.146 s |
| j3040_1 | 0.131 s | 0.131 s |
| j3044_1 | 0.135 s | 0.133 s |
| j3048_1 | 0.156 s | 0.156 s |
| ft06 | 1.125 s | 1.136 s |
| la01 | 0.397 s | 0.394 s |
| la02 | 2.113 s | 2.116 s |
| la03 | 2.763 s | 2.802 s |
| la04 | 6.348 s | 6.251 s |
| la05 | 0.401 s | 0.399 s |

For `j309_1`, the final clique-based order phase takes a median **1.391 s**
and enters 2,961 nodes. The full portfolio takes **7.133 s**, including preparation
and earlier phases. Thirty additional unary resources strengthen this model.
For `j3014_1`, the window phase closes the proof in **0.371 s**, with **537
propagation probes**, 89 failed restrictions, and no DFS nodes. Total time is
**2.521 s**. These node and probe counts repeat exactly across all three runs.

`j305_1` also benefits: its median total falls from 4.313 s to 2.405 s.
The job-shop strategy is unchanged; its small timing differences should not be
interpreted as a systematic improvement. The existing two-second local-search
overhead on some easy project cases is retained.

The [source snapshot](../benchmarks/results/scheduling_proofs_2026-09-29_sources.tar.gz)
preserves all 113 measured runtime, driver and protocol files. Their hashes
remain unchanged throughout the comparison.

### Ablations

The [18 additional runs](../benchmarks/results/scheduling_proofs_2026-09-29_ablations.json)
remove one component at a time on the two formerly open cases, with the same
ten-second budget and three repetitions. Outcomes are identical in every
repetition. Times below are median total algorithm times.

| Configuration | j309_1 | j3014_1 |
| --- | --- | --- |
| Omit window phase | Proved / 6.138 s | Unproved / 10 s |
| Omit clique resources | Unproved / 10 s | Proved / 2.523 s |
| Window search without root probes | Proved / 7.144 s | Unproved / 10 s |

The clique constraints are decisive for `j309_1` in this comparison. Its window
phase costs about one second without helping the proof. Root probing is decisive
for `j3014_1`: ordinary disjoint window search does not substitute for the failed
restriction deductions within the allocated phase. The generic project portfolio
keeps both phases; it does not dispatch by instance name.

## Why the changes help

### Resource conflicts spanning several resources

`add_conflict_cliques(problem)` builds a graph whose vertices are tasks. An edge
means the two tasks' combined demand exceeds at least one original resource
capacity. Every pair in a clique must execute without overlap. Therefore a
redundant resource of capacity one, used at demand one by all clique members,
is valid even when different pairs conflict on different original resources.

The added resources let the existing work bounds account for an entire mutually
exclusive group. Previously, pairwise conflicts mainly supplied ordering choices
and forced precedences. The original constraints and feasible schedules are
preserved; this requires no task symmetry assumption.

Enumeration is deterministic and stops after 128 added groups or 10,000
enumeration nodes. It skips groups with fewer than three members and groups
already represented by a full-capacity unary resource. Truncating enumeration
only omits possible improvements. Every retained constraint is independently
valid. The helper returns a new `SchedulingProblem`, or the original when there
are no new groups.

### Failed-domain probing

The new `solve_windows` engine represents each task's allowed integer starts as
a bitset. Precedence propagation tightens its earliest and latest starts.
Compulsory task execution intervals build a shared resource-load profile; starts
that overlap an overloaded profile are removed, including holes inside domains.

At the root, the engine tentatively restricts each task to either half of its
start domain, and then to either endpoint. If precedence and timetable
propagation prove such a restriction impossible, that range can be removed from
the real domain. Successful probes imply no deduction. The process repeats until
no range is removed or a domain becomes empty. An empty domain proves that the
incumbent cannot be improved.

If root probing does not finish the proof, the engine branches on an earliest
start versus all remaining starts. Those branches are disjoint and cover the
entire domain. It validates every improved incumbent against original constraints.
A deadline interrupt retains a valid incumbent and a sound root bound; it never
turns an unfinished probe into an infeasibility claim.

The engine has the same mandatory, fixed-duration renewable-resource contract as
order search, and explicitly rejects incumbent horizons above 10,000 before
allocating time-domain bitsets. Optional energy filtering can remove start ranges
using capacity-time available in windows, but remains disabled by default.

## Portfolio and API

For projects, the benchmark runs a one-second window-search phase, then up to
2.5 seconds in the original finite solver, then spends the remaining budget in
critical-conflict order search with added clique resources. Job shops retain the
previous first-conflict/critical-conflict order-search sequence. All phases share
validated incumbents. Selection depends on the problem family, never the instance
name or reference objective.

```python
from snarky.finite.scheduling_search import add_conflict_cliques, solve_schedule
from snarky.finite.scheduling_windows import solve_windows

# problem is a SchedulingProblem; incumbent contains a valid start per task.
result = solve_windows(problem, incumbent, seconds=1)
if result.status != "optimal":
    strengthened = add_conflict_cliques(problem)
    result = solve_schedule(
        strengthened, result.starts, seconds=10, conflict_policy="critical"
    )
```

These are opt-in APIs. The general finite solver and the default order-search
algorithm are unchanged. `ScheduleResult.statistics` adds diagnostic counters.
Window search counts DFS nodes and propagation probes separately; a root proof
can have zero DFS nodes while performing hundreds of probes. Timeout bounds are
root relaxation bounds, not the best bound on the remaining search frontier.

## Exploration and rejected changes

Initial instrumentation showed that exact-state memoization catches substantially
more duplicates in `j3014_1` than in `j309_1`. That motivated trials of disjoint
start-domain branching and a temporal-constraint prototype which excludes the
ordering alternatives already covered by earlier branches. Neither alone closed
the remaining cases in the exploratory ten-second runs.

We also tried alternative task-selection policies, timetable filtering inside
order search, full energy-window domain filtering, and unary not-first/not-last
filtering on the derived cliques. The more expensive propagators did not justify
becoming defaults. The retained additions target stronger group bounds and
inexpensive failed-domain probes. General conflict-clause learning was not needed
to close this selection and remains unimplemented.

Exploratory runs guided development; they are not stable timing estimates.
The repeated comparisons and ablations provide the final performance evidence.

## Validation and reproduction

The [validation log](../benchmarks/results/scheduling_proofs_2026-09-29_validation.txt)
records **1,245 passed tests and six skips** in the full non-Bach regression gate
(230.38 s), plus lint, formatting, strict types, DSL checks, Markdown links,
distribution content checks and isolated installation. The installed wheel
exercises both the clique helper and window-search API.

Independent replay validates **1,263 stored schedule records across 126 runs**:
1,110 records in the main comparison and 153 in the ablations. All references
agree, every run is error-free, and both archives retain identical hashes for
all 113 measured source/protocol files. The saved source snapshot and final
workspace match those hashes.

Small exhaustive tests check the complete feasible-set equivalence of added
clique resources, including conflicts spanning different resources and truncated
enumeration. Independent integer-schedule enumeration checks the resulting
optima. Additional tests verify that probing preserves every feasible assignment
in domains with holes, arbitrary task numbering and zero-duration milestones.
Timeout tests interrupt a probe and check that no false proof is reported.

```sh
python -m benchmarks.scheduling_proofs --repeat 3 --seconds 10 \
  --output generated/scheduling_proofs_new.json
python -m benchmarks.scheduling_proofs --repeat 3 --seconds 10 \
  --cases j309_1 j3014_1 --variants cliques shaving unshaved \
  --output generated/scheduling_proofs_ablations_new.json
python -m benchmarks.scheduling_verify \
  benchmarks/results/scheduling_proofs_2026-09-29.json
pytest tests/test_scheduling_proofs.py tests/test_scheduling_order.py
```

Use the checksum-pinned cache prepared by the original standard benchmark.
No raw third-party instance data is included in the new tracked artifacts.
