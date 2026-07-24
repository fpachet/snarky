# Solveur CSP déclaratif

Ce projet teste le mécanisme générique de `choice` et de backtracking sans
appeler `BacktrackingConstraintSolver`.

Un problème est représenté par des faits Snarky :

```text
(problem variable x)
(x candidate red)
(constraint kind binary_constraint)
(relation allows SEQ[red blue])
```

Les groupes de règles :

1. appliquent une décision en retirant les autres candidats ;
2. propagent les relations binaires par `NOT EXISTS` et `REMOVE` ;
3. reconnaissent les domaines singletons ;
4. dérivent `solved` ou `contradiction`.

`SessionChoiceSearch` choisit un domaine par MRV, crée une branche isolée,
assert une décision, sature les groupes puis abandonne la branche en cas de
contradiction.

Le premier oracle est le problème des quatre reines. Il possède exactement
deux solutions et s'exécute avec :

```sh
PYTHONPATH=src python -m csp_solver.four_queens
```

Le pilote Python est générique : les relations et la propagation restent
déclaratives. Sur la baseline courante, le problème explore quatre nœuds,
rencontre une branche contradictoire et produit exactement les deux solutions.
