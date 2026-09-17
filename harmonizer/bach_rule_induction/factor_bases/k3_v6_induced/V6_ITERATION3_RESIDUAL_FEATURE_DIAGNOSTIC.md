# V6 — diagnostic des facteurs résiduels après l'itération 2

Ce diagnostic ne réapprend pas encore le modèle. Il réutilise les états
finaux des trois campagnes multigraines et compare, pièce par pièce, les
activations de Bach à celles de Gibbs. Le test réservé reste fermé.

## Protocole

- Pièces de train : `32`.
- Graines : `[10103, 20207, 30313]`.
- États générés par pièce : `6`.
- Candidates lisibles : `782`.
- Seuil : signe identique sur les trois graines, `|z| ≥ 2.0`.

## Candidates prioritaires

| Famille | Description | Bach | Gibbs | Gradient | z |
|---|---|---:|---:|---:|---:|
| `bass_motion` | basse : classe d'intervalle entrant 2 | 0.3686 | 0.2825 | +0.0861 | +6.68 |
| `bass_motion` | basse : saut entrant supérieur à 2 demi-tons | 0.3289 | 0.4079 | -0.0790 | -5.91 |
| `bass_motion` | basse : classe d'intervalle entrant 3 | 0.0340 | 0.0840 | -0.0500 | -9.17 |
| `bass_motion` | basse : directions K3 (+1, -1) | 0.1292 | 0.1905 | -0.0614 | -7.73 |
| `bass_motion` | basse : classe d'intervalle entrant 0 | 0.0913 | 0.0530 | +0.0383 | +4.21 |
| `bass_motion` | basse : directions K3 (+1, +0) | 0.1902 | 0.1486 | +0.0415 | +5.80 |
| `vertical_context` | intervalle vertical 7 présent sur bloc métrique fort | 0.2023 | 0.1774 | +0.0249 | +5.74 |
| `vertical_context` | intervalle vertical 10 présent sur bloc métrique faible | 0.0663 | 0.0417 | +0.0246 | +5.50 |
| `vertical_context` | intervalle vertical 8 présent sur bloc métrique faible | 0.1188 | 0.1442 | -0.0254 | -5.08 |
| `vertical_context` | sonorité {0, 4, 9} relative à la basse, bloc faible | 0.0425 | 0.0189 | +0.0236 | +6.98 |
| `vertical_context` | intervalle vertical 6 présent sur bloc métrique fort | 0.0272 | 0.0436 | -0.0164 | -5.36 |
| `vertical_context` | sonorité {0, 5, 8} relative à la basse, bloc fort | 0.0037 | 0.0192 | -0.0155 | -7.48 |
| `sonority_transition` | transition {0, 4, 7} → {0, 4, 7, 10} | 0.0334 | 0.0143 | +0.0192 | +4.79 |
| `sonority_transition` | transition {0, 5, 7} → {0, 4, 7} | 0.0183 | 0.0037 | +0.0146 | +4.22 |
| `sonority_transition` | transition {0, 3, 6, 8} → {0, 3, 6, 8} | 0.0006 | 0.0082 | -0.0076 | -6.39 |
| `sonority_transition` | transition {0, 4, 7, 10} → {0, 4, 7} | 0.0221 | 0.0091 | +0.0130 | +3.66 |
| `sonority_transition` | transition {0, 4, 7, 10} → {0, 4, 7, 10} | 0.0000 | 0.0073 | -0.0073 | -6.23 |
| `sonority_transition` | transition {0, 3, 7} → {0, 5, 8} | 0.0004 | 0.0062 | -0.0058 | -7.03 |

Ces candidates sont des hypothèses de structure, pas encore des
règles acceptées. La prochaine expérience doit les ajouter par petits
lots, réapprendre leurs poids sur train et exiger un gain simultané à
6 et 30 sweeps avant toute promotion.
