# Interchangeable scheduling fixture

`inputs.json` contains the complete synthetic worker/job inputs from the local
population POC's `results/larger_scheduling_checks/original.json`, with that
record's path and SHA-256 hash. No population service or credentials are needed.
The POC evidence is retained unchanged in its original repository.

The benchmark reproduces its hard model: skill eligibility, availability,
pairwise non-overlap, a two-hour workload limit per worker, and one private
emergency alternative per two-hour job at cost 100. Labels have no operational
effect. Eight jobs and workers belong to each of four independent skill groups.

The independent oracle is maximum bipartite matching for this restricted
one-job-per-worker model. It verifies completed solves and is never used for
branching, bounds, incumbents or pruning. The expected optimum of 400 comes
from two C-early and two D-late shortages.
