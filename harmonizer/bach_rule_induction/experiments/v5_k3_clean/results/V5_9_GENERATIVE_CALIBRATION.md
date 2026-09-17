# V5.9 — calibration générative par contraste de moments

Le socle V5.7 est gelé. Un petit budget de statuts chromatiques reçoit
des poids supplémentaires par le gradient :

`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.

Calibration sur `16` chorals
du train choisis par hash, sans consulter validation pour les poids.
Le test scellé n'est pas chargé.

## Règles génératives retenues

| # | Règle lisible | Bach initial | Gibbs initial | Gradient initial | Poids final |
|---:|---|---:|---:|---:|---:|
| 1 | classe rare, Bass, majeur, classes [1, 3, 8, 10] | 1.560 % | 6.013 % | -4.454 pp | -0.466094 |
| 2 | classe rare approchée par pas, Bass, majeur, classes [1, 3, 8, 10] | 1.143 % | 4.728 % | -3.584 pp | -0.464252 |
| 3 | classe rare, Alto, majeur, classes [1, 3, 8, 10] | 1.046 % | 3.325 % | -2.279 pp | -0.442545 |
| 4 | classe rare sur temps faible, Bass, majeur, classes [1, 3, 8, 10] | 1.318 % | 4.651 % | -3.333 pp | -0.459304 |
| 5 | classe rare immédiatement résolue par pas, Bass, majeur, classes [1, 3, 8, 10] | 1.097 % | 3.891 % | -2.794 pp | -0.457807 |
| 6 | classe rare, Bass, mineur, classes [4, 6] | 1.796 % | 4.229 % | -2.433 pp | -0.466357 |
| 7 | classe rare approchée par pas, Alto, majeur, classes [1, 3, 8, 10] | 0.998 % | 3.082 % | -2.084 pp | -0.443125 |
| 8 | classe rare immédiatement résolue par pas, Alto, majeur, classes [1, 3, 8, 10] | 0.928 % | 2.741 % | -1.813 pp | -0.386257 |

## Critères après gel

- NLL conditionnelle V5.7 : `1.120257`.
- NLL conditionnelle V5.9 : `1.130530`.
- Distance moyenne absolue des moments sélectionnés : `0.028467` → `0.016242` sur le sous-ensemble train.

La promotion générative dépend d'une campagne séparée sur validation
avec exactement les mêmes pièces, graines et balayages que V5.7.
