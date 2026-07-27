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

## Conjunctions in CLAIRE4's built-in event rules

The built-in rule path visible in CLAIRE4 commit `25b1496` is a procedural
event-demon compiler, not a general RETE-style join network. In
`meta/define.cl`, `make_filter` requires the first conjunct to identify an
event such as a property write or a table update. `self_eval(Defrule)` attaches
the resulting demon to that relation, and `eval_if_write` invokes it when the
relation changes.

`make_demon` binds the object and new value supplied by that event, then
compiles the remaining conjuncts into an ordinary Boolean test in the demon's
lambda. Consequently, a rule such as `N1(x) := y & y > 0` does not search a
Cartesian product: the update provides `x` and `y`, and only `y > 0` remains
to be checked. When a rule needs to enumerate other objects, the CLAIRE source
does so explicitly with `exists`, `for`, or a set comprehension, as in
`test/rules/dinner.cl`; that enumeration carries the combinatorial cost.

CLAIRE4 also exposes `eval_rule` as a hook for rules with typed rule
arguments, described in the source as the ClaireRules engine. That engine is
not implemented in this checkout, so the repository alone does not establish
whether that separate path keeps partial joins or uses another production-rule
algorithm. The Talarian comparison in this project deliberately exercises the
built-in event-demon path.

## Factorized conjunctions in current Snarky

Snarky now has a conservative multi-premise event path for a related but
different execution model. When an addition reaches a positive rule whose
comparisons were already bound at their textual positions, the added fact is
used as a join anchor. Fixed relation fields reject irrelevant anchor
positions, and the remaining fact premises are retrieved from exact indexes.
The runtime neither scans all hubs nor materializes every left/right prefix.

For example, the shared triangle rule prepares `hub → left` and
`hub → right` facts, then streams `left → right` edges. Each edge supplies
both endpoint variables; two indexed lookups find the common hub. The
executable Snarky version is
[`rulebases/small/triangle_closure`](../rulebases/small/triangle_closure/README.md),
and the common-language runner is
[`benchmarks/claire_triangle_closure.py`](../benchmarks/claire_triangle_closure.py).

This specialization is deliberately narrower than a general RETE network.
It excludes focused conflict-resolution rules, comparisons that were
textually unbound, negative or aggregate queries, bindings, combinations, and
removal deltas. Those cases preserve the existing semi-naive, partial-memory,
or complete-evaluation behavior.

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
