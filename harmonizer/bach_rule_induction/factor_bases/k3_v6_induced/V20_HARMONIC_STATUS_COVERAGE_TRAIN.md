# V20 — couverture train des statuts harmoniques nommés

Cet audit précède toute induction. Il mesure seulement si un vocabulaire
déterministe de fondamentales, qualités et renversements couvre le corpus.
Aucun poids n'est appris et le test réservé n'est pas chargé.

## Couverture

- Chorals de train : `251`.
- Blocs verticaux : `24452`.
- Accord complet nommé : `78.21 %`.
- Analyse unique : `76.77 %`.
- Analyse symétriquement ambiguë : `1.44 %`.
- Couverture exacte sur temps fort : `86.13 %`.
- Couverture exacte sur temps faible : `74.05 %`.
- Triade plus une classe étrangère : `6.90 %`.
- Accord nommé ou triade plus une étrangère : `85.11 %`.

## Qualités reconnues exactement

| Qualité | Blocs | Support en chorals |
|---|---:|---:|
| `major_triad` | 8453 | 251 |
| `minor_triad` | 4414 | 251 |
| `dominant_seventh` | 2243 | 251 |
| `minor_seventh` | 1214 | 246 |
| `diminished_triad` | 1102 | 237 |
| `major_seventh` | 668 | 220 |
| `half_diminished_seventh` | 641 | 205 |
| `diminished_seventh` | 264 | 127 |
| `augmented_triad` | 89 | 55 |
| `minor_major_seventh` | 37 | 28 |

Les analyses ambiguës, notamment les accords symétriques, ne reçoivent
pas arbitrairement une fondamentale. La prochaine décision doit
comparer cette couverture au coût du nouveau vocabulaire avant de
construire la grammaire V20.
