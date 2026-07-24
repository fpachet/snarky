# Réseau de Petri borné

Le scénario représente un réseau séquentiel à trois places :

```text
source --load--> buffer --finish--> done
```

Un jeton quitte `source`, traverse `buffer`, puis arrive dans `done`. Chaque
franchissement modifie atomiquement deux compteurs et l'état de contrôle.

## Intérêt

- plusieurs `REMOVE` et `ADD` dans une même activation ;
- calcul des nouveaux marquages avec `LET` ;
- reprise du matching après suppressions ;
- journal d'événements permettant de rejouer les franchissements.

```sh
uv run python -m rulebases.runner thesis/petri_net
```

## Limite restante

`COLLECT`, `COMBINATIONS` et `FOR EACH` permettent maintenant de construire la
collection finie des arcs d'une transition et d'appliquer des actions à chacun.
Le noyau fourni reste volontairement déterministe et explicite.

Un interpréteur général doit encore choisir une sémantique de multiensemble
pour plusieurs jetons identiques. Cette notion ne se confond pas avec
`FiniteSet` ni avec les faits uniques de la mémoire.

`ConflictResolutionStrategy` fournit maintenant le point d’extension nécessaire
pour choisir entre plusieurs transitions activables ; chaque réseau doit encore
déclarer sa politique. Les actions d'une activation Snarky sont déjà atomiques,
il ne manque donc pas de transaction supplémentaire pour ce scénario.
