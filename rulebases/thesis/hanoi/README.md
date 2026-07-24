# Tours de Hanoï

La thèse utilise les tours de Hanoï pour montrer comment dérécursiver une
fonction dans une base de règles. Chaque appel devient un objet-problème
possédant un nombre de disques, trois tours, deux sous-problèmes et un état de
terminaison. La présente reformulation suit directement cette construction :
la connaissance récursive ne se trouve dans aucun contrôleur Python.

Le scénario demande de déplacer cinq disques de `a` vers `c` en utilisant
`b`. Le groupe `solve_hanoi` contient quatre règles :

1. `solve_one_disk` produit le mouvement terminal ;
2. `create_first_subproblem` crée le premier appel de taille `n - 1` ;
3. `continue_after_first_subproblem` attend sa terminaison, produit le
   mouvement central et crée le second appel ;
4. `finish_problem` propage la terminaison au problème père.

`FRESH` remplace la création d'un objet `HanoiPb`, `LET` calcule `n - 1`,
`NOT EXISTS` représente l'absence d'un fils et le fait `state done`
synchronise les deux appels. Un fait ajouté est immédiatement visible du
moteur : les méta-actions NéOpus `go` et `modified` n'ont donc pas besoin
d'équivalent procédural.

## Résultat

Pour cinq disques, la trace contient les 31 mouvements classiques, depuis le
premier déplacement effectué sur la configuration initiale jusqu'au dernier
déplacement qui complète la tour `c`.

```sh
uv run python -m rulebases.runner thesis/hanoi --trace
```

Changer le fait `(hanoi-root disks 5)` suffit à demander une autre taille.
La saturation crée alors explicitement l'arbre des sous-problèmes et produit
`2^n - 1` mouvements.

Les mouvements sont ordonnés par leurs dépendances et par le journal
d'exécution. La mémoire de travail demeure un ensemble de faits : elle
conserve chaque occurrence grâce à l'identifiant propre de son
sous-problème, mais ne prétend pas transformer l'ensemble final en liste
chronologique.

Le test d'intégration ne vérifie pas seulement le nombre de mouvements : il
rejoue chronologiquement la trace sur trois piles initialisées avec les cinq
disques, refuse de poser un disque sur un disque plus petit et vérifie
finalement que `c` contient `[5, 4, 3, 2, 1]`. La trace constitue donc bien un
plan exécutable complet depuis l'état initial.

## Intérêt

- récursion entièrement dérécursivée en chaînage avant ;
- création déclarative de sous-problèmes ;
- synchronisation explicite des appels séquentiels ;
- arbre de calcul, mouvements et retours inspectables dans la provenance ;
- reformulation fidèle des quatre règles du chapitre V.1.2.4 de la thèse.

La base construit le plan comme la version NéOpus, qui affichait les
mouvements ; elle ne simule pas séparément le contenu physique des trois
tours. Une telle simulation pourrait être ajoutée comme groupe de validation,
sans intervenir dans la résolution.
