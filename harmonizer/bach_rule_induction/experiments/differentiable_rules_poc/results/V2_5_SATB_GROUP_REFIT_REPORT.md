# POC V2.5 — ablation par groupe avec réajustement

## Protocole

- Chaque groupe est retiré du catalogue de sept règles.
- Tous les poids restants sont réestimés depuis zéro.
- La référence complète est le modèle canonique V2.4.
- Le test final reste scellé.
- Chorals authentiques.

## Résultats

NLL validation du catalogue complet : `1.287062`.

| Groupe retiré | Règles retirées | NLL train | NLL validation | Pénalité après réajustement |
|---|---|---:|---:|---:|
| parallels | `R-PARALLEL-001`, `R-PARALLEL-002` | 1.331164 | 1.338445 | +0.051384 |
| melody | `R-MELODY-001`, `R-MELODY-002` | 1.290828 | 1.295815 | +0.008753 |
| overlap | `R-OVERLAP-001` | 1.286659 | 1.292481 | +0.005419 |
| direct | `R-DIRECT-001`, `R-DIRECT-002` | 1.283518 | 1.288059 | +0.000997 |

Une pénalité positive signifie que le modèle réajusté ne compense
pas entièrement le retrait du groupe.
