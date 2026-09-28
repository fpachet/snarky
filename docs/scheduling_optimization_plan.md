# Scheduling optimization plan — 28 September 2026

## Objective

Improve proof performance on the archived 32-worker/32-job population POC,
preserving its independently verified optimum of 400. Keep the POC and its
evidence unchanged. Work in Snarky; no population-service calls are needed.

## Steps and acceptance

1. Port the archived inputs and equivalent model into a standalone benchmark.
   Profile the original monolithic model; measure first incumbent, proof time,
   nodes, bounds, propagation revisions and model construction separately.
2. Add an opt-in scheduling helper for explicitly certified interchangeable
   mandatory tasks. Validate structural prerequisites, require explicit resource
   order and private-resource mappings, and distinguish nondecreasing ordering
   from ordering under a certified at-most-one-task-per-resource assumption.
   Document that adding these constraints constructs a reduced model and changes
   enumeration and probability semantics. Do not infer groups automatically.
3. If profiling supports it, optimize workload propagation separately from the
   helper. Preserve complete predicates, shared-variable behavior, deadlines,
   rollback, and the existing sound filtering strength.
4. Test small instances against independent exhaustive/matching oracles, including
   scarce resources, emergencies, flexible shifts, identity permutations, resource
   reuse and unsafe asymmetric examples. Check untouched enumeration/inference.
5. Measure original, symmetry-only, propagation-only and combined variants in
   fresh processes, with monolithic and independently decomposed models. Use
   three interleaved repetitions and the same ten-second per-solve budget.
   Validate every incumbent; record timeouts without treating them as proofs.
6. Run relevant solver suites and repository checks. Publish source identity,
   raw results, limits and exact replacement for the POC's handwritten tables.

No matching oracle may choose solver assignments, seed incumbents, prune search
or supply bounds. The expected 400 is used only after solving for validation.
Timing is benchmark evidence, never a CI assertion. Generic decomposition and
stronger resource-allocation bounds are follow-up work unless evidence requires
them for this scope.

## Status

All six steps are complete. The [report](performance_scheduling_2026-09-28.md)
records the diagnosis, API contract, exact POC migration and 24 fresh-process
measurements. Both changes prove the monolithic optimum in a median 148 ms;
symmetry alone takes 3.397 seconds. The original and propagation-only models
retain a proof gap at ten seconds.

Validation: 1,189 tests passed, 6 skipped; lint, strict types, DSL formatting,
Markdown links, distribution contents and isolated installation passed. A fresh
reconstruction from the archived patch matched all 103 source hashes and proved
the same optimum. General allocation bounds and decomposition remain documented
follow-up work. The POC and its evidence were left unchanged.
