# V23 — basse métrique et harmonie nommée

Les deux groupes sont appris conjointement avec tous les paramètres V22,
mais évalués aussi séparément. Les poids de basse sont centrés par mode ;
les poids d'accord utilisent comme référence l'absence d'une analyse
nommée unique.

## Ablations sur le découpage de structure

### `bass_only`

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|---:|
| socle V22 réajusté | absent | 0.798404 | — | — | — | **← retenu**
| bass_only λ=0.6 | 0.6 | 0.798275 | +0.000129 | [-0.001371, +0.001630] | 5/10 |
| bass_only λ=0.3 | 0.3 | 0.798021 | +0.000383 | [-0.001327, +0.002125] | 5/10 |
| bass_only λ=0.1 | 0.1 | 0.797946 | +0.000458 | [-0.001602, +0.002565] | 5/10 |
| bass_only λ=0.03 | 0.03 | 0.797927 | +0.000477 | [-0.001674, +0.002687] | 5/10 |
| bass_only λ=0 | 0 | 0.797924 | +0.000480 | [-0.001701, +0.002711] | 4/10 |

- Sélection : `socle V22 réajusté`.
- Variante retenue sur ce découpage : `false`.

### `harmony_only`

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|---:|
| socle V22 réajusté | absent | 0.798404 | — | — | — | **← retenu**
| harmony_only λ=0.6 | 0.6 | 0.796642 | +0.001762 | [-0.000815, +0.004141] | 6/10 |
| harmony_only λ=0.3 | 0.3 | 0.796127 | +0.002277 | [-0.001335, +0.005525] | 7/10 |
| harmony_only λ=0.1 | 0.1 | 0.796014 | +0.002390 | [-0.001838, +0.006202] | 7/10 |
| harmony_only λ=0.03 | 0.03 | 0.795975 | +0.002429 | [-0.002222, +0.006543] | 7/10 |
| harmony_only λ=0 | 0 | 0.795966 | +0.002438 | [-0.002291, +0.006691] | 7/10 |

- Sélection : `socle V22 réajusté`.
- Variante retenue sur ce découpage : `false`.

### `both_groups`

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|---:|
| socle V22 réajusté | absent | 0.798404 | — | — | — | **← retenu**
| both_groups λ=0.6 | 0.6 | 0.796215 | +0.002189 | [-0.000595, +0.004805] | 6/10 |
| both_groups λ=0.3 | 0.3 | 0.795565 | +0.002839 | [-0.000971, +0.006311] | 7/10 |
| both_groups λ=0.1 | 0.1 | 0.795409 | +0.002995 | [-0.001524, +0.007141] | 7/10 |
| both_groups λ=0.03 | 0.03 | 0.795315 | +0.003089 | [-0.001196, +0.007084] | 6/10 |
| both_groups λ=0 | 0 | 0.795277 | +0.003127 | [-0.001292, +0.007203] | 7/10 |

- Sélection : `socle V22 réajusté`.
- Variante retenue sur ce découpage : `false`.

## Portée de la décision

Ce résultat ne suffit pas encore à adopter V23. Les pénalités et
variantes candidates retenues ici doivent être gelées puis répétées
dans des plis de chorals disjoints avant le réajustement complet.
