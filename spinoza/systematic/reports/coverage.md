# Couverture du modèle systématique

| Proposition | Cas exécutables | Résultat | Dépendances non-III |
|---|---:|---|---|
| E3P01 | 2 | prouvée | E1P36, E2P11C |
| E3P02 | 1 | prouvée avec faits `FAUX` explicites | E2P06, E2P07 |
| E3P03 | 2 | prouvée avec règle de compilation | E3P01 |

Couverture actuelle : 3 propositions sur 59. La prochaine tranche doit traiter
E3P04–E3P08, autour de la destruction extérieure et du conatus.

L'ordre des tranches, leurs concepts et leurs critères de sortie sont décrits
dans [`roadmap.md`](roadmap.md).

Les résultats « prouvée » signifient ici qu'une instanciation ground de chaque
branche de l'énoncé atteint ses buts. Ils ne constituent pas encore une preuve
dans un calcul quantifié complet.
