# Analyse du POC V3.8 — test final gelé

## Gel antérieur

Le modèle `graded_exact`, les hyperparamètres et les critères ont été publiés
dans le commit `b635d6a` avant toute lecture des 51 chorals de test. Le script
vérifie les empreintes de l'implémentation et des résultats V3.7 avant de
charger ce split.

Les trois critères préenregistrés étaient :

1. NLL test inférieure à la baseline ;
2. borne bootstrap à 2,5 % du gain strictement positive ;
3. au moins 90 % du gain du modèle à deux poids.

## Résultat

| Modèle | Paramètres appris | NLL test | Gain contre baseline |
|---|---:|---:|---:|
| baseline | 0 | 1,234034 | — |
| proxy + exact | 2 | 1,229618 | 0,004415 |
| `graded_exact` | 1 | **1,229620** | **0,004414** |

La feature graduée reçoit un poids de `2,0215`. Elle conserve `99,964 %` du
gain obtenu avec deux poids libres.

Sur 10 000 bootstraps des 51 chorals de test :

```text
gain médian     0,004180
intervalle 95 % [0,001248 ; 0,008493]
P(gain > 0)    0,9995
```

Les trois critères sont satisfaits. Aucun ajustement n'a été effectué après
lecture.

## Support musical

Le test contient :

- 12 opportunités du proxy dans 8 pièces, résolues 10 fois ;
- 9 opportunités `vii°6→I6` dans 6 pièces, toutes résolues ;
- 11 contextes du noyau fonctionnel dominant→tonique, résolus 10 fois.

La confirmation porte donc sur un effet local rare, mais reproduit dans des
pièces entièrement tenues à part.

## Conclusion

La connaissance extraite peut être représentée par un statut local fini et
lisible :

```text
0 : aucune préférence particulière
1 : résolution ascendante attendue dans le contexte local appris
2 : même résolution, renforcée lorsque la candidate forme vii°6→I6
```

Ce statut est plus compact que deux clauses pondérées indépendamment et
conserve pratiquement tout leur pouvoir prédictif sur données inédites.
