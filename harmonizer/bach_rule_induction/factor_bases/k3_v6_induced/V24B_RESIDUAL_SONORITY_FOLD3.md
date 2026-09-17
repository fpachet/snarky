# V24 — groupe exhaustif des sonorités résiduelles

Les huit cellules sont apprises simultanément au-dessus de V23. Elles
ne dupliquent aucun accord nommé unique : elles couvrent exactement
l'état de référence laissé sans facteur par V23.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V23 réajusté | — | 0.879961 | — | — | — | **← retenu**
| groupe V24 λ=0.6 | 0.6 | 0.880063 | -0.000102 | [-0.002133, +0.002002] | 4/8 |

- Sélection : `socle V23 réajusté`.
- Groupe retenu sur ce découpage : `false`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `exact_named_ambiguous` | +0.0000 |
| `incomplete_consonant_triad` | +0.0000 |
| `triad_plus_one_ambiguous` | +0.0000 |
| `triad_plus_passing_or_neighbor` | +0.0000 |
| `triad_plus_suspension` | +0.0000 |
| `triad_plus_appoggiatura` | +0.0000 |
| `triad_plus_unlicensed` | +0.0000 |
| `other_unlicensed` | +0.0000 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
