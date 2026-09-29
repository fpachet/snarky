# Supplemental scheduling order diagnostics

These are targeted follow-ups to the main 18-case, three-repeat comparison;
they are not included in its proof counts or timing aggregates.

1. `first`, `critical`, `energy`, `not_first_last` on LA02, LA03 and LA04:
   one fresh process each, six seconds including heuristics and search.
2. `conflicts`, `shared` on j309_1 and j3014_1: one fresh process each, ten seconds
   including heuristics and search. Compare with all retained main samples,
   without treating one sample as a stable timing estimate.
3. `order` on j309_1 and j3014_1: one fresh process each with a 60-second budget,
   keeping the same two-second local cap and fixed initial search phases.
4. `order` on LA02, LA03 and LA04 at six seconds, one process each, as a budget
   control for the search diagnostics. Retain this in a separate control archive.

Retain timeouts and exceptions, replay every witness and verify unchanged
measured sources. Every schedule must be generated from original instance input;
never feed a published optimum into a search cutoff or heuristic stopping rule.
