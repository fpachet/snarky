# Tours de Hanoï

La thèse utilise les tours de Hanoï pour illustrer la traduction d'appels
récursifs séquentiels en règles. Le noyau fourni exécute correctement
l'instance bornée à deux disques :

1. petit disque de `a` vers `b` ;
2. grand disque de `a` vers `c` ;
3. petit disque de `b` vers `c`.

Les phases sont explicites afin que les règles ne puissent pas réordonner les
mouvements.

## Intérêt

- contrôle séquentiel entre activations ;
- mutations d'un état structuré ;
- exemple révélant précisément ce que `RuleGroup` ne sait pas encore exprimer.

```sh
uv run python -m rulebases.runner thesis/hanoi
```

## Extensions proposées

Les mouvements possèdent désormais des identifiants créés par `FRESH`. Une
version réellement récursive demanderait encore des groupes paramétrés,
capables d'appeler un groupe avec `n - 1`, ou une pile de tâches explicite et
des continuations.
