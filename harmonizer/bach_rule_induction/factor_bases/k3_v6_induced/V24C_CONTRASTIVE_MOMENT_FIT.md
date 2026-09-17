# V24C — apprentissage par moments contrastifs

Le vocabulaire V24 reste gelé. À chaque itération, le gradient compare
la fréquence des huit statuts chez Bach à leur fréquence dans les
générations du modèle courant. Les paramètres V23 sont fixes.

| Itération | Résiduel Bach | Résiduel généré | MAE moments | Norme des poids |
|---:|---:|---:|---:|---:|
| 0 | 0.1742 | 0.2464 | 0.01335 | 0.0000 |
| 1 | 0.1742 | 0.2329 | 0.01215 | 0.0359 |
| 2 | 0.1742 | 0.2368 | 0.01311 | 0.0671 |
| 3 | 0.1742 | 0.2262 | 0.01155 | 0.1011 |
| 4 | 0.1742 | 0.2320 | 0.01203 | 0.1321 |
| 5 | 0.1742 | 0.2320 | 0.01107 | 0.1640 |
| 6 | 0.1742 | 0.2281 | 0.01011 | 0.1938 |
| 7 | 0.1742 | 0.2291 | 0.00974 | 0.2214 |
| 8 | 0.1742 | 0.2204 | 0.00938 | 0.2465 |

## Poids finaux

| Statut | Bach | Généré final | Poids |
|---|---:|---:|---:|
| `exact_named_ambiguous` | 0.0154 | 0.0183 | -0.0075 |
| `incomplete_consonant_triad` | 0.0318 | 0.0221 | +0.0486 |
| `triad_plus_one_ambiguous` | 0.0000 | 0.0010 | -0.0043 |
| `triad_plus_passing_or_neighbor` | 0.0010 | 0.0029 | -0.0090 |
| `triad_plus_suspension` | 0.0038 | 0.0000 | +0.0151 |
| `triad_plus_appoggiatura` | 0.0029 | 0.0019 | +0.0033 |
| `triad_plus_unlicensed` | 0.0231 | 0.0327 | -0.0392 |
| `other_unlicensed` | 0.0962 | 0.1415 | -0.2377 |

Cette calibration est une approximation Monte-Carlo du gradient
MaxEnt génératif. Elle ne transforme aucune cellule en contrainte
dure et n'utilise pas la validation pour modifier les poids.
