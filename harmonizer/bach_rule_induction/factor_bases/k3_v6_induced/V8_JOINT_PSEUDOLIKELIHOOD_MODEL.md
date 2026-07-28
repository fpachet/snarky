# V8 — apprentissage conjoint par pseudo-vraisemblance

Tous les facteurs retenus contribuent au score de chaque note candidate
avant le softmax. Les poids sont appris simultanément sur les choix
authentiques de Bach; aucun poids V6 n'est gelé. Le test réservé reste
fermé.

## Protocole

- Décisions train : `68263`.
- Décisions validation : `13202`.
- Alternatives par décision : `46`.
- Facteurs V6 : `30`.
- Facteurs résiduels candidats : `18`.
- Facteurs appris conjointement : `48`.
- L1 : `0.0005`; L2 : `0.001`.

## Pseudo-vraisemblance conditionnelle

| Modèle | NLL train | NLL validation |
|---|---:|---:|
| Baseline registre + tonalité | — | 2.422315 |
| V6 appris par pseudo-vraisemblance | 1.043839 | 1.048935 |
| Iteration 2 après calibration générative | — | 1.241166 |
| V8 conjoint (48 facteurs) | 0.996693 | 0.998314 |

Gain V8 contre la structure V6 en validation : `+0.050621` nats/décision.

## Poids résiduels appris

| Famille | Facteur | Poids |
|---|---|---:|
| `bass_motion` | basse : classe d'intervalle entrant 2 | +0.059169 |
| `bass_motion` | basse : saut entrant supérieur à 2 demi-tons | -0.099599 |
| `bass_motion` | basse : classe d'intervalle entrant 3 | -0.405268 |
| `bass_motion` | basse : directions K3 (+1, -1) | -0.160434 |
| `bass_motion` | basse : classe d'intervalle entrant 0 | +0.700656 |
| `bass_motion` | basse : directions K3 (+1, +0) | -0.354738 |
| `vertical_context` | intervalle vertical 7 présent sur bloc métrique fort | +0.065234 |
| `vertical_context` | intervalle vertical 10 présent sur bloc métrique faible | +0.978076 |
| `vertical_context` | intervalle vertical 8 présent sur bloc métrique faible | +0.020004 |
| `vertical_context` | sonorité {0, 4, 9} relative à la basse, bloc faible | +0.894539 |
| `vertical_context` | intervalle vertical 6 présent sur bloc métrique fort | -0.326658 |
| `vertical_context` | sonorité {0, 5, 8} relative à la basse, bloc fort | -0.537405 |
| `sonority_transition` | transition {0, 4, 7} → {0, 4, 7, 10} | +1.134050 |
| `sonority_transition` | transition {0, 5, 7} → {0, 4, 7} | +1.062817 |
| `sonority_transition` | transition {0, 3, 6, 8} → {0, 3, 6, 8} | -0.329073 |
| `sonority_transition` | transition {0, 4, 7, 10} → {0, 4, 7} | +0.500154 |
| `sonority_transition` | transition {0, 4, 7, 10} → {0, 4, 7, 10} | -0.098561 |
| `sonority_transition` | transition {0, 3, 7} → {0, 5, 8} | +0.022919 |

Ce résultat mesure la prédiction locale. Une promotion exige encore
les audits génératifs appariés à 6 et 30 sweeps.
