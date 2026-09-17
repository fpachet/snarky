# K3-V26-JOINT-WEAK-RESOLUTION-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 18 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V24 réajusté | — | 0.786946 | — | — | — |
| groupe V26 faible × résolution λ=0.6 | 0.6 | 0.786743 | +0.000203 | [+0.000072, +0.000337] | 8/10 | **← retenu**
| groupe V26 faible × résolution λ=0.3 | 0.3 | 0.786594 | +0.000352 | [+0.000123, +0.000587] | 8/10 |
| groupe V26 faible × résolution λ=0.1 | 0.1 | 0.786793 | +0.000153 | [-0.013879, +0.011706] | 7/10 |
| groupe V26 faible × résolution λ=0.03 | 0.03 | 0.786552 | +0.000394 | [-0.014227, +0.012360] | 7/10 |
| groupe V26 faible × résolution λ=0 | 0 | 0.786476 | +0.000470 | [-0.014362, +0.012522] | 7/10 |

- Sélection : `groupe V26 faible × résolution λ=0.6`.
- Groupe retenu sur ce découpage : `true`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `exact_named_ambiguous__acceptable_following_sonority` | +0.0080 |
| `exact_named_ambiguous__unacceptable_following_sonority` | -0.0080 |
| `incomplete_consonant_triad__acceptable_following_sonority` | +0.0080 |
| `incomplete_consonant_triad__unacceptable_following_sonority` | -0.0080 |
| `triad_plus_one_ambiguous__acceptable_following_sonority` | -0.0080 |
| `triad_plus_one_ambiguous__unacceptable_following_sonority` | -0.0080 |
| `triad_plus_passing__acceptable_following_sonority` | +0.0080 |
| `triad_plus_passing__unacceptable_following_sonority` | -0.0080 |
| `triad_plus_neighbor__acceptable_following_sonority` | -0.0080 |
| `triad_plus_neighbor__unacceptable_following_sonority` | -0.0080 |
| `triad_plus_suspension__acceptable_following_sonority` | +0.0080 |
| `triad_plus_suspension__unacceptable_following_sonority` | +0.0080 |
| `triad_plus_appoggiatura__acceptable_following_sonority` | -0.0080 |
| `triad_plus_appoggiatura__unacceptable_following_sonority` | -0.0080 |
| `triad_plus_unlicensed__acceptable_following_sonority` | +0.0080 |
| `triad_plus_unlicensed__unacceptable_following_sonority` | -0.0080 |
| `other_unlicensed__acceptable_following_sonority` | +0.0080 |
| `other_unlicensed__unacceptable_following_sonority` | -0.0080 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
