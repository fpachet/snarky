# V26 — décision faible × qualité de résolution

## Question

V25 décrivait séparément le rôle d'une sonorité faible et V24 la qualité des
sonorités fortes. V26 teste une seule partition locale :

`rôle faible résiduel × acceptabilité de la sonorité suivante`.

La résolution est dite acceptable si son ensemble de classes de hauteurs
possède au moins une analyse d'accord nommée ou s'il est inclus dans une
triade majeure ou mineure. Cette définition et les 18 cellules ont été gelées
avant l'apprentissage. L'exemple généré de BWV 108.6 n'est jamais chargé pour
estimer ou choisir les poids.

## Couverture

Sur les 32 chorals de structure, les 18 cellules franchissent les seuils
préétablis de 100 alternatives testables et cinq chorals. La partition couvre
exactement les 552 blocs faibles résiduels de Bach.

## Apprentissage conditionnel

Les 18 poids sont appris conjointement avec réajustement du socle V24.
Le groupe régularisé `λ=0,6` est retenu :

- gain moyen de NLL par choral : `+0,000203` ;
- intervalle bootstrap 95 % : `[+0,000072 ; +0,000337]` ;
- chorals de validation améliorés : `8/10`.

Les variantes moins régularisées obtiennent parfois une meilleure moyenne,
mais des intervalles instables. Elles ne sont pas retenues.

## Génération Snarky appariée

Le modèle de 83 facteurs est compilé puis utilisé pour la même génération
complète à soprano et rythme imposés. Il modifie 76 des 98 blocs.

| Mesure | Bach | V23 | V26 |
|---|---:|---:|---:|
| Blocs triadiques | 56,12 % | 30,61 % | 39,80 % |
| Blocs forts non triadiques | 26,92 % | 61,54 % | 53,85 % |
| Dissonances par bloc fort | 0,462 | 1,038 | 0,885 |
| Dissonances par bloc faible | 0,875 | 1,111 | 0,861 |
| Faibles résiduels vers résolution inacceptable | 4,55 % | 28,13 % | 4,55 % |
| Mouvements chromatiques de basse | 29,35 % | 83,70 % | 81,52 % |

## Décision

V26 est retenu comme amélioration conditionnelle compacte et comme preuve que
la relation faible–résolution manquait réellement. Il corrige fortement sa
cible, mais les accords forts restent trop souvent non triadiques et la basse
reste presque entièrement chromatique.

La prochaine induction ne doit pas ajouter une nouvelle licence faible. Elle
doit apprendre, séparément :

1. un critère de séquence pour la proportion de sonorités fortes acceptables ;
2. un groupe de trajectoire de basse fondé sur le rôle
   `note d'accord / passage / broderie / appoggiature / chromatisme résolu`.

Ces critères devront être calibrés sur Bach avant une nouvelle génération et
pourront déclencher contradiction et backtracking dans Snarky.

## Artefacts

- [Couverture](V26_JOINT_WEAK_RESOLUTION_COVERAGE.md)
- [Modèle conditionnel](V26_JOINT_WEAK_RESOLUTION_MODEL.md)
- [Audit de génération](V26_SNARKY_GENERATION_AUDIT.md)
- [Génération complète](TWO_LOOP_FULL_GENERATION_V26.md)
