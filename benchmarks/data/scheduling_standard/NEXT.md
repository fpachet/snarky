# Local improvement and order-search comparison

Same fixed 18 cases and pinned input/reference data as the earlier assessments.
Main variants are `previous` (archived bda7b5e runtime, previous seeded method),
`local` (same general finite solver with local improvement), and `order` (local
improvement followed by the explicit scheduling order solver). Three fresh
processes per case/variant; reverse the complete pair order on alternate repeats.

Ten seconds for constructive generation, local improvement and search together.
Model construction is measured separately and included in algorithm totals.
The previous API also excludes native-state initialization from its search clock;
solve-call totals retain that overhead. The order solver starts its clock before
validation and setup. Whole-process times also include Python startup/imports.

Constructive portfolio: 256 project trials or 2,048 job-shop trials as before.
Local improvement: at most 5,000 iterations and two seconds, seed 3292026. Stop
when an elementary input-derived bound is met. No reference objective enters
scheduling, stopping criteria, warm starts, propagation or proofs.

The `order` portfolio first gives projects up to 2.5 search seconds in the
original finite model. It then gives order search with first-conflict selection
up to two seconds (at most half the remaining search budget), followed by
critical-conflict selection for the rest. Jobs omit the initial finite phase.
Every phase passes its improved incumbent to the next; a proof ends the run.
Phase times, budgets, bounds and nodes are all retained. Limits are selected
by problem family, never by instance name or known objective.

The order solver uses resource subset bounds, forced pair orders,
incumbent-guided branch ordering and a bounded transitive-closure memo.
Energy-window and not-first/not-last filtering remain separate opt-in variants.
The general finite solver and existing public solve API are unchanged.

Supplemental variants: `conflicts` adds derived incompatible pairs to the finite
model; `shared` gives a compact finite model at most two search seconds and passes
its best incumbent to order search with the remaining budget. `first`, `critical`, `energy`
and `not_first_last` isolate branching and propagation choices. Keep diagnostics
separate from main aggregates and retain every timeout, exception and witness.
Validate saved schedules against the original instance definitions, including
all heuristic improvement history. Snapshot source hashes and measured files.
