# LORE, LAURE, CLAIRE, and Snarky

Snarky's combination of rules, constraints, choices, and reversible search has
an important direct precedent in Yves Caseau's work. The project should not
present that general combination as new.

## Historical lineage

**LORE** was Caseau's earlier object-oriented knowledge-representation
language. It supplied an object model in which later rule and constraint work
could be expressed.

**LAURE** combined finite-domain constraints, deductive or production rules,
methods, and depth-first search over the same objects. Rules could guide
constraint resolution and react when the solver introduced a hypothesis.
LAURE's open backtracking architecture allowed other components to participate
in search; extended rollback removed not only a failed hypothesis but also
consequences computed by rules and methods.

The closest primary descriptions are:

- Yves Caseau, [*Rule-aided constraint resolution in
  Laure*](https://doi.org/10.1007/BFb0013534), PDK 1991.
- Yves Caseau, [*Constraint satisfaction with an object-oriented knowledge
  representation language*](https://doi.org/10.1007/BF00872107), *Applied
  Intelligence* 4(2), 1994.
- Yves Caseau and Peter Koppstein, [*A Cooperative-Architecture Expert System
  for Solving Large Time/Travel Assignment
  Problems*](https://doi.org/10.1007/978-3-7091-7557-6_34), DEXA 1992.

**CLAIRE** continued this direction with a language integrating sets, rules,
and search. Its inference compiler translated logical rules into efficient
procedural attachments:

- Yves Caseau, François-Xavier Josset, and François Laburthe,
  [*CLAIRE: combining sets, search and rules to better express
  algorithms*](https://doi.org/10.1017/S1471068401001363), *Theory and
  Practice of Logic Programming* 2(6), 2002.

The names are easy to conflate: the useful sequence here is **LORE → LAURE →
CLAIRE**, not “CLAURE.”

## Operational comparison

| Snarky case-1 concept | LAURE precedent |
|---|---|
| Persistent constraint closure | Finite-domain constraint resolution |
| Forward rules inspect restricted state | Rules cooperate with constraints on the same objects |
| Explicit `CHOICE` | Solver hypothesis |
| Propagation after a choice | Rules and constraints react to the hypothesis |
| Session checkpoint and rollback | Open/extended backtracking |
| Rule-derived facts restored with the branch | Consequences of rules and methods removed on backtracking |
| Sequential `RuleStep` fixed points | Laurière's *étapes* of rule/constraint execution |

The comparison is architectural rather than an assertion that the two
languages have identical syntax or domain semantics.

Snarky's steps are deliberately search-reversible. Completing a harmonic-plan
step does not commit its choices: a contradiction during SATB realization can
return to an earlier harmonic choice. This preserves the single search tree
and avoids the incompleteness of solving each phase independently.

## Snarky's current formulation

The present narrowing-only layer makes several distinctions explicit:

- root candidate facts define base domains;
- persistent constraints compute filtered domains;
- rules observe those filtered facts and may derive facts or further
  restrictions;
- only `CHOICE` branches;
- the complete inference session, including provenance and rule refraction, is
  reversible.

Potential contributions therefore lie in the explicit semantics, integration
with immutable fact/provenance machinery, reusable fact-derived constraint
templates, and empirical hybrid examples—not in claiming invention of the
rules-plus-constraints architecture.

Rules that add new candidate values belong to a second, widening semantics.
That extension would require dependency tracking or recomputation and should
be compared separately with dynamic CSPs, truth-maintenance systems, and
reactive constraint languages.
