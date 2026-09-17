# Propagated incumbent cuts — 17 September 2026

This follows `104d903`. Exact integer linear objectives now feed the incumbent
back into ordinary constraint propagation. The previous controller pruned a node
when its objective bound could not improve the incumbent, but did not restrict
its cost variables using that incumbent.

## Implementation and semantics

For minimization, an incumbent `U` produces `sum(terms) <= U - offset - 1`.
Maximization produces `sum(terms) >= U - offset + 1`. A single cost variable is the
unary case; existing defining constraints propagate its tighter domain back to
other variables. Signed coefficients, holes, repeated-term normalization and large
integer offsets preserve exact arithmetic. Constant objectives need no cut.

The cut is a virtual entry in the ordinary propagation queue, scheduled first and
rescheduled when its scope changes. Mixed rules and guarded constraints reach the
same joint fixed point. The search controller owns the latest immutable cut and
resupplies it after every rollback; only its consequences are trailed. No cut is
left in the model or state after search. Existing admissible bound checks remain.

`objective_propagation=False` disables cuts for ablation. Factor objectives and
rational-product objectives retain their previous bounds and receive no linear
cut. Satisfaction and enumeration queries do not use improving cuts. This seeks
one optimal witness, not every tied optimum. Failures caused by the cut count as
failed branches; cut revisions are included in constraint revisions. These counter
changes are intentional, so comparisons must not demand identical search trees.

## Protocol

Paired runs use the same worker and FlatZinc inputs, one discarded warmup and
three alternating repetitions, with a five-second external process cap. The
reference runtime is `104d903`; both runtimes use native NValue. A separate
same-source on/off ablation isolates the cut. Timing includes process startup,
preparation, search and output; compilation and independent validation are outside.
CPU diagnostics are separate from uninstrumented latency runs. Background load
and thermal conditions are uncontrolled; three-sample medians are descriptive.

Assignments returned by the paired and full comparison collectors are checked
against original FlatZinc primitives and
original MiniZinc models with Gecode. Claimed optima must match independently
validated objectives. Timeouts remain timeouts, never proofs. Changes to the
optimal witness or incumbent history are allowed when the objective agrees.

## Paired results against the previous runtime

The [record](../benchmarks/results/csp_objective_2026-09-17/results.json) and
[summary](../benchmarks/results/csp_objective_2026-09-17/summary.json) retain every
sample and exact source hashes. All completed optimization runs prove the same
objectives: Golomb 6 = 17, Golomb 7 = 25 and FT06 = 55.

| Workload | Before seconds | With cuts seconds | Before / after |
| --- | ---: | ---: | ---: |
| magic_square_4 | 0.1743 | 0.1663 | 1.05× |
| queens_50 | 0.5731 | 0.5777 | 0.99× |
| golomb_opt_6 | 0.1388 | 0.1347 | 1.03× |
| golomb_opt_7 | 0.2390 | 0.2350 | 1.02× |
| jobshop_ft06_opt | 1.0684 | 0.9749 | 1.10× |
| knapsack_20_opt | >5 | >5 | — |
| bin_packing_20_opt | >5 | >5 | — |
| all_different_incremental_16 | 0.4508 | 0.4513 | 1.00× |

FT06 keeps 615 nodes while revisions drop from 74,994 to 68,529 (8.6%). Its
52 bound-pruned nodes become failures. The separate cut audit counts 54 cut
failures and 332 ordinary failures, for 386 failures and zero bound-pruned nodes
with cuts: two branches are rejected by the cut before their former ordinary
constraint failure. This is earlier rejection
and less propagation work, not a reduced node count. Golomb reaches its supplied
valid lower bound at the first solution, so no subsequent cut is needed; small
timing differences there do not establish a benefit. The three non-optimization
controls retain their counters and solutions.

The two previously difficult optimization cases still time out at five seconds.
The earlier speculative 2–10× benefit on favorable cases was not achieved here.
A standard missing mechanism is now implemented, but its effectiveness depends
on incumbent quality, ordering and how strongly model constraints transmit the cut.

## Same-source ablation

The [on/off record](../benchmarks/results/csp_objective_ablation_2026-09-17/results.json)
and [summary](../benchmarks/results/csp_objective_ablation_2026-09-17/summary.json)
use the same current runtime for both engines; only `objective_propagation` differs.
Worker records identify whether the feature is available and enabled, independently
of the collector's `auto` setting.

| Workload | Cuts off seconds | Cuts on seconds | Off / on |
| --- | ---: | ---: | ---: |
| golomb_opt_6 | 0.1408 | 0.1369 | 1.03× |
| golomb_opt_7 | 0.2387 | 0.2346 | 1.02× |
| jobshop_ft06_opt | 1.0705 | 0.9681 | 1.11× |
| knapsack_20_opt | >5 | >5 | — |
| bin_packing_20_opt | >5 | >5 | — |

The ablation reproduces the modest FT06 gain and the unchanged timeout outcomes.

## Fresh Prune comparison

The [full record](../benchmarks/results/prune_objective_2026-09-17/results.json)
and [summary](../benchmarks/results/prune_objective_2026-09-17/summary.csv) cover
54 available inputs and 59 mode workloads at the same five-second cap.

| Engine | Completed per repetition | Optimization proofs per repetition |
| --- | --- | --- |
| Snarky | 52/59, 52/59, 52/59 | 3/5, 3/5, 3/5 |
| Prune | 59/59, 58/59, 59/59 | 5/5, 4/5, 5/5 |

