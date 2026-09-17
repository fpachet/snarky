# V24 — groupe exhaustif des sonorités résiduelles

Les huit cellules sont apprises simultanément au-dessus de V23. Elles
ne dupliquent aucun accord nommé unique : elles couvrent exactement
l'état de référence laissé sans facteur par V23.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V23 réajusté | — | 0.887905 | — | — | — | **← retenu**
| groupe V24 λ=0.6 | 0.6 | 0.887075 | +0.000829 | [-0.002308, +0.003676] | 5/8 |

- Sélection : `socle V23 réajusté`.
- Groupe retenu sur ce découpage : `false`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `exact_named_ambiguous` | +0.2298 |
| `incomplete_consonant_triad` | -0.1712 |
| `triad_plus_one_ambiguous` | -0.2808 |
| `triad_plus_passing_or_neighbor` | -0.0083 |
| `triad_plus_suspension` | +0.2915 |
| `triad_plus_appoggiatura` | +0.3188 |
| `triad_plus_unlicensed` | -0.1655 |
| `other_unlicensed` | -0.2377 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
