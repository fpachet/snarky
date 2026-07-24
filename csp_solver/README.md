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

## Deux formulations de N-reines

`solve_n_queens(size)` conserve la formulation extensionnelle historique :
elle matérialise les couples de lignes compatibles pour chaque paire de
colonnes. Elle est utile comme oracle du CSP binaire générique, mais sa base
croît approximativement en O(n⁴).

`solve_n_queens_intensional(size)` construit seulement les candidats de chaque
reine et charge
[`n_queens_intensional.rules`](n_queens_intensional.rules). Une règle retire
un candidat quand une autre colonne n'a plus aucun support satisfaisant les
trois contraintes :

```text
row != other_row
row - column != other_row - other_column
row + column != other_row + other_column
```

La résolution reste entièrement pilotée par Snarky : `NOT EXISTS` effectue la
recherche de support, `REMOVE` filtre les domaines jusqu'au point fixe, puis
`CHOICE` et le trail explorent les valeurs restantes. Aucun solveur Python
métier n'est appelé.

Sur N=14, les deux versions trouvent la même première solution avec 20 nœuds
et 8 branches en échec :

| Formulation | Faits initiaux | Médiane |
|---|---:|---:|
| extensionnelle | 15 513 | 2,675 s |
| intensionnelle | 253 | 1,145 s |

La reformulation vaut ×2,34 (`-57,2 %`). En incluant les optimisations du
moteur depuis la baseline extensionnelle de 4,749 s, le gain total vaut
×4,15 (`-75,9 %`).

Le benchmark A/B est reproductible avec :

```sh
PYTHONPATH=.:src python benchmarks/choice_formulations.py --repeat 3
```
