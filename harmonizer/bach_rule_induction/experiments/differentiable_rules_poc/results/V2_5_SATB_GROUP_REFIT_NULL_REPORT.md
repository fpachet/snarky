# POC V2.5 — ablation par groupe avec réajustement

## Protocole

- Chaque groupe est retiré du catalogue de sept règles.
- Tous les poids restants sont réestimés depuis zéro.
- La référence complète est le modèle canonique V2.4.
- Le test final reste scellé.
- Contrôle nul par permutation.

## Résultats

NLL validation du catalogue complet : `2.456363`.

| Groupe retiré | Règles retirées | NLL train | NLL validation | Pénalité après réajustement |
|---|---|---:|---:|---:|
| melody | `R-MELODY-001`, `R-MELODY-002` | 2.455655 | 2.462117 | +0.005754 |
| overlap | `R-OVERLAP-001` | 2.450387 | 2.456966 | +0.000603 |
| direct | `R-DIRECT-001`, `R-DIRECT-002` | 2.449889 | 2.456365 | +0.000002 |
| parallels | `R-PARALLEL-001`, `R-PARALLEL-002` | 2.449957 | 2.456357 | -0.000007 |

Une pénalité positive signifie que le modèle réajusté ne compense
pas entièrement le retrait du groupe.