Prune's only timeout is one bin-packing optimization repetition: the three samples
are approximately 4.93 s, >5 s and 4.80 s. Its unchanged pinned Rust binary proved
all workloads in the previous run. This threshold variability is retained, not
interpreted as a consequence of changing Snarky. No Snarky timeout was removed.

| Optimization | Prune process seconds | Snarky process seconds |
| --- | ---: | ---: |
| Golomb 6 | 0.0037 | 0.1263 |
| Golomb 7 | 0.0043 | 0.2153 |
| FT06 | 0.0089 | 0.9518 |
| Knapsack 20 | 0.0178 | >5 |
| Bin packing 20 | 4.9264 (2/3 complete) | >5 |

These process medians use a different worker/import path from the paired Python
experiment; do not mix them to calculate speedups. Complete Rust/Python solver
comparisons do not isolate language overhead. The 31 requested upstream cases
remain unavailable, and compiler-solved billion-range chains still do not measure
native compact-domain support.

The [parity audit](../benchmarks/results/prune_objective_2026-09-17/parity_with_alldiff.json)
confirms unchanged hashes for all 54 compiled inputs and identical normalized
solutions/objectives for all 52 mutually completed Snarky workloads. FT06 is the
only one with changed failure/revision counts; the other 51 preserve their recorded
search statistics. This is an output/work audit, not a paired latency comparison.

## Application controls and remaining bottlenecks

All six [compatibility controls](../benchmarks/results/csp_objective_controls_2026-09-17/results.json)
preserve their observations and applicable search counts. These internal medians
cover preparation and search/inference, excluding process startup.

| Control | Before seconds | After seconds |
| --- | ---: | ---: |
| Rule closure | 0.001181 | 0.001136 |
| Streamed joins | 0.108143 | 0.106487 |
| Legacy magic square 4 | 0.375521 | 0.379585 |
| Mixed magic square 3 | 0.002122 | 0.002077 |
| Markov 33×8 | 0.134382 | 0.136986 |
| Boulez | 1.569946 | 1.583095 |

Boulez still proves optimality and recovers the published sequence without a
supplied incumbent. Its rational-product objective does not use the new linear
cut; the small timing changes in these controls are not claimed as improvements.

The separate [five-second CPU profiles](../benchmarks/results/csp_objective_profiles_2026-09-17/results.json)
are instrumented diagnostics, not latency measurements or matched-work comparisons.
Packing reaches 2,184 nodes with **no incumbent**, so there is no cut to post.
Knapsack reaches 6,818 nodes and an incumbent of 110, without a proof (the
independently known optimum is 111). It finds a
first feasible value of zero after 21 nodes and improves to 110 after 685 nodes.
These observations distinguish finding good incumbents from proving optimality.
They motivate value/variable ordering and stronger problem relaxations; improving
cuts alone do not resolve either case under the measured cap.

## Cut-specific diagnostic audit

A separate [audit script](../benchmarks/results/csp_objective_2026-09-17/audit_cuts.py)
records cut revisions, failures and removals with a five-second cooperative search
cap. Its [results](../benchmarks/results/csp_objective_2026-09-17/cut_effects.json)
validate returned assignments against original FlatZinc primitives. This is a
single instrumented run per mode, with different work at the time limit; it is
not a repeated latency comparison and is distinct from the heavier CPU profiles.

| Case, cuts enabled | Cut revisions | Cut failures | Values removed directly by cuts |
| --- | ---: | ---: | ---: |
| Golomb 6 | 0 | 0 | 0 |
| Golomb 7 | 0 | 0 | 0 |
| FT06 | 54 | 54 | 0 |
| Knapsack 20 | 39,949 | 0 | 1,441 |
| Bin packing 20 | 0 | 0 | 0 |

For FT06 the benefit is early rejection: every executed cut immediately fails,
so it avoids downstream constraint work without filtering a surviving domain.
Knapsack demonstrates genuine filtering and interaction with other constraints.
In this diagnostic, cuts enabled reach the known optimal incumbent **111**,
while cuts disabled reach **110**. Neither proves optimality; both terminate on
time with a loose root upper bound of **307**. This is an observed incumbent-quality
improvement in one bounded diagnostic, not a newly completed benchmark or a
promise of repeatable five-second attainment.

Packing has no incumbent in either diagnostic and posts zero cuts. Its root
lower bound is only **1**, while the independently known optimum is **6**. Better
feasible-solution search and stronger aggregate bounds therefore remain material
next steps. No known optimum was supplied to these searches.

## Correctness coverage

One hundred deterministic signed/holey three-variable problems are exhaustively
enumerated, then solved for both directions with cuts on and off (400 searches).
Tests include huge positive/negative offsets and feasible seeds, plus explicit
constant/cancelled objectives, an infeasible portfolio, multiple improving
incumbents, rescheduling, synthetic-name collision, nested rollback, state reuse,
limits/exceptions and cost-to-sum-to-rule propagation. Existing factor/product,
mixed, optimization and application tests remain in the full regression gate.
The full workspace gate passes **1,099 tests, three skips**; see the
[validation record](../benchmarks/results/csp_objective_2026-09-17/validation.md)
for commands, logs and the scope of concurrent Alice tests.

## Reproduction

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source /path/to/104d903 --reference-ref 104d903 \
  --reference-nvalue native --only optimization/ --hard-seconds 5 \
  --warmups 1 --repeats 3 --output benchmarks/results/objective_NEW_LABEL
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.csp_followup compare \
  --reference-source . --reference-ref same-source-cut-disabled \
  --reference-nvalue native --reference-objective-propagation off \
  --candidate-objective-propagation on --only optimization/ --hard-seconds 5 \
  --warmups 1 --repeats 3 --output benchmarks/results/objective_ablation_NEW_LABEL
```
