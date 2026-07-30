# V25 — licences de sonorité aux temps faibles

## Question

V24 réduit les sonorités fortes étranges, mais laisse les temps faibles
pratiquement inchangés. V25 demande si une partition locale et lisible des
sonorités faibles suffit à distinguer les ornements légitimes des fausses
notes.

## Vocabulaire gelé

Chaque bloc faible qui n'a pas une analyse d'accord nommé unique reçoit
exactement un des neuf statuts suivants :

1. accord nommé ambigu ;
2. triade consonante incomplète ;
3. triade plus une note, avec analyse ambiguë ;
4. triade plus note de passage ;
5. triade plus broderie ;
6. triade plus suspension ;
7. triade plus appoggiature ;
8. triade plus note étrangère non licenciée ;
9. autre sonorité non licenciée.

La préparation et la résolution sont calculées dans la fenêtre K3
`précédent–courant–suivant`, avec la sémantique `ATTACK/HOLD`. Les catégories
sont mutuellement exclusives. Leur définition est humaine ; leurs poids sont
appris.

Sur 32 chorals de structure, le corpus contient 2 219 blocs faibles :
1 667 accords nommés uniques et 552 cas résiduels. Les neuf catégories sont
testables par contrefactuels locaux. Bach ne produit aucun cas strict de
broderie ou d'appoggiature sous cette définition étroite ; cela interdit d'en
faire des contraintes universelles.

## Ajustement conditionnel

L'ajustement par pseudo-vraisemblance apporte un gain moyen faible :
`+0,000518` NLL au meilleur niveau de régularisation, avec un intervalle à
95 % de `−0,000180` à `+0,001233`. Le groupe n'est donc pas retenu comme
amélioration conditionnelle stable de V24.

## Ajustement génératif

Les 65 poids V24 sont gelés. Seuls les neuf nouveaux poids sont ajustés par
les moments `Bach − générateur`, sans consulter la validation. La MAE des neuf
moments passe de `0,01137` à un minimum de `0,00726` à l'itération 6. Ce point
d'arrêt, choisi sur l'apprentissage uniquement, est exporté ; les itérations
ultérieures remontent jusqu'à `0,00931`.

## Validation

L'audit réservé porte sur dix chorals de validation, cinq graines et six
balayages, avec la même initialisation pour V24 et V25.

| Mesure | Bach | V24 | V25 |
|---|---:|---:|---:|
| Dissonances par bloc faible | 1,032 | 1,080 | 1,051 |
| Dissonances par bloc fort | 0,357 | 0,510 | 0,552 |
| Blocs forts non triadiques | 26,91 % | 30,49 % | 31,91 % |
| Basse hors gamme naturelle | 7,14 % | 12,25 % | 11,69 % |

V25 rapproche donc les temps faibles de Bach, mais dégrade les temps forts.
L'écart des dissonances fortes devient positif avec un intervalle à 95 %
`[+0,010 ; +0,381]`.

L'audit détaillé des statuts faibles montre que V25 réduit surtout
`other_unlicensed` de `19,30 %` à `17,98 %` (Bach : `14,35 %`). En revanche,
les suspensions restent trop rares : `0,76 %` contre `2,60 %` chez Bach.
Pénaliser le résidu ne suffit donc pas à apprendre la conduite correcte.

## Interprétation

Le facteur V25 ne déclenche aucune autre règle. Cependant, une préférence
appliquée à un choix faible change la configuration musicale échantillonnée,
donc les choix disponibles et les activations au bloc fort voisin. Cet effet
est une dépendance réelle de la distribution conjointe, pas un effet de bord
impératif.

La lacune est désormais précise : V25 décrit le rôle du bloc faible et V24
la sonorité forte, mais aucun groupe n'apprend leur relation conjointe.

## Décision

V25 est **rejeté comme successeur génératif de V24**. Il n'est ni compilé dans
la base Snarky retenue ni utilisé pour produire un exemple de référence. Son
vocabulaire, son ajustement et ses audits sont conservés comme résultat
négatif reproductible.

La prochaine expérience V26 doit utiliser une seule partition K3 conjointe :

`rôle de la sonorité faible × qualité de la résolution forte`.

Elle séparera notamment :

- passage ou suspension avec résolution forte acceptable ;
- passage ou suspension sans résolution forte acceptable ;
- sonorité faible non licenciée avec ou sans résolution forte acceptable.

Ces états resteront locaux, exhaustifs et mutuellement exclusifs. Le groupe
sera appris conjointement et ne sera retenu que s'il améliore les temps
faibles sans dégrader les temps forts sur validation. L'étude structurée de
la basse restera un groupe séparé.

## Artefacts

- [Couverture](V25_WEAK_SONORITY_COVERAGE.md)
- [Ajustement conditionnel](V25_WEAK_SONORITY_CONDITIONAL_FIT.md)
- [Résidu initial V24](V25_WEAK_SONORITY_MOMENT_AUDIT.md)
- [Ajustement génératif](V25_CONTRASTIVE_MOMENT_FIT.md)
- [Validation V24–V25](V25_CHECKPOINT6_V24_GENERATION_VALIDATION10X5_SWEEP6.md)
- [Statuts faibles V24](V25_WEAK_STATUS_VALIDATION_V24.md)
- [Statuts faibles V25](V25_WEAK_STATUS_VALIDATION_V25.md)
