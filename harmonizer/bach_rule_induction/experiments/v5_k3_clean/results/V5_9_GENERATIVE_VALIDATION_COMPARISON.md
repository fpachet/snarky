# V5.9 — validation du gradient génératif

Même ensemble de 20 chorals de validation, mêmes deux graines, même
soprano, même rythme et six balayages. Les poids V5.9 ont été calibrés
exclusivement sur 16 chorals du train. Le test scellé reste fermé.

Ici, « Bach » désigne les attaques authentiques d'alto, ténor et basse
dans ces mêmes 20 chorals. Une classe rare est définie voix par voix et
mode par mode sur le train ; elle n'est pas synonyme d'altération écrite.

| Modèle | NLL validation | Classes rares générées | Écart à Bach | IC95 | MAE par pièce |
|---|---:|---:|---:|---:|---:|
| V5.7 | 1.120257 | 5.925 % | +1.728 pp | [-0.517, +3.974] | 4.401 pp |
| V5.8 | 1.060328 | 8.029 % | +3.654 pp | [+1.466, +5.841] | 5.582 pp |
| V5.9 | 1.130530 | 4.529 % | +0.151 pp | [-1.750, +2.052] | 3.107 pp |

Référence Bach pondérée : `4.828 %`.

V5.9 améliore l'erreur absolue sur
`14/20` chorals. La MAE
baisse de `4,401` à `3,107` points. Le taux global devient très proche
de Bach, sans dégradation conditionnelle majeure (`+0,0103` NLL).

## Retour sur BWV 108.6

| Mesure | Bach | V5.7 | V5.9 |
|---|---:|---:|---:|
| Classes tonales rares | 0.68 % | 3.42 % | 3.42 % |
| Répétitions de basse | 0 | 7 | 7 |
| Blocs triadiques | 45.92 % | 47.96 % | 48.98 % |
| Blocs structurels | 52.04 % | 62.24 % | 62.24 % |

La calibration globale ne modifie pas le taux rare de cet échantillon
mineur particulier, mais conserve la correction des répétitions de
basse et les proportions triadiques. Les pièces fortement chromatiques
restent sous-modélisées : V5.9 corrige la surproduction moyenne, mais
n'apprend pas encore les licences positives de tonicisation locale.

## Décision

**V5.9 remplace V5.7 comme modèle chromatiquement calibré expérimental.**
La prochaine extension devra apprendre un statut tonal local et des
licences positives, sans rouvrir le test scellé.
