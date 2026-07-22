# Couverture du modèle systématique

| Proposition | Cas exécutables | Résultat | Dépendances non-III |
|---|---:|---|---|
| E3P01 | 2 | prouvée | E1P36, E2P11C |
| E3P02 | 1 | prouvée avec faits `FAUX` explicites | E2P06, E2P07 |
| E3P03 | 2 | prouvée avec règle de compilation | E3P01 |
| E3P04 | 2 | prouvée avec statuts `FAUX` explicites | — |
| E3P05 | 2 | prouvée par réfutation d'une cohabitation nommée | E3P04 |
| E3P06 | 2 | prouvée avec témoin explicite du conatus | E1P25C, E1P34, E3P04, E3P05 |
| E3P07 | 2 | prouvée comme identité ontologique explicite | E1P29, E1P36, E3P06 |
| E3P08 | 2 | prouvée par réfutation du temps fini | E3P04, E3P06 |

Couverture actuelle : 8 propositions sur 59. Les cinq propositions du bloc
destruction–conatus possèdent chacune un cas positif et un contre-cas de
non-dérivation. La prochaine tranche traite E3P09–E3P11 : conscience du
conatus, appétit, désir, joie et tristesse.

L'ordre des tranches, leurs concepts et leurs critères de sortie sont décrits
dans [`roadmap.md`](roadmap.md).

Les résultats « prouvée » signifient ici qu'une instanciation ground de chaque
branche de l'énoncé atteint ses buts. Ils ne constituent pas encore une preuve
dans un calcul quantifié complet.

Pour E3P05 et E3P08, la réfutation n'est pas une négation par défaut : une
hypothèse réifiée est marquée `FAUX` seulement lorsque la proposition qu'elle
affirme a elle-même été dérivée avec le statut `FAUX`. Les règles réutilisables
publiées dans `rules/validated/` restent exclues de la preuve de leur propre
proposition.
