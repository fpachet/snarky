# V25 — résidu des moments de sonorité faible

Le modèle V24 est figé. Ce diagnostic compare ses générations au corpus
sur les neuf statuts V25, sans modifier aucun poids.

| Statut | Bach | V24 | Écart Bach − V24 |
|---|---:|---:|---:|
| `exact_named_ambiguous` | 0.0171 | 0.0248 | -0.0077 |
| `incomplete_consonant_triad` | 0.0261 | 0.0225 | +0.0036 |
| `triad_plus_one_ambiguous` | 0.0000 | 0.0072 | -0.0072 |
| `triad_plus_passing` | 0.0072 | 0.0032 | +0.0041 |
| `triad_plus_neighbor` | 0.0000 | 0.0014 | -0.0014 |
| `triad_plus_suspension` | 0.0090 | 0.0041 | +0.0050 |
| `triad_plus_appoggiatura` | 0.0000 | 0.0023 | -0.0023 |
| `triad_plus_unlicensed` | 0.0469 | 0.0473 | -0.0005 |
| `other_unlicensed` | 0.1424 | 0.2132 | -0.0708 |

- Résiduel total Bach : `0.2488`.
- Résiduel total V24 : `0.3258`.
- MAE des neuf moments : `0.01137`.
