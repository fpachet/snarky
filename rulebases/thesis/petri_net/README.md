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

## Limite et extensions proposées

Le noyau fourni est déterministe et chaque transition possède une entrée et
une sortie. Un interpréteur général de réseaux décrits uniquement par des arcs
demanderait :

- une action ou un agrégat capable de construire la collection finie des arcs
  à mettre à jour ;
- éventuellement une sémantique de multiensemble, distincte des faits uniques.

`ConflictResolutionStrategy` fournit maintenant le point d’extension nécessaire
pour choisir entre plusieurs transitions activables ; chaque réseau doit encore
déclarer sa politique. Les actions d'une activation Snarky sont déjà atomiques,
il ne manque donc pas de transaction supplémentaire pour ce scénario.
