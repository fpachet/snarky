# Factorielle explicite

Cette base traduit directement la définition récursive
`n! = n × (n - 1)!`. Chaque appel est un nœud explicite, ce qui rend visibles
la descente récursive et la remontée des résultats.

Le scénario calcule `6! = 720`.

## Intérêt

La factorielle est plus simple que Fibonacci : elle isole la récursion
linéaire, `LET` et la dépendance entre un appel et son unique fils. Elle sert de
tutoriel avant l'arbre binaire de Fibonacci et de contrôle lorsqu'une
optimisation de ce dernier semble dépendre de sa largeur.

```sh
uv run python -m rulebases.runner small/factorial_explicit
```

La base est entièrement supportée et ne demande aucune extension.
