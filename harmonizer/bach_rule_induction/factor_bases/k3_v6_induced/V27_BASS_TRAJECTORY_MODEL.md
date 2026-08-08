# K3-V27-BASS-TRAJECTORY-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 10 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V26 réajusté | — | 0.786549 | — | — | — | **← retenu**
| groupe V27 trajectoire de basse λ=0.6 | 0.6 | 0.781174 | +0.005375 | [-0.001955, +0.012266] | 6/10 |
| groupe V27 trajectoire de basse λ=0.3 | 0.3 | 0.778802 | +0.007747 | [-0.003546, +0.018379] | 6/10 |
| groupe V27 trajectoire de basse λ=0.1 | 0.1 | 0.778390 | +0.008159 | [-0.004631, +0.020189] | 6/10 |
| groupe V27 trajectoire de basse λ=0.03 | 0.03 | 0.778328 | +0.008222 | [-0.004977, +0.020501] | 6/10 |
| groupe V27 trajectoire de basse λ=0 | 0 | 0.778306 | +0.008243 | [-0.005178, +0.020722] | 6/10 |

- Sélection : `socle V26 réajusté`.
- Groupe retenu sur ce découpage : `false`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `named_chord_bass` | +1.2392 |
| `consonant_scaffold_chord_tone` | +0.3282 |
| `diatonic_passing` | +0.6869 |
| `chromatic_passing` | -0.9843 |
| `diatonic_neighbor` | +0.2428 |
| `chromatic_neighbor` | -0.7264 |
| `prepared_step_resolution` | +0.1650 |
| `attacked_step_resolution` | -1.0474 |
| `other_diatonic` | +0.4885 |
| `other_chromatic` | -0.5097 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
