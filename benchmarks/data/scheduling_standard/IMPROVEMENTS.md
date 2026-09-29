# Scheduling optimization comparison protocol

2026-09-29, fixed before the complete comparison. Use the same 18 instances and
original data/reference manifest as the initial assessment, all retained.

Four variants, three repetitions, fresh process per case/variant, sequential
execution, with the complete pair order reversed on alternate repetitions:

- `baseline`: hash-verified archived runtime from the first assessment, original
  model, no constructive incumbent.
- `kernels`: current runtime, original model, no constructive incumbent.
- `seeded`: current runtime and original constraint structure, input-only
  constructive incumbent, and horizon tightened to that validated schedule.
- `combined`: same as seeded, with implied end-to-makespan constraints removed
  and redundant capacity-one constraints posted on job-shop machines.

The common budget is **10 seconds of constructive generation plus search**.
Model construction and input parsing are measured separately. The constructive
portfolio uses 256 project priority trials or 2,048 job-shop conflict-set trials,
with deterministic seed indices starting at zero. All generated schedules are
independently validated. A deadline is checked between trials; at least one trial
is completed so even a very small preparation budget retains a valid witness.
The API initializes native state before starting its search timer; that overhead
is included in the solve-call and total algorithm timings. Ten seconds is a
heuristic-plus-search budget, not a strict whole-process wall-clock limit.

Settings remain native DFS, dom/wdeg, objective value ordering, automatic bounds,
objective propagation and numeric masks enabled; `PYTHONHASHSEED=0`. The public
`initial_assignment` API receives the incumbent for seeded variants. Reference
objective values are accessed for evaluation only after the worker returns.

Every emitted incumbent is validated, every timeout or process error is retained,
and every output has a fresh filename. Archive runtime and harness source hashes.
Do not blend the exploratory pilot with the complete comparison's aggregates.
Timing is evidence, never a test assertion.

## Supplemental kernel attribution

After the main comparison, run baseline, numeric-only, capacity-only,
ordering-only and all-kernel variants on `j309_1`, `j3031_1` and `la01`, with
three fresh processes and **one second** per search. These targeted diagnostics
separate the mechanisms; they do not extend the main proof-rate assessment.
The cases represent a stalled capacity model, a small objective-ordering model,
and a stalled disjunctive job shop, respectively. The runner restores archived
capacity/search functions or disables the compiled disjunction path as needed.
Keep all 45 diagnostic results in a separate archive.
