# K3-V30-JOINT-STRONG-RESOLUTION-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 16 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V29 réajusté | — | 0.750238 | — | — | — | **← retenu**
| groupe V30 forte résiduelle et résolution λ=0.6 | 0.6 | 0.749929 | +0.000309 | [-0.002115, +0.002905] | 5/10 |
| groupe V30 forte résiduelle et résolution λ=0.3 | 0.3 | 0.749682 | +0.000556 | [-0.003615, +0.004918] | 4/10 |
| groupe V30 forte résiduelle et résolution λ=0.1 | 0.1 | 0.749706 | +0.000532 | [-0.004822, +0.006060] | 4/10 |
| groupe V30 forte résiduelle et résolution λ=0.03 | 0.03 | 0.749745 | +0.000493 | [-0.005201, +0.006404] | 4/10 |
| groupe V30 forte résiduelle et résolution λ=0 | 0 | 0.749765 | +0.000473 | [-0.005410, +0.006487] | 4/10 |

- Sélection : `socle V29 réajusté`.
- Groupe retenu sur ce découpage : `false`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `exact_named_ambiguous__acceptable_following_sonority` | +0.1975 |
| `exact_named_ambiguous__unacceptable_following_sonority` | -0.2248 |
| `incomplete_consonant_triad__acceptable_following_sonority` | +0.1669 |
| `incomplete_consonant_triad__unacceptable_following_sonority` | -0.2532 |
| `triad_plus_one_ambiguous__acceptable_following_sonority` | -0.1780 |
| `triad_plus_one_ambiguous__unacceptable_following_sonority` | -0.0511 |
| `triad_plus_passing_or_neighbor__acceptable_following_sonority` | -0.2030 |
| `triad_plus_passing_or_neighbor__unacceptable_following_sonority` | +0.1117 |
| `triad_plus_suspension__acceptable_following_sonority` | +0.0386 |
| `triad_plus_suspension__unacceptable_following_sonority` | +0.3364 |
| `triad_plus_appoggiatura__acceptable_following_sonority` | +0.1945 |
| `triad_plus_appoggiatura__unacceptable_following_sonority` | +0.1501 |
| `triad_plus_unlicensed__acceptable_following_sonority` | +0.3033 |
| `triad_plus_unlicensed__unacceptable_following_sonority` | -0.3192 |
| `other_unlicensed__acceptable_following_sonority` | +0.3518 |
| `other_unlicensed__unacceptable_following_sonority` | -0.3625 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
