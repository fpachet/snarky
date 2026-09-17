# V25 — résidu des moments de sonorité faible

Le modèle V24 est figé. Ce diagnostic compare ses générations au corpus sur les neuf statuts V25, sans modifier aucun poids.

| Statut | Bach | V24 | Écart Bach − V24 |
|---|---:|---:|---:|
| `exact_named_ambiguous` | 0.0198 | 0.0275 | -0.0076 |
| `incomplete_consonant_triad` | 0.0168 | 0.0229 | -0.0061 |
| `triad_plus_one_ambiguous` | 0.0000 | 0.0027 | -0.0027 |
| `triad_plus_passing` | 0.0046 | 0.0024 | +0.0021 |
| `triad_plus_neighbor` | 0.0000 | 0.0006 | -0.0006 |
| `triad_plus_suspension` | 0.0260 | 0.0082 | +0.0177 |
| `triad_plus_appoggiatura` | 0.0000 | 0.0009 | -0.0009 |
| `triad_plus_unlicensed` | 0.0687 | 0.0571 | +0.0116 |
| `other_unlicensed` | 0.1435 | 0.1930 | -0.0495 |

- Résiduel total Bach : `0.2794`.
- Résiduel total V24 : `0.3154`.
- MAE des neuf moments : `0.01099`.
