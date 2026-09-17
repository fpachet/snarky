# K3-V28-BASS-MOTION-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 8 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V27 réajusté | — | 0.786094 | — | — | — |
| groupe V28 mouvement de basse λ=0.6 | 0.6 | 0.779258 | +0.006836 | [+0.004376, +0.009328] | 39/50 | **← retenu**

- Sélection : `groupe V28 mouvement de basse λ=0.6`.
- Groupe retenu sur ce découpage : `true`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `held_bass` | -0.0000 |
| `attacked_repeat` | -0.3715 |
| `chromatic_passing_or_neighbor` | +0.2588 |
| `chromatic_step_resolved` | -0.3727 |
| `chromatic_step_unresolved` | +0.2980 |
| `whole_tone_arrival` | +0.3194 |
| `small_skip_arrival` | -0.2738 |
| `leap_arrival` | -0.0832 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
