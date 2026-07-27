# V5.2 — audit de la première règle K3

## Question

Le seuil `> 2` représente-t-il une frontière musicale, ou seulement une
approximation compacte d'une préférence graduée pour les petits pas ?

Cette règle est souple : elle modifie les odds, mais n'interdit aucun
candidat. Les choix authentiques qui l'activent restent conservés.

## Scan des seuils sur le train

| Seuil | Taux Bach | Taux attendu | z | gain NLL approximatif |
|---:|---:|---:|---:|---:|
| > 0 | 0.8186 | 0.9016 | -49.21 | 0.017737 |
| > 1 | 0.6002 | 0.8068 | -111.49 | 0.091049 |
| > 2 | 0.2100 | 0.7056 | -284.80 | 0.594088 |
| > 3 | 0.2016 | 0.5777 | -209.22 | 0.320607 |
| > 4 | 0.1790 | 0.4740 | -166.62 | 0.203347 |
| > 5 | 0.0871 | 0.3467 | -156.79 | 0.180070 |
| > 6 | 0.0864 | 0.2762 | -122.86 | 0.110556 |
| > 7 | 0.0370 | 0.1867 | -111.36 | 0.090831 |
| > 8 | 0.0302 | 0.1372 | -89.80 | 0.059062 |
| > 9 | 0.0237 | 0.0923 | -68.17 | 0.034040 |
| > 10 | 0.0224 | 0.0601 | -45.22 | 0.014980 |
| > 11 | 0.0220 | 0.0417 | -27.96 | 0.005728 |
| > 12 | 0.0009 | 0.0242 | -42.39 | 0.013164 |

## Comparaison des paramétrisations

NLL validation du registre seul : `2.594465`.

| Représentation | Paramètres | NLL train | NLL validation | Gain validation |
|---|---:|---:|---:|---:|
| `categorical_0_to_11_and_12_plus` | 13 | 1.948692 | 1.925994 | 0.668471 |
| `two_thresholds_gt_2_gt_7` | 2 | 1.991013 | 1.971650 | 0.622816 |
| `single_threshold_gt_2` | 1 | 2.029483 | 2.011656 | 0.582810 |
| `linear_step_size` | 1 | 2.224473 | 2.226575 | 0.367891 |
| `clipped_linear_at_12` | 1 | 2.225286 | 2.227767 | 0.366699 |
| `hinge_after_2` | 1 | 2.235131 | 2.238487 | 0.355979 |

## Distribution exacte sur validation

| Taille maximale | Taux Bach | Taux attendu par le registre | Ratio |
|---:|---:|---:|---:|
| 0 | 0.0789 | 0.0435 | 1.813 |
| 1 | 0.1769 | 0.0761 | 2.325 |
| 2 | 0.4639 | 0.1420 | 3.266 |
| 3 | 0.0495 | 0.1369 | 0.362 |
| 4 | 0.0461 | 0.1170 | 0.394 |
| 5 | 0.0988 | 0.1298 | 0.761 |
| 6 | 0.0042 | 0.0748 | 0.056 |
| 7 | 0.0459 | 0.0905 | 0.507 |
| 8 | 0.0068 | 0.0489 | 0.139 |
| 9 | 0.0042 | 0.0469 | 0.089 |
| 10 | 0.0013 | 0.0315 | 0.041 |
| 11 | 0.0007 | 0.0193 | 0.035 |
| 12+ | 0.0230 | 0.0428 | 0.536 |

## Décomposition par voix sur validation

| Voix | max > 2 Bach | max > 2 attendu | exactement 2 | entrée > 2 | sortie > 2 si attaque |
|---|---:|---:|---:|---:|---:|
| Soprano | 0.2056 | 0.7000 | 0.5070 | 0.1446 | 0.1611 |
| Alto | 0.1991 | 0.6888 | 0.4581 | 0.1342 | 0.1269 |
| Tenor | 0.2904 | 0.7277 | 0.4513 | 0.1941 | 0.1951 |
| Bass | 0.4081 | 0.8269 | 0.4478 | 0.3141 | 0.2696 |

## Lecture

La meilleure représentation de cet audit est `categorical_0_to_11_and_12_plus` avec 13 paramètre(s).
Son avantage de validation sur le seuil simple est `0.085662` NLL.

À complexité égale, le seuil simple bat la pente linéaire de `0.214919` NLL.
Le ratio observé/attendu passe de `3.266` pour deux demi-tons à `0.362` pour trois.

Les quatre voix montrent la même direction, avec davantage de sauts
à la basse. Les données soutiennent donc une frontière **souple**
après le ton : `PREFER mouvement ≤ 2`, et non `FORBID mouvement > 2`.
La seconde colonne `> 7` représente une pénalité graduée additionnelle.
