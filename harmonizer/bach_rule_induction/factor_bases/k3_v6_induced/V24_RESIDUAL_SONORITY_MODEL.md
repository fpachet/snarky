# V24 — groupe exhaustif des sonorités résiduelles

Les huit cellules sont apprises simultanément au-dessus de V23. Elles
ne dupliquent aucun accord nommé unique : elles couvrent exactement
l'état de référence laissé sans facteur par V23.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V23 réajusté | — | 0.787948 | — | — | — |
| groupe V24 λ=0.6 | 0.6 | 0.787897 | +0.000051 | [+0.000001, +0.000106] | 6/10 | **← retenu**
| groupe V24 λ=0.3 | 0.3 | 0.787860 | +0.000088 | [+0.000000, +0.000183] | 6/10 |
| groupe V24 λ=0.1 | 0.1 | 0.787836 | +0.000112 | [-0.000001, +0.000235] | 6/10 |
| groupe V24 λ=0.03 | 0.03 | 0.787827 | +0.000121 | [-0.000002, +0.000252] | 6/10 |
| groupe V24 λ=0 | 0 | 0.787824 | +0.000124 | [-0.000001, +0.000260] | 6/10 |

- Sélection : `groupe V24 λ=0.6`.
- Groupe retenu sur ce découpage : `true`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `exact_named_ambiguous` | +0.0080 |
| `incomplete_consonant_triad` | +0.0080 |
| `triad_plus_one_ambiguous` | -0.0080 |
| `triad_plus_passing_or_neighbor` | -0.0080 |
| `triad_plus_suspension` | +0.0080 |
| `triad_plus_appoggiatura` | +0.0080 |
| `triad_plus_unlicensed` | -0.0080 |
| `other_unlicensed` | -0.0080 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
