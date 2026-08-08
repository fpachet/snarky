# K3-V27-BASS-TRAJECTORY-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 10 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V26 réajusté | — | 0.797436 | — | — | — |
| groupe V27 trajectoire de basse λ=0.6 | 0.6 | 0.790105 | +0.007331 | [+0.004941, +0.009671] | 40/50 | **← retenu**

- Sélection : `groupe V27 trajectoire de basse λ=0.6`.
- Groupe retenu sur ce découpage : `true`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `named_chord_bass` | +0.4544 |
| `consonant_scaffold_chord_tone` | +0.0150 |
| `diatonic_passing` | +0.3788 |
| `chromatic_passing` | -0.4221 |
| `diatonic_neighbor` | +0.1344 |
| `chromatic_neighbor` | -0.3962 |
| `prepared_step_resolution` | +0.0030 |
| `attacked_step_resolution` | -0.4183 |
| `other_diatonic` | +0.2828 |
| `other_chromatic` | -0.3513 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
