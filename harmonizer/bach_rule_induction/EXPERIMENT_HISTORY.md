# Historique condensé des expériences V1–V4

Ce document fige les expériences antérieures à `V5-K3-CLEAN`. Elles restent
reproductibles et ne sont pas supprimées, mais leurs règles et leurs poids ne
sont jamais chargés par la nouvelle induction clean-room.

## V1–V2.6 — récupération de règles locales connues

Les premières expériences ont construit des décisions conditionnelles note par
note et utilisé le gradient de vraisemblance pour rechercher des clauses
numériques courtes. Elles ont récupéré, sans leurs noms musicologiques pendant
la recherche :

- la classe mélodique du triton ;
- l'overlap entre voix adjacentes ;
- les classes numériques des octaves et quintes parallèles ;
- les classes numériques des octaves et quintes directes.

Les poids ont été réajustés conjointement, puis chaque groupe a été retiré et
réappris afin de mesurer son apport propre. Le partage par groupes de variantes
`251/50/51` a remplacé le partage historique qui laissait passer quelques
variantes proches entre ensembles.

## V3.1–V3.9 — première obligation tonale

La recherche a ensuite traité les préférences positives. Elle a isolé la classe
relative `11` et une résolution ascendante d'un demi-ton, puis appris des
raffinements de voix, basse et mode. Une calibration par 49 maxima nuls n'a
confirmé qu'un contexte. L'analyse des exceptions a conduit à un statut
ordinal lisible de résolution de sensible, compilé en Snarky et ouvert une fois
sur le test gelé.

## V4.1 — génération avec la base apprise historique

Sept règles récupérées ont été compilées dans une base autonome
`S-LEARNED`, séparée de `S-HISTORICAL`. Dix fragments ont été générés sans
règle humaine. Cette campagne a validé la séparation et la traçabilité, mais
les poids appris note par note avaient été projetés sur des choix de tranches
SATB complètes.

## V4.2 — première boucle après génération

Les sorties V4.1 ont motivé l'ouverture de la famille d'ordre vertical. Le
corpus authentique pénalise fortement le croisement strict, mais un contrôle
mélangé unique sélectionne la même frontière avec un effet beaucoup plus
faible. `R-LEARNED-ORDER-001` reste donc candidate et n'a pas rejoint
`S-LEARNED`.

## Ce qui est conservé, et à quel titre

| Élément | Statut à partir de V5 |
|---|---|
| Corpus, empreintes et groupes de variantes | infrastructure réutilisée |
| Algorithmes numériques génériques | bibliothèque méthodologique consultable |
| Règles et poids V1–V4 | benchmark externe seulement |
| Noms des règles historiques | masqués pendant l'induction |
| Résultats et rapports | archive scientifique, non supprimée |
| Ancien test de 51 chorals | fermé à toute adaptation V5 |

La question de V5 est volontairement plus forte : une induction vide, limitée
à un noyau local unique, récupère-t-elle les résultats antérieurs puis les
dépasse-t-elle ?
