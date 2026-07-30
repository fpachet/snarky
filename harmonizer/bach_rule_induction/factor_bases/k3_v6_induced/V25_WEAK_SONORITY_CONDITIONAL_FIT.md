# K3-V25-WEAK-SONORITY-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 9 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V24 réajusté | — | 0.786946 | — | — | — | **← retenu**
| groupe V25 faible λ=0.6 | 0.6 | 0.786734 | +0.000212 | [-0.000066, +0.000498] | 6/10 |
| groupe V25 faible λ=0.3 | 0.3 | 0.786580 | +0.000367 | [-0.000120, +0.000865] | 6/10 |
| groupe V25 faible λ=0.1 | 0.1 | 0.786478 | +0.000468 | [-0.000160, +0.001111] | 6/10 |
| groupe V25 faible λ=0.03 | 0.03 | 0.786443 | +0.000503 | [-0.000171, +0.001196] | 6/10 |
| groupe V25 faible λ=0 | 0 | 0.786429 | +0.000518 | [-0.000180, +0.001233] | 6/10 |

- Sélection : `socle V24 réajusté`.
- Groupe retenu sur ce découpage : `false`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `exact_named_ambiguous` | +0.0200 |
| `incomplete_consonant_triad` | +0.0200 |
| `triad_plus_one_ambiguous` | -0.0200 |
| `triad_plus_passing` | +0.0200 |
| `triad_plus_neighbor` | -0.0200 |
| `triad_plus_suspension` | +0.0200 |
| `triad_plus_appoggiatura` | -0.0200 |
| `triad_plus_unlicensed` | -0.0200 |
| `other_unlicensed` | -0.0200 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
