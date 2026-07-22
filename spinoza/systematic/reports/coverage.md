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
| E3P09 | 5 | prouvée avec scolie et contextes « en tant que » | E2P23, E3P03, E3P06–E3P08 |
| E3P10 | 2 | prouvée avec exclusion `FAUX` et contrariété | E2P09C, E2P11, E2P13, E3P05–E3P07 |
| E3P11 | 4 | quatre variations et scolie joie–tristesse prouvées | E2P07, E2P14, E3P09S |

Couverture actuelle : 11 propositions sur 59. Toutes les propositions depuis
E3P04 possèdent au moins un contre-cas de non-dérivation. E3P09 et E3P11
exécutent aussi les principaux fragments ontologiques de leurs scolies :
volonté, appétit, désir, jugement de bonté, joie, tristesse et leurs variantes
corporelles. La prochaine tranche traite E3P12–E3P18 : imagination,
association, présence et temporalité.

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

E3P09 préserve l'idée sous laquelle l'âme persévère dans le terme dérivé ; le
contexte « en tant que » n'est donc pas effacé. Son contre-test causal établit
également que `juge_bon` ne permet jamais de reconstruire `s_efforce_vers`,
`veut`, `appete` ou `desire`.

E3P11 conserve quatre relations qualitatives distinctes pour augmenter,
diminuer, seconder et réduire la puissance. Les intensités et l'exclusion
formelle de tout quatrième affect primitif restent hors du fragment actuel.
