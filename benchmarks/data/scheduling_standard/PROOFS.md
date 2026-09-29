# Conflict cliques and start-domain shaving

Follow-up to NEXT.md, retaining the same fixed 18 inputs and ten-second budget.
The previous variant reconstructs the hash-checked 80abc15 runtime from the NEXT
source archive and runs its unchanged order portfolio. The candidate uses the
same constructive/local preparation and no published objectives during solving.

For projects the candidate first gives integer-domain search one second. Its
root probes both halves and endpoints of start domains, removing only ranges
that fail precedence/timetable propagation. It then gives the original finite
model up to 2.5 seconds and spends the remainder in critical-conflict order search
with redundant unary resources for maximal incompatibility cliques. Enumeration
is deterministic and capped at 128 added groups / 10,000 enumeration nodes.
Job shops retain the previous first-conflict / critical-conflict portfolio.

Main comparison: previous and proofs, all 18 cases, three sequential fresh
processes per pair, reverse ordering on alternate repetitions, PYTHONHASHSEED=0.
Ten seconds covers heuristic preparation and solver calls. Construction is
measured separately and included in algorithm totals. Inputs and every incumbent
are independently validated. Reference objectives are consulted only afterward.
Source hashes must remain unchanged for a measurement archive to be accepted.

Targeted ablations: j309_1 and j3014_1, three repetitions, ten seconds, variants
cliques (no window phase), shaving (no derived cliques), unshaved (window search
without root probes). These diagnose the contributions of the two additions.
Shaving probes and DFS nodes are counted separately; a root proof can have zero
DFS nodes and hundreds of propagation probes. Timeout bounds remain root bounds.

Exploratory trials also considered full energetic domain filtering, alternate
start-domain branching, timetable filtering inside order search, and disjoint
branching using temporal difference constraints. Those trials guided development;
only the declared fresh-process comparisons above provide final timing evidence.
The unsuccessful prototypes do not change the production order-search default.
