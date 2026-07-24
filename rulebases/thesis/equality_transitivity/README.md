# Transitivité de l'égalité

La thèse utilise cette base très courte pour mesurer le coût du filtrage et de
la réfraction : deux égalités valides `A = B` et `B = C` rendent valide une
égalité `A = C` déjà présente mais marquée fausse.

Cette reformulation conserve une identité pour chaque objet égalité. C'est
indispensable pour reproduire plusieurs occurrences logiquement identiques,
car la mémoire de Snarky possède une sémantique d'ensemble pour les faits.

## Intérêt

- micro-benchmark historique comparable à NéOpus ;
- jointure de neuf prémisses avec plusieurs variables partagées ;
- mutation `false` vers `true` ;
- test de la réfraction lorsque plusieurs témoins produisent le même résultat.

Ce cas ne met pas en œuvre la sémantique complète de `owl:sameAs`. Il propage
seulement la validité d'objets explicitement fournis.

```sh
uv run python -m rulebases.runner thesis/equality_transitivity
```

Le noyau est entièrement supporté par Snarky et ne demande aucune extension.
