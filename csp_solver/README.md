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

1. produisent une décision avec `CHOICE ... FROM` ;
2. appliquent cette décision en retirant les autres candidats ;
3. propagent les relations binaires par `NOT EXISTS` et `REMOVE` ;
4. reconnaissent les domaines singletons ;
5. dérivent `solved` ou `contradiction`.

La règle de décision est entièrement déclarative :

```text
RULE choose_csp_value
WHEN
    ($problem kind csp_problem)
    ($problem variable $variable)
    NOT EXISTS ($variable value $assigned)
THEN
    CHOICE ($variable decision $chosen) WEIGHT $weight
    FROM
        ($variable candidate $chosen)
        ($variable choice_weight SEQ[$chosen $weight])
    END_CHOICE
END
```

`SessionChoiceSearch` choisit l'un des points produits par MRV, pose un
checkpoint, affirme le fait cible, sature les groupes puis restaure le
checkpoint en cas de contradiction ou avant le choix frère. La session de
l'appelant reste isolée par un unique fork racine.

Le constructeur accepte maintenant une taille `n`; l'oracle principal reste
le problème des quatre reines, qui possède exactement deux solutions :

```sh
PYTHONPATH=src python -m csp_solver.four_queens
```

Le pilote Python ne construit plus les `ChoicePoint` métier : il ne fait que
piloter les règles génériques. Sur la baseline courante, le problème explore
quatre nœuds, rencontre une branche contradictoire et produit exactement les
deux solutions.

Le paramètre `reversible_depth_first=False` réactive le DFS à forks paresseux
pour les tests différentiels et les benchmarks. Le trail est le défaut.
