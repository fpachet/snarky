# V25 — résidu des moments de sonorité faible

Le modèle V25 est figé. Ce diagnostic compare ses générations au corpus sur les neuf statuts V25, sans modifier aucun poids.

| Statut | Bach | V25 | Écart Bach − V25 |
|---|---:|---:|---:|
| `exact_named_ambiguous` | 0.0198 | 0.0269 | -0.0070 |
| `incomplete_consonant_triad` | 0.0168 | 0.0223 | -0.0055 |
| `triad_plus_one_ambiguous` | 0.0000 | 0.0031 | -0.0031 |
| `triad_plus_passing` | 0.0046 | 0.0031 | +0.0015 |
| `triad_plus_neighbor` | 0.0000 | 0.0006 | -0.0006 |
| `triad_plus_suspension` | 0.0260 | 0.0076 | +0.0183 |
| `triad_plus_appoggiatura` | 0.0000 | 0.0006 | -0.0006 |
| `triad_plus_unlicensed` | 0.0687 | 0.0577 | +0.0110 |
| `other_unlicensed` | 0.1435 | 0.1798 | -0.0363 |

- Résiduel total Bach : `0.2794`.
- Résiduel total V25 : `0.3017`.
- MAE des neuf moments : `0.00933`.
