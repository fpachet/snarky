# K3-V28-BASS-MOTION-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 8 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V27 réajusté | — | 0.778018 | — | — | — |
| groupe V28 mouvement de basse λ=0.6 | 0.6 | 0.769780 | +0.008238 | [+0.003818, +0.012649] | 7/10 | **← retenu**
| groupe V28 mouvement de basse λ=0.3 | 0.3 | 0.767749 | +0.010270 | [+0.004184, +0.016372] | 7/10 |
| groupe V28 mouvement de basse λ=0.1 | 0.1 | 0.767332 | +0.010686 | [+0.004056, +0.017354] | 7/10 |
| groupe V28 mouvement de basse λ=0.03 | 0.03 | 0.767239 | +0.010780 | [+0.004023, +0.017593] | 7/10 |
| groupe V28 mouvement de basse λ=0 | 0 | 0.767009 | +0.011009 | [+0.004038, +0.018087] | 7/10 |

- Sélection : `groupe V28 mouvement de basse λ=0.6`.
- Groupe retenu sur ce découpage : `true`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `held_bass` | -0.0000 |
| `attacked_repeat` | -0.3695 |
| `chromatic_passing_or_neighbor` | +0.2589 |
| `chromatic_step_resolved` | -0.3726 |
| `chromatic_step_unresolved` | +0.2982 |
| `whole_tone_arrival` | +0.3195 |
| `small_skip_arrival` | -0.2739 |
| `leap_arrival` | -0.0833 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
