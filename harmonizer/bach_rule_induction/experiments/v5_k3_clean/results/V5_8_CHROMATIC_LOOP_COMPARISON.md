# V5.8 — boucle chromatique et critère de rejet

## Question

L'excès visuel de notes chromatiques dans BWV 108.6 vient-il d'une
préférence conditionnelle erronée, d'une lacune de représentation locale
ou de la dynamique de génération Gibbs ?

## 1. Choix locaux authentiques

Sur les 50 chorals de validation, V5.7 prévoit moins de classes rares
que Bach :

- Bach observé : `3.780 %` ;
- V5.7 attendu : `2.364 %` ;
- z du résidu : `+11.41`.

Une interdiction chromatique globale est donc exclue. Parmi les choix
rares authentiques, 82 % sont approchés par pas, 56 % ont une résolution
immédiate par pas, 21 % sont des broderies et 25 % des passages.

## 2. Génération multi-chorals

Même soprano, même rythme, 20 chorals de validation, deux graines et six
balayages. Les taux portent sur alto, ténor et basse.

| Modèle | NLL validation | Classes rares générées | Écart apparié à Bach | IC95 |
|---|---:|---:|---:|---:|
| V5.7 | 1.120257 | 5.925 % | +1.728 pp | [-0.517, +3.974] |
| V5.8 | 1.060328 | 8.029 % | +3.654 pp | [+1.466, +5.841] |

Référence Bach pondérée : `4.828 %`.

V5.8 reconstruit d'abord exactement les vingt règles de V5.7, puis ajoute
huit régularités générales. Aucune des 72 interactions chromatiques
candidates n'est sélectionnée. La NLL s'améliore, mais les générations
deviennent significativement trop chromatiques.

## Décision

**V5.8 est rejeté comme successeur génératif de V5.7.** Il reste conservé
comme résultat négatif : la pseudo-vraisemblance conditionnelle seule ne
suffit pas à choisir une base de règles destinée à un Gibbs libre.

## V5.9 proposé : gradient génératif

Pour chaque règle lisible `r`, ajouter au gradient conditionnel un contraste
de moments :

`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.

Une feature trop fréquente dans les générations reçoit ainsi un gradient
négatif, même si elle améliore la prédiction locale. Les statuts de licence
(approche conjointe, passage, broderie, résolution, métrique) peuvent
recevoir simultanément des poids positifs. Le test scellé restera fermé
pendant ce calibrage.
